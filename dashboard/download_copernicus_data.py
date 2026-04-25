import os
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from PIL import Image
import io
import base64
from dotenv import load_dotenv
import json
import sys

try:
    import copernicusmarine
    HAS_COPERNICUS = True
except ImportError:
    HAS_COPERNICUS = False
    print("Warning: copernicusmarine not installed. Install with: pip install copernicusmarine")

try:
    import regionmask
except ImportError:
    print("Warning: regionmask not installed")
    regionmask = None

# ================================
# CONFIGURATION
# ================================
load_dotenv()

# North Sea boundaries
MIN_LON, MAX_LON = -4, 10
MIN_LAT, MAX_LAT = 51, 59

# Fishing-relevant datasets (working IDs for 2026)
DATASETS = {
    "temperature": {
        "id": "cmems_mod_glo_phy-tem_anfc_0.083deg_P1D-m",
        "vars": ["sea_water_temperature"],
        "cmap": "RdYlBu_r",
        "label": "Sea Surface Temperature (°C)",
        "min": 0, "max": 25,
        "ideal_min": 12, "ideal_max": 18  # Fish preference
    },
    "salinity": {
        "id": "cmems_mod_glo_phy-sal_anfc_0.083deg_P1D-m",
        "vars": ["sea_water_salinity"],
        "cmap": "Blues",
        "label": "Salinity (PSU)",
        "min": 34, "max": 35.5,
        "ideal_min": 34.8, "ideal_max": 35.2  # Fish preference
    },
    "chlorophyll": {
        "id": "cmems_obs_oc_nrt_glo_0deg08_nrt_chunk",  # Higher resolution: 0.08° (~9km)
        "vars": ["CHL"],
        "cmap": "YlGn",
        "label": "Chlorophyll (mg/m³)",
        "min": 0, "max": 5,
        "ideal_min": 1, "ideal_max": 3,  # Fish food preference
        "stretch": "percentile"  # Better visualization
    },
    "mixed_layer": {
        "id": "cmems_mod_glo_phy_anfc_0.083deg_P1D-m",
        "vars": ["mlotst"],
        "cmap": "viridis",
        "label": "Mixed Layer Depth (m)",
        "min": 0, "max": 300,
        "ideal_min": 20, "ideal_max": 80  # Fish habitat preference
    }
}

OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================================
# HELPER FUNCTIONS
# ================================

def apply_percentile_stretch(values, lower=2, upper=98):
    """
    Apply percentile-based contrast stretching for better visualization.
    This is especially useful for noisy datasets like chlorophyll.
    
    Values below lower percentile → 0
    Values above upper percentile → 255
    This dramatically improves pattern visibility.
    """
    data_valid = values[~np.isnan(values)]
    if len(data_valid) == 0:
        return values
    
    p_low = np.percentile(data_valid, lower)
    p_high = np.percentile(data_valid, upper)
    
    if p_low == p_high:
        return values
    
    stretched = (values - p_low) / (p_high - p_low)
    stretched = np.clip(stretched, 0, 1)
    print(f"  ✓ Percentile stretch applied ({lower}%-{upper}%: {p_low:.3f} → {p_high:.3f})")
    return stretched

def apply_ocean_mask(data, lons, lats):
    """Apply land mask to data (requires regionmask)"""
    if regionmask is None:
        print("  ⚠ regionmask not available - no land masking")
        return data
    
    try:
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        land = regionmask.defined_regions.natural_earth_v5_0_0.land_110
        land_mask = land.mask(lon_grid, lat_grid)
        
        # land_mask returns:
        # - NaN for ocean (no land region)
        # - 0 (or region number) for land
        # So we want to mask OUT non-NaN values (the land)
        ocean_mask = np.isnan(land_mask)
        
        masked = data.copy()
        masked[~ocean_mask] = np.nan  # Set land to NaN
        
        ocean_pixels = np.isnan(masked).sum()
        land_pixels = (~np.isnan(masked)).sum()
        print(f"  ✓ Land mask applied (ocean: {land_pixels}, land: {ocean_pixels})")
        return masked
    except Exception as e:
        print(f"  ⚠ Land masking failed: {e}")
        return data

def prepare_image_for_leaflet(img_array, alpha, lats):
    """
    Prepare image array for Leaflet display.
    Ensures north is at top of image (row 0).
    
    If lats go from south to north (ascending), flip the image.
    If lats go from north to south (descending), keep as is.
    """
    if len(lats) > 1 and lats[0] < lats[-1]:
        # Lats are ascending (south to north) - flip to put north at top
        img_array = np.flipud(img_array)
        alpha = np.flipud(alpha)
        print(f"  ✓ Image flipped for proper georeferencing")
    return img_array, alpha

def standardize_resolution(values, lons, lats, target_km=1):
    """
    Standardize data to 1km x 1km resolution grid.
    Resamples data to uniform resolution covering the same geographic area.
    """
    try:
        # Calculate current resolution in km
        # Approximate: 1 degree ≈ 111 km at equator
        lon_res_km = (MAX_LON - MIN_LON) / len(lons) * 111 * np.cos(np.radians(np.mean(lats)))
        lat_res_km = (MAX_LAT - MIN_LAT) / len(lats) * 111
        
        print(f"  Current resolution: {lon_res_km:.2f}km (lon) x {lat_res_km:.2f}km (lat)")
        
        # Calculate target grid size
        area_lon_km = (MAX_LON - MIN_LON) * 111 * np.cos(np.radians(np.mean(lats)))
        area_lat_km = (MAX_LAT - MIN_LAT) * 111
        
        target_width = int(area_lon_km / target_km)
        target_height = int(area_lat_km / target_km)
        
        # Resample using scipy if available
        try:
            from scipy.ndimage import zoom
            # Calculate zoom factors
            zoom_y = target_height / values.shape[0]
            zoom_x = target_width / values.shape[1]
            zoom_factor = (zoom_y, zoom_x)
            
            resampled = zoom(values, zoom_factor, order=1, mode='constant', cval=np.nan)
            print(f"  Resampled to: {resampled.shape[1]} x {resampled.shape[0]} pixels (~{target_km}km)")
            return resampled
        except:
            print(f"  (scipy not available, using PIL resize)")
            # Fallback: use PIL
            from PIL import Image as PILImage
            
            # Create temp image for resizing
            mask = ~np.isnan(values)
            temp_data = np.nan_to_num(values, nan=0)
            temp_img = PILImage.fromarray((temp_data * 255 / np.nanmax(temp_data)).astype(np.uint8))
            temp_resized = temp_img.resize((target_width, target_height), PILImage.BILINEAR)
            resampled = np.array(temp_resized) / 255 * np.nanmax(temp_data)
            resampled[np.array(temp_resized) == 0] = np.nan
            
            return resampled
    except Exception as e:
        print(f"  ⚠ Resampling failed: {e}")
        return values

def calculate_fish_likelihood(temp, salinity, chlorophyll=None, mixed_layer=None):
    """
    Calculate composite fish likelihood index (0-100) based on environmental parameters.
    
    Uses ideal parameter ranges for North Atlantic fish species.
    """
    likelihood = np.ones_like(temp, dtype=np.float32) * 50  # Base score
    
    # Temperature preference (ideal 12-18°C)
    temp_score = np.zeros_like(temp)
    mask_ideal_temp = (temp >= 12) & (temp <= 18)
    mask_acceptable_temp = (temp >= 8) & (temp <= 22)
    
    temp_score[mask_ideal_temp] = 100
    temp_score[mask_acceptable_temp & ~mask_ideal_temp] = 60
    temp_score[~mask_acceptable_temp & (temp >= 0)] = 30
    
    # Salinity preference (ideal 34.8-35.2 PSU)
    salinity_score = np.zeros_like(salinity)
    mask_ideal_sal = (salinity >= 34.8) & (salinity <= 35.2)
    mask_acceptable_sal = (salinity >= 34.5) & (salinity <= 35.5)
    
    salinity_score[mask_ideal_sal] = 100
    salinity_score[mask_acceptable_sal & ~mask_ideal_sal] = 70
    salinity_score[~mask_acceptable_sal & (salinity >= 34)] = 40
    
    # Combined score
    likelihood = (temp_score * 0.4 + salinity_score * 0.4)
    
    # Add chlorophyll if available (food availability)
    if chlorophyll is not None:
        chl_score = np.zeros_like(chlorophyll)
        chl_score[(chlorophyll >= 1) & (chlorophyll <= 3)] = 100  # Ideal food
        chl_score[(chlorophyll >= 0.5) & (chlorophyll <= 5)] = 70   # Acceptable
        chl_score[(chlorophyll > 0)] = 40                           # Present but suboptimal
        likelihood = likelihood * 0.6 + chl_score * 0.4
    
    # Add mixed layer depth if available (habitat structure)
    if mixed_layer is not None:
        mld_score = np.zeros_like(mixed_layer)
        mld_score[(mixed_layer >= 20) & (mixed_layer <= 80)] = 100  # Ideal depth
        mld_score[(mixed_layer >= 10) & (mixed_layer <= 150)] = 70   # Acceptable
        mld_score[(mixed_layer > 0)] = 50                            # Present
        if chlorophyll is not None:
            likelihood = likelihood * 0.7 + mld_score * 0.3
        else:
            likelihood = likelihood * 0.6 + mld_score * 0.4
    
    # Ensure values are in range
    likelihood = np.clip(likelihood, 0, 100)
    
    return likelihood

def download_dataset(dataset_name, force=False):
    """Download a Copernicus dataset"""
    if not HAS_COPERNICUS:
        print(f"Skipping {dataset_name}: copernicusmarine not available")
        return None
    
    config = DATASETS[dataset_name]
    nc_file = os.path.join(OUTPUT_DIR, f"{dataset_name}.nc")
    
    if os.path.exists(nc_file) and not force:
        print(f"✓ {dataset_name} already cached")
        return nc_file
    
    print(f"⏳ Downloading {dataset_name}...")
    
    try:
        # Use recent date for better data availability
        START_DATE = "2024-01-15T00:00:00"
        END_DATE = "2024-01-15T00:00:00"
        
        print(f"  Dataset ID: {config['id']}")
        print(f"  Variables: {config['vars']}")
        
        copernicusmarine.subset(
            dataset_id=config["id"],
            variables=config["vars"],
            minimum_longitude=MIN_LON,
            maximum_longitude=MAX_LON,
            minimum_latitude=MIN_LAT,
            maximum_latitude=MAX_LAT,
            start_datetime=START_DATE,
            end_datetime=END_DATE,
            output_filename=nc_file
        )
        print(f"✓ Downloaded {dataset_name}")
        return nc_file
    except Exception as e:
        print(f"✗ Failed to download {dataset_name}: {e}")
        print(f"  Hint: Check dataset ID and variable names at")
        print(f"  https://data.marine.copernicus.eu/")
        return None

def generate_sample_data(dataset_name, output_prefix=""):
    """Generate synthetic data for testing when Copernicus download fails"""
    config = DATASETS[dataset_name]
    
    print(f"  Generating sample data for {dataset_name}...")
    
    try:
        # Create synthetic data grid
        lons = np.linspace(MIN_LON, MAX_LON, 50)
        lats = np.linspace(MIN_LAT, MAX_LAT, 50)
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        
        # Generate synthetic but realistic data
        np.random.seed(42 + hash(dataset_name) % 1000)
        
        if "temperature" in dataset_name.lower():
            # Temperature: north to south gradient + noise
            values = 8 + (lat_grid - MIN_LAT) * 0.3 + np.random.normal(0, 1, lon_grid.shape)
        elif "salinity" in dataset_name.lower():
            # Salinity: coastal variation
            values = 34.5 + (lon_grid - MIN_LON) * 0.05 + np.random.normal(0, 0.1, lon_grid.shape)
        elif "mixed" in dataset_name.lower():
            # Mixed layer: varies with latitude
            values = 50 + (lat_grid - MIN_LAT) * 4 + np.random.normal(0, 10, lon_grid.shape)
        else:
            # Default: random values
            values = np.random.uniform(config["min"], config["max"], lon_grid.shape)
        
        # Apply ocean mask (simple: all water for now)
        values = np.clip(values, config["min"], config["max"])
        
        # Apply land masking using helper function
        values = apply_ocean_mask(values, lons, lats)
        
        # Normalize to 0-255, handling NaN for transparency
        vmin, vmax = config["min"], config["max"]
        norm = Normalize(vmin=vmin, vmax=vmax, clip=True)
        normalized = (norm(values) * 255).astype(np.uint8)
        
        # Create RGBA image with colormap
        cmap = plt.get_cmap(config["cmap"])
        rgba = cmap(normalized / 255.0)
        img_array = (rgba[:, :, :3] * 255).astype(np.uint8)
        
        # Create alpha channel: transparent where data is NaN (land)
        alpha = np.ones((values.shape[0], values.shape[1]), dtype=np.uint8) * 255
        alpha[np.isnan(values)] = 0  # Transparent on land
        
        # Prepare for Leaflet (flip if needed for proper georeferencing)
        img_array, alpha = prepare_image_for_leaflet(img_array, alpha, lats)
        
        # Convert to RGBA image
        rgba_img = np.dstack([img_array, alpha])
        img = Image.fromarray(rgba_img, 'RGBA')
        
        # Save PNG
        png_file = os.path.join(OUTPUT_DIR, f"{dataset_name}_layer.png")
        img.save(png_file)
        
        # Save bounds metadata
        bounds_file = os.path.join(OUTPUT_DIR, f"{dataset_name}_bounds.json")
        bounds_data = {
            "bounds": [[MIN_LAT, MIN_LON], [MAX_LAT, MAX_LON]],
            "dataset": dataset_name,
            "label": config["label"] + " (sample)",
            "cmap": config["cmap"],
            "opacity": 0.7,
            "min": vmin,
            "max": vmax
        }
        with open(bounds_file, "w") as f:
            json.dump(bounds_data, f)
        
        print(f"✓ Generated sample {png_file}")
        return png_file, bounds_file
        
    except Exception as e:
        print(f"✗ Error generating sample: {e}")
        return None, None


def generate_composite_index():
    """Reads processed layers, aligns them, and calculates the final fish index."""
    print("\n🐟 Calculating Composite Fish Likelihood Index...")
    
    loaded_data = {}
    base_lons = np.linspace(MIN_LON, MAX_LON, 200) # Standard high-res grid
    base_lats = np.linspace(MIN_LAT, MAX_LAT, 200)
    
    # 1. Load and align all downloaded/sample datasets
    for dataset_name in DATASETS.keys():
        nc_file = os.path.join(OUTPUT_DIR, f"{dataset_name}.nc")
        if os.path.exists(nc_file) and not USE_SAMPLE_ONLY:
            try:
                ds = xr.open_dataset(nc_file)
                var_name = DATASETS[dataset_name]["vars"][0]
                data = ds[var_name].isel(time=0) if "time" in ds[var_name].dims else ds[var_name]
                
                # Resample to standard grid to ensure perfectly matching arrays
                data_interp = data.interp(
                    latitude=base_lats, 
                    longitude=base_lons, 
                    method="linear"
                ).values
                loaded_data[dataset_name] = data_interp
            except Exception as e:
                print(f"  ⚠ Failed to load real data for {dataset_name}, falling back to sample logic.")
        
        # Fallback to generating a standard grid sample if NC fails or in sample mode
        if dataset_name not in loaded_data:
            lon_grid, lat_grid = np.meshgrid(base_lons, base_lats)
            config = DATASETS[dataset_name]
            if "temperature" in dataset_name: val = 8 + (lat_grid - MIN_LAT) * 0.3
            elif "salinity" in dataset_name: val = 34.5 + (lon_grid - MIN_LON) * 0.05
            elif "mixed" in dataset_name: val = 50 + (lat_grid - MIN_LAT) * 4
            else: val = np.random.uniform(config["min"], config["max"], lon_grid.shape)
            loaded_data[dataset_name] = val

    # 2. Calculate the index using your existing function
    temp = loaded_data.get("temperature")
    salinity = loaded_data.get("salinity")
    chlorophyll = loaded_data.get("chlorophyll")
    mixed_layer = loaded_data.get("mixed_layer")
    
    index_values = calculate_fish_likelihood(temp, salinity, chlorophyll, mixed_layer)
    
    # 3. Apply Land Mask and output as PNG
    index_values = apply_ocean_mask(index_values, base_lons, base_lats)
    
    # Create Colormap matching your Leaflet config (RdYlGn)
    norm = Normalize(vmin=0, vmax=100, clip=True)
    normalized = (norm(index_values) * 255).astype(np.uint8)
    cmap = plt.get_cmap("RdYlGn")
    rgba = cmap(normalized / 255.0)
    
    img_array = (rgba[:, :, :3] * 255).astype(np.uint8)
    alpha = np.ones_like(index_values, dtype=np.uint8) * 255
    alpha[np.isnan(index_values)] = 0
    
    img_array, alpha = prepare_image_for_leaflet(img_array, alpha, base_lats)
    rgba_img = np.dstack([img_array, alpha])
    
    # Save files
    png_file = os.path.join(OUTPUT_DIR, "fish_index_layer.png")
    Image.fromarray(rgba_img, 'RGBA').save(png_file)
    
    bounds_file = os.path.join(OUTPUT_DIR, "fish_index_bounds.json")
    with open(bounds_file, "w") as f:
        json.dump({
            "bounds": [[MIN_LAT, MIN_LON], [MAX_LAT, MAX_LON]],
            "dataset": "fish_index",
            "label": "🐟 Fish Likelihood Index",
            "cmap": "RdYlGn",
            "opacity": 0.8,
            "min": 0, "max": 100
        }, f)
        
    print(f"✓ Generated Composite Index: {png_file}")
    import math

    # --- ADD THIS TO EXPORT HOVER DATA ---
    print("  Saving raw data grid for interactive hover...")
    
    # Helper to convert NaNs to None for valid JSON
    def clean_array(arr):
        if arr is None: return None
        # Round arrays to keep file size small
        rounded = np.round(arr, 2).tolist()
        return [[None if math.isnan(val) else val for val in row] for row in rounded]

    hover_data = {
        "lons": np.round(base_lons, 3).tolist(),
        "lats": np.round(base_lats, 3).tolist(), # Lats are stored bottom-to-top or top-to-bottom
        "data": {
            "temp": clean_array(loaded_data.get("temperature")),
            "salinity": clean_array(loaded_data.get("salinity")),
            "chl": clean_array(loaded_data.get("chlorophyll")),
            "mld": clean_array(loaded_data.get("mixed_layer")),
            "index": clean_array(index_values)
        }
    }
    
    with open(os.path.join(OUTPUT_DIR, "hover_data.json"), "w") as f:
        json.dump(hover_data, f)
    # ---------------------------------------
    return bounds_file





def process_to_geotiff(nc_file, dataset_name, output_prefix=""):
    """Convert NetCDF to GeoTIFF via PNG + bounds JSON"""
    config = DATASETS[dataset_name]
    
    try:
        ds = xr.open_dataset(nc_file)
        
        # Get coordinate names
        lat_name = "latitude" if "latitude" in ds.coords else "lat"
        lon_name = "longitude" if "longitude" in ds.coords else "lon"
        
        # Get variable (single variable per dataset)
        var_names = config["vars"]
        
        # Try first variable name
        var_name = var_names[0]
        if var_name not in ds.data_vars:
            # Fallback: list available variables
            available = list(ds.data_vars)
            if available:
                var_name = available[0]
                print(f"  → Using available variable: {var_name}")
            else:
                raise ValueError(f"No variables in dataset")
        
        data = ds[var_name]
        if "time" in data.dims:
            data = data.isel(time=0)
        
        lats = data[lat_name].values
        lons = data[lon_name].values
        values = data.values
        
        # Apply ocean mask
        values = apply_ocean_mask(values, lons, lats)
        
        # Apply percentile stretch if configured (improves pattern visibility)
        if config.get("stretch") == "percentile":
            values = apply_percentile_stretch(values, lower=2, upper=98)
            vmin, vmax = 0, 1  # Already normalized by stretch
            norm = Normalize(vmin=vmin, vmax=vmax, clip=True)
        else:
            vmin, vmax = config["min"], config["max"]
            norm = Normalize(vmin=vmin, vmax=vmax, clip=True)
        
        # Normalize to 0-255, handling NaN for transparent areas
        normalized = (norm(values) * 255).astype(np.uint8)
        
        # Create RGBA image with colormap
        cmap = plt.get_cmap(config["cmap"])
        rgba = cmap(normalized / 255.0)  # Returns RGBA (H, W, 4)
        img_array = (rgba[:, :, :3] * 255).astype(np.uint8)  # RGB only
        
        # Create alpha channel: transparent where data is NaN (land)
        alpha = np.ones((values.shape[0], values.shape[1]), dtype=np.uint8) * 255
        alpha[np.isnan(values)] = 0  # Transparent on land
        
        # Prepare for Leaflet (flip if needed for proper georeferencing)
        img_array, alpha = prepare_image_for_leaflet(img_array, alpha, lats)
        
        # Convert to RGBA image
        rgba_img = np.dstack([img_array, alpha])
        img = Image.fromarray(rgba_img, 'RGBA')
        
        # Save PNG
        png_file = os.path.join(OUTPUT_DIR, f"{dataset_name}_layer.png")
        img.save(png_file)
        
        # Save bounds metadata
        bounds_file = os.path.join(OUTPUT_DIR, f"{dataset_name}_bounds.json")
        bounds_data = {
            "bounds": [[MIN_LAT, MIN_LON], [MAX_LAT, MAX_LON]],
            "dataset": dataset_name,
            "label": config["label"],
            "cmap": config["cmap"],
            "opacity": config["opacity"],
            "min": vmin,
            "max": vmax
        }
        with open(bounds_file, "w") as f:
            json.dump(bounds_data, f)
        
        print(f"✓ Created {png_file}")
        return png_file, bounds_file
        
    except Exception as e:
        print(f"✗ Error processing {dataset_name}: {e}")
        return None, None

# ================================
# MAIN WORKFLOW
# ================================

print("\n🌊 Copernicus Fishing Likelihood Dashboard")
print("=" * 50)

# Check command-line arguments
USE_SAMPLE_ONLY = "--sample" in sys.argv or os.getenv("USE_SAMPLE_DATA") == "1"
if USE_SAMPLE_ONLY:
    print("📊 Sample data mode (no downloads)")
else:
    print("📊 Download mode (with sample fallback)")

# Login to Copernicus
if HAS_COPERNICUS and not USE_SAMPLE_ONLY:
    try:
        COPERNICUS_USER = os.getenv("COPERNICUS_USERNAME")
        COPERNICUS_PASS = os.getenv("COPERNICUS_PASSWORD")
        if COPERNICUS_USER and COPERNICUS_PASS:
            copernicusmarine.login(username=COPERNICUS_USER, password=COPERNICUS_PASS)
            print("✓ Logged in to Copernicus")
        else:
            print("⚠ No Copernicus credentials in .env")
    except Exception as e:
        print(f"⚠ Login error: {e}")

# Download and process datasets
layers_config = []
for dataset_name in DATASETS.keys():
    if USE_SAMPLE_ONLY:
        # Skip downloads, go straight to sample
        print(f"📊 Generating sample data for {dataset_name}...")
        png_file, bounds_file = generate_sample_data(dataset_name)
    else:
        nc_file = download_dataset(dataset_name)
        
        if nc_file:
            # Try to process downloaded NetCDF
            png_file, bounds_file = process_to_geotiff(nc_file, dataset_name)
        else:
            # Fallback: generate sample data
            print(f"⚠ Using sample data for {dataset_name}")
            png_file, bounds_file = generate_sample_data(dataset_name)
    
    if png_file and bounds_file:
        with open(bounds_file) as f:
            bounds_data = json.load(f)
            layers_config.append(bounds_data)




index_bounds_file = generate_composite_index()
with open(index_bounds_file) as f:
    layers_config.append(json.load(f))




# Save layers config for dashboard
config_file = os.path.join(OUTPUT_DIR, "layers.json")
with open(config_file, "w") as f:
    json.dump(layers_config, f, indent=2)

print(f"\n✓ Saved configuration to {config_file}")
print(f"✓ All data ready in {OUTPUT_DIR}/")
print("\nNext: Open index.html in browser to view dashboard")
print("\n" + "=" * 50)
print("Usage Tips:")
print("  python test.py              # Download real data (with fallback)")
print("  python test.py --sample     # Use sample data only (no downloads)")
print("  python discover_datasets.py # Find correct dataset IDs")
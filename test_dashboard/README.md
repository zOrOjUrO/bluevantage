# 🌊 Fishing Likelihood Dashboard - North Sea

Multi-layer interactive dashboard displaying Copernicus marine datasets relevant to fishing site prediction.

## Features

✅ **Multiple Datasets**
- Chlorophyll concentration (food indicator)
- Sea surface temperature (habitat preference)
- Ocean currents (fish migration)

✅ **Interactive Controls**
- Toggle layers on/off
- Adjust opacity per layer
- Real-time legend updates

✅ **Proper Rendering**
- Uses Leaflet.js for efficient tile-based map
- PNG image overlays with georeferencing
- Optimized for web performance

## Setup

### 1. Install Dependencies

```bash
pip install xarray netcdf4 matplotlib pillow python-dotenv
pip install copernicusmarine regionmask
```

### 2. Configure Copernicus Credentials

1. Sign up at: https://data.marine.copernicus.eu/
2. Copy `.env.example` to `.env`
3. Fill in your credentials

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Generate Data Layers

```bash
python test.py
```

This will:
- Download fishing-relevant datasets from Copernicus
- Process them into PNG layers with proper georeferencing
- Generate `data/layers.json` configuration

### 4. View Dashboard

Open `index.html` in your browser:

```bash
# On Windows:
start index.html

# Or use a local server (recommended):
python -m http.server 8000
# Then visit http://localhost:8000
```

## Architecture

### Backend (`test.py`)

- **Downloads**: Multiple Copernicus datasets (chlorophyll, temperature, currents)
- **Processing**: 
  - Applies ocean/land masking
  - Normalizes data to 0-255 range
  - Applies scientific colormaps
  - Exports as PNG + bounds JSON
- **Output**: `data/` folder with layers and configuration

### Frontend (`index.html`)

- **Map Engine**: Leaflet.js
- **Base Layer**: OpenStreetMap
- **Data Layers**: PNG overlays with proper georeferencing
- **Controls**: 
  - Layer visibility toggle
  - Opacity slider
  - Dynamic legend

## File Structure

```
test_dashboard/
├── test.py                 # Data processing pipeline
├── index.html              # Dashboard
├── .env                    # Credentials (create from .env.example)
├── .env.example            # Credentials template
└── data/                   # Generated output
    ├── chlorophyll_layer.png
    ├── chlorophyll_bounds.json
    ├── temperature_layer.png
    ├── temperature_bounds.json
    ├── current_layer.png
    ├── current_bounds.json
    └── layers.json         # Master config
```

## Datasets Used

| Dataset | Purpose | Variable | Unit |
|---------|---------|----------|------|
| Copernicus Colour | Food availability | Chlorophyll | mg/m³ |
| Copernicus Physics | Habitat preference | Temperature | °C |
| Copernicus Physics | Fish migration | Current speed | m/s |

## Troubleshooting

**Q: "layers.json not found"**
- Run `python test.py` first
- Check that `data/` folder exists

**Q: Images not appearing on map**
- Verify PNG files were created in `data/` folder
- Check browser console for CORS errors
- Use a local server instead of `file://` protocol

**Q: No Copernicus login warning**
- Add credentials to `.env` file
- Verify file is in same directory as `test.py`

**Q: Import errors**
- Run: `pip install -r requirements.txt` (if available)
- Or install manually: `pip install xarray matplotlib pillow copernicusmarine`

## Customization

### Add New Datasets

Edit `DATASETS` dictionary in `test.py`:

```python
DATASETS = {
    "new_dataset": {
        "id": "cmems_dataset_id",
        "vars": ["variable_name"],
        "cmap": "viridis",
        "label": "My Dataset (unit)",
        "min": 0, "max": 100
    }
}
```

### Change Region

Edit North Sea bounds:

```python
MIN_LON, MAX_LON = -4, 10      # Longitude range
MIN_LAT, MAX_LAT = 51, 59      # Latitude range
```

### Adjust Colormap

Choose from matplotlib: `viridis`, `plasma`, `YlGn`, `RdYlBu_r`, etc.

## References

- 🔗 [Copernicus Marine Data](https://data.marine.copernicus.eu/)
- 🔗 [Leaflet.js Documentation](https://leafletjs.com/)
- 🔗 [xarray Documentation](https://xarray.pydata.org/)
- 🔗 [regionmask Documentation](https://regionmask.readthedocs.io/)

## License

Data sourced from Copernicus Marine Service - follow their licensing terms.

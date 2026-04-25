#!/usr/bin/env python3
"""
Discover available Copernicus Marine datasets and variables
Helps find correct dataset IDs and variable names for your region
"""

import os
from dotenv import load_dotenv

try:
    import copernicusmarine
except ImportError:
    print("Error: copernicusmarine not installed")
    print("Run: pip install copernicusmarine")
    exit(1)

# ================================
# CONFIGURATION
# ================================
load_dotenv()

COPERNICUS_USER = os.getenv("COPERNICUS_USERNAME")
COPERNICUS_PASS = os.getenv("COPERNICUS_PASSWORD")

# Login if credentials available
if COPERNICUS_USER and COPERNICUS_PASS:
    try:
        copernicusmarine.login(username=COPERNICUS_USER, password=COPERNICUS_PASS)
        print("✓ Logged in to Copernicus\n")
    except:
        print("⚠ Could not login (proceeding with public datasets)\n")

# North Sea boundaries
MIN_LON, MAX_LON = -4, 10
MIN_LAT, MAX_LAT = 51, 59

# ================================
# COMMON DATASETS TO TRY
# ================================
CANDIDATE_DATASETS = [
    # Physics models (temperature, currents, etc.)
    "cmems_mod_glo_phy_anfc_0.083deg_P1D-m",
    "cmems_mod_glo_phy_anfc_merged-uv_0.083deg_P1D-m",
    "cmems_mod_glo_phy_anfc_merged-uv_0.25deg_P1D-m",
    "GLOBAL_ANALYSIS_FORECAST_PHY_001_024",
    
    # Biogeochemistry (chlorophyll, nutrients, etc.)
    "cmems_mod_glo_bgc_anfc_0.25deg_P1D-m",
    "GLOBAL_ANALYSIS_FORECAST_BIO_001_014",
    
    # Ocean color / Chlorophyll (satellite)
    "cmems_obs_oc_nrt_glo_0deg25_nrt_chunk",
    "cmems_obs_oc_nrt_glo_0.25deg_nrt_chunk",
    "OCEANCOLOUR_NWEU_CHL_L4_NRT",
    
    # Wave models
    "cmems_mod_glo_wav_anfc_0.2deg_PT3H-m",
]

# ================================
# MAIN DISCOVERY
# ================================
def test_dataset(dataset_id):
    """Try to access dataset info"""
    try:
        print(f"\n📊 Testing: {dataset_id}")
        print("-" * 60)
        
        # Try metadata request
        info = copernicusmarine.describe(
            dataset_id=dataset_id,
            minimum_longitude=MIN_LON,
            maximum_longitude=MAX_LON,
            minimum_latitude=MIN_LAT,
            maximum_latitude=MAX_LAT,
        )
        
        # Show dataset info
        print(f"  ✓ Dataset found")
        
        # Try to get dimensions/variables
        try:
            subset_preview = copernicusmarine.describe(
                dataset_id=dataset_id,
                minimum_longitude=MIN_LON,
                maximum_longitude=MAX_LON,
                minimum_latitude=MIN_LAT,
                maximum_latitude=MAX_LAT,
                start_datetime="2024-01-01T00:00:00",
                end_datetime="2024-01-01T00:00:00",
            )
            print(f"  Supports time subsetting ✓")
        except:
            print(f"  Time subsetting may be limited")
        
        return True
        
    except Exception as e:
        print(f"  ✗ {str(e)[:80]}")
        return False

# ================================
# RECOMMENDED DATASETS
# ================================
print("\n🌊 Copernicus Marine Dataset Discovery Tool")
print("=" * 60)
print(f"Region: North Sea [{MIN_LAT}°N-{MAX_LAT}°N, {MIN_LON}°E-{MAX_LON}°E]\n")

print("Testing commonly available datasets...\n")

working = []
for dataset_id in CANDIDATE_DATASETS:
    if test_dataset(dataset_id):
        working.append(dataset_id)

if working:
    print("\n" + "=" * 60)
    print("✓ WORKING DATASETS:\n")
    for i, ds in enumerate(working, 1):
        print(f"  {i}. {ds}")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:\n")
    print("1. Pick a dataset ID from above")
    print("2. Use this command to see available variables:\n")
    print(f"   python -c \"import copernicusmarine; ")
    print(f"   copernicusmarine.describe(dataset_id='[ID]')\"")
    print("\n3. Update DATASETS in test.py with correct IDs and variable names\n")
else:
    print("\n" + "=" * 60)
    print("⚠ No datasets found")
    print("\nTroubleshooting:")
    print("• Check internet connection")
    print("• Verify credentials in .env file")
    print("• Visit: https://data.marine.copernicus.eu/")
    print("\n")

print("=" * 60)

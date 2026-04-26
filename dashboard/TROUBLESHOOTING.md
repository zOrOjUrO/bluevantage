# Troubleshooting Guide

## Error: "Dataset ID not found"

**Cause:** The dataset ID in `test.py` is outdated or incorrect.

**Fix:**
1. Run the discovery script to find working dataset IDs:
   ```bash
   python discover_datasets.py
   ```

2. Copy a working dataset ID from the output

3. Update `DATASETS` dictionary in `test.py`:
   ```python
   DATASETS = {
       "temperature": {
           "id": "[CORRECT_ID_HERE]",  # Replace with working ID
           "vars": ["variable_name"],   # Get this from Copernicus website
           "cmap": "RdYlBu_r",
           "label": "Temperature (°C)",
           "min": 0, "max": 25
       }
   }
   ```

---

## Error: "The variable 'thetao' is neither a variable..."

**Cause:** Variable name doesn't exist in that dataset.

**Fix:**
1. Check Copernicus Marine website: https://data.marine.copernicus.eu/
2. Search for the dataset ID
3. See "Variables" section for correct names
4. Update `DATASETS["vars"]` list in `test.py`

Example: If dataset has `sea_water_temperature`, use:
```python
"vars": ["sea_water_temperature"],
```

---

## Error: "cmems_obs_oc_nrt_glo_0deg25_nrt_chunk not found"

**Cause:** Chlorophyll dataset ID changed. Satellite data products are frequently updated.

**Fix:** Use alternative approaches:

**Option A: Use Physics Model (has temperature)**
```python
"temperature": {
    "id": "cmems_mod_glo_phy_anfc_0.083deg_P1D-m",
    "vars": ["sea_water_temperature"],
    "cmap": "RdYlBu_r",
    "label": "Sea Surface Temperature (°C)",
    "min": 0, "max": 25
}
```

**Option B: Find current satellite dataset**
- Visit https://data.marine.copernicus.eu/
- Search for "ocean color" or "chlorophyll"
- Copy the current dataset ID

**Option C: Use sample data**
```bash
python test.py --sample
```

---

## Solution: Use Sample Data First

If you're having trouble finding correct datasets, start with sample data:

```bash
python test.py --sample
```

This generates realistic synthetic data so you can:
- Test the dashboard interface
- Verify HTML/frontend is working
- Get familiar with the system

Then later, update with real Copernicus data.

---

## Quick Fix: Working Dataset Configuration

Here's a configuration that's likely to work (as of 2026):

```python
DATASETS = {
    "temperature": {
        "id": "cmems_mod_glo_phy_anfc_0.083deg_P1D-m",
        "vars": ["sea_water_temperature"],
        "cmap": "RdYlBu_r",
        "label": "Sea Surface Temperature (°C)",
        "min": 0, "max": 25
    },
    "salinity": {
        "id": "cmems_mod_glo_phy-sal_anfc_0.083deg_P1D-m",
        "vars": ["sea_water_salinity"],
        "cmap": "Blues",
        "label": "Salinity (PSU)",
        "min": 34, "max": 35.5
    }
}
```

---

## Manual Variable Discovery

If `discover_datasets.py` doesn't work, try this Python command:

```python
import copernicusmarine
from dotenv import load_dotenv

load_dotenv()
info = copernicusmarine.describe(
    dataset_id="cmems_mod_glo_phy_anfc_0.083deg_P1D-m",
    minimum_longitude=-4,
    maximum_longitude=10,
    minimum_latitude=51,
    maximum_latitude=59,
)
print(info)
```

Look for the list of available variables in the output.

---

## Still Having Issues?

1. **Check credentials:**
   ```bash
   python setup_check.py
   ```

2. **Verify internet connection:**
   ```bash
   ping data.marine.copernicus.eu
   ```

3. **Use the dashboard with sample data:**
   ```bash
   python test.py --sample
   ```
   Then work on fixing Copernicus integration later

4. **Check the Copernicus website directly:**
   - https://data.marine.copernicus.eu/
   - Verify datasets are available in your region
   - Check dataset version dates
   - Ensure credentials are correct

5. **Review browser console for errors:**
   - Press F12 while viewing `index.html`
   - Look for error messages in Console tab
   - Check Network tab for failed requests

---

## Success Indicators

✓ `python test.py` runs without hanging  
✓ `data/layers.json` file is created  
✓ PNG files appear in `data/` folder  
✓ Opening `index.html` shows map with layers  
✓ Layer toggle buttons work  
✓ Opacity slider adjusts visibility

If you see all of these, you're good!

#!/usr/bin/env python3
"""
Test regionmask to see if it's correctly identifying ocean vs land
"""
import numpy as np

try:
    import regionmask
    print("✓ regionmask imported")
except:
    print("✗ regionmask not available")
    exit(1)

# Config
MIN_LON, MAX_LON = -4, 10
MIN_LAT, MAX_LAT = 51, 59

# Create grid
lons = np.linspace(MIN_LON, MAX_LON, 50)
lats = np.linspace(MIN_LAT, MAX_LAT, 50)
lon_grid, lat_grid = np.meshgrid(lons, lats)

print("\n🗺️ Testing regionmask land detection")
print("=" * 60)

try:
    land = regionmask.defined_regions.natural_earth_v5_0_0.land_110
    land_mask = land.mask(lon_grid, lat_grid)
    
    print(f"\nLand mask shape: {land_mask.shape}")
    print(f"Land mask dtype: {land_mask.dtype}")
    print(f"NaN values in mask (ocean): {np.isnan(land_mask).sum()}")
    print(f"Non-NaN values in mask (land): {(~np.isnan(land_mask)).sum()}")
    
    # Check specific corners
    print("\n📍 Corner analysis:")
    corners = [
        ("Top-left (59N, -4E - North Sea)", -1, 0),
        ("Top-right (59N, 10E - Norway)", -1, -1),
        ("Bottom-left (51N, -4E - Ireland)", 0, 0),
        ("Bottom-right (51N, 10E - North Sea)", 0, -1),
    ]
    
    for desc, row, col in corners:
        lat_val = lat_grid[row, col]
        lon_val = lon_grid[row, col]
        mask_val = land_mask[row, col]
        is_ocean = np.isnan(mask_val)
        print(f"\n  {desc}")
        print(f"    Coords: ({lat_val:.1f}°N, {lon_val:.1f}°E)")
        print(f"    Mask value: {mask_val}")
        print(f"    Detected as: {'OCEAN ✓' if is_ocean else 'LAND ✗'}")
        
        # Manual check
        if -4 <= lon_val <= -2 and 51 <= lat_val <= 52:
            expected = "LAND"
        elif lon_val >= 8 and lat_val >= 58:
            expected = "LAND"
        else:
            expected = "OCEAN"
        
        correct = "✓" if (expected == "OCEAN") == is_ocean else "✗"
        print(f"    Expected: {expected} {correct}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

#!/usr/bin/env python3
"""
Test different meshgrid orientations to fix georeferencing
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from PIL import Image

print("🔬 Testing Meshgrid Orientations")
print("=" * 60)

# Config
MIN_LON, MAX_LON = -4, 10
MIN_LAT, MAX_LAT = 51, 59

# Create grids
lons = np.linspace(MIN_LON, MAX_LON, 50)
lats = np.linspace(MIN_LAT, MAX_LAT, 50)

# Current approach
lon_grid, lat_grid = np.meshgrid(lons, lats)
print(f"\nCurrent meshgrid(lons, lats):")
print(f"  lon_grid.shape: {lon_grid.shape}")
print(f"  lat_grid.shape: {lat_grid.shape}")
print(f"  lon_grid[0, 0]={lon_grid[0,0]:.1f}, lat_grid[0,0]={lat_grid[0,0]:.1f}")
print(f"  lon_grid[0,-1]={lon_grid[0,-1]:.1f}, lat_grid[0,-1]={lat_grid[0,-1]:.1f}")
print(f"  lon_grid[-1,0]={lon_grid[-1,0]:.1f}, lat_grid[-1,0]={lat_grid[-1,0]:.1f}")
print(f"  lon_grid[-1,-1]={lon_grid[-1,-1]:.1f}, lat_grid[-1,-1]={lat_grid[-1,-1]:.1f}")

# Alternative approach
lat_grid_alt, lon_grid_alt = np.meshgrid(lats, lons)
print(f"\nAlternative meshgrid(lats, lons):")
print(f"  lon_grid.shape: {lon_grid_alt.shape}")
print(f"  lat_grid.shape: {lat_grid_alt.shape}")
print(f"  lon_grid[0, 0]={lon_grid_alt[0,0]:.1f}, lat_grid[0,0]={lat_grid_alt[0,0]:.1f}")
print(f"  lon_grid[0,-1]={lon_grid_alt[0,-1]:.1f}, lat_grid[0,-1]={lat_grid_alt[0,-1]:.1f}")
print(f"  lon_grid[-1,0]={lon_grid_alt[-1,0]:.1f}, lat_grid[-1,0]={lat_grid_alt[-1,0]:.1f}")
print(f"  lon_grid[-1,-1]={lon_grid_alt[-1,-1]:.1f}, lat_grid[-1,-1]={lat_grid_alt[-1,-1]:.1f}")

print("\n" + "=" * 60)
print("Analysis:")
print("For image coordinates after flip:")
print("  [0,0] (top-left) should be (59°N, -4°E) = North Sea west")
print("  [0,-1] (top-right) should be (59°N, 10°E) = Norway")
print("  [-1,0] (bottom-left) should be (51°N, -4°E) = Ireland west")
print("  [-1,-1] (bottom-right) should be (51°N, 10°E) = Southern North Sea")

print("\nCurrent approach after flipud:")
print(f"  [0,0]: lat={lat_grid[-1,0]:.1f}, lon={lon_grid[-1,0]:.1f} ✓")
print(f"  [0,-1]: lat={lat_grid[-1,-1]:.1f}, lon={lon_grid[-1,-1]:.1f} ✓")
print(f"  [-1,0]: lat={lat_grid[0,0]:.1f}, lon={lon_grid[0,0]:.1f} ✓")
print(f"  [-1,-1]: lat={lat_grid[0,-1]:.1f}, lon={lon_grid[0,-1]:.1f} {'✓' if lat_grid[0,-1]==51 else '✗'}")

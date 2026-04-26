#!/usr/bin/env python3
"""
Debug script to verify coordinate system and georeferencing
"""
import json
import os
import numpy as np
from PIL import Image

print("🔍 Coordinate System Debug")
print("=" * 60)

# Check layers.json
if os.path.exists('data/layers.json'):
    with open('data/layers.json') as f:
        layers = json.load(f)
    
    print("\n📍 Bounds in configuration:")
    for layer in layers:
        bounds = layer['bounds']
        print(f"\n  {layer['dataset']}:")
        print(f"    Southwest: lat={bounds[0][0]}°, lon={bounds[0][1]}°")
        print(f"    Northeast: lat={bounds[1][0]}°, lon={bounds[1][1]}°")
        print(f"    Region: {bounds[0][1]}°E to {bounds[1][1]}°E, {bounds[0][0]}°N to {bounds[1][0]}°N")

# Check PNG files
print("\n\n📊 PNG Image Properties:")
png_files = [f for f in os.listdir('data') if f.endswith('_layer.png')]
for png_file in sorted(png_files):
    img = Image.open(f'data/{png_file}')
    print(f"\n  {png_file}:")
    print(f"    Format: {img.format}")
    print(f"    Mode: {img.mode} (should be RGBA for transparency)")
    print(f"    Size: {img.size[0]}x{img.size[1]} pixels")
    
    # Check for transparency
    if img.mode == 'RGBA':
        alpha = np.array(img.split()[-1])
        opaque = (alpha == 255).sum()
        transparent = (alpha < 255).sum()
        print(f"    Opaque pixels: {opaque} ({100*opaque/alpha.size:.1f}%)")
        print(f"    Transparent pixels: {transparent} ({100*transparent/alpha.size:.1f}%)")

print("\n\n✅ Verification Complete")
print("=" * 60)
print("\nNotes:")
print("  • Region should be around UK/North Sea (roughly 51-59°N, -4 to +10°E)")
print("  • PNG mode should be RGBA for land masking to work")
print("  • Transparent pixels should be significant (land areas)")
print("\nIf coordinates look wrong, the issue is in:")
print("  - Bounds calculation")
print("  - Leaflet bounds parameter format")
print("  - Image orientation (north/south)")

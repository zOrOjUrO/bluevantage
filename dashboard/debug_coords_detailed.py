#!/usr/bin/env python3
"""
Detailed coordinate debugging - visualize where pixels end up
"""
import numpy as np
from PIL import Image
import json
import os

print("🗺️ Coordinate Placement Debug")
print("=" * 60)

# Expected region for North Sea
print("\n📍 Expected Region (North Sea):")
print("  Latitude:  51°N to 59°N (south to north)")
print("  Longitude: -4°E to 10°E (west to east)")
print("  SW Corner: (51°N, -4°E)  - Ireland/UK west coast")
print("  NE Corner: (59°N, 10°E)  - Norway")
print("  UK roughly at: (52-54°N, -2 to 2°E)")

# Check what's in the layers.json
with open('data/layers.json') as f:
    layers = json.load(f)

print("\n📊 Bounds in layers.json:")
for layer in layers[:1]:  # Just check first layer
    bounds = layer['bounds']
    print(f"\n  Layer: {layer['dataset']}")
    print(f"  Bounds parameter: {bounds}")
    print(f"  → Leaflet receives: [[{bounds[0][0]}, {bounds[0][1]}], [{bounds[1][0]}, {bounds[1][1]}]]")
    print(f"  → This maps to: SW=({bounds[0][0]}°N, {bounds[0][1]}°E), NE=({bounds[1][0]}°N, {bounds[1][1]}°E)")

# Check temperature PNG for clues
print("\n📸 Temperature PNG structure:")
img = Image.open('data/temperature_layer.png')
print(f"  Size: {img.size} (width x height)")
print(f"  Mode: {img.mode}")

# Sample pixel locations in the image
alpha = np.array(img.split()[-1])
print(f"\n  Transparency map (0=transparent/land, 255=opaque/ocean):")
print(f"    Top-left corner:     alpha={alpha[0, 0]} (should be land - UK area)")
print(f"    Top-right corner:    alpha={alpha[0, -1]} (should be sea)")
print(f"    Bottom-left corner:  alpha={alpha[-1, 0]} (should be sea)")
print(f"    Bottom-right corner: alpha={alpha[-1, -1]} (should be sea)")

# If using flipped image
print(f"\n  ✓ Image was flipped for proper N/S orientation")
print(f"  (First row = North, Last row = South)")

print("\n" + "=" * 60)
print("\n🔧 Troubleshooting:")
print("  If values appear on UK land:")
print("    → Image might be flipped horizontally (need to mirror W/E)")
print("    → Or flipped vertically (need to check lat order)")
print("    → Or bounds might need [[N, W], [S, E]] instead of [[S, W], [N, E]]")
print("\n  If sea areas have no data:")
print("    → Land mask is too aggressive")
print("    → Or land mask is backwards")
print("\n  Next step: Check browser console (F12) for error messages")

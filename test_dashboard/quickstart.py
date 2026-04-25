#!/usr/bin/env python3
"""
Quick start - generates dashboard with sample data in seconds
"""
import subprocess
import sys
import os

print("🌊 Fishing Likelihood Dashboard - Quick Start")
print("=" * 60)

# Step 1: Check dependencies
print("\n1️⃣  Checking dependencies...")
try:
    import numpy
    import matplotlib
    from PIL import Image
    print("   ✓ Core dependencies found")
except ImportError:
    print("   ⚠ Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])
    print("   ✓ Dependencies installed")

# Step 2: Generate sample data
print("\n2️⃣  Generating sample dashboard data...")
try:
    subprocess.check_call([sys.executable, "test.py", "--sample"], cwd=os.path.dirname(__file__) or ".")
    print("\n   ✓ Dashboard data generated!")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Step 3: Show how to view
print("\n3️⃣  View your dashboard:")
print("   Option A - Use Python server (recommended):")
print("      python -m http.server 8000")
print("      Then open: http://localhost:8000")
print()
print("   Option B - Open directly:")
print("      index.html  (in this folder)")
print()
print("=" * 60)
print("\n✅ Dashboard ready! Sample data is loaded.")
print("\nNext: To use real Copernicus data:")
print("  • Run: python discover_datasets.py")
print("  • Update DATASETS in test.py with correct IDs")
print("  • Run: python test.py")

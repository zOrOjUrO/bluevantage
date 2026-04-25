#!/usr/bin/env python3
"""
Setup verification script for Fishing Likelihood Dashboard
Checks dependencies, credentials, and file structure
"""

import os
import sys
from pathlib import Path

def check_python_version():
    """Verify Python 3.8+"""
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 8):
        print(f"❌ Python 3.8+ required (current: {v.major}.{v.minor}.{v.micro})")
        return False
    print(f"✓ Python {v.major}.{v.minor}.{v.micro}")
    return True

def check_dependencies():
    """Check installed packages"""
    required = [
        'xarray', 'numpy', 'matplotlib', 'PIL',
        'dotenv', 'copernicusmarine', 'regionmask'
    ]
    
    missing = []
    for pkg in required:
        try:
            if pkg == 'PIL':
                __import__('PIL')
            elif pkg == 'dotenv':
                __import__('dotenv')
            else:
                __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print(f"   Run: pip install -r requirements.txt")
        return False
    print("✓ All dependencies installed")
    return True

def check_credentials():
    """Check .env file"""
    if not os.path.exists('.env'):
        print("⚠ .env file not found")
        print("   Copy .env.example → .env and add credentials")
        return False
    
    with open('.env') as f:
        content = f.read()
        has_user = 'COPERNICUS_USERNAME' in content and 'your_username' not in content
        has_pass = 'COPERNICUS_PASSWORD' in content and 'your_password' not in content
    
    if has_user and has_pass:
        print("✓ Credentials configured")
        return True
    else:
        print("⚠ Credentials not set (optional - some datasets work anonymously)")
        return True

def check_structure():
    """Check directory structure"""
    if not Path('data').exists():
        Path('data').mkdir(exist_ok=True)
    
    print("✓ data/ directory ready")
    return True

def check_html():
    """Check HTML file"""
    if os.path.exists('index.html'):
        print("✓ index.html found")
        return True
    else:
        print("❌ index.html not found")
        return False

# ================================
# MAIN
# ================================
def main():
    print("\n🌊 Fishing Likelihood Dashboard - Setup Check")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Credentials", check_credentials),
        ("Directory Structure", check_structure),
        ("HTML Dashboard", check_html),
    ]
    
    results = []
    for name, check_fn in checks:
        print(f"\n{name}:")
        try:
            result = check_fn()
            results.append(result)
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    if all(results):
        print("✅ Setup complete! Ready to run:\n   python test.py")
    else:
        print("⚠ Some checks failed. Review above.")
    print()

if __name__ == '__main__':
    main()

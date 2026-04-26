import os
import sys
from pathlib import Path
import subprocess

def ensure_packages(packages):
    missing = []
    for pkg_name, import_name in packages:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg_name)
    
    if missing:
        print(f"Installing missing packages: {missing}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q"] + missing)
    else:
        print("All required packages are already installed.")

def setup_environment():
    DATA_DIR = Path("data")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "models").mkdir(exist_ok=True)
    
    packages = [
        ("xgboost", "xgboost"),
        ("scikit-learn", "sklearn"),
        ("h3", "h3"),
        ("geopandas", "geopandas"),
        ("shapely", "shapely"),
        ("scipy", "scipy"),
        ("requests", "requests"),
        ("joblib", "joblib"),
        ("python-dotenv", "dotenv")
    ]
    ensure_packages(packages)
    print(f"Environment setup complete. Data directory: {DATA_DIR.resolve()}")

if __name__ == "__main__":
    setup_environment()

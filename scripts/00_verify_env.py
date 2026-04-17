# scripts/00_verify_env.py
import sys

REQUIRED = [
    "rasterio", "geopandas", "pandas", "numpy", "scipy",
    "matplotlib", "seaborn", "sklearn", "pylandstats",
    "shapely", "xarray", "rioxarray", "contextily",
    "statsmodels", "streamlit", "networkx", "pwlf"
]

failed = []
for pkg in REQUIRED:
    try:
        __import__(pkg)
        print(f"  ✅ {pkg}")
    except ImportError:
        print(f"  ❌ {pkg} — MISSING")
        failed.append(pkg)

if failed:
    sys.exit(f"\nABORT: Install missing packages: {failed}")

# Verify raw data files exist
import os
RAW = "data/raw"
REQUIRED_FILES = [
    "treecover2000.tif",
    "lossyear.tif",
    "ESA_WorldCover_2021.tif",
    "andaman_islands.gpkg"
]
for f in REQUIRED_FILES:
    path = os.path.join(RAW, f)
    exists = os.path.exists(path)
    print(f"  {'✅' if exists else '❌'} {path}")
    if not exists:
        failed.append(path)

if failed:
    sys.exit(f"\nABORT: Missing raw files: {failed}")

print("\n✅ All checks passed. Proceed to Phase 0.")

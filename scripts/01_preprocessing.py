# scripts/01_preprocessing.py
"""
Phase 1: Reproject rasters, create annual binary forest masks.
Output: data/processed/forest_masks/forest_mask_{YYYY}.tif  (24 files)
CRS: EPSG:32646 (UTM Zone 46N)
Values: 1=forest, 0=non-forest, 255=NoData (ocean/outside)
"""

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.windows import Window
import os

RAW = "data/raw"
OUT = "data/processed/forest_masks"
TARGET_CRS = CRS.from_epsg(32646)
TREE_THRESH = 30          # Hansen tree cover threshold (%)
NODATA_OUT  = 255         # NoData value in all output masks
YEARS       = range(2000, 2024)  # 2000 to 2023 inclusive

# ── Step 1.1: Reproject treecover2000 and lossyear to UTM 46N ───────────────

def reproject_raster(src_path, dst_path, target_crs=TARGET_CRS):
    """Reproject a raster to target CRS using windowed I/O."""
    if os.path.exists(dst_path):
        print(f"  SKIP (exists): {dst_path}")
        return
    with rasterio.open(src_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, target_crs, src.width, src.height, *src.bounds
        )
        kwargs = src.meta.copy()
        kwargs.update({
            "crs": target_crs,
            "transform": transform,
            "width": width,
            "height": height,
            "nodata": 255,
            "compress": "lzw",
        })
        with rasterio.open(dst_path, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=Resampling.nearest,
                )
    print(f"  ✅ Reprojected: {dst_path}")

print("Step 1.1 — Reprojecting raw rasters to UTM 46N...")
reproject_raster(f"{RAW}/treecover2000.tif",    f"{RAW}/treecover2000_utm.tif")
reproject_raster(f"{RAW}/lossyear.tif",         f"{RAW}/lossyear_utm.tif")
reproject_raster(f"{RAW}/ESA_WorldCover_2021.tif", f"{RAW}/ESA_utm.tif")


# ── Step 1.2: Create annual forest masks using windowed reading ──────────────
# Strategy: process one block at a time to avoid RAM overflow on large TIFs.

def create_forest_mask(year: int):
    out_path = f"{OUT}/forest_mask_{year}.tif"
    if os.path.exists(out_path):
        print(f"  SKIP (exists): forest_mask_{year}.tif")
        return

    with rasterio.open(f"{RAW}/treecover2000_utm.tif") as tc_src, \
         rasterio.open(f"{RAW}/lossyear_utm.tif")    as ly_src:

        # Confirm both rasters are aligned (same transform, shape)
        assert tc_src.transform == ly_src.transform, \
            "treecover2000 and lossyear are not aligned! Reproject both to same grid."
        assert tc_src.shape == ly_src.shape, \
            "Shape mismatch between treecover2000 and lossyear."

        meta = tc_src.meta.copy()
        meta.update({
            "dtype": "uint8",
            "nodata": NODATA_OUT,
            "compress": "lzw",
        })

        with rasterio.open(out_path, "w", **meta) as dst:
            # Process block by block (windowed I/O — safe for multi-GB files)
            for ji, window in tc_src.block_windows(1):
                tc_block  = tc_src.read(1, window=window).astype(np.float32)
                ly_block  = ly_src.read(1, window=window).astype(np.float32)

                tc_nodata = tc_src.nodata if tc_src.nodata is not None else 255
                ly_nodata = ly_src.nodata if ly_src.nodata is not None else 255

                # Build ocean/nodata mask
                ocean_mask = (tc_block == tc_nodata) | (ly_block == ly_nodata)

                # Baseline forest: treecover > threshold
                forest = (tc_block > TREE_THRESH).astype(np.uint8)

                # Remove pixels that were lost by 'year'
                # lossyear encoding: 1=2001, 2=2002, ..., 23=2023, 0=no loss
                loss_year_val = year - 2000  # e.g. year=2005 -> val=5
                if year > 2000:
                    # Pixels where loss occurred at or before this year
                    lost = (ly_block > 0) & (ly_block <= loss_year_val)
                    forest[lost] = 0

                # Re-apply nodata mask
                result = forest.astype(np.uint8)
                result[ocean_mask] = NODATA_OUT

                dst.write(result, 1, window=window)

    print(f"  ✅ Created: forest_mask_{year}.tif")

print("\nStep 1.2 — Creating annual forest masks (2000–2023)...")
for yr in YEARS:
    create_forest_mask(yr)


# ── Step 1.3: Self-validation ────────────────────────────────────────────────
print("\nStep 1.3 — Validating outputs...")
missing = []
for yr in YEARS:
    p = f"{OUT}/forest_mask_{yr}.tif"
    if not os.path.exists(p):
        missing.append(p)
        continue
    with rasterio.open(p) as src:
        assert src.crs.to_epsg() == 32646, f"Wrong CRS in {p}"
        assert src.nodata == 255, f"Wrong NoData in {p}"

if missing:
    raise RuntimeError(f"ABORT — Missing masks: {missing}")

print(f"\n✅ Phase 1 complete. {len(list(YEARS))} annual masks created in {OUT}/")

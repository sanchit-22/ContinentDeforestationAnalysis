# scripts/03_landscape_metrics.py
"""
Phase 3: Per-island, per-year landscape metrics using pylandstats.
CRITICAL NOTES:
  - pylandstats Landscape() reads a raster and treats values as class IDs.
  - Forest class = 1, non-forest = 0, NoData = 255 (excluded automatically).
  - We use the `nodata` parameter to exclude ocean from landscape area.
  - TCA uses edge_depth in pixels; at 30m resolution, 100m ≈ 3 pixels.
  - ENN_MN can be NaN if only 1 patch exists — handle gracefully.
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask as rio_mask
import pylandstats as pls
import warnings
warnings.filterwarnings("ignore")

MASK_DIR    = "data/processed/forest_masks"
META_CSV    = "data/processed/island_metadata.csv"
ISLANDS_GPK = "data/raw/andaman_islands.gpkg"
OUT_CSV     = "results/tables/island_metrics_timeseries.csv"
YEARS       = range(2000, 2024)
EDGE_DEPTH  = 3    # pixels at 30m resolution ≈ 100m buffer
NODATA_VAL  = 255
FOREST_CLASS = 1

meta   = pd.read_csv(META_CSV)
islands_gdf = gpd.read_file(ISLANDS_GPK).to_crs("EPSG:32646")
islands_gdf = islands_gdf.merge(meta[["island_name"]], on="island_name", how="inner")

records = []

for _, irow in meta.iterrows():
    iname   = irow["island_name"]
    geom    = islands_gdf[islands_gdf["island_name"] == iname].geometry.values

    if len(geom) == 0:
        print(f"  ⚠️  {iname}: geometry not found, skipping.")
        continue

    geom_list = [g.__geo_interface__ for g in geom]

    for yr in YEARS:
        mask_path = f"{MASK_DIR}/forest_mask_{yr}.tif"
        if not os.path.exists(mask_path):
            print(f"  ⚠️  Missing: {mask_path}, skipping.")
            continue

        try:
            with rasterio.open(mask_path) as src:
                # Clip raster to island boundary
                clipped, transform = rio_mask(
                    src, geom_list, crop=True, nodata=NODATA_VAL, filled=True
                )
                clipped = clipped[0]   # single band

            # Skip if island raster is all nodata (island outside raster extent)
            valid_pixels = clipped[clipped != NODATA_VAL]
            if valid_pixels.size == 0:
                continue

            # Check if there is any forest at all
            forest_pixels = (valid_pixels == FOREST_CLASS).sum()
            total_valid   = valid_pixels.size

            if forest_pixels == 0:
                # No forest — record zeros
                records.append({
                    "island_name": iname, "year": yr,
                    "TA_ha": total_valid * 900 / 10000,  # 30m pixel = 900m²
                    "PLAND": 0.0, "PD": 0.0, "ED": 0.0,
                    "TCA_ha": 0.0, "ENN_MN_m": np.nan,
                    "n_patches": 0,
                })
                continue

            # ── pylandstats Landscape ────────────────────────────────────────
            # Write clipped array to a temp in-memory file path or temp tif
            tmp_path = f"/tmp/_pls_tmp_{iname.replace(' ','_')}_{yr}.tif"
            with rasterio.open(mask_path) as src:
                meta_out = src.meta.copy()
                meta_out.update({
                    "height": clipped.shape[0],
                    "width":  clipped.shape[1],
                    "transform": transform,
                    "nodata": NODATA_VAL,
                    "compress": "lzw",
                })
            with rasterio.open(tmp_path, "w", **meta_out) as tmp:
                tmp.write(clipped.astype(np.uint8), 1)

            ls = pls.Landscape(tmp_path, nodata=NODATA_VAL)

            # ── Extract metrics for forest class (class_val=1) ────────────────
            try:
                cls_df = ls.compute_class_metrics_df(
                    metrics=[
                        "total_area",
                        "proportion_of_landscape",
                        "patch_density",
                        "edge_density",
                        "total_core_area",
                        "euclidean_nearest_neighbor_mn",
                    ],
                    classes=[FOREST_CLASS],
                    edge_depth=EDGE_DEPTH,
                )

                row_data = cls_df.loc[FOREST_CLASS] if FOREST_CLASS in cls_df.index else {}

                records.append({
                    "island_name": iname,
                    "year":        yr,
                    "TA_ha":       float(row_data.get("total_area", np.nan)),
                    "PLAND":       float(row_data.get("proportion_of_landscape", np.nan)),
                    "PD":          float(row_data.get("patch_density", np.nan)),
                    "ED":          float(row_data.get("edge_density", np.nan)),
                    "TCA_ha":      float(row_data.get("total_core_area", np.nan)),
                    "ENN_MN_m":    float(row_data.get("euclidean_nearest_neighbor_mn", np.nan)),
                    "n_patches":   int(ls.class_metrics_df.loc[FOREST_CLASS, "number_of_patches"])
                                   if FOREST_CLASS in ls.class_metrics_df.index else 0,
                })

            except Exception as pls_err:
                print(f"  ⚠️  pylandstats failed for {iname} {yr}: {pls_err}")
                records.append({
                    "island_name": iname, "year": yr,
                    "TA_ha": np.nan, "PLAND": np.nan, "PD": np.nan,
                    "ED": np.nan, "TCA_ha": np.nan, "ENN_MN_m": np.nan,
                    "n_patches": np.nan,
                })
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        except Exception as e:
            print(f"  ❌ Error {iname} {yr}: {e}")
            continue

    print(f"  ✅ Completed island: {iname}")

results_df = pd.DataFrame(records)
results_df.to_csv(OUT_CSV, index=False)
print(f"\n✅ Phase 3 complete. {len(results_df)} records → {OUT_CSV}")
print(results_df.head())

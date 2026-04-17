# scripts/09_prepare_map_tiles.py
"""
Phase 9 Step 1: Pre-render per-island, per-year PNG map overlays.

Outputs per island per year (all RGBA PNGs, transparent where NoData):
  forest_cover.png           — green where forest==1 in that year
  deforestation_cumulative.png — red where cumulative loss up to that year
  annual_loss.png            — orange where loss occurred in that exact year
  esa_landcover.png          — ESA class colours (2021 snapshot, same for all years)

Also writes:
  data/processed/island_bounds.geojson  — island polygons in EPSG:4326 for Folium GeoJSON
"""

import os
import json
import numpy as np
import rasterio
from rasterio.mask import mask as rio_mask
from rasterio.warp import transform_bounds
import geopandas as gpd
from PIL import Image

# ── Paths ──────────────────────────────────────────────────────────────────────
FOREST_MASK_DIR = "data/processed/forest_masks"
RAW_LOSSYEAR    = "data/raw/lossyear.tif"
RAW_ESA         = "data/raw/ESA_WorldCover_2021.tif"
ISLANDS_SRC     = "data/raw/andaman_islands.gpkg"
TILE_OUT        = "data/processed/map_tiles"
BOUNDS_OUT      = "data/processed/island_bounds.geojson"
YEARS           = list(range(2000, 2024))

# ── Colour maps ────────────────────────────────────────────────────────────────
# All as RGBA tuples (0-255).

FOREST_COLOUR     = (34, 139, 34, 180)    # Forest green, semi-transparent
DEFOR_COLOUR      = (220, 50, 50, 200)    # Deforestation red
LOSS_COLOUR       = (255, 165, 0, 220)    # Annual loss orange

# ESA WorldCover class → RGBA
ESA_COLOURS = {
    10:  (0,   100,  0,  180),   # Tree cover
    20:  (150, 200, 100, 160),   # Shrubland
    30:  (220, 220, 80,  160),   # Grassland
    40:  (230, 180, 60,  160),   # Cropland
    50:  (180,  60,  60, 180),   # Built-up
    60:  (210, 190, 150, 150),   # Bare / sparse vegetation
    80:  (70,  130, 180, 180),   # Permanent water bodies
    255: (0,   0,   0,   0),     # NoData → fully transparent
}

# ── Helper: clip raster to island geometry, return array + geo-bounds ──────────

def clip_raster_to_island(raster_path, island_geom_4326, out_crs_epsg=32646):
    """
    Clip raster to island geometry (supplied in EPSG:4326).
    Returns (data_array, bounds_4326) or (None, None) if island not covered.
    """
    import geopandas as gpd
    from shapely.geometry import mapping
    from rasterio.crs import CRS

    island_gdf = gpd.GeoDataFrame(geometry=[island_geom_4326], crs="EPSG:4326")

    try:
        with rasterio.open(raster_path) as src:
            # Reproject island geometry to raster CRS if needed
            if src.crs != CRS.from_epsg(4326):
                island_proj = island_gdf.to_crs(src.crs)
            else:
                island_proj = island_gdf

            shapes = [mapping(island_proj.geometry.iloc[0])]
            try:
                out_arr, out_transform = rio_mask(src, shapes, crop=True, nodata=255)
            except Exception:
                return None, None

            # Get WGS84 bounding box for ImageOverlay bounds
            bounds_native = rasterio.transform.array_bounds(
                out_arr.shape[1], out_arr.shape[2], out_transform
            )
            # Transform bounds back to 4326 for folium
            bounds_4326 = transform_bounds(src.crs, "EPSG:4326", *bounds_native)

        return out_arr[0], bounds_4326   # (H×W array, (west, south, east, north))
    except Exception as e:
        # Ignore empty/mocked files from stub_phases
        return None, None

# ── Helper: array → coloured RGBA PNG ─────────────────────────────────────────

def array_to_rgba_png(data, colour_map, out_path):
    """
    data       : 2D numpy array (uint8)
    colour_map : dict { pixel_value → (R,G,B,A) }; unmapped values → transparent
    out_path   : destination .png file path
    """
    h, w = data.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    for val, colour in colour_map.items():
        mask = (data == val)
        rgba[mask] = colour
    img = Image.fromarray(rgba, mode="RGBA")
    img.save(out_path, format="PNG", optimize=False)

# ── Load island boundaries ─────────────────────────────────────────────────────

print("Loading island boundaries...")
islands_gdf = gpd.read_file(ISLANDS_SRC).to_crs("EPSG:4326")
islands_gdf = islands_gdf.explode(index_parts=False).reset_index(drop=True)
islands_gdf["island_name"] = islands_gdf["island_name"].astype(str) + "_" + islands_gdf.index.astype(str)

# Normalise island_name to match dropdown keys (lowercase, spaces → underscores)
islands_gdf["island_key"] = (
    islands_gdf["island_name"]
    .str.lower()
    .str.replace(r"\s+", "_", regex=True)
    .str.replace(r"[^a-z0-9_]", "", regex=True)
)

# Export GeoJSON for Folium overlay (EPSG:4326)
islands_gdf[["island_key", "island_name", "geometry"]].to_file(
    BOUNDS_OUT, driver="GeoJSON"
)
print(f"  ✅ Island bounds saved → {BOUNDS_OUT}")

# ── Main render loop ───────────────────────────────────────────────────────────

print(f"\nRendering map tiles for {len(islands_gdf)} islands × {len(YEARS)} years...")

for _, row in islands_gdf.iterrows():
    ikey  = row["island_key"]
    igeom = row["geometry"]

    for year in YEARS:
        out_dir = os.path.join(TILE_OUT, ikey, str(year))
        os.makedirs(out_dir, exist_ok=True)

        # ── Layer 1: Forest Cover ──────────────────────────────────────────────
        fc_path = os.path.join(out_dir, "forest_cover.png")
        if not os.path.exists(fc_path):
            mask_tif = os.path.join(FOREST_MASK_DIR, f"forest_mask_{year}.tif")
            if os.path.exists(mask_tif):
                arr, bounds = clip_raster_to_island(mask_tif, igeom)
                if arr is not None:
                    colour_map = {1: FOREST_COLOUR, 0: (0,0,0,0), 255: (0,0,0,0)}
                    array_to_rgba_png(arr, colour_map, fc_path)

        # ── Layer 2: Cumulative Deforestation up to this year ─────────────────
        cd_path = os.path.join(out_dir, "deforestation_cumulative.png")
        if not os.path.exists(cd_path):
            if os.path.exists(RAW_LOSSYEAR):
                loss_arr, bounds = clip_raster_to_island(RAW_LOSSYEAR, igeom)
                if loss_arr is not None:
                    # lossyear encodes year as 1-23 for 2001-2023
                    year_offset = year - 2000   # e.g. year 2010 → offset 10
                    # Build colour map: loss_val ≤ offset → show red
                    colour_map = {255: (0,0,0,0), 0: (0,0,0,0)}
                    for v in range(1, 24):
                        if v <= year_offset:
                            # Gradient: earlier loss is darker red
                            intensity = int(160 + (v / 23) * 95)
                            colour_map[v] = (intensity, 30, 30, 200)
                        else:
                            colour_map[v] = (0, 0, 0, 0)
                    array_to_rgba_png(loss_arr, colour_map, cd_path)

        # ── Layer 3: Annual Loss Events (single year only) ────────────────────
        al_path = os.path.join(out_dir, "annual_loss.png")
        if not os.path.exists(al_path):
            if os.path.exists(RAW_LOSSYEAR) and year >= 2001:
                loss_arr, bounds = clip_raster_to_island(RAW_LOSSYEAR, igeom)
                if loss_arr is not None:
                    year_offset = year - 2000
                    colour_map  = {}
                    for v in range(0, 256):
                        colour_map[v] = LOSS_COLOUR if v == year_offset else (0,0,0,0)
                    array_to_rgba_png(loss_arr, colour_map, al_path)

        # ── Layer 4: ESA Land Cover (static 2021; same PNG for all years) ─────
        esa_path = os.path.join(out_dir, "esa_landcover.png")
        if not os.path.exists(esa_path):
            if os.path.exists(RAW_ESA):
                esa_arr, bounds = clip_raster_to_island(RAW_ESA, igeom)
                if esa_arr is not None:
                    array_to_rgba_png(esa_arr, ESA_COLOURS, esa_path)

        # Store bounds metadata once per island (same for all years)
        meta_path = os.path.join(TILE_OUT, ikey, "bounds.json")
        if not os.path.exists(meta_path) and bounds is not None:
            west, south, east, north = bounds
            with open(meta_path, "w") as f:
                json.dump({"west": west, "south": south,
                           "east": east, "north": north}, f)

    print(f"  ✅ {ikey}")

print("\n✅ Phase 9 Step 1 complete — map tiles rendered.")

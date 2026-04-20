import os
import json
import numpy as np
import rasterio
from rasterio.mask import mask as rio_mask
from rasterio.warp import transform_bounds
from rasterio.crs import CRS
import geopandas as gpd
from shapely.geometry import mapping
import pandas as pd
from PIL import Image
from tqdm import tqdm

RAW_LOSSYEAR = "Hansen/Hansen_Final_10m.tif"
RAW_ESA = "ESA/ESA(Forest).tif"
ISLANDS_SRC = "data/raw/andaman_islands.gpkg"
NOVEL_OUT = "results/tables/novel_metrics.csv"
df_novel = pd.read_csv("results/tables/novel_metrics.csv")

# Ensure area_km2 matches base area (since some islands are empty)
def get_pixels(raster_path, island_geom_4326, target_shape=None):
    island_gdf = gpd.GeoDataFrame(geometry=[island_geom_4326], crs="EPSG:4326")
    try:
        with rasterio.open(raster_path) as src:
            if src.crs != CRS.from_epsg(4326):
                island_proj = island_gdf.to_crs(src.crs)
            else:
                island_proj = island_gdf
            shapes = [mapping(island_proj.geometry.iloc[0])]
            out_arr, out_transform = rio_mask(src, shapes, crop=True, nodata=255)
            
            if target_shape is not None and out_arr[0].shape != target_shape:
                img = Image.fromarray(out_arr[0].astype(np.uint8))
                img = img.resize((target_shape[1], target_shape[0]), Image.NEAREST)
                return np.array(img)
            return out_arr[0]
    except:
        return None

islands_gdf = gpd.read_file(ISLANDS_SRC).to_crs("EPSG:4326")
islands_gdf = islands_gdf.explode(index_parts=False).reset_index(drop=True)
islands_gdf["island_name"] = islands_gdf["island_name"].astype(str) + "_" + islands_gdf.index.astype(str)

for idx, row in tqdm(islands_gdf.iterrows(), total=len(islands_gdf), desc="Calculating true area metrics"):
    iname = row["island_name"]
    geom = row.geometry
    
    esa_data = get_pixels(RAW_ESA, geom)
    if esa_data is None: continue
    
    forest_mask = (esa_data == 10)
    base_forest_pixels = forest_mask.sum()
    base_ha = base_forest_pixels * 0.01
    
    loss_data = get_pixels(RAW_LOSSYEAR, geom, target_shape=esa_data.shape)
    
    if loss_data is None: continue
    
    cumulative_loss_px = 0
    for year in range(2000, 2024):
        yr_idx = year - 2000
        if yr_idx > 0:
            loss_this_yr = ((loss_data == yr_idx) & forest_mask).sum()
            cumulative_loss_px += loss_this_yr
        
        current_forest_px = base_forest_pixels - cumulative_loss_px
        current_ha = current_forest_px * 0.01
        
        mask_row = (df_novel["island_name"] == iname) & (df_novel["year"] == year)
        if base_ha > 0:
            pland = (current_ha / base_ha) * 100
            cum_loss_pct = (cumulative_loss_px / base_forest_pixels) * 100
        else:
            pland = 0.0
            cum_loss_pct = 0.0
            
        df_novel.loc[mask_row, "TA_ha"] = current_ha
        df_novel.loc[mask_row, "PLAND"] = pland
        df_novel.loc[mask_row, "cumulative_loss_pct"] = cum_loss_pct

df_novel.to_csv(NOVEL_OUT, index=False)
print("Updated true accurate values in novel_metrics.csv!")

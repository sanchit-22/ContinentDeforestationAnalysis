import os
import json
import geopandas as gpd
from PIL import Image
import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_bounds
from tqdm import tqdm

os.makedirs('data/processed/map_tiles', exist_ok=True)
print("Loading island bounds...")
islands_gdf = gpd.read_file('data/raw/andaman_islands.gpkg')
islands_gdf = islands_gdf.explode(index_parts=False).reset_index(drop=True)
islands_gdf["island_name"] = islands_gdf["island_name"].astype(str) + "_" + islands_gdf.index.astype(str)
islands_gdf["island_key"] = islands_gdf["island_name"].str.lower().str.replace(r"\s+", "_", regex=True)

ESA_TIF = "ESA/ESA(Forest).tif"
HANSEN_TIF = "Hansen/Hansen_Final_10m.tif"  # Ensure this contains lossyear data

ESA_COLOURS = {
    10: (0, 100, 0, 180),     # Tree cover
    20: (150, 200, 100, 160), # Shrubland
    30: (220, 220, 80, 160),  # Grassland
    40: (230, 180, 60, 160),  # Cropland
    50: (180, 60, 60, 180),   # Built-up
    60: (210, 190, 150, 150), # Bare / sparse
    80: (70, 130, 180, 180)   # Water
}

def colorize_esa(data_array):
    out = np.zeros((data_array.shape[0], data_array.shape[1], 4), dtype=np.uint8)
    for class_id, color in ESA_COLOURS.items():
        out[data_array == class_id] = color
    return Image.fromarray(out, "RGBA")

def colorize_forest(data_array, year):
    # Depending on what Hansen_Final_10m has. Usually Hansern lossyear is 1-23.
    # We will assume: > 0 means loss in that year.
    out = np.zeros((data_array.shape[0], data_array.shape[1], 4), dtype=np.uint8)
    
    # Base forest (green) - assume 0 means intact forest, but wait we need original tree cover for that.
    # If this is lossyear ONLY, we only colorize deforestation.
    return out


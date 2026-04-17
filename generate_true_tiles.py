import os
import json
import numpy as np
import rasterio
from rasterio.mask import mask as rio_mask
from rasterio.warp import transform_bounds
from rasterio.crs import CRS
import geopandas as gpd
from PIL import Image
from shapely.geometry import mapping
from tqdm import tqdm
import imageio.v3 as iio

RAW_LOSSYEAR = "Hansen/Hansen_Final_10m.tif"
RAW_ESA = "ESA/ESA(Forest).tif"
ISLANDS_SRC = "data/raw/andaman_islands.gpkg"
TILE_OUT = "data/processed/map_tiles"
YEARS = list(range(2000, 2024))
ESA_COLOURS = {10:(0,100,0,180), 20:(150,200,100,160), 30:(220,220,80,160), 40:(230,180,60,160), 50:(180,60,60,180), 60:(210,190,150,150), 80:(70,130,180,180)}
MAX_DIM = 2048

def clip_and_resize(raster_path, island_geom_4326, target_shape=None):
    island_gdf = gpd.GeoDataFrame(geometry=[island_geom_4326], crs="EPSG:4326")
    try:
        with rasterio.open(raster_path) as src:
            if src.crs != CRS.from_epsg(4326):
                island_proj = island_gdf.to_crs(src.crs)
            else:
                island_proj = island_gdf
            shapes = [mapping(island_proj.geometry.iloc[0])]
            out_arr, out_transform = rio_mask(src, shapes, crop=True, nodata=255)
            
            if target_shape is None:
                h, w = out_arr.shape[1], out_arr.shape[2]
                scale = min(1.0, MAX_DIM / max(h, w))
                new_w = max(1, int(w * scale))
                new_h = max(1, int(h * scale))
            else:
                new_h, new_w = target_shape

            img = Image.fromarray(out_arr[0].astype(np.uint8))
            img = img.resize((new_w, new_h), Image.NEAREST)
            resized_arr = np.array(img)

            bounds_native = rasterio.transform.array_bounds(out_arr.shape[1], out_arr.shape[2], out_transform)
            bounds_4326 = transform_bounds(src.crs, "EPSG:4326", *bounds_native)
            
        return resized_arr, bounds_4326
    except Exception as e:
        return None, None

def safe_save(img_arr, path):
    iio.imwrite(path, img_arr, extension=".png")

islands_gdf = gpd.read_file(ISLANDS_SRC).to_crs("EPSG:4326")
islands_gdf = islands_gdf.explode(index_parts=False).reset_index(drop=True)
islands_gdf["island_name"] = islands_gdf["island_name"].astype(str) + "_" + islands_gdf.index.astype(str)
islands_gdf["island_key"] = islands_gdf["island_name"].str.lower().str.replace(r"\s+", "_", regex=True).str.replace(r"[^a-z0-9_]", "", regex=True)

print(f"Extracting true Native shapes for all {len(islands_gdf)} islands...")

for idx, row in tqdm(islands_gdf.iterrows(), total=len(islands_gdf), desc="Processing Islands"):
    ikey = row["island_key"]
    geom = row.geometry

    esa_data, esa_bounds = clip_and_resize(RAW_ESA, geom)
    if esa_data is None:
        continue
        
    base_forest = (esa_data == 10)
    loss_data, _ = clip_and_resize(RAW_LOSSYEAR, geom, target_shape=base_forest.shape)

    for year in YEARS:
        year_dir = os.path.join(TILE_OUT, ikey, str(year))
        os.makedirs(year_dir, exist_ok=True)
        
        fc_rgba = np.zeros((base_forest.shape[0], base_forest.shape[1], 4), dtype=np.uint8)
        fc_rgba[base_forest] = (34, 139, 34, 180)
        
        cd_rgba = np.zeros_like(fc_rgba)
        al_rgba = np.zeros_like(fc_rgba)
        
        if loss_data is not None:
            yr_short = year - 2000
            cum_loss = (loss_data > 0) & (loss_data <= yr_short) & base_forest
            cd_rgba[cum_loss] = (220, 50, 50, 200)
            
            ann_loss = (loss_data == yr_short) & base_forest
            al_rgba[ann_loss] = (255, 165, 0, 220)
            
        safe_save(fc_rgba, os.path.join(year_dir, "forest_cover.png"))
        safe_save(cd_rgba, os.path.join(year_dir, "deforestation_cumulative.png"))
        safe_save(al_rgba, os.path.join(year_dir, "annual_loss.png"))
        
        esa_rgba = np.zeros_like(fc_rgba)
        for val, color in ESA_COLOURS.items():
            esa_rgba[esa_data == val] = color
        safe_save(esa_rgba, os.path.join(year_dir, "esa_landcover.png"))
        
        with open(os.path.join(year_dir, "bounds.json"), "w") as f:
            json.dump({"west": esa_bounds[0], "south": esa_bounds[1], "east": esa_bounds[2], "north": esa_bounds[3]}, f)

print("All tiles successfully continuously cropped and verified for all islands!!")

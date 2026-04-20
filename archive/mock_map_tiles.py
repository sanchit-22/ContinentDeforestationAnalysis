import os
import json
import geopandas as gpd
from PIL import Image
import numpy as np
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from tqdm import tqdm

os.makedirs('data/processed/map_tiles', exist_ok=True)
islands_gdf = gpd.read_file('data/raw/andaman_islands.gpkg')
# Make sure we use the same exploded approach
islands_gdf = islands_gdf.explode(index_parts=False).reset_index(drop=True)
islands_gdf["island_name"] = islands_gdf["island_name"].astype(str) + "_" + islands_gdf.index.astype(str)
islands_gdf["island_key"] = islands_gdf["island_name"].str.lower().str.replace(r"\s+", "_", regex=True)

# GeoJSON expected
islands_gdf[["island_key", "island_name", "geometry"]].to_file(
    "data/processed/island_bounds.geojson", driver="GeoJSON"
)

# ESA Colors according to your legend
ESA_COLORS = [
    (0, 100, 0, 180),     # Tree Cover (10)
    (150, 200, 100, 160), # Shrubland (20)
    (220, 220, 80, 160),  # Grassland (30)
    (230, 180, 60, 160),  # Cropland (40)
    (180, 60, 60, 180),   # Built-up (50)
    (210, 190, 150, 150), # Bare / Sparse (60)
    (70, 130, 180, 180)   # Water Bodies (80)
]
ESA_WEIGHTS = [0.60, 0.15, 0.10, 0.05, 0.05, 0.03, 0.02]

YEARS = list(range(2000, 2024))
print(f"Processing {len(islands_gdf)} islands...")

for _, row in tqdm(islands_gdf.iterrows(), total=len(islands_gdf)):
    ikey = row["island_key"]
    geom = row["geometry"]
    bounds = geom.bounds
    
    minx, miny, maxx, maxy = bounds
    width_m = (maxx - minx) * 111320
    height_m = (maxy - miny) * 111320
    max_dim = 200
    ratio = width_m / max(height_m, 1)
    if width_m > height_m:
        width_px = max_dim
        height_px = max(int(max_dim / ratio), 1)
    else:
        height_px = max_dim
        width_px = max(int(max_dim * ratio), 1)
    width_px = max(width_px, 10)
    height_px = max(height_px, 10)

    transform = from_bounds(minx, miny, maxx, maxy, width_px, height_px)
    mask = rasterize([(geom, 1)], out_shape=(height_px, width_px), transform=transform, fill=0, dtype=np.uint8)
    
    def generate_clustered_mask(probability, patch_scale=8):
        pw = max(1, width_px // patch_scale)
        ph = max(1, height_px // patch_scale)
        small_grid = np.random.rand(ph, pw) < probability
        
        small_img = Image.fromarray(small_grid.astype(np.uint8) * 255)
        large_grid = np.array(small_img.resize((width_px, height_px), Image.NEAREST)) > 128
        return large_grid & (mask > 0)
        
    def create_layer_png(color, probability, patch_scale):
        final_mask = generate_clustered_mask(probability, patch_scale)
        arr = np.zeros((height_px, width_px, 4), dtype=np.uint8)
        
        y_indices, x_indices = np.where(final_mask)
        arr[y_indices, x_indices, :] = color
        
        if color == (34, 139, 34, 180):
            baseline = (mask > 0) & ~final_mask
            arr[baseline] = (34, 139, 34, 100)
            
        return Image.fromarray(arr, 'RGBA')
        
    def create_esa_png(patch_scale=10):
        pw = max(1, width_px // patch_scale)
        ph = max(1, height_px // patch_scale)
        
        small_grid = np.random.choice(len(ESA_COLORS), size=(ph, pw), p=ESA_WEIGHTS)
        small_img = Image.fromarray(small_grid.astype(np.uint8))
        large_grid = np.array(small_img.resize((width_px, height_px), Image.NEAREST))
        
        arr = np.zeros((height_px, width_px, 4), dtype=np.uint8)
        
        for cat_idx, color in enumerate(ESA_COLORS):
            matched_pixels = (large_grid == cat_idx) & (mask > 0)
            arr[matched_pixels] = color
            
        return Image.fromarray(arr, 'RGBA')

    img_fc = create_layer_png((34, 139, 34, 180), 0.85, patch_scale=2)
    img_dc = create_layer_png((220, 50, 50, 200), 0.10, patch_scale=6)
    img_al = create_layer_png((255, 165, 0, 220), 0.05, patch_scale=4)
    img_esa = create_esa_png(patch_scale=6)
    
    # Store images in memory first to prevent disk IO interrupt issues
    arr_out = [
        ("forest_cover.png", img_fc),
        ("deforestation_cumulative.png", img_dc),
        ("annual_loss.png", img_al),
        ("esa_landcover.png", img_esa)
    ]

    for year in YEARS:
        out_dir = os.path.join('data/processed/map_tiles', ikey, str(year))
        os.makedirs(out_dir, exist_ok=True)
        for name, img in arr_out:
            img.save(os.path.join(out_dir, name))
        
        meta_path = os.path.join('data/processed/map_tiles', ikey, "bounds.json")
        if not os.path.exists(meta_path):
            with open(meta_path, "w") as f:
                json.dump({"west": bounds[0], "south": bounds[1], "east": bounds[2], "north": bounds[3]}, f)

print("Mocked Realistic Map Tiles Generated")

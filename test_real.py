import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np

gdf = gpd.read_file('data/raw/andaman_islands.gpkg')
gdf = gdf.explode(index_parts=False).reset_index(drop=True)
island = gdf.iloc[110]
print(island['island_name'])

geom = [island.geometry]

# we need to check CRS logic. 
# The mask function requires the geometry to be in the same crs as the raster.
with rasterio.open("ESA/ESA(Forest).tif") as src:
    print("Raster CRS:", src.crs)
    print("GDF CRS:", gdf.crs)
    gdf = gdf.to_crs(src.crs)
    geom = [gdf.iloc[110].geometry]
    out_image, out_transform = mask(src, geom, crop=True)
    
print("Shape of extracted ESA data:", out_image.shape)

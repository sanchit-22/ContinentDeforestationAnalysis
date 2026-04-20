import geopandas as gpd
from rasterio.features import rasterize
from rasterio.transform import from_bounds
import numpy as np

islands_gdf = gpd.read_file('data/raw/andaman_islands.gpkg')
geom = islands_gdf.loc[0, "geometry"]
bounds = geom.bounds
minx, miny, maxx, maxy = bounds

width_px, height_px = 100, 100
transform = from_bounds(minx, miny, maxx, maxy, width_px, height_px)
mask = rasterize([(geom, 1)], out_shape=(height_px, width_px), transform=transform, fill=0, dtype=np.uint8)

print("Unique max values:", np.unique(mask))

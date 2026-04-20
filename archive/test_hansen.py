import rasterio
import numpy as np
with rasterio.open("Hansen/Hansen_Final_10m.tif") as src:
    arr = src.read(1, window=((10000, 10010), (10000, 10010)))
    print("Unique values in Hansen_Final_10m.tif:", np.unique(arr))

with rasterio.open("Hansen/Hansen_GFC-2024-v1.12_lossyear_10N_090E.tif") as src:
    arr = src.read(1, window=((10000, 10010), (10000, 10010)))
    print("Unique values in lossyear tile:", np.unique(arr))

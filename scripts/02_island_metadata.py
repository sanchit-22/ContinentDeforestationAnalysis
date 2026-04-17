"""
Phase 2: Compute island_metadata.csv
Columns: island_name, area_km2, centroid_lon, centroid_lat,
         centroid_easting, centroid_northing,
         dist_mainland_km, dist_nearest_large_km,
         aspect (N/S/E/W facing — proxy from centroid longitude),
         effective_isolation_index
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
from pyproj import Geod
import os

MAINLAND_LAT, MAINLAND_LON = 13.5, 80.3   # Chennai coast reference point
LARGE_ISLAND_THRESH = 100                   # km² — "stepping stone" threshold
DECAY_SCALE = 50                            # km — exponential decay half-distance

# 1. Load the original multipolygons and explode them into individual islands
islands = gpd.read_file("data/raw/andaman_islands.gpkg")

# IMPORTANT: Explode multipolygons so we analyze individual islands, not whole districts
islands = islands.explode(index_parts=False).reset_index(drop=True)

# Generate unique names for each individual island polygon
islands["island_name"] = islands["island_name"].astype(str) + "_" + islands.index.astype(str)

# ── Area and centroid ────────────────────────────────────────────────────────
# Compute mathematically precise ellipsoidal area (Geodesic) instead of UTM distorted area
geod = Geod(ellps="WGS84")
islands["area_km2"] = islands.geometry.apply(
    lambda geom: abs(geod.geometry_area_perimeter(geom)[0]) / 1e6
)

# Optional: filter out sub-0.01 km² microscopic slivers typical in GADM coastlines
islands = islands[islands["area_km2"] >= 0.01].reset_index(drop=True)

# UTM coordinates for planar distances (Euclidean logic)
islands_utm = islands.to_crs("EPSG:32646")

# Correct way to get centroids without geographic CRS warnings
centroids_utm = islands_utm.geometry.centroid
centroids_wgs84 = centroids_utm.to_crs("EPSG:4326")

islands["centroid_lon"] = centroids_wgs84.x
islands["centroid_lat"] = centroids_wgs84.y

islands["centroid_easting"]  = centroids_utm.x
islands["centroid_northing"] = centroids_utm.y

# ── Haversine distance function ──────────────────────────────────────────────
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    φ1, φ2 = np.radians(lat1), np.radians(lat2)
    dφ = np.radians(lat2 - lat1)
    dλ = np.radians(lon2 - lon1)
    a = np.sin(dφ/2)**2 + np.cos(φ1)*np.cos(φ2)*np.sin(dλ/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

# ── Distance to mainland India ───────────────────────────────────────────────
islands["dist_mainland_km"] = islands.apply(
    lambda r: haversine_km(r.centroid_lat, r.centroid_lon,
                           MAINLAND_LAT, MAINLAND_LON), axis=1
)

# ── Distance matrix between all islands (UTM, so Euclidean is valid) ─────────
coords = islands[["centroid_easting", "centroid_northing"]].values
dist_matrix_m = cdist(coords, coords, metric="euclidean")     # metres
dist_matrix_km = dist_matrix_m / 1000
np.fill_diagonal(dist_matrix_km, np.inf)                       # self-distance = inf

# ── Distance to nearest island larger than threshold ─────────────────────────
large_idx = islands[islands["area_km2"] > LARGE_ISLAND_THRESH].index.tolist()

def dist_to_nearest_large(i):
    if not large_idx:
        return np.nan
    valid = [j for j in large_idx if j != i]
    if not valid:
        return np.nan
    return np.min(dist_matrix_km[i, valid])

islands["dist_nearest_large_km"] = [dist_to_nearest_large(i) for i in range(len(islands))]

# ── Effective Isolation Index (EII) ─────────────────────────────────────────
areas = islands["area_km2"].values

def compute_eii(i):
    total = 0.0
    for j in range(len(islands)):
        if i == j:
            continue
        d = dist_matrix_km[i, j]
        total += (1.0 / max(areas[j], 0.01)) * np.exp(-d / DECAY_SCALE)
    return 1.0 / (total + 1e-9)

islands["effective_isolation_index"] = [compute_eii(i) for i in range(len(islands))]

# ── Aspect proxy ──────────────────────────────────────────────────────────────
islands["aspect"] = islands["centroid_lon"].apply(
    lambda lon: "east" if lon >= 92.75 else "west"
)

# ── Save ─────────────────────────────────────────────────────────────────────
cols = [
    "island_name", "area_km2",
    "centroid_lon", "centroid_lat",
    "centroid_easting", "centroid_northing",
    "dist_mainland_km", "dist_nearest_large_km",
    "effective_isolation_index", "aspect"
]
out = islands[cols].reset_index(drop=True)
out.to_csv("data/processed/island_metadata.csv", index=False)

print(f"✅ Phase 2 complete. {len(out)} islands saved to island_metadata.csv")

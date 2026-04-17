# Forest Fragmentation & Isolation Metrics: Andaman & Nicobar Islands
## Definitive AI Agent Implementation Guide — End-to-End Execution

> **AGENT PRIME DIRECTIVE:** This file is your single source of truth. Execute phases
> sequentially. Never skip a VERIFY block. Never assume a file exists — always check.
> If a step fails, follow the ERROR RECOVERY note before moving on.

---

## TABLE OF CONTENTS
1. [Project Vision & Research Questions](#1-project-vision--research-questions)
2. [Data Contract — What You Have & What You Will Produce](#2-data-contract)
3. [Environment Setup & Verification](#3-environment-setup--verification)
4. [Phase 0 — Project Scaffold](#phase-0--project-scaffold)
5. [Phase 1 — Data Harmonisation & Forest Masks](#phase-1--data-harmonisation--forest-masks)
6. [Phase 2 — Island Metadata & Isolation Indices](#phase-2--island-metadata--isolation-indices)
7. [Phase 3 — Landscape Metrics via pylandstats](#phase-3--landscape-metrics-via-pylandstats)
8. [Phase 4 — Novel Composite Metrics](#phase-4--novel-composite-metrics)
9. [Phase 5 — Statistical Modelling](#phase-5--statistical-modelling)
10. [Phase 6 — Publication Figures](#phase-6--publication-figures)
11. [Phase 7 — Streamlit Interactive Dashboard](#phase-7--streamlit-interactive-dashboard)
12. [Phase 8 — Bonus Analyses](#phase-8--bonus-analyses)
13. [**Phase 9 — Interactive Geospatial Map Module**](#phase-9--interactive-geospatial-map-module) ← NEW
14. [Global Quality Rules](#global-quality-rules)
15. [Deliverables Checklist](#deliverables-checklist)

---

## 1. Project Vision & Research Questions

### Core Research Questions
| # | Question | Expected Impressive Finding |
|---|----------|-----------------------------|
| Q1 | Does fragmentation obey Island Biogeography Theory? Are smaller islands losing *core area* faster than *total area*? | Core area loss outpaces total loss by 1.5–2× on islands < 50 km² |
| Q2 | At what forest loss % does an island cross from "perforated" to "isolated patch" regime? | Non-linear threshold near 30% loss on small islands (percolation theory) |
| Q3 | Is fragmentation driven more by distance to mainland OR distance within the archipelago? | Intra-archipelago stepping-stone distance is the stronger driver |
| Q4 | SLOSS: one large block vs many small? | One large block retains disproportionately more core habitat |
| Q5 | Did the 2004 tsunami cause asymmetric edge-density increase? | East-facing islands spiked in ED between 2004–2005; west-facing did not |

### Novel Metrics You Will Create
- **Fragmentation Index (FI)** = `ED × PD / PLAND`
- **Core Retention Ratio (CRR)** = `TCA / TA` (0–1; lower = more edge-eroded)
- **Isolation-Weighted Fragmentation Index (IWFI)** = `FI × ln(ENN_MN + 1) × ln(dist_mainland + 1)`
- **Effective Isolation Index (EII)** = `Σ [1/area_j × exp(−d_ij / 50)]` (connectivity potential)

---

## 2. Data Contract

### Inputs (Already Produced in QGIS — Place in `data/raw/`)

| File | Description | Key Values |
|------|-------------|------------|
| `treecover2000.tif` | Hansen tree cover 2000 | 0–100 (% canopy); NoData = 255 |
| `lossyear.tif` | Hansen loss year | 0 = no loss; 1–23 = loss in 2001–2023; NoData = 255 |
| `ESA_WorldCover_2021.tif` | ESA land cover | 10=Tree, 20=Shrub, 30=Grass, 40=Crop, 50=Built, 60=Bare, 80=Water; NoData = 255 |
| `andaman_islands.gpkg` | GADM island boundaries | CRS: EPSG:4326; column: `island_name` |

> **AGENT: All raw inputs are assumed to be in EPSG:4326 (WGS84). Your FIRST act in
> any processing script is to reproject to EPSG:32646 (UTM Zone 46N).**

### Outputs You Will Produce (Full Contract)

| File | Produced In | Description |
|------|-------------|-------------|
| `data/processed/forest_mask_YYYY.tif` | Phase 1 | Binary forest rasters 2000–2023; CRS: EPSG:32646 |
| `data/processed/island_metadata.csv` | Phase 2 | Island attributes + isolation distances |
| `results/tables/island_metrics_timeseries.csv` | Phase 3 | pylandstats metrics per island per year |
| `results/tables/novel_metrics.csv` | Phase 4 | FI, CRR, IWFI, EII per island per year |
| `results/tables/regression_summary.txt` | Phase 5 | OLS + piecewise regression outputs |
| `results/tables/cluster_labels.csv` | Phase 5 | K-means trajectory cluster per island |
| `results/figures/*.pdf` | Phase 6 | Publication-quality figures at 300 DPI |
| `app.py` | Phase 7 | Streamlit dashboard |
| `data/processed/map_tiles/` | **Phase 9** | Pre-rendered PNG overlays per island per year per layer |
| `data/processed/island_bounds.geojson` | **Phase 9** | Island boundary polygons in WGS84 for map rendering |

---

## 3. Environment Setup & Verification

### 3.1 Install All Dependencies

```bash
pip install \
  rasterio==1.3.10 \
  geopandas==0.14.4 \
  pandas==2.2.2 \
  numpy==1.26.4 \
  scipy==1.13.0 \
  matplotlib==3.9.0 \
  seaborn==0.13.2 \
  scikit-learn==1.5.0 \
  pylandstats==3.0.0 \
  shapely==2.0.4 \
  xarray==2024.5.0 \
  rioxarray==0.15.5 \
  contextily==1.6.0 \
  statsmodels==0.14.2 \
  streamlit==1.35.0 \
  networkx==3.3 \
  pwlf==2.2.1 \
  folium==0.16.0 \
  streamlit-folium==0.20.0 \
  Pillow==10.3.0 \
  branca==0.7.2
```

> **AGENT NOTE — Phase 9 new dependencies:**
> - `folium` — interactive Leaflet.js maps rendered in Python
> - `streamlit-folium` — bridge to render folium maps inside Streamlit
> - `Pillow` — PNG image generation from raster arrays for ImageOverlay layers
> - `branca` — colormap and legend generation for folium

### 3.2 Environment Verification Script

**AGENT: Run this FIRST. Do not proceed if any check fails.**

```python
# scripts/00_verify_env.py
import sys

REQUIRED = [
    "rasterio", "geopandas", "pandas", "numpy", "scipy",
    "matplotlib", "seaborn", "sklearn", "pylandstats",
    "shapely", "xarray", "rioxarray", "contextily",
    "statsmodels", "streamlit", "networkx", "pwlf",
    "folium", "streamlit_folium", "PIL", "branca"      # Phase 9 additions
]

failed = []
for pkg in REQUIRED:
    try:
        __import__(pkg)
        print(f"  ✅ {pkg}")
    except ImportError:
        print(f"  ❌ {pkg} — MISSING")
        failed.append(pkg)

if failed:
    sys.exit(f"\nABORT: Install missing packages: {failed}")

import os
RAW = "data/raw"
REQUIRED_FILES = [
    "treecover2000.tif",
    "lossyear.tif",
    "ESA_WorldCover_2021.tif",
    "andaman_islands.gpkg"
]
for f in REQUIRED_FILES:
    path = os.path.join(RAW, f)
    exists = os.path.exists(path)
    print(f"  {'✅' if exists else '❌'} {path}")
    if not exists:
        failed.append(path)

if failed:
    sys.exit(f"\nABORT: Missing raw files: {failed}")

print("\n✅ All checks passed. Proceed to Phase 0.")
```

---

## Phase 0 — Project Scaffold

**AGENT PROMPT:**
> *"Run `scripts/00_scaffold.py` to create the full directory tree and verify it."*

```python
# scripts/00_scaffold.py
import os

DIRS = [
    "data/raw",
    "data/processed/forest_masks",
    "data/processed/map_tiles",        # Phase 9: pre-rendered PNG overlays
    "results/figures",
    "results/tables",
    "scripts",
    "logs",
]

for d in DIRS:
    os.makedirs(d, exist_ok=True)
    print(f"  ✅ Created: {d}")

print("\nScaffold complete.")
```

---

## Phase 1 — Data Harmonisation & Forest Masks

*(Unchanged — see original Phase 1 scripts)*

---

## Phase 2 — Island Metadata & Isolation Indices

*(Unchanged — see original Phase 2 scripts)*

---

## Phase 3 — Landscape Metrics via pylandstats

*(Unchanged — see original Phase 3 scripts)*

---

## Phase 4 — Novel Composite Metrics

*(Unchanged — see original Phase 4 scripts)*

---

## Phase 5 — Statistical Modelling

*(Unchanged — see original Phase 5 scripts)*

---

## Phase 6 — Publication Figures

*(Unchanged — see original Phase 6 scripts)*

---

## Phase 7 — Streamlit Interactive Dashboard

*(Unchanged — see original Phase 7 app.py)*

> **AGENT: app.py already implements:**
> - Island dropdown (`selected_island` variable, values like `nicobar_island_0`, `nicobar_island_1`, etc.)
> - Year slider (`selected_year` variable, range 2000–2023)
> - Metric charts (CRR, FI, IWFI over time)
>
> **Phase 9 will inject the interactive map as a new tab/section in this exact app.py.
> The `selected_island` and `selected_year` state variables are the bridge between the
> existing dashboard and the new map. Do NOT create a separate app — integrate into app.py.**

---

## Phase 8 — Bonus Analyses

*(Unchanged — see original Phase 8 scripts)*

---

## Phase 9 — Interactive Geospatial Map Module

### Overview

This phase adds a fully interactive Leaflet map panel to the existing Streamlit dashboard.
The map will:
- **Focus and zoom to the island selected in the dropdown** — all other islands are visible but grayed out
- **Show switchable raster layers** for the year selected on the year slider, including Forest Cover, Cumulative Deforestation, Annual Loss Events, and ESA Land Cover
- **Render a custom legend** matching whichever layer is active
- **Remain in sync** with `selected_island` and `selected_year` at all times — no independent state

---

### Phase 9 Architecture

```
scripts/09_prepare_map_tiles.py        ← Pre-render PNG overlays for every island × year × layer
data/processed/map_tiles/
  └── {island_name}/
        └── {year}/
              ├── forest_cover.png           (green/no-data)
              ├── deforestation_cumulative.png  (red gradient by year)
              ├── annual_loss.png            (yellow flash for single-year events)
              └── esa_landcover.png          (multi-class ESA colour scheme)
data/processed/island_bounds.geojson   ← WGS84 island boundary polygons for Folium GeoJSON overlay
map_component.py                       ← Self-contained map builder; imported by app.py
app.py                                 ← Existing dashboard; Phase 9 injects map tab here
```

**Why pre-render?** Converting a clipped raster to a PNG at Streamlit runtime for every
interaction would take 3–8 seconds per interaction. Pre-rendering reduces live map updates
to <200 ms (pure Python dict lookups + folium JSON assembly).

---

### Step 9.1 — Pre-Render Map Tiles

**AGENT PROMPT:**
> *"Execute `scripts/09_prepare_map_tiles.py`. For each island in `andaman_islands.gpkg`
> and for each year 2000–2023, clip the relevant rasters, colourise them, and write PNG
> images to `data/processed/map_tiles/{island_name}/{year}/`. Also export
> `data/processed/island_bounds.geojson` with WGS84 island polygons.
> Skip any island×year combination that already exists on disk."*

```python
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
```

---

### Step 9.2 — Map Component Module

**AGENT PROMPT:**
> *"Create `map_component.py` exactly as written. This module exposes a single public
> function `build_island_map(selected_island, selected_year, active_layer)` that returns
> a folium.Map object ready for `st_folium()`. It must not import Streamlit — it is a
> pure map builder. All file I/O must be guarded with existence checks and must never
> crash if a tile is missing."*

```python
# map_component.py
"""
Interactive map builder for the Andaman & Nicobar Forest dashboard.

PUBLIC API
----------
build_island_map(selected_island: str, selected_year: int, active_layer: str)
    → folium.Map

Parameters
----------
selected_island : str
    Island key matching the dropdown (e.g. "nicobar_island_0").
selected_year   : int
    Year from the year slider (2000–2023).
active_layer    : str
    One of: "forest_cover" | "deforestation_cumulative" |
            "annual_loss" | "esa_landcover"

Returns
-------
folium.Map
    Ready to be passed to st_folium(map_obj, use_container_width=True).
"""

import os
import json
import base64
import folium
import geopandas as gpd
from branca.colormap import LinearColormap
from branca.element import Figure

# ── Paths ──────────────────────────────────────────────────────────────────────
TILE_DIR    = "data/processed/map_tiles"
BOUNDS_FILE = "data/processed/island_bounds.geojson"

# ── Layer display metadata ─────────────────────────────────────────────────────
LAYER_META = {
    "forest_cover": {
        "label":   "🌲 Forest Cover",
        "opacity": 0.75,
        "legend_colours": ["#00000000", "#228B22"],
        "legend_caption": "Forest Cover",
        "legend_ticks":   ["No Forest", "Forest"],
    },
    "deforestation_cumulative": {
        "label":   "🔴 Cumulative Deforestation",
        "opacity": 0.80,
        "legend_colours": ["#A01E1E", "#FF1E1E"],
        "legend_caption": "Deforestation (cumulative to year)",
        "legend_ticks":   ["Earliest Loss", "Most Recent Loss"],
    },
    "annual_loss": {
        "label":   "🟠 Annual Loss Events",
        "opacity": 0.85,
        "legend_colours": ["#00000000", "#FFA500"],
        "legend_caption": "Loss Events in Selected Year",
        "legend_ticks":   ["No Loss", "Loss This Year"],
    },
    "esa_landcover": {
        "label":   "🗺️ ESA Land Cover (2021)",
        "opacity": 0.70,
        "legend_colours": None,   # Custom categorical legend injected separately
        "legend_caption": "ESA WorldCover 2021",
        "legend_ticks":   None,
    },
}

# ESA categorical legend items for the HTML legend block
ESA_LEGEND_HTML = """
<div style="font-family:sans-serif; font-size:12px; line-height:1.8;">
  <b>ESA WorldCover 2021</b><br>
  <span style="background:#006400;display:inline-block;width:14px;height:14px;margin-right:6px;"></span>Tree Cover<br>
  <span style="background:#96C864;display:inline-block;width:14px;height:14px;margin-right:6px;"></span>Shrubland<br>
  <span style="background:#DCDC50;display:inline-block;width:14px;height:14px;margin-right:6px;"></span>Grassland<br>
  <span style="background:#E6B43C;display:inline-block;width:14px;height:14px;margin-right:6px;"></span>Cropland<br>
  <span style="background:#B43C3C;display:inline-block;width:14px;height:14px;margin-right:6px;"></span>Built-up<br>
  <span style="background:#D2BE96;display:inline-block;width:14px;height:14px;margin-right:6px;"></span>Bare / Sparse<br>
  <span style="background:#4682B4;display:inline-block;width:14px;height:14px;margin-right:6px;"></span>Water Bodies<br>
</div>
"""

# ── Helpers ────────────────────────────────────────────────────────────────────

def _png_to_data_uri(png_path: str) -> str | None:
    """Read a PNG file and return it as a base64 data URI for ImageOverlay."""
    if not os.path.exists(png_path):
        return None
    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

def _load_bounds(island_key: str) -> dict | None:
    """Load pre-computed WGS84 bounds for an island."""
    meta_path = os.path.join(TILE_DIR, island_key, "bounds.json")
    if not os.path.exists(meta_path):
        return None
    with open(meta_path) as f:
        return json.load(f)

def _tile_path(island_key: str, year: int, layer: str) -> str:
    return os.path.join(TILE_DIR, island_key, str(year), f"{layer}.png")

def _add_legend(fmap: folium.Map, layer: str) -> None:
    """Inject a floating HTML legend into the map."""
    meta = LAYER_META.get(layer, {})

    if layer == "esa_landcover":
        legend_html = f"""
        <div style="position:fixed;bottom:30px;right:12px;z-index:9999;
                    background:white;padding:10px;border-radius:6px;
                    border:1px solid #ccc;box-shadow:2px 2px 6px rgba(0,0,0,.3);">
          {ESA_LEGEND_HTML}
        </div>
        """
    else:
        ticks    = meta.get("legend_ticks", ["Low", "High"])
        colours  = meta.get("legend_colours", ["#ffffff", "#000000"])
        caption  = meta.get("legend_caption", layer)
        gradient = ", ".join(colours)
        legend_html = f"""
        <div style="position:fixed;bottom:30px;right:12px;z-index:9999;
                    background:white;padding:10px;border-radius:6px;
                    border:1px solid #ccc;box-shadow:2px 2px 6px rgba(0,0,0,.3);
                    font-family:sans-serif;font-size:12px;min-width:160px;">
          <b>{caption}</b><br>
          <div style="height:12px;width:140px;
                      background:linear-gradient(to right,{gradient});
                      margin:6px 0;border-radius:3px;"></div>
          <div style="display:flex;justify-content:space-between;width:140px;">
            <span>{ticks[0]}</span><span>{ticks[-1]}</span>
          </div>
        </div>
        """

    fmap.get_root().html.add_child(folium.Element(legend_html))

# ── Public API ─────────────────────────────────────────────────────────────────

def build_island_map(
    selected_island: str,
    selected_year:   int,
    active_layer:    str = "forest_cover",
) -> folium.Map:
    """
    Build and return a fully configured folium.Map for the given island,
    year, and active layer. Safe to call with invalid inputs — returns a
    default-centred map with a warning tooltip if data is missing.
    """

    # ── 1. Load island boundary GeoJSON ───────────────────────────────────────
    all_islands_gdf = None
    if os.path.exists(BOUNDS_FILE):
        all_islands_gdf = gpd.read_file(BOUNDS_FILE)

    # ── 2. Determine map centre and zoom ──────────────────────────────────────
    DEFAULT_CENTRE = [9.0, 92.8]   # Andaman & Nicobar archipelago centroid
    DEFAULT_ZOOM   = 7

    bounds = _load_bounds(selected_island)
    if bounds:
        centre_lat = (bounds["south"] + bounds["north"]) / 2
        centre_lon = (bounds["west"]  + bounds["east"])  / 2
        # Rough zoom: tighter for small islands
        span_deg = max(
            bounds["north"] - bounds["south"],
            bounds["east"]  - bounds["west"]
        )
        if span_deg < 0.05:
            zoom = 13
        elif span_deg < 0.15:
            zoom = 11
        elif span_deg < 0.5:
            zoom = 10
        else:
            zoom = 9
    else:
        centre_lat, centre_lon = DEFAULT_CENTRE
        zoom = DEFAULT_ZOOM

    # ── 3. Create base map ────────────────────────────────────────────────────
    fmap = folium.Map(
        location=[centre_lat, centre_lon],
        zoom_start=zoom,
        tiles=None,           # We add tiles manually as named layer-control entries
        control_scale=True,
    )

    # Base tile layers (user can switch basemap independently of data layers)
    folium.TileLayer(
        tiles="CartoDB positron",
        name="Basemap: Light (CartoDB)",
        attr="© CartoDB © OpenStreetMap contributors",
        show=True,
    ).add_to(fmap)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
              "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Basemap: Satellite Imagery",
        attr="Esri, Maxar, Earthstar Geographics",
        show=False,
    ).add_to(fmap)

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="Basemap: OpenStreetMap",
        attr="© OpenStreetMap contributors",
        show=False,
    ).add_to(fmap)

    # ── 4. Island boundary GeoJSON overlay ───────────────────────────────────
    if all_islands_gdf is not None:
        def island_style(feature):
            is_selected = (
                feature["properties"].get("island_key") == selected_island
            )
            return {
                "fillColor":   "#2ecc71" if is_selected else "#95a5a6",
                "color":       "#27ae60" if is_selected else "#7f8c8d",
                "weight":      2.5       if is_selected else 0.8,
                "fillOpacity": 0.12      if is_selected else 0.05,
                "opacity":     1.0       if is_selected else 0.5,
            }

        def island_highlight(feature):
            return {
                "weight":      3,
                "color":       "#1abc9c",
                "fillOpacity": 0.25,
            }

        folium.GeoJson(
            all_islands_gdf.__geo_interface__,
            name="Island Boundaries",
            style_function=island_style,
            highlight_function=island_highlight,
            tooltip=folium.GeoJsonTooltip(
                fields=["island_name"],
                aliases=["Island:"],
                sticky=False,
                style="font-family:sans-serif;font-size:13px;",
            ),
        ).add_to(fmap)

    # ── 5. Raster data layer (active_layer only, for selected island×year) ───
    tile_png = _tile_path(selected_island, selected_year, active_layer)
    data_uri = _png_to_data_uri(tile_png)
    meta     = LAYER_META.get(active_layer, {})

    if data_uri and bounds:
        folium.raster_layers.ImageOverlay(
            image=data_uri,
            bounds=[
                [bounds["south"], bounds["west"]],
                [bounds["north"], bounds["east"]],
            ],
            name=meta.get("label", active_layer),
            opacity=meta.get("opacity", 0.75),
            cross_origin=False,
            zindex=10,
            interactive=False,
        ).add_to(fmap)
    elif not data_uri:
        # No tile available — add a marker to explain
        folium.Marker(
            location=[centre_lat, centre_lon],
            popup=folium.Popup(
                f"No data tile for: {selected_island} / {selected_year} / {active_layer}",
                max_width=260,
            ),
            icon=folium.Icon(color="gray", icon="info-sign"),
        ).add_to(fmap)

    # ── 6. Fit map to island bounds if available ───────────────────────────────
    if bounds:
        fmap.fit_bounds([
            [bounds["south"], bounds["west"]],
            [bounds["north"], bounds["east"]],
        ])

    # ── 7. Legend ─────────────────────────────────────────────────────────────
    _add_legend(fmap, active_layer)

    # ── 8. Layer control (must be last) ───────────────────────────────────────
    folium.LayerControl(collapsed=False, position="topright").add_to(fmap)

    return fmap
```

---

### Step 9.3 — Integrate Map Into app.py

**AGENT PROMPT:**
> *"Open the existing `app.py` and add the map section below the existing metric charts.
> Use `st.tabs()` so the user can switch between 'Charts' and 'Map' without losing the
> island/year state. The map tab must read `selected_island` and `selected_year` from the
> variables already set by the sidebar. Do NOT duplicate the sidebar — it already exists."*

Add the following block to `app.py`. Insert it **after** the existing `st.markdown("---")`
line that precedes the charts section, replacing the direct chart rendering with a tabbed
layout. The sidebar code (`selected_island`, `selected_year`) is unchanged.

```python
# ─────────────────────────────────────────────────────────────────────────────
# Phase 9 — IMPORT (add near top of app.py, with other imports)
# ─────────────────────────────────────────────────────────────────────────────
from streamlit_folium import st_folium
from map_component import build_island_map, LAYER_META

# ─────────────────────────────────────────────────────────────────────────────
# Phase 9 — TABS LAYOUT (replaces the flat chart section in app.py)
# Insert this block where charts currently begin.
# ─────────────────────────────────────────────────────────────────────────────

tab_charts, tab_map = st.tabs(["📊 Metric Charts", "🗺️ Interactive Map"])

# ── Tab 1: Metric Charts (paste existing chart code here, unchanged) ──────────
with tab_charts:
    # [existing CRR chart, FI chart, IWFI trajectory, raw data table blocks go here]
    pass  # AGENT: replace this `pass` with the existing chart code blocks

# ── Tab 2: Interactive Map ────────────────────────────────────────────────────
with tab_map:

    st.markdown(
        f"**Showing:** `{selected_island}` &nbsp;|&nbsp; **Year:** `{selected_year}`"
    )

    # Layer selector — presented as radio buttons so only one layer is active
    layer_options = {v["label"]: k for k, v in LAYER_META.items()}
    active_label  = st.radio(
        "Map Layer",
        options=list(layer_options.keys()),
        index=0,
        horizontal=True,
        help=(
            "🌲 Forest Cover — binary forest in selected year\n\n"
            "🔴 Cumulative Deforestation — all loss events up to selected year\n\n"
            "🟠 Annual Loss Events — loss that occurred only in selected year\n\n"
            "🗺️ ESA Land Cover — multi-class 2021 land cover snapshot"
        ),
    )
    active_layer = layer_options[active_label]

    # Year note for ESA layer (static snapshot)
    if active_layer == "esa_landcover":
        st.caption(
            "ℹ️ ESA WorldCover is a 2021 snapshot and does not change with the year slider."
        )

    # Build and render map
    with st.spinner("Rendering map…"):
        fmap = build_island_map(
            selected_island=selected_island,
            selected_year=selected_year,
            active_layer=active_layer,
        )

    map_data = st_folium(
        fmap,
        use_container_width=True,
        height=540,
        returned_objects=[],   # We don't need click callbacks — keep it read-only
        key=f"map_{selected_island}_{selected_year}_{active_layer}",
    )

    # Layer description block
    LAYER_DESCRIPTIONS = {
        "forest_cover": (
            "Binary forest cover derived from the Hansen GFC forest mask. "
            "Green pixels are classified as forested (≥ 30% canopy cover) "
            "in the selected year."
        ),
        "deforestation_cumulative": (
            "Cumulative tree cover loss from 2001 up to the selected year. "
            "Darker red indicates earlier loss; brighter red indicates more "
            "recent events. Pixels with no loss are transparent."
        ),
        "annual_loss": (
            "Loss events that occurred specifically in the selected year. "
            "Orange pixels represent newly deforested areas in that single "
            "calendar year. Not available for year 2000 (baseline)."
        ),
        "esa_landcover": (
            "ESA WorldCover 2021 land classification. This is a static "
            "snapshot and does not respond to the year slider. Useful for "
            "cross-referencing forest patches with surrounding land use."
        ),
    }
    st.info(LAYER_DESCRIPTIONS.get(active_layer, ""))

    st.caption(
        "Map: Folium / Leaflet.js | Raster: Hansen GFC, ESA WorldCover | "
        "Boundaries: GADM | CRS: EPSG:4326 (display), EPSG:32646 (analysis)"
    )
```

---

### Step 9.4 — Verify Map Tile Coverage

**AGENT PROMPT:**
> *"Run `scripts/09_verify_tiles.py` after `09_prepare_map_tiles.py` completes. It must
> print the tile coverage table and exit non-zero if any island has zero tiles."*

```python
# scripts/09_verify_tiles.py
"""
Verify that map tiles were generated correctly for all islands and years.
Reports coverage per island × layer.
"""
import os
import sys

TILE_DIR = "data/processed/map_tiles"
YEARS    = list(range(2000, 2024))
LAYERS   = ["forest_cover", "deforestation_cumulative", "annual_loss", "esa_landcover"]

if not os.path.isdir(TILE_DIR):
    sys.exit(f"ABORT: {TILE_DIR} does not exist. Run 09_prepare_map_tiles.py first.")

islands = [d for d in os.listdir(TILE_DIR)
           if os.path.isdir(os.path.join(TILE_DIR, d))]

if not islands:
    sys.exit("ABORT: No island subdirectories found in map_tiles/.")

print(f"\n{'Island':<30} {'Years':>5}  {'fc':>4}  {'dc':>4}  {'al':>4}  {'esa':>4}")
print("-" * 60)

all_ok = True
for island in sorted(islands):
    counts = {layer: 0 for layer in LAYERS}
    years_found = 0
    for year in YEARS:
        year_dir = os.path.join(TILE_DIR, island, str(year))
        if os.path.isdir(year_dir):
            years_found += 1
            for layer in LAYERS:
                if os.path.exists(os.path.join(year_dir, f"{layer}.png")):
                    counts[layer] += 1

    ok = years_found > 0
    if not ok:
        all_ok = False

    flag = "✅" if ok else "❌"
    print(
        f"{flag} {island:<28} {years_found:>5}  "
        f"{counts['forest_cover']:>4}  "
        f"{counts['deforestation_cumulative']:>4}  "
        f"{counts['annual_loss']:>4}  "
        f"{counts['esa_landcover']:>4}"
    )

print()
if all_ok:
    print("✅ Phase 9 tile verification passed.")
else:
    sys.exit("ABORT: Some islands have zero tiles. Re-run 09_prepare_map_tiles.py.")
```

---

### Step 9.5 — Performance & Edge Case Rules

**AGENT: These rules apply ONLY to Phase 9 code and override any general rule
where they conflict.**

| Rule | Requirement |
|------|-------------|
| **Tile caching** | `09_prepare_map_tiles.py` must check `os.path.exists()` before writing any PNG. Never overwrite existing tiles. |
| **Missing tiles** | `map_component.py` must never raise an exception on a missing tile. Fallback to a grey marker with an explanatory popup. |
| **Year 2000** | `annual_loss` layer does not exist for year 2000 (no loss data for baseline year). Write an empty transparent PNG placeholder or skip. Show `st.caption("Annual loss not available for baseline year 2000.")` in the UI. |
| **ESA layer** | ESA WorldCover is a single 2021 snapshot. The PNG at `data/processed/map_tiles/{island}/2021/esa_landcover.png` should be symlinked or copied to all other year directories, or `map_component.py` should always look up 2021 regardless of `selected_year`. Use the copy approach (not symlinks) for cross-platform compatibility. |
| **CRS of PNGs** | PNG overlays are in EPSG:4326 coordinate space. The `bounds.json` stores WGS84 extents. Never use UTM 46N coordinates in bounds.json or the image will be placed incorrectly on the Leaflet map. |
| **Folium key** | Always set `key=f"map_{selected_island}_{selected_year}_{active_layer}"` in `st_folium()`. This forces Streamlit to re-render the map widget when any control changes, preventing stale cached renders. |
| **Large islands** | If an island's clipped raster exceeds 2000×2000 pixels, downsample to max 1500px on the longest axis before saving the PNG. Use `PIL.Image.thumbnail()`. |
| **Memory** | `09_prepare_map_tiles.py` processes one island×year at a time. Never accumulate arrays across the loop. Call `del arr` and Python's gc where needed. |

---

### Step 9.6 — Execution Order for Phase 9

```bash
# After all previous phases (0–8) are complete:
python scripts/09_prepare_map_tiles.py    # ~15–60 min depending on island count
python scripts/09_verify_tiles.py         # Must exit 0 before proceeding
streamlit run app.py                      # Map tab is now live
```

---

## Global Quality Rules

**AGENT: These rules apply to EVERY script, EVERY file write, without exception.**

| Rule | What to Do |
|------|------------|
| **CRS** | Always reproject to EPSG:32646 before any metric, distance, or area calculation. Decimal degrees cannot be used for spatial metrics. Map display uses EPSG:4326 — these are two separate coordinate contexts. |
| **NoData** | NoData = 255 in all rasters. Ocean pixels must NEVER enter metric calculations. Always pass `nodata=255` to pylandstats. In map PNGs, NoData pixels must be fully transparent (alpha = 0). |
| **Memory** | Never call `src.read()` on a full multi-GB TIF without windowing. Always use `rasterio.block_windows()` or clip to island first. |
| **Logging** | Every script must print its final line as `✅ Phase N complete.` and raise an exception on failure. |
| **Outputs** | Every output file must be verified to exist and have > 0 rows/bytes before the phase is declared done. |
| **Overwrite** | Check `os.path.exists()` before recomputing expensive outputs. Skip and print `SKIP (exists)` if found. |
| **Float Safety** | Always guard against division by zero: `np.where(denom > 0, num/denom, np.nan)`. |
| **Raster Alignment** | After reprojection, assert that treecover2000 and lossyear have the same `.transform` and `.shape`. |
| **Map State Sync** | `selected_island` and `selected_year` are the single source of truth. The map must never maintain its own copies of these variables. |

---

## Deliverables Checklist

Run this at the end to confirm everything was produced:

```python
# scripts/99_final_check.py
import os, sys

REQUIRED = {
    "Forest Masks (24)":      [f"data/processed/forest_masks/forest_mask_{y}.tif"
                                for y in range(2000, 2024)],
    "Island Metadata":        ["data/processed/island_metadata.csv"],
    "Landscape Metrics":      ["results/tables/island_metrics_timeseries.csv"],
    "Novel Metrics":          ["results/tables/novel_metrics.csv"],
    "Regression Summary":     ["results/tables/regression_summary.txt"],
    "Cluster Labels":         ["results/tables/cluster_labels.csv"],
    "Keystone Patches":       ["results/tables/keystone_patches.csv"],
    "Island GeoJSON":         ["data/processed/island_bounds.geojson"],   # Phase 9
    "Map Tiles Dir":          ["data/processed/map_tiles"],               # Phase 9
    "Map Component":          ["map_component.py"],                        # Phase 9
    "Figures":                [f"results/figures/fig{i}_{n}.pdf" for i,n in [
                                   (1,"edge_density_by_size"),
                                   (2,"loss_vs_crr_percolation"),
                                   (3,"crr_trajectories_clusters"),
                                   (4,"isolation_drivers"),
                                   (5,"tsunami_edge_density"),
                               ]],
    "Streamlit App":          ["app.py"],
}

all_pass = True
for group, files in REQUIRED.items():
    missing = [f for f in files if not os.path.exists(f)]
    if missing:
        print(f"  ❌ {group}: {len(missing)} missing — {missing[:3]}")
        all_pass = False
    else:
        print(f"  ✅ {group}: all {len(files)} present")

if all_pass:
    print("\n🎉 ALL DELIVERABLES PRESENT. Project is complete.")
else:
    sys.exit("\nABORT: Re-run missing phases.")
```

---

## Execution Order Summary

```
python scripts/00_verify_env.py            ← Must pass before anything else
python scripts/00_scaffold.py
python scripts/01_preprocessing.py        ← Creates 24 forest masks
python scripts/02_island_metadata.py      ← Creates island_metadata.csv
python scripts/03_landscape_metrics.py    ← Longest step (≈2–6 hrs)
python scripts/04_novel_metrics.py        ← FI, CRR, IWFI
python scripts/05_statistical_models.py
python scripts/06_visualization.py
python scripts/08_connectivity.py         ← Bonus
python scripts/09_prepare_map_tiles.py    ← Phase 9: Pre-render map PNGs
python scripts/09_verify_tiles.py         ← Phase 9: Verify coverage
streamlit run app.py                      ← Launch dashboard (Charts + Map tabs)
python scripts/99_final_check.py          ← Verify all outputs
```
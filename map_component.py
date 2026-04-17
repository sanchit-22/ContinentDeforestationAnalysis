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

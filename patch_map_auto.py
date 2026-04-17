import re
with open("map_component.py", "r", encoding="utf-8") as f:
    code = f.read()

# Replace API signature
new_api = """def build_island_map(
    selected_island,
    selected_year:   int,
    active_layer:    str = "forest_cover",
) -> folium.Map:"""
code = re.sub(r'def build_island_map\([^)]*\)\s*->\s*folium\.Map:', new_api, code, flags=re.MULTILINE)

# Now completely replace the body of the function.
# The body starts with '    """\n    Build and return a fully configured' 
# or similar, and ends at 'return fmap'
# Find the index of the start of the body
function_start = code.find('def build_island_map(')
docstring_end = code.find('    """', code.find('    """', function_start) + 3) + 7

new_body = """
    # Normalize selected_islands to a list
    islands_list = [selected_island] if isinstance(selected_island, str) else selected_island

    # ── 1. Load island boundary GeoJSON ───────────────────────────────────────
    all_islands_gdf = None
    if os.path.exists(BOUNDS_FILE):
        import geopandas as gpd
        all_islands_gdf = gpd.read_file(BOUNDS_FILE)

    # ── 2. Determine map centre and zoom ──────────────────────────────────────
    DEFAULT_CENTRE = [9.0, 92.8]   # Andaman & Nicobar archipelago centroid
    DEFAULT_ZOOM   = 7

    all_bounds_dict = {}
    valid_souths, valid_norths, valid_wests, valid_easts = [], [], [], []
    for island_key in islands_list:
        b = _load_bounds(island_key)
        if b:
            all_bounds_dict[island_key] = b
            valid_souths.append(b["south"])
            valid_norths.append(b["north"])
            valid_wests.append(b["west"])
            valid_easts.append(b["east"])

    global_bounds = None
    if valid_souths:
        global_bounds = {
            "south": min(valid_souths),
            "north": max(valid_norths),
            "west": min(valid_wests),
            "east": max(valid_easts)
        }
        centre_lat = (global_bounds["south"] + global_bounds["north"]) / 2
        centre_lon = (global_bounds["west"]  + global_bounds["east"])  / 2
        span_deg = max(
            global_bounds["north"] - global_bounds["south"],
            global_bounds["east"]  - global_bounds["west"]
        )
        if span_deg < 0.05: zoom = 13
        elif span_deg < 0.15: zoom = 11
        elif span_deg < 0.5: zoom = 10
        elif span_deg < 1.0: zoom = 8
        else: zoom = 7
    else:
        centre_lat, centre_lon = DEFAULT_CENTRE
        zoom = DEFAULT_ZOOM

    # ── 3. Create base map ────────────────────────────────────────────────────
    fmap = folium.Map(
        location=[centre_lat, centre_lon],
        zoom_start=zoom,
        tiles=None,
        control_scale=True,
    )

    folium.TileLayer(
        tiles="CartoDB positron",
        name="Basemap: Light (CartoDB)",
        attr="© CartoDB © OpenStreetMap contributors",
        show=True,
    ).add_to(fmap)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Basemap: Esri Satellite",
        attr="Esri, Maxar, Earthstar Geographics, etc.",
        show=False,
    ).add_to(fmap)

    # ── 4. Island boundary GeoJSON overlay ───────────────────────────────────
    if all_islands_gdf is not None:
        def get_island_style(feature):
            is_selected = feature["properties"]["island_key"] in islands_list
            return {
                "fillColor":   "#2ecc71" if is_selected else "#95a5a6",
                "color":       "#27ae60" if is_selected else "#7f8c8d",
                "weight":      2.5       if is_selected else 0.8,
                "fillOpacity": 0.12      if is_selected else 0.05,
                "opacity":     1.0       if is_selected else 0.5,
            }

        def island_highlight(feature):
            return {"weight": 3, "color": "#1abc9c", "fillOpacity": 0.25}

        folium.GeoJson(
            all_islands_gdf.__geo_interface__,
            name="Island Boundaries",
            style_function=get_island_style,
            highlight_function=island_highlight,
            tooltip=folium.GeoJsonTooltip(
                fields=["island_name"],
                aliases=["Island:"],
                sticky=False,
                style="font-family:sans-serif;font-size:13px;",
            ),
        ).add_to(fmap)

    # ── 5. Raster data layer (active_layer only, for selected islands×year) ───
    meta = LAYER_META.get(active_layer, {})
    for island_key in islands_list:
        b = all_bounds_dict.get(island_key)
        if not b: continue
        
        tile_png = _tile_path(island_key, selected_year, active_layer)
        data_uri = _png_to_data_uri(tile_png)
        
        if data_uri:
            folium.raster_layers.ImageOverlay(
                image=data_uri,
                bounds=[[b["south"], b["west"]], [b["north"], b["east"]]],
                name=f"{meta.get('label', active_layer)} - {island_key}",
                opacity=meta.get("opacity", 0.75),
                cross_origin=False,
                zindex=10,
                interactive=False,
            ).add_to(fmap)
        else:
            folium.Marker(
                location=[(b["south"]+b["north"])/2, (b["west"]+b["east"])/2],
                popup=folium.Popup(f"No data tile for: {island_key} / {selected_year} / {active_layer}", max_width=260),
                icon=folium.Icon(color="gray", icon="info-sign"),
            ).add_to(fmap)

    # ── 6. Fit map to global bounds if available ───────────────────────────────
    if global_bounds:
        fmap.fit_bounds([
            [global_bounds["south"], global_bounds["west"]],
            [global_bounds["north"], global_bounds["east"]],
        ])

    # ── 7. Legend ─────────────────────────────────────────────────────────────
    _add_legend(fmap, active_layer)

    # ── 8. Layer control (must be last) ───────────────────────────────────────
    folium.LayerControl(collapsed=False, position="topright").add_to(fmap)

    return fmap
"""

code = code[:docstring_end] + new_body
with open("map_component.py", "w", encoding="utf-8") as f:
    f.write(code)
print("Rewrite of map_component complete.")

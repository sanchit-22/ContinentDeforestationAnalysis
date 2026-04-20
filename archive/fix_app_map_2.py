with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Replace from line 256 to 286 (0-indexed 255 to 285)
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if 'if view_level == "Individual island":' in line and "selected_island_key =" in lines[i+1]:
        start_idx = i
    if 'st.info("🗺️ **Raster maps are generated' in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    new_chunk = """    if view_level == "Individual island":
        selected_island_keys = selected.lower().replace(" ", "_").replace(".", "").replace(",", "")
        string_key = selected_island_keys
    else:
        # group_meta contains all the islands for the selected group
        raw_names = group_meta["island_name"].dropna().unique().tolist()
        selected_island_keys = [n.lower().replace(" ", "_").replace(".", "").replace(",", "") for n in raw_names]
        # Just a unique string for the folium key
        string_key = "aggregate_" + str(hash("".join(selected_island_keys)))

    with st.spinner("Rendering map…"):
        fmap = build_island_map(
            selected_island=selected_island_keys,
            selected_year=selected_year,
            active_layer=active_layer,
        )

    map_data = st_folium(
        fmap,
        use_container_width=True,
        height=540,
        returned_objects=[],
        key=f"map_{string_key}_{selected_year}_{active_layer}",
    )

    LAYER_DESCRIPTIONS = {
        "forest_cover": "Binary forest cover derived from the Hansen GFC forest mask. Green pixels are classified as forested (≥ 30% canopy cover) in the selected year.",
        "deforestation_cumulative": "Cumulative tree cover loss from 2001 up to the selected year. Darker red indicates earlier loss; brighter red indicates more recent events.",
        "annual_loss": "Loss events that occurred specifically in the selected year. Orange pixels represent newly deforested areas in that single calendar year. Not available for year 2000 (baseline).",
        "esa_landcover": "ESA WorldCover 2021 land classification. This is a static snapshot and does not respond to the year slider."
    }
    st.info(LAYER_DESCRIPTIONS.get(active_layer, ""))

    st.caption(
        "Map: Folium / Leaflet.js | Raster: Hansen GFC, ESA WorldCover | "
        "Boundaries: GADM | CRS: EPSG:4326 (display)"
    )\n"""
    
    lines[start_idx:end_idx+1] = [new_chunk]
    with open("app.py", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Replaced lines successfully.")
else:
    print(f"Could not find indices: start_idx={start_idx}, end_idx={end_idx}")

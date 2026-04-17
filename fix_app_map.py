with open("app.py", "r", encoding="utf-8") as f:
    app_text = f.read()

orig_map = """    if view_level == "Individual island":
        selected_island_key = selected.lower().replace(" ", "_").replace(".", "").replace(",", "")
        with st.spinner("Rendering map…"):
            fmap = build_island_map(
                selected_island=selected_island_key,
                selected_year=selected_year,
                active_layer=active_layer,
            )

        map_data = st_folium(
            fmap,
            use_container_width=True,
            height=540,
            returned_objects=[],
            key=f"map_{selected_island_key}_{selected_year}_{active_layer}",
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
        )
    else:
        st.info("🗺️ **Raster maps are generated at the individual island level.** To view high-resolution forest cover tiles, please select 'Individual island' in the View Level toggle from the sidebar.")"""

new_map = """    if view_level == "Individual island":
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
    )"""

if orig_map in app_text:
    app_text = app_text.replace(orig_map, new_map)
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(app_text)
    print("app patched successfully")
else:
    print("could not find orig_map in app.py")

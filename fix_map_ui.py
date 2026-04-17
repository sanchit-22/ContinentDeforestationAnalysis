with open("app.py", "r", encoding="utf-8") as f:
    app_text = f.read()

orig_map_ui = """with tab_map:
    # Use selected and year_range instead of selected_island/selected_year
    selected_year = year_range[1]  # Using upper bound of slider as the selected map year

    st.markdown(
        f"**Showing:** `{selected}` &nbsp;|&nbsp; **Year:** `{selected_year}`"
    )

    # Layer selector — presented as radio buttons so only one layer is active
    layer_options = {v["label"]: k for k, v in LAYER_META.items()}
    active_label  = st.radio(
        "Map Layer",
        options=list(layer_options.keys()),
        index=0,
        horizontal=True,
        help=(
            "🌲 Forest Cover — binary forest in selected year\\n\\n"
            "🔴 Cumulative Deforestation — all loss events up to selected year\\n\\n"
            "🟠 Annual Loss Events — loss that occurred only in selected year\\n\\n"
            "🗺️ ESA Land Cover — multi-class 2021 land cover snapshot"
        ),
    )
    active_layer = layer_options[active_label]

    if active_layer == "esa_landcover":
        st.caption(
            "ℹ️ ESA WorldCover is a 2021 snapshot and does not change with the year slider."
        )

    if view_level == "Individual island":
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
    else:
        st.info("🗺️ **Raster maps are generated at the individual island level.** To view high-resolution forest cover tiles, please select 'Individual island' in the View Level toggle from the sidebar.")

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

new_map_ui = """with tab_map:
    # Use selected and year_range instead of selected_island/selected_year
    selected_year = year_range[1]  # Using upper bound of slider as the selected map year

    st.markdown(
        f"**Showing:** `{selected}` &nbsp;|&nbsp; **Year:** `{selected_year}`"
    )

    if view_level == "Individual island":
        # Layer selector — presented as radio buttons so only one layer is active
        layer_options = {v["label"]: k for k, v in LAYER_META.items()}
        active_label  = st.radio(
            "Map Layer",
            options=list(layer_options.keys()),
            index=0,
            horizontal=True,
            help=(
                "🌲 Forest Cover — binary forest in selected year\\n\\n"
                "🔴 Cumulative Deforestation — all loss events up to selected year\\n\\n"
                "🟠 Annual Loss Events — loss that occurred only in selected year\\n\\n"
                "🗺️ ESA Land Cover — multi-class 2021 land cover snapshot"
            ),
        )
        active_layer = layer_options[active_label]

        if active_layer == "esa_landcover":
            st.caption(
                "ℹ️ ESA WorldCover is a 2021 snapshot and does not change with the year slider."
            )

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
        st.info("🗺️ **Raster maps are generated at the individual island level.** To view high-resolution forest cover tiles, please select 'Individual island' in the View Level toggle from the sidebar.")
"""

if orig_map_ui in app_text:
    app_text = app_text.replace(orig_map_ui, new_map_ui)
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(app_text)
    print("Patched map ui")
else:
    print("Could not find orig_map_ui")

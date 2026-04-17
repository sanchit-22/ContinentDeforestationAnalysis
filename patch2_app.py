with open("app.py", "r", encoding="utf-8") as f:
    app_text = f.read()

# Replace map logic to handle aggregate views gracefully
map_orig = """    selected_island_key = selected.lower().replace(" ", "_").replace(".", "").replace(",", "")
    selected_year = year_range[1]  # Using upper bound of slider as the selected map year

    st.markdown(
        f"**Showing:** `{selected}` &nbsp;|&nbsp; **Year:** `{selected_year}`
    )"""

map_new = """    selected_year = year_range[1]  # Using upper bound of slider as the selected map year

    st.markdown(
        f"**Showing:** `{selected}` &nbsp;|&nbsp; **Year:** `{selected_year}`"
    )"""

app_text = app_text.replace(map_orig, map_new)

map_orig2 = """    with st.spinner("Rendering map…"):
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
    )"""

map_new2 = """    if view_level == "Individual island":
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
        st.info("🗺️ **Raster maps are generated at the individual island level.** To view high-resolution forest cover tiles, please select 'Individual island' in the View Level toggle from the sidebar.")"""

app_text = app_text.replace(map_orig2, map_new2)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(app_text)

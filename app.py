# app.py
"""
Streamlit Interactive Dashboard — Andaman Forest Fragmentation
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from streamlit_folium import st_folium
from map_component import build_island_map, LAYER_META

st.set_page_config(page_title="Andaman Forest Fragmentation", layout="wide")
st.title("🌿 Andaman & Nicobar — Forest Fragmentation Explorer")
st.caption("Data: Hansen GFC 2000–2023 | ESA WorldCover 2021 | Metrics: pylandstats")

@st.cache_data
def load_data():
    df  = pd.read_csv("results/tables/novel_metrics.csv")
    meta = pd.read_csv("data/processed/island_metadata.csv")
    return df, meta

df, meta = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.header("🗺️ Controls")
islands  = sorted(df["island_name"].dropna().unique())
selected = st.sidebar.selectbox("Select Island", islands)
year_range = st.sidebar.slider("Year Range", 2000, 2023, (2000, 2023))

island_df = df[
    (df["island_name"] == selected) &
    (df["year"].between(*year_range))
].sort_values("year")

# ── Key Statistics ─────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
irow = meta[meta["island_name"] == selected]

with col1:
    area = irow["area_km2"].values[0] if len(irow) else "N/A"
    st.metric("Island Area", f"{area:.1f} km²" if area != "N/A" else area)
with col2:
    dist = irow["dist_mainland_km"].values[0] if len(irow) else "N/A"
    st.metric("Distance to Mainland", f"{dist:.0f} km" if dist != "N/A" else dist)
with col3:
    latest_crr = island_df["CRR"].dropna().iloc[-1] if not island_df["CRR"].dropna().empty else np.nan
    st.metric("Latest CRR", f"{latest_crr:.3f}" if not np.isnan(latest_crr) else "N/A",
              help="Core Retention Ratio — 1.0=no edge effect, 0=all edge")
with col4:
    latest_loss = island_df["cumulative_loss_pct"].dropna().iloc[-1] if not island_df.empty else np.nan
    st.metric("Cumulative Loss", f"{latest_loss:.5f}%" if not np.isnan(latest_loss) else "N/A")

# ── Charts ────────────────────────────────────────────────────────────────────
tab_charts, tab_map = st.tabs(["📊 Metric Charts", "🗺️ Interactive Map"])

with tab_charts:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Core Retention Ratio (CRR) Over Time")
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(island_df["year"], island_df["CRR"], marker="o", color="#2ecc71",
                markersize=4, linewidth=1.8)
        ax.axhline(0.5, linestyle="--", color="red", linewidth=1, alpha=0.7,
                   label="CRR = 0.5 (critical threshold)")
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("Year")
        ax.set_ylabel("CRR")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close(fig)

    with c2:
        st.subheader("Fragmentation Index (FI) Over Time")
        fig2, ax2 = plt.subplots(figsize=(6, 3))
        ax2.bar(island_df["year"], island_df["FI"].fillna(0),
                color="#e74c3c", alpha=0.75, width=0.7)
        ax2.set_xlabel("Year")
        ax2.set_ylabel("FI = ED × PD / PLAND")
        ax2.grid(True, alpha=0.3, axis="y")
        st.pyplot(fig2)
        plt.close(fig2)

    # ── IWFI trajectory ───────────────────────────────────────────────────────────
    st.subheader("Isolation-Weighted Fragmentation Index (IWFI)")
    fig3, ax3 = plt.subplots(figsize=(10, 3))
    ax3.fill_between(island_df["year"], island_df["IWFI"].fillna(0),
                     alpha=0.45, color="#9b59b6")
    ax3.plot(island_df["year"], island_df["IWFI"].fillna(0), color="#9b59b6", linewidth=1.5)
    ax3.set_xlabel("Year")
    ax3.set_ylabel("IWFI")
    ax3.grid(True, alpha=0.3)
    st.pyplot(fig3)
    plt.close(fig3)

    # ── Raw data table ────────────────────────────────────────────────────────────
    with st.expander("📋 Full Data Table"):
        st.dataframe(island_df.set_index("year").round(4))

with tab_map:
    # Use selected and year_range instead of selected_island/selected_year
    selected_island_key = selected.lower().replace(" ", "_").replace(".", "").replace(",", "")
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
            "🌲 Forest Cover — binary forest in selected year\n\n"
            "🔴 Cumulative Deforestation — all loss events up to selected year\n\n"
            "🟠 Annual Loss Events — loss that occurred only in selected year\n\n"
            "🗺️ ESA Land Cover — multi-class 2021 land cover snapshot"
        ),
    )
    active_layer = layer_options[active_label]

    if active_layer == "esa_landcover":
        st.caption(
            "ℹ️ ESA WorldCover is a 2021 snapshot and does not change with the year slider."
        )

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

st.markdown("---")
st.caption("Built with Streamlit | Data: Hansen GFC, ESA WorldCover, GADM | "
           "Metrics: pylandstats | CRS: EPSG:32646 (UTM 46N)")

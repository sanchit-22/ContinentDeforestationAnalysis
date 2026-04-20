# app.py
"""
Streamlit Interactive Dashboard — Andaman Forest Fragmentation
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import altair as alt
import os
from streamlit_folium import st_folium
from src.components.map_component import build_island_map, LAYER_META

st.set_page_config(page_title="Andaman Forest Fragmentation", layout="wide")
st.title("🌿 Andaman & Nicobar — Forest Fragmentation Explorer")
st.caption("Data: Hansen GFC 2000–2023 | ESA WorldCover 2021 | Metrics: pylandstats")

@st.cache_data
def load_data():
    df  = pd.read_csv("results/tables/novel_metrics.csv")
    meta = pd.read_csv("data/processed/island_metadata.csv")
    df["group_name"] = df["island_name"].str.replace(r"_\d+$", "", regex=True)
    meta["group_name"] = meta["island_name"].str.replace(r"_\d+$", "", regex=True)
    return df, meta

def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    mask = values.notna() & weights.notna()
    if mask.sum() == 0: return np.nan
    v = values[mask].astype(float)
    w = weights[mask].astype(float).clip(lower=0)
    if float(w.sum()) == 0.0: return float(v.mean())
    return float((v * w).sum() / w.sum())

def aggregate_group_timeseries(group_df: pd.DataFrame, group_meta: pd.DataFrame) -> pd.DataFrame:
    years = sorted(group_df["year"].dropna().astype(int).unique())
    if not years or group_meta.empty: return pd.DataFrame()
    group_area_km2 = float(group_meta["area_km2"].sum())
    group_area_ha = group_area_km2 * 100.0
    group_dist_mainland = weighted_mean(group_meta["dist_mainland_km"], group_meta["area_km2"])
    group_name = str(group_meta["group_name"].iloc[0])
    records = []
    for yr in years:
        ydf = group_df[group_df["year"] == yr]
        ta_sum = float(ydf["TA_ha"].fillna(0).sum())
        tca_sum = float(ydf["TCA_ha"].fillna(0).sum())
        pland = (ta_sum / group_area_ha) * 100.0 if group_area_ha > 0 else np.nan
        ed_w = weighted_mean(ydf["ED"], ydf["TA_ha"])
        pd_w = weighted_mean(ydf["PD"], ydf["TA_ha"])
        enn_w = weighted_mean(ydf["ENN_MN_m"], ydf["TA_ha"])
        fi = (ed_w * pd_w / pland) if pd.notna(pland) and pland > 0 else np.nan
        crr = (tca_sum / ta_sum) if ta_sum > 0 else np.nan
        crr = float(np.clip(crr, 0, 1)) if pd.notna(crr) else np.nan
        iwfi = (fi * np.log((0.0 if np.isnan(enn_w) else enn_w) + 1.0) * np.log(group_dist_mainland + 1.0)
            if pd.notna(fi) and pd.notna(group_dist_mainland) else np.nan)
        records.append({"group_name": group_name, "island_name": group_name, "year": int(yr),
            "area_km2": group_area_km2, "dist_mainland_km": group_dist_mainland,
            "TA_ha": ta_sum, "PLAND": pland, "PD": pd_w, "ED": ed_w, "TCA_ha": tca_sum,
            "ENN_MN_m": enn_w, "n_patches": int(ydf["n_patches"].fillna(0).sum()),
            "FI": fi, "CRR": crr, "IWFI": iwfi, "cumulative_loss_pct": ydf["cumulative_loss_pct"].mean()}) # roughly aggregate loss
    return pd.DataFrame(records)

df, meta = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.header("🗺️ Controls")

view_level = st.sidebar.radio("View Level", ["Individual island", "Aggregate island group"])

if view_level == "Individual island":
    islands = sorted(df["island_name"].dropna().unique())
    selected = st.sidebar.selectbox("Select Island", islands)
else:
    group_display = {"Nicobar Islands": "Nicobar", "North and Middle Andaman": "North Andaman", "South Andaman": "South Andaman"}
    groups = sorted(df["group_name"].dropna().unique(), key=lambda g: group_display.get(g, g))
    selected = st.sidebar.selectbox("Select Aggregate Group", groups, format_func=lambda g: group_display.get(g, g))

year_range = st.sidebar.slider("Year Range", 2000, 2023, (2000, 2023))

if view_level == "Individual island":
    island_df = df[(df["island_name"] == selected) & (df["year"].between(*year_range))].sort_values("year")
    irow = meta[meta["island_name"] == selected]
    area_label = "Island Area"
else:
    group_meta = meta[meta["group_name"] == selected]
    island_df = aggregate_group_timeseries(df[df["group_name"] == selected], group_meta)
    if not island_df.empty:
        island_df = island_df[island_df["year"].between(*year_range)].sort_values("year")
    irow = pd.DataFrame([{"area_km2": float(group_meta["area_km2"].sum()) if not group_meta.empty else np.nan,
                          "dist_mainland_km": weighted_mean(group_meta["dist_mainland_km"], group_meta["area_km2"]) if not group_meta.empty else np.nan}])
    area_label = "Aggregate Area"
    selected = f"{group_display.get(selected, selected)} (aggregate)"

# ── Key Statistics ─────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    area = irow["area_km2"].values[0] if len(irow) else "N/A"
    st.metric(area_label, f"{area:.1f} km²" if area != "N/A" and pd.notna(area) else "N/A")
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

    if view_level == "Individual island":
        selected_island_keys = selected.lower().replace(" ", "_").replace(".", "").replace(",", "")
        string_key = selected_island_keys
    else:
        # group_meta contains all the islands for the selected group
        raw_names = group_meta["island_name"].dropna().unique().tolist()
        selected_island_keys = [n.lower().replace(" ", "_").replace(".", "").replace(",", "") for n in raw_names]
        # Just a unique string for the folium key
        string_key = "aggregate_" + "_".join(selected_island_keys[:3])

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
    )

st.markdown("---")
st.caption("Built with Streamlit | Data: Hansen GFC, ESA WorldCover, GADM | "
           "Metrics: pylandstats | CRS: EPSG:32646 (UTM 46N)")
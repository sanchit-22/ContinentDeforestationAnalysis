import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import altair as alt
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
    df["group_name"] = df["island_name"].str.replace(r"_\d+$", "", regex=True)
    meta["group_name"] = meta["island_name"].str.replace(r"_\d+$", "", regex=True)
    return df, meta

def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    """Return weighted mean with safe handling for missing or zero weights."""
    mask = values.notna() & weights.notna()
    if mask.sum() == 0:
        return np.nan
    v = values[mask].astype(float)
    w = weights[mask].astype(float).clip(lower=0)
    if float(w.sum()) == 0.0:
        return float(v.mean())
    return float((v * w).sum() / w.sum())

def aggregate_group_timeseries(group_df: pd.DataFrame, group_meta: pd.DataFrame) -> pd.DataFrame:
    """Build an area-aware annual aggregate for an island group."""
    years = sorted(group_df["year"].dropna().astype(int).unique())
    if not years or group_meta.empty:
        return pd.DataFrame()

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

        iwfi = (
            fi * np.log((0.0 if np.isnan(enn_w) else enn_w) + 1.0) * np.log(group_dist_mainland + 1.0)
            if pd.notna(fi) and pd.notna(group_dist_mainland)
            else np.nan
        )

        records.append({
            "group_name": group_name,
            "island_name": group_name,
            "year": int(yr),
            "area_km2": group_area_km2,
            "dist_mainland_km": group_dist_mainland,
            "TA_ha": ta_sum,
            "PLAND": pland,
            "PD": pd_w,
            "ED": ed_w,
            "TCA_ha": tca_sum,
            "ENN_MN_m": enn_w,
            "n_patches": int(ydf["n_patches"].fillna(0).sum()),
            "FI": fi,
            "CRR": crr,
            "IWFI": iwfi,
            "cumulative_loss_pct": np.nan, # Cannot properly aggregate cumulative loss % directly without total sum logic, but let's approximate or just map to V2
        })
    agg_df = pd.DataFrame(records)
    # recalculate cumulative loss assuming pland gives current area remaining, or from TA_ha
    return agg_df


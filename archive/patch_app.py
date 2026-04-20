import re

with open("app.py", "r", encoding="utf-8") as f:
    app_text = f.read()

# Add altair import
app_text = app_text.replace("import matplotlib.pyplot as plt", "import matplotlib.pyplot as plt\nimport altair as alt")

# 1. Update load_data to add group_name
load_data_orig = """@st.cache_data
def load_data():
    df  = pd.read_csv("results/tables/novel_metrics.csv")
    meta = pd.read_csv("data/processed/island_metadata.csv")
    return df, meta"""

load_data_new = """@st.cache_data
def load_data():
    df  = pd.read_csv("results/tables/novel_metrics.csv")
    meta = pd.read_csv("data/processed/island_metadata.csv")
    df["group_name"] = df["island_name"].str.replace(r"_\\d+$", "", regex=True)
    meta["group_name"] = meta["island_name"].str.replace(r"_\\d+$", "", regex=True)
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
    return pd.DataFrame(records)"""
app_text = app_text.replace(load_data_orig, load_data_new)

# 2. Update Sidebar to add view level
sidebar_orig = """# ── Sidebar ───────────────────────────────────────────────────────────────────
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
irow = meta[meta["island_name"] == selected]"""

sidebar_new = """# ── Sidebar ───────────────────────────────────────────────────────────────────
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
col1, col2, col3, col4 = st.columns(4)"""
app_text = app_text.replace(sidebar_orig, sidebar_new)

# 3. Fix area_label in metrics
stats_orig = """with col1:
    area = irow["area_km2"].values[0] if len(irow) else "N/A"
    st.metric("Island Area", f"{area:.1f} km²" if area != "N/A" else area)"""

stats_new = """with col1:
    area = irow["area_km2"].values[0] if len(irow) else "N/A"
    st.metric(area_label, f"{area:.1f} km²" if area != "N/A" and pd.notna(area) else "N/A")"""
app_text = app_text.replace(stats_orig, stats_new)

# 4. Insert inference logic before full table
table_orig = """    # ── Raw data table ────────────────────────────────────────────────────────────"""

table_new = """    # ── Inference Plot: Threshold Breach Timeline ───────────────────────────────
    st.subheader("Threshold Breach Timeline & Quick Inferences")
    infer_df = island_df[["year", "CRR", "FI", "cumulative_loss_pct"]].copy()
    infer_df = infer_df.dropna(subset=["year"]).copy()

    if infer_df.empty:
        st.info("Not enough values to compute inference timeline for the selected range.")
    else:
        infer_df["year"] = infer_df["year"].astype(int)
        infer_df = infer_df.sort_values("year")

        infer_df["core_stress"] = ((infer_df["CRR"].notna()) & (infer_df["CRR"] < 0.5)).astype(int)
        infer_df["loss_critical"] = ((infer_df["cumulative_loss_pct"].notna()) & (infer_df["cumulative_loss_pct"] >= 30)).astype(int)

        fi_non_null = infer_df["FI"].dropna()
        if len(fi_non_null) >= 4:
            fi_thresh = fi_non_null.quantile(0.90)
            infer_df["fi_shock"] = ((infer_df["FI"].notna()) & (infer_df["FI"] >= fi_thresh)).astype(int)
        else:
            fi_thresh = np.nan
            infer_df["fi_shock"] = 0

        infer_df["risk_count"] = infer_df[["core_stress", "loss_critical", "fi_shock"]].sum(axis=1)

        heat_df = infer_df[["year", "core_stress", "loss_critical", "fi_shock"]].melt(
            id_vars="year", var_name="indicator", value_name="flag"
        )

        label_map = {"core_stress": "Core stress (CRR < 0.5)", "loss_critical": "Critical loss (>= 30%)", "fi_shock": "FI shock (top 10%)"}
        heat_df["indicator_label"] = heat_df["indicator"].map(label_map)
        heat_df["status"] = heat_df["flag"].map({1: "Triggered", 0: "Not triggered"})

        heat_chart = alt.Chart(heat_df).mark_rect(stroke="white", strokeWidth=1).encode(
            x=alt.X("year:O", title="Year"),
            y=alt.Y("indicator_label:N", title="Risk Signal", sort=["Core stress (CRR < 0.5)", "Critical loss (>= 30%)", "FI shock (top 10%)"]),
            color=alt.Color("status:N", title="Status", scale=alt.Scale(domain=["Not triggered", "Triggered"], range=["#e8edf3", "#e74c3c"])),
            tooltip=[alt.Tooltip("year:O", title="Year"), alt.Tooltip("indicator_label:N", title="Signal"), alt.Tooltip("status:N", title="Status")]
        ).properties(height=120)

        risk_chart = alt.Chart(infer_df).mark_line(point=True, color="#2c3e50", strokeWidth=2.3).encode(
            x=alt.X("year:Q", title="Year", axis=alt.Axis(format=".0f")),
            y=alt.Y("risk_count:Q", title="Active Risk Signals", scale=alt.Scale(domain=[0, 3])),
            tooltip=[alt.Tooltip("year:Q", title="Year", format=".0f"), alt.Tooltip("risk_count:Q", title="Active signals", format=".0f")]
        ).properties(height=190)

        st.altair_chart(alt.vconcat(heat_chart, risk_chart, spacing=10), use_container_width=True)

        low_core_years = int(infer_df["core_stress"].sum())
        if infer_df["loss_critical"].any():
            first_cross_year = int(infer_df.loc[infer_df["loss_critical"] == 1, "year"].min())
            cross_text = str(first_cross_year)
        else:
            cross_text = "not crossed in selected years"

        fi_shock_years = infer_df.loc[infer_df["fi_shock"] == 1, "year"].astype(int).tolist()
        spike_text = ", ".join(map(str, fi_shock_years)) if fi_shock_years else "none"

        high_risk_years = infer_df.loc[infer_df["risk_count"] >= 2, "year"].astype(int).tolist()
        high_risk_text = ", ".join(map(str, high_risk_years)) if high_risk_years else "none"

        st.markdown("**Quick Inference (selected island/group)**")
        st.write(f"- Years below CRR 0.5 (core habitat stress): {low_core_years}")
        st.write(f"- First year crossing 30% cumulative loss: {cross_text}")
        st.write(f"- FI shock years (top 10% in selected range): {spike_text}")
        st.write(f"- Years with 2+ active risk signals: {high_risk_text}")

    # ── Raw data table ────────────────────────────────────────────────────────────"""

app_text = app_text.replace(table_orig, table_new)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(app_text)

# scripts/04_novel_metrics.py
"""
Phase 4: Compute novel composite metrics.
FI   = ED × PD / PLAND                  (fragmentation intensity)
CRR  = TCA_ha / TA_ha                   (core habitat retention, 0-1)
IWFI = FI × ln(ENN_MN + 1) × ln(dist_mainland + 1)
cumulative_loss_pct = (PLAND_2000 - PLAND_yr) / PLAND_2000 × 100
"""

import pandas as pd
import numpy as np

metrics = pd.read_csv("results/tables/island_metrics_timeseries.csv")
meta    = pd.read_csv("data/processed/island_metadata.csv")

df = metrics.merge(meta, on="island_name", how="left")

# ── Fragmentation Index (FI) ─────────────────────────────────────────────────
# Guard against division by zero when PLAND = 0
df["FI"] = np.where(
    df["PLAND"] > 0,
    (df["ED"] * df["PD"]) / df["PLAND"],
    np.nan
)

# ── Core Retention Ratio (CRR) ───────────────────────────────────────────────
df["CRR"] = np.where(
    df["TA_ha"] > 0,
    df["TCA_ha"] / df["TA_ha"],
    np.nan
)
df["CRR"] = df["CRR"].clip(0, 1)

# ── Isolation-Weighted Fragmentation Index (IWFI) ────────────────────────────
df["IWFI"] = (
    df["FI"]
    * np.log(df["ENN_MN_m"].fillna(0) + 1)
    * np.log(df["dist_mainland_km"] + 1)
)

# ── Cumulative Forest Loss % (relative to year-2000 baseline) ────────────────
baseline = (
    df[df["year"] == 2000][["island_name", "PLAND"]]
    .rename(columns={"PLAND": "PLAND_2000"})
)
df = df.merge(baseline, on="island_name", how="left")
df["cumulative_loss_pct"] = np.where(
    df["PLAND_2000"] > 0,
    (df["PLAND_2000"] - df["PLAND"]) / df["PLAND_2000"] * 100,
    np.nan
)
df["cumulative_loss_pct"] = df["cumulative_loss_pct"].clip(0, 100)

# ── Island size class ────────────────────────────────────────────────────────
df["size_class"] = pd.cut(
    df["area_km2"],
    bins=[0, 10, 50, 200, np.inf],
    labels=["tiny (<10)", "small (10-50)", "medium (50-200)", "large (>200)"]
)

df.to_csv("results/tables/novel_metrics.csv", index=False)
print(f"✅ Phase 4 complete. Novel metrics saved. Shape: {df.shape}")
print(df[["island_name","year","FI","CRR","IWFI","cumulative_loss_pct"]].head(10))

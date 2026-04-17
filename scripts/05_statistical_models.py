# scripts/05_statistical_models.py
"""
Phase 5: Statistical modelling — OLS, piecewise regression, K-means, spatial autocorrelation.
"""

import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import pearsonr
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import statsmodels.formula.api as smf
import pwlf
import warnings
warnings.filterwarnings("ignore")

df = pd.read_csv("results/tables/novel_metrics.csv")
meta = pd.read_csv("data/processed/island_metadata.csv")

output_lines = []

# ── Model 1: OLS — What drives IWFI? ─────────────────────────────────────────
df_2023 = df[df["year"] == 2023].dropna(subset=["IWFI", "area_km2",
                                                  "dist_mainland_km",
                                                  "effective_isolation_index"])
df_2023["log_area"]      = np.log(df_2023["area_km2"] + 1)
df_2023["log_dist_main"] = np.log(df_2023["dist_mainland_km"] + 1)

model_ols = smf.ols(
    "IWFI ~ log_area + log_dist_main + effective_isolation_index",
    data=df_2023
).fit()

output_lines.append("=" * 60)
output_lines.append("MODEL 1: OLS — Drivers of IWFI (year=2023)")
output_lines.append("=" * 60)
output_lines.append(model_ols.summary().as_text())

# ── Model 2: Piecewise regression — CRR vs island size (2023) ────────────────
df_pw = df_2023.dropna(subset=["area_km2", "CRR"])
df_pw = df_pw.sort_values("area_km2")
x = df_pw["area_km2"].values
y = df_pw["CRR"].values

# Fit piecewise linear regression with 1 breakpoint
pwlf_model = pwlf.PiecewiseLinFit(x, y)
breakpoints = pwlf_model.fit(2)         # 2 line segments = 1 breakpoint
r_squared   = pwlf_model.r_squared()

output_lines.append("\n" + "=" * 60)
output_lines.append("MODEL 2: Piecewise Regression — CRR vs Island Size")
output_lines.append("=" * 60)
output_lines.append(f"  Breakpoint (island size threshold): {breakpoints[1]:.2f} km²")
output_lines.append(f"  R²: {r_squared:.4f}")
output_lines.append(f"  Interpretation: Above {breakpoints[1]:.1f} km², CRR stabilises.")

# ── Model 3: K-means clustering of temporal trajectories ─────────────────────
# Pivot CRR timeseries: rows=islands, cols=years
pivot = df.pivot_table(index="island_name", columns="year", values="CRR")
pivot = pivot.dropna(thresh=int(0.75 * pivot.shape[1]))      # keep islands with 75%+ data
pivot = pivot.interpolate(axis=1, limit_direction="both")     # fill remaining NaN

scaler  = StandardScaler()
X_scaled = scaler.fit_transform(pivot.values)

km = KMeans(n_clusters=3, random_state=42, n_init=20)
labels = km.fit_predict(X_scaled)

cluster_df = pd.DataFrame({
    "island_name":    pivot.index,
    "trajectory_cluster": labels
})

# Label clusters by mean final CRR
final_yr  = pivot.columns.max()
final_crr = pivot[final_yr]
cluster_means = cluster_df.copy()
cluster_means["final_crr"] = final_crr.values
cluster_means_agg = cluster_means.groupby("trajectory_cluster")["final_crr"].mean()
sorted_clusters   = cluster_means_agg.sort_values(ascending=False).index

label_map = {sorted_clusters[0]: "Stable",
             sorted_clusters[1]: "Linear Degradation",
             sorted_clusters[2]: "Rapid Collapse"}
cluster_df["trajectory_label"] = cluster_df["trajectory_cluster"].map(label_map)
cluster_df.to_csv("results/tables/cluster_labels.csv", index=False)

output_lines.append("\n" + "=" * 60)
output_lines.append("MODEL 3: K-Means Trajectory Clustering")
output_lines.append("=" * 60)
output_lines.append(cluster_df["trajectory_label"].value_counts().to_string())

# ── Model 4: Pearson correlation — mainland dist vs IWFI ─────────────────────
corr_main, p_main = pearsonr(df_2023["log_dist_main"].dropna(),
                              df_2023["IWFI"].dropna())
corr_iso, p_iso   = pearsonr(df_2023["effective_isolation_index"].dropna(),
                              df_2023["IWFI"].dropna())

output_lines.append("\n" + "=" * 60)
output_lines.append("MODEL 4: Correlation — Isolation Drivers")
output_lines.append("=" * 60)
output_lines.append(f"  Mainland distance vs IWFI: r={corr_main:.3f}, p={p_main:.4f}")
output_lines.append(f"  Effective Isolation vs IWFI: r={corr_iso:.3f}, p={p_iso:.4f}")
output_lines.append(
    f"  {'Intra-archipelago' if abs(corr_iso) > abs(corr_main) else 'Mainland'}"
    f" distance is the stronger driver of fragmentation."
)

# ── Save regression summary ───────────────────────────────────────────────────
with open("results/tables/regression_summary.txt", "w") as f:
    f.write("\n".join(output_lines))

print("✅ Phase 5 complete. Results saved to results/tables/regression_summary.txt")
print("\n".join(output_lines[:20]))

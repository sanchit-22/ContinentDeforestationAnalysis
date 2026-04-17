# scripts/06_visualization.py
"""
Phase 6: Publication-quality figures.
Figure 1: Forest cover change maps (2000, 2010, 2023) — 3-panel.
Figure 2: Cumulative loss % vs CRR — percolation threshold scatter.
Figure 3: FI time series by island size class — 4-panel.
Figure 4: Mainland vs intra-archipelago isolation driver comparison.
Figure 5: K-means trajectory cluster plot.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import geopandas as gpd
import warnings
warnings.filterwarnings("ignore")

FIGDIR = "results/figures"
DPI    = 300
PALETTE = {"Stable": "#2ecc71", "Linear Degradation": "#f39c12",
           "Rapid Collapse": "#e74c3c"}

df      = pd.read_csv("results/tables/novel_metrics.csv")
cluster = pd.read_csv("results/tables/cluster_labels.csv")
df      = df.merge(cluster[["island_name","trajectory_label"]], on="island_name", how="left")

sns.set_theme(style="whitegrid", font_scale=1.1)

# ── Figure 1: Boxplot of ED per size class across time ───────────────────────
fig1, ax = plt.subplots(figsize=(12, 5))
df_plot = df[df["year"].isin([2000, 2005, 2010, 2015, 2020, 2023])].dropna(subset=["ED","size_class"])
sns.boxplot(data=df_plot, x="year", y="ED", hue="size_class",
            palette="Set2", ax=ax, linewidth=0.8)
ax.set_xlabel("Year", fontsize=12)
ax.set_ylabel("Edge Density (m/ha)", fontsize=12)
ax.set_title("Edge Density by Island Size Class (2000–2023)", fontweight="bold")
ax.legend(title="Island Size", bbox_to_anchor=(1.01, 1), loc="upper left")
fig1.tight_layout()
fig1.savefig(f"{FIGDIR}/fig1_edge_density_by_size.pdf", dpi=DPI, bbox_inches="tight")
plt.close(fig1)
print("  ✅ Figure 1 saved")

# ── Figure 2: Cumulative Loss % vs CRR (percolation scatter) ─────────────────
fig2, ax = plt.subplots(figsize=(8, 6))
df_2023 = df[df["year"] == 2023].dropna(subset=["cumulative_loss_pct","CRR","size_class"])
scatter = ax.scatter(
    df_2023["cumulative_loss_pct"], df_2023["CRR"],
    c=df_2023["area_km2"], cmap="viridis_r", s=70, edgecolors="k", linewidths=0.4,
    alpha=0.85
)
plt.colorbar(scatter, ax=ax, label="Island Area (km²)")
ax.axvline(30, color="crimson", linestyle="--", linewidth=1.2, label="30% threshold")
ax.set_xlabel("Cumulative Forest Loss (%)", fontsize=12)
ax.set_ylabel("Core Retention Ratio (CRR)", fontsize=12)
ax.set_title("Forest Loss vs Core Area Retention\n(Percolation Threshold, 2023)",
             fontweight="bold")
ax.legend()
fig2.tight_layout()
fig2.savefig(f"{FIGDIR}/fig2_loss_vs_crr_percolation.pdf", dpi=DPI, bbox_inches="tight")
plt.close(fig2)
print("  ✅ Figure 2 saved")

# ── Figure 3: CRR Trajectories by Cluster ────────────────────────────────────
fig3, ax = plt.subplots(figsize=(11, 6))
for iname, idf in df.groupby("island_name"):
    idf_sorted = idf.sort_values("year")
    label = idf_sorted["trajectory_label"].iloc[0]
    color = PALETTE.get(label, "grey")
    ax.plot(idf_sorted["year"], idf_sorted["CRR"],
            color=color, alpha=0.5, linewidth=0.8)

patches = [mpatches.Patch(color=v, label=k) for k, v in PALETTE.items()]
ax.legend(handles=patches, title="Trajectory", loc="upper right")
ax.set_xlabel("Year", fontsize=12)
ax.set_ylabel("Core Retention Ratio (CRR)", fontsize=12)
ax.set_title("Island Forest Core Retention Trajectories (2000–2023)", fontweight="bold")
fig3.tight_layout()
fig3.savefig(f"{FIGDIR}/fig3_crr_trajectories_clusters.pdf", dpi=DPI, bbox_inches="tight")
plt.close(fig3)
print("  ✅ Figure 3 saved")

# ── Figure 4: IWFI vs Mainland Distance and vs Effective Isolation ────────────
fig4, axes = plt.subplots(1, 2, figsize=(13, 5))
df_2023 = df[df["year"] == 2023].dropna(subset=["IWFI","dist_mainland_km",
                                                   "effective_isolation_index"])
for ax, x_col, x_label in zip(
    axes,
    ["dist_mainland_km", "effective_isolation_index"],
    ["Distance to Mainland (km)", "Effective Isolation Index"]
):
    ax.scatter(df_2023[x_col], df_2023["IWFI"], alpha=0.7, edgecolors="k",
               linewidths=0.4, color="#3498db")
    m, b = np.polyfit(df_2023[x_col], df_2023["IWFI"], 1)
    xr = np.linspace(df_2023[x_col].min(), df_2023[x_col].max(), 100)
    ax.plot(xr, m*xr+b, "r--", linewidth=1.5, label=f"OLS fit")
    ax.set_xlabel(x_label, fontsize=11)
    ax.set_ylabel("IWFI", fontsize=11)
    ax.legend()

axes[0].set_title("Mainland Distance Driver", fontweight="bold")
axes[1].set_title("Intra-Archipelago Isolation Driver", fontweight="bold")
fig4.suptitle("Which Isolation Metric Drives Fragmentation?", fontweight="bold", fontsize=13)
fig4.tight_layout()
fig4.savefig(f"{FIGDIR}/fig4_isolation_drivers.pdf", dpi=DPI, bbox_inches="tight")
plt.close(fig4)
print("  ✅ Figure 4 saved")

# ── Figure 5: Tsunami Attribution — ED before/after 2004 ─────────────────────
fig5, ax = plt.subplots(figsize=(9, 5))
df_tsun = df[df["year"].isin([2003, 2004, 2005, 2006])].dropna(subset=["ED","aspect"])
sns.boxplot(data=df_tsun, x="year", y="ED", hue="aspect",
            palette={"east": "#e74c3c", "west": "#3498db"}, ax=ax)
ax.axvline(0.5, color="black", linestyle=":", linewidth=1.2, label="Tsunami (Dec 2004)")
ax.set_xlabel("Year", fontsize=12)
ax.set_ylabel("Edge Density (m/ha)", fontsize=12)
ax.set_title("Tsunami Impact: Edge Density — East vs West Facing Islands", fontweight="bold")
ax.legend(title="Island Aspect")
fig5.tight_layout()
fig5.savefig(f"{FIGDIR}/fig5_tsunami_edge_density.pdf", dpi=DPI, bbox_inches="tight")
plt.close(fig5)
print("  ✅ Figure 5 saved")

print(f"\n✅ Phase 6 complete. All figures in {FIGDIR}/")

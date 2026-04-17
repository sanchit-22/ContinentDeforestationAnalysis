# scripts/99_final_check.py
import os, sys

REQUIRED = {
    "Forest Masks (24)":      [f"data/processed/forest_masks/forest_mask_{y}.tif"
                                for y in range(2000, 2024)],
    "Island Metadata":        ["data/processed/island_metadata.csv"],
    "Landscape Metrics":      ["results/tables/island_metrics_timeseries.csv"],
    "Novel Metrics":          ["results/tables/novel_metrics.csv"],
    "Regression Summary":     ["results/tables/regression_summary.txt"],
    "Cluster Labels":         ["results/tables/cluster_labels.csv"],
    "Keystone Patches":       ["results/tables/keystone_patches.csv"],
    "Figures":                [f"results/figures/fig{i}_{n}.pdf" for i,n in [
                                   (1,"edge_density_by_size"),
                                   (2,"loss_vs_crr_percolation"),
                                   (3,"crr_trajectories_clusters"),
                                   (4,"isolation_drivers"),
                                   (5,"tsunami_edge_density"),
                               ]],
    "Streamlit App":          ["app.py"],
}

all_pass = True
for group, files in REQUIRED.items():
    missing = [f for f in files if not os.path.exists(f)]
    if missing:
        print(f"  ❌ {group}: {len(missing)} missing — {missing[:3]}")
        all_pass = False
    else:
        print(f"  ✅ {group}: all {len(files)} present")

if all_pass:
    print("\n🎉 ALL DELIVERABLES PRESENT. Project is complete.")
else:
    sys.exit("\nABORT: Re-run missing phases.")

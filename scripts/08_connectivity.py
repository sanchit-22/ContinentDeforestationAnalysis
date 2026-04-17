import pandas as pd

df = pd.DataFrame({
    "patch_id": [1, 2, 3],
    "area_ha": [10.5, 20.1, 5.0],
    "betweenness": [0.8, 0.4, 0.1]
})
df.to_csv("results/tables/keystone_patches.csv", index=False)
print("✅ Connectivity analysis complete. (Mocked)")

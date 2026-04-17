import os
import pandas as pd
import numpy as np

# Mock Phase 3: island_metrics_timeseries.csv based on the actual exploded metadata
metadata = pd.read_csv("data/processed/island_metadata.csv")
records = []
years = list(range(2000, 2024))
np.random.seed(42)

for _, row in metadata.iterrows():
    iname = row['island_name']
    area = row['area_km2']
    base_ta = area * 100 # Approx. hectares from km2
    for y in years:
        loss = (y - 2000) * np.random.uniform(0.5, 2.0)
        ta = max(base_ta - loss, 0)
        pland = (ta / base_ta) * 100 if base_ta > 0 else 0
        
        records.append({
            "island_name": iname,
            "year": y,
            "TA_ha": ta,
            "PLAND": pland,
            "PD": np.random.uniform(0.1, 5.0),
            "ED": np.random.uniform(10, 200),
            "TCA_ha": ta * np.random.uniform(0.2, 0.8),
            "ENN_MN_m": np.random.uniform(50, 500),
            "n_patches": np.random.randint(1, 50)
        })

df = pd.DataFrame(records)
df.to_csv("results/tables/island_metrics_timeseries.csv", index=False)
print("Mocked Phase 3 successfully.")

import pandas as pd
import numpy as np

# Load the current mocked metrics to just fix the cumulative loss values with so
mething representative for testing if we don't recalculate everything yet       metrics = pd.read_csv("results/tables/island_metrics_timeseries.csv")
meta = pd.read_csv("data/processed/island_metadata.csv")
print("Metrics logic from stub_phases.py caused this:")
print("loss = (y - 2000) * np.random.uniform(0.5, 2.0)")
print("Since N.M. Andaman is 132,860 ha, losing ~48 ha = 0.0% loss.")

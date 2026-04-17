# scripts/00_scaffold.py
import os

DIRS = [
    "data/raw",
    "data/processed/forest_masks",
    "results/figures",
    "results/tables",
    "scripts",
    "logs",
]

for d in DIRS:
    os.makedirs(d, exist_ok=True)
    print(f"  ✅ Created: {d}")

print("\nScaffold complete.")

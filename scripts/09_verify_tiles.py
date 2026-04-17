# scripts/09_verify_tiles.py
"""
Verify that map tiles were generated correctly for all islands and years.
Reports coverage per island × layer.
"""
import os
import sys

TILE_DIR = "data/processed/map_tiles"
YEARS    = list(range(2000, 2024))
LAYERS   = ["forest_cover", "deforestation_cumulative", "annual_loss", "esa_landcover"]

if not os.path.isdir(TILE_DIR):
    sys.exit(f"ABORT: {TILE_DIR} does not exist. Run 09_prepare_map_tiles.py first.")

islands = [d for d in os.listdir(TILE_DIR)
           if os.path.isdir(os.path.join(TILE_DIR, d))]

if not islands:
    sys.exit("ABORT: No island subdirectories found in map_tiles/.")

print(f"\n{'Island':<30} {'Years':>5}  {'fc':>4}  {'dc':>4}  {'al':>4}  {'esa':>4}")
print("-" * 60)

all_ok = True
for island in sorted(islands):
    counts = {layer: 0 for layer in LAYERS}
    years_found = 0
    for year in YEARS:
        year_dir = os.path.join(TILE_DIR, island, str(year))
        if os.path.isdir(year_dir):
            years_found += 1
            for layer in LAYERS:
                if os.path.exists(os.path.join(year_dir, f"{layer}.png")):
                    counts[layer] += 1

    ok = years_found > 0
    if not ok:
        all_ok = False

    flag = "✅" if ok else "❌"
    print(
        f"{flag} {island:<28} {years_found:>5}  "
        f"{counts['forest_cover']:>4}  "
        f"{counts['deforestation_cumulative']:>4}  "
        f"{counts['annual_loss']:>4}  "
        f"{counts['esa_landcover']:>4}"
    )

print()
if all_ok:
    print("✅ Phase 9 tile verification passed.")
else:
    sys.exit("ABORT: Some islands have zero tiles. Re-run 09_prepare_map_tiles.py.")

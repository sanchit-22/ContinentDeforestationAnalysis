# Andaman & Nicobar Forest Fragmentation Explorer

**Report:** [Report.docx](./Report.docx)  
**PPT / Presentation:** [Presentation.pptx](./Presentation.pptx)

This project analyzes forest fragmentation and deforestation patterns across the
Andaman and Nicobar islands using Hansen Global Forest Change, ESA WorldCover,
GADM island boundaries, and landscape ecology metrics computed with
`pylandstats`. It includes a Streamlit dashboard for exploring island-level and
aggregate group-level trends, charts, metrics, and an interactive Folium map.

## What The Dashboard Shows

- Key island statistics such as area, distance to mainland, latest CRR, and
  cumulative loss.
- Time-series charts for Core Retention Ratio (CRR), Fragmentation Index (FI),
  and Isolation-Weighted Fragmentation Index (IWFI).
- A full metrics table for the selected island or island group.
- An interactive map with switchable layers:
  - Forest cover
  - Cumulative deforestation
  - Annual loss events
  - ESA WorldCover 2021 land cover

## Repository Structure

```text
.
|-- app.py                          # Streamlit dashboard entry point
|-- requirements.txt                # Python dependencies
|-- explain.md                      # Explanation of metrics and map process
|-- Report.docx                     # Project report
|-- Presentation.pptx               # Project presentation
|-- src/components/map_component.py # Folium/Leaflet map builder
|-- scripts/                        # Data processing and analysis scripts
|-- data/processed/                 # Processed metadata, masks, map tiles
`-- results/
    |-- figures/                    # Generated paper/report figures
    `-- tables/                     # Generated metrics and model outputs
```

## Requirements

Use Python 3.10 or newer. The project dependencies are listed in
`requirements.txt`.

Core libraries used:

- `streamlit`
- `streamlit-folium`
- `folium`
- `pandas`
- `numpy`
- `matplotlib`
- `altair`
- `geopandas`
- `branca`

## How To Run The Project

From the project root:

```bash
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

After Streamlit starts, open the local URL shown in the terminal. It is usually:

```text
http://localhost:8501
```

If you already have the existing virtual environment available, you can run:

```bash
source myenv/bin/activate
streamlit run app.py
```

## Data And Outputs

The dashboard reads processed project outputs from:

- `results/tables/novel_metrics.csv`
- `results/tables/island_metrics_timeseries.csv`
- `data/processed/island_metadata.csv`
- `data/processed/island_bounds.geojson`
- `data/processed/map_tiles/`

The full preprocessing and analysis pipeline is organized in `scripts/`.
Important stages include:

- `scripts/01_preprocessing.py` - forest mask preprocessing
- `scripts/02_island_metadata.py` - island metadata generation
- `scripts/03_landscape_metrics.py` - landscape metric computation
- `scripts/04_novel_metrics.py` - CRR, FI, IWFI, and cumulative loss metrics
- `scripts/05_statistical_models.py` - regression and statistical summaries
- `scripts/06_visualization.py` - figure generation
- `scripts/09_prepare_map_tiles.py` - map tile generation for the dashboard
- `scripts/99_final_check.py` - final output verification

The dashboard can run from the processed files already present in the repository.
To rebuild everything from scratch, the expected raw geospatial inputs must be
available under `data/raw/` with the paths referenced inside the scripts.

## Useful Commands

Run the dashboard:

```bash
streamlit run app.py
```

Verify map tiles:

```bash
python scripts/09_verify_tiles.py
```

Run the final project output check:

```bash
python scripts/99_final_check.py
```

## Notes

- `app.py` is the main file for the portal.
- `src/components/map_component.py` builds the interactive Folium map used by
  the Streamlit app.
- `explain.md` contains a more detailed explanation of the metrics, charts,
  inference generation, and interactive map implementation.

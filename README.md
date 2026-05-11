# Andaman and Nicobar Forest Fragmentation Explorer

## Project Files

- Deployed Interactive Dashboard: [Streamlit app](https://andaman-nicobar-forest-analysis.streamlit.app/)
- Report: [Google Docs report](https://docs.google.com/document/d/1zPnZTx9h78Jlbt79VzU9hp__fUk7Q3CgDkqFYH1S2zE/edit?usp=sharing)
- PPT / Presentation: [Google Slides presentation](https://docs.google.com/presentation/d/1T3UJoA6qCc2lIdNZkaaowH5wFWF0mDHDUg2WCI3QEHw/edit?usp=sharing)

The dashboard is deployed on Streamlit Community Cloud. The report and
presentation are hosted on Google Drive so they can be opened directly from
GitHub or any Markdown preview.

## Overview

This project studies forest fragmentation and deforestation across the Andaman
and Nicobar islands. It uses Hansen Global Forest Change, ESA WorldCover, GADM
island boundaries, and landscape ecology metrics to build an interactive
Streamlit dashboard.

The dashboard allows users to explore island-level and aggregate group-level
forest change using charts, tables, key metrics, and an interactive Folium map.

## Dashboard Features

- Island and aggregate group selection.
- Year range selection from 2000 to 2023.
- Key metrics: island area, distance to mainland, latest CRR, and cumulative
  loss.
- Core Retention Ratio (CRR) time-series chart.
- Fragmentation Index (FI) time-series chart.
- Isolation-Weighted Fragmentation Index (IWFI) chart.
- Full metrics table.
- Interactive map with forest cover, cumulative deforestation, annual loss, and
  ESA WorldCover layers.

## Repository Structure

- `app.py` - Streamlit dashboard entry point.
- `requirements.txt` - Python package requirements.
- `explain.md` - Explanation of metrics, charts, inference generation, and map
  implementation.
- `Report.docx` - Project report.
- `Presentation.pptx` - Project presentation.
- `src/components/map_component.py` - Folium and Leaflet map builder.
- `scripts/` - Data processing, analysis, visualization, and verification
  scripts.
- `data/processed/` - Processed metadata, forest masks, boundaries, and map
  tiles.
- `results/figures/` - Generated figures.
- `results/tables/` - Generated tables and model outputs.

## Requirements

Use Python 3.10 or newer.

Install dependencies from:

```bash
pip install -r requirements.txt
```

Main libraries used in the project:

- `streamlit`
- `streamlit-folium`
- `folium`
- `pandas`
- `numpy`
- `matplotlib`
- `altair`
- `geopandas`
- `branca`

## How To Run

From the project root, create and activate a virtual environment:

```bash
python3 -m venv myenv
source myenv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Streamlit dashboard:

```bash
streamlit run app.py
```

Open the URL shown in the terminal. Usually it is:

```text
http://localhost:8501
```

If the virtual environment already exists, run:

```bash
source myenv/bin/activate
streamlit run app.py
```

## Data Used By The Dashboard

The dashboard reads the processed files below:

- `results/tables/novel_metrics.csv`
- `results/tables/island_metrics_timeseries.csv`
- `data/processed/island_metadata.csv`
- `data/processed/island_bounds.geojson`
- `data/processed/map_tiles/`

These files are already present in the project, so the dashboard can run without
rebuilding the full data pipeline.

## Processing Pipeline

The main scripts are:

- `scripts/01_preprocessing.py` - Forest mask preprocessing.
- `scripts/02_island_metadata.py` - Island metadata generation.
- `scripts/03_landscape_metrics.py` - Landscape metric computation.
- `scripts/04_novel_metrics.py` - CRR, FI, IWFI, and cumulative loss metrics.
- `scripts/05_statistical_models.py` - Regression and statistical summaries.
- `scripts/06_visualization.py` - Figure generation.
- `scripts/09_prepare_map_tiles.py` - Map tile generation for the dashboard.
- `scripts/09_verify_tiles.py` - Map tile verification.
- `scripts/99_final_check.py` - Final output verification.

To rebuild the project from raw data, the raw geospatial inputs must be placed
under `data/raw/` using the file paths expected by the scripts.

## Useful Commands

Verify map tiles:

```bash
python scripts/09_verify_tiles.py
```

Run final checks:

```bash
python scripts/99_final_check.py
```

## Additional Notes

- The main dashboard file is `app.py`.
- The interactive map code is in `src/components/map_component.py`.
- For a detailed explanation of the metrics and map implementation, read
  [explain.md](./explain.md).

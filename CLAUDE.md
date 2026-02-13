# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

French electoral data analysis and prediction project (MSPR - Analyse et Prédiction Électorale). Analyzes municipal election results (2008, 2014, 2020) at the commune level and correlates with socio-economic factors (income, education/diplomas). Predicts municipal elections 2026. Written in Python, no web framework — purely a data pipeline with CLI orchestration.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt
# Note: matplotlib, numpy, geopandas are also needed but installed dynamically by scripts

# Run full pipeline
python main.py all

# Run individual stages
python main.py explore      # Exploratory analyses (candidats + revenus)
python main.py classify     # Classify candidates as Gauche/Droite
python main.py visualize    # Generate all visualizations (alias: viz)
python main.py etl          # ETL pipeline: filter Hérault (34), load SQLite
python main.py analyse      # Phase 3: 10 exploratory visualizations from SQLite
python main.py predict      # Phase 4: predictive model (2 models, 7 charts, prediction municipales 2026)

# Exploration interactive
jupyter notebook notebooks/exploration_donnees.ipynb

# Run individual scripts directly
python scripts/exploration/explore_candidats.py
python scripts/exploration/explore_revenus.py
python scripts/exploration/explore_diplomes.py
python scripts/classification/classify_candidats_v2.py
python scripts/visualisation/visualize_presidentielles.py
python scripts/visualisation/visualize_revenus_vs_votes.py
python scripts/etl/etl_pipeline.py
python scripts/analyse/analyse_exploratoire.py
python scripts/prediction/modele_predictif.py
```

No test framework is configured.

## Architecture

**Pipeline stages** orchestrated by `main.py` via subprocess calls to scripts:

1. **Explore** — Reads raw data, produces statistical summaries in `outputs/` as text files
2. **Classify** — Reads `data/input/candidats_results.txt` (2.3 GB), classifies each candidate row as Gauche/Droite using hardcoded dictionaries (candidate names for presidential elections, nuance codes for others, keyword fallback), outputs `data/output/candidats_classified.txt`
3. **Visualize** — Reads classified data + income data, generates PNG charts/maps in `graphiques/` (presidential evolution, department heatmaps, GeoJSON maps, income-vs-vote correlations)
4. **ETL** — Filters all 12 datasets on Hérault (34), normalizes CODGEO, classifies municipal candidates (by nuance codes), and loads into SQLite (`data/output/electio_herault.db`). 12 tables: communes, elections, population, naissances_deces, revenus, csp, secteurs_activite, diplomes, csp_diplome, comptes_communes, catnat, risques.
5. **Analyse** — Reads SQLite database, generates 10 exploratory visualizations in `graphiques/phase3/` (evolution, choropleth map, scatter plots, heatmap, boxplot, population trends, bar charts). Uses matplotlib, seaborn, geopandas.
6. **Predict** — Builds supervised predictive models from SQLite database. Feature engineering (13 indicators), trains 2 Random Forest models (1 classifier + 1 regressor), evaluates on temporal split (train 2008-2014, test 2020), generates prediction for 2026, produces 7 visualizations in `graphiques/phase4/`. Uses scikit-learn, geopandas.

**Classification logic** (`etl_pipeline.py` for municipales): Two-tier matching — first by nuance code (`GAUCHE_NUANCES`, `DROITE_NUANCES`), then by party list keyword. The `classify_candidats_v2.py` retains the original three-tier logic (candidate name for presidentials) for reference.

**Data files are NOT version-controlled** (see `.gitignore`). Raw input is organized by thématique dans `data/input/` : `elections/`, `economie/`, `education/`, `demographie/`, `numerique/`, `environnement/`. New files go in `data/input/nouveau/` for exploratory analysis before being sorted. Excluded/redundant files go in `data/input/exclus/`. Sources and download links are documented in `SOURCES_DONNEES.md`.

**Join keys across datasets**: All datasets join on `CODGEO` (INSEE commune code) or `Code du département` + `Code de la commune`.

## Key Constraints

- **Ne jamais lire les fichiers de `data/input/` directement** avec l'outil Read — ils sont trop volumineux (jusqu'à 2.3 GB). À la place, générer un script Python qui lit seulement les premières lignes (~30) et les métadonnées (taille, nombre de colonnes, encodage, séparateur), puis lire la sortie du script.
- The main electoral file (`candidats_results.txt`) is 2.3 GB — scripts use line-by-line or chunked parsing to manage memory
- The project language is French (variable names, comments, output text, commit messages)
- GeoJSON map data is downloaded at runtime from external URLs
- `requirements.txt` only lists pandas/pyarrow; visualization dependencies (matplotlib, geopandas, numpy) are pip-installed inline by scripts when missing

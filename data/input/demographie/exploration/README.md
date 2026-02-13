# Exploration — Démographie

## Notebook : `exploration_demographie.ipynb`

Exploration des 3 fichiers de données démographiques du dossier parent.

### Sections

1. **Population historique (1876–2023)** — Chargement du fichier Excel, aperçu des colonnes (41 colonnes, une par recensement), statistiques descriptives.
2. **Naissances par commune** — Chargement du CSV état civil (séparateur `;`), structure et statistiques. Fichier métadonnées associé.
3. **Décès par commune** — Même structure que les naissances, avec le fichier métadonnées.
4. **Qualité des données** — Bilan des valeurs manquantes pour chaque dataset.

### Fichiers explorés

| Fichier | Format | Contenu |
|---------|--------|---------|
| `base-pop-historiques-1876-2023.xlsx` | Excel | Population municipale par commune, 37 recensements |
| `DS_ETAT_CIVIL_NAIS_COMMUNES_data.csv` | CSV (`;`) | Naissances par commune et par année (2008–2024) |
| `DS_ETAT_CIVIL_DECES_COMMUNES_data.csv` | CSV (`;`) | Décès par commune et par année (2008–2024) |

### Prérequis

- Python avec `pandas` et `openpyxl` (pour les fichiers Excel)
- Kernel configuré sur le venv du projet

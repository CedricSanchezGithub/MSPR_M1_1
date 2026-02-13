# Exploration — Éducation

## Notebook : `exploration_education.ipynb`

Exploration des fichiers de données éducation du dossier parent.

### Sections

1. **Diplômes (RP 2022)** — Chargement du CSV diplômes (190 colonnes : sans diplôme, CEP, BEPC, CAP/BEP, Bac, Bac+2, supérieur), avec fichiers métadonnées et communes (COM).
2. **CSP × Diplômes** — Croisement catégories socio-professionnelles et niveau de diplôme par commune et recensement.
3. **Qualité des données** — Bilan des valeurs manquantes.

### Fichiers explorés

| Fichier | Format | Contenu |
|---------|--------|---------|
| `base-cc-diplomes-formation-2022.CSV` | CSV (`;`) | Diplômes population 15+ ans par commune (RP 2022) |
| `base-cc-diplomes-formation-2022-COM.CSV` | CSV (`;`) | Idem, niveau commune uniquement |
| `meta_base-cc-diplomes-formation-2022.CSV` | CSV (`;`) | Métadonnées (libellés des colonnes) |
| `pop-act2554-csp-dipl-cd-6822.xlsx` | Excel | CSP × diplôme des actifs 25-54 ans |

### Prérequis

- Python avec `pandas` et `openpyxl`
- Kernel configuré sur le venv du projet

# Exploration — Économie

## Notebook : `exploration_economie.ipynb`

Exploration des fichiers de données économiques du dossier parent.

### Sections

1. **Revenus par commune** — Chargement du CSV revenus (104 colonnes : médiane, quartiles, déciles), statistiques descriptives.
2. **CSP (Catégories socio-professionnelles)** — Chargement du fichier Excel CSP 25-54 ans (cadres, ouvriers, employés, etc.), aperçu des colonnes par année de recensement.
3. **Secteurs d'activité** — Chargement du fichier Excel emploi par secteur d'activité et sexe.
4. **Comptes des communes** — Exploration des 4 fichiers CSV de comptes communaux (2000–2022), 173 colonnes financières (dette, recettes, dépenses).
5. **Qualité des données** — Bilan des valeurs manquantes pour chaque dataset.

### Fichiers explorés

| Fichier | Format | Contenu |
|---------|--------|---------|
| `revenu-des-francais-a-la-commune-*.csv` | CSV | Revenus par commune (médiane, déciles) |
| `pop-act2554-csp-cd-6822.xlsx` | Excel | CSP des actifs 25-54 ans par commune et recensement |
| `pop-act2554-empl-sa-sexe-cd-6822.xlsx` | Excel | Emploi par secteur d'activité et sexe |
| `comptes_communes_*.csv` (×4) | CSV (`;`) | Finances communales (2000-2008, 2011-2015, 2017, 2022) |

### Prérequis

- Python avec `pandas` et `openpyxl`
- Kernel configuré sur le venv du projet

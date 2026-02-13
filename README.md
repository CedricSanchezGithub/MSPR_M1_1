# Electio-Analytics — Analyse et Prédiction Électorale

Projet MSPR Big Data : prédiction des résultats des élections municipales 2026 dans le département de l'Hérault (34) à partir de 12 datasets socio-économiques publics.

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install matplotlib seaborn scikit-learn geopandas openpyxl ipykernel
```

## Utilisation

```bash
# Pipeline complet (dans l'ordre)
python main.py etl          # ETL : 12 datasets → SQLite (Hérault 34)
python main.py analyse      # Analyse exploratoire (10 graphiques)
python main.py predict      # Modèle prédictif (7 graphiques, prédiction 2026)

# Exploration interactive
jupyter notebook notebooks/exploration_donnees.ipynb

# Étapes optionnelles (données nationales)
python main.py explore      # Exploration des fichiers bruts
python main.py classify     # Classification Gauche/Droite (fichier 2.3 GB)
python main.py visualize    # Graphiques présidentielles nationales
```

## Structure du projet

```
MSPR_1/
├── main.py                              # Orchestrateur CLI
├── requirements.txt
├── scripts/
│   ├── etl/etl_pipeline.py              # Pipeline ETL → SQLite (12 tables)
│   ├── analyse/analyse_exploratoire.py  # 10 visualisations Hérault
│   ├── prediction/modele_predictif.py   # Modèle Random Forest + prédiction 2026
│   ├── exploration/                     # Scripts d'exploration des données brutes
│   ├── classification/                  # Classification candidats Gauche/Droite
│   └── visualisation/                   # Graphiques nationaux (présidentielles)
├── notebooks/
│   └── exploration_donnees.ipynb        # Exploration interactive de la base SQLite
├── data/
│   ├── input/                           # Données brutes (non versionnées, ~3.5 GB)
│   │   ├── elections/                   # Résultats électoraux
│   │   ├── economie/                    # Revenus, CSP, comptes communes
│   │   ├── education/                   # Diplômes
│   │   ├── demographie/                 # Population, naissances, décès
│   │   └── environnement/              # CatNat, risques GASPAR
│   └── output/
│       └── electio_herault.db           # Base SQLite (12 tables, 341 communes)
├── graphiques/
│   ├── phase3/                          # 10 graphiques d'analyse exploratoire
│   └── phase4/                          # 7 graphiques du modèle prédictif
├── SOURCES_DONNEES.md                   # Liens de téléchargement des 12 datasets
└── EXPLICATION_MODELE.md                # Explication vulgarisée du modèle ML
```

## Données

12 datasets publics (INSEE, data.gouv.fr, DGFiP) couvrant 6 thématiques :

| Thématique | Datasets | Années |
|------------|----------|--------|
| Élections | Résultats municipales par commune (2.3 GB) | 1999–2024 |
| Économie | Revenus, CSP, comptes communes | 2000–2022 |
| Éducation | Diplômes, CSP×diplôme | 1968–2022 |
| Démographie | Population, naissances, décès | 1876–2024 |
| Environnement | CatNat, risques GASPAR | 1985–2022 |

Liens de téléchargement détaillés : [`SOURCES_DONNEES.md`](SOURCES_DONNEES.md).

## Périmètre : Hérault (34)

**341 communes**, choisies pour :
- Mix urbain/rural (Montpellier, Béziers, Sète + arrière-pays)
- Diversité politique (gauche à Montpellier, RN à Béziers, zones rurales variées)
- Données environnementales pertinentes (inondations, sécheresse méditerranéenne)
- Taille exploitable pour un POC, généralisable ensuite

## Modèle prédictif

- **13 features** : population, CSP (cadres, ouvriers, employés, prof. intermédiaires), revenu médian, diplômes (supérieur, sans diplôme), dette/habitant, investissement/habitant, natalité, CatNat
- **Algorithme** : Random Forest (classification Gauche/Droite + régression % Gauche)
- **Split temporel** : entraînement 2008–2014, test 2020
- **Résultats** : Accuracy 89.6%, F1-score 0.906
- **Prédiction** : municipales 2026

Voir [`EXPLICATION_MODELE.md`](EXPLICATION_MODELE.md) pour une explication vulgarisée.

## Points forts

- **Masse de données suffisante** : ~690 observations (341 communes × 3 élections municipales) malgré le faible nombre de scrutins
- **Diversité territoriale** : métropoles, zones périurbaines, rural — profils socio-économiques très variés
- **Validation temporelle** : entraînement sur le passé (2008–2014), test sur le présent (2020) — pas de fuite de données
- **Données open data** : INSEE, data.gouv.fr, DGFiP — entièrement reproductible

## Limites

- **Hypothèse de stabilité** : le modèle suppose que les liens socio-économiques → vote restent stables sur 12 ans
- **Facteurs locaux non captés** : maire populaire, scandale, fermeture d'usine — le modèle ne voit que les chiffres
- **Extrapolation naïve** : pour 2026, la population est extrapolée linéairement, les autres indicateurs sont maintenus à leur valeur 2020
- **Classification binaire** : Gauche/Droite simplifie la réalité politique (LREM classé Droite, pas de catégorie Centre)

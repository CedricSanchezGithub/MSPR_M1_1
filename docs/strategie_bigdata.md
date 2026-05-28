# Stratégie Big Data — Electio-Analytics

## Objectif

Définir l'approche de traitement des données retenue pour le POC, justifier les arbitrages méthodologiques (ETL vs ELT vs Datalake), inventorier les technologies réellement utilisées et tracer la perspective de passage à l'échelle.

Périmètre rappelé : **341 communes** de l'Hérault (34), **12 datasets publics** (~3,5 GB brut), **12 tables SQLite**, **12 features ML**, **2 Random Forest** (Classifier + Regressor).

---

## 1. Caractérisation Big Data : le projet face aux 5 V

| Dimension | Caractéristique du projet | Lecture |
|---|---|---|
| **Volume** | ~3,5 GB en entrée brute, dominés par le fichier élections de **2,3 GB** | Volumétrie modeste pour un système distribué, mais incompressible côté élections : le fichier couvre tous les scrutins nationaux 1999–2024. |
| **Variété** | CSV (UTF-8 et latin-1), XLSX multi-onglets à en-têtes complexes, TXT à séparateur `;` | Cinq thématiques sans format ni schéma commun, normalisation indispensable. |
| **Vélocité** | Mise à jour pluriannuelle (recensement, élections) à annuelle (état civil, comptes communes, CatNat) | Pas de flux temps réel ; batch reproductible suffit. |
| **Véracité** | Données officielles mais inégalement renseignées : revenu médian absent pour ~6 % des communes, fusions/scissions de communes au fil du temps | Contrôles qualité dans l'ETL (cf. `docs/qualite_donnees.md`). |
| **Valeur** | Forte : ces données publiques, correctement consolidées, constituent un actif différenciant pour Electio-Analytics | Le facteur limitant n'est pas la volumétrie mais la qualité du référentiel et la cohérence inter-sources. |

---

## 2. ETL, ELT, Datalake : quel patron retenir ?

| Critère | **ETL (retenu)** | ELT | Datalake |
|---|---|---|---|
| Volume brut typique | quelques GB | dizaines de GB+ | TB+ |
| Volume après filtrage | quelques MB (dépt 34) | — | — |
| Nature des données | structurées (CSV, XLSX, TXT) | semi-structurées | tous types, y compris non structurés |
| Fréquence | batch reproductible | flux ou batch fréquent | flux + batch |
| Complexité de déploiement | faible (script Python local) | moyenne à élevée (cluster / data warehouse) | élevée (Hadoop / cloud) |
| Compétences | Python + pandas | Spark / dbt / Snowflake | Hadoop / cloud / data engineering |
| Reproductibilité POC | excellente | bonne | dépend de l'infrastructure |

### 2.1 Choix retenu : ETL classique avec **filtrage en amont**

Sur ce POC, l'**ETL** s'impose. Trois raisons :

1. **Filtrage massif au plus tôt** : seules les lignes département 34 ont une valeur métier. Filtrer dès la lecture réduit la volumétrie d'un facteur 30 à 100 et évite de stocker des dizaines de millions de lignes inutiles.
2. **Données stables** : pas de flux temps réel, mise à jour pluriannuelle pour la majorité des sources. Un batch déclenché à la main suffit.
3. **Déploiement zéro infrastructure** : un script Python + une base SQLite tournent sur n'importe quel poste, sans serveur ni cloud.

### 2.2 Nuance ELT pour le **feature engineering**

Les **calculs dérivés** utilisés par la Phase 3 (analyses exploratoires) et la Phase 4 (panel ML) sont effectués **après chargement**, par requêtes SQL + pandas sur la base SQLite (`construire_panel()` dans `modele_predictif.py`, `_calcul_csp_pct()` et autres dans `analyse_exploratoire.py`). C'est techniquement de l'**ELT** :

- les **données brutes filtrées** sont conservées telles quelles dans la base (audit possible) ;
- les **agrégats** (`pct_gauche`, `dette_par_hab`, `taux_natalite`, `pct_cadres`, …) sont reconstruits à la demande ;
- ajouter une nouvelle feature ne nécessite **pas** de relancer l'ingestion.

On parle donc d'un **patron hybride ETL → ELT** : ETL pour l'ingestion (filtrage + chargement) et ELT pour la couche analytique (features dérivées). Cette hybridation est cohérente avec la taille du projet et préserve la traçabilité (les bruts restent en base).

### 2.3 Datalake : écarté pour ce POC

Un datalake (Hadoop, S3 + Parquet, lakehouse) serait disproportionné : pas de variété non structurée, pas de volumétrie justifiant un stockage distribué, équipe et budget POC limités. Cette option est envisagée à plus long terme dans la trajectoire d'industrialisation (§5).

---

## 3. Stack technique réellement utilisée

### 3.1 Ingestion

| Outil | Rôle | Justification |
|---|---|---|
| **Python 3** | Langage unique du pipeline | Écosystème data science mature, déjà installé sur les postes |
| **pandas ≥ 2.0** | Lecture CSV/XLSX, `to_sql`, normalisation | Standard de facto pour ETL de volume modéré |
| **openpyxl** | Lecture XLSX | Seule bibliothèque Python capable de lire les XLSX INSEE multi-onglets avec en-têtes complexes |
| **csv (stdlib)** | Lecture du fichier élections **2,3 GB** ligne à ligne | Pandas est volontairement **évité** pour ce fichier (consommation mémoire) ; itération directe via `csv.reader`, filtrage `_muni_` + département 34 au fil de l'eau |
| **pyarrow** | Backend rapide de pandas (CSV/Parquet) | Pinné dans `requirements.txt` ; utile à pandas pour les autres CSV volumineux. **Pas utilisé** pour le fichier élections, qui passe par `csv` stdlib. |

### 3.2 Stockage

| Outil | Rôle | Justification |
|---|---|---|
| **SQLite 3** | Entrepôt relationnel local | Sans serveur, portable, fichier unique, lecture native pandas/Power BI/DuckDB |
| **sqlite3 (stdlib)** | Connexion + DDL | Inclus à Python, aucun driver externe |

Détail du schéma : `docs/modele_multidimensionnel.md`, `docs/PIPELINE_ETL.md`.

### 3.3 Machine learning

| Outil | Rôle | Justification |
|---|---|---|
| **scikit-learn** | `RandomForestClassifier` + `RandomForestRegressor` | Bibliothèque de référence pour le ML supervisé en Python, interprétabilité native (feature importance) |
| **numpy** | Manipulation matricielle | Dépendance pandas / scikit-learn |
| **StandardScaler** | Normalisation des features | Sans effet pratique sur les arbres, conservé pour homogénéité du pipeline |

Choix de modèle : **deux Random Forest** (pas un seul). Le classifieur produit le camp binaire (Gauche/Droite), le régresseur produit le `% Gauche` continu. L'algorithme est retenu pour sa robustesse au faible volume (~690 lignes après `dropna`), sa capacité à capter les non-linéarités, son interprétabilité, et son insensibilité aux échelles. Hyperparamètres : `n_estimators=200, random_state=42`, le reste par défaut scikit-learn. Pas de grid search dans le POC.

### 3.4 Restitution

| Outil | Rôle | Justification |
|---|---|---|
| **matplotlib** (backend `Agg`) | Graphiques de base (line, scatter, bar, hist) | Standard Python, génère des PNG haute résolution |
| **seaborn** | Heatmaps, boxplots, matrice de confusion annotée | Styles statistiques professionnels par défaut |
| **geopandas** | Cartes choroplèthes communales | Lecture GeoJSON, jointure avec la base SQLite |
| **streamlit** | Dashboard interactif `app.py` (4 pages) | Framework Python natif, déploiement en une commande |

### 3.5 Dépendances pinnées vs installées à part

Le `requirements.txt` ne pin que les libs strictement nécessaires à l'ingestion : `pandas`, `pyarrow`, `openpyxl`. La stack ML / viz / dashboard (`scikit-learn`, `matplotlib`, `seaborn`, `geopandas`, `streamlit`) est installée séparément (cf. `README.md`, `CLAUDE.md`). Ce minimalisme est assumé pour le POC mais doit être durci avant industrialisation.

---

## 4. Pipeline et mode de restitution

```
EXTRACT (par dataset)
   pandas.read_excel() / pandas.read_csv()
   csv.reader pour le fichier élections (2,3 GB)
              │
              ▼
TRANSFORM (par module)
   1. Filtrage département 34
   2. Reconstruction codgeo (5 caractères)
   3. Classification politique Gauche/Droite (par défaut : Droite)
   4. Pivotement temporel (colonnes annuelles → lignes)
   5. Nettoyage et casting
              │
              ▼
LOAD → SQLite (12 tables, index sur codgeo et annee)
              │
              ├─── PHASE 3 : Analyse exploratoire (10 PNG)
              ├─── PHASE 4 : Random Forest (2 modèles) + 7 PNG + prédiction 2026
              └─── Streamlit app.py (lecture SQLite + PNG)
```

### 4.1 Mode de restitution dual

| Audience | Canal | Outil |
|---|---|---|
| Décideurs / clients | PNG statiques pré-calculés (17 au total) | matplotlib + seaborn + geopandas |
| Analystes internes Electio-Analytics | Dashboard interactif | Streamlit (`app.py`) lisant SQLite et les PNG |
| Data scientists | Notebooks Jupyter + accès SQL direct | `notebooks/`, `sqlite3` |
| Outils BI tiers | Base SQLite connectable | ODBC SQLite (Power BI, DBeaver, etc.) |

Cette double restitution (statique + interactive) couvre les usages présentation (slides, rapport) et exploration (filtrage, drill-down).

---

## 5. Passage à l'échelle : trajectoire d'industrialisation

Le POC est volontairement contraint à un département. Si Electio-Analytics étend le périmètre à plusieurs départements ou à la France entière (~35 000 communes), chaque couche doit évoluer.

| Composant | POC actuel | Cible industrielle |
|---|---|---|
| Ingestion | pandas + csv stdlib, exécution mono-poste | Apache Spark ou Dask ; lecture parallèle des sources |
| Orchestration | Script manuel `python main.py` | Apache Airflow / Prefect avec DAG planifié |
| Stockage | SQLite (fichier `.db`) | PostgreSQL (transactionnel) ou DuckDB + Parquet sur object store (analytique) |
| ML | scikit-learn local, run unique | scikit-learn / XGBoost + MLflow pour tracking, validation croisée temporelle |
| Restitution | Streamlit local + PNG | Power BI / Metabase + Streamlit conteneurisé (Docker, Kubernetes) |
| Infrastructure | Poste de travail | Cloud (AWS, GCP, OVH) ou on-premise mutualisé |

Charge estimée pour cette montée en charge : 3 à 6 mois pour une équipe de 2–3 data engineers, sans réécriture des transformations métier (les fonctions `etl_*` restent valides). Le **schéma logique en grappe** (cf. `docs/modele_multidimensionnel.md`) est compatible avec PostgreSQL : les types `TEXT`, `INTEGER`, `REAL` se mappent directement.

---

## 6. Risques et arbitrages assumés

| Risque / arbitrage | Décision | Mitigation |
|---|---|---|
| Volumétrie du fichier élections (2,3 GB) | Lecture ligne à ligne via `csv` stdlib (et non pandas) | Empreinte mémoire constante, filtrage à la volée sur `_muni_` et dépt 34 |
| `requirements.txt` minimal | ML/viz/dashboard installés à part | Documenter explicitement dans `README.md`, `CLAUDE.md` ; à durcir pour la prod |
| Schéma SQLite partiellement dynamique (`revenus`, `csp`, `secteurs_activite`, `diplomes`, `csp_diplome`) | `df.to_sql(..., if_exists='replace')` recrée la table avec les colonnes du DataFrame source | Documenté dans `PIPELINE_ETL.md` ; le DDL placeholder ne garantit que `codgeo` et `annee` |
| Foreign keys désactivées (`PRAGMA foreign_keys=OFF`) | Performance d'écriture privilégiée | Vérification *a posteriori* dans `validate()` |
| Choix unique de Random Forest | Pas de benchmark multi-modèles dans le périmètre POC | Documenté comme priorité d'amélioration |
| Classification par défaut = **Droite** | Quand aucune nuance ni mot-clé ne matche | Biais documenté ; à pondérer lors de l'interprétation |

---

## 7. Pointeurs

- [`docs/architecture_bi.md`](architecture_bi.md) — vue d'ensemble technique (3 couches).
- [`docs/PIPELINE_ETL.md`](PIPELINE_ETL.md) — détail des transformations.
- [`docs/modele_multidimensionnel.md`](modele_multidimensionnel.md) — schéma en grappe.
- [`docs/qualite_donnees.md`](qualite_donnees.md) — contrôles qualité dans l'ETL.
- `requirements.txt`, `main.py`, `app.py` — implémentations.

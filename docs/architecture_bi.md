# Architecture Business Intelligence — Electio-Analytics

## Objectif

Décrire l'architecture décisionnelle du projet : flux de données, technologies retenues à chaque étape, points de bascule entre couches et choix structurants. Le périmètre est un **POC** sur le département de l'Hérault (34), **341 communes**, **12 datasets publics**, **12 tables SQLite**.

---

## 1. Vue d'ensemble : architecture à trois couches

L'architecture suit le découpage BI classique **Collecte → Stockage → Restitution**. Une couche de **machine learning** s'intercale entre stockage et restitution pour la production des prédictions 2026.

```
┌────────────────────────────────────────────────────────────────────────┐
│  COUCHE 1 — COLLECTE / INGESTION                                        │
│  Sources : 12 fichiers (~3,5 GB) — INSEE · data.gouv.fr · DGFiP · GASPAR│
│  Outils  : Python 3 · pandas · openpyxl · csv stdlib                    │
│  Sortie  : DataFrames filtrés sur le département 34                     │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │ Pipeline ETL (main.py etl)
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│  COUCHE 2 — STOCKAGE / ENTREPÔT                                         │
│  data/output/electio_herault.db                                         │
│  SQLite 3 · 12 tables · grappe autour de COMMUNES · index (codgeo, annee)│
└────────────────────────────────┬───────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│  ANALYSE       │  │  ML / PRÉDICTION     │  │  EXPLORATION         │
│  (Phase 3)     │  │  (Phase 4)           │  │  (notebooks ad hoc)  │
│  10 PNG        │  │  Random Forest ×2    │  │  Jupyter             │
│  matplotlib    │  │  scikit-learn        │  │                      │
│  seaborn       │  │  7 PNG               │  │                      │
│  geopandas     │  │  prédictions 2026    │  │                      │
└────────┬───────┘  └──────────┬───────────┘  └──────────────────────┘
         │                     │
         └──────────┬──────────┘
                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  COUCHE 3 — RESTITUTION                                                 │
│  Sortie statique : graphiques/phase3 (10 PNG), graphiques/phase4 (7 PNG)│
│  Sortie interactive : app.py — Streamlit (4 pages) lisant SQLite + PNG  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Couche 1 — Collecte / Ingestion

### 2.1 Sources

Les 12 datasets bruts sont déposés dans `data/input/`, organisés par thématique (5 dossiers).

| Thématique | Fichiers | Organisme | Format |
|---|---|---|---|
| `elections/` | `candidats_results.txt` (~2,3 GB) | data.gouv.fr / Ministère de l'Intérieur | TXT `;` |
| `demographie/` | `base-pop-historiques-1876-2023.xlsx` ; `DS_ETAT_CIVIL_NAIS_COMMUNES_data.csv` ; `DS_ETAT_CIVIL_DECES_COMMUNES_data.csv` | INSEE | XLSX, CSV |
| `economie/` | `revenu-des-francais-a-la-commune-*.csv` ; `pop-act2554-csp-cd-6822.xlsx` ; `pop-act2554-empl-sa-sexe-cd-6822.xlsx` ; `comptes_communes_*.csv` (4 millésimes) | data.gouv.fr · INSEE · DGFiP | CSV, XLSX |
| `education/` | `base-cc-diplomes-formation-2022.CSV` ; `pop-act2554-csp-dipl-cd-6822.xlsx` | INSEE | CSV, XLSX |
| `environnement/` | `catnat_gaspar.csv` ; `risq_gaspar.csv` | GASPAR / data.gouv.fr | CSV |

Détail dans [`SOURCES_DONNEES.md`](../data/input/SOURCES_DONNEES.md) et [`docs/referentiel_donnees.md`](referentiel_donnees.md).

### 2.2 Outillage technique

| Outil | Rôle |
|---|---|
| **Python 3** | Langage unique de la pipeline |
| **pandas ≥ 2.0** | Lecture CSV/XLSX, manipulation tabulaire, `to_sql` |
| **openpyxl** | Lecture des XLSX INSEE multi-onglets (headers complexes) |
| **csv (stdlib)** | Lecture ligne à ligne du fichier élections de 2,3 GB (pandas n'est pas utilisé pour ce fichier : iteration directe `csv.reader` pour minimiser la mémoire) |
| **sqlite3 (stdlib)** | Connexion à l'entrepôt, exécution DDL |

### 2.3 Stratégie d'ingestion

- **Filtrage en amont** : chaque module ETL filtre dès la lecture sur le département 34 (`codgeo` commençant par `'34'` ou `dep == '34'`). Volumétrie réduite d'un facteur 30 à 100.
- **Reconstruction d'identifiant** : selon les sources, `codgeo` est reconstitué depuis (a) une colonne unique paddée à 5 caractères, (b) `dep` + `commune` zfill, ou (c) `Département` + `Commune` (colonnes INSEE séparées).
- **Idempotence** : la base est **systématiquement supprimée** au début du pipeline et recréée à neuf (cf. `os.remove(DB_PATH)`, ligne 883 d'`etl_pipeline.py`). Aucun mode incrémental.

---

## 3. Couche 2 — Stockage / Entrepôt

### 3.1 Choix du SGBD : SQLite

| Critère | Pourquoi SQLite |
|---|---|
| Volumétrie cible | < 10 MB après filtrage département (base finale de l'ordre de quelques MB) |
| Concurrence | Aucune écriture concurrente (1 producteur, plusieurs lecteurs) |
| Portabilité | Fichier unique `.db`, copiable, versionnable s'il est petit |
| Coût | Open source, fourni avec Python (`sqlite3` stdlib) |
| Compatibilité aval | Lecture native par pandas, Streamlit, Power BI (ODBC), DBeaver, DuckDB |

La connexion SQLite est ouverte avec deux PRAGMA (cf. `etl_pipeline.py` lignes 888–889) :

```python
PRAGMA journal_mode = WAL   # accélère les écritures massives
PRAGMA foreign_keys = OFF   # les contraintes FK déclarées dans le DDL sont documentaires
```

Conséquence : les clauses `FOREIGN KEY` du DDL sont **documentaires** ; la cohérence référentielle est vérifiée *a posteriori* par la fonction `validate()` (cf. `PIPELINE_ETL.md` §4).

### 3.2 Modèle multidimensionnel

Schéma **en grappe** autour de la table maîtresse `communes`. Détail dans [`docs/modele_multidimensionnel.md`](modele_multidimensionnel.md). Les 12 tables :

| Table | Grain | Schéma |
|---|---|---|
| `communes` | 1 ligne / commune | DDL strict (PK `codgeo`) |
| `elections` | candidat × tour × année | DDL strict |
| `population` | commune × année | DDL strict |
| `naissances_deces` | commune × année | DDL strict |
| `revenus` | commune (snapshot) | dynamique (`df.to_sql replace`) |
| `csp` | commune × année | dynamique |
| `secteurs_activite` | commune × année | dynamique |
| `diplomes` | commune (snapshot) | dynamique |
| `csp_diplome` | commune × année | dynamique |
| `comptes_communes` | commune × année | DDL strict après remplacement |
| `catnat` | arrêté × commune | DDL strict |
| `risques` | risque × commune | DDL strict |

### 3.3 Index physiques

Index créés sur les colonnes de jointure fréquentes :

```
idx_elections_codgeo · idx_elections_annee
idx_population_codgeo
idx_naissances_deces_codgeo
idx_csp_codgeo · idx_secteurs_codgeo
idx_comptes_codgeo
idx_catnat_codgeo · idx_risques_codgeo
```

---

## 4. Couche ML — Phase 4

La couche ML s'intercale entre stockage et restitution. Elle est implémentée dans `scripts/prediction/modele_predictif.py` et orchestrée par `python main.py predict`.

| Étape | Composant |
|---|---|
| **Feature engineering** | Fonction `construire_panel()` : 7 requêtes SQL agrégées (`pct_gauche`, population, CSP, revenus, diplômes, comptes, natalité, CatNat) → DataFrame dénormalisé `(codgeo, annee)` × 12 features. |
| **Split temporel** | Train = {2008, 2014}, Test = 2020, Prédiction = 2026. |
| **Modèles** | `RandomForestClassifier(n_estimators=200, random_state=42)` pour le camp (Gauche/Droite) **et** `RandomForestRegressor(n_estimators=200, random_state=42)` pour le `% Gauche` continu. |
| **Pré-traitement** | `StandardScaler` (sans effet pratique sur les arbres, conservé pour homogénéité). |
| **Extrapolation 2026** | Population : tendance linéaire 2014→2020 ; autres features : valeur 2020 maintenue ; CatNat : cumul historique inchangé. |
| **Sortie** | 7 visualisations PNG (`graphiques/phase4/`) + impression console des métriques. |

Métriques de référence (test 2020) : **Accuracy 89,6 %**, **F1-score pondéré 0,906**.

---

## 5. Couche 3 — Restitution

### 5.1 Restitution statique : graphiques PNG

| Dossier | Volume | Contenu |
|---|---|---|
| `graphiques/phase3/` | 10 PNG | Analyse exploratoire — évolution Gauche/Droite, carte 2020, scatters socio-éco, heatmap de corrélations, boxplot, top croissance population, CatNat |
| `graphiques/phase4/` | 7 PNG | Importance features, matrice de confusion, prédictions temporelles, carte 2026, distribution % Gauche, réel vs prédit, communes remarquables |

Bibliothèques : `matplotlib` (backend `Agg`), `seaborn` (heatmap, boxplot), `geopandas` (cartes choroplèthes à partir d'un GeoJSON téléchargé à la volée). Chaque figure est sauvegardée avec `plt.savefig(..., dpi=150, bbox_inches='tight')` puis `plt.close(fig)` pour éviter les fuites mémoire.

### 5.2 Restitution interactive : dashboard Streamlit

L'application `app.py` (à la racine, lancée par `streamlit run app.py`) lit directement la base SQLite et les PNG produits par les Phases 3 et 4. Elle se compose de **quatre pages** accessibles via la sidebar :

| Page | Source | Contenu principal |
|---|---|---|
| **Vue d'ensemble** | SQLite | Métriques départementales 2020, bar chart par année, table des communes remarquables |
| **Données électorales** | SQLite | Filtre par commune et par année, table dynamique, distribution `% Gauche` |
| **Analyse exploratoire** | `graphiques/phase3/*.png` + SQLite | Sélecteur de graphique parmi les 10 + scatter `revenu vs vote` recalculé à la volée |
| **Prédictions 2026** | `graphiques/phase4/*.png` + SQLite | Sélecteur parmi les 7 PNG, fiche métriques, liste des 12 features, courbe communes remarquables |

Cache : décorateurs `@st.cache_data` sur les chargements SQL pour éviter les re-requêtes.

### 5.3 Exploration ad hoc (notebooks Jupyter)

Le dossier `notebooks/` contient un notebook d'exploration interactive consommant la même base SQLite. Il sert à l'analyse ponctuelle et au prototypage de nouvelles features avant intégration au pipeline.

---

## 6. Orchestration

Le point d'entrée unique est `main.py` (CLI). Les commandes critiques :

```bash
python main.py etl        # Phase 2 : 12 datasets → SQLite
python main.py analyse    # Phase 3 : 10 PNG dans graphiques/phase3/
python main.py predict    # Phase 4 : 7 PNG dans graphiques/phase4/ + prédictions 2026
python main.py all        # enchaîne etl → analyse → predict
streamlit run app.py      # dashboard
```

Les phases consomment la sortie de la précédente : **réexécuter `etl`** dès que les fichiers d'entrée changent (sinon Phase 3 et Phase 4 utilisent silencieusement des données obsolètes).

---

## 7. Justification des choix technologiques

| Critère | Choix | Justification |
|---|---|---|
| Coût | 100 % open source | POC à budget contraint, transférabilité au client |
| Reproductibilité | Python + SQLite | Tourne sur tout poste, pas de serveur ; CLI unique |
| Compétences | Stack Python data | Largement maîtrisée, formation minimale pour le client |
| Volumétrie POC | SQLite | Fichier final ≪ 10 MB, suffisant pour 341 communes |
| Scalabilité | Pipeline modulaire | Portage vers PostgreSQL (couche 2) ou Spark / Airflow (couche 1) possible sans refonte |
| Dépendances déclarées | `requirements.txt` ne pin que `pandas, pyarrow, openpyxl` | Les libs ML/viz/dashboard sont installées à part (cf. `README.md`, `CLAUDE.md`). À durcir lors d'une industrialisation. |

---

## 8. Trajectoire de passage à l'échelle

Pour étendre le périmètre (par exemple, 5 départements ou couverture nationale) :

| Couche | POC actuel | Cible industrielle |
|---|---|---|
| Ingestion | pandas + csv stdlib (mono-poste) | Apache Airflow + Spark / Dask |
| Stockage | SQLite (fichier `.db` ~quelques MB) | PostgreSQL ou DuckDB / Parquet sur object store |
| ML | scikit-learn local | MLflow + scikit-learn ou XGBoost, tracking des expériences |
| Restitution | Streamlit local + PNG | Power BI / Metabase + service Streamlit conteneurisé |
| Hébergement | Poste de travail | Cloud (AWS / GCP / OVH) |

La grappe SQLite est compatible avec une migration directe vers PostgreSQL (types `TEXT`, `INTEGER`, `REAL` mappables sans transformation).

---

## 9. Pointeurs

- [`docs/PIPELINE_ETL.md`](PIPELINE_ETL.md) — détail des transformations.
- [`docs/modele_multidimensionnel.md`](modele_multidimensionnel.md) — schéma en grappe.
- [`docs/referentiel_donnees.md`](referentiel_donnees.md) — dictionnaire des 12 tables.
- [`docs/strategie_bigdata.md`](strategie_bigdata.md) — choix ETL/ELT et stack.
- `main.py`, `app.py`, `scripts/etl/etl_pipeline.py`, `scripts/analyse/analyse_exploratoire.py`, `scripts/prediction/modele_predictif.py` — implémentations.
- [`docs/pipeline_etl.drawio`](pipeline_etl.drawio) — diagramme éditable du pipeline.

# Roadmap — MSPR Big Data & Analyse Électorale

> Dernière mise à jour : 9 février 2026

## Contexte

POC pour **Electio-Analytics** : prédiction des tendances électorales à moyen terme (1-3 ans) à partir d'indicateurs socio-économiques et environnementaux, sur un périmètre géographique restreint.

Cahier des charges : `25-26 I1 EISI - Sujet MSPR TPRE813.pdf`

---

## Données collectées (12 datasets intégrés)

| Dataset | Dossier | Années | Indicateur | Clé jointure |
|---------|---------|--------|------------|--------------|
| Résultats électoraux (2.1 GB) | elections/ | 1999-2024 | Élections | Code dept + commune |
| Population historique (6.7 MB) | demographie/ | 1876-2023 | Démographie | CODGEO |
| Naissances par commune (24.4 MB) | demographie/ | 2008-2024 | Démographie | GEO (filtrer GEO_OBJECT=COM) |
| Décès par commune (24.4 MB) | demographie/ | 2008-2024 | Démographie | GEO (filtrer GEO_OBJECT=COM) |
| CSP par commune (28.5 MB) | economie/ | 1968-2022 | Emploi | Commune en géo courante |
| Secteur activité × sexe (23.5 MB) | economie/ | 1968-2022 | Emploi | Commune en géo courante |
| Revenus par commune (4.8 MB) | economie/ | snapshot | Économie | Code géographique |
| Comptes communes DGFiP (652 MB) | economie/ | 2000-2022 | Finances publiques | dep + icom |
| CSP × diplôme (51.9 MB) | education/ | 1968-2022 | Éducation | Commune en géo courante |
| Diplômes formation (81 MB) | education/ | 2022 | Éducation | CODGEO |
| CatNat GASPAR (34.5 MB) | environnement/ | 1985-2022+ | Environnement | cod_commune |
| Risques connus GASPAR (8.4 MB) | environnement/ | snapshot | Environnement | cod_commune |

## Données en cours d'acquisition

*Aucune — tous les datasets prioritaires ont été téléchargés.*

## Données exclues (dans `data/input/exclus/`)

- `fichier_pop_reference_6823.xlsx` — doublon population
- `barometre-du-numerique` (parquet + csv) — pas de CODGEO
- `agri.xlsx` + GeoJSON SAU — pas temporel / couverture partielle
- `Arretes_de_catastrophe_naturelles.xlsx` — doublon obsolète du CSV GASPAR (s'arrête en avril 2015)
- `azi_gaspar.csv` — Atlas zones inondables, redondant avec risq_gaspar
- `pprn_gaspar.csv` — Plans prévention risques naturels, trop administratif
- `pprm_gaspar.csv` — Risques miniers, hors scope (996 lignes)
- `pprt_gaspar.csv` — Risques technologiques, hors scope
- `dicrim_gaspar.csv` — Registre admin (publication de documents), pas un indicateur
- `tim_gaspar.csv` — Transmission info au maire, purement administratif

---

## Ce qui est fait

- [x] Collecte de 12 datasets publics (INSEE, data.gouv.fr, DGFiP) couvrant 6 thématiques
- [x] Organisation thématique : `elections/`, `economie/`, `education/`, `demographie/`, `environnement/`, `exclus/`, `nouveau/`
- [x] Scripts d'exploration par format (xlsx, csv, parquet, geojson) dans `scripts/`
- [x] Documentation `.md` par dataset dans chaque dossier
- [x] `SOURCES_DONNEES.md` avec tous les liens de téléchargement
- [x] `.gitignore` configuré (fichiers data ignorés par extension, docs `.md` versionnées)
- [x] `CLAUDE.md` avec règles du projet (ne jamais lire les data directement, générer des scripts)
- [x] Recherche approfondie de datasets environnementaux/climatiques
- [x] Intégration des données GASPAR (CatNat + risques) dans `environnement/`
- [x] Intégration des comptes individuels des communes (DGFiP 2000-2022) dans `economie/`
- [x] Analyse du cahier des charges et identification de tous les écarts

---

## Ce qui manque (vs cahier des charges)

### 1. Périmètre géographique — CHOISI : Hérault (34)

> *« La POC devra être conçue pour un secteur géographique restreint (ville, arrondissement, circonscription, département…) et unique. »*

**Département de l'Hérault (34)** — ~340 communes. Justification :
- Mix urbain/rural (Montpellier, Béziers, Sète + arrière-pays)
- Diversité politique (gauche/écolo à Montpellier, RN à Béziers, zones rurales variées)
- Données environnementales pertinentes (inondations, sécheresse méditerranéenne)
- Code département classique (pas d'exception type Corse 2A/2B)
- Taille exploitable pour une POC, généralisable ensuite au niveau national

### 2. Indicateurs du sujet — couverture actuelle

Les indicateurs cités dans le cahier des charges sont des **exemples** (*« comme la sécurité, l'emploi, la vie associative… »*), pas une liste obligatoire. Le critère d'évaluation est la **pertinence et la justification** des indicateurs retenus.

| Indicateur cité | Couvert ? | Par quel dataset |
|----------------|-----------|------------------|
| Élections (résultats historiques) | **Oui** | `candidats_results.txt` (1999-2024) |
| Emploi | **Oui** | CSP + secteurs d'activité (1968-2022) |
| Population / démographie | **Oui** | Population historique + naissances + décès |
| Pauvreté / revenus | **Oui** | Revenus par commune |
| Activité économique | **Oui** | Comptes communes DGFiP (dépenses, investissement) |
| Dépenses publiques locales | **Oui** | Comptes communes DGFiP |
| Environnement | **Oui** | CatNat GASPAR + risques connus |
| Éducation | **Oui** (bonus) | Diplômes + CSP×diplôme |
| Sécurité | Non | Justifier dans le rapport (données communales peu fiables) |
| Vie associative | Non | Justifier dans le rapport (RNA peu structuré) |

### 3. Livrables manquants

| Livrable | Statut |
|----------|--------|
| Pipeline ETL automatisé | ✅ `scripts/etl_pipeline.py` |
| Base de données structurée (SQL ou NoSQL) | ✅ SQLite `data/output/electio_herault.db` (12 tables, 9.5 MB) |
| Modèle Conceptuel de Données (MCD) | ✅ DDL dans `etl_pipeline.py`, relations dans `PHASE2_ETL.md` |
| Analyse exploratoire + visualisations (cartes, histogrammes, heatmaps) | ✅ `scripts/analyse_exploratoire.py` (10 graphiques) |
| Modèle prédictif supervisé (train/test, accuracy) | Pas commencé |
| Prédictions à 1, 2 et 3 ans (courbes, cartes de chaleur, probabilités) | Pas commencé |
| Dossier de synthèse / rapport | Pas commencé |
| Support de soutenance | Pas commencé |
| Code propre et commenté | En cours |

---

## Plan d'action

### Phase 1 — Cadrage & collecte (TERMINÉE)

- [x] **Collecte de données** : 12 datasets, 6 thématiques
- [x] **Périmètre géographique** : département de l'Hérault (34)
- [ ] Justifier les choix (zone géo + indicateurs) dans le rapport

### Phase 2 — Modélisation & ETL (TERMINÉE)

- [x] **Concevoir le MCD** (12 tables, relations via `codgeo`)
- [x] **Créer la base de données** (SQLite `data/output/electio_herault.db`)
- [x] **Pipeline ETL** (`scripts/etl_pipeline.py`, commande `python main.py etl`) :
  - [x] Extraction : lecture des 12 fichiers sources (CSV, XLSX, TXT 2.3 GB)
  - [x] Transformation : normalisation codgeo, filtrage dept 34, classification Gauche/Droite
  - [x] Chargement : 12 tables SQLite, 341 communes, ~100k lignes total
- [x] Nommer les tables et champs de manière pertinente
- [x] Documenter le schéma (DDL + `PHASE2_ETL.md`)

### Phase 3 — Analyse exploratoire (EN COURS)

- [x] **Script** : `scripts/analyse_exploratoire.py` (commande `python main.py analyse`)
- [x] **10 visualisations** dans `graphiques/phase3/` :
  - [x] 01 — Évolution Gauche/Droite 2002-2022 (line chart)
  - [x] 02 — Carte choroplèthe des communes (GeoJSON, T1 2022)
  - [x] 03 — Revenu médian vs % Gauche (scatter + Pearson)
  - [x] 04 — Heatmap de corrélation (9 indicateurs vs % Gauche)
  - [x] 05 — Box plot revenus par camp
  - [x] 06 — CSP : % cadres vs % ouvriers par camp (scatter)
  - [x] 07 — Évolution population (top 10 croissance + top 10 déclin)
  - [x] 08 — Dette par habitant vs % Gauche (scatter)
  - [x] 09 — % Diplôme supérieur vs % Gauche (scatter + Pearson)
  - [x] 10 — Top 20 communes CatNat par camp (bar chart)
- [x] Identifier les indicateurs les plus corrélés aux résultats électoraux

### Phase 4 — Modèle prédictif

- [ ] Préparer les features (feature engineering)
- [ ] Découper en jeu d'entraînement / jeu de test
- [ ] **Tester plusieurs modèles** (régression logistique, random forest, gradient boosting…)
- [ ] Évaluer : accuracy, matrice de confusion, F1-score
- [ ] Choisir le meilleur modèle et justifier
- [ ] Répondre aux questions d'analyse :
  - [ ] Quelle donnée est la plus corrélée aux résultats ?
  - [ ] Définir le principe d'un apprentissage supervisé
  - [ ] Comment définir l'accuracy du modèle ?

### Phase 5 — Prédictions & visualisations

- [ ] Générer les prédictions à **1, 2 et 3 ans**
- [ ] Visualisations des scénarios :
  - [ ] Courbes temporelles
  - [ ] Cartes de chaleur
  - [ ] Diagrammes de probabilité
- [ ] Export compatible PowerBI si nécessaire

### Phase 6 — Livrables

- [ ] **Dossier de synthèse** (rapport complet)
- [ ] **Jeu de données nettoyé** (export SQL ou CSV)
- [ ] **Code propre et commenté** (scripts Python / notebooks Jupyter)
- [ ] **Support de soutenance** (20 min de présentation)

---

## Structure du projet

```
MSPR_1/
├── CLAUDE.md                    # Règles pour Claude Code
├── ROADMAP.md                   # Ce fichier
├── SOURCES_DONNEES.md           # Liens de téléchargement des données
├── requirements.txt             # Dépendances Python
├── main.py                      # Point d'entrée (orchestre les scripts)
├── scripts/
│   ├── explore_*.py             # Scripts d'exploration par format
│   ├── classify_candidats*.py   # Classification des candidats
│   └── visualize_*.py           # Visualisations
├── data/
│   ├── input/
│   │   ├── elections/           # Résultats électoraux
│   │   ├── economie/            # Revenus, CSP, secteurs d'activité, comptes communes
│   │   ├── education/           # Diplômes, CSP×diplôme
│   │   ├── demographie/         # Population, naissances, décès
│   │   ├── environnement/       # CatNat GASPAR, risques connus
│   │   ├── nouveau/             # Zone de dépôt pour nouveaux fichiers
│   │   └── exclus/              # Fichiers écartés + README
│   └── output/                  # Résultats des explorations
```

## Outils & formats attendus

| Besoin | Outil |
|--------|-------|
| Langage | Python (Pandas, scikit-learn) |
| Visualisation | Matplotlib / Seaborn / PowerBI |
| Base de données | SQL (SQLite ou PostgreSQL) |
| Notebooks | Jupyter |
| Versionnage | Git |
| Données | CSV, XLSX → SQL |

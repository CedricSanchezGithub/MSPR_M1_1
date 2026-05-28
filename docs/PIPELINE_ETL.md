# Documentation Pipeline ETL - Electio-Analytics

## Vue d'ensemble du Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                           PIPELINE ETL - ELECTIO-ANALYTICS                                  │
│                        (Extraction → Transformation → Load)                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────────────┐
                                    │   SOURCES DE DONNÉES │
                                    │   (data/input/)      │
                                    └──────────┬──────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
         ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
         │   ÉLECTIONS      │      │   DÉMOGRAPHIE    │      │   ÉCONOMIE       │
         │                  │      │                  │      │                  │
         │ candidats_results│      │ base-pop-*.xlsx  │      │ revenu-*.csv    │
         │ .txt (2.3GB)     │      │ DS_ETAT_CIVIL_*  │      │ pop-act*.xlsx    │
         │                  │      │                   │      │ comptes_*.csv    │
         └────────┬─────────┘      └────────┬─────────┘      └────────┬─────────┘
                  │                         │                         │
                  │              ┌──────────┴──────────┐              │
                  │              │                     │              │
                  ▼              ▼                     ▼              ▼
         ┌──────────────────┐┌──────────────────┐┌──────────────────┐
         │   ÉDUCATION      ││  ENVIRONNEMENT   ││   ... (autres)   │
         │                  ││                  ││                  │
         │ base-cc-diplomes ││ catnat_gaspar.csv││                  │
         │ pop-act*dipl*.xlsx││ risq_gaspar.csv  ││                  │
         └──────────────────┘└──────────────────┘└──────────────────┘
```

---

## Étape 1 : EXTRACTION (E)

Les données brutes proviennent de plusieurs sources officielles :

| Source | Fichier | Description |
|--------|---------|-------------|
| **Élections** | `candidats_results.txt` | Résultats électoraux (municipales) - 2.3GB |
| **Démographie** | `base-pop-historiques-1876-2023.xlsx` | Population historique |
| **Démographie** | `DS_ETAT_CIVIL_*_data.csv` | Naissances et décès |
| **Économie** | `revenu-des-francais-*.csv` | Revenus par commune |
| **Économie** | `pop-act*-csp-*.xlsx` | Population active par CSP |
| **Économie** | `pop-act*-empl-*.xlsx` | Emploi par secteur |
| **Économie** | `comptes_communes_*.csv` | Finances locales |
| **Éducation** | `base-cc-diplomes-formation-*.CSV` | Niveaux de diplômes |
| **Éducation** | `pop-act*-csp-dipl-*.xlsx` | CSP × Diplôme |
| **Environnement** | `catnat_gaspar.csv` | Catastrophes naturelles |
| **Environnement** | `risq_gaspar.csv` | Inventaire des risques |

---

## Étape 2 : TRANSFORMATION (T)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TRANSFORMATIONS APPLIQUÉES                          │
└─────────────────────────────────────────────────────────────────────────────┘

  1. FILTRAGE DÉPARTEMENT 34 (HÉRAULT)
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  Toutes les sources → Filtrage sur codgeo commence par "34"            │
  │  Ex: 34001, 34002, ... → 34001, 34002, ...                             │
  └─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  2. NORMALISATION CODGEO
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  • dep (2 car.) + commune (3 car.) → codgeo (5 car.)                  │
  │  • Application de zfill(5) pour uniformiser                            │
  │  Ex: "34" + "001" → "34001"                                            │
  └─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  3. CLASSIFICATION POLITIQUE (Gauche/Droite)
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  Pour les élections municipales :                                        │
  │  • Classification par nuance (code parti)                              │
  │    - GAUCHE: EXG, COM, FG, SOC, VEC, DVG, NUP, FI, ...                │
  │    - DROITE: FN, UMP, LR, UDF, DVD, REM, DIV, ...                     │
  │                                                                         │
  │  • Classification par mots-clés dans le libellé de liste                │
  │    (appliquée si aucun code de nuance ne matche) :                      │
  │    - GAUCHE : socialiste, communiste, gauche, écologi, vert,            │
  │               insoumis, ouvrier, citoyen, solidaire                     │
  │    - DROITE : national, républicain, droite, marche, renaissance,       │
  │               ensemble, majorité, libéral, conservat                    │
  │                                                                         │
  │  ⚠ Par défaut, si **aucune nuance ni mot-clé** ne matche, le camp est   │
  │    classé **"Droite"** (cf. ligne 105 de etl_pipeline.py). Ce parti     │
  │    pris est à garder en tête pour l'interprétation des résultats : il   │
  │    favorise mécaniquement la classe "Droite" sur les listes sans       │
  │    étiquette politique claire (listes "sans étiquette", divers, etc.). │
  └─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  4. PIVOTAGE TEMPOREL
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  • Colonnes PMUN2023, PMUN2014, ... → Lignes (codgeo, annee, pop)     │
  │  • Pour population, revenus, CSP, secteurs...                          │
  └─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  5. NETTOYAGE & CONVERSION
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  • Suppression colonnes inutiles (codes, libellés géographiques)        │
  │  • Conversion types (str → int, float)                                 │
  │  • Normalisation noms de colonnes (minuscules, underscores)            │
  └─────────────────────────────────────────────────────────────────────────┘
```

---

## Étape 3 : CHARGEMENT (L)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     BASE DE DONNÉES SQLite                                 │
│                     (data/output/electio_herault.db)                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│    communes         │     │    elections         │     │    population        │
│                     │     │                     │     │                     │
│ • codgeo (PK)       │     │ • codgeo (FK)       │     │ • codgeo (FK)       │
│ • nom               │     │ • annee             │     │ • annee             │
│ • departement       │     │ • tour              │     │ • population        │
│                     │     │ • nom_candidat      │     │                     │
│                     │     │ • prenom_candidat   │     │                     │
│                     │     │ • nuance            │     │                     │
│                     │     │ • voix              │     │                     │
│                     │     │ • pct_voix_*        │     │                     │
│                     │     │ • camp (G/D)        │     │                     │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│  naissances_deces   │     │    revenus          │     │    csp               │
│                     │     │                     │     │                     │
│ • codgeo (FK)       │     │ • codgeo (PK)       │     │ • codgeo (FK)       │
│ • annee             │     │ • (nombreuses       │     │ • annee             │
│ • naissances        │     │   colonnes          │     │ • (colonnes CSP)    │
│ • deces             │     │   numériques)       │     │                     │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────────────┐
│  secteurs_activite │     │    diplomes         │     │      comptes_communes        │
│                     │     │                     │     │                             │
│ • codgeo (FK)       │     │ • codgeo (PK)       │     │ • codgeo (FK)               │
│ • annee             │     │ • (diplômes)        │     │ • annee                     │
│ • (secteurs)        │     │                     │     │ • population                │
│                     │     │                     │     │ • produits_fonctionnement   │
│                     │     │                     │     │ • charges_fonctionnement    │
│                     │     │                     │     │ • depenses_personnel        │
│                     │     │                     │     │ • depenses_investissement   │
│                     │     │                     │     │ • depenses_equipement       │
│                     │     │                     │     │ • dette                     │
│                     │     │                     │     │ • dgf                       │
│                     │     │                     │     │ • capacite_autofinancement  │
│                     │     │                     │     │ • impots_directs            │
│                     │     │                     │     │ • impots_indirects          │
└─────────────────────┘     └─────────────────────┘     └─────────────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│    catnat           │     │    risques           │     │    csp_diplome      │
│                     │     │                     │     │                     │
│ • codgeo (FK)       │     │ • codgeo (FK)       │     │ • codgeo (FK)       │
│ • risque            │     │ • libelle_risque    │     │ • annee             │
│ • date_debut        │     │ • code_risque       │     │ • (schéma dynamique │
│ • date_fin          │     │                     │     │   issu du DataFrame │
│ • date_arrete       │     │                     │     │   source — voir     │
│                     │     │                     │     │   note ci-dessous)  │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘

> **Note — tables à schéma dynamique.**
> Les tables `revenus`, `csp`, `secteurs_activite`, `diplomes`, `csp_diplome` et
> `comptes_communes` sont écrites via `df.to_sql(..., if_exists='replace')`. Cet
> appel **écrase** le DDL initial et crée un schéma **dérivé directement du
> DataFrame source** (colonnes nettoyées en minuscules / underscores). Le bloc
> `CREATE TABLE` du DDL ne sert ici que de **placeholder** : ses colonnes
> exactes (au-delà de `codgeo` et `annee`) ne sont pas garanties à l'exécution.
>
> Seules les tables `communes`, `elections`, `population`, `naissances_deces`,
> `catnat` et `risques` conservent un schéma DDL **strict** : leurs colonnes
> sont fixées par le `CREATE TABLE` et alimentées via `INSERT` / `executemany`.

Indexes créés sur :
  • idx_elections_codgeo, idx_elections_annee
  • idx_population_codgeo
  • idx_naissances_deces_codgeo
  • idx_csp_codgeo, idx_secteurs_codgeo
  • idx_comptes_codgeo
  • idx_catnat_codgeo, idx_risques_codgeo
```

---

## Étape 4 : VALIDATION

Une étape de validation est exécutée en fin de pipeline (fonction `validate()`
définie aux lignes 815-865 de `etl_pipeline.py`). Elle effectue trois contrôles
principaux :

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONTRÔLES DE VALIDATION                             │
└─────────────────────────────────────────────────────────────────────────────┘

  1. COMPTAGE PAR TABLE
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  • Itère sur les 12 tables attendues                                    │
  │  • Affiche le nombre de lignes de chacune                               │
  │  • Reporte les éventuelles erreurs d'accès (table manquante)            │
  │  • Synthétise : "Tables présentes : X/12"                               │
  └─────────────────────────────────────────────────────────────────────────┘

  2. ANNÉES D'ÉLECTIONS DISTINCTES
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  SELECT DISTINCT annee FROM elections ORDER BY annee                    │
  │  → Liste les millésimes municipaux présents (ex : 2008, 2014, 2020)     │
  └─────────────────────────────────────────────────────────────────────────┘

  3. COHÉRENCE DES JOINTURES (codgeo orphelins)
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  Vérifie qu'aucun codgeo de la table `elections` n'est absent du        │
  │  référentiel `communes` :                                               │
  │                                                                         │
  │    SELECT COUNT(DISTINCT e.codgeo)                                      │
  │    FROM elections e                                                     │
  │    LEFT JOIN communes c ON e.codgeo = c.codgeo                          │
  │    WHERE c.codgeo IS NULL                                               │
  │                                                                         │
  │  → 0 attendu. Si > 0, alerte affichée dans le log.                      │
  └─────────────────────────────────────────────────────────────────────────┘
```

Cette validation **ne fait pas échouer** le pipeline en cas d'anomalie : elle
se contente d'afficher les incohérences dans la sortie standard. Le contrôle
qualité reste à la charge de l'opérateur.

---

## Schéma ASCII Complet du Pipeline

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     PIPELINE COMPLET                                          │
└──────────────────────────────────────────────────────────────────────────────────────────────┘

                           ┌────────────────────────────┐
                           │   data/input/              │
                           │   (fichiers bruts)         │
                           │   • elections/             │
                           │   • demographie/            │
                           │   • economie/               │
                           │   • education/              │
                           │   • environnement/         │
                           └─────────────┬──────────────┘
                                         │
                                         │ EXTRACTION
                                         │ (pandas, csv, Excel)
                                         ▼
                           ┌────────────────────────────┐
                           │   TRANSFORMATION            │
                           │                            │
                           │ 1. Filtrage dept 34         │
                           │ 2. Normalisation codgeo    │
                           │ 3. Classification G/D      │
                           │ 4. Pivotage temporel       │
                           │ 5. Nettoyage colonnes      │
                           └─────────────┬──────────────┘
                                         │
                                         │ LOAD (SQLite)
                                         ▼
                           ┌────────────────────────────┐
                           │   data/output/             │
                           │   electio_herault.db       │
                           │                            │
                           │  • communes (référentiel)  │
                           │  • elections               │
                           │  • population              │
                           │  • naissances_deces        │
                           │  • revenus                 │
                           │  • csp                     │
                           │  • secteurs_activite       │
                           │  • diplomes                │
                           │  • csp_diplome             │
                           │  • comptes_communes        │
                           │  • catnat                  │
                           │  • risques                 │
                           └────────────────────────────┘
                                         │
                                         │ UTILISATION
                                         ▼
                    ┌────────────────────────────────────────────┐
                    │   PHASES SUIVANTES                         │
                    │                                            │
                    │  Phase 3: Analyse exploratoire (10 graphes) │
                    │  Phase 4: Modèle prédictif (municipales)   │
                    └────────────────────────────────────────────┘
```

---

## Exécution du Pipeline

```bash
# Via le CLI principal
python main.py etl

# Ou directement
python scripts/etl/etl_pipeline.py
```

> **Reconstruction complète à chaque exécution.**
> Le pipeline **supprime systématiquement la base existante** avant de la
> recréer (`os.remove(DB_PATH)` à la ligne 883 de `etl_pipeline.py`). Il n'y a
> **pas de mode incrémental** : chaque appel à `python main.py etl` repart de
> zéro et reconstruit l'intégralité des 12 tables depuis les fichiers sources.
> Toute donnée injectée manuellement dans la base entre deux runs est donc
> perdue.

> **Note technique — pragmas SQLite.**
> La connexion ouvre la base avec deux `PRAGMA` (lignes 888-889) :
> `PRAGMA journal_mode=WAL` (mode Write-Ahead Logging, accélère les écritures
> massives) et `PRAGMA foreign_keys=OFF` (contraintes FK désactivées).
> **Conséquence** : les clauses `FOREIGN KEY (codgeo) REFERENCES communes(codgeo)`
> déclarées dans le DDL ne sont **pas appliquées** par le moteur. Elles ont une
> valeur **documentaire uniquement** ; un `codgeo` invalide dans `elections` ou
> une autre table ne déclenchera pas d'erreur d'insertion. La cohérence
> référentielle est vérifiée *a posteriori* par la fonction `validate()`
> (cf. Étape 4).

### Logs de sortie typiques :

> **Note** : les chiffres ci-dessous (lignes lues, conservées, populations,
> risques, etc.) sont des **valeurs approximatives**, fournies à titre indicatif
> pour illustrer la structure du log. Les comptages réels peuvent varier selon
> la version des fichiers sources.

```
────────────────────────────────────────────────────────────
  PIPELINE ETL — HÉRAULT (34)
────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────
  1/12 — communes (référentiel)
────────────────────────────────────────────────────────────
  ✓ communes : 341 lignes

────────────────────────────────────────────────────────────
  2/12 — elections (municipales, dept 34)
────────────────────────────────────────────────────────────
  Lignes lues : 45,000,000
  Lignes conservées (muni + dept 34) : 125,430
  ✓ elections : 125,430 lignes

────────────────────────────────────────────────────────────
  3/12 — population
────────────────────────────────────────────────────────────
  ✓ population : 18,432 lignes
  ...
────────────────────────────────────────────────────────────
  12/12 — risques
────────────────────────────────────────────────────────────
  ✓ risques : 8,562 lignes
```

---

## Jointures possibles en base

```sql
-- Exemple: Croiser élections + population + revenus
SELECT 
    e.annee,
    e.nom_candidat,
    e.nuance,
    e.voix,
    e.camp,
    p.population,
    r.mediane
FROM elections e
JOIN communes c ON e.codgeo = c.codgeo
JOIN population p ON e.codgeo = p.codgeo AND e.annee = p.annee
JOIN revenus r ON e.codgeo = r.codgeo
WHERE e.annee IN (2008, 2014, 2020)
ORDER BY e.annee, e.voix DESC;
```

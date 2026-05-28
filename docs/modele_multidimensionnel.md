# Modèle multidimensionnel — Electio-Analytics

## Objectif

Documenter le **modèle multidimensionnel** retenu pour l'entrepôt SQLite `data/output/electio_herault.db`, justifier ce choix au regard des trois patrons classiques (étoile, flocon, grappe / constellation) et préciser comment ce modèle est consommé par les phases d'analyse (Phase 3) et de prédiction (Phase 4).

Périmètre : **341 communes** du département de l'Hérault (34), **12 tables** SQLite, **12 features** dénormalisées pour le modèle ML.

---

## 1. Les trois patrons de modélisation

### 1.1 Schéma en étoile (star schema)

Une **unique** table de faits centrale, entourée de plusieurs tables de dimensions **dénormalisées** (tous les attributs d'une dimension dans la même table).

```
            ┌──────────────┐
            │  DIM_TEMPS   │
            └──────┬───────┘
                   │
   ┌────────┐  ┌───▼──────────┐  ┌─────────────┐
   │DIM_GEO │──▶│ FACT_VOTES   │◀─│DIM_NUANCE   │
   └────────┘  │ voix, % voix │  └─────────────┘
               └───┬──────────┘
                   │
              ┌────▼──────────┐
              │ DIM_SCRUTIN   │
              └───────────────┘
```

Atouts : requêtes OLAP simples, agrégations performantes, parfait avec Power BI/Tableau. Limites : redondance dans les dimensions, mal adapté quand plusieurs phénomènes hétérogènes coexistent.

### 1.2 Schéma en flocon (snowflake schema)

Variante normalisée du schéma en étoile : chaque dimension est éclatée en sous-dimensions en cascade.

```
DIM_REGION ─▶ DIM_DEPT ─▶ DIM_COMMUNE ─▶ FACT_VOTES ◀─ DIM_TEMPS
                                              ▲
                            DIM_NUANCE_FAMILLE │
                                    │         │
                              DIM_NUANCE ──────┘
```

Atouts : intégrité référentielle, économie d'espace. Limites : multiplication des jointures, performances dégradées en agrégation.

### 1.3 Schéma en grappe (galaxy / constellation)

**Plusieurs** tables de faits partagent une **dimension maître commune** (ici la commune). Adapté quand plusieurs phénomènes coexistent et doivent rester analysables indépendamment.

```
              ┌──────────────┐
              │  DIM_TEMPS   │
              └──┬────────┬──┘
                 │        │
┌───────────┐  ┌─▼─────┐  ┌─▼─────┐  ┌───────────┐
│DIM_COMMUNE│─▶│ FACT  │  │ FACT  │◀─│DIM_NUANCE │
└───────────┘  │ VOTES │  │ POP   │  └───────────┘
               └───────┘  └───────┘
                  ▲          ▲
              ┌───┴──────────┴───┐
              │  FACT_REVENUS    │
              └──────────────────┘
```

Atouts : flexibilité, ajout simple de nouvelles tables de faits, lecture autonome de chaque thématique. Limites : pas de dimension cubique universelle, optimisation OLAP à faire au cas par cas.

---

## 2. Patron retenu : **modèle en grappe**

### 2.1 Justification fonctionnelle

Le projet consolide **cinq thématiques hétérogènes** (élections, démographie, économie, éducation, environnement) reliées par une **dimension géographique commune** : la commune (`codgeo`). Aucune thématique ne joue le rôle de fait unique :

- les **élections** sont la cible prédictive mais aussi un objet d'analyse autonome ;
- la **démographie**, les **CSP**, les **finances communales** ont chacune leur trajectoire temporelle propre, étudiée pour elle-même dans la Phase 3 ;
- les **arrêtés CatNat** sont des événements discrets sans cardinalité comparable aux autres tables.

Un schéma en **étoile** aurait imposé de choisir arbitrairement une table de faits maîtresse (`FACT_ELECTIONS`) en y aplatissant toutes les autres données comme attributs de `DIM_COMMUNE` : plus de 100 colonnes mélangeant CSP, finances, diplômes et démographie, requêtes alourdies, maintenance plus délicate. Un schéma en **flocon** aggraverait la dispersion des jointures.

Le schéma en **grappe** correspond mieux à la réalité métier : chaque thématique garde sa table de faits propre, toutes rattachées à la dimension maître `communes` par `codgeo`, complétées par une **dimension temporelle implicite** portée par la colonne `annee`.

### 2.2 Le projet n'est pas un cube OLAP

Le besoin n'est pas un cube OLAP classique (mesures additives × hiérarchies). Il est :

- **exploratoire** — produire des corrélations, cartes choroplèthes, distributions (Phase 3, 10 graphiques) ;
- **prédictif** — alimenter un modèle ML structurel (Phase 4, Random Forest sur 12 features).

Pour ces deux usages, le **panel d'apprentissage** est dénormalisé **à la volée** par la fonction `construire_panel()` de `scripts/prediction/modele_predictif.py`. Cette dénormalisation tardive offre la flexibilité de changer le set de features sans toucher au schéma de stockage.

---

## 3. Structure de la grappe Electio-Analytics

### 3.1 Dimension maître

| Table | Rôle | Clé | Volume |
|---|---|---|---|
| `communes` | Référentiel des communes du département 34 | `codgeo` (PK, TEXT 5) | 341 |

### 3.2 Tables de faits à grain temporel

| Table | Clé composite | Grain | Mesures principales |
|---|---|---|---|
| `elections` | (`codgeo`, `annee`, `tour`, `nom_candidat`) | Candidat × tour × année | `voix`, `pct_voix_inscrits`, `pct_voix_exprimes`, `camp` |
| `population` | (`codgeo`, `annee`) | Recensement | `population` |
| `naissances_deces` | (`codgeo`, `annee`) | Annuel 2008–2024 | `naissances`, `deces` |
| `csp` | (`codgeo`, `annee`) | Recensement | colonnes dynamiques (actifs × CSP) |
| `secteurs_activite` | (`codgeo`, `annee`) | Recensement | colonnes dynamiques (actifs × secteur) |
| `csp_diplome` | (`codgeo`, `annee`) | Recensement | colonnes dynamiques (CSP × diplôme) |
| `comptes_communes` | (`codgeo`, `annee`) | Annuel 2000–2022 | `dette`, `dgf`, `caf`, `produits_fonctionnement`, … |

### 3.3 Tables de faits sans dimension temporelle (snapshots)

| Table | Clé | Contenu |
|---|---|---|
| `revenus` | `codgeo` | Médiane, déciles, indicateurs INSEE (colonnes dynamiques) |
| `diplomes` | `codgeo` | Niveaux de diplôme avec préfixes `p11_*`, `p16_*`, `p22_*` (colonnes dynamiques) |

### 3.4 Tables d'événements discrets

| Table | Clé logique | Contenu |
|---|---|---|
| `catnat` | (`codgeo`, dates) | Arrêtés de catastrophe naturelle (1 ligne par arrêté × commune) |
| `risques` | (`codgeo`, `code_risque`) | Inventaire des risques majeurs identifiés |

### 3.5 Schéma de la grappe

```
                                ┌──────────────────┐
                                │     COMMUNES     │  (référentiel maître)
                                │  codgeo  PK      │
                                │  nom             │
                                │  departement=34  │
                                └────────┬─────────┘
                                         │
        ┌──────────────┬─────────────────┼────────────────┬──────────────┐
        │              │                 │                │              │
   ┌────▼─────┐  ┌─────▼──────┐  ┌───────▼────────┐ ┌─────▼──────┐ ┌────▼──────┐
   │ELECTIONS │  │ POPULATION │  │NAISSANCES_DECES│ │  REVENUS   │ │ DIPLOMES  │
   │ codgeo   │  │  codgeo    │  │   codgeo       │ │ codgeo PK  │ │codgeo PK  │
   │ annee    │  │  annee     │  │   annee        │ │ (snapshot) │ │(snapshot) │
   │ tour     │  │  population│  │   naissances   │ └────────────┘ └───────────┘
   │ candidat │  │            │  │   deces        │
   │ nuance   │  └────────────┘  └────────────────┘
   │ voix     │
   │ camp     │       ┌──────────────┐  ┌──────────────────┐  ┌───────────────┐
   └──────────┘       │     CSP      │  │ SECTEURS_ACTIVITE│  │ CSP_DIPLOME   │
                      │   codgeo     │  │     codgeo       │  │   codgeo      │
                      │   annee      │  │     annee        │  │   annee       │
                      │ (dynamique)  │  │   (dynamique)    │  │  (dynamique)  │
                      └──────────────┘  └──────────────────┘  └───────────────┘

        ┌──────────────────┐    ┌──────────────┐    ┌──────────────┐
        │ COMPTES_COMMUNES │    │    CATNAT    │    │   RISQUES    │
        │   codgeo         │    │   codgeo     │    │   codgeo     │
        │   annee          │    │   risque     │    │  libelle_risk│
        │   dette, dgf,    │    │   dates      │    │  code_risque │
        │   caf, …         │    │              │    │              │
        └──────────────────┘    └──────────────┘    └──────────────┘
```

Index physiques (`scripts/etl/etl_pipeline.py`, lignes 244–252) :

```
idx_elections_codgeo, idx_elections_annee
idx_population_codgeo
idx_naissances_deces_codgeo
idx_csp_codgeo, idx_secteurs_codgeo
idx_comptes_codgeo
idx_catnat_codgeo, idx_risques_codgeo
```

Diagramme éditable : [`docs/mcd.drawio`](mcd.drawio).

---

## 4. Granularité, hiérarchies et jointures

### 4.1 Hiérarchies

- **Hiérarchie géographique** : `commune (codgeo)` est le grain le plus fin disponible dans le projet. Une hiérarchie supérieure (intercommunalité, département, région) n'est pas matérialisée — elle s'obtient en sous-chaînant `codgeo` (les 2 premiers caractères = département).
- **Hiérarchie temporelle** : `annee` est l'unique niveau implémenté. Les sous-niveaux (mois, jour) ne sont pas utiles ici, sauf pour les arrêtés CatNat qui conservent leurs dates brutes.

### 4.2 Mapping temporel inter-tables

Les recensements et l'élection municipale n'ont pas le même calendrier. Le **mapping** suivant est appliqué dans `modele_predictif.py` :

| Année élection | RP INSEE retenu (CSP/secteurs) | Préfixe diplômes |
|---|---|---|
| 2008 | 2006 | `p11_` |
| 2014 | 2011 | `p16_` |
| 2020 | 2022 | `p22_` |

Ces correspondances sont stockées dans les constantes `MAPPING_CSP` et `MAPPING_DIPLOMES`.

### 4.3 Patron de jointure type

```sql
-- Croiser élections + finances + population autour d'une année donnée
SELECT
    e.codgeo, c.nom, e.annee, e.camp, e.voix,
    p.population,
    cc.dette / NULLIF(p.population, 0) AS dette_par_hab
FROM elections e
JOIN communes c        ON e.codgeo = c.codgeo
JOIN population p      ON p.codgeo = e.codgeo AND p.annee = e.annee
LEFT JOIN comptes_communes cc
       ON cc.codgeo = e.codgeo AND cc.annee = e.annee
WHERE e.tour = 1 AND e.annee IN (2008, 2014, 2020);
```

---

## 5. Du modèle en grappe au panel ML (dénormalisation tardive)

Le modèle prédictif consomme un **DataFrame Pandas dénormalisé** assemblé à partir des tables de faits ci-dessus. Ce panel sert exclusivement à l'entraînement et la prédiction.

```
            ┌──────────────────────────────────────────┐
            │   Grappe SQLite (12 tables, source       │
            │   de vérité, normalisée)                 │
            └────────────────────┬─────────────────────┘
                                 │ construire_panel()
                                 ▼
            ┌──────────────────────────────────────────┐
            │  Panel dénormalisé Pandas                │
            │  Grain : (codgeo, annee)                 │
            │  Colonnes : 12 features + 2 cibles       │
            │            (pct_gauche, camp_label)      │
            └──────────────────────────────────────────┘
                                 │
                                 ▼
                Random Forest (Classifier + Regressor)
```

### 5.1 Cibles dérivées

| Cible | Type | Définition |
|---|---|---|
| `pct_gauche` | continue | 100 × voix Gauche / (voix Gauche + voix Droite) au tour 1 |
| `camp_label` | binaire (0/1) | 1 si `pct_gauche > 50` |

### 5.2 Les 12 features

Définies dans la constante `FEATURES` de `modele_predictif.py` (lignes 69–74) :

`population, pct_cadres, pct_ouvriers, pct_employes, pct_prof_intermediaires, revenu_median, pct_diplome_sup, pct_sans_diplome, dette_par_hab, invest_par_hab, taux_natalite, nb_catnat`.

### 5.3 Volumétrie du panel

| Niveau | Volume théorique | Volume après `dropna` |
|---|---|---|
| (commune × élection) | 341 × 3 = 1 023 | ~690 (logs ; principal trou : revenu médian) |

---

## 6. Pourquoi pas un schéma en étoile, même au final ?

| Critère | Étoile | Flocon | **Grappe (retenu)** |
|---|---|---|---|
| Nombre de tables de faits | 1 | 1 | Plusieurs |
| Adapté à un phénomène unique | ✓ | ✓ | △ |
| Adapté à plusieurs phénomènes hétérogènes | ✗ | ✗ | **✓** |
| Performance OLAP brute | ✓✓ | ✓ | △ |
| Lisibilité du schéma | ✓ | ✗ | ✓ |
| Évolutivité (ajout d'un domaine) | △ | △ | **✓✓** |
| Compatibilité ML / dénormalisation tardive | △ | ✗ | **✓** |
| Choix pour Electio-Analytics | ✗ | ✗ | **✓** |

---

## 7. Évolutions envisageables en cas d'industrialisation

1. **Étoile en surcouche**. Conserver la grappe comme ODS (Operational Data Store) et matérialiser un schéma en étoile au-dessus pour les usages OLAP (Power BI). `FACT_ELECTIONS` agrège alors les 12 features comme colonnes ; `DIM_COMMUNE`, `DIM_TEMPS`, `DIM_NUANCE` sont les dimensions.
2. **Flocon hiérarchique géographique**. Si l'analyse passe à plusieurs échelles (commune → EPCI → département → région), normaliser la dimension géographique en cascade.
3. **Migration SQLite → PostgreSQL** sans changer le schéma logique : le DDL actuel est compatible (les types `TEXT`, `INTEGER`, `REAL` se mappent directement).

---

## 8. Pointeurs

- [`docs/referentiel_donnees.md`](referentiel_donnees.md) — dictionnaire complet des 12 tables et des 12 datasets.
- [`docs/PIPELINE_ETL.md`](PIPELINE_ETL.md) — transformations qui alimentent chaque table de la grappe.
- [`docs/mcd.drawio`](mcd.drawio) — diagramme éditable (diagrams.net).
- `scripts/etl/etl_pipeline.py` — DDL et chargement.
- `scripts/prediction/modele_predictif.py` — fonction `construire_panel()` : dénormalisation pour le ML.

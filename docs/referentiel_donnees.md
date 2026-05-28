# Référentiel de données — Electio-Analytics

## Objectif

Ce document tient lieu de **dictionnaire des données** du projet. Pour chacun des douze jeux de données externes ingérés et pour chacune des douze tables SQLite produites, il décrit la source, la fréquence de mise à jour, la granularité, les colonnes principales et la clé de jointure. Il documente également les référentiels métier qui pilotent la classification politique (`GAUCHE_NUANCES` / `DROITE_NUANCES`).

Périmètre : **341 communes** du département de l'Hérault (34). Identifiant pivot : le code INSEE de la commune, stocké systématiquement en chaîne de **5 caractères** (colonne `codgeo`, parfois nommée `code_insee` dans les sources brutes).

---

## 1. Critères de sélection des jeux de données

Un dataset n'est retenu dans le pipeline que s'il satisfait l'**ensemble** des critères ci-dessous.

| Critère | Description |
|---|---|
| **Pertinence métier** | Hypothèse explicite d'effet sur le vote (sociologie politique, économie locale, démographie, exposition aux risques). |
| **Disponibilité** | Téléchargement libre sur `data.gouv.fr`, `insee.fr` ou `data.economie.gouv.fr`, sans inscription ni paiement. |
| **Licence** | Licence Ouverte Etalab 2.0 ou équivalente (réutilisation autorisée, y compris commerciale, sous condition de citation). |
| **Granularité** | Donnée publiée à l'échelle de la **commune** (le département ou la région ne suffisent pas). |
| **Identifiant commun** | Possibilité de reconstituer un code INSEE 5 caractères pour la jointure. |
| **Couverture temporelle** | Données disponibles sur au moins l'un des trois millésimes municipaux ciblés (2008, 2014, 2020). |
| **Format exploitable** | CSV, XLSX ou TXT à séparateur ; les PDF et images sont exclus. |

Les datasets évalués mais écartés sont listés au §4.

---

## 2. Dictionnaire des sources externes (12 datasets)

Chaque entrée renvoie à `SOURCES_DONNEES.md` (URL canonique) et au `scripts/etl/etl_pipeline.py` (fonction `etl_*` correspondante).

### Thématique « Élections »

#### 2.1 Résultats électoraux par bureau de vote

| Attribut | Valeur |
|---|---|
| Fichier | `data/input/elections/candidats_results.txt` (~2,3 GB) |
| Source | data.gouv.fr — Ministère de l'Intérieur |
| Couverture | Toutes élections nationales, 1999–2024 |
| Granularité | Bureau de vote → agrégé commune par l'ETL |
| Lecture | `csv.reader` ligne à ligne, encodage UTF-8, séparateur `;` |
| Filtre ETL | `id_election` contient `_muni_` **et** `Code du département == '34'` |
| Clé de jointure | `Code du département` + `Code de la commune` → `codgeo` |
| Justification | Variable cible (camp Gauche/Droite, % Gauche) |

#### Thématique « Démographie »

#### 2.2 Population historique 1876–2023

| Attribut | Valeur |
|---|---|
| Fichier | `data/input/demographie/base-pop-historiques-1876-2023.xlsx` (~6,7 MB) |
| Source | INSEE |
| Couverture | 39 recensements 1876–2023 |
| Onglet | `pop_1876_2023` ; header en ligne 5 |
| Granularité | Commune |
| Clé de jointure | `CODGEO` (5 caractères) |
| Justification | Tendance démographique (extrapolation 2026), pondération « par habitant » |

#### 2.3 Naissances par commune 2008–2024

| Attribut | Valeur |
|---|---|
| Fichier | `data/input/demographie/DS_ETAT_CIVIL_NAIS_COMMUNES_data.csv` (~24,4 MB) |
| Source | INSEE — bulletins d'état civil |
| Filtre ETL | `GEO_OBJECT == 'COM'`, `GEO` commence par `34` |
| Clé de jointure | `GEO` → `codgeo` |
| Justification | Taux de natalité = composante de la dynamique démographique |

#### 2.4 Décès par commune 2008–2024

| Attribut | Valeur |
|---|---|
| Fichier | `data/input/demographie/DS_ETAT_CIVIL_DECES_COMMUNES_data.csv` (~24,4 MB) |
| Source | INSEE — bulletins d'état civil |
| Filtre ETL | identique au 2.3 |
| Clé de jointure | `GEO` → `codgeo` |
| Justification | Solde naturel, vitalité démographique |

### Thématique « Économie »

#### 2.5 Revenus des Français par commune

| Attribut | Valeur |
|---|---|
| Fichier | `data/input/economie/revenu-des-francais-a-la-commune-*.csv` (~4,8 MB) |
| Source | data.gouv.fr |
| Couverture | Snapshot le plus récent ; quartiles, déciles, médiane disponibles |
| Clé de jointure | `Code géographique` → `codgeo` (zfill 5) |
| Justification | Niveau de vie : hypothèse classique d'effet sur le vote |

#### 2.6 CSP des actifs 25–54 ans (1968–2022)

| Attribut | Valeur |
|---|---|
| Fichier | `data/input/economie/pop-act2554-csp-cd-6822.xlsx` (~28,5 MB) |
| Source | INSEE |
| Couverture | 9 recensements : 1968, 1975, 1982, 1990, 1999, 2006, 2011, 2016, 2022 |
| Onglets | `COM_<annee>` ; header en ligne 14, ligne 0 = codes internes à sauter |
| Reconstruction codgeo | `Département (géographie courante).zfill(2)` + `Commune (géographie courante).zfill(3)` |
| Justification | Structure de classes (effet sociologique) |

#### 2.7 Secteurs d'activité des actifs 25–54 ans

| Attribut | Valeur |
|---|---|
| Fichier | `data/input/economie/pop-act2554-empl-sa-sexe-cd-6822.xlsx` (~23,5 MB) |
| Source | INSEE |
| Couverture | Même calendrier que 2.6 |
| Structure | Mêmes onglets `COM_<annee>` |
| Justification | Répartition agriculture/industrie/BTP/tertiaire |

#### 2.8 Comptes individuels des communes (DGFiP)

| Attribut | Valeur |
|---|---|
| Fichiers | `data/input/economie/comptes_communes_*.csv` (4 fichiers, ~650 MB cumulés) |
| Source | DGFiP via `data.economie.gouv.fr` |
| Couverture | 2000–2022 (annuel) |
| Reconstruction codgeo | `dep.lstrip('0')` + `icom.zfill(3)` |
| Colonnes conservées | `an, pop, prod, charge, perso, depinv, equip, dette, dgf, caf, impo1, impo2` (renommées en clair par l'ETL) |
| Justification | Santé financière communale, politique d'investissement |

### Thématique « Éducation »

#### 2.9 Diplômes et formation (recensement 2022)

| Attribut | Valeur |
|---|---|
| Fichier | `data/input/education/base-cc-diplomes-formation-2022.CSV` (~81 MB) |
| Source | INSEE |
| Couverture | Snapshot RP 2022 ; colonnes préfixées `p11_`, `p16_`, `p22_` pour les recensements de 2011, 2016, 2022 |
| Clé de jointure | `CODGEO` |
| Justification | Niveau de diplôme = prédicteur sociologique robuste |

#### 2.10 CSP × diplôme

| Attribut | Valeur |
|---|---|
| Fichier | `data/input/education/pop-act2554-csp-dipl-cd-6822.xlsx` (~51,9 MB) |
| Source | INSEE |
| Couverture | 1968–2022 (mêmes années que 2.6) |
| Structure | Onglets `COM_<annee>` |
| Justification | Croisement éducation × position sociale |

### Thématique « Environnement »

#### 2.11 Arrêtés de catastrophe naturelle — GASPAR

| Attribut | Valeur |
|---|---|
| Fichier | `data/input/environnement/catnat_gaspar.csv` (~34,5 MB, 260 799 lignes) |
| Source | data.gouv.fr — base GASPAR |
| Couverture | 1985 → 2022+ |
| Clé de jointure | `cod_commune` (chaîne avec zéros) |
| Colonnes conservées | `lib_risque_jo, dat_deb, dat_fin, dat_pub_arrete` |
| Justification | Exposition vécue aux aléas (inondations, sécheresse, littoral) |

#### 2.12 Inventaire des risques — GASPAR

| Attribut | Valeur |
|---|---|
| Fichier | `data/input/environnement/risq_gaspar.csv` (~8,4 MB, 172 595 lignes) |
| Source | data.gouv.fr — base GASPAR |
| Couverture | Inventaire courant |
| Clé de jointure | `cod_commune` → `codgeo` (zfill 5) |
| Colonnes conservées | `lib_risque, num_risque` |
| Justification | Complète CatNat par le catalogue des risques identifiés |

---

## 3. Dictionnaire des tables SQLite (12 tables)

Toutes les tables sont stockées dans `data/output/electio_herault.db`. La clé de jointure transverse est `codgeo` (TEXT, 5 caractères). Le détail de la DDL est dans `scripts/etl/etl_pipeline.py`, constante `DDL` (lignes 147–253).

### 3.1 `communes` — référentiel maître

| Colonne | Type | Description |
|---|---|---|
| `codgeo` | TEXT, PK | Code INSEE de la commune (5 caractères) |
| `nom` | TEXT | Libellé de la commune (colonne `LIBGEO` de l'INSEE) |
| `departement` | TEXT | Constante `'34'` |

Volume attendu : **341 lignes**. Construit depuis l'onglet `pop_1876_2023` du fichier population historique.

### 3.2 `elections` — table de faits principale

| Colonne | Type | Description |
|---|---|---|
| `codgeo` | TEXT, FK → communes | Code INSEE |
| `annee` | INTEGER | Année du scrutin (2008, 2014, 2020 retenues à l'usage) |
| `tour` | INTEGER | Tour de scrutin (1 ou 2) |
| `nom_candidat` | TEXT | Nom de la tête de liste |
| `prenom_candidat` | TEXT | Prénom |
| `nuance` | TEXT | Code nuance officiel ministère Intérieur |
| `voix` | INTEGER | Nombre de voix obtenues |
| `pct_voix_inscrits` | REAL | % voix / inscrits |
| `pct_voix_exprimes` | REAL | % voix / exprimés |
| `camp` | TEXT | `'Gauche'` ou `'Droite'` (cf. §5) |

Index : `idx_elections_codgeo`, `idx_elections_annee`.

### 3.3 `population`

| Colonne | Type | Description |
|---|---|---|
| `codgeo` | TEXT, FK | |
| `annee` | INTEGER | Année du recensement (colonnes `PMUNxxxx`, `PSDCxxxx`, `PTOTxxxx` dépivotées) |
| `population` | INTEGER | Population municipale |

Volume attendu : ~12 000 lignes (341 communes × ~37 millésimes utiles).

### 3.4 `naissances_deces`

| Colonne | Type | Description |
|---|---|---|
| `codgeo` | TEXT, FK | |
| `annee` | INTEGER | 2008–2024 |
| `naissances` | INTEGER | |
| `deces` | INTEGER | |

### 3.5 `revenus` — schéma dynamique

Table créée via `df.to_sql(..., if_exists='replace')` : le DDL placeholder du DDL ne fixe que `codgeo`. Les colonnes effectives sont dérivées du CSV source (médiane, déciles, indicateurs INSEE) après normalisation des en-têtes en minuscules / underscores. Une seule ligne par commune (snapshot).

### 3.6 `csp` — schéma dynamique

Table empilée millésime par millésime (colonne `annee` ajoutée par l'ETL). Colonnes nombreuses (population active 25–54 ans × CSP × situation d'emploi). Les requêtes type recherchent les colonnes `*actifs_ayant_un_emploi*rp<annee>*`.

### 3.7 `secteurs_activite` — schéma dynamique

Même structure que `csp` ; ventilation par secteur (agriculture, industrie, construction, tertiaire) × sexe.

### 3.8 `diplomes` — schéma dynamique

Snapshot recensement 2022. Colonnes préfixées :
- `p11_*` pour les colonnes issues du RP 2011 (réinjecté rétroactivement),
- `p16_*` pour le RP 2016,
- `p22_*` pour le RP 2022.

Colonnes clés exploitées par les phases 3 et 4 :
- `pXX_nscol15p` : population non scolarisée 15+ (dénominateur),
- `pXX_nscol15p_diplmin` / `pXX_nscol15p_dipl0` : sans diplôme,
- `pXX_nscol15p_sup`, `pXX_nscol15p_sup2`, `pXX_nscol15p_sup34`, `pXX_nscol15p_sup5` : diplôme supérieur.

### 3.9 `csp_diplome` — schéma dynamique

Croisement CSP × niveau de diplôme empilé par millésime.

### 3.10 `comptes_communes`

Schéma DDL strict (colonnes renommées par l'ETL) :

| Colonne | Type | Description |
|---|---|---|
| `codgeo` | TEXT, FK | |
| `annee` | INTEGER | 2000–2022 |
| `population` | INTEGER | Population de référence DGFiP |
| `produits_fonctionnement` | REAL | |
| `charges_fonctionnement` | REAL | |
| `depenses_personnel` | REAL | |
| `depenses_investissement` | REAL | |
| `depenses_equipement` | REAL | |
| `dette` | REAL | Encours de dette en fin d'exercice |
| `dgf` | REAL | Dotation globale de fonctionnement |
| `capacite_autofinancement` | REAL | |
| `impots_directs` | REAL | |
| `impots_indirects` | REAL | |

### 3.11 `catnat`

| Colonne | Type | Description |
|---|---|---|
| `codgeo` | TEXT, FK | |
| `risque` | TEXT | Libellé JO du risque |
| `date_debut` | TEXT | Début de l'événement |
| `date_fin` | TEXT | Fin de l'événement |
| `date_arrete` | TEXT | Date de publication de l'arrêté |

Une ligne par arrêté × commune.

### 3.12 `risques`

| Colonne | Type | Description |
|---|---|---|
| `codgeo` | TEXT, FK | |
| `libelle_risque` | TEXT | Type de risque (inondation, séisme, …) |
| `code_risque` | TEXT | Code numérique GASPAR |

---

## 4. Datasets évalués puis écartés

| Dataset | Raison d'exclusion |
|---|---|
| `catnat_gaspar.xlsx` | Doublon du CSV GASPAR, moins complet |
| GASPAR `dicrim, tim, pprm, pprt, pprn, azi` | Données réglementaires sans valeur prédictive |
| Baromètre du numérique | Pas de code INSEE commune exploitable |
| Population de référence INSEE | Doublon de `base-pop-historiques-1876-2023.xlsx` |
| Statistiques de délinquance | Seuil de publication ~5 000 habitants : exclurait ~80 % des communes du 34 |
| Répertoire National des Associations | Non disponible à l'échelle commune avec activité réelle |

---

## 5. Référentiels métier : classification politique

La fonction `classify_camp()` (`scripts/etl/etl_pipeline.py`, lignes 83–105) classe chaque liste en **Gauche** ou **Droite**. La même logique est dupliquée dans `scripts/prediction/modele_predictif.py` ; les deux fichiers doivent rester synchronisés.

### 5.1 Codes nuance

- `GAUCHE_NUANCES` (64 codes) : extrême gauche (`EXG, LO, LCR, …`), communistes (`COM, LCOM, HUE`), France Insoumise (`FI, LFI, NUP, MELE, …`), socialistes (`SOC, LSOC, HOLL, JOSP, ROYA`), écologistes (`VEC, ECO, LVE, JOLY, BOVE, …`), divers gauche / union gauche (`DVG, UG, LUGE, RDG, PRG, …`), candidats nominatifs historiques (`ARTH, POUT, BUFF, GLUC, TAUB, …`) et binômes communaux préfixés `BC-` (`BC-SOC, BC-COM, BC-FG, …`).
- `DROITE_NUANCES` (101 codes) : extrême droite (`EXD, FN, RN, MNR, LEPA, …`), Les Républicains / UMP (`UMP, LR, RPR, DVD, …`), centre / UDI / MoDem (`UDF, UDI, CEN, BAYR, MDM, …`), Renaissance / Ensemble (`REM, LREM, ENS, HOR, …`), souverainistes (`MPF, DLF, DUPO, …`), Reconquête (`REC, LREC`), divers droite et binômes communaux (`DVC, LDD, NC, REG, MNA, BC-LR, BC-RN, …`).

Listes exhaustives : `scripts/etl/etl_pipeline.py` lignes 52–80.

### 5.2 Repli par mots-clés

Si la nuance est absente ou inconnue, le libellé de liste est scanné :
- **Gauche** : `socialiste`, `communiste`, `gauche`, `écologi`, `vert`, `insoumis`, `ouvrier`, `citoyen`, `solidaire`.
- **Droite** : `national`, `républicain`, `droite`, `marche`, `renaissance`, `ensemble`, `majorité`, `libéral`, `conservat`.

### 5.3 Valeur par défaut

Si **aucune nuance ni mot-clé** ne matche, le camp retenu est **`'Droite'`** (cf. ligne 105 d'`etl_pipeline.py`). Ce choix favorise mécaniquement la classe Droite sur les listes « sans étiquette » ou divers ; il doit être gardé en tête pour l'interprétation des résultats. Il n'existe **pas** de catégorie `'Autre'` dans la table `elections`.

---

## 6. Conventions transverses

| Convention | Règle |
|---|---|
| Code INSEE | Toujours `TEXT`, longueur 5, zéros initiaux préservés (`'34001'`, pas `34001`). |
| Année | `INTEGER`. Pour les indicateurs publiés en colonnes (`PMUN2014`, `p22_*`), l'ETL dépivote en lignes. |
| Mapping temporel | Année élection → millésime indicateur le plus proche : `2008 → RP 2006 / p11`, `2014 → RP 2011 / p16`, `2020 → RP 2022 / p22`. Défini dans `MAPPING_CSP` et `MAPPING_DIPLOMES` (`modele_predictif.py`). |
| Valeurs manquantes | Conservées en `NULL` ; le panel ML applique `dropna(how='any')` sur les 12 features. |
| Tables à schéma dynamique | `revenus`, `csp`, `secteurs_activite`, `diplomes`, `csp_diplome` (et `comptes_communes` après remplacement) : la liste exacte des colonnes dépend du fichier source à l'exécution. |

---

## 7. Pointeurs

- `SOURCES_DONNEES.md` — URL canonique et notes de téléchargement des 12 datasets.
- `docs/PIPELINE_ETL.md` — détail des transformations par table.
- `docs/modele_multidimensionnel.md` — positionnement des 12 tables dans le schéma en grappe.
- `docs/mcd.drawio` — diagramme éditable du MCD.
- `scripts/etl/etl_pipeline.py` — DDL, classification, ETL par table.

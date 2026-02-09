# Sources des données

Ce fichier liste les liens pour télécharger les données utilisées dans ce projet.

## Elections (`data/input/elections/`)

### Résultats électoraux par bureau de vote
- **Lien** : https://www.data.gouv.fr/datasets/donnees-des-elections-agregees
- **Fichier** : `candidats_results.txt` (2.1 GB)
- **Description** : Résultats de toutes les élections (présidentielles, législatives, européennes, régionales, départementales, municipales) de 1999 à 2024
- **Clé de jointure** : `Code du département` + `Code de la commune`

## Economie (`data/input/economie/`)

### Revenus des Français par commune
- **Lien** : https://www.data.gouv.fr/datasets/revenu-des-francais-a-la-commune
- **Fichier** : `revenu-des-francais-a-la-commune-*.csv` (4.8 MB)
- **Description** : Revenus médians, quartiles, déciles par commune
- **Clé de jointure** : `Code géographique` (code INSEE commune)

### CSP des actifs 25-54 ans par commune (1968-2022)
- **Lien** : https://www.insee.fr/fr/information/2837787
- **Fichier** : `pop-act2554-csp-cd-6822.xlsx` (28.5 MB)
- **Description** : Population active 25-54 ans par CSP (Agriculteurs, Artisans, Cadres, Prof. intermédiaires, Employés, Ouvriers) × statut (Emploi/Chômeurs). Onglets `COM_xxxx` pour les données communales. Header en ligne 12-14 (métadonnées INSEE à sauter).
- **Années** : 1968, 1975, 1982, 1990, 1999, 2006, 2011, 2016, 2022
- **Clé de jointure** : `Commune en géographie courante` (code INSEE commune)

### Comptes individuels des communes (2000-2022)
- **Lien** : https://data.economie.gouv.fr/explore/?q=comptes+individuels+des+communes
- **Fichiers** :
  - `comptes_communes_2000_2008.csv` (344 MB) — années 2000 à 2008
  - `comptes_communes_2011_2015.csv` (214 MB) — années 2011 à 2015
  - `comptes_communes_2017.csv` (44 MB) — année 2017
  - `comptes_communes_2022.csv` (50 MB) — année 2022
- **Description** : Comptes de fonctionnement et d'investissement de chaque commune : recettes, dépenses, personnel, dette, dotation globale de fonctionnement (DGF), fiscalité locale, capacité d'autofinancement. ~253 colonnes par fichier.
- **Années** : 2000 à 2022 (couvre les présidentielles 2002, 2007, 2012, 2017, 2022)
- **Clé de jointure** : `dep` + `icom` → reconstituer le code INSEE commune à 5 chiffres

### Secteur d'activité des actifs 25-54 ans par commune (1968-2022)
- **Lien** : https://www.insee.fr/fr/information/2837787
- **Fichier** : `pop-act2554-empl-sa-sexe-cd-6822.xlsx` (23.5 MB)
- **Description** : Actifs 25-54 ans par secteur d'activité (Agriculture, Industrie, Construction, Tertiaire) × sexe (H/F). Onglets `COM_xxxx`.
- **Années** : 1968, 1975, 1982, 1990, 1999, 2006, 2011, 2016, 2022
- **Clé de jointure** : `Commune en géographie courante` (code INSEE commune)

## Education (`data/input/education/`)

### Diplômes et Formation (2022)
- **Lien** : https://www.insee.fr/fr/statistiques/8581488
- **Fichiers** :
  - `base-cc-diplomes-formation-2022.CSV` (81 MB)
  - `base-cc-diplomes-formation-2022-COM.CSV`
  - `meta_base-cc-diplomes-formation-2022.CSV`
- **Description** : Données sur les diplômes et la formation par commune (recensement 2022)
- **Clé de jointure** : `CODGEO` (code INSEE commune)

### CSP × Diplôme des actifs 25-54 ans par commune (1968-2022)
- **Lien** : https://www.insee.fr/fr/information/2837787
- **Fichier** : `pop-act2554-csp-dipl-cd-6822.xlsx` (51.9 MB)
- **Description** : Croisement CSP × niveau de diplôme (6 CSP × 6 niveaux = 36 colonnes). Onglets `COM_xxxx`.
- **Années** : 1968, 1975, 1982, 1990, 1999, 2006, 2011, 2022
- **Clé de jointure** : `Commune en géographie courante` (code INSEE commune)

## Démographie (`data/input/demographie/`)

### Population historique par commune (1876-2023)
- **Lien** : https://www.data.gouv.fr/datasets/bases-de-donnees-et-fichiers-details-du-recensement-de-la-population
- **Fichier** : `base-pop-historiques-1876-2023.xlsx` (6.7 MB)
- **Description** : Population municipale de chaque commune de 1876 à 2023 (39 recensements). Onglet principal : `pop_1876_2023`. Attention : 3 lignes de métadonnées à sauter (`skiprows=5`, header en ligne 4 avec codes `CODGEO`, `REG`, `DEP`, `LIBGEO`, `PMUN2023`…)
- **Clé de jointure** : `CODGEO` (code INSEE commune)

### Naissances par commune (2008-2024)
- **Lien** : https://www.insee.fr/fr/statistiques/1893255
- **Fichiers** :
  - `DS_ETAT_CIVIL_NAIS_COMMUNES_data.csv` (24.4 MB)
  - `DS_ETAT_CIVIL_NAIS_COMMUNES_metadata.csv` (1.8 MB)
- **Description** : Nombre de naissances vivantes par commune et par année (bulletins d'état civil)
- **Années** : 2008 à 2024 (annuel)
- **Clé de jointure** : `GEO` (code INSEE commune) — filtrer sur `GEO_OBJECT = 'COM'`

### Décès par commune (2008-2024)
- **Lien** : https://www.insee.fr/fr/statistiques/1893253
- **Fichiers** :
  - `DS_ETAT_CIVIL_DECES_COMMUNES_data.csv` (24.4 MB)
  - `DS_ETAT_CIVIL_DECES_COMMUNES_metadata.csv` (1.8 MB)
- **Description** : Nombre de décès domiciliés par commune et par année (bulletins d'état civil)
- **Années** : 2008 à 2024 (annuel)
- **Clé de jointure** : `GEO` (code INSEE commune) — filtrer sur `GEO_OBJECT = 'COM'`

## Environnement (`data/input/environnement/`)

### Arrêtés de catastrophe naturelle — GASPAR CatNat (1985-2022+)
- **Lien** : https://www.data.gouv.fr/fr/datasets/base-nationale-de-gestion-assistee-des-procedures-administratives-relatives-aux-risques-gaspar/
- **Fichier** : `catnat_gaspar.csv` (34.5 MB)
- **Description** : Arrêtés de catastrophe naturelle par commune (inondations, mouvements de terrain, sécheresse, tempêtes…). Contient le type de risque, dates début/fin de l'événement, date de l'arrêté, date de publication au JO.
- **Lignes** : 260 799
- **Années** : 1985 à 2022+
- **Clé de jointure** : `cod_commune` (code INSEE commune, format texte avec zéros)

### Risques connus par commune — GASPAR
- **Lien** : https://www.data.gouv.fr/fr/datasets/base-nationale-de-gestion-assistee-des-procedures-administratives-relatives-aux-risques-gaspar/
- **Fichier** : `risq_gaspar.csv` (8.4 MB)
- **Description** : Inventaire des risques identifiés par commune (inondation, séisme, mouvement de terrain, transport de marchandises dangereuses, rupture de barrage…)
- **Lignes** : 172 595
- **Clé de jointure** : `cod_commune` (code INSEE commune, format entier)

---

## Notes

- Les fichiers sont organisés par thématique dans `data/input/<thématique>/`
- Les nouveaux fichiers peuvent être déposés dans `data/input/nouveau/` pour analyse exploratoire avant classement
- Les fichiers exclus (doublons, hors scope) sont dans `data/input/exclus/` : XLSX CatNat incomplet (doublon du CSV GASPAR), fichiers GASPAR administratifs (dicrim, tim, pprm, pprt, pprn, azi), baromètre du numérique (pas de CODGEO), population de référence (doublon)
- Les fichiers volumineux ne sont pas versionnés (voir `.gitignore`)

# Sources des données

Ce fichier liste les liens pour télécharger les données utilisées dans ce projet.

## Données INSEE

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

## Numérique (`data/input/numerique/`)

*À venir (ex: taux d'installation de fibre)*

## Environnement (`data/input/environnement/`)

*À venir (ex: taux de pollution)*

---

## Notes

- Les fichiers sont organisés par thématique dans `data/input/<thématique>/`
- Les nouveaux fichiers peuvent être déposés dans `data/input/nouveau/` pour analyse exploratoire avant classement
- Les fichiers exclus (doublons) sont dans `data/input/exclus/` avec un README explicatif
- Les fichiers volumineux ne sont pas versionnés (voir `.gitignore`)

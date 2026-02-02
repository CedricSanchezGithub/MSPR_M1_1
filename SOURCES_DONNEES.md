# Sources des données

Ce fichier liste les liens pour télécharger les données utilisées dans ce projet.

## Données INSEE

### Diplômes et Formation (2022)
- **Lien** : https://www.insee.fr/fr/statistiques/8581488
- **Fichiers** :
  - `base-cc-diplomes-formation-2022.CSV` (81 MB)
  - `base-cc-diplomes-formation-2022-COM.CSV`
  - `meta_base-cc-diplomes-formation-2022.CSV`
- **Description** : Données sur les diplômes et la formation par commune (recensement 2022)
- **Clé de jointure** : `CODGEO` (code INSEE commune)

### Revenus des Français par commune
- **Lien** : https://www.data.gouv.fr/datasets/revenu-des-francais-a-la-commune
- **Fichier** : `revenu-des-francais-a-la-commune-*.csv` (4.8 MB)
- **Description** : Revenus médians, quartiles, déciles par commune
- **Clé de jointure** : `Code géographique` (code INSEE commune)

## Données électorales

### Résultats électoraux par bureau de vote
- **Lien** : https://www.data.gouv.fr/datasets/donnees-des-elections-agregees
- **Fichier** : `candidats_results.txt` (2.1 GB)
- **Description** : Résultats de toutes les élections (présidentielles, législatives, européennes, régionales, départementales, municipales) de 1999 à 2024
- **Clé de jointure** : `Code du département` + `Code de la commune`

---

## Notes

- Tous les fichiers doivent être placés dans `data/input/`
- Les nouveaux fichiers peuvent être déposés dans `data/input/nouveau/` pour analyse
- Les fichiers volumineux ne sont pas versionnés (voir `.gitignore`)

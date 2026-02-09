# DS_ETAT_CIVIL_DECES_COMMUNES_data.csv

**Source** : [INSEE - Décès de 2008 à 2024](https://www.insee.fr/fr/statistiques/1893253)

**Taille** : 24.4 MB | **Format** : CSV (séparateur `;`)

## Contenu

Nombre de décès domiciliés (DTH) par commune et par année, issus des bulletins d'état civil.

## Colonnes

`EC_MEASURE`, `FREQ`, `GEO`, `GEO_OBJECT`, `OBS_STATUS`, `TIME_PERIOD`, `OBS_VALUE`

- `GEO` : code INSEE commune
- `GEO_OBJECT` : niveau géographique (COM, ARR, REG, AAV2020, BV2022, ARM, FRANCE)
- `TIME_PERIOD` : année (2008-2024)
- `OBS_VALUE` : nombre de décès
- `OBS_STATUS` : A (normale) ou M (valeur manquante)

## Années

2008 à 2024 (17 ans, fréquence annuelle)

## Clé de jointure

`GEO` (code INSEE commune) — filtrer sur `GEO_OBJECT = 'COM'`

## Fichier associé

- `DS_ETAT_CIVIL_DECES_COMMUNES_metadata.csv` : dictionnaire des variables (1.8 MB)

## Notes techniques

- Certaines petites communes d'outre-mer ont des valeurs manquantes (`OBS_STATUS = 'M'`, `OBS_VALUE` vide)
- Le fichier contient aussi des agrégats (région, arrondissement, France) : filtrer sur `GEO_OBJECT = 'COM'` pour les communes

# DS_ETAT_CIVIL_NAIS_COMMUNES_data.csv

**Source** : [INSEE - Naissances de 2008 à 2024](https://www.insee.fr/fr/statistiques/1893255)

**Taille** : 24.4 MB | **Format** : CSV (séparateur `;`)

## Contenu

Nombre de naissances vivantes (LVB) par commune et par année, issues des bulletins d'état civil.

## Colonnes

`EC_MEASURE`, `FREQ`, `GEO`, `GEO_OBJECT`, `OBS_STATUS`, `TIME_PERIOD`, `OBS_VALUE`

- `GEO` : code INSEE commune
- `GEO_OBJECT` : niveau géographique (COM = commune)
- `TIME_PERIOD` : année (2008-2024)
- `OBS_VALUE` : nombre de naissances

## Années

2008 à 2024 (17 ans, fréquence annuelle)

## Clé de jointure

`GEO` (code INSEE commune) — filtrer sur `GEO_OBJECT = 'COM'`

## Fichier associé

- `DS_ETAT_CIVIL_NAIS_COMMUNES_metadata.csv` : dictionnaire des variables (1.8 MB)

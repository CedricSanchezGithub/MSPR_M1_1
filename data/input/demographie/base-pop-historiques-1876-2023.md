# base-pop-historiques-1876-2023.xlsx

**Source** : [data.gouv.fr - Bases de données du recensement de la population](https://www.data.gouv.fr/datasets/bases-de-donnees-et-fichiers-details-du-recensement-de-la-population)

**Taille** : 6.7 MB | **Format** : XLSX (3 onglets)

## Contenu

Population municipale de chaque commune française de **1876 à 2023** (39 recensements).

## Onglets

- `pop_1876_2023` : données principales (~34 883 communes, 41 colonnes)
- `Variables` : dictionnaire des variables
- `Documentation` : notes méthodologiques

## Colonnes principales

`CODGEO`, `REG`, `DEP`, `LIBGEO`, `PMUN2023`, `PMUN2022`, ..., `PTOT1876`

## Clé de jointure

`CODGEO` (code INSEE commune)

## Notes techniques

- 3 lignes de métadonnées en en-tête, header réel en ligne 4
- Utiliser `pd.read_excel(file, sheet_name='pop_1876_2023', header=4)`

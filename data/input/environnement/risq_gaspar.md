# risq_gaspar.csv

**Source** : [data.gouv.fr - Base GASPAR](https://www.data.gouv.fr/fr/datasets/base-nationale-de-gestion-assistee-des-procedures-administratives-relatives-aux-risques-gaspar/)

**Taille** : 8.4 MB | **Format** : CSV (séparateur `;`)

## Contenu

Inventaire des risques identifiés par commune : inondation, séisme, mouvement de terrain, transport de marchandises dangereuses, rupture de barrage, etc. Chaque ligne associe une commune à un type de risque connu.

## Colonnes

- `cod_commune` : code INSEE commune (format entier, ex: `1001`)
- `lib_commune` : nom de la commune
- `lib_risque` : libellé du risque (Inondation, Séisme, Mouvement de terrain…)
- `num_risque` : code numérique du risque

## Lignes

172 595

## Clé de jointure

`cod_commune` (code INSEE commune, format entier)

# catnat_gaspar.csv

**Source** : [data.gouv.fr - Base GASPAR](https://www.data.gouv.fr/fr/datasets/base-nationale-de-gestion-assistee-des-procedures-administratives-relatives-aux-risques-gaspar/)

**Taille** : 34.5 MB | **Format** : CSV (séparateur `;`)

## Contenu

Arrêtés de catastrophe naturelle par commune (inondations, mouvements de terrain, sécheresse, tempêtes…). Chaque ligne correspond à un arrêté CatNat pour une commune donnée.

## Colonnes

- `cod_nat_catnat` : code national de l'arrêté
- `cod_commune` : code INSEE commune (format texte avec zéros, ex: `06120`)
- `lib_commune` : nom de la commune
- `num_risque_jo` : code du type de risque (GLT, ICB, MVT…)
- `lib_risque_jo` : libellé du risque (Inondations et/ou Coulées de Boue, Mouvement de Terrain…)
- `dat_deb` : date de début de l'événement
- `dat_fin` : date de fin de l'événement
- `dat_pub_arrete` : date de publication de l'arrêté
- `dat_pub_jo` : date de publication au Journal Officiel
- `dat_maj` : date de dernière mise à jour

## Lignes

260 799

## Années

1985 à 2022+

## Clé de jointure

`cod_commune` (code INSEE commune, format texte avec zéros)

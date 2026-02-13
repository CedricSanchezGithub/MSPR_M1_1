# candidats_results.txt

**Source** : [data.gouv.fr - Données des élections agrégées](https://www.data.gouv.fr/datasets/donnees-des-elections-agregees)

**Taille** : 2.1 GB | **Format** : TXT (séparateur `;`) | **Encodage** : UTF-8

## Contenu

Résultats de toutes les élections françaises (présidentielles, législatives, européennes, régionales, départementales, municipales) de 1999 à 2024, par bureau de vote.

## Colonnes clés

- `Code du département` + `Code de la commune` : identification géographique
- Nom du candidat, nuance politique, liste, nombre de voix, etc.

## Clé de jointure

`Code du département` + `Code de la commune` (code INSEE)

## Notes

- Fichier très volumineux, nécessite un parsing ligne par ligne (csv.reader)
- Ne pas charger entièrement en mémoire avec pandas

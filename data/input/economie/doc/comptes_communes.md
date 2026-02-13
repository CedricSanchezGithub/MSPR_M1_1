# comptes_communes_*.csv

**Source** : [data.economie.gouv.fr - Comptes individuels des communes](https://data.economie.gouv.fr/explore/?q=comptes+individuels+des+communes)

**Taille** : 652 MB (total 4 fichiers) | **Format** : CSV (séparateur `;`)

## Contenu

Comptes de fonctionnement et d'investissement de chaque commune française : recettes, dépenses, personnel, dette, dotation globale de fonctionnement (DGF), fiscalité locale, capacité d'autofinancement. ~253 colonnes par fichier.

## Fichiers

- `comptes_communes_2000_2008.csv` (344 MB) — 329 986 lignes, années 2000 à 2008
- `comptes_communes_2011_2015.csv` (214 MB) — 183 433 lignes, années 2011 à 2015
- `comptes_communes_2017.csv` (44 MB) — 35 410 lignes, année 2017
- `comptes_communes_2022.csv` (50 MB) — 34 956 lignes, année 2022

## Colonnes principales

- `an` : année
- `dep` : code département
- `icom` : code commune (dans le département)
- `inom` : nom de la commune
- `prod` : produits de fonctionnement
- `charge` : charges de fonctionnement
- `perso` : dépenses de personnel
- `depinv` : dépenses d'investissement
- `equip` : dépenses d'équipement
- `dette` : encours de la dette
- `dgf` : dotation globale de fonctionnement
- `caf` : capacité d'autofinancement
- `impo1` / `impo2` : impositions directes / indirectes
- `tfb` / `tth` : taux de taxe foncière bâti / taxe d'habitation

Les préfixes `f` = par habitant, `m` = moyenne de la strate, `r` = ratio.

## Années

2000 à 2022 (couvre les présidentielles 2002, 2007, 2012, 2017, 2022)

## Clé de jointure

`dep` + `icom` → reconstituer le code INSEE commune à 5 chiffres (dep sur 2-3 car. + icom sur 3 car.)

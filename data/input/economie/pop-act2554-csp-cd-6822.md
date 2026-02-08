# pop-act2554-csp-cd-6822.xlsx

**Source** : [INSEE - Séries historiques par commune](https://www.insee.fr/fr/information/2837787)

**Taille** : 28.5 MB | **Format** : XLSX (21 onglets)

## Contenu

Population active **25-54 ans** par **Catégorie Socioprofessionnelle** (CSP) et statut d'activité, par commune.

- 6 CSP : Agriculteurs, Artisans/Commerçants/Chefs d'entreprise, Cadres, Professions intermédiaires, Employés, Ouvriers
- 2 statuts : Actifs ayant un emploi, Chômeurs
- 12 colonnes de données par onglet

## Onglets

- `DEP_xxxx` : données départementales (~101 lignes)
- `COM_xxxx` : données communales (~39 000 lignes)
- Années : **1968, 1975, 1982, 1990, 1999, 2006, 2011, 2016, 2022**

## Clé de jointure

`Commune en géographie courante` (code INSEE commune)

## Notes techniques

- Header en ligne **12-14** selon les onglets (lignes de métadonnées INSEE à sauter)
- Utiliser `pd.read_excel(file, sheet_name='COM_2022', header=14)`

# Phase 2 — Modélisation & ETL

> Référence : `consignes.pdf` (cahier des charges Electio-Analytics)
> Périmètre : département de l'Hérault (34), ~340 communes
> Base de données cible : SQLite (`data/output/electio_herault.db`)

---

## Exigences du cahier des charges (extraits)

- *« Proposer un schéma de traitement des données (flux de données) »*
- *« Utiliser un outil de normalisation des données pour le mettre en œuvre (ETL) »*
- *« Définir une architecture de données adaptée aux traitements, en nommant spécifiquement et de manière pertinente vos tables et vos champs »*
- *« Les données seront nettoyées, normalisées et stockées dans une base structurée »*
- *« Un pipeline ETL automatisé (extraction, transformation, chargement) devra être mis en place »*
- *« Un Modèle Conceptuel de Données »* (livrable attendu)

---

## Étape 1 — Modèle Conceptuel de Données (MCD)

**Objectif** : définir les tables, relations et clés avant d'écrire le moindre code ETL.

### Tables prévues

| Table | Source | Description | Clé primaire |
|-------|--------|-------------|--------------|
| `communes` | Population historique | Référentiel des communes du 34 | `codgeo` (code INSEE 5 car.) |
| `elections` | candidats_results.txt | Résultats électoraux par commune × élection × candidat | `codgeo` + `annee` + `tour` + `candidat` |
| `population` | base-pop-historiques | Population municipale par commune × année de recensement | `codgeo` + `annee` |
| `naissances_deces` | DS_ETAT_CIVIL_* | Naissances et décès par commune × année | `codgeo` + `annee` |
| `revenus` | revenu-des-francais | Revenus médians, quartiles par commune | `codgeo` |
| `csp` | pop-act2554-csp | Population active par CSP × commune × année | `codgeo` + `annee` |
| `secteurs_activite` | pop-act2554-empl-sa | Actifs par secteur d'activité × sexe × commune × année | `codgeo` + `annee` |
| `diplomes` | base-cc-diplomes | Niveaux de diplôme par commune (2022) | `codgeo` |
| `comptes_communes` | comptes_communes_* | Finances locales (dépenses, recettes, dette, DGF…) × année | `codgeo` + `annee` |
| `catnat` | catnat_gaspar.csv | Arrêtés de catastrophe naturelle par commune | `codgeo` + `dat_deb` + `risque` |
| `risques` | risq_gaspar.csv | Risques connus par commune | `codgeo` + `num_risque` |

### Relations

```
communes (codgeo) ─── 1:N ──→ elections
communes (codgeo) ─── 1:N ──→ population
communes (codgeo) ─── 1:N ──→ naissances_deces
communes (codgeo) ─── 1:1 ──→ revenus
communes (codgeo) ─── 1:N ──→ csp
communes (codgeo) ─── 1:N ──→ secteurs_activite
communes (codgeo) ─── 1:1 ──→ diplomes
communes (codgeo) ─── 1:N ──→ comptes_communes
communes (codgeo) ─── 1:N ──→ catnat
communes (codgeo) ─── 1:N ──→ risques
```

La table `communes` est le **référentiel central**. Toutes les autres tables se joignent dessus via `codgeo`.

### À valider avant de coder

- [ ] Vérifier le nombre exact de communes du 34 dans chaque dataset
- [ ] Vérifier les formats de `codgeo` (5 car. avec zéros ? entier ? dep+icom ?)
- [ ] Décider de la granularité temporelle (garder toutes les années ou seulement celles des présidentielles ?)

---

## Étape 2 — Pipeline ETL

**Script cible** : `scripts/etl_pipeline.py`
**Orchestration** : ajout d'une commande `python main.py etl` dans `main.py`

### 2.1 — Extraction

Pour chaque dataset, lire le fichier source et filtrer sur le département 34.

| Dataset | Format | Filtre dept 34 | Difficulté |
|---------|--------|----------------|------------|
| Résultats électoraux | TXT (2.3 GB) | `Code du département == '34'` | Lecture chunked (fichier énorme) |
| Population historique | XLSX | `DEP == '34'` | skiprows=5, onglet spécifique |
| Naissances/Décès | CSV (`;`) | `GEO` commence par `'34'` + `GEO_OBJECT == 'COM'` | Filtrer sur préfixe codgeo |
| Revenus | CSV | `Code géographique` commence par `'34'` | Simple |
| CSP | XLSX (28 MB) | Colonne commune commence par `'34'` | Onglets COM_xxxx, header décalé |
| Secteurs activité | XLSX (23 MB) | Idem CSP | Idem |
| Diplômes | CSV (81 MB) | `CODGEO` commence par `'34'` | Simple |
| CSP × diplôme | XLSX (52 MB) | Colonne commune commence par `'34'` | Onglets COM_xxxx |
| Comptes communes | CSV (`;`) | `dep == '34'` | Reconstituer codgeo = dep + icom |
| CatNat | CSV (`;`) | `cod_commune` commence par `'34'` | Format texte avec zéros |
| Risques | CSV (`;`) | `cod_commune` entre 34001 et 34999 | Format entier |

### 2.2 — Transformation

Pour chaque table :

1. **Normaliser les codgeo** : toujours 5 caractères, string, avec zéros (ex: `'34001'`)
2. **Normaliser les noms de colonnes** : snake_case, français, explicites
3. **Gérer les valeurs manquantes** : documenter les NaN, décider par table (drop / impute / laisser)
4. **Typer les colonnes** : int pour les comptages, float pour les montants, str pour les codes
5. **Dédoublonner** si nécessaire
6. **Filtrer les élections** : ne garder que les présidentielles (2002, 2007, 2012, 2017, 2022) ou toutes ?

### 2.3 — Chargement

1. Créer la base SQLite `data/output/electio_herault.db`
2. Créer les tables avec les bons types et contraintes (PRIMARY KEY, FOREIGN KEY)
3. Insérer les données avec `pandas.DataFrame.to_sql()`
4. Créer les index sur `codgeo` et `annee` pour les performances
5. Vérifier les comptages post-chargement (nb lignes attendues vs insérées)

---

## Étape 3 — Validation & documentation

- [ ] Script de validation : nb communes, nb lignes par table, cohérence des jointures
- [ ] Documenter le schéma SQL final (DDL exporté)
- [ ] Mettre à jour `ROADMAP.md` (Phase 2 terminée)
- [ ] Mettre à jour `CLAUDE.md` si nécessaire (nouvelles commandes)

---

## Suivi d'avancement

| Tâche | Statut | Date | Notes |
|-------|--------|------|-------|
| MCD (conception tables/relations) | ⬜ À faire | | |
| Vérification formats codgeo par dataset | ⬜ À faire | | |
| Script ETL — extraction + filtrage dept 34 | ⬜ À faire | | |
| Script ETL — transformation/normalisation | ⬜ À faire | | |
| Script ETL — chargement SQLite | ⬜ À faire | | |
| Validation post-chargement | ⬜ À faire | | |
| Documentation schéma SQL | ⬜ À faire | | |
| Intégration dans main.py | ⬜ À faire | | |
| Commit & push | ⬜ À faire | | |

---

## Décisions à prendre

1. **Granularité des élections** : toutes les élections (législatives, municipales…) ou seulement les présidentielles ?
   - Recommandation : présidentielles uniquement (2002, 2007, 2012, 2017, 2022) — plus simple, directement lié au besoin de prédiction
2. **Granularité temporelle des indicateurs** : garder toutes les années disponibles ou aligner sur les années d'élection ?
   - Recommandation : garder toutes les années, interpoler si nécessaire en Phase 4
3. **Classification Gauche/Droite** : la faire dans l'ETL ou en Phase 3 ?
   - Recommandation : intégrer dans l'ETL (colonne `camp` dans la table `elections`)

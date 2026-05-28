# Qualité des données — Data Quality Management

## Objectif

Décrire les **dimensions qualité** retenues, les **contrôles réellement implémentés** dans le pipeline et les **limites résiduelles** identifiées. Le périmètre est l'entrepôt SQLite `data/output/electio_herault.db` (**12 tables**, **341 communes** de l'Hérault, ingéré par `scripts/etl/etl_pipeline.py`).

---

## 1. Cadre Data Quality retenu

Six dimensions inspirées d'ISO 8000, traduites en règles concrètes pour le projet.

| Dimension | Définition appliquée au projet | Où c'est contrôlé |
|---|---|---|
| **Complétude** | Toutes les communes du périmètre sont représentées dans chaque table principale | `validate()` (comptage par table, `etl_pipeline.py` l. 815–865) ; `dropna(how='any')` côté ML (`modele_predictif.py` l. 447) |
| **Cohérence** | Les jointures `codgeo` sont stables d'une table à l'autre ; les années des élections sont attendues | `validate()` : vérification des orphelins (`elections` → `communes`) et liste des années distinctes |
| **Exactitude** | Les valeurs reflètent la source officielle (INSEE, DGFiP, GASPAR) | Pas de transformation modifiant les valeurs ; logs de lignes lues / conservées par module |
| **Fraîcheur** | Sélection systématique de la dernière édition disponible pour chaque dataset | `SOURCES_DONNEES.md` documente les URL et années |
| **Unicité** | Pas de doublons sur les clés naturelles | PRIMARY KEY sur `communes.codgeo` ; `drop_duplicates(subset='codgeo')` lors de la construction du référentiel |
| **Validité** | Types corrects, codes INSEE bien formés (5 chars), pourcentages numériques | `pd.to_numeric(..., errors='coerce')`, normalisation `zfill(5)` |

---

## 2. Contrôles implémentés dans le pipeline ETL

### 2.1 Filtrage géographique

- **Règle** : toutes les sources filtrées sur le département 34 dès la lecture.
- **Mise en œuvre** : selon la source, comparaison sur `codgeo.startswith('34')` ou `dep.lstrip('0') == '34'` ou `Code du département == '34'`.
- **Effet** : volumétrie réduite d'un facteur 30 à 100 ; les anomalies hors périmètre sont ignorées sans bruit.

### 2.2 Normalisation des codes INSEE

- **Règle** : `codgeo` est systématiquement une chaîne de 5 caractères avec zéros initiaux préservés.
- **Mise en œuvre** : `str(x).strip().zfill(5)` ou recombinaison `dep + commune.zfill(3)` selon la source (helpers `normalize_codgeo()` et `codgeo_from_single()` dans `etl_pipeline.py`).
- **Effet** : jointabilité garantie entre datasets ; pas de perte d'information liée aux codes type `01001` ou `2A004`.

### 2.3 Classification politique des candidats

- **Règle primaire** : mapping du code nuance officiel vers `Gauche` / `Droite` via les ensembles `GAUCHE_NUANCES` (63 codes) et `DROITE_NUANCES` (75 codes).
- **Règle de repli** : scan du libellé de liste sur mots-clés (`socialiste`, `gauche`, `vert`… pour Gauche ; `national`, `républicain`, `marche`… pour Droite).
- **Valeur par défaut** : si aucune nuance ni mot-clé ne matche, le camp retenu est **`Droite`** (cf. ligne 105 d'`etl_pipeline.py`). Ce parti pris est documenté et doit être gardé en tête lors de l'interprétation des résultats.
- **Conséquence qualité** : les listes « sans étiquette politique » et `DIV` sont mécaniquement classées Droite, ce qui **gonfle artificiellement** la part Droite dans les communes rurales sans étiquette.

### 2.4 Pivotement temporel

Les datasets INSEE publiés en format large (colonnes `PMUN2014`, `p22_*`, etc.) sont **dépivotés** en lignes `(codgeo, annee, valeur)` lors de l'ETL. Les valeurs `NaN` issues du pivot sont conservées en `NULL` pour permettre un audit ultérieur.

### 2.5 Casting et nettoyage

- Conversion explicite des colonnes numériques avec `pd.to_numeric(..., errors='coerce')` : les valeurs non convertibles deviennent `NaN`.
- Strip et lowercase des noms de colonnes (transformation systématique dans les blocs `df.columns = ...`).
- Détection automatique du séparateur CSV pour le fichier revenus (`,` vs `;`).
- Détection automatique d'encodage (`utf-8`, `latin-1`, `cp1252`) pour les fichiers DGFiP et INSEE diplômes.

### 2.6 Validation finale (`validate()` lignes 815–865)

La fonction `validate()` est appelée à la toute fin du pipeline et exécute **trois contrôles** :

```
1. Comptage par table
   → Itère sur les 12 tables attendues, affiche le nombre de lignes,
     synthétise "Tables présentes : X/12"

2. Années d'élections distinctes
   SELECT DISTINCT annee FROM elections ORDER BY annee
   → Liste des millésimes municipaux présents (attendu : 2008, 2014, 2020)

3. Cohérence des jointures (orphelins)
   SELECT COUNT(DISTINCT e.codgeo)
   FROM elections e
   LEFT JOIN communes c ON e.codgeo = c.codgeo
   WHERE c.codgeo IS NULL
   → 0 attendu ; alerte affichée sinon
```

**Caractéristique importante** : `validate()` est purement informatif. Elle **n'interrompt pas** le pipeline en cas d'anomalie ; elle journalise les incohérences sur la sortie standard. Le contrôle qualité reste à la charge de l'opérateur qui lit le log.

---

## 3. Contrôles côté analyse et ML

### 3.1 Phase 3 — Analyse exploratoire

`scripts/analyse/analyse_exploratoire.py` applique systématiquement `dropna(...)` avant chaque graphique (par exemple lignes 110, 271, 343, 405). Si la jointure produit moins de 10 communes, un avertissement est affiché et le graphique est sauté (cf. la heatmap, lignes 407–410).

### 3.2 Phase 4 — Panel ML

Dans `modele_predictif.py`, fonction `construire_panel()` :

- Reporte le **taux de complétude** par feature (lignes 442–445) : `print(f"  {col} : {pct_ok:.0f}% complet")`.
- Applique `dropna(subset=FEATURES, how='any')` (ligne 447) : seules les lignes ayant les 12 features non nulles sont conservées.
- Trace la volumétrie restante : `print(f"Panel final (sans NaN) : {len(panel_complet)} lignes")`.

Le **mapping temporel** (`MAPPING_CSP = {2008: 2006, 2014: 2011, 2020: 2022}`, `MAPPING_DIPLOMES = {2008: 'p11', 2014: 'p16', 2020: 'p22'}`) garantit qu'à chaque année d'élection est associé le millésime de recensement le plus proche disponible. En cas d'absence du millésime exact, un repli sur le plus proche est appliqué (cf. lignes 161–166 et 280–289).

---

## 4. Limites qualité connues

### 4.1 Schémas dynamiques

Les tables `revenus`, `csp`, `secteurs_activite`, `diplomes`, `csp_diplome` (et `comptes_communes` après remplacement) sont écrites via `df.to_sql(..., if_exists='replace')`, ce qui **écrase le DDL initial** et crée un schéma dérivé du DataFrame source. Conséquence :

- Les colonnes exactes ne sont **pas garanties** à l'exécution.
- Les requêtes consommatrices doivent rechercher leurs colonnes par motif (`'actifs_ayant_un_emploi' in c and 'rp2022' in c`).
- Documenté dans `docs/PIPELINE_ETL.md` ; pas de risque pour les phases avales mais sensibilité aux changements de fichier source.

### 4.2 Foreign keys désactivées

`PRAGMA foreign_keys = OFF` au moment de la connexion (ligne 889) : les clauses `FOREIGN KEY` du DDL sont **documentaires**. Un `codgeo` orphelin dans `elections` ne déclenche pas d'erreur d'insertion, il est seulement détecté *a posteriori* par `validate()`.

### 4.3 Complétude inégale

| Feature | Couverture attendue | Cause d'absence |
|---|---|---|
| `population` | 100 % | — |
| `nb_catnat` | 100 % (forcé à 0 par `fillna(0)` ligne 440) | Communes sans arrêté CatNat |
| `taux_natalite` | proche de 100 % | Trous résiduels dans l'état civil (très petites communes) |
| `pct_cadres`, `pct_ouvriers`, `pct_employes`, `pct_prof_intermediaires` | 100 % après mapping temporel | RP le plus proche utilisé en repli |
| `pct_diplome_sup`, `pct_sans_diplome` | dépend du préfixe `p11_/p16_/p22_` disponible | Si le préfixe manque, l'année est sautée |
| `dette_par_hab`, `invest_par_hab` | dépend du millésime DGFiP le plus proche | Communes nouvelles, dissolutions |
| **`revenu_median`** | ~94 % | INSEE n'a pas publié pour quelques très petites communes |

Le facteur limitant principal est le **revenu médian** : il est le principal contributeur à la réduction du panel de 1 023 (théorique 341 × 3) à ~690 lignes après `dropna`.

### 4.4 Classification par défaut « Droite »

Cf. §2.3. Les listes sans étiquette politique claire sont mécaniquement classées Droite. Cela peut surreprésenter le camp Droite dans les communes rurales où les listes « divers » sont nombreuses.

### 4.5 Extrapolation 2026 naïve

Pour produire les prédictions 2026, la Phase 4 :

- **Population** : prolongement linéaire de la tendance 2014 → 2020 par commune.
- **Toutes les autres features** : valeur 2020 maintenue (`pct_cadres`, `revenu_median`, `dette_par_hab`, `pct_diplome_sup`, `taux_natalite`, …).
- **`nb_catnat`** : cumul historique inchangé.

C'est une **simplification consciente**, documentée dans `EXPLICATION_MODELE.md`. Toute évolution structurelle (déménagements, choc économique, vague d'arrêtés CatNat post-2020) est invisible pour le modèle.

### 4.6 Anachronisme léger sur les finances

Pour expliquer le vote 2020, le pipeline utilise les `comptes_communes` du **millésime DGFiP le plus proche** (par défaut, fonction `min(annees_cc, key=lambda x: abs(x - annee_elec))`, ligne 314). Si seule l'année 2022 est disponible, elle est utilisée pour 2020. Impact limité (les finances évoluent lentement), à durcir en allant chercher 2019–2020 explicitement.

### 4.7 Cohérence référentielle non bloquante

Les orphelins `codgeo` détectés par `validate()` sont journalisés mais non corrigés. Une éventuelle commune historique disparue (fusion, scission) reste dans `elections` mais sans ligne `communes`. Les tests réels indiquent au plus quelques unités (sur ~125 000 lignes `elections`).

---

## 5. Indicateurs qualité finaux attendus

Valeurs cibles à l'issue d'une exécution standard du pipeline. Les chiffres exacts varient selon la version des fichiers sources.

| Indicateur | Valeur attendue |
|---|---|
| Tables présentes | 12 / 12 |
| Communes dans `communes` | 341 |
| Années distinctes dans `elections` | 2008, 2014, 2020 (millésimes municipaux retenus) |
| Orphelins `elections.codgeo` ∉ `communes.codgeo` | 0 (ou ≤ quelques unités, journalisés) |
| Complétude moyenne des 12 features sur le panel ML | ≥ 94 % (revenu médian = principal facteur de réduction) |
| Volumétrie du panel ML après `dropna` | ~690 lignes / 1 023 théoriques |
| Taille du fichier `.db` | quelques MB |

---

## 6. Pointeurs

- [`scripts/etl/etl_pipeline.py`](../scripts/etl/etl_pipeline.py) — implémentation des contrôles.
- [`docs/PIPELINE_ETL.md`](PIPELINE_ETL.md) — détail de la transformation par table.
- [`docs/referentiel_donnees.md`](referentiel_donnees.md) — dictionnaire complet.
- [`docs/rgpd_securite.md`](rgpd_securite.md) — qualité côté licences et conformité.
- `EXPLICATION_MODELE.md` — explicitation de l'extrapolation 2026.

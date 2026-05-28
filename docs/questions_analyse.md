# Questions d'analyse — Electio-Analytics

## Objectif

Recenser les questions auxquelles le projet doit répondre, classer ces questions par nature (descriptive, diagnostique, prédictive, prescriptive), et tracer pour chacune le **livrable du projet** qui la traite (graphique, table SQL, métrique de modèle, etc.).

Périmètre rappelé : **341 communes** de l'Hérault, 3 millésimes municipaux (2008, 2014, 2020), prédiction 2026 ; **12 features ML**, **2 Random Forest** (Classifier + Regressor).

---

## 1. Questions imposées par le cahier des charges

Trois questions sont explicitement posées par le client Electio-Analytics. Les réponses détaillées figurent dans le `DOSSIER_SYNTHESE.md` §15 ; les éléments saillants sont rappelés ici.

### 1.1 Q1 — Quelle donnée est la plus corrélée aux résultats électoraux ?

**Nature** : diagnostique.

**Livrable** :
- `graphiques/phase4/01_importance_features.png` — barres d'importance Random Forest.
- `graphiques/phase3/04_heatmap_correlations.png` — matrice de corrélation de Pearson (lecture qualitative).
- Console du script `predict` — section « Questions d'analyse » imprimée par `afficher_questions_analyse()` (l. 859–896 de `modele_predictif.py`).

**Réponse synthétique** (au sens de l'importance Random Forest) : le top 5 est **`population`, `dette_par_hab`, `invest_par_hab`, `nb_catnat`, `pct_diplome_sup`**. Le `revenu_median` n'apparaît pas dans le top 5, ce qui invalide partiellement l'hypothèse initiale d'une dominance des variables sociologiques classiques.

### 1.2 Q2 — Définir le principe de l'apprentissage supervisé

**Nature** : pédagogique (méthodologie).

**Livrable** : section §15.2 du `DOSSIER_SYNTHESE.md` ; `EXPLICATION_MODELE.md` ; impression console du script `predict`.

**Réponse synthétique** : l'apprentissage supervisé entraîne une fonction `f : X → Y` à partir d'exemples étiquetés (entrées + sortie connue). Dans le projet :

- **X** : 12 features socio-éco par couple (commune, année).
- **Y** : camp politique (binaire) et `% Gauche` (continu).
- **Train** : élections 2008 + 2014.
- **Test** : élection 2020 (jamais vue à l'entraînement, pas de fuite temporelle).
- **Prédiction** : 2026 (features extrapolées).

### 1.3 Q3 — Comment définir l'accuracy du modèle ?

**Nature** : pédagogique (évaluation).

**Livrable** :
- `graphiques/phase4/02_matrice_confusion.png`.
- `graphiques/phase4/06_reel_vs_predit_2020.png`.
- Métriques imprimées par `entrainer_modeles()` (l. 488 et 496 de `modele_predictif.py`).

**Réponse synthétique** :

```
Accuracy = nombre de prédictions correctes / nombre total de prédictions
        = 0,896 sur le test 2020
```

Le **F1-score pondéré** complète l'accuracy en tenant compte du déséquilibre de classes : **0,906**. Le test 2020 est fortement déséquilibré côté Droite (le panel est dominé par les communes rurales pour lesquelles le repli `classify_camp()` choisit Droite par défaut). L'accuracy seule peut donc masquer un rappel Gauche médiocre ; la matrice de confusion est l'outil à privilégier pour une lecture honnête.

---

## 2. Questions descriptives (Phase 3)

Questions « **quoi se passe-t-il** » répondues par les 10 visualisations de `scripts/analyse/analyse_exploratoire.py`. Chaque livrable correspond à un graphique PNG dans `graphiques/phase3/`.

| # | Question | Graphique | Lecture clé |
|---|---|---|---|
| D1 | Comment a évolué le vote Gauche / Droite au tour 1 des municipales dans le 34 ? | `01_evolution_vote_herault.png` | Trajectoire des moyennes départementales 2008 → 2020 |
| D2 | Quelle est la **géographie** du vote 2020 dans l'Hérault ? | `02_carte_communes_2020.png` | Carte choroplèthe `% Gauche` par commune |
| D3 | Existe-t-il un lien **visuel** entre revenu médian et vote ? | `03_revenu_vs_vote.png` | Scatter + droite de tendance + corrélation de Pearson |
| D4 | Quelles **corrélations linéaires** entre les indicateurs socio-éco et le vote ? | `04_heatmap_correlations.png` | Matrice de Pearson sur 10 variables |
| D5 | Les **distributions** de revenus diffèrent-elles selon le camp ? | `05_boxplot_revenus_par_camp.png` | Boxplot communes Gauche vs Droite, moyennes annotées |
| D6 | La structure **socio-professionnelle** (cadres vs ouvriers) corrèle-t-elle au vote ? | `06_csp_cadres_ouvriers_vote.png` | Scatter `% cadres` × `% ouvriers`, couleur = camp |
| D7 | Quelles communes ont connu la plus forte **croissance / déclin démographique** ? | `07_evolution_population.png` | Double line chart top 10 croissance / top 10 déclin (1968–2022) |
| D8 | La **dette par habitant** est-elle corrélée au vote ? | `08_dette_vs_vote.png` | Scatter `dette_par_hab` × `% Gauche` |
| D9 | Le **niveau d'études** explique-t-il le vote ? | `09_diplomes_vs_vote.png` | Scatter `% diplôme supérieur` × `% Gauche` |
| D10 | Quelles communes sont les plus exposées aux **catastrophes naturelles** ? | `10_catnat_vs_vote.png` | Bar chart horizontal top 20, couleur = camp |

---

## 3. Questions diagnostiques (Phase 3 + Phase 4)

Questions « **pourquoi** » — explorations causales (à interpréter avec prudence ; on parle de corrélation, pas de causalité).

| # | Question | Livrable |
|---|---|---|
| Diag1 | Quelles variables sont **les plus discriminantes** pour distinguer une commune Gauche d'une commune Droite ? | `graphiques/phase4/01_importance_features.png` (Random Forest) + heatmap Pearson |
| Diag2 | Y a-t-il un **effet métropole** (Montpellier vs reste du département) ? | `02_carte_communes_2020.png` + table `communes` (taille = `population`) |
| Diag3 | Les variables **financières** (dette, investissement) jouent-elles plus que les variables **sociologiques** (CSP, diplôme) ? | Top 5 features RF : `population, dette_par_hab, invest_par_hab` dominent → réponse positive sur ce panel |
| Diag4 | Les communes à forte exposition aux risques naturels votent-elles différemment ? | `10_catnat_vs_vote.png` + importance de `nb_catnat` (rang 4) |
| Diag5 | Les **dynamiques** (croissance population, hausse % cadres) expliquent-elles le vote, indépendamment des niveaux ? | Panel `(codgeo, annee)` × 3 millésimes ; à approfondir par un Random Forest avec interactions explicites |

---

## 4. Questions prédictives (Phase 4)

Questions « **que va-t-il se passer** » — répondues par les modèles RF.

| # | Question | Livrable |
|---|---|---|
| Pred1 | Quel **camp** (Gauche / Droite) chaque commune va-t-elle élire en 2026 ? | Sortie du `RandomForestClassifier` → `graphiques/phase4/04_carte_predictions_2026.png` + DataFrame `df_futures` |
| Pred2 | Quel **`% Gauche`** continu prévoit le modèle pour chaque commune en 2026 ? | Sortie du `RandomForestRegressor`, identique à Pred1 |
| Pred3 | Comment évolue le **% Gauche départemental** entre 2008 et 2026 ? | `03_predictions_temporelles.png` |
| Pred4 | Comment se répartissent les **probabilités prédites** entre 0 et 100 % ? | `05_distribution_probabilites.png` (histogramme) |
| Pred5 | Le modèle **généralise-t-il** correctement à l'année test (2020) ? | `02_matrice_confusion.png` + `06_reel_vs_predit_2020.png` ; Accuracy 89,6 %, F1 0,906 |
| Pred6 | Quelle **trajectoire prédite** pour les communes remarquables (Montpellier, Béziers, Sète, Agde, Lunel) ? | `07_evolution_communes_remarquables.png` |

**Avertissements méthodologiques** (cf. `EXPLICATION_MODELE.md`, `DOSSIER_SYNTHESE.md`) :

- **Hypothèse de stabilité** : seules la population est extrapolée linéairement ; toutes les autres features sont **figées à leur valeur 2020**. Un changement structurel post-2020 n'est pas capté.
- **Déséquilibre du test 2020** : très majoritairement Droite (effet du repli `Droite` par défaut sur les listes sans étiquette). À pondérer dans l'interprétation des prédictions agrégées.
- **Effets locaux** non captés : maire sortant populaire, scandale, fermeture d'usine — invisibles pour un modèle structurel.

---

## 5. Questions prescriptives (perspectives — non couvertes par le POC)

Questions « **que faut-il faire** » — non implémentées dans le périmètre POC, mentionnées comme pistes pour une itération future.

| Question | Pourquoi non couverte | Comment l'aborder ensuite |
|---|---|---|
| Sur quelles communes Electio-Analytics doit-elle concentrer son ciblage stratégique ? | Hors périmètre analytique | Croiser `pred_pct_gauche` ≈ 50 % (incertitude) avec la `population` (impact potentiel) |
| Quel **scénario** ferait basculer une commune ? | Le modèle actuel ne simule pas de what-if | Construire une UI Streamlit permettant de modifier `pct_cadres`, `revenu_median`, etc. et relancer la prédiction |
| Quelles **interventions** (investissement, équipement) ont l'effet prédit le plus marqué ? | Pas d'analyse causale dans le POC | Ajouter un module SHAP / feature attribution + analyse contrefactuelle |

---

## 6. Synthèse — questions × livrables

| Type de question | Phase | Livrable principal |
|---|---|---|
| **Descriptive** | Phase 3 | 10 PNG dans `graphiques/phase3/` |
| **Diagnostique** | Phases 3 et 4 | Heatmap de corrélation + importance Random Forest |
| **Prédictive** | Phase 4 | 7 PNG dans `graphiques/phase4/` + prédictions 2026 |
| **Prescriptive** | (perspective) | Non couverte par le POC |
| **Cahier des charges (3 questions imposées)** | Phase 4 | `DOSSIER_SYNTHESE.md` §15 + console `python main.py predict` |

---

## 7. Pointeurs

- [`DOSSIER_SYNTHESE.md`](../DOSSIER_SYNTHESE.md) §15 — réponses détaillées aux 3 questions imposées.
- [`EXPLICATION_MODELE.md`](EXPLICATION_MODELE.md) — vulgarisation du modèle.
- `scripts/analyse/analyse_exploratoire.py` — code des 10 graphiques.
- `scripts/prediction/modele_predictif.py` — code des 7 graphiques et de la routine `afficher_questions_analyse()`.
- `app.py` — dashboard Streamlit, pages « Analyse exploratoire » et « Prédictions 2026 ».

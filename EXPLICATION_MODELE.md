# Comment fonctionne le modèle prédictif — Explication vulgarisée

## Principe général

On utilise un algorithme de **machine learning** (scikit-learn, pas un LLM type ChatGPT) pour trouver des corrélations entre les indicateurs socio-économiques d'une commune et son vote. Une fois ces corrélations apprises, le modèle peut **prédire** le vote d'une commune à partir de ses indicateurs.

---

## Étape 1 — Construire le tableau d'entraînement

### La dimension temporelle

On ne travaille pas sur une seule photo figée. On dispose de **3 élections municipales** (2008, 2014, 2020) et d'indicateurs qui évoluent dans le temps :

| Donnée | Années disponibles |
|--------|--------------------|
| Élections municipales (variable cible) | 2008, 2014, 2020 |
| Population | 1876–2023 (37 recensements) |
| CSP (cadres, ouvriers...) | 1968, 1975, ..., 2006, 2011, 2016, 2022 |
| Comptes communes (dette, dépenses...) | 2000–2022 (annuel) |
| Naissances / décès | 2008–2024 (annuel) |
| Revenus | snapshot (une seule année) |
| Diplômes | 2022 |
| CatNat | 1985–2022+ (cumul) |

### Le tableau

On croise **commune × année d'élection** : chaque ligne = une commune à une année donnée, avec les indicateurs les plus proches de cette année.

| commune     | année | population | % cadres | % ouvriers | dette/hab | nb_catnat | ... | % Gauche |
|-------------|-------|-----------|----------|------------|-----------|-----------|-----|----------|
| Montpellier | 2008  | 248 252   | 19.5     | 11.1       | 1 050     | 10        | ... | 52.3     |
| Montpellier | 2014  | 272 084   | 20.8     | 10.4       | 1 120     | 12        | ... | 55.1     |
| Montpellier | 2020  | 290 053   | 22.3     | 8.7        | 1 200     | 15        | ... | 58.7     |
| Béziers     | 2008  | 72 245    | 7.2      | 18.5       | 870       | 7         | ... | 35.2     |
| ...         | ...   | ...       | ...      | ...        | ...       | ...       | ... | ...      |

Ça donne environ **341 communes × 3 élections = ~690 lignes** d'entraînement, ce qui est suffisant pour détecter des relations significatives.

L'avantage : le modèle apprend non seulement les corrélations statiques (*« commune riche → vote Gauche »*), mais aussi les **dynamiques** (*« quand la population augmente ET le % cadres monte → le vote évolue vers la Gauche »*).

- Les colonnes à gauche = les **features** (ce que le modèle utilise pour deviner)
- La dernière colonne = la **cible** (ce qu'il doit prédire : le % Gauche)

## Étape 2 — Entraîner le modèle (apprentissage supervisé)

On donne les élections **2008 et 2014** au modèle en lui montrant les indicateurs **ET** le résultat du vote. Le modèle va chercher des règles, par exemple :

- *« quand le revenu est haut ET le % diplômé est haut → plutôt Gauche »*
- *« quand le % ouvriers est haut ET peu de diplômés → plutôt Droite »*

C'est ça l'**apprentissage supervisé** : on lui montre les réponses pour qu'il apprenne les patterns tout seul.

## Étape 3 — Tester le modèle

On prend l'élection **2020** (que le modèle n'a jamais vue) et on lui demande de prédire le vote uniquement à partir des indicateurs.

On compare ses prédictions avec la réalité → ça donne l'**accuracy** : **89.6%** des communes correctement classées Gauche ou Droite.

L'algorithme utilisé est **Random Forest** : il construit 200 arbres de décision indépendants et fait voter le résultat. C'est robuste et interprétable (on peut voir quels indicateurs pèsent le plus).

## Étape 4 — Prédire le futur

Pour prédire **2026**, on a besoin d'indicateurs futurs que l'on n'a pas encore. On les **extrapole** à partir des tendances passées :

- **Population** : on prolonge la tendance 2014→2020 pour chaque commune
- **CSP / diplômes / revenus** : on maintient les valeurs 2020 (hypothèse de stabilité)
- **Finances communales** : on maintient les valeurs 2020
- **CatNat** : on garde le cumul historique connu

On construit ainsi un tableau fictif pour 2026 avec les indicateurs projetés, et le modèle sort une **prédiction de vote** pour chaque commune.

---

## En pratique dans le code

C'est la librairie **scikit-learn** (Python). Le code ressemble à ça :

```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=200)
model.fit(X_train, y_train)         # apprend sur 2008-2014
score = model.score(X_test, y_test) # teste sur 2020
predictions = model.predict(X_2026) # prédit 2026
```

Le plus long c'est la **préparation du tableau** (feature engineering), l'entraînement en lui-même prend quelques secondes.

---

## Vocabulaire clé

| Terme | Définition |
|-------|-----------|
| **Feature** | Un indicateur utilisé en entrée (revenu, % cadres, dette...) |
| **Cible (target)** | Ce qu'on cherche à prédire (% Gauche ou camp Gauche/Droite) |
| **Apprentissage supervisé** | On montre au modèle les réponses pour qu'il apprenne les patterns |
| **Split temporel** | On sépare les données dans le temps : 2008–2014 pour apprendre, 2020 pour évaluer |
| **Accuracy** | % de prédictions correctes sur les données de test (89.6%) |
| **Matrice de confusion** | Tableau qui montre les erreurs : combien de communes Gauche prédites Droite (et inversement) |
| **F1-score** | Mesure plus fine que l'accuracy, utile quand les classes sont déséquilibrées (0.906) |
| **Random Forest** | Algorithme qui construit 200 arbres de décision et fait voter le résultat |
| **Feature importance** | Classement des indicateurs par leur poids dans la prédiction |

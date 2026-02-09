# Comment fonctionne le modèle prédictif — Explication vulgarisée

## Principe général

On utilise un algorithme de **machine learning** (scikit-learn, pas un LLM type ChatGPT) pour trouver des corrélations entre les indicateurs socio-économiques d'une commune et son vote. Une fois ces corrélations apprises, le modèle peut **prédire** le vote d'une commune à partir de ses indicateurs.

---

## Étape 1 — Construire le tableau d'entraînement

### La dimension temporelle

On ne travaille pas sur une seule photo figée. On dispose de **5 élections présidentielles** (2002, 2007, 2012, 2017, 2022) et d'indicateurs qui évoluent dans le temps :

| Donnée | Années disponibles |
|--------|--------------------|
| Élections (variable cible) | 2002, 2007, 2012, 2017, 2022 |
| Population | 1968, 1975, 1982, 1990, 1999, 2006-2023 |
| CSP (cadres, ouvriers...) | 1968, 1975, 1982, 1990, 1999, 2006, 2011, 2016, 2022 |
| Comptes communes (dette, dépenses...) | 2000-2022 (annuel) |
| Naissances / décès | 2008-2024 (annuel) |
| Revenus | snapshot (une seule année) |
| Diplômes | 2022 |
| CatNat | 1985-2022+ (cumul) |

### Le tableau

On croise **commune × année d'élection** : chaque ligne = une commune à une année donnée, avec les indicateurs les plus proches de cette année.

| commune     | année | population | % cadres | % ouvriers | dette/hab | nb_catnat | ... | % Gauche |
|-------------|-------|-----------|----------|------------|-----------|-----------|-----|----------|
| Montpellier | 2002  | 225 392   | 18.1     | 12.3       | 980       | 8         | ... | 55.2     |
| Montpellier | 2007  | 248 252   | 19.5     | 11.1       | 1 050     | 10        | ... | 51.8     |
| Montpellier | 2012  | 264 538   | 20.8     | 10.4       | 1 120     | 12        | ... | 58.3     |
| Montpellier | 2022  | 295 542   | 22.3     | 8.7        | 1 200     | 15        | ... | 62.4     |
| Béziers     | 2002  | 69 153    | 7.2      | 18.5       | 870       | 7         | ... | 38.1     |
| ...         | ...   | ...       | ...      | ...        | ...       | ...       | ... | ...      |

Ça donne environ **341 communes × 5 élections = ~1 700 lignes** d'entraînement au lieu de 341, ce qui rend le modèle plus robuste.

L'avantage : le modèle apprend non seulement les corrélations statiques (*« commune riche → vote Gauche »*), mais aussi les **dynamiques** (*« quand la population augmente ET le % cadres monte → le vote évolue vers la Gauche »*).

- Les colonnes à gauche = les **features** (ce que le modèle utilise pour deviner)
- La dernière colonne = la **cible** (ce qu'il doit prédire : le % Gauche)

## Étape 2 — Entraîner le modèle (apprentissage supervisé)

On donne **~80% des communes** au modèle en lui montrant les indicateurs **ET** le résultat du vote. Le modèle va chercher des règles, par exemple :

- *« quand le revenu est haut ET le % diplômé est haut → plutôt Gauche »*
- *« quand le % ouvriers est haut ET peu de diplômés → plutôt Droite »*

C'est ça l'**apprentissage supervisé** : on lui montre les réponses pour qu'il apprenne les patterns tout seul.

## Étape 3 — Tester le modèle

On prend les **20% de communes restantes** (que le modèle n'a jamais vues) et on lui demande de prédire le vote uniquement à partir des indicateurs.

On compare ses prédictions avec la réalité → ça donne l'**accuracy** (ex : « il a bon sur 75% des communes »).

On teste plusieurs algorithmes (régression logistique, random forest, gradient boosting) et on garde le meilleur.

## Étape 4 — Prédire le futur

Pour prédire 2025, 2026 et 2027, on a besoin d'indicateurs futurs que l'on n'a pas encore. On les **extrapole** à partir des tendances passées :

- **Population** : on a les chiffres de 1968 à 2023. On prolonge la courbe de chaque commune (régression linéaire sur les dernières années).
- **CSP / diplômes** : on prolonge les tendances 2006 → 2022 (ex : si le % cadres monte de +0.5% par an, on continue).
- **Finances** : idem avec les comptes communes 2000-2022.
- **CatNat** : on garde le cumul connu (pas d'extrapolation, c'est un historique).

On construit ainsi un tableau fictif pour 2025/2026/2027 avec les indicateurs projetés, et le modèle sort une **prédiction de vote** pour chaque commune à chaque horizon.

---

## En pratique dans le code

C'est la librairie **scikit-learn** (Python). Le code ressemble à ça :

```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier()
model.fit(X_train, y_train)         # apprend sur 80%
score = model.score(X_test, y_test) # teste sur 20%
predictions = model.predict(X_2025) # prédit le futur
```

C'est environ 200 lignes de Python. Le plus long c'est la **préparation du tableau** (feature engineering), l'entraînement en lui-même prend quelques secondes.

---

## Vocabulaire clé

| Terme | Définition |
|-------|-----------|
| **Feature** | Un indicateur utilisé en entrée (revenu, % cadres, dette...) |
| **Cible (target)** | Ce qu'on cherche à prédire (% Gauche ou camp Gauche/Droite) |
| **Apprentissage supervisé** | On montre au modèle les réponses pour qu'il apprenne les patterns |
| **Train/test split** | On sépare les données en 80% pour apprendre, 20% pour évaluer |
| **Accuracy** | % de prédictions correctes sur les données de test |
| **Matrice de confusion** | Tableau qui montre les erreurs : combien de communes Gauche prédites Droite (et inversement) |
| **F1-score** | Mesure plus fine que l'accuracy, utile quand les classes sont déséquilibrées |
| **Random Forest** | Algorithme qui construit plein d'arbres de décision et fait voter le résultat |
| **Feature importance** | Classement des indicateurs par leur poids dans la prédiction |

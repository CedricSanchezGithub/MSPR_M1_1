# Comment fonctionne le modèle prédictif — Explication vulgarisée

## Principe général

On utilise un algorithme de **machine learning** (scikit-learn, pas un LLM type ChatGPT) pour trouver des corrélations entre les indicateurs socio-économiques d'une commune et son vote. Une fois ces corrélations apprises, le modèle peut **prédire** le vote d'une commune à partir de ses indicateurs.

---

## Étape 1 — Construire le tableau d'entraînement

On prend la base SQLite et on construit **un grand tableau** où chaque ligne = une commune, et chaque colonne = un indicateur :

| commune     | revenu_median | % cadres | % diplômé_sup | dette/hab | nb_catnat | ... | % Gauche |
|-------------|--------------|----------|---------------|-----------|-----------|-----|----------|
| Montpellier | 19 800       | 22.3     | 38.1          | 1 200     | 15        | ... | 62.4     |
| Béziers     | 16 200       | 8.7      | 14.2          | 980       | 12        | ... | 31.8     |
| Sète        | 18 100       | 12.1     | 21.5          | 1 450     | 18        | ... | 48.2     |
| ...         | ...          | ...      | ...           | ...       | ...       | ... | ...      |

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

On modifie les valeurs des indicateurs pour simuler **2025, 2026, 2027** (en extrapolant les tendances : population qui augmente, revenus qui bougent...) et le modèle sort une **prédiction de vote** pour chaque commune.

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

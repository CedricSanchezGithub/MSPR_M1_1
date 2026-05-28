# Metabase — Documentation

## Qu'est-ce que c'est

Metabase est un outil de Business Intelligence open source qui permet de créer des dashboards interactifs à partir d'une base de données, sans écrire de code front-end. Dans ce projet, il sert d'interface de visualisation pour les résultats du pipeline ETL et du modèle prédictif.

Trois dashboards sont configurés :
- **Dashboard 1 — Prédictions 2026** : carte choroplèthe, distribution et évolution du vote prédit
- **Dashboard 2 — Validation du modèle** : matrice de confusion, importance des features, métriques Random Forest
- **Dashboard 3 — Profil socio-démographique** : population, revenus, finances communales, démographie

---

## Lancer l'instance

Metabase tourne via Docker Compose avec deux services :

```bash
docker compose up -d
```

| Service | URL | Rôle |
|---|---|---|
| `electio_metabase` | http://localhost:3000 | Interface Metabase |
| `electio_images` | http://localhost:8080 | Serveur de fichiers statiques (PNGs matplotlib) |

La base SQLite est montée dans le conteneur via un volume :

```yaml
volumes:
  - ./data/output:/sqlite-data
```

La connexion à la DB est configurée dans Metabase sous **Admin → Bases de données** avec le chemin `/sqlite-data/electio_herault.db`.

---

## Connexion à l'ETL

Le pipeline complet suit cet ordre :

```
python main.py etl        → Reconstruit electio_herault.db (12 tables)
python main.py predict    → Entraîne le modèle, écrit 5 tables de résultats en base
docker compose restart metabase  → Force Metabase à relire le schéma SQLite
```

Les tables écrites par `main.py predict` et consommées par Metabase :

| Table | Contenu |
|---|---|
| `feature_importances` | Importance de chaque variable selon le Random Forest |
| `metriques_modele` | Accuracy, F1, R², MAE |
| `predictions_test_2020` | Prédictions sur le jeu de test avec écarts et flag correct/incorrect |
| `predictions_2026` | Prédictions pour les municipales 2026 par commune |
| `comparaison_2020_2026` | Bascules de camp entre 2020 et 2026 |

> **Important** : après chaque `python main.py etl`, relancer `docker compose restart metabase` est obligatoire. Metabase met en cache le schéma SQLite et ne détecte pas automatiquement les changements de structure.

Les PNGs matplotlib (carte, matrice de confusion, etc.) sont servis par le container `electio_images` sur `http://localhost:8080` et peuvent être embarqués dans les dashboards via des blocs texte Markdown.

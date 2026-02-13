# Exploration — Environnement

## Notebook : `exploration_environnement.ipynb`

Exploration des fichiers de données environnementales du dossier parent.

### Sections

1. **Catastrophes naturelles (CatNat)** — Chargement du CSV des arrêtés CatNat (~260 000 lignes). Types de catastrophes, communes touchées, dates.
2. **Risques GASPAR** — Chargement du CSV des risques identifiés par commune (inondation, sécheresse, etc.).
3. **Qualité des données** — Bilan des valeurs manquantes pour chaque dataset.

### Fichiers explorés

| Fichier | Format | Contenu |
|---------|--------|---------|
| `catnat_gaspar.csv` | CSV | Arrêtés de catastrophes naturelles par commune (1985–2022+) |
| `risq_gaspar.csv` | CSV | Risques GASPAR identifiés par commune |

### Prérequis

- Python avec `pandas`
- Kernel configuré sur le venv du projet

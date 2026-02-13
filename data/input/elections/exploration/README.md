# Exploration — Élections

## Notebook : `exploration_elections.ipynb`

Exploration du fichier de résultats électoraux du dossier parent.

### Sections

1. **Structure du fichier** — Lecture des premières lignes brutes pour identifier l'encodage (UTF-8) et le séparateur (`;`).
2. **Chargement d'un échantillon** — Chargement des 10 000 premières lignes (le fichier complet fait 2.3 GB). Aperçu des 18 colonnes.
3. **Valeurs uniques** — Analyse des colonnes catégorielles (types d'élections, nuances politiques, etc.).
4. **Qualité des données** — Bilan des valeurs manquantes (certaines colonnes comme Nom/Prénom sont vides pour les élections de liste).

### Fichiers explorés

| Fichier | Format | Contenu |
|---------|--------|---------|
| `candidats_results.txt` | CSV (`;`, UTF-8) | Résultats électoraux par candidat/liste et bureau de vote (2.3 GB) |

### Attention

Le fichier fait **2.3 GB** — le notebook ne charge qu'un échantillon de 10 000 lignes pour l'exploration. Ne pas tenter de charger le fichier entier en mémoire.

### Prérequis

- Python avec `pandas`
- Kernel configuré sur le venv du projet

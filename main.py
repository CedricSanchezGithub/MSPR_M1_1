#!/usr/bin/env python3
"""
MSPR - Analyse et Prédiction Électorale
Point d'entrée principal

Usage:
    python main.py [commande]

Commandes disponibles:
    explore     - Lancer les analyses exploratoires
    classify    - Classifier les candidats (Gauche/Droite)
    visualize   - Générer tous les graphiques
    etl         - Pipeline ETL : filtrer Hérault (34), charger SQLite
    analyse     - Analyse exploratoire Phase 3 (10 graphiques depuis SQLite)
    predict     - Modèle prédictif Phase 4 (2 modèles, 7 graphiques, prédiction municipales 2026)
    export      - Exporter les visualisations Metabase + générer rapports Markdown
    all         - Exécuter toutes les étapes
"""

import os
import sys
import subprocess

# Chemins des scripts
SCRIPTS_DIR = "scripts"

SCRIPTS = {
    "explore_candidats": os.path.join(SCRIPTS_DIR, "exploration", "explore_candidats.py"),
    "explore_revenus": os.path.join(SCRIPTS_DIR, "exploration", "explore_revenus.py"),
    "classify": os.path.join(SCRIPTS_DIR, "classification", "classify_candidats_v2.py"),
    "viz_presidentielles": os.path.join(SCRIPTS_DIR, "visualisation", "visualize_presidentielles.py"),
    "viz_comparatifs": os.path.join(SCRIPTS_DIR, "visualisation", "visualize_revenus_vs_votes.py"),
    "etl": os.path.join(SCRIPTS_DIR, "etl", "etl_pipeline.py"),
    "analyse": os.path.join(SCRIPTS_DIR, "analyse", "analyse_exploratoire.py"),
    "predict": os.path.join(SCRIPTS_DIR, "prediction", "modele_predictif.py"),
    "metabase_export": os.path.join(SCRIPTS_DIR, "visualisation", "metabase_export.py"),
}


def print_header():
    print("=" * 70)
    print("   MSPR - ANALYSE ET PRÉDICTION ÉLECTORALE")
    print("=" * 70)


def print_structure():
    """Affiche la structure du projet"""
    print("""
Structure du projet:
├── data/
│   ├── input/              # Données brutes (candidats, revenus, etc.)
│   └── output/             # SQLite + données générées
├── outputs/                # Résultats textuels des analyses
├── graphiques/
│   ├── presidentielles/    # Graphiques des présidentielles
│   ├── comparatifs/        # Graphiques revenus vs votes
│   ├── phase3/             # Analyse exploratoire Hérault (10 graphiques)
│   ├── phase4/             # Modèle prédictif (8 graphiques)
│   └── metabase_export/    # PNGs téléchargés depuis Metabase (latest/ + YYYY-MM-DD/)
├── docs/
│   └── rapports/           # Rapports Markdown générés (synthese_latest.md + archives)
├── scripts/
│   ├── exploration/        # Scripts d'exploration des données
│   ├── classification/     # Classification Gauche/Droite
│   ├── visualisation/      # Graphiques + export Metabase
│   ├── etl/                # Pipeline ETL → SQLite
│   ├── analyse/            # Analyse exploratoire Phase 3
│   └── prediction/         # Modèle prédictif Phase 4
├── metabase_config.json    # Configuration Metabase (UUIDs, credentials)
├── main.py                 # Ce fichier
└── requirements.txt
""")


def run_script(script_path, description, extra_args=None):
    """Exécute un script Python (avec args supplémentaires si fournis)"""
    print(f"\n{'─' * 50}")
    print(f"▶ {description}")
    print(f"{'─' * 50}")

    cmd = [sys.executable, script_path]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f"⚠ Erreur lors de l'exécution de {script_path}")
        return False
    return True


def cmd_explore():
    """Lancer les analyses exploratoires"""
    print("\n📊 ANALYSES EXPLORATOIRES")
    run_script(SCRIPTS["explore_candidats"], "Analyse du fichier candidats")
    run_script(SCRIPTS["explore_revenus"], "Analyse du fichier revenus")


def cmd_classify():
    """Classifier les candidats"""
    print("\n🏷️  CLASSIFICATION GAUCHE/DROITE")
    run_script(SCRIPTS["classify"], "Classification des candidats")


def cmd_visualize():
    """Générer les graphiques"""
    print("\n📈 GÉNÉRATION DES GRAPHIQUES")
    run_script(SCRIPTS["viz_presidentielles"], "Graphiques présidentielles")
    run_script(SCRIPTS["viz_comparatifs"], "Graphiques revenus vs votes")


def cmd_etl():
    """Lancer le pipeline ETL (Phase 2) puis exporter vers Metabase"""
    print("\n🔄 PIPELINE ETL — HÉRAULT (34)")
    etl_ok = run_script(SCRIPTS["etl"], "Pipeline ETL : extraction, transformation, chargement SQLite")

    # ── Export Metabase automatique après chaque ETL ───────────────────
    # Télécharge les PNGs Metabase et régénère les rapports Markdown.
    # Passe silencieusement si metabase_config.json n'est pas configuré.
    print("\n📊 EXPORT METABASE (post-ETL)")
    export_script = SCRIPTS["metabase_export"]
    if os.path.exists(export_script):
        run_script(export_script, "Export Metabase : téléchargement PNGs + rapports Markdown")
    else:
        print("  ⚠ Script d'export introuvable — ignoré")


def cmd_export():
    """Exporter les visualisations Metabase et générer les rapports Markdown"""
    print("\n📊 EXPORT METABASE")
    run_script(SCRIPTS["metabase_export"], "Export Metabase : téléchargement PNGs + rapports Markdown")


def cmd_analyse():
    """Lancer l'analyse exploratoire (Phase 3)"""
    print("\n🔬 ANALYSE EXPLORATOIRE — HÉRAULT (34)")
    run_script(SCRIPTS["analyse"], "Analyse exploratoire : 10 visualisations depuis SQLite")


def cmd_predict():
    """Lancer le modèle prédictif (Phase 4).

    Arg optionnel : --annee YYYY pour changer l'année cible (défaut 2026).
    Ex. : python main.py predict --annee 2032
    """
    print("\n🤖 MODÈLE PRÉDICTIF — HÉRAULT (34)")
    # Tout ce qui suit "predict" est passé au script de prédiction (ex. --annee)
    extra = sys.argv[2:]
    run_script(SCRIPTS["predict"],
               "Modèle prédictif : 2 modèles, 7 graphiques, prédiction municipales",
               extra_args=extra)


def cmd_all():
    """Exécuter toutes les étapes"""
    cmd_explore()
    cmd_classify()
    cmd_visualize()


def cmd_help():
    """Afficher l'aide"""
    print(__doc__)
    print_structure()
    print("\nFichiers de données requis dans data/input/:")
    print("  - candidats_results.txt (résultats électoraux)")
    print("  - revenu-des-francais-*.csv (revenus par commune)")


def main():
    print_header()

    if len(sys.argv) < 2:
        cmd_help()
        return

    command = sys.argv[1].lower()

    commands = {
        "explore": cmd_explore,
        "classify": cmd_classify,
        "visualize": cmd_visualize,
        "viz": cmd_visualize,
        "etl": cmd_etl,
        "analyse": cmd_analyse,
        "predict": cmd_predict,
        "export": cmd_export,
        "all": cmd_all,
        "help": cmd_help,
        "-h": cmd_help,
        "--help": cmd_help,
    }

    if command in commands:
        commands[command]()
        print("\n" + "=" * 70)
        print("   TERMINÉ")
        print("=" * 70)
    else:
        print(f"Commande inconnue: {command}")
        cmd_help()


if __name__ == "__main__":
    main()

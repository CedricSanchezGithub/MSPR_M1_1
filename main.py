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
    all         - Exécuter toutes les étapes
"""

import os
import sys
import subprocess

# Chemins des scripts
SCRIPTS_DIR = "scripts"

SCRIPTS = {
    "explore_candidats": os.path.join(SCRIPTS_DIR, "explore_candidats.py"),
    "explore_revenus": os.path.join(SCRIPTS_DIR, "explore_revenus.py"),
    "classify": os.path.join(SCRIPTS_DIR, "classify_candidats_v2.py"),
    "viz_presidentielles": os.path.join(SCRIPTS_DIR, "visualize_presidentielles.py"),
    "viz_comparatifs": os.path.join(SCRIPTS_DIR, "visualize_revenus_vs_votes.py"),
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
│   ├── input/          # Données brutes (candidats, revenus)
│   └── output/         # Données générées (candidats_classified.txt)
├── outputs/            # Résultats textuels des analyses
├── graphiques/
│   ├── presidentielles/  # Graphiques des présidentielles
│   └── comparatifs/      # Graphiques revenus vs votes
├── scripts/            # Scripts Python
├── main.py             # Ce fichier
└── requirements.txt
""")


def run_script(script_path, description):
    """Exécute un script Python"""
    print(f"\n{'─' * 50}")
    print(f"▶ {description}")
    print(f"{'─' * 50}")

    result = subprocess.run([sys.executable, script_path],
                          capture_output=False)

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

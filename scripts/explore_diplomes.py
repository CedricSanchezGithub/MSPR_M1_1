#!/usr/bin/env python3
"""
Script d'exploration des fichiers diplômes et formation (INSEE 2022)
"""

import csv
import os
from collections import Counter, defaultdict

# Configuration
INPUT_DIR = "data/input/nouveau"
OUTPUT_FILE = "outputs/exploration_diplomes_output.txt"

def analyze_file(filepath, output_lines, max_rows=100000):
    """Analyse un fichier CSV"""
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath) / (1024 * 1024)  # MB

    def log(msg):
        print(msg)
        output_lines.append(msg)

    log(f"\n{'=' * 70}")
    log(f"FICHIER: {filename} ({filesize:.2f} MB)")
    log("=" * 70)

    # Détection du séparateur
    separators = [';', ',', '\t', '|']
    encodings = ['utf-8', 'latin-1', 'cp1252']

    detected_sep = None
    detected_enc = None
    headers = []

    for enc in encodings:
        for sep in separators:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    first_line = f.readline()
                    if sep in first_line and first_line.count(sep) > 1:
                        detected_sep = sep
                        detected_enc = enc
                        headers = [h.strip().strip('"') for h in first_line.strip().split(sep)]
                        break
            except:
                continue
        if detected_sep:
            break

    if not detected_sep:
        log("  ERREUR: Impossible de détecter le format")
        return

    log(f"\n  Encodage: {detected_enc}")
    log(f"  Séparateur: '{detected_sep}'")
    log(f"  Colonnes: {len(headers)}")

    # Afficher les colonnes
    log(f"\n  COLONNES:")
    for i, col in enumerate(headers[:30], 1):
        log(f"    {i:3}. {col}")
    if len(headers) > 30:
        log(f"    ... et {len(headers) - 30} autres colonnes")

    # Analyser le contenu
    total_rows = 0
    counters = defaultdict(Counter)
    sample_rows = []

    try:
        with open(filepath, 'r', encoding=detected_enc) as f:
            reader = csv.reader(f, delimiter=detected_sep)
            next(reader)  # Skip header

            for row in reader:
                total_rows += 1

                if total_rows <= 5:
                    sample_rows.append(dict(zip(headers, row)))

                if total_rows <= max_rows:
                    # Compter quelques colonnes clés
                    for i, val in enumerate(row[:10]):
                        if i < len(headers):
                            counters[headers[i]][val.strip()] += 1

        log(f"\n  LIGNES: {total_rows:,}")

    except Exception as e:
        log(f"  ERREUR: {e}")
        return

    # Afficher les distributions pour les colonnes avec peu de valeurs uniques
    log(f"\n  DISTRIBUTIONS (colonnes avec < 50 valeurs uniques):")
    for col in list(counters.keys())[:10]:
        n_unique = len(counters[col])
        if n_unique < 50:
            log(f"\n    {col} ({n_unique} valeurs):")
            for val, count in counters[col].most_common(10):
                display_val = val[:40] if val else "(vide)"
                log(f"      - {display_val}: {count:,}")

    # Échantillon
    log(f"\n  ÉCHANTILLON (3 premières lignes):")
    for i, row in enumerate(sample_rows[:3], 1):
        log(f"\n    Ligne {i}:")
        for j, (key, val) in enumerate(row.items()):
            if j < 15:  # Limiter l'affichage
                display_val = val[:60] if val else "(vide)"
                log(f"      {key}: {display_val}")
        if len(row) > 15:
            log(f"      ... et {len(row) - 15} autres champs")


def main():
    output_lines = []

    def log(msg):
        print(msg)
        output_lines.append(msg)

    log("=" * 70)
    log("ANALYSE EXPLORATOIRE - DIPLÔMES ET FORMATION (INSEE 2022)")
    log("=" * 70)

    # Lister les fichiers
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.CSV') or f.endswith('.csv')]

    log(f"\nFichiers trouvés dans {INPUT_DIR}/:")
    for f in sorted(files):
        size = os.path.getsize(os.path.join(INPUT_DIR, f)) / (1024 * 1024)
        log(f"  - {f} ({size:.2f} MB)")

    # Analyser d'abord les métadonnées (plus petits)
    meta_files = [f for f in files if f.startswith('meta_')]
    data_files = [f for f in files if not f.startswith('meta_')]

    # Analyser les fichiers meta d'abord
    for f in sorted(meta_files):
        analyze_file(os.path.join(INPUT_DIR, f), output_lines)

    # Puis les fichiers de données
    for f in sorted(data_files):
        analyze_file(os.path.join(INPUT_DIR, f), output_lines)

    log("\n" + "=" * 70)
    log("FIN DE L'ANALYSE")
    log("=" * 70)

    # Sauvegarder
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"\n=> Résultats sauvegardés dans: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

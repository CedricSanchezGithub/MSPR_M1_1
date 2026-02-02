#!/usr/bin/env python3
"""
Script d'exploration du fichier revenus des Français par commune
"""

import csv
from collections import Counter, defaultdict
import sys

# Configuration
FILE_PATH = "data/input/revenu-des-francais-a-la-commune-1765372688826.csv"
OUTPUT_FILE = "outputs/exploration_revenus_output.txt"

def main():
    output_lines = []

    def log(msg):
        print(msg)
        output_lines.append(msg)

    log("=" * 80)
    log("ANALYSE EXPLORATOIRE - Revenus des Français par commune")
    log("=" * 80)

    # Détection du séparateur et de l'encodage
    separators = [';', ',', '\t', '|']
    encodings = ['utf-8', 'latin-1', 'cp1252']

    detected_sep = None
    detected_enc = None
    headers = []

    for enc in encodings:
        for sep in separators:
            try:
                with open(FILE_PATH, 'r', encoding=enc) as f:
                    first_line = f.readline()
                    if sep in first_line and first_line.count(sep) > 2:
                        detected_sep = sep
                        detected_enc = enc
                        headers = first_line.strip().split(sep)
                        break
            except:
                continue
        if detected_sep:
            break

    log(f"\n[1] DÉTECTION DU FORMAT")
    log("-" * 40)
    log(f"  Encodage détecté: {detected_enc}")
    log(f"  Séparateur détecté: '{detected_sep}'")
    log(f"  Nombre de colonnes: {len(headers)}")

    log(f"\n[2] COLONNES")
    log("-" * 40)
    for i, col in enumerate(headers, 1):
        log(f"  {i:2}. {col}")

    # Analyse du contenu
    total_rows = 0
    col_idx = {h: i for i, h in enumerate(headers)}

    # Compteurs pour différentes colonnes
    counters = defaultdict(Counter)
    numeric_stats = defaultdict(list)
    sample_rows = []

    # Colonnes à analyser (on détectera automatiquement)
    text_cols = []
    numeric_cols = []

    log(f"\n[3] LECTURE DU FICHIER...")
    log("-" * 40)

    try:
        with open(FILE_PATH, 'r', encoding=detected_enc) as f:
            reader = csv.reader(f, delimiter=detected_sep)
            next(reader)  # Skip header

            for row in reader:
                total_rows += 1

                # Garder les 10 premières lignes comme échantillon
                if total_rows <= 10:
                    sample_rows.append(dict(zip(headers, row)))

                # Analyser chaque colonne
                for i, val in enumerate(row):
                    if i >= len(headers):
                        continue
                    col_name = headers[i]
                    val = val.strip()

                    # Essayer de détecter si numérique
                    try:
                        # Gérer les nombres avec virgule décimale
                        num_val = float(val.replace(',', '.').replace(' ', ''))
                        if total_rows <= 100000:  # Limiter pour mémoire
                            numeric_stats[col_name].append(num_val)
                    except:
                        # C'est du texte
                        if total_rows <= 100000:
                            counters[col_name][val] += 1

        log(f"  Total de lignes: {total_rows:,}")

    except Exception as e:
        log(f"\nERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Identifier les types de colonnes
    for col in headers:
        if col in numeric_stats and len(numeric_stats[col]) > total_rows * 0.5:
            numeric_cols.append(col)
        elif col in counters:
            text_cols.append(col)

    log(f"\n[4] TYPES DE COLONNES DÉTECTÉS")
    log("-" * 40)
    log(f"  Colonnes numériques: {len(numeric_cols)}")
    log(f"  Colonnes textuelles: {len(text_cols)}")

    # Statistiques sur les colonnes numériques
    log(f"\n[5] STATISTIQUES NUMÉRIQUES")
    log("-" * 40)

    for col in numeric_cols[:15]:  # Limiter à 15 colonnes
        vals = numeric_stats[col]
        if vals:
            vals_sorted = sorted(vals)
            n = len(vals)
            mean_val = sum(vals) / n
            min_val = vals_sorted[0]
            max_val = vals_sorted[-1]
            median_val = vals_sorted[n // 2]

            log(f"\n  {col}:")
            log(f"    Count:  {n:,}")
            log(f"    Min:    {min_val:,.2f}")
            log(f"    Max:    {max_val:,.2f}")
            log(f"    Mean:   {mean_val:,.2f}")
            log(f"    Median: {median_val:,.2f}")

    # Statistiques sur les colonnes textuelles
    log(f"\n[6] COLONNES TEXTUELLES - VALEURS UNIQUES")
    log("-" * 40)

    for col in text_cols[:10]:  # Limiter à 10 colonnes
        counter = counters[col]
        n_unique = len(counter)
        log(f"\n  {col}:")
        log(f"    Valeurs uniques: {n_unique:,}")

        if n_unique <= 20:
            log(f"    Distribution:")
            for val, count in counter.most_common(20):
                display_val = val[:50] if val else "(vide)"
                log(f"      - {display_val}: {count:,}")
        else:
            log(f"    Top 10:")
            for val, count in counter.most_common(10):
                display_val = val[:50] if val else "(vide)"
                log(f"      - {display_val}: {count:,}")

    # Échantillon de données
    log(f"\n[7] ÉCHANTILLON DE DONNÉES (5 premières lignes)")
    log("-" * 40)
    for i, row in enumerate(sample_rows[:5], 1):
        log(f"\n  Ligne {i}:")
        for key, val in row.items():
            display_val = val[:80] if val else "(vide)"
            log(f"    {key}: {display_val}")

    # Résumé
    log(f"\n[8] RÉSUMÉ")
    log("=" * 80)
    log(f"  Fichier: {FILE_PATH}")
    log(f"  Lignes: {total_rows:,}")
    log(f"  Colonnes: {len(headers)}")
    log(f"  Colonnes numériques: {len(numeric_cols)}")
    log(f"  Colonnes textuelles: {len(text_cols)}")

    log("\n" + "=" * 80)
    log("FIN DE L'ANALYSE")
    log("=" * 80)

    # Sauvegarde
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"\n=> Résultats sauvegardés dans: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

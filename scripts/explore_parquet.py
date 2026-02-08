#!/usr/bin/env python3
"""
Script d'exploration légère d'un fichier Parquet.
Lit les métadonnées et les 30 premières lignes.
"""

import os
import sys

try:
    import pandas as pd
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "pyarrow"])
    import pandas as pd

INPUT_FILE = "data/input/nouveau/barometre-du-numerique.parquet"
OUTPUT_FILE = "outputs/exploration_barometre_numerique_output.txt"
MAX_LIGNES = 30


def log(msg, output_lines):
    print(msg)
    output_lines.append(msg)


def main():
    output_lines = []

    filename = os.path.basename(INPUT_FILE)
    filesize = os.path.getsize(INPUT_FILE) / (1024 * 1024)

    log("=" * 70, output_lines)
    log(f"ANALYSE EXPLORATOIRE - {filename} ({filesize:.1f} MB)", output_lines)
    log("=" * 70, output_lines)

    # Lire les métadonnées parquet sans charger les données
    pf = pd.read_parquet(INPUT_FILE, engine='pyarrow')
    total_rows = len(pf)
    total_cols = len(pf.columns)

    log(f"\n  Lignes totales: {total_rows:,}", output_lines)
    log(f"  Colonnes: {total_cols}", output_lines)
    log(f"  Mémoire estimée: {pf.memory_usage(deep=True).sum() / (1024*1024):.1f} MB", output_lines)

    # Travailler sur un échantillon
    df = pf.head(MAX_LIGNES)
    del pf  # Libérer la mémoire

    # Colonnes et types
    log(f"\n  COLONNES ({total_cols}):", output_lines)
    # Recharger juste pour les stats de null
    null_counts = pd.read_parquet(INPUT_FILE, engine='pyarrow').isnull().sum()
    for i, col in enumerate(df.columns, 1):
        dtype = df[col].dtype
        non_null = total_rows - null_counts[col]
        log(f"    {i:3}. {str(col):<45} | type: {str(dtype):<12} | non-null: {non_null:,}/{total_rows:,}", output_lines)

    # Aperçu des 5 premières lignes
    log(f"\n  APERÇU (5 premières lignes):", output_lines)
    sample = df.head(5).to_string(max_colwidth=50)
    for line in sample.split('\n'):
        log(f"    {line}", output_lines)

    # Stats numériques
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    if numeric_cols:
        log(f"\n  STATS (colonnes numériques, sur {MAX_LIGNES} lignes):", output_lines)
        stats = df[numeric_cols].describe().round(2)
        for line in stats.to_string().split('\n'):
            log(f"    {line}", output_lines)

    # Valeurs uniques pour colonnes catégorielles
    cat_cols = [c for c in df.columns if df[c].dtype == 'object' or str(df[c].dtype) == 'category']
    if cat_cols:
        log(f"\n  VALEURS UNIQUES (colonnes texte/catégorielles):", output_lines)
        # Recharger pour avoir les vraies distributions
        full_cats = pd.read_parquet(INPUT_FILE, columns=cat_cols, engine='pyarrow')
        for col in cat_cols:
            n_unique = full_cats[col].nunique()
            if n_unique <= 30:
                vals = full_cats[col].value_counts().head(15)
                log(f"\n    {col} ({n_unique} valeurs):", output_lines)
                for val, count in vals.items():
                    display_val = str(val)[:60] if val else "(vide)"
                    log(f"      - {display_val}: {count:,}", output_lines)
            else:
                log(f"\n    {col}: {n_unique} valeurs uniques (trop pour lister)", output_lines)
        del full_cats

    log(f"\n{'=' * 70}", output_lines)
    log("FIN DE L'ANALYSE", output_lines)
    log("=" * 70, output_lines)

    # Sauvegarder
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"\n=> Résultats sauvegardés dans: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

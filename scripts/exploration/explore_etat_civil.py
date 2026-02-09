"""Exploration des fichiers d'état civil (naissances et décès) par commune."""
import csv
import os

INPUT_DIR = "data/input/nouveau"
OUTPUT_FILE = "data/output/exploration_etat_civil.txt"

files = [
    "DS_ETAT_CIVIL_NAIS_COMMUNES_data.csv",
    "DS_ETAT_CIVIL_NAIS_COMMUNES_metadata.csv",
    "DS_ETAT_CIVIL_DECES_COMMUNES_data.csv",
    "DS_ETAT_CIVIL_DECES_COMMUNES_metadata.csv",
]

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for fname in files:
        fpath = os.path.join(INPUT_DIR, fname)
        if not os.path.exists(fpath):
            out.write(f"\n{'='*60}\nFICHIER INTROUVABLE : {fname}\n")
            continue

        size_mb = os.path.getsize(fpath) / (1024 * 1024)
        out.write(f"\n{'='*60}\n")
        out.write(f"FICHIER : {fname}\n")
        out.write(f"TAILLE  : {size_mb:.1f} MB\n")
        out.write(f"{'='*60}\n\n")

        # Détecter le séparateur
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            first_line = f.readline()

        sep = ";" if first_line.count(";") > first_line.count(",") else ","
        out.write(f"Séparateur détecté : '{sep}'\n\n")

        # Lire les 30 premières lignes
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f, delimiter=sep)
            rows = []
            for i, row in enumerate(reader):
                if i >= 30:
                    break
                rows.append(row)

        if not rows:
            out.write("Fichier vide !\n")
            continue

        header = rows[0]
        out.write(f"Nombre de colonnes : {len(header)}\n")
        out.write(f"Colonnes : {header}\n\n")

        out.write("--- 30 premières lignes ---\n")
        for i, row in enumerate(rows):
            out.write(f"L{i:>3} | {sep.join(row[:10])}")
            if len(row) > 10:
                out.write(f" ... (+{len(row)-10} cols)")
            out.write("\n")

        # Compter le nombre total de lignes
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            total = sum(1 for _ in f)
        out.write(f"\nNombre total de lignes : {total:,}\n")

        # Pour les fichiers data, analyser les valeurs uniques de quelques colonnes clés
        if "_data.csv" in fname and len(rows) > 1:
            out.write("\n--- Analyse des colonnes clés ---\n")
            # Identifier les colonnes intéressantes
            key_cols = {}
            for idx, col in enumerate(header):
                col_upper = col.upper().strip()
                if any(k in col_upper for k in ["GEO", "TIME", "FREQ", "MEASURE", "OBS", "UNIT"]):
                    key_cols[col] = idx

            if not key_cols:
                # Prendre les 5 premières colonnes
                for idx, col in enumerate(header[:5]):
                    key_cols[col] = idx

            # Collecter les valeurs uniques (limité à 50k lignes pour rapidité)
            col_values = {col: set() for col in key_cols}
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f, delimiter=sep)
                next(reader)  # skip header
                for i, row in enumerate(reader):
                    if i >= 50000:
                        break
                    for col, idx in key_cols.items():
                        if idx < len(row):
                            col_values[col].add(row[idx])

            for col, values in col_values.items():
                out.write(f"\n  {col} ({len(values)} valeurs uniques sur 50k lignes) :\n")
                sample = sorted(list(values))[:20]
                out.write(f"    Exemples : {sample}\n")
                if len(values) <= 30:
                    out.write(f"    Toutes : {sorted(list(values))}\n")

print(f"Exploration terminée -> {OUTPUT_FILE}")

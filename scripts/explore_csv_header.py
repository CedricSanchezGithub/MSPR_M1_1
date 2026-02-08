#!/usr/bin/env python3
"""
Lecture rapide du header + 5 premières lignes d'un gros CSV.
Ne charge pas tout le fichier.
"""

import csv
import os

INPUT_FILE = "data/input/nouveau/barometre-du-numerique-2007-2024.csv"

filesize = os.path.getsize(INPUT_FILE) / (1024 * 1024)
print(f"Fichier: {os.path.basename(INPUT_FILE)} ({filesize:.1f} MB)")

# Tester encodage et séparateur
for enc in ['utf-8', 'latin-1', 'cp1252']:
    try:
        with open(INPUT_FILE, 'r', encoding=enc) as f:
            first_line = f.readline()
            # Détecter le séparateur
            for sep in [';', ',', '\t', '|']:
                if sep in first_line and first_line.count(sep) > 5:
                    headers = [h.strip().strip('"') for h in first_line.strip().split(sep)]
                    print(f"Encodage: {enc}, Séparateur: '{sep}'")
                    print(f"Nombre de colonnes: {len(headers)}")

                    # Chercher des colonnes géographiques
                    geo_cols = [h for h in headers if any(k in h.upper() for k in
                        ['CODGEO', 'CODE', 'COMMUNE', 'DEP', 'REGION', 'GEO', 'INSEE', 'CP', 'POSTAL'])]
                    print(f"\nColonnes géographiques trouvées: {geo_cols}")

                    # Lister toutes les colonnes
                    print(f"\nTOUTES LES COLONNES ({len(headers)}):")
                    for i, h in enumerate(headers, 1):
                        print(f"  {i:4}. {h}")

                    # Lire 5 lignes
                    print(f"\n5 PREMIÈRES LIGNES (10 premières colonnes):")
                    reader = csv.reader(f, delimiter=sep)
                    for j, row in enumerate(reader):
                        if j >= 5:
                            break
                        print(f"  Ligne {j+1}: {row[:10]}")

                    # Compter les lignes rapidement
                    f.seek(0)
                    total = sum(1 for _ in f) - 1
                    print(f"\nLignes totales: {total:,}")
                    raise SystemExit(0)
    except UnicodeDecodeError:
        continue
    except SystemExit:
        raise

print("Impossible de lire le fichier")

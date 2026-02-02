#!/usr/bin/env python3
"""
Script d'exploration du fichier candidats_results.txt
Analyse ligne par ligne pour gérer les fichiers volumineux (2.1GB)
Sans dépendances externes (pas de pandas)
"""

import csv
from collections import Counter, defaultdict
import sys

# Configuration
FILE_PATH = "data_input/candidats_results.txt"
OUTPUT_FILE = "exploration_candidats_output.txt"
SEPARATOR = ";"

def main():
    output_lines = []

    def log(msg):
        print(msg)
        output_lines.append(msg)

    log("=" * 80)
    log("ANALYSE EXPLORATOIRE - candidats_results.txt")
    log("=" * 80)

    # Compteurs globaux
    total_rows = 0
    elections_counter = Counter()
    departements_counter = Counter()
    communes_counter = Counter()
    listes_counter = Counter()
    nuances_counter = Counter()
    tetes_liste_counter = Counter()
    panneau_counter = Counter()
    sexe_counter = Counter()

    # Stats numériques
    voix_values = []
    pct_ins_values = []
    pct_exp_values = []

    # Échantillons
    sample_rows = []
    headers = []

    # Index des colonnes (sera défini après lecture de l'en-tête)
    col_idx = {}

    log("\n[1] Lecture du fichier ligne par ligne...")

    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=SEPARATOR)

            # Lire l'en-tête
            headers = next(reader)
            for i, h in enumerate(headers):
                col_idx[h] = i

            log(f"  En-tête détecté avec {len(headers)} colonnes")

            for row in reader:
                total_rows += 1

                if total_rows % 1_000_000 == 0:
                    print(f"  {total_rows:,} lignes traitées...")

                # Garder les 5 premières lignes comme échantillon
                if total_rows <= 5:
                    sample_rows.append(dict(zip(headers, row)))

                # Vérifier que la ligne a assez de colonnes
                if len(row) < len(headers):
                    continue

                # Comptages
                if 'id_election' in col_idx:
                    val = row[col_idx['id_election']].strip()
                    if val:
                        elections_counter[val] += 1

                if 'Code du département' in col_idx:
                    val = row[col_idx['Code du département']].strip()
                    if val:
                        departements_counter[val] += 1

                if 'Code de la commune' in col_idx:
                    val = row[col_idx['Code de la commune']].strip()
                    if val:
                        communes_counter[val] += 1

                if 'Libellé Abrégé Liste' in col_idx:
                    val = row[col_idx['Libellé Abrégé Liste']].strip()
                    if val:
                        listes_counter[val] += 1

                if 'Nuance' in col_idx:
                    val = row[col_idx['Nuance']].strip()
                    if val:
                        nuances_counter[val] += 1

                if 'Nom Tête de Liste' in col_idx:
                    val = row[col_idx['Nom Tête de Liste']].strip()
                    if val:
                        tetes_liste_counter[val] += 1

                if 'N°Panneau' in col_idx:
                    val = row[col_idx['N°Panneau']].strip()
                    if val:
                        panneau_counter[val] += 1

                if 'Sexe' in col_idx:
                    val = row[col_idx['Sexe']].strip()
                    if val:
                        sexe_counter[val] += 1

                # Valeurs numériques (échantillonner pour stats)
                if total_rows <= 1_000_000:  # Limiter pour mémoire
                    if 'Voix' in col_idx:
                        try:
                            val = float(row[col_idx['Voix']].strip())
                            voix_values.append(val)
                        except:
                            pass

                    if '% Voix/Ins' in col_idx:
                        try:
                            val = float(row[col_idx['% Voix/Ins']].strip())
                            pct_ins_values.append(val)
                        except:
                            pass

                    if '% Voix/Exp' in col_idx:
                        try:
                            val = float(row[col_idx['% Voix/Exp']].strip())
                            pct_exp_values.append(val)
                        except:
                            pass

        log(f"\n  => Lecture terminée!")

    except Exception as e:
        log(f"\nERREUR lors de la lecture: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Affichage des résultats
    log("\n" + "=" * 80)
    log("[2] STATISTIQUES GÉNÉRALES")
    log("=" * 80)
    log(f"  Nombre total de lignes (hors en-tête): {total_rows:,}")

    log("\n" + "-" * 40)
    log("[3] COLONNES")
    log("-" * 40)
    for i, col in enumerate(headers, 1):
        log(f"  {i:2}. {col}")

    log("\n" + "-" * 40)
    log("[4] ÉLECTIONS PRÉSENTES")
    log("-" * 40)
    log(f"  Nombre d'élections distinctes: {len(elections_counter)}")
    for election, count in elections_counter.most_common():
        log(f"    - {election}: {count:,} lignes")

    log("\n" + "-" * 40)
    log("[5] DÉPARTEMENTS")
    log("-" * 40)
    log(f"  Nombre de départements: {len(departements_counter)}")
    log("  Top 15 départements (par nombre de lignes):")
    for dept, count in departements_counter.most_common(15):
        log(f"    - {dept}: {count:,} lignes")

    log("\n" + "-" * 40)
    log("[6] COMMUNES")
    log("-" * 40)
    log(f"  Nombre de communes distinctes: {len(communes_counter)}")
    log("  Top 10 communes (par nombre de lignes):")
    for commune, count in communes_counter.most_common(10):
        log(f"    - {commune}: {count:,} lignes")

    log("\n" + "-" * 40)
    log("[7] LISTES / PARTIS (Libellé Abrégé)")
    log("-" * 40)
    log(f"  Nombre de listes distinctes: {len(listes_counter)}")
    log("  Top 30 listes:")
    for liste, count in listes_counter.most_common(30):
        log(f"    - {liste}: {count:,}")

    log("\n" + "-" * 40)
    log("[8] NUANCES POLITIQUES")
    log("-" * 40)
    log(f"  Nombre de nuances distinctes: {len(nuances_counter)}")
    if nuances_counter:
        log("  Toutes les nuances:")
        for nuance, count in nuances_counter.most_common():
            log(f"    - '{nuance}': {count:,}")
    else:
        log("  (Aucune nuance trouvée ou colonne vide)")

    log("\n" + "-" * 40)
    log("[9] TÊTES DE LISTE")
    log("-" * 40)
    log(f"  Nombre de têtes de liste distinctes: {len(tetes_liste_counter)}")
    log("  Top 30 têtes de liste:")
    for tete, count in tetes_liste_counter.most_common(30):
        log(f"    - {tete}: {count:,}")

    log("\n" + "-" * 40)
    log("[10] NUMÉROS DE PANNEAU")
    log("-" * 40)
    log(f"  Valeurs distinctes: {len(panneau_counter)}")
    log("  Distribution (triée):")
    sorted_panneaux = sorted(panneau_counter.items(),
                              key=lambda x: (int(x[0]) if x[0].isdigit() else 999, x[0]))
    for panneau, count in sorted_panneaux[:30]:
        log(f"    - Panneau {panneau}: {count:,}")
    if len(sorted_panneaux) > 30:
        log(f"    ... et {len(sorted_panneaux) - 30} autres valeurs")

    log("\n" + "-" * 40)
    log("[11] SEXE")
    log("-" * 40)
    if sexe_counter:
        for sexe, count in sexe_counter.most_common():
            log(f"    - '{sexe}': {count:,}")
    else:
        log("  (Colonne vide ou non renseignée)")

    log("\n" + "-" * 40)
    log("[12] STATISTIQUES SUR LES VOIX")
    log("-" * 40)
    if voix_values:
        voix_values.sort()
        log(f"  Basé sur {len(voix_values):,} entrées (échantillon)")
        log(f"  Total: {sum(voix_values):,.0f}")
        log(f"  Moyenne: {sum(voix_values)/len(voix_values):,.2f}")
        log(f"  Min: {voix_values[0]:,.0f}")
        log(f"  Max: {voix_values[-1]:,.0f}")
        log(f"  Médiane: {voix_values[len(voix_values)//2]:,.0f}")
        # Percentiles
        p25 = voix_values[int(len(voix_values)*0.25)]
        p75 = voix_values[int(len(voix_values)*0.75)]
        p90 = voix_values[int(len(voix_values)*0.90)]
        p99 = voix_values[int(len(voix_values)*0.99)]
        log(f"  25e percentile: {p25:,.0f}")
        log(f"  75e percentile: {p75:,.0f}")
        log(f"  90e percentile: {p90:,.0f}")
        log(f"  99e percentile: {p99:,.0f}")
    else:
        log("  (Pas de données)")

    log("\n" + "-" * 40)
    log("[13] STATISTIQUES SUR % Voix/Inscrits")
    log("-" * 40)
    if pct_ins_values:
        pct_ins_values.sort()
        log(f"  Basé sur {len(pct_ins_values):,} entrées")
        log(f"  Moyenne: {sum(pct_ins_values)/len(pct_ins_values):.2f}%")
        log(f"  Min: {pct_ins_values[0]:.2f}%")
        log(f"  Max: {pct_ins_values[-1]:.2f}%")
        log(f"  Médiane: {pct_ins_values[len(pct_ins_values)//2]:.2f}%")
    else:
        log("  (Pas de données)")

    log("\n" + "-" * 40)
    log("[14] STATISTIQUES SUR % Voix/Exprimés")
    log("-" * 40)
    if pct_exp_values:
        pct_exp_values.sort()
        log(f"  Basé sur {len(pct_exp_values):,} entrées")
        log(f"  Moyenne: {sum(pct_exp_values)/len(pct_exp_values):.2f}%")
        log(f"  Min: {pct_exp_values[0]:.2f}%")
        log(f"  Max: {pct_exp_values[-1]:.2f}%")
        log(f"  Médiane: {pct_exp_values[len(pct_exp_values)//2]:.2f}%")
    else:
        log("  (Pas de données)")

    log("\n" + "-" * 40)
    log("[15] ÉCHANTILLON DE DONNÉES (5 premières lignes)")
    log("-" * 40)
    for i, row in enumerate(sample_rows, 1):
        log(f"\n  Ligne {i}:")
        for key, val in row.items():
            log(f"    {key}: {val}")

    log("\n" + "=" * 80)
    log("FIN DE L'ANALYSE")
    log("=" * 80)

    # Sauvegarde dans le fichier output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"\n=> Résultats sauvegardés dans: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

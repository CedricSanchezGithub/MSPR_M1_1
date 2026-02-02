#!/usr/bin/env python3
"""
Script de classification des candidats en Gauche/Droite - VERSION LÉGÈRE
Crée un fichier avec seulement les colonnes essentielles + Camp
LREM et la majorité présidentielle Macron sont classés à droite
"""

import csv
import sys

# Configuration
INPUT_FILE = "data_input/candidats_results.txt"
OUTPUT_FILE = "candidats_camp.txt"
SEPARATOR = ";"

# Classification des nuances politiques
GAUCHE_NUANCES = {
    # Extrême gauche
    'EXG', 'LEXG', 'LXG', 'DXG',
    'LO', 'LCR',
    # Communistes
    'COM', 'LCOM', 'HUE',
    # Front de Gauche / NUPES / Insoumis
    'FG', 'LFG', 'NUP', 'FI', 'LFI', 'PG', 'LPG', 'MELE',
    # Socialistes
    'SOC', 'LSOC', 'HOLL', 'JOSP', 'ROYA',
    # Écologistes
    'VEC', 'LVEC', 'ECO', 'LECO', 'LVEG', 'LVE', 'LEC', 'JOLY', 'BOVE',
    # Divers gauche
    'DVG', 'LDVG', 'UG', 'LUG', 'LUGE', 'RDG', 'LRDG', 'LRG', 'LDG', 'PRG',
    # Autres gauche
    'MDC', 'GAU',
    # Binômes gauche
    'BC-SOC', 'BC-COM', 'BC-FG', 'BC-ECO', 'BC-VEC', 'BC-DVG',
    'BC-EXG', 'BC-UG', 'BC-UGE', 'BC-FI', 'BC-RDG', 'BC-UCG', 'BC-PG',
    # Candidats gauche
    'ARTH', 'POUT', 'BUFF', 'GLUC', 'TAUB', 'SCHI', 'BESA', 'LAGU',
}

DROITE_NUANCES = {
    # Extrême droite
    'EXD', 'LEXD', 'LXD', 'DXD', 'UXD',
    'FN', 'LFN', 'RN', 'LRN', 'MNR', 'MEGR', 'LEPA',
    # Droite traditionnelle
    'UMP', 'LUMP', 'LR', 'LLR', 'RPR', 'DVD', 'LDVD', 'DTE', 'SARK', 'CHIR',
    # Centre-droit / UDF
    'UDF', 'LUDF', 'UDFD', 'DL', 'UDI', 'LUDI', 'CEN', 'PRV', 'BAYR', 'LPC', 'LCP', 'LCMD',
    # Souverainistes droite
    'MPF', 'DLF', 'LDLF', 'DUPO', 'RPF', 'CPNT',
    # MACRON / LREM (classé à droite)
    'REM', 'LREM', 'ENS', 'LENS', 'MDM', 'LMDM', 'MODM', 'MAJ', 'LMAJ', 'HOR', 'ALLI', 'LMC',
    'REC', 'LREC',
    # Binômes droite
    'BC-FN', 'BC-RN', 'BC-DVD', 'BC-UMP', 'BC-LR', 'BC-UD',
    'BC-UDI', 'BC-UC', 'BC-UCD', 'BC-REM', 'BC-MDM', 'BC-DLF',
    'BC-EXD', 'BC-UXD', 'BC-DVC',
    # Divers droite
    'DVC', 'LDVC', 'LDR', 'LDD', 'LUCD', 'FRN',
    # Divers (classés droite par défaut)
    'DIV', 'LDIV', 'NC', 'LNC', 'NCE', 'M-NC', 'AUT', 'LAUT',
    'REG', 'LREG', 'MNA', 'DSV', 'LDSV', 'BC-DSV', 'LDV', 'LUD', 'LCOP', 'PREP',
    # Candidats droite
    'VILL', 'NIHO', 'VOYN', 'BOUT', 'MADE', 'CHEV', 'SAIN', 'MAME',
}


def classify_nuance(nuance):
    """Classifie une nuance politique en Gauche ou Droite"""
    nuance = nuance.strip().upper()
    if not nuance:
        return "Droite"
    if nuance in GAUCHE_NUANCES:
        return "Gauche"
    return "Droite"


def classify_by_liste(libelle):
    """Classification de secours par le nom de liste"""
    libelle = libelle.lower().strip()

    gauche_kw = ['insoumis', 'communiste', 'socialiste', 'écologi', 'vert',
                 'lutte ouvrière', 'npa', 'gauche', 'ouvrier', 'pcf', 'eelv']
    droite_kw = ['national', 'républicain', 'marche', 'renaissance', 'ensemble',
                 'modem', 'horizons', 'reconquête', 'zemmour', 'droite', 'ump',
                 'frexit', 'patriote', 'udi', 'centriste']

    for kw in gauche_kw:
        if kw in libelle:
            return "Gauche"
    for kw in droite_kw:
        if kw in libelle:
            return "Droite"
    return None


def main():
    print("=" * 70)
    print("CLASSIFICATION LÉGÈRE - GAUCHE / DROITE")
    print("(LREM/Macron classé à DROITE)")
    print("=" * 70)

    total = 0
    gauche_count = 0
    droite_count = 0
    col_idx = {}

    print(f"\nLecture de {INPUT_FILE}...")
    print(f"Écriture vers {OUTPUT_FILE}...")

    with open(INPUT_FILE, 'r', encoding='utf-8') as infile, \
         open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as outfile:

        reader = csv.reader(infile, delimiter=SEPARATOR)
        writer = csv.writer(outfile, delimiter=SEPARATOR)

        headers = next(reader)
        for i, h in enumerate(headers):
            col_idx[h] = i

        # Colonnes essentielles seulement
        out_headers = [
            "id_election",
            "Code du département",
            "Code de la commune",
            "Code du b.vote",
            "Libellé Abrégé Liste",
            "Voix",
            "% Voix/Ins",
            "% Voix/Exp",
            "Nuance",
            "Camp"
        ]
        writer.writerow(out_headers)

        for row in reader:
            total += 1

            if total % 2_000_000 == 0:
                print(f"  {total:,} lignes traitées...")

            # Extraire les valeurs
            def get_val(col):
                if col in col_idx and len(row) > col_idx[col]:
                    return row[col_idx[col]].strip()
                return ""

            nuance = get_val('Nuance')
            libelle = get_val('Libellé Abrégé Liste')

            # Classifier
            if nuance:
                camp = classify_nuance(nuance)
            else:
                camp_by_liste = classify_by_liste(libelle)
                camp = camp_by_liste if camp_by_liste else "Droite"

            if camp == "Gauche":
                gauche_count += 1
            else:
                droite_count += 1

            # Écrire ligne réduite
            out_row = [
                get_val('id_election'),
                get_val('Code du département'),
                get_val('Code de la commune'),
                get_val('Code du b.vote'),
                libelle,
                get_val('Voix'),
                get_val('% Voix/Ins'),
                get_val('% Voix/Exp'),
                nuance,
                camp
            ]
            writer.writerow(out_row)

    print("\n" + "=" * 70)
    print("RÉSUMÉ DE LA CLASSIFICATION")
    print("=" * 70)
    print(f"  Total de lignes: {total:,}")
    print(f"  Gauche: {gauche_count:,} ({100*gauche_count/total:.1f}%)")
    print(f"  Droite: {droite_count:,} ({100*droite_count/total:.1f}%)")
    print(f"\n  Fichier créé: {OUTPUT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()

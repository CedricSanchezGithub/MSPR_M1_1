#!/usr/bin/env python3
"""
Script de classification des candidats en Gauche/Droite - VERSION 2
Gère les présidentielles (classification par nom de candidat)
LREM et la majorité présidentielle Macron sont classés à droite
"""

import csv
import sys

# Configuration
INPUT_FILE = "data_input/candidats_results.txt"
OUTPUT_FILE = "candidats_classified.txt"
SEPARATOR = ";"

# Classification par NOM DE CANDIDAT (pour les présidentielles)
CANDIDATS_GAUCHE = {
    # 2002
    'JOSPIN', 'HUE', 'CHEVÈNEMENT', 'CHEVENEMENT', 'MAMÈRE', 'MAMERE',
    'BESANCENOT', 'LAGUILLER', 'GLUCKSTEIN', 'TAUBIRA',
    # 2007
    'ROYAL', 'BUFFET', 'BOVÉ', 'BOVE', 'VOYNET', 'SCHIVARDI',
    # 2012
    'HOLLANDE', 'MÉLENCHON', 'MELENCHON', 'JOLY', 'POUTOU', 'ARTHAUD',
    # 2017
    'HAMON',
    # 2022
    'HIDALGO', 'JADOT', 'ROUSSEL',
}

CANDIDATS_DROITE = {
    # 2002
    'CHIRAC', 'LE PEN', 'BAYROU', 'LEPAGE', 'BOUTIN', 'MADELIN',
    'SAINT-JOSSE', 'MÉGRET', 'MEGRET',
    # 2007
    'SARKOZY', 'LE PEN', 'BAYROU', 'VILLIERS', 'NIHOUS',
    # 2012
    'SARKOZY', 'LE PEN', 'BAYROU', 'DUPONT-AIGNAN', 'CHEMINADE',
    # 2017
    'MACRON', 'LE PEN', 'FILLON', 'DUPONT-AIGNAN', 'LASSALLE',
    'ASSELINEAU', 'CHEMINADE',
    # 2022
    'MACRON', 'LE PEN', 'ZEMMOUR', 'PÉCRESSE', 'PECRESSE',
    'DUPONT-AIGNAN', 'LASSALLE',
}

# Candidats gauche présents dans toutes les élections
CANDIDATS_GAUCHE_ALL = {
    'MÉLENCHON', 'MELENCHON', 'POUTOU', 'ARTHAUD', 'BESANCENOT',
    'LAGUILLER', 'BUFFET', 'HUE', 'JOSPIN', 'ROYAL', 'HOLLANDE',
    'HAMON', 'JOLY', 'BOVÉ', 'BOVE', 'VOYNET', 'MAMÈRE', 'MAMERE',
    'GLUCKSTEIN', 'TAUBIRA', 'SCHIVARDI', 'CHEVÈNEMENT', 'CHEVENEMENT',
    'HIDALGO', 'JADOT', 'ROUSSEL',
}

# Classification des nuances politiques (pour les autres élections)
GAUCHE_NUANCES = {
    'EXG', 'LEXG', 'LXG', 'DXG', 'LO', 'LCR',
    'COM', 'LCOM', 'HUE',
    'FG', 'LFG', 'NUP', 'FI', 'LFI', 'PG', 'LPG', 'MELE',
    'SOC', 'LSOC', 'HOLL', 'JOSP', 'ROYA',
    'VEC', 'LVEC', 'ECO', 'LECO', 'LVEG', 'LVE', 'LEC', 'JOLY', 'BOVE',
    'DVG', 'LDVG', 'UG', 'LUG', 'LUGE', 'RDG', 'LRDG', 'LRG', 'LDG', 'PRG',
    'MDC', 'GAU',
    'BC-SOC', 'BC-COM', 'BC-FG', 'BC-ECO', 'BC-VEC', 'BC-DVG',
    'BC-EXG', 'BC-UG', 'BC-UGE', 'BC-FI', 'BC-RDG', 'BC-UCG', 'BC-PG',
    'ARTH', 'POUT', 'BUFF', 'GLUC', 'TAUB', 'SCHI', 'BESA', 'LAGU',
}

DROITE_NUANCES = {
    'EXD', 'LEXD', 'LXD', 'DXD', 'UXD',
    'FN', 'LFN', 'RN', 'LRN', 'MNR', 'MEGR', 'LEPA',
    'UMP', 'LUMP', 'LR', 'LLR', 'RPR', 'DVD', 'LDVD', 'DTE', 'SARK', 'CHIR',
    'UDF', 'LUDF', 'UDFD', 'DL', 'UDI', 'LUDI', 'CEN', 'PRV', 'BAYR', 'LPC', 'LCP', 'LCMD',
    'MPF', 'DLF', 'LDLF', 'DUPO', 'RPF', 'CPNT',
    'REM', 'LREM', 'ENS', 'LENS', 'MDM', 'LMDM', 'MODM', 'MAJ', 'LMAJ', 'HOR', 'ALLI', 'LMC',
    'REC', 'LREC',
    'BC-FN', 'BC-RN', 'BC-DVD', 'BC-UMP', 'BC-LR', 'BC-UD',
    'BC-UDI', 'BC-UC', 'BC-UCD', 'BC-REM', 'BC-MDM', 'BC-DLF',
    'BC-EXD', 'BC-UXD', 'BC-DVC',
    'DVC', 'LDVC', 'LDR', 'LDD', 'LUCD', 'FRN',
    'DIV', 'LDIV', 'NC', 'LNC', 'NCE', 'M-NC', 'AUT', 'LAUT',
    'REG', 'LREG', 'MNA', 'DSV', 'LDSV', 'BC-DSV', 'LDV', 'LUD', 'LCOP', 'PREP',
    'VILL', 'NIHO', 'VOYN', 'BOUT', 'MADE', 'CHEV', 'SAIN', 'MAME',
}


def classify_by_candidate_name(nom):
    """Classifie par nom de candidat (pour présidentielles)"""
    nom = nom.strip().upper()

    if not nom:
        return None

    # Vérifier les noms de gauche
    for candidat in CANDIDATS_GAUCHE_ALL:
        if candidat.upper() in nom or nom in candidat.upper():
            return "Gauche"

    # Vérifier les noms de droite
    for candidat in CANDIDATS_DROITE:
        if candidat.upper() in nom or nom in candidat.upper():
            return "Droite"

    return None


def classify_nuance(nuance):
    """Classifie une nuance politique en Gauche ou Droite"""
    nuance = nuance.strip().upper()

    if not nuance:
        return None

    if nuance in GAUCHE_NUANCES:
        return "Gauche"

    if nuance in DROITE_NUANCES:
        return "Droite"

    return "Droite"  # Défaut


def classify_by_liste(libelle):
    """Classification de secours par le nom de liste"""
    libelle = libelle.lower().strip()

    if not libelle:
        return None

    gauche_kw = ['insoumis', 'communiste', 'socialiste', 'écologi', 'vert',
                 'lutte ouvrière', 'npa', 'gauche', 'ouvrier', 'pcf', 'eelv',
                 'nupes', 'front de gauche']
    droite_kw = ['national', 'républicain', 'marche', 'renaissance', 'ensemble',
                 'modem', 'horizons', 'reconquête', 'zemmour', 'droite', 'ump',
                 'frexit', 'patriote', 'udi', 'centriste', 'fillon']

    for kw in gauche_kw:
        if kw in libelle:
            return "Gauche"
    for kw in droite_kw:
        if kw in libelle:
            return "Droite"
    return None


def main():
    print("=" * 70)
    print("CLASSIFICATION DES CANDIDATS V2 - GAUCHE / DROITE")
    print("(Gère les présidentielles par nom de candidat)")
    print("(LREM/Macron classé à DROITE)")
    print("=" * 70)

    total = 0
    gauche_count = 0
    droite_count = 0
    col_idx = {}

    # Stats par type d'élection
    stats = {}

    print(f"\nLecture de {INPUT_FILE}...")
    print(f"Écriture vers {OUTPUT_FILE}...")

    with open(INPUT_FILE, 'r', encoding='utf-8') as infile, \
         open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as outfile:

        reader = csv.reader(infile, delimiter=SEPARATOR)
        writer = csv.writer(outfile, delimiter=SEPARATOR)

        headers = next(reader)
        for i, h in enumerate(headers):
            col_idx[h] = i

        new_headers = headers + ["Camp"]
        writer.writerow(new_headers)

        for row in reader:
            total += 1

            if total % 2_000_000 == 0:
                print(f"  {total:,} lignes traitées...")

            def get_val(col):
                if col in col_idx and len(row) > col_idx[col]:
                    return row[col_idx[col]].strip()
                return ""

            election = get_val('id_election')
            nuance = get_val('Nuance')
            libelle = get_val('Libellé Abrégé Liste')
            nom = get_val('Nom')

            # Classification
            camp = None

            # 1. Pour les présidentielles, utiliser le nom du candidat
            if '_pres_' in election and nom:
                camp = classify_by_candidate_name(nom)

            # 2. Sinon, utiliser la nuance
            if camp is None and nuance:
                camp = classify_nuance(nuance)

            # 3. Sinon, utiliser le libellé de liste
            if camp is None and libelle:
                camp = classify_by_liste(libelle)

            # 4. Défaut: Droite
            if camp is None:
                camp = "Droite"

            # Compteurs
            if camp == "Gauche":
                gauche_count += 1
            else:
                droite_count += 1

            # Stats par élection
            year_type = election.split('_')[0] + '_' + election.split('_')[1] if '_' in election else election
            if year_type not in stats:
                stats[year_type] = {'gauche': 0, 'droite': 0}
            if camp == "Gauche":
                stats[year_type]['gauche'] += 1
            else:
                stats[year_type]['droite'] += 1

            new_row = row + [camp]
            writer.writerow(new_row)

    print("\n" + "=" * 70)
    print("RÉSUMÉ DE LA CLASSIFICATION")
    print("=" * 70)
    print(f"  Total de lignes: {total:,}")
    print(f"  Gauche: {gauche_count:,} ({100*gauche_count/total:.1f}%)")
    print(f"  Droite: {droite_count:,} ({100*droite_count/total:.1f}%)")

    print("\n  Par élection présidentielle:")
    for key in sorted(stats.keys()):
        if 'pres' in key:
            g = stats[key]['gauche']
            d = stats[key]['droite']
            t = g + d
            print(f"    {key}: Gauche {100*g/t:.1f}% / Droite {100*d/t:.1f}%")

    print(f"\n  Fichier créé: {OUTPUT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()

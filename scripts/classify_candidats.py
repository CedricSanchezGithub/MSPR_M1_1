#!/usr/bin/env python3
"""
Script de classification des candidats en Gauche/Droite
LREM et la majorité présidentielle Macron sont classés à droite
"""

import csv
import sys

# Configuration
INPUT_FILE = "data/input/candidats_results.txt"
OUTPUT_FILE = "data/output/candidats_classified.txt"
SEPARATOR = ";"

# Classification des nuances politiques
# GAUCHE: extrême gauche, communistes, socialistes, écologistes, insoumis, etc.
# DROITE: extrême droite, FN/RN, LR/UMP, centre-droit, LREM/Macron, etc.

GAUCHE_NUANCES = {
    # Extrême gauche
    'EXG', 'LEXG', 'LXG', 'DXG',
    'LO',      # Lutte Ouvrière
    'LCR',     # Ligue Communiste Révolutionnaire

    # Communistes
    'COM', 'LCOM',
    'HUE',     # Robert Hue

    # Front de Gauche / NUPES
    'FG', 'LFG',
    'NUP',     # NUPES
    'FI', 'LFI',  # France Insoumise
    'PG', 'LPG',  # Parti de Gauche
    'MELE',    # Mélenchon

    # Socialistes
    'SOC', 'LSOC',
    'HOLL',    # Hollande
    'JOSP',    # Jospin
    'ROYA',    # Royal

    # Écologistes
    'VEC', 'LVEC', 'ECO', 'LECO', 'LVEG', 'LVE', 'LEC',
    'JOLY',    # Eva Joly
    'BOVE',    # José Bové

    # Divers gauche
    'DVG', 'LDVG',
    'UG', 'LUG', 'LUGE',  # Union de la gauche
    'RDG', 'LRDG', 'LRG', 'LDG',  # Radicaux de gauche
    'PRG',     # Parti radical de gauche

    # Autres gauche
    'MDC',     # Mouvement des citoyens
    'GAU',     # Gauche

    # Binômes gauche
    'BC-SOC', 'BC-COM', 'BC-FG', 'BC-ECO', 'BC-VEC', 'BC-DVG',
    'BC-EXG', 'BC-UG', 'BC-UGE', 'BC-FI', 'BC-RDG', 'BC-UCG', 'BC-PG',
}

DROITE_NUANCES = {
    # Extrême droite
    'EXD', 'LEXD', 'LXD', 'DXD', 'UXD',
    'FN', 'LFN',      # Front National
    'RN', 'LRN',      # Rassemblement National
    'MNR',            # Mouvement National Républicain
    'MEGR',           # Mégret
    'LEPA',           # Le Pen

    # Droite traditionnelle
    'UMP', 'LUMP',
    'LR', 'LLR',      # Les Républicains
    'RPR',            # RPR
    'DVD', 'LDVD',    # Divers droite
    'DTE',            # Droite
    'SARK',           # Sarkozy
    'CHIR',           # Chirac

    # Centre-droit / UDF
    'UDF', 'LUDF', 'UDFD',
    'DL',             # Démocratie Libérale
    'UDI', 'LUDI',    # UDI
    'CEN',            # Centre
    'PRV',            # Parti radical valoisien
    'BAYR',           # Bayrou
    'LPC', 'LCP',     # ex-UDF
    'LCMD',           # Centre

    # Souverainistes droite
    'MPF',            # Mouvement pour la France
    'DLF', 'LDLF',    # Debout la France
    'DUPO',           # Dupont-Aignan
    'RPF',            # RPF
    'CPNT',           # Chasse Pêche Nature Traditions

    # MACRON / LREM / Majorité présidentielle (classé à droite comme demandé)
    'REM', 'LREM',    # La République En Marche
    'ENS', 'LENS',    # Ensemble (coalition Macron)
    'MDM', 'LMDM', 'MODM',  # MoDem
    'MAJ', 'LMAJ',    # Majorité présidentielle
    'HOR',            # Horizons
    'ALLI',           # Alliance centriste
    'LMC',            # Mouvement central
    'REC', 'LREC',    # Reconquête (Zemmour)

    # Binômes droite
    'BC-FN', 'BC-RN', 'BC-DVD', 'BC-UMP', 'BC-LR', 'BC-UD',
    'BC-UDI', 'BC-UC', 'BC-UCD', 'BC-REM', 'BC-MDM', 'BC-DLF',
    'BC-EXD', 'BC-UXD', 'BC-DVC',

    # Divers droite
    'DVC', 'LDVC',
    'LDR',            # Liste de droite
    'LDD',            # Liste divers droite
    'LUCD',           # Union centre-droit
    'FRN',            # Front
}

# Nuances "divers" qu'on doit classifier
# On va les mettre selon le contexte le plus probable
DIVERS_TO_DROITE = {
    'DIV', 'LDIV',    # Divers (souvent plus à droite dans les stats)
    'NC', 'LNC', 'NCE', 'M-NC',  # Non classé
    'AUT', 'LAUT',    # Autres
    'REG', 'LREG',    # Régionalistes (variable, mis à droite par défaut)
    'MNA',            # Mouvement national
    'DSV', 'LDSV', 'BC-DSV',  # Divers
    'LDV',            # Liste divers
    'LUD', 'LCOP',    # Union diverse
    'PREP',           # Préparatoire
    'LDIV',
}

# Candidats présidentiels - classification
CANDIDATS_GAUCHE = {
    'ARTH',    # Arthaud (LO)
    'POUT',    # Poutou (NPA)
    'BUFF',    # Buffet
    'GLUC',    # Gluckstein
    'TAUB',    # Taubira
    'SCHI',    # Schivardi
}

CANDIDATS_DROITE = {
    'VILL',    # Villiers
    'NIHO',    # Nihous
    'VOYN',    # Voynet (écolo mais...)
    'BOUT',    # Boutin
    'MADE',    # Madelin
    'CHEV',    # Chèvenement (souverainiste)
    'SAIN',    # Saint-Josse
    'MAME',    # Mamère
    'BESA',    # Besancenot - en fait gauche
    'LAGU',    # Laguiller - en fait gauche
}

# Correction: Besancenot et Laguiller sont à gauche
CANDIDATS_GAUCHE.add('BESA')
CANDIDATS_GAUCHE.add('LAGU')


def classify_nuance(nuance):
    """Classifie une nuance politique en Gauche ou Droite"""
    nuance = nuance.strip().upper()

    if not nuance:
        return "Droite"  # Par défaut si vide

    if nuance in GAUCHE_NUANCES or nuance in CANDIDATS_GAUCHE:
        return "Gauche"

    if nuance in DROITE_NUANCES or nuance in DIVERS_TO_DROITE or nuance in CANDIDATS_DROITE:
        return "Droite"

    # Par défaut, on met à droite (pour les nuances non reconnues)
    return "Droite"


def classify_by_liste(libelle_liste):
    """Classification de secours par le nom de liste si pas de nuance"""
    libelle = libelle_liste.lower().strip()

    # Mots-clés gauche
    gauche_keywords = [
        'insoumis', 'france insoumise', 'lfi', 'nupes',
        'communiste', 'pcf', 'front de gauche',
        'socialiste', 'ps ', 'parti socialiste',
        'écologi', 'eelv', 'vert', 'europe écologie',
        'lutte ouvrière', 'npa', 'anticapitaliste',
        'gauche', 'ouvrier', 'travailleur',
        'génération.s', 'place publique',
    ]

    # Mots-clés droite (incluant Macron)
    droite_keywords = [
        'national', 'rassemblement national', 'front national', 'fn', 'rn',
        'républicain', 'les républicains', 'ump', 'rpr',
        'en marche', 'renaissance', 'ensemble', 'lrem', 'rem',
        'modem', 'mouvement démocrate',
        'horizons', 'agir',
        'reconquête', 'zemmour',
        'debout la france', 'dupont-aignan',
        'udf', 'udi', 'centriste',
        'chasse', 'cpnt',
        'droite', 'souverain',
        'frexit', 'patriote',
    ]

    for kw in gauche_keywords:
        if kw in libelle:
            return "Gauche"

    for kw in droite_keywords:
        if kw in libelle:
            return "Droite"

    return None  # Pas de classification trouvée


def main():
    print("=" * 70)
    print("CLASSIFICATION DES CANDIDATS - GAUCHE / DROITE")
    print("(LREM/Macron classé à DROITE)")
    print("=" * 70)

    # Compteurs
    total = 0
    gauche_count = 0
    droite_count = 0

    # Index des colonnes
    col_idx = {}

    print(f"\nLecture de {INPUT_FILE}...")
    print(f"Écriture vers {OUTPUT_FILE}...")

    with open(INPUT_FILE, 'r', encoding='utf-8') as infile, \
         open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as outfile:

        reader = csv.reader(infile, delimiter=SEPARATOR)
        writer = csv.writer(outfile, delimiter=SEPARATOR)

        # Lire et écrire l'en-tête avec la nouvelle colonne
        headers = next(reader)
        for i, h in enumerate(headers):
            col_idx[h] = i

        # Ajouter la colonne "Camp"
        new_headers = headers + ["Camp"]
        writer.writerow(new_headers)

        # Traiter chaque ligne
        for row in reader:
            total += 1

            if total % 1_000_000 == 0:
                print(f"  {total:,} lignes traitées...")

            # Récupérer la nuance et le libellé liste
            nuance = ""
            libelle_liste = ""

            if 'Nuance' in col_idx and len(row) > col_idx['Nuance']:
                nuance = row[col_idx['Nuance']].strip()

            if 'Libellé Abrégé Liste' in col_idx and len(row) > col_idx['Libellé Abrégé Liste']:
                libelle_liste = row[col_idx['Libellé Abrégé Liste']].strip()

            # Classifier
            if nuance:
                camp = classify_nuance(nuance)
            else:
                # Essayer par le nom de liste
                camp_by_liste = classify_by_liste(libelle_liste)
                if camp_by_liste:
                    camp = camp_by_liste
                else:
                    camp = "Droite"  # Par défaut

            # Compter
            if camp == "Gauche":
                gauche_count += 1
            else:
                droite_count += 1

            # Écrire la ligne avec le camp
            new_row = row + [camp]
            writer.writerow(new_row)

    # Résumé
    print("\n" + "=" * 70)
    print("RÉSUMÉ DE LA CLASSIFICATION")
    print("=" * 70)
    print(f"  Total de lignes traitées: {total:,}")
    print(f"  Gauche: {gauche_count:,} ({100*gauche_count/total:.1f}%)")
    print(f"  Droite: {droite_count:,} ({100*droite_count/total:.1f}%)")
    print(f"\n  Fichier créé: {OUTPUT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()

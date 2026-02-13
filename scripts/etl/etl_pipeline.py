#!/usr/bin/env python3
"""
Pipeline ETL — Phase 2 Electio-Analytics
Filtre sur le département 34 (Hérault), normalise et charge dans SQLite.

Usage :
    python scripts/etl_pipeline.py
    python main.py etl
"""

import csv
import os
import sqlite3
import sys
import glob as glob_module

# Installer openpyxl si manquant (nécessaire pour lire les .xlsx)
try:
    import openpyxl
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])

import pandas as pd

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = "data/output/electio_herault.db"
DEPT = "34"

# Chemins des fichiers sources
ELECTIONS_FILE = "data/input/elections/candidats_results.txt"
POPULATION_FILE = "data/input/demographie/base-pop-historiques-1876-2023.xlsx"
NAISSANCES_FILE = "data/input/demographie/DS_ETAT_CIVIL_NAIS_COMMUNES_data.csv"
DECES_FILE = "data/input/demographie/DS_ETAT_CIVIL_DECES_COMMUNES_data.csv"
REVENUS_FILE = "data/input/economie/revenu-des-francais-a-la-commune-1765372688826.csv"
CSP_FILE = "data/input/economie/pop-act2554-csp-cd-6822.xlsx"
SECTEURS_FILE = "data/input/economie/pop-act2554-empl-sa-sexe-cd-6822.xlsx"
DIPLOMES_FILE = "data/input/education/base-cc-diplomes-formation-2022.CSV"
CSP_DIPLOME_FILE = "data/input/education/pop-act2554-csp-dipl-cd-6822.xlsx"
CATNAT_FILE = "data/input/environnement/catnat_gaspar.csv"
RISQUES_FILE = "data/input/environnement/risq_gaspar.csv"

COMPTES_FILES = sorted(glob_module.glob("data/input/economie/comptes_communes_*.csv"))

# ============================================================================
# CLASSIFICATION GAUCHE / DROITE (par nuance, pour municipales)
# ============================================================================

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


def classify_camp(id_election, nom, nuance, libelle_liste):
    """Classifie une liste/candidat en Gauche ou Droite (par nuance puis mots-clés)."""
    nuance = (nuance or "").strip().upper()
    libelle = (libelle_liste or "").strip().lower()

    # 1. Par code de nuance
    if nuance in GAUCHE_NUANCES:
        return "Gauche"
    if nuance in DROITE_NUANCES:
        return "Droite"

    # 2. Par mots-clés dans le libellé de liste
    if libelle:
        for kw in ['socialiste', 'communiste', 'gauche', 'écologi', 'vert',
                    'insoumis', 'ouvrier', 'citoyen', 'solidaire']:
            if kw in libelle:
                return "Gauche"
        for kw in ['national', 'républicain', 'droite', 'marche', 'renaissance',
                    'ensemble', 'majorité', 'libéral', 'conservat']:
            if kw in libelle:
                return "Droite"

    return "Droite"


# ============================================================================
# HELPERS
# ============================================================================

def normalize_codgeo(dep, commune):
    """Normalise un codgeo à partir de dep + commune (colonnes séparées)."""
    dep = str(dep).strip()
    commune = str(commune).strip().zfill(3)
    return dep + commune


def codgeo_from_single(val):
    """Normalise un codgeo depuis une seule colonne (zfill 5 caractères)."""
    return str(val).strip().zfill(5)


def is_dept34(codgeo):
    """Vérifie si un codgeo appartient au département 34."""
    return str(codgeo).startswith(DEPT)


def print_section(title):
    """Affiche un séparateur de section."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def print_count(table_name, conn):
    """Affiche le nombre de lignes dans une table."""
    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"  ✓ {table_name} : {count:,} lignes")
    return count


# ============================================================================
# CRÉATION DES TABLES (DDL)
# ============================================================================

DDL = """
CREATE TABLE IF NOT EXISTS communes (
    codgeo TEXT PRIMARY KEY,
    nom TEXT,
    departement TEXT
);

CREATE TABLE IF NOT EXISTS elections (
    codgeo TEXT,
    annee INTEGER,
    tour INTEGER,
    nom_candidat TEXT,
    prenom_candidat TEXT,
    nuance TEXT,
    voix INTEGER,
    pct_voix_inscrits REAL,
    pct_voix_exprimes REAL,
    camp TEXT,
    FOREIGN KEY (codgeo) REFERENCES communes(codgeo)
);

CREATE TABLE IF NOT EXISTS population (
    codgeo TEXT,
    annee INTEGER,
    population INTEGER,
    FOREIGN KEY (codgeo) REFERENCES communes(codgeo)
);

CREATE TABLE IF NOT EXISTS naissances_deces (
    codgeo TEXT,
    annee INTEGER,
    naissances INTEGER,
    deces INTEGER,
    FOREIGN KEY (codgeo) REFERENCES communes(codgeo)
);

CREATE TABLE IF NOT EXISTS revenus (
    codgeo TEXT,
    FOREIGN KEY (codgeo) REFERENCES communes(codgeo)
);

CREATE TABLE IF NOT EXISTS csp (
    codgeo TEXT,
    annee INTEGER,
    FOREIGN KEY (codgeo) REFERENCES communes(codgeo)
);

CREATE TABLE IF NOT EXISTS secteurs_activite (
    codgeo TEXT,
    annee INTEGER,
    FOREIGN KEY (codgeo) REFERENCES communes(codgeo)
);

CREATE TABLE IF NOT EXISTS diplomes (
    codgeo TEXT,
    FOREIGN KEY (codgeo) REFERENCES communes(codgeo)
);

CREATE TABLE IF NOT EXISTS csp_diplome (
    codgeo TEXT,
    annee INTEGER,
    FOREIGN KEY (codgeo) REFERENCES communes(codgeo)
);

CREATE TABLE IF NOT EXISTS comptes_communes (
    codgeo TEXT,
    annee INTEGER,
    population INTEGER,
    produits_fonctionnement REAL,
    charges_fonctionnement REAL,
    depenses_personnel REAL,
    depenses_investissement REAL,
    depenses_equipement REAL,
    dette REAL,
    dgf REAL,
    capacite_autofinancement REAL,
    impots_directs REAL,
    impots_indirects REAL,
    FOREIGN KEY (codgeo) REFERENCES communes(codgeo)
);

CREATE TABLE IF NOT EXISTS catnat (
    codgeo TEXT,
    risque TEXT,
    date_debut TEXT,
    date_fin TEXT,
    date_arrete TEXT,
    FOREIGN KEY (codgeo) REFERENCES communes(codgeo)
);

CREATE TABLE IF NOT EXISTS risques (
    codgeo TEXT,
    libelle_risque TEXT,
    code_risque TEXT,
    FOREIGN KEY (codgeo) REFERENCES communes(codgeo)
);

CREATE INDEX IF NOT EXISTS idx_elections_codgeo ON elections(codgeo);
CREATE INDEX IF NOT EXISTS idx_elections_annee ON elections(annee);
CREATE INDEX IF NOT EXISTS idx_population_codgeo ON population(codgeo);
CREATE INDEX IF NOT EXISTS idx_naissances_deces_codgeo ON naissances_deces(codgeo);
CREATE INDEX IF NOT EXISTS idx_csp_codgeo ON csp(codgeo);
CREATE INDEX IF NOT EXISTS idx_secteurs_codgeo ON secteurs_activite(codgeo);
CREATE INDEX IF NOT EXISTS idx_comptes_codgeo ON comptes_communes(codgeo);
CREATE INDEX IF NOT EXISTS idx_catnat_codgeo ON catnat(codgeo);
CREATE INDEX IF NOT EXISTS idx_risques_codgeo ON risques(codgeo);
"""


# ============================================================================
# ETL PAR TABLE
# ============================================================================

def etl_communes(conn):
    """Table communes : référentiel depuis population historique."""
    print_section("1/12 — communes (référentiel)")

    if not os.path.exists(POPULATION_FILE):
        print(f"  ⚠ Fichier manquant : {POPULATION_FILE}")
        return

    df = pd.read_excel(POPULATION_FILE, sheet_name='pop_1876_2023', header=5)

    # Filtrer département 34
    df['CODGEO'] = df['CODGEO'].astype(str).str.strip().str.zfill(5)
    df['codgeo'] = df['CODGEO']
    df = df[df['codgeo'].str.startswith(DEPT)]

    communes = df[['codgeo', 'LIBGEO', 'DEP']].copy()
    communes.columns = ['codgeo', 'nom', 'departement']
    communes = communes.drop_duplicates(subset='codgeo')

    # Insérer dans la table DDL (déjà créée avec PRIMARY KEY)
    conn.execute("DELETE FROM communes")
    for _, row in communes.iterrows():
        conn.execute("INSERT OR IGNORE INTO communes VALUES (?,?,?)",
                     (row['codgeo'], row['nom'], row['departement']))
    conn.commit()
    print_count('communes', conn)


def etl_elections(conn):
    """Table elections : fichier 2.3 GB, lecture ligne par ligne."""
    print_section("2/12 — elections (municipales, dept 34)")

    if not os.path.exists(ELECTIONS_FILE):
        print(f"  ⚠ Fichier manquant : {ELECTIONS_FILE}")
        return

    rows = []
    total_read = 0
    total_kept = 0
    col_idx = {}

    with open(ELECTIONS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        headers = next(reader)
        for i, h in enumerate(headers):
            col_idx[h] = i

        for row in reader:
            total_read += 1
            if total_read % 5_000_000 == 0:
                print(f"    {total_read:,} lignes lues...")

            if len(row) < len(headers):
                continue

            def get_val(col):
                if col in col_idx and len(row) > col_idx[col]:
                    return row[col_idx[col]].strip()
                return ""

            id_election = get_val('id_election')

            # Filtrer : municipales uniquement
            if '_muni_' not in id_election:
                continue

            # Filtrer : département 34
            dep = get_val('Code du département')
            if dep != DEPT:
                continue

            commune = get_val('Code de la commune')
            codgeo = normalize_codgeo(dep, commune)

            # Extraire année et tour
            parts = id_election.split('_')
            annee = int(parts[0]) if parts[0].isdigit() else 0
            tour = int(parts[2][1]) if len(parts) > 2 and parts[2].startswith('t') else 1

            nom = get_val('Nom')
            prenom = get_val('Prénom')
            nuance = get_val('Nuance')
            libelle_liste = get_val('Libellé Abrégé Liste')

            try:
                voix = int(get_val('Voix')) if get_val('Voix') else 0
            except ValueError:
                voix = 0

            try:
                pct_ins = float(get_val('% Voix/Ins')) if get_val('% Voix/Ins') else None
            except ValueError:
                pct_ins = None

            try:
                pct_exp = float(get_val('% Voix/Exp')) if get_val('% Voix/Exp') else None
            except ValueError:
                pct_exp = None

            camp = classify_camp(id_election, nom, nuance, libelle_liste)

            rows.append((codgeo, annee, tour, nom, prenom, nuance, voix,
                         pct_ins, pct_exp, camp))
            total_kept += 1

    print(f"  Lignes lues : {total_read:,}")
    print(f"  Lignes conservées (muni + dept 34) : {total_kept:,}")

    if rows:
        conn.executemany(
            "INSERT INTO elections VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
        conn.commit()

    print_count('elections', conn)


def etl_population(conn):
    """Table population : pivoter PMUNxxxx en lignes."""
    print_section("3/12 — population")

    if not os.path.exists(POPULATION_FILE):
        print(f"  ⚠ Fichier manquant : {POPULATION_FILE}")
        return

    df = pd.read_excel(POPULATION_FILE, sheet_name='pop_1876_2023', header=5)
    df['CODGEO'] = df['CODGEO'].astype(str).str.strip().str.zfill(5)
    df['codgeo'] = df['CODGEO']
    df = df[df['codgeo'].str.startswith(DEPT)]

    # Identifier les colonnes de population (PMUN, PSDC, PTOT)
    pmun_cols = [c for c in df.columns if c.startswith(('PMUN', 'PSDC', 'PTOT'))]

    rows = []
    for _, row in df.iterrows():
        codgeo = row['codgeo']
        for col in pmun_cols:
            # Extraire l'année du nom de colonne (PMUN2023, PSDC1999, PTOT1936)
            annee_str = ''.join(c for c in col if c.isdigit())
            annee = int(annee_str)
            pop = row[col]
            if pd.notna(pop):
                rows.append((codgeo, annee, int(pop)))

    if rows:
        conn.executemany("INSERT INTO population VALUES (?,?,?)", rows)
        conn.commit()

    print_count('population', conn)


def etl_naissances_deces(conn):
    """Table naissances_deces : joindre naissances + décès."""
    print_section("4/12 — naissances_deces")

    def read_etat_civil(filepath):
        """Lit un fichier d'état civil et retourne un dict {(codgeo, annee): valeur}."""
        if not os.path.exists(filepath):
            print(f"  ⚠ Fichier manquant : {filepath}")
            return {}

        data = {}
        df = pd.read_csv(filepath, sep=';', dtype=str)
        # Filtrer sur communes uniquement
        df = df[df['GEO_OBJECT'] == 'COM']
        df = df[df['GEO'].str.startswith(DEPT)]

        for _, row in df.iterrows():
            codgeo = str(row['GEO']).strip()
            annee = str(row['TIME_PERIOD']).strip()
            valeur = str(row['OBS_VALUE']).strip()
            if codgeo and annee and valeur:
                try:
                    data[(codgeo, int(annee))] = int(float(valeur))
                except ValueError:
                    pass
        return data

    naissances = read_etat_civil(NAISSANCES_FILE)
    deces = read_etat_civil(DECES_FILE)

    # Joindre sur (codgeo, annee)
    all_keys = set(naissances.keys()) | set(deces.keys())
    rows = []
    for (codgeo, annee) in sorted(all_keys):
        n = naissances.get((codgeo, annee))
        d = deces.get((codgeo, annee))
        rows.append((codgeo, annee, n, d))

    if rows:
        conn.executemany("INSERT INTO naissances_deces VALUES (?,?,?,?)", rows)
        conn.commit()

    print_count('naissances_deces', conn)


def etl_revenus(conn):
    """Table revenus : revenu des Français à la commune."""
    print_section("5/12 — revenus")

    if not os.path.exists(REVENUS_FILE):
        print(f"  ⚠ Fichier manquant : {REVENUS_FILE}")
        return

    # Détecter le séparateur
    with open(REVENUS_FILE, 'r', encoding='utf-8') as f:
        first_line = f.readline()

    sep = ';' if ';' in first_line and first_line.count(';') > 2 else ','

    df = pd.read_csv(REVENUS_FILE, sep=sep, dtype={'Code géographique': str})

    # Identifier la colonne codgeo
    codgeo_col = None
    for col in df.columns:
        if 'code' in col.lower() and 'géo' in col.lower():
            codgeo_col = col
            break
        if 'code' in col.lower() and 'geo' in col.lower():
            codgeo_col = col
            break

    if codgeo_col is None:
        # Essayer la première colonne
        codgeo_col = df.columns[0]
        print(f"  Colonne codgeo détectée par défaut : {codgeo_col}")

    df['codgeo'] = df[codgeo_col].apply(lambda x: str(x).strip().zfill(5))
    df = df[df['codgeo'].str.startswith(DEPT)]

    # Supprimer la colonne source et renommer
    cols_to_drop = [c for c in df.columns if c != 'codgeo' and ('code' in c.lower() or 'commune' in c.lower() or 'nom' in c.lower() or 'libellé' in c.lower() or 'libelle' in c.lower())]
    df = df.drop(columns=cols_to_drop, errors='ignore')

    # Nettoyer les noms de colonnes
    df.columns = [c.lower().strip().replace(' ', '_').replace("'", '').replace('é', 'e').replace('è', 'e') if c != 'codgeo' else c for c in df.columns]

    # Supprimer la table existante et recréer dynamiquement
    conn.execute("DROP TABLE IF EXISTS revenus")
    df.to_sql('revenus', conn, if_exists='replace', index=False)

    print_count('revenus', conn)


def _read_insee_xlsx(filepath, sheet_prefix='COM_', header_row=14):
    """Lit un fichier INSEE xlsx avec onglets COM_xxxx, retourne un dict {annee: DataFrame}.

    Ces fichiers INSEE ont une structure spécifique :
    - header_row contient les noms de colonnes (avec retours à la ligne)
    - La ligne suivante (row 0 des données) contient des codes internes → à sauter
    - Les colonnes 'Département' et 'Commune' sont séparées (dep 2 car + commune 3 car)
    """
    if not os.path.exists(filepath):
        print(f"  ⚠ Fichier manquant : {filepath}")
        return {}

    xl = pd.ExcelFile(filepath)
    results = {}

    for sheet in xl.sheet_names:
        if not sheet.startswith(sheet_prefix):
            continue

        annee_str = sheet.replace(sheet_prefix, '')
        try:
            annee = int(annee_str)
        except ValueError:
            continue

        try:
            df = pd.read_excel(filepath, sheet_name=sheet, header=header_row)
        except Exception as e:
            print(f"    ⚠ Impossible de lire l'onglet {sheet}: {e}")
            continue

        # Sauter la première ligne de données (codes internes)
        if len(df) > 0:
            first_val = str(df.iloc[0, 0]).strip()
            if first_val in ('RR', 'REG', 'CR', '') or not first_val[0].isdigit():
                df = df.iloc[1:].reset_index(drop=True)

        # Trouver les colonnes département et commune
        dep_col = None
        com_col = None
        for c in df.columns:
            c_lower = str(c).lower().replace('\n', ' ')
            if 'département' in c_lower and 'géographie courante' in c_lower and dep_col is None:
                dep_col = c
            elif 'commune' in c_lower and 'géographie courante' in c_lower and com_col is None:
                com_col = c

        if dep_col is None or com_col is None:
            print(f"    ⚠ Colonnes dep/commune non trouvées dans {sheet}")
            print(f"      Colonnes disponibles: {list(df.columns[:6])}")
            continue

        # Construire codgeo = dep (2 car.) + commune (3 car.)
        df['codgeo'] = df.apply(
            lambda r: str(r[dep_col]).strip().zfill(2) + str(r[com_col]).strip().zfill(3),
            axis=1
        )

        # Filtrer dept 34
        df = df[df['codgeo'].str.startswith(DEPT)]

        if len(df) == 0:
            continue

        # Supprimer les colonnes non numériques (métadonnées)
        cols_to_drop = []
        for c in df.columns:
            if c in ('codgeo', 'annee'):
                continue
            c_lower = str(c).lower().replace('\n', ' ')
            if any(kw in c_lower for kw in ['libellé', 'libelle', 'commune', 'région', 'region',
                                              'département', 'departement', 'indicateur', 'stabilité']):
                cols_to_drop.append(c)
        df = df.drop(columns=cols_to_drop, errors='ignore')

        df['annee'] = annee
        results[annee] = df

    return results


def etl_csp(conn):
    """Table csp : population active par CSP."""
    print_section("6/12 — csp")

    data = _read_insee_xlsx(CSP_FILE, 'COM_', 14)

    if not data:
        return

    all_dfs = []
    for annee, df in sorted(data.items()):
        all_dfs.append(df)

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        # Nettoyer les noms de colonnes
        combined.columns = [c.lower().strip().replace(' ', '_') if c not in ('codgeo', 'annee') else c for c in combined.columns]

        conn.execute("DROP TABLE IF EXISTS csp")
        combined.to_sql('csp', conn, if_exists='replace', index=False)

    print_count('csp', conn)


def etl_secteurs_activite(conn):
    """Table secteurs_activite : actifs par secteur d'activité × sexe."""
    print_section("7/12 — secteurs_activite")

    data = _read_insee_xlsx(SECTEURS_FILE, 'COM_', 14)

    if not data:
        return

    all_dfs = []
    for annee, df in sorted(data.items()):
        all_dfs.append(df)

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        combined.columns = [c.lower().strip().replace(' ', '_') if c not in ('codgeo', 'annee') else c for c in combined.columns]

        conn.execute("DROP TABLE IF EXISTS secteurs_activite")
        combined.to_sql('secteurs_activite', conn, if_exists='replace', index=False)

    print_count('secteurs_activite', conn)


def etl_diplomes(conn):
    """Table diplomes : niveaux de diplôme par commune."""
    print_section("8/12 — diplomes")

    if not os.path.exists(DIPLOMES_FILE):
        print(f"  ⚠ Fichier manquant : {DIPLOMES_FILE}")
        return

    # Détecter encodage et séparateur
    for enc in ['utf-8', 'latin-1', 'cp1252']:
        try:
            df = pd.read_csv(DIPLOMES_FILE, sep=';', encoding=enc, dtype={'CODGEO': str}, nrows=5)
            break
        except Exception:
            continue
    else:
        print("  ⚠ Impossible de lire le fichier diplômes")
        return

    df = pd.read_csv(DIPLOMES_FILE, sep=';', encoding=enc, dtype={'CODGEO': str})
    df['codgeo'] = df['CODGEO'].apply(codgeo_from_single)
    df = df[df['codgeo'].str.startswith(DEPT)]

    # Supprimer colonnes non numériques inutiles
    cols_to_drop = [c for c in df.columns if c != 'codgeo' and any(kw in c.upper() for kw in ['CODGEO', 'LIBGEO', 'REG', 'DEP', 'COM', 'ARR'])]
    df = df.drop(columns=cols_to_drop, errors='ignore')

    # Nettoyer les noms de colonnes
    df.columns = [c.lower().strip() if c != 'codgeo' else c for c in df.columns]

    conn.execute("DROP TABLE IF EXISTS diplomes")
    df.to_sql('diplomes', conn, if_exists='replace', index=False)

    print_count('diplomes', conn)


def etl_csp_diplome(conn):
    """Table csp_diplome : croisement CSP × diplôme."""
    print_section("9/12 — csp_diplome")

    data = _read_insee_xlsx(CSP_DIPLOME_FILE, 'COM_', 14)

    if not data:
        return

    all_dfs = []
    for annee, df in sorted(data.items()):
        all_dfs.append(df)

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        combined.columns = [c.lower().strip().replace(' ', '_') if c not in ('codgeo', 'annee') else c for c in combined.columns]

        conn.execute("DROP TABLE IF EXISTS csp_diplome")
        combined.to_sql('csp_diplome', conn, if_exists='replace', index=False)

    print_count('csp_diplome', conn)


def etl_comptes_communes(conn):
    """Table comptes_communes : finances locales."""
    print_section("10/12 — comptes_communes")

    if not COMPTES_FILES:
        print("  ⚠ Aucun fichier comptes_communes trouvé")
        return

    # Colonnes à extraire et renommer
    colonnes_renommage = {
        'an': 'annee',
        'pop': 'population',
        'prod': 'produits_fonctionnement',
        'charge': 'charges_fonctionnement',
        'perso': 'depenses_personnel',
        'depinv': 'depenses_investissement',
        'equip': 'depenses_equipement',
        'dette': 'dette',
        'dgf': 'dgf',
        'caf': 'capacite_autofinancement',
        'impo1': 'impots_directs',
        'impo2': 'impots_indirects',
    }

    all_dfs = []

    for filepath in COMPTES_FILES:
        print(f"    Lecture : {os.path.basename(filepath)}")

        # Détecter encodage
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(filepath, sep=';', encoding=enc, dtype=str, nrows=5)
                break
            except Exception:
                continue
        else:
            print(f"    ⚠ Impossible de lire {filepath}")
            continue

        df = pd.read_csv(filepath, sep=';', encoding=enc, dtype=str, low_memory=False)

        # Filtrer département 34 (dep peut être '34' ou '034')
        if 'dep' in df.columns:
            df = df[df['dep'].str.strip().str.lstrip('0') == DEPT]
        else:
            print(f"    ⚠ Colonne 'dep' non trouvée dans {filepath}")
            continue

        if len(df) == 0:
            continue

        # Construire codgeo = dep (sans zéro initial) + icom (3 car.)
        df['codgeo'] = df.apply(
            lambda r: str(r['dep']).strip().lstrip('0') + str(r['icom']).strip().zfill(3),
            axis=1
        )

        # Sélectionner et renommer les colonnes disponibles
        cols_available = {k: v for k, v in colonnes_renommage.items() if k in df.columns}
        cols_to_keep = ['codgeo'] + list(cols_available.keys())
        df = df[cols_to_keep]
        df = df.rename(columns=cols_available)

        # Convertir en numérique
        for col in df.columns:
            if col not in ('codgeo', 'annee'):
                df[col] = pd.to_numeric(df[col].str.replace(',', '.').str.strip(), errors='coerce')
            elif col == 'annee':
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

        all_dfs.append(df)

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        conn.execute("DROP TABLE IF EXISTS comptes_communes")
        combined.to_sql('comptes_communes', conn, if_exists='replace', index=False)

    print_count('comptes_communes', conn)


def etl_catnat(conn):
    """Table catnat : arrêtés de catastrophe naturelle."""
    print_section("11/12 — catnat")

    if not os.path.exists(CATNAT_FILE):
        print(f"  ⚠ Fichier manquant : {CATNAT_FILE}")
        return

    df = pd.read_csv(CATNAT_FILE, sep=';', dtype={'cod_commune': str})

    df['codgeo'] = df['cod_commune'].apply(lambda x: str(x).strip())
    df = df[df['codgeo'].str.startswith(DEPT)]

    result = df[['codgeo', 'lib_risque_jo', 'dat_deb', 'dat_fin', 'dat_pub_arrete']].copy()
    result.columns = ['codgeo', 'risque', 'date_debut', 'date_fin', 'date_arrete']

    result.to_sql('catnat', conn, if_exists='replace', index=False)
    print_count('catnat', conn)


def etl_risques(conn):
    """Table risques : inventaire des risques par commune."""
    print_section("12/12 — risques")

    if not os.path.exists(RISQUES_FILE):
        print(f"  ⚠ Fichier manquant : {RISQUES_FILE}")
        return

    df = pd.read_csv(RISQUES_FILE, sep=';', dtype=str)

    df['codgeo'] = df['cod_commune'].apply(lambda x: codgeo_from_single(str(x).strip()))
    df = df[df['codgeo'].str.startswith(DEPT)]

    result = df[['codgeo', 'lib_risque', 'num_risque']].copy()
    result.columns = ['codgeo', 'libelle_risque', 'code_risque']

    result.to_sql('risques', conn, if_exists='replace', index=False)
    print_count('risques', conn)


# ============================================================================
# VALIDATION
# ============================================================================

def validate(conn):
    """Validation finale : comptages et cohérence."""
    print_section("VALIDATION FINALE")

    tables = [
        'communes', 'elections', 'population', 'naissances_deces',
        'revenus', 'csp', 'secteurs_activite', 'diplomes',
        'csp_diplome', 'comptes_communes', 'catnat', 'risques'
    ]

    print("\n  Comptages par table :")
    total_tables = 0
    for table in tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"    {table:25s} : {count:>8,} lignes")
            total_tables += 1
        except Exception as e:
            print(f"    {table:25s} : ⚠ ERREUR ({e})")

    print(f"\n  Tables présentes : {total_tables}/{len(tables)}")

    # Vérifier les communes
    try:
        n_communes = conn.execute("SELECT COUNT(*) FROM communes").fetchone()[0]
        print(f"\n  Communes du 34 : {n_communes}")
    except Exception:
        pass

    # Vérifier les années des élections
    try:
        annees = conn.execute("SELECT DISTINCT annee FROM elections ORDER BY annee").fetchall()
        annees_str = ', '.join(str(a[0]) for a in annees)
        print(f"  Années d'élections : {annees_str}")
    except Exception:
        pass

    # Vérifier la cohérence des jointures
    try:
        orphans = conn.execute("""
            SELECT COUNT(DISTINCT e.codgeo)
            FROM elections e
            LEFT JOIN communes c ON e.codgeo = c.codgeo
            WHERE c.codgeo IS NULL
        """).fetchone()[0]
        if orphans > 0:
            print(f"  ⚠ {orphans} codgeo dans elections sans correspondance dans communes")
        else:
            print("  ✓ Toutes les communes des elections sont dans le référentiel")
    except Exception:
        pass


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("  PIPELINE ETL — ELECTIO-ANALYTICS")
    print("  Département : Hérault (34)")
    print("=" * 60)

    # Créer le répertoire de sortie
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Supprimer la base existante
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"\n  Base existante supprimée : {DB_PATH}")

    # Connexion SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=OFF")

    # Créer les tables
    print("\n  Création des tables...")
    conn.executescript(DDL)

    # ETL par table (ordre logique)
    etl_communes(conn)
    etl_elections(conn)
    etl_population(conn)
    etl_naissances_deces(conn)
    etl_revenus(conn)
    etl_csp(conn)
    etl_secteurs_activite(conn)
    etl_diplomes(conn)
    etl_csp_diplome(conn)
    etl_comptes_communes(conn)
    etl_catnat(conn)
    etl_risques(conn)

    # Validation
    validate(conn)

    conn.close()

    print(f"\n{'=' * 60}")
    print(f"  BASE CRÉÉE : {DB_PATH}")
    size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
    print(f"  Taille : {size_mb:.1f} MB")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

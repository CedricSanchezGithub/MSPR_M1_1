"""
📊 Graphes de Classification — Données RÉELLES
Electio-Analytics — Hérault (34) — MSPR Big Data

Récupère les données directement depuis :
  - data.gouv.fr  → API REST (élections, revenus, population, catnat)
  - INSEE         → URL directe (naissances, décès)

Usage :
    pip install requests pandas numpy matplotlib seaborn scikit-learn openpyxl
    python classification_graphes_real.py
"""

import io
import os
import sys
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import learning_curve
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    roc_curve, auc,
    precision_recall_curve,
)
from sklearn.preprocessing import label_binarize

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
DEPT         = "34"
OUTPUT_DIR   = "graphiques"
ANNEES_TRAIN = [2008, 2014]
ANNEE_TEST   = 2020
os.makedirs(OUTPUT_DIR, exist_ok=True)

C_GAUCHE = '#e74c3c'
C_DROITE = '#3498db'
C_NEUTRE = '#bdc3c7'

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Electio-Analytics/1.0 (MSPR)"})

# ─────────────────────────────────────────────
# CLASSIFICATION GAUCHE / DROITE
# (identique à etl_pipeline.py)
# ─────────────────────────────────────────────
GAUCHE_NUANCES = {
    'EXG','LEXG','LXG','DXG','LO','LCR','COM','LCOM','HUE',
    'FG','LFG','NUP','FI','LFI','PG','LPG','MELE',
    'SOC','LSOC','VEC','LVEC','ECO','LECO','DVG','LDVG',
    'UG','LUG','RDG','LRDG','PRG','MDC','GAU',
}
DROITE_NUANCES = {
    'EXD','LEXD','FN','LFN','RN','LRN','UMP','LUMP','LR','LLR',
    'DVD','LDVD','UDF','UDI','LUDI','REM','LREM','ENS','LENS',
    'MDM','LMDM','DVC','LDVC','DIV','LDIV','REG','LREG',
}

def classify_camp(nuance, libelle=""):
    n = (nuance or "").strip().upper()
    l = (libelle or "").strip().lower()
    if n in GAUCHE_NUANCES: return "Gauche"
    if n in DROITE_NUANCES: return "Droite"
    for kw in ['socialiste','communiste','gauche','écologi','insoumis']:
        if kw in l: return "Gauche"
    for kw in ['national','républicain','droite','renaissance','ensemble','libéral']:
        if kw in l: return "Droite"
    return "Droite"


# ─────────────────────────────────────────────
# HELPERS API
# ─────────────────────────────────────────────
def get_datagouv_resources(slug):
    """Récupère les ressources d'un dataset data.gouv.fr."""
    url = f"https://www.data.gouv.fr/api/1/datasets/{slug}/"
    try:
        r = SESSION.get(url, timeout=30)
        r.raise_for_status()
        return r.json().get("resources", [])
    except Exception as e:
        print(f"  ⚠ API data.gouv.fr '{slug}' : {e}")
        return []

def find_resource(resources, keywords):
    """Trouve la ressource la plus pertinente par mots-clés."""
    kws = [k.lower() for k in keywords]
    for res in resources:
        title = res.get("title", "").lower()
        if all(kw in title for kw in kws):
            return res
    for res in resources:
        title = res.get("title", "").lower()
        if any(kw in title for kw in kws):
            return res
    return resources[0] if resources else None

def download_csv(url, sep=';', encoding='utf-8', dtype=None, nrows=None):
    """Télécharge un CSV depuis une URL et retourne un DataFrame."""
    print(f"    ↓ {url[:80]}...")
    try:
        r = SESSION.get(url, timeout=120, stream=True)
        r.raise_for_status()
        content = r.content
        for enc in [encoding, 'latin-1', 'utf-8', 'cp1252']:
            try:
                return pd.read_csv(
                    io.BytesIO(content), sep=sep,
                    encoding=enc, dtype=dtype,
                    nrows=nrows, low_memory=False
                )
            except Exception:
                continue
        print("  ⚠ Impossible de décoder le CSV")
        return pd.DataFrame()
    except Exception as e:
        print(f"  ⚠ Échec téléchargement : {e}")
        return pd.DataFrame()


# ─────────────────────────────────────────────
# 1. CHARGEMENT DES DONNÉES RÉELLES
# ─────────────────────────────────────────────

def charger_elections():
    """
    Charge les résultats électoraux municipaux du Hérault (34)
    depuis data.gouv.fr — fichier candidats_results (~2.1 GB).
    Lit en streaming ligne par ligne pour filtrer uniquement le dept 34.
    """
    print("\n[1/5] Élections municipales Hérault (34)...")

    resources = get_datagouv_resources("donnees-des-elections-agregees")

    if not resources:
        print("  ⚠ API data.gouv.fr non accessible")
        return pd.DataFrame()

    print(f"  {len(resources)} ressource(s) disponible(s) :")
    for res in resources[:8]:
        print(f"    - {res.get('title','?')[:65]} [{res.get('format','?')}]")

    # Chercher le fichier candidats (le plus gros, ~2.1GB)
    res = find_resource(resources, ["candidat"])
    if not res:
        res = find_resource(resources, ["résultats"])
    if not res:
        res = max(resources, key=lambda r: r.get("filesize", 0) or 0)

    url = res["url"]
    print(f"\n  URL : {url[:90]}")
    print(f"  Taille : {(res.get('filesize') or 0) / 1e9:.2f} GB")
    print("  Streaming en cours (peut prendre 3-10 min selon connexion)...")

    import csv as csv_module
    rows  = []
    total = 0
    col_idx = {}

    try:
        r = SESSION.get(url, stream=True, timeout=600)
        r.raise_for_status()

        # Détecter l'encodage depuis les headers
        enc = r.encoding or 'utf-8'

        sep = ','  # candidats_results.csv utilise des virgules
        buffer = b""
        for chunk in r.iter_content(chunk_size=1_048_576):
            buffer += chunk
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                try:
                    decoded = line.decode(enc, errors='replace').rstrip('\r')
                except Exception:
                    decoded = line.decode('latin-1', errors='replace').rstrip('\r')

                try:
                    row = next(csv_module.reader([decoded], delimiter=sep))
                except Exception:
                    continue

                # En-tête : détecter séparateur et colonnes
                if total == 0 and not col_idx:
                    if decoded.count(';') > decoded.count(','):
                        sep = ';'
                    row = next(csv_module.reader([decoded], delimiter=sep))
                    col_idx = {h.strip(): j for j, h in enumerate(row)}
                    total = 1
                    print(f"  Séparateur : '{sep}'")
                    print(f"  Colonnes   : {list(col_idx.keys())[:10]}")
                    # Vérifier les colonnes critiques
                    for col_check in ['id_election', 'Code du département', 'code_departement', 'dep']:
                        if col_check in col_idx:
                            print(f"  Colonne dept trouvée : '{col_check}'")
                            break
                    continue

                total += 1
                if total % 1_000_000 == 0:
                    print(f"    {total:,} lignes lues — {len(rows)} conservées...")

                def get_val(col):
                    idx = col_idx.get(col, -1)
                    return row[idx].strip() if 0 <= idx < len(row) else ""

                id_election = get_val('id_election')
                if not id_election:
                    id_election = get_val('id_election ')  # trailing space
                if '_muni_' not in id_election:
                    continue

                # Essayer plusieurs noms de colonne pour le département
                dep = (get_val('Code du département')
                       or get_val('code_departement')
                       or get_val('dep')
                       or get_val('DEP'))
                # Normaliser : "034" ou "34" → "34"
                dep = dep.lstrip('0') or '0'
                if dep != DEPT:
                    continue

                # Extraire commune
                commune = (get_val('Code de la commune')
                           or get_val('code_commune')
                           or get_val('commune'))
                codgeo  = DEPT + commune.zfill(3)

                parts = id_election.split('_')
                try:
                    annee = int(parts[0])
                except Exception:
                    continue

                # Garder 2008, 2014, 2020 uniquement
                if annee not in (2008, 2014, 2020):
                    continue

                tour = 1
                if len(parts) > 2 and parts[2].startswith('t'):
                    try: tour = int(parts[2][1])
                    except Exception: pass

                nuance  = (get_val('Nuance')
                           or get_val('nuance')
                           or get_val('code_nuance'))
                libelle = (get_val('Libellé Abrégé Liste')
                           or get_val('libelle_liste')
                           or get_val('libelle'))
                camp    = classify_camp(nuance, libelle)

                try:
                    voix = int(get_val('Voix') or get_val('voix') or get_val('nb_voix') or 0)
                except Exception:
                    voix = 0

                rows.append({
                    'codgeo': codgeo, 'annee': annee,
                    'tour': tour, 'camp': camp, 'voix': voix
                })

        print(f"  ✅ {total:,} lignes lues — {len(rows):,} conservées (muni + dept 34)")

    except requests.exceptions.Timeout:
        print(f"  ⚠ Timeout — {len(rows):,} lignes récupérées avant interruption")
        if not rows:
            return pd.DataFrame()
    except Exception as e:
        print(f"  ⚠ Erreur : {e}")
        if not rows:
            return pd.DataFrame()

    return pd.DataFrame(rows)


def charger_population():
    """
    Charge la population historique depuis data.gouv.fr.
    Fichier : base-pop-historiques-1876-2023.xlsx
    """
    print("\n[2/5] Population historique...")

    # URLs directes connues du fichier INSEE sur data.gouv.fr
    urls_directes = [
        "https://www.insee.fr/fr/statistiques/fichier/6689607/base-pop-historiques-1876-2023.xlsx",
        "https://static.data.gouv.fr/resources/bases-de-donnees-et-fichiers-details-du-recensement-de-la-population/base-pop-historiques-1876-2023.xlsx",
    ]

    # Essayer d'abord via l'API data.gouv.fr
    resources = get_datagouv_resources(
        "bases-de-donnees-et-fichiers-details-du-recensement-de-la-population"
    )
    print(f"  {len(resources)} ressource(s) disponible(s) :")
    for res in resources[:6]:
        print(f"    - {res.get('title','?')[:65]} [{res.get('format','?')}]")

    res = find_resource(resources, ["historique"])
    if not res:
        res = find_resource(resources, ["1876"])
    if not res:
        # Chercher tout fichier xlsx
        res = next((r for r in resources if r.get('format','').lower() == 'xlsx'), None)

    if res:
        urls_directes.insert(0, res["url"])

    for url in urls_directes:
        print(f"  Essai : {url[:80]}")
        try:
            r = SESSION.get(url, timeout=120)
            r.raise_for_status()
            content = r.content

            # Vérifier que c'est bien un fichier Excel (magic bytes)
            if not (content[:4] == b'PK\x03\x04' or content[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
                print(f"    ⚠ Ce n'est pas un fichier Excel (reçu : {content[:50]}...)")
                continue

            df = pd.read_excel(
                io.BytesIO(content),
                sheet_name='pop_1876_2023',
                header=5,
                engine='openpyxl'
            )
            df['CODGEO'] = df['CODGEO'].astype(str).str.strip().str.zfill(5)
            df = df[df['CODGEO'].str.startswith(DEPT)]

            pmun_cols = [c for c in df.columns if str(c).startswith('PMUN')]
            rows = []
            for _, row in df.iterrows():
                for col in pmun_cols:
                    annee_str = ''.join(c for c in str(col) if c.isdigit())
                    annee = int(annee_str)
                    pop   = row[col]
                    if pd.notna(pop):
                        rows.append({'codgeo': row['CODGEO'], 'annee': annee,
                                     'population': int(pop)})

            df_pop = pd.DataFrame(rows)
            print(f"  ✅ {len(df_pop):,} lignes population — {df['CODGEO'].nunique()} communes")
            return df_pop

        except Exception as e:
            print(f"    ⚠ Échec : {e}")
            continue

    print("  ⚠ Population non disponible — feature ignorée")
    return pd.DataFrame()


def charger_revenus():
    """
    Charge les revenus médians par commune depuis data.gouv.fr.
    Le fichier utilise des codes SDMX comme colonnes — on détecte
    automatiquement la colonne codgeo et la colonne revenu médian.
    """
    print("\n[3/5] Revenus par commune...")

    resources = get_datagouv_resources("revenu-des-francais-a-la-commune")
    if not resources:
        print("  ⚠ Dataset revenus introuvable")
        return pd.DataFrame()

    # Afficher toutes les ressources disponibles pour debug
    print(f"  {len(resources)} ressource(s) disponible(s)")
    for res in resources[:5]:
        print(f"    - {res.get('title','?')[:70]} [{res.get('format','?')}]")

    # Prendre la première ressource CSV
    res = find_resource(resources, ["csv"]) or resources[0]

    df = download_csv(res["url"], sep=';')
    if df.empty:
        # Essayer avec virgule comme séparateur
        df = download_csv(res["url"], sep=',')
    if df.empty:
        return df

    print(f"  Colonnes disponibles : {df.columns.tolist()[:10]}")
    print(f"  Aperçu première ligne : {df.iloc[0].tolist()[:5]}")

    # Chercher la colonne codgeo parmi toutes les colonnes
    codgeo_col = None
    for c in df.columns:
        cl = c.lower()
        if any(kw in cl for kw in ['codgeo', 'code_geo', 'code geo',
                                    'insee', 'commune', 'geo_code',
                                    '[geo]', 'geo']):
            # Vérifier que les valeurs ressemblent à des codes INSEE (5 chiffres)
            sample = df[c].astype(str).str.strip().head(20)
            if sample.str.match(r'^\d{4,6}$').mean() > 0.5:
                codgeo_col = c
                break

    if codgeo_col is None:
        # Chercher dans toutes les colonnes la première avec des codes INSEE
        for c in df.columns:
            sample = df[c].astype(str).str.strip().head(50)
            if sample.str.match(r'^\d{5}$').mean() > 0.5:
                codgeo_col = c
                break

    if codgeo_col is None:
        print(f"  ⚠ Colonne codgeo introuvable. Colonnes : {df.columns.tolist()}")
        return pd.DataFrame()

    print(f"  Colonne codgeo détectée : '{codgeo_col}'")
    df['codgeo'] = df[codgeo_col].astype(str).str.strip().str.zfill(5)
    df = df[df['codgeo'].str.startswith(DEPT)]
    print(f"  Lignes pour dept {DEPT} : {len(df)}")

    # Chercher colonne revenu médian
    rev_col = None
    for kw in ['median', 'med', 'q2', 'd5', 'revenu', 'disp', 'niveau_vie']:
        for c in df.columns:
            if kw in c.lower() and c != codgeo_col:
                # Vérifier que c'est numérique
                vals = pd.to_numeric(df[c], errors='coerce')
                if vals.notna().mean() > 0.3:
                    rev_col = c
                    break
        if rev_col:
            break

    if rev_col is None:
        # Chercher explicitement la médiane dans les noms de colonnes
        for c in df.columns:
            if 'médiane' in c.lower() or 'mediane' in c.lower() or 'median' in c.lower():
                rev_col = c
                break

    if rev_col is None:
        # Prendre la première colonne numérique avec valeurs > 1000 (revenus en €)
        for c in df.columns:
            if c == 'codgeo':
                continue
            vals = pd.to_numeric(df[c], errors='coerce')
            if vals.notna().mean() > 0.5 and vals.median() > 1000:
                rev_col = c
                break

    if rev_col:
        df = df[['codgeo', rev_col]].rename(columns={rev_col: 'revenu_median'})
        df['revenu_median'] = pd.to_numeric(df['revenu_median'], errors='coerce')
        print(f"  ✅ {len(df)} communes — colonne revenu : '{rev_col}'")
    else:
        print(f"  ⚠ Colonne revenu médian introuvable")
        df = df[['codgeo']]

    return df


def charger_catnat():
    """
    Charge les arrêtés CatNat depuis l'API Géorisques v1 (sans token)
    en paginant sur le département 34.
    Fallback : data.gouv.fr dataset dédié CatNat.
    """
    print("\n[4/5] CatNat GASPAR...")

    # ── Méthode 1 : API Géorisques v1 (sans token, pagination par dept)
    try:
        url  = "https://georisques.gouv.fr/api/v1/gaspar/catnat"
        rows = []
        page = 1
        while True:
            params = {"page": page, "page_size": 1000, "code_insee_commune": f"{DEPT}*"}
            r = SESSION.get(url, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            items = data.get("data", [])
            if not items:
                break
            for item in items:
                codgeo = str(item.get("code_insee_commune", "")).strip()
                if codgeo.startswith(DEPT):
                    rows.append({"codgeo": codgeo})
            if page >= data.get("total_pages", 1):
                break
            page += 1

        if rows:
            df_cat = pd.DataFrame(rows).groupby("codgeo").size().reset_index(name="nb_catnat")
            print(f"  ✅ API Géorisques : {len(df_cat)} communes avec CatNat")
            return df_cat
    except Exception as e:
        print(f"  ⚠ API Géorisques v1 : {e}")

    # ── Méthode 2 : data.gouv.fr dataset CatNat dédié
    try:
        print("  → Fallback data.gouv.fr CatNat...")
        resources = get_datagouv_resources("risques-arretes-catastrophes-naturelles")
        res = find_resource(resources, ["catnat"]) or (resources[0] if resources else None)
        if res:
            df = download_csv(res["url"], sep=";", dtype={"cod_commune": str})
            if not df.empty:
                col = next((c for c in df.columns if "commune" in c.lower()), None)
                if col:
                    df["codgeo"] = df[col].astype(str).str.strip().str.zfill(5)
                    df = df[df["codgeo"].str.startswith(DEPT)]
                    df_cat = df.groupby("codgeo").size().reset_index(name="nb_catnat")
                    print(f"  ✅ data.gouv.fr : {len(df_cat)} communes avec CatNat")
                    return df_cat
    except Exception as e:
        print(f"  ⚠ Fallback CatNat : {e}")

    # ── Méthode 3 : ZIP Géorisques (extrait catnat_gaspar.csv)
    try:
        import zipfile
        print("  → Fallback ZIP Géorisques...")
        zip_url = "https://files.georisques.fr/GASPAR/gaspar.zip"
        r = SESSION.get(zip_url, timeout=120, stream=True)
        r.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(r.content))
        csv_name = next((n for n in z.namelist() if "catnat" in n.lower()), None)
        if csv_name:
            with z.open(csv_name) as f:
                df = pd.read_csv(f, sep=";", dtype={"cod_commune": str}, low_memory=False)
            df["codgeo"] = df["cod_commune"].astype(str).str.strip()
            df = df[df["codgeo"].str.startswith(DEPT)]
            df_cat = df.groupby("codgeo").size().reset_index(name="nb_catnat")
            print(f"  ✅ ZIP : {len(df_cat)} communes avec CatNat")
            return df_cat
    except Exception as e:
        print(f"  ⚠ Fallback ZIP : {e}")

    print("  ⚠ CatNat non disponible — feature ignorée")
    return pd.DataFrame()


def charger_naissances():
    """
    Charge les naissances par commune.
    Méthode 1 : data.gouv.fr (dataset naissances communes)
    Méthode 2 : INSEE sdmx API
    """
    print("\n[5/5] Naissances par commune...")

    # ── Méthode 1 : data.gouv.fr
    try:
        print("  → data.gouv.fr naissances...")
        resources = get_datagouv_resources("nombre-de-naissances-par-commune")
        res = find_resource(resources, ["commune", "data"]) or (resources[0] if resources else None)
        if res:
            df = download_csv(res["url"], sep=";", dtype=str)
            if not df.empty and "GEO" in df.columns:
                if "GEO_OBJECT" in df.columns:
                    df = df[df["GEO_OBJECT"] == "COM"]
                df["codgeo"]     = df["GEO"].astype(str).str.strip()
                df               = df[df["codgeo"].str.startswith(DEPT)]
                df["annee"]      = pd.to_numeric(df["TIME_PERIOD"], errors="coerce")
                df["naissances"] = pd.to_numeric(df["OBS_VALUE"],   errors="coerce")
                df = df[["codgeo", "annee", "naissances"]].dropna()
                print(f"  ✅ {len(df):,} lignes naissances")
                return df
    except Exception as e:
        print(f"  ⚠ data.gouv.fr naissances : {e}")

    # ── Méthode 2 : INSEE SDMX API (naissances dept 34 par commune)
    try:
        print("  → INSEE SDMX API...")
        url = (
            "https://api.insee.fr/series/BDM/V1/data/"
            "SERIE_BDM/001564169"  # Naissances vivantes par commune
        )
        r = SESSION.get(url, timeout=30,
                        headers={"Accept": "application/json"})
        if r.status_code == 200:
            # Parser la réponse JSON INSEE
            data = r.json()
            rows = []
            for obs in data.get("serieList", []):
                codgeo = obs.get("idBank", "")
                if codgeo.startswith(DEPT):
                    for period, val in obs.get("observations", {}).items():
                        try:
                            annee = int(period[:4])
                            rows.append({"codgeo": codgeo, "annee": annee,
                                         "naissances": float(val[0])})
                        except Exception:
                            pass
            if rows:
                df = pd.DataFrame(rows)
                print(f"  ✅ INSEE SDMX : {len(df):,} lignes")
                return df
    except Exception as e:
        print(f"  ⚠ INSEE SDMX : {e}")

    print("  ⚠ Naissances non disponibles — feature ignorée")
    return pd.DataFrame()


# ─────────────────────────────────────────────
# 2. CONSTRUCTION DU DATASET ML
# ─────────────────────────────────────────────

def construire_dataset():
    """Joint toutes les sources pour produire X, y par commune × année."""
    print("\n" + "="*55)
    print("  CONSTRUCTION DU DATASET ML")
    print("="*55)

    # ── Charger toutes les sources
    df_elec  = charger_elections()
    df_pop   = charger_population()
    df_rev   = charger_revenus()
    df_cat   = charger_catnat()
    df_nais  = charger_naissances()

    if df_elec.empty:
        print("\n❌ Données électorales manquantes — impossible de construire le dataset")
        sys.exit(1)

    # ── Label : camp majoritaire par commune × année
    df_elec_t1 = df_elec[df_elec['tour'] == 1]
    idx    = df_elec_t1.groupby(['codgeo', 'annee'])['voix'].idxmax()
    df     = df_elec_t1.loc[idx, ['codgeo', 'annee', 'camp']].copy()
    df.columns = ['codgeo', 'annee', 'label']
    df['label_bin'] = (df['label'] == 'Droite').astype(int)

    # ── Population (année la plus proche de l'élection)
    if not df_pop.empty:
        df_pop['annee_elec'] = df_pop['annee'].apply(
            lambda a: min(ANNEES_TRAIN + [ANNEE_TEST], key=lambda e: abs(e - a))
        )
        df_pop_agg = (df_pop.groupby(['codgeo', 'annee_elec'])['population']
                      .mean().reset_index()
                      .rename(columns={'annee_elec': 'annee'}))
        df = df.merge(df_pop_agg, on=['codgeo', 'annee'], how='left')

    # ── Revenus
    if not df_rev.empty and 'revenu_median' in df_rev.columns:
        df = df.merge(df_rev[['codgeo', 'revenu_median']], on='codgeo', how='left')

    # ── CatNat
    if not df_cat.empty:
        df = df.merge(df_cat, on='codgeo', how='left')

    # ── Naissances
    if not df_nais.empty:
        df_nais['annee_elec'] = df_nais['annee'].apply(
            lambda a: min(ANNEES_TRAIN + [ANNEE_TEST], key=lambda e: abs(e - a))
        )
        df_nais_agg = (df_nais.groupby(['codgeo', 'annee_elec'])['naissances']
                       .sum().reset_index()
                       .rename(columns={'annee_elec': 'annee'}))
        df = df.merge(df_nais_agg, on=['codgeo', 'annee'], how='left')

    # ── Features disponibles
    features_candidates = ['population', 'revenu_median', 'nb_catnat', 'naissances']
    features = [f for f in features_candidates if f in df.columns]

    print(f"\n  ✅ Dataset final : {len(df)} observations")
    print(f"     Features      : {features}")
    print(f"     Labels        : {df['label'].value_counts().to_dict()}")
    print(f"     Par année     : {df.groupby('annee').size().to_dict()}")

    # Imputer les valeurs manquantes
    df[features] = df[features].fillna(df[features].median())

    return df, features


# ─────────────────────────────────────────────
# 3. GRAPHES (identiques au script original)
# ─────────────────────────────────────────────

def plot_confusion_matrix(y_test, y_pred):
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(7, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='RdBu_r',
                xticklabels=['Gauche', 'Droite'],
                yticklabels=['Gauche', 'Droite'],
                linewidths=2, linecolor='white',
                annot_kws={'size': 20, 'weight': 'bold'})
    acc = (np.array(y_test) == np.array(y_pred)).mean()
    plt.title(f'Matrice de Confusion — Test {ANNEE_TEST}\nAccuracy : {acc:.1%}',
              fontsize=14, fontweight='bold')
    plt.ylabel('Valeur Réelle')
    plt.xlabel('Valeur Prédite')
    plt.tight_layout()
    path = f'{OUTPUT_DIR}/1_matrice_confusion.png'
    plt.savefig(path, dpi=150)
    plt.show()
    print(f"✅ {path}")


def plot_roc_curve(y_test, y_proba):
    fpr, tpr, _ = roc_curve(y_test, y_proba[:, 1])
    roc_auc = auc(fpr, tpr)
    plt.figure(figsize=(7, 6))
    plt.plot(fpr, tpr, color=C_DROITE, lw=2,
             label=f'Random Forest (AUC = {roc_auc:.2f})')
    plt.fill_between(fpr, tpr, alpha=0.08, color=C_DROITE)
    plt.plot([0, 1], [0, 1], 'k--', lw=1, label='Aléatoire')
    plt.title('Courbe ROC — Gauche/Droite\nMunicipales Hérault (34)',
              fontsize=14, fontweight='bold')
    plt.xlabel('Taux Faux Positifs')
    plt.ylabel('Taux Vrais Positifs')
    plt.legend(loc='lower right')
    plt.tight_layout()
    path = f'{OUTPUT_DIR}/2_courbe_roc.png'
    plt.savefig(path, dpi=150)
    plt.show()
    print(f"✅ {path}")


def plot_precision_recall(y_test, y_proba):
    precision, recall, _ = precision_recall_curve(y_test, y_proba[:, 1])
    f1_scores = 2 * precision * recall / (precision + recall + 1e-9)
    best = np.argmax(f1_scores)
    plt.figure(figsize=(7, 6))
    plt.plot(recall, precision, color=C_GAUCHE, lw=2)
    plt.fill_between(recall, precision, alpha=0.1, color=C_GAUCHE)
    plt.scatter(recall[best], precision[best], color='gold', s=120, zorder=5,
                label=f'Meilleur F1 = {f1_scores[best]:.3f}')
    plt.title('Courbe Précision / Rappel', fontsize=14, fontweight='bold')
    plt.xlabel('Rappel (Recall)')
    plt.ylabel('Précision')
    plt.legend()
    plt.tight_layout()
    path = f'{OUTPUT_DIR}/3_precision_recall.png'
    plt.savefig(path, dpi=150)
    plt.show()
    print(f"✅ {path}")


def plot_feature_importance(model, features):
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    colors = [C_GAUCHE if importances[i] > np.median(importances) else C_NEUTRE
              for i in indices]
    plt.figure(figsize=(9, 5))
    sns.barplot(x=[importances[i] for i in indices],
                y=[features[i] for i in indices],
                palette=colors)
    plt.title('Importance des Features\nRandom Forest — Hérault (34)',
              fontsize=14, fontweight='bold')
    plt.xlabel('Importance')
    plt.tight_layout()
    path = f'{OUTPUT_DIR}/4_feature_importance.png'
    plt.savefig(path, dpi=150)
    plt.show()
    print(f"✅ {path}")


def plot_learning_curve(model, X_train, y_train):
    train_sizes, train_scores, val_scores = learning_curve(
        model, X_train, y_train, cv=5, n_jobs=-1,
        train_sizes=np.linspace(0.1, 1.0, 10), scoring='accuracy'
    )
    train_mean = np.mean(train_scores, axis=1)
    val_mean   = np.mean(val_scores,   axis=1)
    train_std  = np.std(train_scores,  axis=1)
    val_std    = np.std(val_scores,    axis=1)

    plt.figure(figsize=(8, 5))
    plt.plot(train_sizes, train_mean, 'o-', color=C_DROITE, label='Entraînement (2008–2014)')
    plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std,
                     alpha=0.15, color=C_DROITE)
    plt.plot(train_sizes, val_mean, 'o-', color=C_GAUCHE, label='Validation (CV=5)')
    plt.fill_between(train_sizes, val_mean - val_std, val_mean + val_std,
                     alpha=0.15, color=C_GAUCHE)
    plt.title("Courbe d'Apprentissage — Split temporel 2008–2014 → 2020",
              fontsize=14, fontweight='bold')
    plt.xlabel("Taille du dataset d'entraînement")
    plt.ylabel('Accuracy')
    plt.legend()
    plt.tight_layout()
    path = f'{OUTPUT_DIR}/5_learning_curve.png'
    plt.savefig(path, dpi=150)
    plt.show()
    print(f"✅ {path}")


def plot_class_distribution(df):
    counts = df['label'].value_counts().reindex(['Gauche', 'Droite'], fill_value=0)
    colors = [C_GAUCHE, C_DROITE]

    plt.figure(figsize=(6, 5))
    bars = plt.bar(['Gauche', 'Droite'], counts.values,
                   color=colors, edgecolor='white', linewidth=1.5)
    for bar, count in zip(bars, counts.values):
        pct = count / counts.sum() * 100
        plt.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 1,
                 f'{count}\n({pct:.1f}%)', ha='center', fontweight='bold')
    plt.title('Distribution Gauche / Droite\n341 communes Hérault (34)',
              fontsize=14, fontweight='bold')
    plt.ylabel("Nombre de communes × élections")
    plt.tight_layout()
    path = f'{OUTPUT_DIR}/6_distribution_classes.png'
    plt.savefig(path, dpi=150)
    plt.show()
    print(f"✅ {path}")


def print_rapport(y_test, y_pred):
    print("\n" + "=" * 50)
    print("📋 RAPPORT DE CLASSIFICATION")
    print("=" * 50)
    print(classification_report(y_test, y_pred, target_names=['Gauche', 'Droite']))


# ─────────────────────────────────────────────
# 🚀 MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  ELECTIO-ANALYTICS — GRAPHES SUR DONNÉES RÉELLES")
    print("  Hérault (34) — Municipales 2008 → 2020")
    print("=" * 55)

    # 1. Construire le dataset depuis les APIs
    df, features = construire_dataset()

    # 2. Split temporel (train 2008–2014 / test 2020)
    df_train = df[df['annee'].isin(ANNEES_TRAIN)]
    df_test  = df[df['annee'] == ANNEE_TEST]

    X_train = df_train[features].values
    y_train = df_train['label_bin'].values
    X_test  = df_test[features].values
    y_test  = df_test['label_bin'].values

    print(f"\n  Train : {len(df_train)} observations | Test : {len(df_test)} observations")

    # 3. Entraînement
    print("\n🤖 Entraînement Random Forest...")
    model = RandomForestClassifier(n_estimators=200, max_depth=10,
                                   random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    acc = (y_pred == y_test).mean()
    print(f"   ✅ Accuracy : {acc:.3f}")

    # 4. Graphes
    print(f"\n🚀 Génération des graphes → {OUTPUT_DIR}/\n")
    plot_confusion_matrix(y_test, y_pred)
    plot_roc_curve(y_test, y_proba)
    plot_precision_recall(y_test, y_proba)
    plot_feature_importance(model, features)
    plot_learning_curve(model, X_train, y_train)
    plot_class_distribution(df)
    print_rapport(y_test, y_pred)

    print(f"\n✅ Tous les graphes ont été générés dans : {OUTPUT_DIR}/")
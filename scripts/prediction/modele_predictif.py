#!/usr/bin/env python3
"""
Modèle prédictif — Phase 4 Electio-Analytics
Feature engineering → entraînement → évaluation → prédictions → visualisations.

Modélisation :
  - Classification (Gauche/Droite) : Random Forest
  - Régression (% Gauche continu) : Random Forest

Panel temporel : 3 élections municipales (2008, 2014, 2020), ~690 lignes.
Split temporel : train = 2008+2014, test = 2020.
Prédiction future : 2026.

Usage :
    python scripts/prediction/modele_predictif.py
    python main.py predict
"""

import os
import sqlite3
import ssl
import urllib.request
import warnings

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import seaborn as sns
import geopandas as gpd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, f1_score, confusion_matrix,
                             r2_score, mean_absolute_error)

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = "data/output/electio_herault.db"
OUTPUT_DIR = "graphiques/phase4"
os.makedirs(OUTPUT_DIR, exist_ok=True)

COULEUR_GAUCHE = '#2E86AB'
COULEUR_DROITE = '#E94F37'
COULEUR_PREDIT = '#9B59B6'

COMMUNES_REMARQUABLES = {
    '34172': 'Montpellier',
    '34032': 'Béziers',
    '34301': 'Sète',
    '34003': 'Agde',
    '34129': 'Lunel',
}

ANNEES_ELECTIONS = [2008, 2014, 2020]
ANNEES_TRAIN = [2008, 2014]
ANNEE_TEST = 2020
ANNEE_FUTURE = 2026

# Mapping année élection → année recensement CSP/diplômes
MAPPING_CSP = {2008: 2006, 2014: 2011, 2020: 2022}
MAPPING_DIPLOMES = {2008: 'p11', 2014: 'p16', 2020: 'p22'}

FEATURES = [
    'population', 'pct_cadres', 'pct_ouvriers', 'pct_employes',
    'pct_prof_intermediaires', 'revenu_median',
    'pct_diplome_sup', 'pct_sans_diplome', 'dette_par_hab',
    'invest_par_hab', 'taux_natalite', 'nb_catnat'
]

LABELS_FR = {
    'population': 'Population',
    'pct_cadres': '% Cadres',
    'pct_ouvriers': '% Ouvriers',
    'pct_employes': '% Employés',
    'pct_prof_intermediaires': '% Prof. intermédiaires',
    'revenu_median': 'Revenu médian',
    'pct_diplome_sup': '% Diplôme supérieur',
    'pct_sans_diplome': '% Sans diplôme',
    'dette_par_hab': 'Dette / habitant',
    'invest_par_hab': 'Investissement / hab.',
    'taux_natalite': 'Taux de natalité',
    'nb_catnat': 'Nb catastrophes nat.',
}


# ============================================================================
# HELPERS
# ============================================================================

def get_conn():
    return sqlite3.connect(DB_PATH)


def sauvegarder(fig, nom_fichier):
    path = os.path.join(OUTPUT_DIR, nom_fichier)
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ Sauvegardé : {path}")


# ============================================================================
# 1. FEATURE ENGINEERING
# ============================================================================

def calcul_pct_gauche(conn):
    """Calcule le % Gauche par commune et par année (T1 municipales)."""
    query = """
        SELECT codgeo, annee, camp, SUM(voix) as total_voix
        FROM elections
        WHERE tour = 1 AND annee IN (2008, 2014, 2020)
        GROUP BY codgeo, annee, camp
    """
    df = pd.read_sql_query(query, conn)
    pivot = df.pivot_table(index=['codgeo', 'annee'], columns='camp',
                           values='total_voix', fill_value=0).reset_index()
    if 'Gauche' not in pivot.columns:
        pivot['Gauche'] = 0
    if 'Droite' not in pivot.columns:
        pivot['Droite'] = 0
    pivot['total'] = pivot['Gauche'] + pivot['Droite']
    pivot['pct_gauche'] = 100 * pivot['Gauche'] / pivot['total'].replace(0, np.nan)
    pivot['camp_label'] = (pivot['pct_gauche'] > 50).astype(int)
    result = pivot[['codgeo', 'annee', 'pct_gauche', 'camp_label']].dropna()
    return result


def calcul_features_population(conn):
    """Population par commune et année."""
    query = """
        SELECT codgeo, annee, population
        FROM population
        WHERE annee IN (2008, 2014, 2020, 2006, 2011, 2022, 2023)
    """
    df = pd.read_sql_query(query, conn)
    rows = []
    for annee_elec in ANNEES_ELECTIONS:
        sub = df[df['annee'] == annee_elec]
        if sub.empty:
            sub = df.iloc[(df['annee'] - annee_elec).abs().argsort()[:len(df['codgeo'].unique())]]
            sub = sub[sub['annee'] == sub['annee'].iloc[0]] if not sub.empty else sub
        sub = sub.copy()
        sub['annee_elec'] = annee_elec
        rows.append(sub[['codgeo', 'annee_elec', 'population']].rename(
            columns={'annee_elec': 'annee'}))
    return pd.concat(rows, ignore_index=True).drop_duplicates(subset=['codgeo', 'annee'])


def calcul_features_csp(conn):
    """% cadres, ouvriers, employés, professions intermédiaires par commune et année."""
    rows = []
    for annee_elec, annee_rp in MAPPING_CSP.items():
        csp = pd.read_sql_query(
            f"SELECT * FROM csp WHERE annee = {annee_rp}", conn)
        if csp.empty:
            annees_dispo = pd.read_sql_query(
                "SELECT DISTINCT annee FROM csp ORDER BY annee", conn)['annee'].tolist()
            annee_proche = min(annees_dispo, key=lambda x: abs(x - annee_rp))
            csp = pd.read_sql_query(
                f"SELECT * FROM csp WHERE annee = {annee_proche}", conn)
            if csp.empty:
                continue

        rp_year = f"rp{annee_rp}"
        actifs_cols = [c for c in csp.columns
                       if 'actifs_ayant_un_emploi' in c and rp_year in c]
        if not actifs_cols:
            all_rp = set()
            for c in csp.columns:
                if 'rp' in c:
                    parts = c.split('rp')
                    if len(parts) > 1:
                        year_part = parts[-1].strip()
                        if year_part.isdigit():
                            all_rp.add(int(year_part))
            if all_rp:
                best_rp = min(all_rp, key=lambda x: abs(x - annee_rp))
                rp_year = f"rp{best_rp}"
                actifs_cols = [c for c in csp.columns
                               if 'actifs_ayant_un_emploi' in c and rp_year in c]

        if not actifs_cols:
            continue

        cadres_col = [c for c in actifs_cols if 'cadres' in c]
        ouvriers_col = [c for c in actifs_cols if 'ouvriers' in c]
        employes_col = [c for c in actifs_cols if 'employes' in c or 'employés' in c]
        prof_int_col = [c for c in actifs_cols if 'intermediaires' in c or 'intermédiaires' in c]

        for c in actifs_cols:
            csp[c] = pd.to_numeric(csp[c], errors='coerce')

        csp['total_actifs'] = csp[actifs_cols].sum(axis=1)
        total = csp['total_actifs'].replace(0, np.nan)

        result = csp[['codgeo']].copy()
        result['annee'] = annee_elec
        result['pct_cadres'] = 100 * csp[cadres_col[0]] / total if cadres_col else np.nan
        result['pct_ouvriers'] = 100 * csp[ouvriers_col[0]] / total if ouvriers_col else np.nan
        result['pct_employes'] = 100 * csp[employes_col[0]] / total if employes_col else np.nan
        result['pct_prof_intermediaires'] = 100 * csp[prof_int_col[0]] / total if prof_int_col else np.nan

        rows.append(result)

    if not rows:
        return pd.DataFrame(columns=['codgeo', 'annee', 'pct_cadres', 'pct_ouvriers',
                                      'pct_employes', 'pct_prof_intermediaires'])
    return pd.concat(rows, ignore_index=True)


def calcul_features_revenus(conn):
    """Revenu médian (statique, répliqué pour chaque année)."""
    cols_query = pd.read_sql_query("SELECT * FROM revenus LIMIT 1", conn)
    all_cols = cols_query.columns.tolist()

    mediane_col = None
    for c in all_cols:
        if 'mediane' in c.lower() and 'disp' in c.lower():
            mediane_col = c
            break
    if mediane_col is None:
        for c in all_cols:
            if 'mediane' in c.lower():
                mediane_col = c
                break

    if mediane_col is None:
        return pd.DataFrame(columns=['codgeo', 'annee', 'revenu_median'])

    revenus = pd.read_sql_query(f'SELECT codgeo, "{mediane_col}" as revenu_median FROM revenus', conn)
    revenus['revenu_median'] = pd.to_numeric(revenus['revenu_median'], errors='coerce')

    rows = []
    for annee in ANNEES_ELECTIONS:
        r = revenus.copy()
        r['annee'] = annee
        rows.append(r)
    return pd.concat(rows, ignore_index=True)


def calcul_features_diplomes(conn):
    """% diplôme supérieur et % sans diplôme par commune, aligné temporellement.

    Les noms de colonnes changent selon le recensement :
    - p11 : _dipl0 (sans diplôme), _sup (diplôme sup = bac+2 et plus)
    - p16 : _diplmin (sans diplôme), _sup (diplôme sup)
    - p22 : _diplmin (sans diplôme), _sup2 + _sup34 + _sup5 (diplôme sup détaillé)
    """
    cols_query = pd.read_sql_query("SELECT * FROM diplomes LIMIT 1", conn)
    all_cols = cols_query.columns.tolist()

    rows = []
    for annee_elec, prefix in MAPPING_DIPLOMES.items():
        nscol_col = f'{prefix}_nscol15p'
        if nscol_col not in all_cols:
            continue

        sans_dipl_col = None
        for candidate in [f'{prefix}_nscol15p_diplmin', f'{prefix}_nscol15p_dipl0']:
            if candidate in all_cols:
                sans_dipl_col = candidate
                break

        cols_sup = []
        for c in [f'{prefix}_nscol15p_sup2', f'{prefix}_nscol15p_sup34',
                  f'{prefix}_nscol15p_sup5']:
            if c in all_cols:
                cols_sup.append(c)
        if not cols_sup:
            if f'{prefix}_nscol15p_sup' in all_cols:
                cols_sup = [f'{prefix}_nscol15p_sup']
            elif f'{prefix}_nscol15p_bacp2' in all_cols:
                cols_sup = [f'{prefix}_nscol15p_bacp2']

        if not cols_sup or sans_dipl_col is None:
            continue

        sup_expr = ' + '.join(cols_sup)
        query = f"""
            SELECT codgeo,
                   {nscol_col} as pop_nscol,
                   {sans_dipl_col} as sans_diplome,
                   ({sup_expr}) as diplome_sup
            FROM diplomes
        """
        dipl = pd.read_sql_query(query, conn)
        for c in ['pop_nscol', 'sans_diplome', 'diplome_sup']:
            dipl[c] = pd.to_numeric(dipl[c], errors='coerce')

        total = dipl['pop_nscol'].replace(0, np.nan)
        result = dipl[['codgeo']].copy()
        result['annee'] = annee_elec
        result['pct_diplome_sup'] = 100 * dipl['diplome_sup'] / total
        result['pct_sans_diplome'] = 100 * dipl['sans_diplome'] / total
        rows.append(result)

    if not rows:
        return pd.DataFrame(columns=['codgeo', 'annee', 'pct_diplome_sup', 'pct_sans_diplome'])
    return pd.concat(rows, ignore_index=True)


def calcul_features_comptes(conn):
    """Dette et investissement par habitant."""
    rows = []
    for annee_elec in ANNEES_ELECTIONS:
        annees_cc = pd.read_sql_query(
            "SELECT DISTINCT annee FROM comptes_communes ORDER BY annee", conn
        )['annee'].tolist()
        annee_cc = min(annees_cc, key=lambda x: abs(x - annee_elec))

        query = f"""
            SELECT c.codgeo, c.dette, c.depenses_investissement as invest,
                   p.population
            FROM comptes_communes c
            JOIN population p ON c.codgeo = p.codgeo AND p.annee = {annee_elec}
            WHERE c.annee = {annee_cc}
              AND p.population > 0
        """
        df = pd.read_sql_query(query, conn)
        if df.empty:
            continue

        dette_median = df['dette'].median()
        if dette_median < 5000:
            df['dette_par_hab'] = df['dette']
            df['invest_par_hab'] = df['invest']
        else:
            df['dette_par_hab'] = df['dette'] / df['population']
            df['invest_par_hab'] = df['invest'] / df['population']

        result = df[['codgeo']].copy()
        result['annee'] = annee_elec
        result['dette_par_hab'] = df['dette_par_hab']
        result['invest_par_hab'] = df['invest_par_hab']
        rows.append(result)

    if not rows:
        return pd.DataFrame(columns=['codgeo', 'annee', 'dette_par_hab', 'invest_par_hab'])
    return pd.concat(rows, ignore_index=True)


def calcul_features_natalite(conn):
    """Taux de natalité (moyenne glissante 3 ans) pour chaque année électorale."""
    rows = []
    for annee_elec in ANNEES_ELECTIONS:
        annee_debut = annee_elec - 2
        annee_fin = annee_elec

        query = f"""
            SELECT n.codgeo,
                   AVG(CAST(n.naissances AS REAL)) as moy_naissances,
                   p.population
            FROM naissances_deces n
            JOIN population p ON n.codgeo = p.codgeo AND p.annee = {annee_elec}
            WHERE n.annee BETWEEN {annee_debut} AND {annee_fin}
            GROUP BY n.codgeo
        """
        df = pd.read_sql_query(query, conn)
        if df.empty:
            query_fallback = f"""
                SELECT n.codgeo,
                       AVG(CAST(n.naissances AS REAL)) as moy_naissances,
                       p.population
                FROM naissances_deces n
                JOIN population p ON n.codgeo = p.codgeo AND p.annee = {annee_elec}
                GROUP BY n.codgeo
            """
            df = pd.read_sql_query(query_fallback, conn)
            if df.empty:
                continue

        pop = df['population'].replace(0, np.nan)
        result = df[['codgeo']].copy()
        result['annee'] = annee_elec
        result['taux_natalite'] = 1000 * df['moy_naissances'] / pop
        rows.append(result)

    if not rows:
        return pd.DataFrame(columns=['codgeo', 'annee', 'taux_natalite'])
    return pd.concat(rows, ignore_index=True)


def calcul_features_catnat(conn):
    """Nombre cumulé de CatNat par commune (statique)."""
    query = """
        SELECT codgeo, COUNT(*) as nb_catnat
        FROM catnat
        GROUP BY codgeo
    """
    catnat = pd.read_sql_query(query, conn)

    rows = []
    for annee in ANNEES_ELECTIONS:
        c = catnat.copy()
        c['annee'] = annee
        rows.append(c)
    return pd.concat(rows, ignore_index=True)


def construire_panel(conn):
    """Assemble le panel complet : cible + 12 features."""
    print("\n[FEATURES] Construction du panel temporel...")

    cible = calcul_pct_gauche(conn)
    print(f"  Cible : {len(cible)} observations (commune × année)")

    pop = calcul_features_population(conn)
    print(f"  Population : {len(pop)} lignes")

    csp = calcul_features_csp(conn)
    print(f"  CSP : {len(csp)} lignes")

    revenus = calcul_features_revenus(conn)
    print(f"  Revenus : {len(revenus)} lignes")

    diplomes = calcul_features_diplomes(conn)
    print(f"  Diplômes : {len(diplomes)} lignes")

    comptes = calcul_features_comptes(conn)
    print(f"  Comptes communes : {len(comptes)} lignes")

    natalite = calcul_features_natalite(conn)
    print(f"  Natalité : {len(natalite)} lignes")

    catnat = calcul_features_catnat(conn)
    print(f"  CatNat : {len(catnat)} lignes")

    # Fusionner tout sur (codgeo, annee)
    panel = cible.copy()
    for df_join in [pop, csp, revenus, diplomes, comptes, natalite, catnat]:
        panel = panel.merge(df_join, on=['codgeo', 'annee'], how='left')

    print(f"\n  Panel brut : {len(panel)} lignes × {len(panel.columns)} colonnes")

    panel['nb_catnat'] = panel['nb_catnat'].fillna(0)

    for col in FEATURES:
        if col in panel.columns:
            pct_ok = 100 * panel[col].notna().sum() / len(panel)
            print(f"  {col:30s} : {pct_ok:.0f}% complet")

    panel_complet = panel.dropna(subset=[f for f in FEATURES if f in panel.columns],
                                  how='any')
    print(f"\n  Panel final (sans NaN) : {len(panel_complet)} lignes")
    print(f"  Années : {sorted(panel_complet['annee'].unique())}")

    return panel_complet


# ============================================================================
# 2. ENTRAÎNEMENT ET ÉVALUATION
# ============================================================================

def entrainer_modeles(panel):
    """Entraîne 2 modèles Random Forest (1 classifieur + 1 régresseur)."""
    print("\n[MODÈLES] Entraînement sur train (2008-2014), test (2020)...")

    train = panel[panel['annee'].isin(ANNEES_TRAIN)]
    test = panel[panel['annee'] == ANNEE_TEST]

    print(f"  Train : {len(train)} lignes ({sorted(train['annee'].unique())})")
    print(f"  Test  : {len(test)} lignes")

    features_presentes = [f for f in FEATURES if f in panel.columns]
    X_train = train[features_presentes].values
    X_test = test[features_presentes].values
    y_train_cls = train['camp_label'].values
    y_test_cls = test['camp_label'].values
    y_train_reg = train['pct_gauche'].values
    y_test_reg = test['pct_gauche'].values

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Classification
    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(X_train_scaled, y_train_cls)
    y_pred_cls = clf.predict(X_test_scaled)
    acc = accuracy_score(y_test_cls, y_pred_cls)
    f1 = f1_score(y_test_cls, y_pred_cls, average='weighted')
    cm = confusion_matrix(y_test_cls, y_pred_cls)
    print(f"  [CLS] Random Forest → Accuracy={acc:.3f}  F1={f1:.3f}")

    # Régression
    reg = RandomForestRegressor(n_estimators=200, random_state=42)
    reg.fit(X_train_scaled, y_train_reg)
    y_pred_reg = reg.predict(X_test_scaled)
    r2 = r2_score(y_test_reg, y_pred_reg)
    mae = mean_absolute_error(y_test_reg, y_pred_reg)
    print(f"  [REG] Random Forest → R²={r2:.3f}  MAE={mae:.1f}")

    return {
        'clf': clf,
        'reg': reg,
        'scaler': scaler,
        'features': features_presentes,
        'accuracy': acc,
        'f1': f1,
        'confusion_matrix': cm,
        'y_pred_cls': y_pred_cls,
        'r2': r2,
        'mae': mae,
        'y_pred_reg': y_pred_reg,
        'y_test_cls': y_test_cls,
        'y_test_reg': y_test_reg,
        'test_codgeo': test['codgeo'].values,
        'train': train,
        'test': test,
    }


# ============================================================================
# 3. PRÉDICTIONS FUTURES (2026)
# ============================================================================

def extrapoler_features(conn, panel):
    """Extrapole les features pour 2026."""
    print("\n[PRÉDICTIONS] Extrapolation des features pour 2026...")

    communes = panel[panel['annee'] == ANNEE_TEST]['codgeo'].unique()
    features_presentes = [f for f in FEATURES if f in panel.columns]

    rows_futures = []
    for codgeo in communes:
        row = {'codgeo': codgeo, 'annee': ANNEE_FUTURE}

        # Population : tendance linéaire 2014→2020 prolongée
        pop_2014 = panel[(panel['codgeo'] == codgeo) & (panel['annee'] == 2014)]['population']
        pop_2020 = panel[(panel['codgeo'] == codgeo) & (panel['annee'] == 2020)]['population']
        if not pop_2014.empty and not pop_2020.empty:
            p14 = pop_2014.values[0]
            p20 = pop_2020.values[0]
            tendance = (p20 - p14) / 6  # par an
            row['population'] = max(0, p20 + tendance * (ANNEE_FUTURE - 2020))
        else:
            row['population'] = pop_2020.values[0] if not pop_2020.empty else np.nan

        # CSP, diplômes, revenus : valeurs 2020 maintenues
        for feat in ['pct_cadres', 'pct_ouvriers', 'pct_employes',
                     'pct_prof_intermediaires', 'revenu_median',
                     'pct_diplome_sup', 'pct_sans_diplome']:
            val = panel[(panel['codgeo'] == codgeo) & (panel['annee'] == 2020)][feat]
            row[feat] = val.values[0] if not val.empty else np.nan

        # Comptes communes : valeurs 2020
        for feat in ['dette_par_hab', 'invest_par_hab']:
            val = panel[(panel['codgeo'] == codgeo) & (panel['annee'] == 2020)][feat]
            row[feat] = val.values[0] if not val.empty else np.nan

        # Natalité : valeur 2020
        val = panel[(panel['codgeo'] == codgeo) & (panel['annee'] == 2020)]['taux_natalite']
        row['taux_natalite'] = val.values[0] if not val.empty else np.nan

        # CatNat : cumul inchangé
        val = panel[(panel['codgeo'] == codgeo) & (panel['annee'] == 2020)]['nb_catnat']
        row['nb_catnat'] = val.values[0] if not val.empty else 0

        rows_futures.append(row)

    df_futures = pd.DataFrame(rows_futures)
    df_futures = df_futures.dropna(subset=features_presentes, how='any')
    print(f"  {len(df_futures)} communes extrapolées pour {ANNEE_FUTURE}")
    return df_futures


def predire_futur(resultats, df_futures):
    """Applique les modèles aux features extrapolées."""
    scaler = resultats['scaler']
    features = resultats['features']

    X_future = df_futures[features].values
    X_future_scaled = scaler.transform(X_future)

    df_futures = df_futures.copy()
    df_futures['pred_camp'] = resultats['clf'].predict(X_future_scaled)
    df_futures['pred_pct_gauche'] = resultats['reg'].predict(X_future_scaled).clip(0, 100)

    moy = df_futures['pred_pct_gauche'].mean()
    pct_gauche = 100 * (df_futures['pred_camp'] == 1).mean()
    print(f"  {ANNEE_FUTURE} : % Gauche moyen = {moy:.1f}%, "
          f"communes Gauche = {pct_gauche:.0f}%")

    return df_futures


# ============================================================================
# 4. VISUALISATIONS (7 graphiques)
# ============================================================================

def plot_01_importance_features(resultats):
    """Bar horizontal : importance des features."""
    print("\n[VIZ 1/7] Importance des features...")

    features = resultats['features']
    importances = resultats['clf'].feature_importances_
    indices = np.argsort(importances)

    fig, ax = plt.subplots(figsize=(10, 8))
    labels = [LABELS_FR.get(features[i], features[i]) for i in indices]
    colors = [COULEUR_GAUCHE if importances[i] > np.median(importances) else '#999999'
              for i in indices]

    ax.barh(range(len(indices)), importances[indices], color=colors, alpha=0.8,
            edgecolor='black', linewidth=0.3)
    ax.set_yticks(range(len(indices)))
    ax.set_yticklabels(labels, fontsize=11)
    ax.set_xlabel('Importance', fontsize=12)
    ax.set_title("Importance des features — Random Forest\n"
                 "(Classification Gauche/Droite, Hérault 34)",
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()
    sauvegarder(fig, "01_importance_features.png")


def plot_02_matrice_confusion(resultats):
    """Heatmap 2×2 : matrice de confusion."""
    print("\n[VIZ 2/7] Matrice de confusion...")

    cm = resultats['confusion_matrix']

    fig, ax = plt.subplots(figsize=(8, 7))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=['Droite', 'Gauche'],
                yticklabels=['Droite', 'Gauche'],
                annot_kws={'size': 20})
    ax.set_xlabel('Prédit', fontsize=13)
    ax.set_ylabel('Réel', fontsize=13)
    ax.set_title(f"Matrice de confusion — Random Forest\n"
                 f"Test 2020 — Accuracy={resultats['accuracy']:.3f}, F1={resultats['f1']:.3f}",
                 fontsize=14, fontweight='bold')

    plt.tight_layout()
    sauvegarder(fig, "02_matrice_confusion.png")


def plot_03_predictions_temporelles(conn, df_futures):
    """Line chart : % Gauche département (réel + prédit 2026)."""
    print("\n[VIZ 3/7] Prédictions temporelles...")

    query = """
        SELECT annee, camp, SUM(voix) as total_voix
        FROM elections
        WHERE tour = 1 AND annee IN (2008, 2014, 2020)
        GROUP BY annee, camp
    """
    df = pd.read_sql_query(query, conn)
    pivot = df.pivot_table(index='annee', columns='camp', values='total_voix', fill_value=0)
    pivot['total'] = pivot.get('Gauche', 0) + pivot.get('Droite', 0)
    pivot['pct_gauche'] = 100 * pivot.get('Gauche', 0) / pivot['total']

    annees_reelles = pivot.index.tolist()
    pct_reelles = pivot['pct_gauche'].tolist()

    pct_predit = df_futures['pred_pct_gauche'].mean()

    fig, ax = plt.subplots(figsize=(12, 7))

    # Réel
    ax.plot(annees_reelles, pct_reelles, '-o', color=COULEUR_GAUCHE, linewidth=3,
            markersize=10, label='Réel', zorder=5)
    for i, a in enumerate(annees_reelles):
        ax.annotate(f'{pct_reelles[i]:.1f}%', (a, pct_reelles[i]),
                    textcoords="offset points", xytext=(0, 12), ha='center',
                    fontsize=11, color=COULEUR_GAUCHE, fontweight='bold')

    # Prédit
    ax.plot([annees_reelles[-1], ANNEE_FUTURE], [pct_reelles[-1], pct_predit],
            '--s', color=COULEUR_PREDIT, linewidth=2.5, markersize=10,
            label='Prédit', zorder=5)
    ax.annotate(f'{pct_predit:.1f}%', (ANNEE_FUTURE, pct_predit),
                textcoords="offset points", xytext=(0, 12), ha='center',
                fontsize=11, color=COULEUR_PREDIT, fontweight='bold')

    ax.axvspan(annees_reelles[-1] + 0.5, ANNEE_FUTURE + 0.5,
               alpha=0.08, color=COULEUR_PREDIT, label='Zone de prédiction')

    ax.axhline(y=50, color='gray', linestyle=':', alpha=0.5, label='50%')
    ax.set_xlabel('Année', fontsize=12)
    ax.set_ylabel('% Gauche (département)', fontsize=12)
    ax.set_title("Évolution et prédiction du vote Gauche — Hérault (34)\n"
                 "Municipales T1 — Moyenne départementale",
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(annees_reelles + [ANNEE_FUTURE])

    plt.tight_layout()
    sauvegarder(fig, "03_predictions_temporelles.png")


def plot_04_carte_predictions(df_futures):
    """Carte choroplèthe : % Gauche prédit 2026."""
    print("\n[VIZ 4/7] Carte des prédictions 2026...")

    pred = df_futures[['codgeo', 'pred_pct_gauche']]
    if pred.empty:
        print("  ⚠ Pas de prédictions")
        return

    # GeoJSON
    geojson_path = os.path.join("graphiques/phase3", "communes_34.geojson")
    if not os.path.exists(geojson_path):
        geojson_path = os.path.join(OUTPUT_DIR, "communes_34.geojson")
        if not os.path.exists(geojson_path):
            print("  Téléchargement du GeoJSON des communes de l'Hérault...")
            url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements/34-herault/communes-34-herault.geojson"
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            urllib.request.urlretrieve(url, geojson_path)

    gdf = gpd.read_file(geojson_path)
    gdf['codgeo'] = gdf['code'].astype(str)
    gdf = gdf.merge(pred, on='codgeo', how='left')

    fig, ax = plt.subplots(figsize=(14, 10))

    cmap = mcolors.LinearSegmentedColormap.from_list('', [COULEUR_DROITE, '#FFFFFF', COULEUR_GAUCHE])
    gdf.plot(column='pred_pct_gauche', cmap=cmap, linewidth=0.3, ax=ax,
             edgecolor='0.5', legend=True, vmin=20, vmax=80,
             missing_kwds={'color': 'lightgray'},
             legend_kwds={'label': '% Gauche prédit', 'shrink': 0.6})

    ax.axis('off')
    ax.set_title(f"Prédiction du vote Gauche par commune — {ANNEE_FUTURE} — Hérault (34)\n"
                 "(Bleu = Gauche, Rouge = Droite)",
                 fontsize=14, fontweight='bold')

    plt.tight_layout()
    sauvegarder(fig, "04_carte_predictions_2026.png")


def plot_05_distribution_probabilites(df_futures):
    """Histogramme : distribution du % Gauche prédit 2026."""
    print("\n[VIZ 5/7] Distribution des probabilités...")

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.hist(df_futures['pred_pct_gauche'], bins=25, alpha=0.5,
            color=COULEUR_PREDIT, label=str(ANNEE_FUTURE),
            edgecolor='black', linewidth=0.3)

    ax.axvline(x=50, color='black', linestyle='--', alpha=0.7, label='50%')
    ax.set_xlabel('% Gauche prédit', fontsize=12)
    ax.set_ylabel('Nombre de communes', fontsize=12)
    ax.set_title(f"Distribution des prédictions par commune — Hérault (34)\n"
                 f"Municipales T1 — {ANNEE_FUTURE}",
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    sauvegarder(fig, "05_distribution_probabilites.png")


def plot_06_reel_vs_predit(resultats):
    """Scatter : % Gauche réel vs prédit pour 2020."""
    print("\n[VIZ 6/7] Réel vs prédit (2020)...")

    y_test = resultats['y_test_reg']
    y_pred = resultats['y_pred_reg']

    fig, ax = plt.subplots(figsize=(10, 10))

    colors = [COULEUR_GAUCHE if g > 50 else COULEUR_DROITE for g in y_test]
    ax.scatter(y_test, y_pred, c=colors, s=50, alpha=0.6,
               edgecolors='black', linewidth=0.3)

    lims = [min(y_test.min(), y_pred.min()) - 5, max(y_test.max(), y_pred.max()) + 5]
    ax.plot(lims, lims, 'k--', alpha=0.6, linewidth=2, label='Prédiction parfaite')

    ax.set_xlabel('% Gauche réel (2020)', fontsize=12)
    ax.set_ylabel('% Gauche prédit', fontsize=12)
    ax.set_title(f"Réel vs Prédit — Random Forest\n"
                 f"R²={resultats['r2']:.3f}, MAE={resultats['mae']:.1f} points",
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_aspect('equal')

    plt.tight_layout()
    sauvegarder(fig, "06_reel_vs_predit_2020.png")


def plot_07_communes_remarquables(conn, df_futures):
    """Multi-line : 5 communes remarquables, réel + prédit."""
    print("\n[VIZ 7/7] Évolution des communes remarquables...")

    query = """
        SELECT codgeo, annee, camp, SUM(voix) as total_voix
        FROM elections
        WHERE tour = 1 AND annee IN (2008, 2014, 2020)
        GROUP BY codgeo, annee, camp
    """
    df = pd.read_sql_query(query, conn)
    pivot = df.pivot_table(index=['codgeo', 'annee'], columns='camp',
                           values='total_voix', fill_value=0).reset_index()
    if 'Gauche' not in pivot.columns:
        pivot['Gauche'] = 0
    if 'Droite' not in pivot.columns:
        pivot['Droite'] = 0
    pivot['total'] = pivot['Gauche'] + pivot['Droite']
    pivot['pct_gauche'] = 100 * pivot['Gauche'] / pivot['total'].replace(0, np.nan)

    fig, ax = plt.subplots(figsize=(14, 8))

    colors_communes = ['#2E86AB', '#E94F37', '#9B59B6', '#F39C12', '#27AE60']

    for i, (codgeo, nom) in enumerate(COMMUNES_REMARQUABLES.items()):
        color = colors_communes[i % len(colors_communes)]

        reel = pivot[pivot['codgeo'] == codgeo].sort_values('annee')
        if reel.empty:
            continue
        ax.plot(reel['annee'], reel['pct_gauche'], '-o', color=color,
                linewidth=2.5, markersize=8, label=f'{nom} (réel)')

        pred = df_futures[df_futures['codgeo'] == codgeo]
        if not pred.empty:
            last_real = reel.iloc[-1]
            pred_x = [last_real['annee'], ANNEE_FUTURE]
            pred_y = [last_real['pct_gauche'], pred.iloc[0]['pred_pct_gauche']]
            ax.plot(pred_x, pred_y, '--s', color=color, linewidth=1.5,
                    markersize=6, alpha=0.7)

    ax.axhline(y=50, color='gray', linestyle=':', alpha=0.5)

    ax.axvspan(2020.5, 2026.5, alpha=0.08, color=COULEUR_PREDIT)
    ax.text(ANNEE_FUTURE, ax.get_ylim()[1] - 2, 'Prédictions', ha='center',
            fontsize=10, color=COULEUR_PREDIT, fontstyle='italic')

    ax.set_xlabel('Année', fontsize=12)
    ax.set_ylabel('% Gauche', fontsize=12)
    ax.set_title("Évolution du vote Gauche — Communes remarquables — Hérault (34)\n"
                 "(Trait plein = réel, Tirets = prédit)",
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=10, loc='best', ncol=2)
    ax.grid(True, alpha=0.3)
    ax.set_xticks([2008, 2014, 2020, ANNEE_FUTURE])

    plt.tight_layout()
    sauvegarder(fig, "07_evolution_communes_remarquables.png")


# ============================================================================
# 5. QUESTIONS D'ANALYSE
# ============================================================================

def afficher_questions_analyse(resultats):
    """Affiche les réponses aux 3 questions d'analyse du cahier des charges."""
    print("\n" + "=" * 70)
    print("  QUESTIONS D'ANALYSE")
    print("=" * 70)

    # Question 1 : Feature la plus corrélée
    print("\n─── Q1 : Quelle donnée est la plus corrélée aux résultats ? ───")
    importances = resultats['clf'].feature_importances_
    features = resultats['features']
    top_idx = np.argsort(importances)[::-1]
    print("\n  Top 5 features par importance (classification) :")
    for rank, i in enumerate(top_idx[:5]):
        label = LABELS_FR.get(features[i], features[i])
        print(f"    {rank+1}. {label} (importance = {importances[i]:.4f})")
    top_feat = LABELS_FR.get(features[top_idx[0]], features[top_idx[0]])
    print(f"\n  → La donnée la plus corrélée est : {top_feat}")

    # Question 2 : Principe d'un apprentissage supervisé
    print("\n─── Q2 : Définir le principe d'un apprentissage supervisé ───")
    print("""
  L'apprentissage supervisé est une méthode de machine learning dans laquelle
  un algorithme apprend à partir de données étiquetées — c'est-à-dire des
  exemples pour lesquels on connaît déjà la réponse correcte (la « cible »).

  Dans notre projet :
  - ENTRÉES (features) : 12 indicateurs socio-économiques par commune
  - SORTIE (cible) : camp majoritaire (Gauche/Droite) ou % de voix Gauche
  - L'algorithme apprend sur 2008-2014, puis prédit 2020 (test) et 2026.""")

    # Question 3 : Comment définir l'accuracy
    print("\n─── Q3 : Comment définir l'accuracy du modèle ? ───")
    print(f"""
  Accuracy = Nombre de prédictions correctes / Nombre total de prédictions
           = {resultats['accuracy']:.3f} ({resultats['accuracy']*100:.1f}% de communes correctement classées)

  F1-score = moyenne harmonique de la précision et du rappel = {resultats['f1']:.3f}
  La matrice de confusion détaille les vrais/faux positifs et négatifs.""")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("  MODÈLE PRÉDICTIF — PHASE 4")
    print("  Département : Hérault (34)")
    print("  Source : SQLite " + DB_PATH)
    print("=" * 70)

    if not os.path.exists(DB_PATH):
        print(f"\n⚠ Base SQLite introuvable : {DB_PATH}")
        print("  Lancez d'abord : python main.py etl")
        return

    conn = get_conn()

    # 1. Feature engineering
    panel = construire_panel(conn)

    if len(panel) < 50:
        print(f"\n⚠ Panel trop petit ({len(panel)} lignes). Vérifiez la base de données.")
        conn.close()
        return

    # 2. Entraînement et évaluation
    resultats = entrainer_modeles(panel)

    # 3. Prédictions futures
    df_futures = extrapoler_features(conn, panel)
    df_futures = predire_futur(resultats, df_futures)

    # 4. Visualisations
    print("\n" + "=" * 70)
    print("  GÉNÉRATION DES VISUALISATIONS")
    print("=" * 70)

    plot_01_importance_features(resultats)
    plot_02_matrice_confusion(resultats)
    plot_03_predictions_temporelles(conn, df_futures)
    plot_04_carte_predictions(df_futures)
    plot_05_distribution_probabilites(df_futures)
    plot_06_reel_vs_predit(resultats)
    plot_07_communes_remarquables(conn, df_futures)

    # 5. Questions d'analyse
    afficher_questions_analyse(resultats)

    conn.close()

    # Résumé
    fichiers = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.png')]
    print(f"\n{'=' * 70}")
    print(f"  TERMINÉ — {len(fichiers)} graphiques générés dans {OUTPUT_DIR}/")
    for f in sorted(fichiers):
        print(f"    {f}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Analyse exploratoire — Phase 3 Electio-Analytics
Lit la base SQLite Hérault (34) et génère 10 visualisations dans graphiques/phase3/.

Usage :
    python scripts/analyse_exploratoire.py
    python main.py analyse
"""

import os
import sqlite3
import ssl
import urllib.request

# Installer les dépendances si nécessaire
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import numpy as np
except ImportError:
    os.system("pip3 install matplotlib numpy")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import numpy as np

try:
    import pandas as pd
except ImportError:
    os.system("pip3 install pandas")
    import pandas as pd

try:
    import seaborn as sns
except ImportError:
    os.system("pip3 install seaborn")
    import seaborn as sns

try:
    import geopandas as gpd
except ImportError:
    os.system("pip3 install geopandas")
    import geopandas as gpd

ssl._create_default_https_context = ssl._create_unverified_context

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = "data/output/electio_herault.db"
OUTPUT_DIR = "graphiques/phase3"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Couleurs Gauche / Droite (même convention que les scripts existants)
COULEUR_GAUCHE = '#2E86AB'
COULEUR_DROITE = '#E94F37'

# Communes remarquables à annoter
COMMUNES_ANNOTEES = {
    '34172': 'Montpellier',
    '34032': 'Béziers',
    '34301': 'Sète',
    '34003': 'Agde',
    '34129': 'Lunel',
}


# ============================================================================
# HELPERS
# ============================================================================

def get_conn():
    """Retourne une connexion SQLite."""
    return sqlite3.connect(DB_PATH)


def calcul_pct_gauche_par_commune(conn, annee=2020, tour=1):
    """Calcule le % de voix Gauche par commune pour une élection donnée.

    Retourne un DataFrame avec colonnes : codgeo, pct_gauche
    """
    query = """
        SELECT codgeo, camp, SUM(voix) as total_voix
        FROM elections
        WHERE annee = ? AND tour = ?
        GROUP BY codgeo, camp
    """
    df = pd.read_sql_query(query, conn, params=(annee, tour))

    if df.empty:
        return pd.DataFrame(columns=['codgeo', 'pct_gauche'])

    # Pivoter : une ligne par commune, colonnes Gauche / Droite
    pivot = df.pivot_table(index='codgeo', columns='camp', values='total_voix', fill_value=0)

    if 'Gauche' not in pivot.columns:
        pivot['Gauche'] = 0
    if 'Droite' not in pivot.columns:
        pivot['Droite'] = 0

    pivot['total'] = pivot['Gauche'] + pivot['Droite']
    pivot['pct_gauche'] = 100 * pivot['Gauche'] / pivot['total'].replace(0, np.nan)

    result = pivot[['pct_gauche']].reset_index()
    result = result.dropna(subset=['pct_gauche'])
    return result


def _calcul_csp_pct(conn):
    """Calcule % cadres et % ouvriers par commune (CSP 2022).

    Les colonnes CSP contiennent des newlines et les valeurs sont stockées
    comme strings — on lit tout avec pandas et on convertit.
    """
    csp_all = pd.read_sql_query("SELECT * FROM csp WHERE annee = 2022", conn)

    if csp_all.empty:
        return pd.DataFrame(columns=['codgeo', 'pct_cadres', 'pct_ouvriers'])

    # Identifier les colonnes rp2022 actifs
    actifs_cols = [c for c in csp_all.columns if 'actifs_ayant_un_emploi' in c and 'rp2022' in c]
    cadres_col = [c for c in actifs_cols if 'cadres' in c]
    ouvriers_col = [c for c in actifs_cols if 'ouvriers' in c]

    if not cadres_col or not ouvriers_col or not actifs_cols:
        return pd.DataFrame(columns=['codgeo', 'pct_cadres', 'pct_ouvriers'])

    # Convertir en numérique
    for c in actifs_cols:
        csp_all[c] = pd.to_numeric(csp_all[c], errors='coerce')

    csp_all['total_actifs'] = csp_all[actifs_cols].sum(axis=1)
    csp_all['pct_cadres'] = 100 * csp_all[cadres_col[0]] / csp_all['total_actifs'].replace(0, np.nan)
    csp_all['pct_ouvriers'] = 100 * csp_all[ouvriers_col[0]] / csp_all['total_actifs'].replace(0, np.nan)

    return csp_all[['codgeo', 'pct_cadres', 'pct_ouvriers']].dropna()


def sauvegarder(fig, nom_fichier):
    """Sauvegarde une figure et affiche le chemin."""
    path = os.path.join(OUTPUT_DIR, nom_fichier)
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ Sauvegardé : {path}")


# ============================================================================
# GRAPHIQUE 1 : Évolution du vote Gauche/Droite (2002-2022)
# ============================================================================

def plot_01_evolution_vote(conn):
    """Line chart : évolution Gauche/Droite dans le 34 (municipales T1)."""
    print("\n[1/10] Évolution du vote Gauche/Droite (2008-2020)...")

    query = """
        SELECT annee, camp, SUM(voix) as total_voix
        FROM elections
        WHERE tour = 1
        GROUP BY annee, camp
        ORDER BY annee
    """
    df = pd.read_sql_query(query, conn)

    if df.empty:
        print("  ⚠ Pas de données élections T1")
        return

    pivot = df.pivot_table(index='annee', columns='camp', values='total_voix', fill_value=0)
    pivot['total'] = pivot.get('Gauche', 0) + pivot.get('Droite', 0)
    pivot['pct_gauche'] = 100 * pivot.get('Gauche', 0) / pivot['total']
    pivot['pct_droite'] = 100 * pivot.get('Droite', 0) / pivot['total']

    annees = pivot.index.tolist()
    pct_g = pivot['pct_gauche'].tolist()
    pct_d = pivot['pct_droite'].tolist()

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.plot(annees, pct_g, '-o', color=COULEUR_GAUCHE, linewidth=3, markersize=10, label='Gauche')
    ax.plot(annees, pct_d, '-o', color=COULEUR_DROITE, linewidth=3, markersize=10, label='Droite')

    for i, a in enumerate(annees):
        ax.annotate(f'{pct_g[i]:.1f}%', (a, pct_g[i]), textcoords="offset points",
                    xytext=(0, 12), ha='center', fontsize=10, color=COULEUR_GAUCHE)
        ax.annotate(f'{pct_d[i]:.1f}%', (a, pct_d[i]), textcoords="offset points",
                    xytext=(0, -15), ha='center', fontsize=10, color=COULEUR_DROITE)

    ax.set_xlabel('Année', fontsize=12)
    ax.set_ylabel('% des voix', fontsize=12)
    ax.set_title("Évolution Gauche/Droite — Municipales T1 — Hérault (34)\n(LREM classé à droite)",
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)
    ax.set_xticks(annees)

    plt.tight_layout()
    sauvegarder(fig, "01_evolution_vote_herault.png")


# ============================================================================
# GRAPHIQUE 2 : Carte des communes par vote majoritaire (T1 2022)
# ============================================================================

def plot_02_carte_communes(conn):
    """Carte choroplèthe : % Gauche par commune (T1 2020)."""
    print("\n[2/10] Carte des communes par vote majoritaire (T1 2020)...")

    pct = calcul_pct_gauche_par_commune(conn, annee=2020, tour=1)

    if pct.empty:
        print("  ⚠ Pas de données pour 2020 T1")
        return

    # Télécharger le GeoJSON des communes du 34
    geojson_path = os.path.join(OUTPUT_DIR, "communes_34.geojson")
    if not os.path.exists(geojson_path):
        print("  Téléchargement du GeoJSON des communes de l'Hérault...")
        url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements/34-herault/communes-34-herault.geojson"
        urllib.request.urlretrieve(url, geojson_path)

    gdf = gpd.read_file(geojson_path)

    # Joindre avec les données de vote
    gdf['codgeo'] = gdf['code'].astype(str)
    gdf = gdf.merge(pct, on='codgeo', how='left')

    fig, ax = plt.subplots(figsize=(14, 10))

    cmap = mcolors.LinearSegmentedColormap.from_list('', [COULEUR_DROITE, '#FFFFFF', COULEUR_GAUCHE])
    gdf.plot(column='pct_gauche', cmap=cmap, linewidth=0.3, ax=ax,
             edgecolor='0.5', legend=True, vmin=20, vmax=80,
             missing_kwds={'color': 'lightgray'},
             legend_kwds={'label': '% Gauche', 'shrink': 0.6})

    ax.axis('off')
    ax.set_title("Vote Gauche/Droite par commune — Municipales T1 2020 — Hérault\n"
                 "(Bleu = Gauche, Rouge = Droite)",
                 fontsize=14, fontweight='bold')

    plt.tight_layout()
    sauvegarder(fig, "02_carte_communes_2020.png")


# ============================================================================
# GRAPHIQUE 3 : Revenu médian vs % vote Gauche (scatter)
# ============================================================================

def plot_03_revenu_vs_vote(conn):
    """Scatter plot : revenu médian vs % Gauche, avec droite de tendance."""
    print("\n[3/10] Revenu médian vs % vote Gauche...")

    pct = calcul_pct_gauche_par_commune(conn, annee=2020, tour=1)

    revenus = pd.read_sql_query(
        'SELECT codgeo, "[disp]_mediane_(€)" as revenu_median FROM revenus', conn)
    revenus = revenus.dropna(subset=['revenu_median'])

    merged = pct.merge(revenus, on='codgeo')

    if merged.empty:
        print("  ⚠ Pas de données après jointure revenus/élections")
        return

    x = merged['revenu_median'].values
    y = merged['pct_gauche'].values

    # Corrélation de Pearson
    correlation = np.corrcoef(x, y)[0, 1]

    # Régression linéaire
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)

    fig, ax = plt.subplots(figsize=(12, 8))

    colors = [COULEUR_GAUCHE if g > 50 else COULEUR_DROITE for g in y]
    ax.scatter(x, y, c=colors, s=50, alpha=0.6, edgecolors='black', linewidth=0.3)

    # Droite de tendance
    x_line = np.linspace(x.min(), x.max(), 100)
    ax.plot(x_line, p(x_line), 'k--', alpha=0.6, linewidth=2,
            label=f'Tendance (r = {correlation:.3f})')

    ax.axhline(y=50, color='gray', linestyle=':', alpha=0.4)

    # Annoter les communes remarquables
    noms = pd.read_sql_query("SELECT codgeo, nom FROM communes", conn)
    merged_noms = merged.merge(noms, on='codgeo')
    for codgeo, nom in COMMUNES_ANNOTEES.items():
        row = merged_noms[merged_noms['codgeo'] == codgeo]
        if not row.empty:
            ax.annotate(nom, (row['revenu_median'].values[0], row['pct_gauche'].values[0]),
                        fontsize=9, fontweight='bold', alpha=0.8,
                        xytext=(5, 5), textcoords='offset points')

    ax.set_xlabel('Revenu médian (€)', fontsize=12)
    ax.set_ylabel('% Vote Gauche (T1 2020)', fontsize=12)
    ax.set_title(f"Revenu médian vs Vote Gauche par commune — Hérault\n"
                 f"Corrélation de Pearson : r = {correlation:.3f}",
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    sauvegarder(fig, "03_revenu_vs_vote.png")


# ============================================================================
# GRAPHIQUE 4 : Heatmap de corrélation
# ============================================================================

def plot_04_heatmap_correlations(conn):
    """Heatmap : matrice de corrélation entre indicateurs socio-éco et % Gauche."""
    print("\n[4/10] Heatmap de corrélation indicateurs vs % Gauche...")

    pct = calcul_pct_gauche_par_commune(conn, annee=2020, tour=1)

    # --- Revenu médian ---
    revenus = pd.read_sql_query(
        'SELECT codgeo, "[disp]_mediane_(€)" as revenu_median FROM revenus', conn)

    # --- CSP (cadres, ouvriers) pour annee = 2022 ---
    csp_df = _calcul_csp_pct(conn)
    csp_df = csp_df[['codgeo', 'pct_cadres', 'pct_ouvriers']].dropna()

    # --- Diplômes (sans diplôme, diplôme sup) ---
    dipl_query = """
        SELECT codgeo,
               p22_nscol15p as pop_nscol,
               p22_nscol15p_diplmin as sans_diplome,
               (p22_nscol15p_sup2 + p22_nscol15p_sup34 + p22_nscol15p_sup5) as diplome_sup
        FROM diplomes
    """
    dipl_df = pd.read_sql_query(dipl_query, conn)
    dipl_df['pct_sans_diplome'] = 100 * dipl_df['sans_diplome'] / dipl_df['pop_nscol'].replace(0, np.nan)
    dipl_df['pct_diplome_sup'] = 100 * dipl_df['diplome_sup'] / dipl_df['pop_nscol'].replace(0, np.nan)
    dipl_df = dipl_df[['codgeo', 'pct_sans_diplome', 'pct_diplome_sup']].dropna()

    # --- Dette par habitant (comptes_communes, année la plus proche de 2020) ---
    comptes_query = """
        SELECT c.codgeo, c.dette, p.population
        FROM comptes_communes c
        JOIN population p ON c.codgeo = p.codgeo AND p.annee = 2020
        WHERE c.annee = (SELECT MAX(annee) FROM comptes_communes WHERE annee <= 2020)
    """
    comptes_df = pd.read_sql_query(comptes_query, conn)
    # dette est en milliers d'€ parfois — vérifier les ordres de grandeur
    comptes_df['dette_par_hab'] = comptes_df['dette'] / comptes_df['population'].replace(0, np.nan)
    comptes_df = comptes_df[['codgeo', 'dette_par_hab']].dropna()

    # --- Nombre de CatNat ---
    catnat_query = """
        SELECT codgeo, COUNT(*) as nb_catnat
        FROM catnat
        GROUP BY codgeo
    """
    catnat_df = pd.read_sql_query(catnat_query, conn)

    # --- Population 2022 ---
    pop_query = "SELECT codgeo, population as pop_2020 FROM population WHERE annee = 2020"
    pop_df = pd.read_sql_query(pop_query, conn)

    # --- Taux de natalité (naissances / population) ---
    nat_query = """
        SELECT n.codgeo,
               AVG(CAST(n.naissances AS REAL)) as moy_naissances,
               p.population
        FROM naissances_deces n
        JOIN population p ON n.codgeo = p.codgeo AND p.annee = 2020
        WHERE n.annee >= 2018
        GROUP BY n.codgeo
    """
    nat_df = pd.read_sql_query(nat_query, conn)
    nat_df['taux_natalite'] = 1000 * nat_df['moy_naissances'] / nat_df['population'].replace(0, np.nan)
    nat_df = nat_df[['codgeo', 'taux_natalite']].dropna()

    # --- Fusionner tout ---
    merged = pct.copy()
    for df_join in [revenus, csp_df, dipl_df, comptes_df, catnat_df, pop_df, nat_df]:
        merged = merged.merge(df_join, on='codgeo', how='left')

    # Sélectionner les colonnes numériques pour la corrélation
    cols_analyse = {
        'pct_gauche': '% Gauche',
        'revenu_median': 'Revenu médian',
        'pct_cadres': '% Cadres',
        'pct_ouvriers': '% Ouvriers',
        'pct_sans_diplome': '% Sans diplôme',
        'pct_diplome_sup': '% Diplôme sup.',
        'dette_par_hab': 'Dette/hab (€)',
        'nb_catnat': 'Nb CatNat',
        'pop_2020': 'Population',
        'taux_natalite': 'Taux natalité (‰)',
    }

    cols_present = [c for c in cols_analyse.keys() if c in merged.columns]
    labels = [cols_analyse[c] for c in cols_present]

    data = merged[cols_present].dropna()

    if len(data) < 10:
        print(f"  ⚠ Seulement {len(data)} communes avec données complètes, corrélation peu fiable")
        if len(data) < 3:
            return

    corr = data.corr()

    fig, ax = plt.subplots(figsize=(12, 10))
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r',
                vmin=-1, vmax=1, center=0,
                xticklabels=labels, yticklabels=labels,
                ax=ax, square=True, linewidths=0.5)

    ax.set_title("Matrice de corrélation — Indicateurs socio-économiques vs Vote\n"
                 "Hérault (34), Municipales T1 2020",
                 fontsize=14, fontweight='bold')

    plt.tight_layout()
    sauvegarder(fig, "04_heatmap_correlations.png")


# ============================================================================
# GRAPHIQUE 5 : Distribution des revenus par camp (box plot)
# ============================================================================

def plot_05_boxplot_revenus(conn):
    """Box plot : revenus médians des communes Gauche vs Droite."""
    print("\n[5/10] Box plot revenus par camp...")

    pct = calcul_pct_gauche_par_commune(conn, annee=2020, tour=1)
    revenus = pd.read_sql_query(
        'SELECT codgeo, "[disp]_mediane_(€)" as revenu_median FROM revenus', conn)

    merged = pct.merge(revenus, on='codgeo').dropna()
    merged['camp'] = merged['pct_gauche'].apply(lambda x: 'Gauche (>50%)' if x > 50 else 'Droite (≤50%)')

    if merged.empty:
        print("  ⚠ Pas de données")
        return

    fig, ax = plt.subplots(figsize=(10, 7))

    data_g = merged[merged['camp'].str.startswith('Gauche')]['revenu_median']
    data_d = merged[merged['camp'].str.startswith('Droite')]['revenu_median']

    bp = ax.boxplot([data_g, data_d],
                    tick_labels=[f'Communes\nmajorité Gauche\n(n={len(data_g)})',
                                 f'Communes\nmajorité Droite\n(n={len(data_d)})'],
                    patch_artist=True, widths=0.5)

    bp['boxes'][0].set_facecolor(COULEUR_GAUCHE)
    bp['boxes'][1].set_facecolor(COULEUR_DROITE)
    for box in bp['boxes']:
        box.set_alpha(0.7)

    # Afficher les moyennes
    if len(data_g) > 0:
        mean_g = data_g.mean()
        ax.plot(1, mean_g, 'D', color='white', markersize=8, markeredgecolor='black', zorder=5)
        ax.text(1.3, mean_g, f'Moy: {mean_g:,.0f}€', va='center', fontsize=10)
    if len(data_d) > 0:
        mean_d = data_d.mean()
        ax.plot(2, mean_d, 'D', color='white', markersize=8, markeredgecolor='black', zorder=5)
        ax.text(2.3, mean_d, f'Moy: {mean_d:,.0f}€', va='center', fontsize=10)

    ax.set_ylabel('Revenu médian (€)', fontsize=12)
    ax.set_title("Distribution des revenus médians selon le vote majoritaire\n"
                 "Hérault (34), Municipales T1 2020",
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    sauvegarder(fig, "05_boxplot_revenus_par_camp.png")


# ============================================================================
# GRAPHIQUE 6 : CSP et vote — % cadres vs % ouvriers
# ============================================================================

def plot_06_csp_vote(conn):
    """Scatter : % cadres (X) vs % ouvriers (Y), couleur par camp majoritaire."""
    print("\n[6/10] CSP et vote : cadres vs ouvriers...")

    pct = calcul_pct_gauche_par_commune(conn, annee=2020, tour=1)

    csp_df = _calcul_csp_pct(conn)

    if csp_df.empty:
        print("  ⚠ Colonnes CSP non trouvées")
        return

    merged = pct.merge(csp_df, on='codgeo')

    if merged.empty:
        print("  ⚠ Pas de données après jointure")
        return

    colors = [COULEUR_GAUCHE if g > 50 else COULEUR_DROITE for g in merged['pct_gauche']]

    fig, ax = plt.subplots(figsize=(12, 8))

    ax.scatter(merged['pct_cadres'], merged['pct_ouvriers'], c=colors,
               s=50, alpha=0.6, edgecolors='black', linewidth=0.3)

    # Annoter les communes remarquables
    noms = pd.read_sql_query("SELECT codgeo, nom FROM communes", conn)
    merged_noms = merged.merge(noms, on='codgeo')
    for codgeo, nom in COMMUNES_ANNOTEES.items():
        row = merged_noms[merged_noms['codgeo'] == codgeo]
        if not row.empty:
            ax.annotate(nom, (row['pct_cadres'].values[0], row['pct_ouvriers'].values[0]),
                        fontsize=9, fontweight='bold', alpha=0.8,
                        xytext=(5, 5), textcoords='offset points')

    # Légende
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=COULEUR_GAUCHE, alpha=0.7, label='Majorité Gauche'),
                       Patch(facecolor=COULEUR_DROITE, alpha=0.7, label='Majorité Droite')]
    ax.legend(handles=legend_elements, fontsize=11)

    ax.set_xlabel('% Cadres (actifs ayant un emploi)', fontsize=12)
    ax.set_ylabel('% Ouvriers (actifs ayant un emploi)', fontsize=12)
    ax.set_title("Structure socio-professionnelle et vote — Hérault (34)\n"
                 "Municipales T1 2020",
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    sauvegarder(fig, "06_csp_cadres_ouvriers_vote.png")


# ============================================================================
# GRAPHIQUE 7 : Évolution de la population
# ============================================================================

def plot_07_evolution_population(conn):
    """Line chart : top 10 croissance + top 10 déclin (1968-2023)."""
    print("\n[7/10] Évolution de la population...")

    # Population pour les années clés (recensements)
    annees_ref = [1968, 1975, 1982, 1990, 1999, 2006, 2011, 2016, 2022]

    query = f"""
        SELECT p.codgeo, c.nom, p.annee, p.population
        FROM population p
        JOIN communes c ON p.codgeo = c.codgeo
        WHERE p.annee IN ({','.join(str(a) for a in annees_ref)})
        ORDER BY p.codgeo, p.annee
    """
    df = pd.read_sql_query(query, conn)

    if df.empty:
        print("  ⚠ Pas de données population")
        return

    # Calculer la croissance relative entre 1968 et 2022
    pop_1968 = df[df['annee'] == 1968][['codgeo', 'nom', 'population']].rename(
        columns={'population': 'pop_1968'})
    pop_2022 = df[df['annee'] == 2022][['codgeo', 'population']].rename(
        columns={'population': 'pop_2022'})

    growth = pop_1968.merge(pop_2022, on='codgeo')
    # Filtrer les communes trop petites (< 100 hab en 1968) pour éviter les % aberrants
    growth = growth[growth['pop_1968'] >= 100]
    growth['croissance'] = 100 * (growth['pop_2022'] - growth['pop_1968']) / growth['pop_1968']

    # Top 10 croissance et top 10 déclin
    top_croissance = growth.nlargest(10, 'croissance')
    top_declin = growth.nsmallest(10, 'croissance')

    communes_selection = pd.concat([top_croissance, top_declin])['codgeo'].tolist()

    # Données complètes pour ces communes
    df_sel = df[df['codgeo'].isin(communes_selection)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Croissance
    for _, row in top_croissance.iterrows():
        commune_data = df_sel[df_sel['codgeo'] == row['codgeo']].sort_values('annee')
        label = f"{row['nom'][:20]} (+{row['croissance']:.0f}%)"
        ax1.plot(commune_data['annee'], commune_data['population'], '-o', markersize=4, label=label)

    ax1.set_xlabel('Année', fontsize=11)
    ax1.set_ylabel('Population', fontsize=11)
    ax1.set_title('Top 10 — Plus forte croissance', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=8, loc='upper left')
    ax1.grid(True, alpha=0.3)

    # Déclin
    for _, row in top_declin.iterrows():
        commune_data = df_sel[df_sel['codgeo'] == row['codgeo']].sort_values('annee')
        label = f"{row['nom'][:20]} ({row['croissance']:.0f}%)"
        ax2.plot(commune_data['annee'], commune_data['population'], '-o', markersize=4, label=label)

    ax2.set_xlabel('Année', fontsize=11)
    ax2.set_ylabel('Population', fontsize=11)
    ax2.set_title('Top 10 — Plus fort déclin', fontsize=13, fontweight='bold')
    ax2.legend(fontsize=8, loc='upper right')
    ax2.grid(True, alpha=0.3)

    plt.suptitle("Évolution de la population — Hérault (34), 1968-2022\n"
                 "(communes ≥ 100 hab. en 1968)", fontsize=14, fontweight='bold')
    plt.tight_layout()
    sauvegarder(fig, "07_evolution_population.png")


# ============================================================================
# GRAPHIQUE 8 : Finances locales et vote — dette vs % Gauche
# ============================================================================

def plot_08_dette_vs_vote(conn):
    """Scatter : dette par habitant vs % Gauche."""
    print("\n[8/10] Finances locales : dette vs % Gauche...")

    pct = calcul_pct_gauche_par_commune(conn, annee=2020, tour=1)

    # Année la plus récente disponible dans comptes_communes
    annee_cc = conn.execute(
        "SELECT MAX(annee) FROM comptes_communes WHERE dette IS NOT NULL").fetchone()[0]

    if annee_cc is None:
        print("  ⚠ Pas de données comptes_communes")
        return

    print(f"  Année comptes_communes utilisée : {annee_cc}")

    comptes_query = f"""
        SELECT c.codgeo, c.dette, p.population
        FROM comptes_communes c
        JOIN population p ON c.codgeo = p.codgeo AND p.annee = {min(annee_cc, 2022)}
        WHERE c.annee = {annee_cc} AND c.dette IS NOT NULL AND p.population > 0
    """
    comptes_df = pd.read_sql_query(comptes_query, conn)
    comptes_df['dette_par_hab'] = comptes_df['dette'] / comptes_df['population']
    comptes_df = comptes_df[['codgeo', 'dette_par_hab']].dropna()

    merged = pct.merge(comptes_df, on='codgeo')

    if merged.empty:
        print("  ⚠ Pas de données après jointure")
        return

    x = merged['dette_par_hab'].values
    y = merged['pct_gauche'].values

    correlation = np.corrcoef(x, y)[0, 1]
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)

    fig, ax = plt.subplots(figsize=(12, 8))

    colors = [COULEUR_GAUCHE if g > 50 else COULEUR_DROITE for g in y]
    ax.scatter(x, y, c=colors, s=50, alpha=0.6, edgecolors='black', linewidth=0.3)

    x_line = np.linspace(x.min(), x.max(), 100)
    ax.plot(x_line, p(x_line), 'k--', alpha=0.6, linewidth=2,
            label=f'Tendance (r = {correlation:.3f})')

    ax.axhline(y=50, color='gray', linestyle=':', alpha=0.4)

    # Annoter les communes remarquables
    noms = pd.read_sql_query("SELECT codgeo, nom FROM communes", conn)
    merged_noms = merged.merge(noms, on='codgeo')
    for codgeo, nom in COMMUNES_ANNOTEES.items():
        row = merged_noms[merged_noms['codgeo'] == codgeo]
        if not row.empty:
            ax.annotate(nom, (row['dette_par_hab'].values[0], row['pct_gauche'].values[0]),
                        fontsize=9, fontweight='bold', alpha=0.8,
                        xytext=(5, 5), textcoords='offset points')

    ax.set_xlabel('Dette par habitant (€)', fontsize=12)
    ax.set_ylabel('% Vote Gauche (T1 2020)', fontsize=12)
    ax.set_title(f"Finances locales et vote — Dette par habitant vs % Gauche\n"
                 f"Hérault (34), Corrélation : r = {correlation:.3f}",
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    sauvegarder(fig, "08_dette_vs_vote.png")


# ============================================================================
# GRAPHIQUE 9 : Diplômes et vote — % diplôme supérieur vs % Gauche
# ============================================================================

def plot_09_diplomes_vs_vote(conn):
    """Scatter : % diplôme supérieur vs % Gauche."""
    print("\n[9/10] Diplômes et vote : % diplôme supérieur vs % Gauche...")

    pct = calcul_pct_gauche_par_commune(conn, annee=2020, tour=1)

    dipl_query = """
        SELECT codgeo,
               p22_nscol15p as pop_nscol,
               (p22_nscol15p_sup2 + p22_nscol15p_sup34 + p22_nscol15p_sup5) as diplome_sup
        FROM diplomes
    """
    dipl_df = pd.read_sql_query(dipl_query, conn)
    dipl_df['pct_diplome_sup'] = 100 * dipl_df['diplome_sup'] / dipl_df['pop_nscol'].replace(0, np.nan)
    dipl_df = dipl_df[['codgeo', 'pct_diplome_sup']].dropna()

    merged = pct.merge(dipl_df, on='codgeo')

    if merged.empty:
        print("  ⚠ Pas de données après jointure")
        return

    x = merged['pct_diplome_sup'].values
    y = merged['pct_gauche'].values

    correlation = np.corrcoef(x, y)[0, 1]
    z = np.polyfit(x, y, 1)
    p_line = np.poly1d(z)

    fig, ax = plt.subplots(figsize=(12, 8))

    colors = [COULEUR_GAUCHE if g > 50 else COULEUR_DROITE for g in y]
    ax.scatter(x, y, c=colors, s=50, alpha=0.6, edgecolors='black', linewidth=0.3)

    x_range = np.linspace(x.min(), x.max(), 100)
    ax.plot(x_range, p_line(x_range), 'k--', alpha=0.6, linewidth=2,
            label=f'Tendance (r = {correlation:.3f})')

    ax.axhline(y=50, color='gray', linestyle=':', alpha=0.4)

    # Annoter les communes remarquables
    noms = pd.read_sql_query("SELECT codgeo, nom FROM communes", conn)
    merged_noms = merged.merge(noms, on='codgeo')
    for codgeo, nom in COMMUNES_ANNOTEES.items():
        row = merged_noms[merged_noms['codgeo'] == codgeo]
        if not row.empty:
            ax.annotate(nom, (row['pct_diplome_sup'].values[0], row['pct_gauche'].values[0]),
                        fontsize=9, fontweight='bold', alpha=0.8,
                        xytext=(5, 5), textcoords='offset points')

    ax.set_xlabel('% Diplôme supérieur (Bac+2 et plus)', fontsize=12)
    ax.set_ylabel('% Vote Gauche (T1 2020)', fontsize=12)
    ax.set_title(f"Diplômes et vote — % Diplôme supérieur vs % Gauche\n"
                 f"Hérault (34), Corrélation : r = {correlation:.3f}",
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    sauvegarder(fig, "09_diplomes_vs_vote.png")


# ============================================================================
# GRAPHIQUE 10 : Catastrophes naturelles et vote
# ============================================================================

def plot_10_catnat_vs_vote(conn):
    """Bar chart horizontal : top 20 communes par nb CatNat, coloré par camp."""
    print("\n[10/10] Catastrophes naturelles et vote...")

    pct = calcul_pct_gauche_par_commune(conn, annee=2020, tour=1)

    catnat_query = """
        SELECT c.codgeo, com.nom, COUNT(*) as nb_catnat
        FROM catnat c
        JOIN communes com ON c.codgeo = com.codgeo
        GROUP BY c.codgeo
        ORDER BY nb_catnat DESC
        LIMIT 20
    """
    catnat_df = pd.read_sql_query(catnat_query, conn)

    if catnat_df.empty:
        print("  ⚠ Pas de données CatNat")
        return

    merged = catnat_df.merge(pct, on='codgeo', how='left')
    merged['camp'] = merged['pct_gauche'].apply(
        lambda x: 'Gauche' if pd.notna(x) and x > 50 else 'Droite')
    merged['color'] = merged['camp'].apply(
        lambda x: COULEUR_GAUCHE if x == 'Gauche' else COULEUR_DROITE)

    # Inverser pour afficher du plus grand en haut
    merged = merged.iloc[::-1]

    fig, ax = plt.subplots(figsize=(12, 8))

    ax.barh(merged['nom'], merged['nb_catnat'], color=merged['color'], alpha=0.8, edgecolor='black', linewidth=0.3)

    # Ajouter le nombre sur chaque barre
    for i, (_, row) in enumerate(merged.iterrows()):
        ax.text(row['nb_catnat'] + 0.3, i, str(row['nb_catnat']),
                va='center', fontsize=9)

    # Légende
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=COULEUR_GAUCHE, alpha=0.8, label='Majorité Gauche'),
                       Patch(facecolor=COULEUR_DROITE, alpha=0.8, label='Majorité Droite')]
    ax.legend(handles=legend_elements, fontsize=11, loc='lower right')

    ax.set_xlabel("Nombre d'arrêtés CatNat", fontsize=12)
    ax.set_title("Top 20 communes — Arrêtés de catastrophe naturelle\n"
                 "Hérault (34), couleur = camp majoritaire (T1 2020)",
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()
    sauvegarder(fig, "10_catnat_vs_vote.png")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("  ANALYSE EXPLORATOIRE — PHASE 3")
    print("  Département : Hérault (34)")
    print("  Source : SQLite " + DB_PATH)
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"\n⚠ Base SQLite introuvable : {DB_PATH}")
        print("  Lancez d'abord : python main.py etl")
        return

    conn = get_conn()

    plot_01_evolution_vote(conn)
    plot_02_carte_communes(conn)
    plot_03_revenu_vs_vote(conn)
    plot_04_heatmap_correlations(conn)
    plot_05_boxplot_revenus(conn)
    plot_06_csp_vote(conn)
    plot_07_evolution_population(conn)
    plot_08_dette_vs_vote(conn)
    plot_09_diplomes_vs_vote(conn)
    plot_10_catnat_vs_vote(conn)

    conn.close()

    # Compter les fichiers générés
    fichiers = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.png')]
    print(f"\n{'=' * 60}")
    print(f"  TERMINÉ — {len(fichiers)} graphiques générés dans {OUTPUT_DIR}/")
    for f in sorted(fichiers):
        print(f"    {f}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

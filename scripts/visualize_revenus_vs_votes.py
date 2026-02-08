#!/usr/bin/env python3
"""
Visualisation comparative : Revenus médians vs Résultats électoraux
Cartes de France côte à côte + corrélation
"""

import csv
import os
import ssl
import urllib.request
from collections import defaultdict

ssl._create_default_https_context = ssl._create_unverified_context

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

try:
    import geopandas as gpd
except ImportError:
    os.system("pip3 install geopandas")
    import geopandas as gpd

# Configuration
REVENUS_FILE = "data/input/economie/revenu-des-francais-a-la-commune-1765372688826.csv"
ELECTIONS_FILE = "data/output/candidats_classified.txt"
OUTPUT_DIR = "graphiques/comparatifs"
GEOJSON_PATH = "data/output/departements.geojson"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_revenus_by_dept():
    """Charge les revenus et agrège par département"""
    print("Chargement des revenus par commune...")

    dept_revenus = defaultdict(list)
    dept_menages = defaultdict(int)

    with open(REVENUS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        headers = next(reader)

        # Trouver les indices des colonnes
        code_idx = headers.index('Code géographique')
        mediane_idx = headers.index('[DISP] Médiane (€)')
        menages_idx = headers.index('[DISP] Nbre de ménages fiscaux')

        for row in reader:
            if len(row) <= max(code_idx, mediane_idx, menages_idx):
                continue

            code = row[code_idx].strip()
            mediane_str = row[mediane_idx].strip()
            menages_str = row[menages_idx].strip()

            if not mediane_str or not code:
                continue

            # Extraire le département (2 premiers caractères, ou 3 pour DOM)
            if code.startswith('97'):
                dept = code[:3]
            else:
                dept = code[:2]

            try:
                mediane = float(mediane_str.replace(',', '.'))
                menages = int(menages_str) if menages_str else 1
                # Pondérer par le nombre de ménages
                dept_revenus[dept].append((mediane, menages))
                dept_menages[dept] += menages
            except:
                continue

    # Calculer la médiane pondérée par département
    dept_mediane = {}
    for dept, values in dept_revenus.items():
        total_weighted = sum(m * n for m, n in values)
        total_menages = sum(n for _, n in values)
        if total_menages > 0:
            dept_mediane[dept] = total_weighted / total_menages

    print(f"  {len(dept_mediane)} départements chargés")
    return dept_mediane


def load_votes_by_dept(election_filter='_pres_t1'):
    """Charge les votes et agrège par département"""
    print(f"Chargement des votes ({election_filter})...")

    dept_votes = defaultdict(lambda: {'gauche': 0, 'droite': 0})

    with open(ELECTIONS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        headers = next(reader)

        col_idx = {h: i for i, h in enumerate(headers)}

        for row in reader:
            if len(row) <= col_idx.get('Camp', 999):
                continue

            election = row[col_idx['id_election']]
            if election_filter not in election:
                continue

            dept = row[col_idx['Code du département']].strip()
            try:
                voix = int(row[col_idx['Voix']])
            except:
                voix = 0

            camp = row[col_idx['Camp']].strip()

            if camp == 'Gauche':
                dept_votes[dept]['gauche'] += voix
            else:
                dept_votes[dept]['droite'] += voix

    # Calculer % gauche
    dept_pct_gauche = {}
    for dept, votes in dept_votes.items():
        total = votes['gauche'] + votes['droite']
        if total > 0:
            dept_pct_gauche[dept] = 100 * votes['gauche'] / total

    print(f"  {len(dept_pct_gauche)} départements chargés")
    return dept_pct_gauche


def plot_side_by_side_maps(dept_revenus, dept_pct_gauche, year="Global"):
    """Crée deux cartes côte à côte : revenus vs votes"""
    print(f"\nCréation des cartes comparatives ({year})...")

    gdf = gpd.read_file(GEOJSON_PATH)

    # Ajouter les données
    gdf['revenu_median'] = gdf['code'].map(dept_revenus)
    gdf['pct_gauche'] = gdf['code'].map(dept_pct_gauche)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

    # Carte 1: Revenus médians
    cmap_revenus = plt.cm.YlOrRd
    gdf.plot(column='revenu_median', cmap=cmap_revenus, linewidth=0.5, ax=ax1,
             edgecolor='0.5', legend=True, missing_kwds={'color': 'lightgray'},
             legend_kwds={'label': 'Revenu médian (€)', 'shrink': 0.6})
    ax1.axis('off')
    ax1.set_title('Revenu médian par département\n(plus foncé = plus riche)',
                  fontsize=14, fontweight='bold')

    # Carte 2: Votes Gauche/Droite
    cmap_votes = mcolors.LinearSegmentedColormap.from_list('', ['#E94F37', '#FFFFFF', '#2E86AB'])
    gdf.plot(column='pct_gauche', cmap=cmap_votes, linewidth=0.5, ax=ax2,
             edgecolor='0.5', legend=True, vmin=20, vmax=60,
             missing_kwds={'color': 'lightgray'},
             legend_kwds={'label': '% Gauche', 'shrink': 0.6})
    ax2.axis('off')
    ax2.set_title(f'Vote Gauche/Droite - Présidentielles T1 {year}\n(Bleu = Gauche, Rouge = Droite)',
                  fontsize=14, fontweight='bold')

    plt.suptitle('Comparaison : Revenus vs Votes en France métropolitaine\n(LREM classé à droite)',
                 fontsize=16, fontweight='bold', y=1.02)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, f"carte_revenus_vs_votes_{year}.png")
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Sauvegardé: {path}")


def plot_correlation(dept_revenus, dept_pct_gauche):
    """Scatter plot : corrélation revenus vs vote gauche"""
    print("\nCréation du graphique de corrélation...")

    # Préparer les données communes
    common_depts = set(dept_revenus.keys()) & set(dept_pct_gauche.keys())

    revenus = []
    pct_gauche = []
    labels = []

    for dept in common_depts:
        if dept.isdigit() and int(dept) <= 95 or dept in ['2A', '2B']:
            revenus.append(dept_revenus[dept])
            pct_gauche.append(dept_pct_gauche[dept])
            labels.append(dept)

    revenus = np.array(revenus)
    pct_gauche = np.array(pct_gauche)

    # Calculer la corrélation
    correlation = np.corrcoef(revenus, pct_gauche)[0, 1]

    # Régression linéaire
    z = np.polyfit(revenus, pct_gauche, 1)
    p = np.poly1d(z)

    fig, ax = plt.subplots(figsize=(12, 8))

    # Colorer les points selon le vote
    colors = ['#2E86AB' if g > 50 else '#E94F37' for g in pct_gauche]

    ax.scatter(revenus, pct_gauche, c=colors, s=80, alpha=0.7, edgecolors='black', linewidth=0.5)

    # Ligne de tendance
    x_line = np.linspace(revenus.min(), revenus.max(), 100)
    ax.plot(x_line, p(x_line), 'k--', alpha=0.5, linewidth=2, label=f'Tendance (r = {correlation:.3f})')

    # Ligne 50%
    ax.axhline(y=50, color='gray', linestyle=':', alpha=0.5)

    # Annoter quelques départements
    for i, dept in enumerate(labels):
        if pct_gauche[i] > 55 or pct_gauche[i] < 25 or revenus[i] > 28000 or revenus[i] < 19000:
            ax.annotate(dept, (revenus[i], pct_gauche[i]), fontsize=8, alpha=0.7)

    ax.set_xlabel('Revenu médian (€)', fontsize=12)
    ax.set_ylabel('% Vote Gauche (Présidentielles T1)', fontsize=12)
    ax.set_title(f'Corrélation : Revenus vs Vote Gauche par département\n(Corrélation = {correlation:.3f})',
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "correlation_revenus_votes.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Sauvegardé: {path}")

    return correlation


def plot_revenus_by_vote(dept_revenus, dept_pct_gauche):
    """Box plot : distribution des revenus selon le vote majoritaire"""
    print("\nCréation du box plot revenus par camp...")

    revenus_gauche = []
    revenus_droite = []

    for dept in set(dept_revenus.keys()) & set(dept_pct_gauche.keys()):
        if dept.isdigit() and int(dept) <= 95 or dept in ['2A', '2B']:
            if dept_pct_gauche[dept] > 50:
                revenus_gauche.append(dept_revenus[dept])
            else:
                revenus_droite.append(dept_revenus[dept])

    fig, ax = plt.subplots(figsize=(10, 7))

    bp = ax.boxplot([revenus_gauche, revenus_droite],
                     labels=['Départements\nmajorité Gauche', 'Départements\nmajorité Droite'],
                     patch_artist=True)

    bp['boxes'][0].set_facecolor('#2E86AB')
    bp['boxes'][1].set_facecolor('#E94F37')

    for box in bp['boxes']:
        box.set_alpha(0.7)

    ax.set_ylabel('Revenu médian (€)', fontsize=12)
    ax.set_title('Distribution des revenus selon le vote majoritaire\n(Présidentielles T1 - LREM à droite)',
                 fontsize=14, fontweight='bold')

    # Ajouter les moyennes
    mean_g = np.mean(revenus_gauche)
    mean_d = np.mean(revenus_droite)
    ax.text(1, mean_g, f'Moy: {mean_g:,.0f}€', ha='center', va='bottom', fontsize=10)
    ax.text(2, mean_d, f'Moy: {mean_d:,.0f}€', ha='center', va='bottom', fontsize=10)

    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "boxplot_revenus_par_camp.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Sauvegardé: {path}")


def plot_top_bottom_depts(dept_revenus, dept_pct_gauche):
    """Top/Bottom départements : riches/pauvres vs leur vote"""
    print("\nCréation du graphique Top/Bottom départements...")

    # Fusionner les données
    data = []
    for dept in set(dept_revenus.keys()) & set(dept_pct_gauche.keys()):
        if dept.isdigit() and int(dept) <= 95 or dept in ['2A', '2B']:
            data.append((dept, dept_revenus[dept], dept_pct_gauche[dept]))

    # Trier par revenu
    data_sorted = sorted(data, key=lambda x: x[1], reverse=True)

    top_10 = data_sorted[:10]
    bottom_10 = data_sorted[-10:][::-1]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Top 10 (plus riches)
    depts_t = [d[0] for d in top_10]
    revenus_t = [d[1] for d in top_10]
    colors_t = ['#2E86AB' if d[2] > 50 else '#E94F37' for d in top_10]

    bars1 = ax1.barh(depts_t, revenus_t, color=colors_t, alpha=0.7)
    ax1.set_xlabel('Revenu médian (€)')
    ax1.set_title('10 départements les plus RICHES\n(couleur = vote majoritaire)', fontweight='bold')
    ax1.invert_yaxis()

    for i, (d, r, g) in enumerate(top_10):
        ax1.text(r + 200, i, f'{g:.0f}% G', va='center', fontsize=9)

    # Bottom 10 (plus pauvres)
    depts_b = [d[0] for d in bottom_10]
    revenus_b = [d[1] for d in bottom_10]
    colors_b = ['#2E86AB' if d[2] > 50 else '#E94F37' for d in bottom_10]

    bars2 = ax2.barh(depts_b, revenus_b, color=colors_b, alpha=0.7)
    ax2.set_xlabel('Revenu médian (€)')
    ax2.set_title('10 départements les plus MODESTES\n(couleur = vote majoritaire)', fontweight='bold')
    ax2.invert_yaxis()

    for i, (d, r, g) in enumerate(bottom_10):
        ax2.text(r + 200, i, f'{g:.0f}% G', va='center', fontsize=9)

    # Légende commune
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='#2E86AB', alpha=0.7, label='Majorité Gauche'),
                       Patch(facecolor='#E94F37', alpha=0.7, label='Majorité Droite')]
    fig.legend(handles=legend_elements, loc='upper center', ncol=2, fontsize=11,
               bbox_to_anchor=(0.5, 0.02))

    plt.suptitle('Revenus et votes par département (Présidentielles T1)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)

    path = os.path.join(OUTPUT_DIR, "top_bottom_revenus_votes.png")
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Sauvegardé: {path}")


def main():
    print("=" * 70)
    print("COMPARAISON REVENUS VS VOTES")
    print("=" * 70)

    # Charger les données
    dept_revenus = load_revenus_by_dept()
    dept_pct_gauche = load_votes_by_dept('_pres_t1')

    # Générer les graphiques
    plot_side_by_side_maps(dept_revenus, dept_pct_gauche, "2002-2022")
    correlation = plot_correlation(dept_revenus, dept_pct_gauche)
    plot_revenus_by_vote(dept_revenus, dept_pct_gauche)
    plot_top_bottom_depts(dept_revenus, dept_pct_gauche)

    print("\n" + "=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    print(f"  Corrélation revenus/vote gauche: {correlation:.3f}")
    if correlation > 0:
        print("  → Les départements plus riches votent légèrement plus à gauche")
    else:
        print("  → Les départements plus riches votent légèrement plus à droite")

    print(f"\n  Graphiques sauvegardés dans: {OUTPUT_DIR}/")
    print("=" * 70)


if __name__ == "__main__":
    main()

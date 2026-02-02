#!/usr/bin/env python3
"""
Visualisation des tendances électorales - Présidentielles françaises
Graphiques: Courbe évolution, Carte de France, Heatmap, Barres, Top départements
"""

import csv
import json
import os
import ssl
import urllib.request
from collections import defaultdict

# Désactiver la vérification SSL (pour le téléchargement du GeoJSON)
ssl._create_default_https_context = ssl._create_unverified_context

# Vérifier les dépendances
try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import numpy as np
except ImportError:
    print("Installation de matplotlib...")
    os.system("pip3 install matplotlib numpy")
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import numpy as np

try:
    import geopandas as gpd
except ImportError:
    print("Installation de geopandas...")
    os.system("pip3 install geopandas")
    import geopandas as gpd

# Configuration
INPUT_FILE = "candidats_classified.txt"
SEPARATOR = ";"
OUTPUT_DIR = "graphiques_presidentielles"

# Créer le dossier de sortie
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mapping des codes département vers noms
DEPT_NAMES = {
    '01': 'Ain', '02': 'Aisne', '03': 'Allier', '04': 'Alpes-de-Haute-Provence',
    '05': 'Hautes-Alpes', '06': 'Alpes-Maritimes', '07': 'Ardèche', '08': 'Ardennes',
    '09': 'Ariège', '10': 'Aube', '11': 'Aude', '12': 'Aveyron',
    '13': 'Bouches-du-Rhône', '14': 'Calvados', '15': 'Cantal', '16': 'Charente',
    '17': 'Charente-Maritime', '18': 'Cher', '19': 'Corrèze', '21': 'Côte-d\'Or',
    '22': 'Côtes-d\'Armor', '23': 'Creuse', '24': 'Dordogne', '25': 'Doubs',
    '26': 'Drôme', '27': 'Eure', '28': 'Eure-et-Loir', '29': 'Finistère',
    '2A': 'Corse-du-Sud', '2B': 'Haute-Corse', '30': 'Gard', '31': 'Haute-Garonne',
    '32': 'Gers', '33': 'Gironde', '34': 'Hérault', '35': 'Ille-et-Vilaine',
    '36': 'Indre', '37': 'Indre-et-Loire', '38': 'Isère', '39': 'Jura',
    '40': 'Landes', '41': 'Loir-et-Cher', '42': 'Loire', '43': 'Haute-Loire',
    '44': 'Loire-Atlantique', '45': 'Loiret', '46': 'Lot', '47': 'Lot-et-Garonne',
    '48': 'Lozère', '49': 'Maine-et-Loire', '50': 'Manche', '51': 'Marne',
    '52': 'Haute-Marne', '53': 'Mayenne', '54': 'Meurthe-et-Moselle', '55': 'Meuse',
    '56': 'Morbihan', '57': 'Moselle', '58': 'Nièvre', '59': 'Nord',
    '60': 'Oise', '61': 'Orne', '62': 'Pas-de-Calais', '63': 'Puy-de-Dôme',
    '64': 'Pyrénées-Atlantiques', '65': 'Hautes-Pyrénées', '66': 'Pyrénées-Orientales',
    '67': 'Bas-Rhin', '68': 'Haut-Rhin', '69': 'Rhône', '70': 'Haute-Saône',
    '71': 'Saône-et-Loire', '72': 'Sarthe', '73': 'Savoie', '74': 'Haute-Savoie',
    '75': 'Paris', '76': 'Seine-Maritime', '77': 'Seine-et-Marne', '78': 'Yvelines',
    '79': 'Deux-Sèvres', '80': 'Somme', '81': 'Tarn', '82': 'Tarn-et-Garonne',
    '83': 'Var', '84': 'Vaucluse', '85': 'Vendée', '86': 'Vienne',
    '87': 'Haute-Vienne', '88': 'Vosges', '89': 'Yonne', '90': 'Territoire de Belfort',
    '91': 'Essonne', '92': 'Hauts-de-Seine', '93': 'Seine-Saint-Denis',
    '94': 'Val-de-Marne', '95': 'Val-d\'Oise',
    '971': 'Guadeloupe', '972': 'Martinique', '973': 'Guyane',
    '974': 'La Réunion', '976': 'Mayotte'
}


def download_france_geojson():
    """Télécharge le GeoJSON des départements français"""
    geojson_path = os.path.join(OUTPUT_DIR, "departements.geojson")
    if not os.path.exists(geojson_path):
        print("Téléchargement du fond de carte des départements...")
        url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson"
        urllib.request.urlretrieve(url, geojson_path)
    return geojson_path


def load_and_aggregate_data():
    """Charge et agrège les données des présidentielles"""
    print("Chargement et agrégation des données présidentielles...")

    # Structure: {année: {département: {'gauche': voix, 'droite': voix}}}
    data_by_year_dept = defaultdict(lambda: defaultdict(lambda: {'gauche': 0, 'droite': 0}))

    # Structure: {année: {'gauche': voix, 'droite': voix}}
    data_by_year = defaultdict(lambda: {'gauche': 0, 'droite': 0})

    col_idx = {}
    total_lines = 0
    pres_lines = 0

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=SEPARATOR)
        headers = next(reader)

        for i, h in enumerate(headers):
            col_idx[h] = i

        for row in reader:
            total_lines += 1

            if total_lines % 5_000_000 == 0:
                print(f"  {total_lines:,} lignes lues...")

            if len(row) <= col_idx.get('Camp', 999):
                continue

            # Filtrer sur les présidentielles T1 uniquement (T2 biaisé car Macron/Le Pen = droite)
            election = row[col_idx['id_election']]
            if '_pres_t1' not in election:
                continue

            pres_lines += 1

            # Extraire l'année
            year = election.split('_')[0]

            # Extraire département et voix
            dept = row[col_idx['Code du département']].strip()
            try:
                voix = int(row[col_idx['Voix']])
            except:
                voix = 0

            camp = row[col_idx['Camp']].strip()

            # Agréger
            if camp == "Gauche":
                data_by_year_dept[year][dept]['gauche'] += voix
                data_by_year[year]['gauche'] += voix
            else:
                data_by_year_dept[year][dept]['droite'] += voix
                data_by_year[year]['droite'] += voix

    print(f"  Total: {total_lines:,} lignes, dont {pres_lines:,} présidentielles")

    return dict(data_by_year), dict(data_by_year_dept)


def plot_evolution_curve(data_by_year):
    """Graphique 1: Courbe d'évolution Gauche/Droite par année"""
    print("\nCréation du graphique d'évolution...")

    years = sorted(data_by_year.keys())
    gauche_pct = []
    droite_pct = []

    for year in years:
        total = data_by_year[year]['gauche'] + data_by_year[year]['droite']
        if total > 0:
            gauche_pct.append(100 * data_by_year[year]['gauche'] / total)
            droite_pct.append(100 * data_by_year[year]['droite'] / total)
        else:
            gauche_pct.append(0)
            droite_pct.append(0)

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.plot(years, gauche_pct, 'b-o', linewidth=3, markersize=10, label='Gauche')
    ax.plot(years, droite_pct, 'r-o', linewidth=3, markersize=10, label='Droite')

    # Ajouter les valeurs sur les points
    for i, year in enumerate(years):
        ax.annotate(f'{gauche_pct[i]:.1f}%', (year, gauche_pct[i]), textcoords="offset points",
                    xytext=(0, 10), ha='center', fontsize=10, color='blue')
        ax.annotate(f'{droite_pct[i]:.1f}%', (year, droite_pct[i]), textcoords="offset points",
                    xytext=(0, -15), ha='center', fontsize=10, color='red')

    ax.set_xlabel('Année', fontsize=12)
    ax.set_ylabel('Pourcentage des voix', fontsize=12)
    ax.set_title('Évolution Gauche/Droite aux Présidentielles T1 (2002-2022)\n(LREM classé à droite)',
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "1_evolution_gauche_droite.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Sauvegardé: {path}")


def plot_stacked_bars(data_by_year):
    """Graphique 2: Barres empilées par élection"""
    print("\nCréation du graphique en barres...")

    years = sorted(data_by_year.keys())
    gauche_pct = []
    droite_pct = []

    for year in years:
        total = data_by_year[year]['gauche'] + data_by_year[year]['droite']
        if total > 0:
            gauche_pct.append(100 * data_by_year[year]['gauche'] / total)
            droite_pct.append(100 * data_by_year[year]['droite'] / total)
        else:
            gauche_pct.append(0)
            droite_pct.append(0)

    fig, ax = plt.subplots(figsize=(12, 7))

    x = np.arange(len(years))
    width = 0.6

    bars1 = ax.bar(x, gauche_pct, width, label='Gauche', color='#2E86AB')
    bars2 = ax.bar(x, droite_pct, width, bottom=gauche_pct, label='Droite', color='#E94F37')

    # Ajouter les pourcentages
    for i, (g, d) in enumerate(zip(gauche_pct, droite_pct)):
        ax.text(i, g/2, f'{g:.1f}%', ha='center', va='center', color='white', fontweight='bold')
        ax.text(i, g + d/2, f'{d:.1f}%', ha='center', va='center', color='white', fontweight='bold')

    ax.set_xlabel('Année', fontsize=12)
    ax.set_ylabel('Pourcentage des voix', fontsize=12)
    ax.set_title('Répartition Gauche/Droite par Présidentielle\n(LREM classé à droite)',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(years)
    ax.legend(loc='upper right', fontsize=12)
    ax.set_ylim(0, 100)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "2_barres_empilees.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Sauvegardé: {path}")


def plot_heatmap(data_by_year_dept):
    """Graphique 3: Heatmap départements × années"""
    print("\nCréation de la heatmap...")

    years = sorted(data_by_year_dept.keys())

    # Collecter tous les départements métropolitains
    all_depts = set()
    for year_data in data_by_year_dept.values():
        all_depts.update(year_data.keys())

    # Filtrer sur métropole (codes 01-95, 2A, 2B)
    metro_depts = sorted([d for d in all_depts if (d.isdigit() and int(d) <= 95) or d in ['2A', '2B']])

    # Créer la matrice (% gauche par département/année)
    matrix = []
    dept_labels = []

    for dept in metro_depts:
        row = []
        for year in years:
            if dept in data_by_year_dept[year]:
                total = data_by_year_dept[year][dept]['gauche'] + data_by_year_dept[year][dept]['droite']
                if total > 0:
                    pct_gauche = 100 * data_by_year_dept[year][dept]['gauche'] / total
                else:
                    pct_gauche = 50
            else:
                pct_gauche = 50
            row.append(pct_gauche)
        matrix.append(row)
        dept_labels.append(f"{dept}")

    matrix = np.array(matrix)

    fig, ax = plt.subplots(figsize=(14, 20))

    # Colormap: bleu (gauche) à rouge (droite)
    cmap = mcolors.LinearSegmentedColormap.from_list('', ['#E94F37', 'white', '#2E86AB'])

    im = ax.imshow(matrix, cmap=cmap, aspect='auto', vmin=0, vmax=100)

    ax.set_xticks(np.arange(len(years)))
    ax.set_xticklabels(years, fontsize=11)
    ax.set_yticks(np.arange(len(dept_labels)))
    ax.set_yticklabels(dept_labels, fontsize=8)

    ax.set_xlabel('Année', fontsize=12)
    ax.set_ylabel('Département', fontsize=12)
    ax.set_title('% de voix Gauche par département et année\n(Bleu = Gauche, Rouge = Droite)',
                 fontsize=14, fontweight='bold')

    cbar = plt.colorbar(im, ax=ax, shrink=0.5)
    cbar.set_label('% Gauche', fontsize=11)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "3_heatmap_departements.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Sauvegardé: {path}")


def plot_top_departments(data_by_year_dept):
    """Graphique 4: Top départements les plus à gauche et à droite"""
    print("\nCréation du graphique Top départements...")

    # Agréger sur toutes les années
    dept_totals = defaultdict(lambda: {'gauche': 0, 'droite': 0})

    for year_data in data_by_year_dept.values():
        for dept, votes in year_data.items():
            dept_totals[dept]['gauche'] += votes['gauche']
            dept_totals[dept]['droite'] += votes['droite']

    # Calculer % gauche
    dept_pct_gauche = {}
    for dept, votes in dept_totals.items():
        total = votes['gauche'] + votes['droite']
        if total > 0:
            dept_pct_gauche[dept] = 100 * votes['gauche'] / total

    # Filtrer métropole
    metro = {d: p for d, p in dept_pct_gauche.items()
             if (d.isdigit() and int(d) <= 95) or d in ['2A', '2B']}

    # Trier
    sorted_depts = sorted(metro.items(), key=lambda x: x[1], reverse=True)

    top_gauche = sorted_depts[:15]
    top_droite = sorted_depts[-15:][::-1]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Top Gauche
    depts_g = [f"{d} ({DEPT_NAMES.get(d, d)[:15]})" for d, _ in top_gauche]
    pcts_g = [p for _, p in top_gauche]
    colors_g = ['#2E86AB' for _ in top_gauche]

    ax1.barh(depts_g, pcts_g, color=colors_g)
    ax1.set_xlabel('% Gauche')
    ax1.set_title('Top 15 départements les plus à GAUCHE', fontweight='bold')
    ax1.set_xlim(0, 100)
    for i, v in enumerate(pcts_g):
        ax1.text(v + 1, i, f'{v:.1f}%', va='center')
    ax1.invert_yaxis()

    # Top Droite
    depts_d = [f"{d} ({DEPT_NAMES.get(d, d)[:15]})" for d, _ in top_droite]
    pcts_d = [100 - p for _, p in top_droite]  # % droite
    colors_d = ['#E94F37' for _ in top_droite]

    ax2.barh(depts_d, pcts_d, color=colors_d)
    ax2.set_xlabel('% Droite')
    ax2.set_title('Top 15 départements les plus à DROITE', fontweight='bold')
    ax2.set_xlim(0, 100)
    for i, v in enumerate(pcts_d):
        ax2.text(v + 1, i, f'{v:.1f}%', va='center')
    ax2.invert_yaxis()

    plt.suptitle('Bastions électoraux aux Présidentielles T1 (2002-2022)\n(LREM classé à droite)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "4_top_departements.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Sauvegardé: {path}")


def plot_maps(data_by_year_dept):
    """Graphique 5: Cartes de France par année"""
    print("\nCréation des cartes de France...")

    geojson_path = download_france_geojson()
    gdf = gpd.read_file(geojson_path)

    years = sorted(data_by_year_dept.keys())

    # Créer une carte par année + une carte globale
    all_years = years + ['Global']

    for year in all_years:
        print(f"  Carte {year}...")

        # Calculer % gauche par département
        if year == 'Global':
            dept_totals = defaultdict(lambda: {'gauche': 0, 'droite': 0})
            for y_data in data_by_year_dept.values():
                for dept, votes in y_data.items():
                    dept_totals[dept]['gauche'] += votes['gauche']
                    dept_totals[dept]['droite'] += votes['droite']

            dept_pct = {}
            for dept, votes in dept_totals.items():
                total = votes['gauche'] + votes['droite']
                if total > 0:
                    dept_pct[dept] = 100 * votes['gauche'] / total
        else:
            dept_pct = {}
            for dept, votes in data_by_year_dept[year].items():
                total = votes['gauche'] + votes['droite']
                if total > 0:
                    dept_pct[dept] = 100 * votes['gauche'] / total

        # Ajouter les données au GeoDataFrame
        gdf['pct_gauche'] = gdf['code'].map(dept_pct)
        gdf['pct_gauche'] = gdf['pct_gauche'].fillna(50)

        # Déterminer le camp gagnant
        gdf['camp'] = gdf['pct_gauche'].apply(lambda x: 'Gauche' if x > 50 else 'Droite')

        # Créer la carte
        fig, ax = plt.subplots(figsize=(12, 12))

        # Colormap
        cmap = mcolors.LinearSegmentedColormap.from_list('', ['#E94F37', '#FFFFFF', '#2E86AB'])

        gdf.plot(column='pct_gauche', cmap=cmap, linewidth=0.5, ax=ax,
                 edgecolor='0.5', legend=True, vmin=20, vmax=80,
                 legend_kwds={'label': '% Gauche', 'shrink': 0.6})

        ax.axis('off')

        if year == 'Global':
            title = 'Vote Gauche/Droite - Toutes Présidentielles T1 (2002-2022)'
        else:
            title = f'Vote Gauche/Droite - Présidentielle {year}'

        ax.set_title(f'{title}\n(Bleu = Gauche, Rouge = Droite, LREM à droite)',
                     fontsize=14, fontweight='bold')

        plt.tight_layout()
        path = os.path.join(OUTPUT_DIR, f"5_carte_{year}.png")
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()

    print(f"  Cartes sauvegardées dans {OUTPUT_DIR}/")


def main():
    print("=" * 70)
    print("VISUALISATION DES PRÉSIDENTIELLES FRANÇAISES")
    print("Gauche vs Droite (LREM classé à droite)")
    print("=" * 70)

    # Charger et agréger les données
    data_by_year, data_by_year_dept = load_and_aggregate_data()

    # Afficher un résumé
    print("\nRésumé des données:")
    for year in sorted(data_by_year.keys()):
        total = data_by_year[year]['gauche'] + data_by_year[year]['droite']
        pct_g = 100 * data_by_year[year]['gauche'] / total if total > 0 else 0
        print(f"  {year}: {total:,} voix - Gauche {pct_g:.1f}%")

    # Générer les graphiques
    plot_evolution_curve(data_by_year)
    plot_stacked_bars(data_by_year)
    plot_heatmap(data_by_year_dept)
    plot_top_departments(data_by_year_dept)
    plot_maps(data_by_year_dept)

    print("\n" + "=" * 70)
    print(f"TERMINÉ ! Tous les graphiques sont dans: {OUTPUT_DIR}/")
    print("=" * 70)


if __name__ == "__main__":
    main()

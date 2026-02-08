#!/usr/bin/env python3
"""
Exploration légère d'un fichier GeoJSON volumineux.
Lit les métadonnées et les premières features sans tout charger.
"""

import json
import os

INPUT_FILE = "data/input/nouveau/ra-superficie-agricole-utilisee-sau-des-exploitations-ensemble-des-exploitations.geojson"
OUTPUT_FILE = "outputs/exploration_sau_output.txt"
MAX_FEATURES = 10


def main():
    output_lines = []

    def log(msg):
        print(msg)
        output_lines.append(msg)

    filename = os.path.basename(INPUT_FILE)
    filesize = os.path.getsize(INPUT_FILE) / (1024 * 1024)

    log("=" * 70)
    log(f"ANALYSE EXPLORATOIRE - {filename} ({filesize:.1f} MB)")
    log("=" * 70)

    # Charger le fichier avec un stream pour compter les features
    # Pour un fichier de 26MB c'est gérable en mémoire
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    log(f"\n  Type: {data.get('type', '?')}")
    if 'crs' in data:
        log(f"  CRS: {data['crs']}")

    features = data.get('features', [])
    log(f"  Nombre de features: {len(features):,}")

    if not features:
        log("  Aucune feature trouvée")
        return

    # Analyser la structure des propriétés
    first = features[0]
    props = first.get('properties', {})
    geom = first.get('geometry', {})

    log(f"  Type de géométrie: {geom.get('type', '?')}")
    log(f"  Nombre de propriétés: {len(props)}")

    log(f"\n  PROPRIÉTÉS:")
    for i, (key, val) in enumerate(props.items(), 1):
        val_type = type(val).__name__
        log(f"    {i:3}. {str(key):<40} | type: {val_type:<10} | ex: {str(val)[:60]}")

    # Chercher des colonnes géographiques (code commune, département, etc.)
    geo_keys = [k for k in props.keys() if any(g in k.upper() for g in
        ['CODGEO', 'CODE', 'COMMUNE', 'DEP', 'REGION', 'GEO', 'INSEE', 'COM'])]
    log(f"\n  Colonnes géographiques détectées: {geo_keys}")

    # Valeurs uniques pour les colonnes avec peu de valeurs
    log(f"\n  DISTRIBUTIONS (propriétés catégorielles):")
    from collections import Counter
    for key in props.keys():
        values = [f['properties'].get(key) for f in features]
        unique = set(values)
        if len(unique) <= 25 and not all(isinstance(v, (int, float)) for v in values if v is not None):
            counter = Counter(values)
            log(f"\n    {key} ({len(unique)} valeurs):")
            for val, count in counter.most_common(15):
                log(f"      - {str(val)[:50]}: {count:,}")

    # Échantillon de features
    log(f"\n  ÉCHANTILLON ({min(MAX_FEATURES, len(features))} premières features):")
    for i, feat in enumerate(features[:MAX_FEATURES], 1):
        p = feat['properties']
        log(f"\n    Feature {i}:")
        for key, val in p.items():
            log(f"      {key}: {str(val)[:60]}")

    # Stats numériques
    numeric_keys = [k for k, v in props.items() if isinstance(v, (int, float))]
    if numeric_keys:
        log(f"\n  STATS (colonnes numériques, sur toutes les features):")
        for key in numeric_keys:
            values = [f['properties'].get(key) for f in features if f['properties'].get(key) is not None]
            if values:
                log(f"    {key}: min={min(values):.2f}, max={max(values):.2f}, moy={sum(values)/len(values):.2f}, n={len(values):,}")

    log(f"\n{'=' * 70}")
    log("FIN DE L'ANALYSE")
    log("=" * 70)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"\n=> Résultats sauvegardés dans: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

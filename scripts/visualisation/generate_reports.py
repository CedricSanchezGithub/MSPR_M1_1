#!/usr/bin/env python3
"""
Générateur de rapports Markdown — Electio-Analytics
=====================================================
Produit deux versions du rapport de synthèse :
  • synthese_latest.md  — mis à jour à chaque run (URLs online Metabase)
  • synthese_YYYY-MM-DD.md — snapshot daté (chemins PNG locaux)

Les images sont embarquées de deux façons :
  • Si public_uuid disponible  → URL Metabase dynamique (toujours à jour)
  • Si PNG local disponible    → chemin relatif (rendu offline, Word, PDF)

Usage standalone :
    python scripts/visualisation/generate_reports.py
    python scripts/visualisation/generate_reports.py --config metabase_config.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DEFAULT = PROJECT_ROOT / "metabase_config.json"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _img_tag(
    alt: str,
    online_url: Optional[str],
    local_path: Optional[str],
    prefer_online: bool = True,
) -> str:
    """
    Retourne un tag Markdown image.
    Si prefer_online et online_url disponible → URL Metabase.
    Sinon → chemin local (relatif à la racine du projet).
    """
    if prefer_online and online_url:
        return f"![{alt}]({online_url})"
    if local_path and Path(PROJECT_ROOT / local_path).exists():
        # Chemin relatif depuis docs/rapports/ vers la racine
        return f"![{alt}](../../{local_path})"
    if online_url:
        return f"![{alt}]({online_url})"
    return f"> ⚠ Image indisponible : {alt}"


def _card_by_slug(cards: list[dict], slug: str) -> Optional[dict]:
    return next((c for c in cards if c["slug"] == slug), None)


def _status_badge(status: str) -> str:
    badges = {
        "public": "🟢 Metabase (public)",
        "authenticated": "🔵 Metabase (auth)",
        "local_fallback": "🟡 Graphique local",
        "online_only": "🟠 URL online (pas de PNG local)",
        "local_only": "🟡 Cache local uniquement",
        "missing": "🔴 Manquant",
    }
    return badges.get(status, f"❓ {status}")


# ─── Sections du rapport ──────────────────────────────────────────────────────

def _section_header(run_date: datetime, metabase_url: str, cards: list[dict]) -> str:
    ok_count = sum(1 for c in cards if c["status"] != "missing")
    return f"""\
# 📊 Electio-Analytics — Synthèse des visualisations

> **Généré le** {run_date.strftime("%d/%m/%Y à %H:%M")}
> **Source** : Metabase ({metabase_url}) | SQLite `electio_herault.db`
> **Couverture** : Hérault (34) — 341 communes — Municipales 2026
> **Visualisations** : {ok_count}/{len(cards)} disponibles

---
"""


def _section_predictions(cards: list[dict], prefer_online: bool) -> str:
    slugs = ["carte_predictions_2026", "predictions_temporelles", "distribution_probabilites"]
    lines = ["## 🗳️ Dashboard 1 — Prédictions municipales 2026\n"]

    for slug in slugs:
        c = _card_by_slug(cards, slug)
        if not c:
            continue
        img = _img_tag(c["title"], c.get("online_url"), c.get("local_path_latest"), prefer_online)
        status = _status_badge(c["status"])
        lines.append(f"### {c['title']}\n{img}\n*{status}*\n")

    lines.append("""\
### Tableau — Prédictions par commune

```sql
SELECT nom_commune AS "Commune", camp_predit AS "Camp",
       ROUND(pred_pct_gauche, 1) AS "% Gauche",
       ROUND(ABS(pred_pct_gauche - 50), 1) AS "Écart à 50 %"
FROM predictions_2026
ORDER BY pred_pct_gauche DESC;
```

### Synthèse département

```sql
SELECT
    COUNT(*) AS "Total communes",
    SUM(CASE WHEN camp_predit = 'Gauche' THEN 1 ELSE 0 END) AS "→ Gauche",
    SUM(CASE WHEN camp_predit = 'Droite' THEN 1 ELSE 0 END) AS "→ Droite",
    ROUND(AVG(pred_pct_gauche), 1) AS "% Gauche moyen"
FROM predictions_2026;
```

### Bascules 2020 → 2026

```sql
SELECT nom_commune AS "Commune", camp_2020 AS "2020", camp_predit AS "2026",
       ROUND(pct_gauche_2020, 1) AS "% G. 2020",
       ROUND(pred_pct_gauche, 1) AS "% G. 2026",
       ROUND(pred_pct_gauche - pct_gauche_2020, 1) AS "Évolution (pts)"
FROM comparaison_2020_2026
WHERE bascule = 1
ORDER BY ABS(pred_pct_gauche - pct_gauche_2020) DESC;
```

---
""")
    return "\n".join(lines)


def _section_validation(cards: list[dict], prefer_online: bool) -> str:
    slugs = ["importance_features", "matrice_confusion", "reel_vs_predit"]
    lines = ["## 🔬 Dashboard 2 — Validation du modèle (Random Forest)\n",
             "> Train : 2008 + 2014 | Test : 2020 | Précision : **89,6 %**\n"]

    for slug in slugs:
        c = _card_by_slug(cards, slug)
        if not c:
            continue
        img = _img_tag(c["title"], c.get("online_url"), c.get("local_path_latest"), prefer_online)
        status = _status_badge(c["status"])
        lines.append(f"### {c['title']}\n{img}\n*{status}*\n")

    lines.append("""\
### Métriques du modèle

```sql
SELECT metrique AS "Métrique", valeur AS "Valeur", description AS "Description"
FROM metriques_modele ORDER BY id;
```

### Précision par camp

```sql
SELECT camp_reel AS "Camp", COUNT(*) AS "Total",
       SUM(correct) AS "Corrects",
       ROUND(100.0 * SUM(correct) / COUNT(*), 1) AS "Précision (%)"
FROM predictions_test_2020
GROUP BY camp_reel;
```

### Distribution des erreurs

```sql
SELECT
    CASE WHEN ecart_abs < 5  THEN '< 5 pts'
         WHEN ecart_abs < 10 THEN '5–10 pts'
         WHEN ecart_abs < 15 THEN '10–15 pts'
         ELSE '≥ 15 pts' END AS "Tranche",
    COUNT(*) AS "Communes",
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM predictions_test_2020), 1) AS "%"
FROM predictions_test_2020
GROUP BY 1 ORDER BY MIN(ecart_abs);
```

---
""")
    return "\n".join(lines)


def _section_profil(cards: list[dict], prefer_online: bool) -> str:
    slugs = ["communes_remarquables"]
    lines = ["## 📊 Dashboard 3 — Profil socio-démographique — Hérault (34)\n",
             "> Sources : INSEE, DGFiP, data.gouv.fr — 2008–2023\n"]

    for slug in slugs:
        c = _card_by_slug(cards, slug)
        if not c:
            continue
        img = _img_tag(c["title"], c.get("online_url"), c.get("local_path_latest"), prefer_online)
        status = _status_badge(c["status"])
        lines.append(f"### {c['title']}\n{img}\n*{status}*\n")

    lines.append("""\
### Top 20 communes — Population 2020

```sql
SELECT c.nom AS "Commune", p.population AS "Population"
FROM population p JOIN communes c ON p.codgeo = c.codgeo
WHERE p.annee = 2020
ORDER BY p.population DESC LIMIT 20;
```

### Revenus médians — 30 communes les plus riches

```sql
SELECT c.nom AS "Commune",
       ROUND(r."[disp]_1ᵉʳ_quartile_(€)", 0) AS "Q1",
       ROUND(r."[disp]_mediane_(€)", 0) AS "Médiane",
       ROUND(r."[disp]_3ᵉ_quartile_(€)", 0) AS "Q3"
FROM revenus r JOIN communes c ON r.codgeo = c.codgeo
WHERE r."[disp]_mediane_(€)" IS NOT NULL
ORDER BY r."[disp]_mediane_(€)" DESC LIMIT 30;
```

### Vote Gauche × Revenu médian

```sql
SELECT c.nom AS "Commune",
       ROUND(r."[disp]_mediane_(€)", 0) AS "Revenu médian (€)",
       ROUND(100.0 * SUM(CASE WHEN e.camp='Gauche' THEN e.voix ELSE 0 END)
             / NULLIF(SUM(e.voix),0), 1) AS "% Gauche 2020",
       p.population AS "Population"
FROM elections e
JOIN communes c ON e.codgeo = c.codgeo
JOIN revenus r ON e.codgeo = r.codgeo
JOIN population p ON e.codgeo = p.codgeo AND p.annee = 2020
WHERE e.tour=1 AND e.annee=2020 AND r."[disp]_mediane_(€)" IS NOT NULL
GROUP BY c.nom, r."[disp]_mediane_(€)", p.population
ORDER BY r."[disp]_mediane_(€)";
```

### CatNat — Communes les plus exposées

```sql
SELECT c.nom AS "Commune", COUNT(*) AS "Nb CatNat",
       MIN(cat.dat_deb) AS "1ère occurrence",
       MAX(cat.dat_deb) AS "Dernière"
FROM catnat cat JOIN communes c ON cat.codgeo = c.codgeo
GROUP BY c.nom ORDER BY 2 DESC LIMIT 20;
```

---
""")
    return "\n".join(lines)


def _section_footer(run_date: datetime, cards: list[dict]) -> str:
    rows = []
    for c in cards:
        status = _status_badge(c["status"])
        online = f"[Lien]({c['online_url']})" if c.get("online_url") else "—"
        local = f"`{c.get('local_path_latest', '—')}`"
        rows.append(f"| {c['title']} | {status} | {online} | {local} |")

    table = "\n".join(rows)
    return f"""\
## 🗂️ Index des visualisations

| Visualisation | Statut | URL Metabase | Fichier local |
|---|---|---|---|
{table}

---

*Rapport généré automatiquement par `scripts/visualisation/metabase_export.py`*
*Dernière mise à jour : {run_date.strftime("%d/%m/%Y %H:%M:%S")}*
"""


# ─── Fonctions principales ────────────────────────────────────────────────────

def build_report(
    cfg: dict,
    cards: list[dict],
    run_date: datetime,
    prefer_online: bool = True,
) -> str:
    """Assemble le rapport Markdown complet."""
    metabase_url = cfg.get("metabase_url", "http://localhost:3000")
    parts = [
        _section_header(run_date, metabase_url, cards),
        _section_predictions(cards, prefer_online),
        _section_validation(cards, prefer_online),
        _section_profil(cards, prefer_online),
        _section_footer(run_date, cards),
    ]
    return "\n".join(parts)


def generate_all_reports(
    cfg: dict,
    cards: list[dict],
    reports_dir: Path,
    run_date: datetime,
):
    """
    Génère deux fichiers :
      1. synthese_latest.md  — URLs Metabase online (prefer_online=True)
      2. synthese_YYYY-MM-DD.md — chemins locaux (prefer_online=False, pour offline/Word)
    """
    # ── Rapport "latest" (URLs Metabase dynamiques) ────────────────────
    latest_path = reports_dir / "synthese_latest.md"
    content_online = build_report(cfg, cards, run_date, prefer_online=True)
    latest_path.write_text(content_online, encoding="utf-8")
    print(f"  ✔ {latest_path.relative_to(PROJECT_ROOT)}")

    # ── Rapport daté (PNGs locaux, pour Word/PDF/offline) ─────────────
    dated_name = f"synthese_{run_date.strftime('%Y-%m-%d')}.md"
    dated_path = reports_dir / dated_name
    content_offline = build_report(cfg, cards, run_date, prefer_online=False)
    dated_path.write_text(content_offline, encoding="utf-8")
    print(f"  ✔ {dated_path.relative_to(PROJECT_ROOT)}")

    # ── README d'index dans docs/rapports/ ────────────────────────────
    _update_index(reports_dir, run_date)


def _update_index(reports_dir: Path, run_date: datetime):
    """Met à jour docs/rapports/README.md avec la liste des snapshots."""
    index_path = reports_dir / "README.md"
    snapshots = sorted(
        [f for f in reports_dir.glob("synthese_????-??-??.md")],
        reverse=True
    )
    rows = "\n".join(
        f"| [{f.stem}]({f.name}) | {f.stat().st_size // 1024} Ko |"
        for f in snapshots
    )
    content = f"""\
# Rapports Electio-Analytics

| Fichier | Taille |
|---|---|
| [synthese_latest.md](synthese_latest.md) *(mise à jour auto)* | — |
{rows}

*Dernière mise à jour : {run_date.strftime("%d/%m/%Y %H:%M")}*
"""
    index_path.write_text(content, encoding="utf-8")
    print(f"  ✔ {index_path.relative_to(PROJECT_ROOT)}")


# ─── Standalone ───────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Génère les rapports Markdown Electio-Analytics")
    parser.add_argument("--config", default=str(CONFIG_DEFAULT))
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        sys.exit(f"✗ Config introuvable : {config_path}")

    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)

    # Mode standalone : construire des cards fictives à partir du config
    # (sans avoir téléchargé les images — on utilise les fallbacks locaux)
    mock_cards = []
    for card in cfg["cards"]:
        public_uuid = card.get("public_uuid", "").strip()
        metabase_url = cfg["metabase_url"].rstrip("/")
        # Préférer le PNG local exporté s'il existe, sinon le fallback phase4
        local_latest = f"{cfg['export']['output_dir']}/latest/{card['filename']}"
        local_fallback = card.get("local_fallback", "")
        # Choisir le local_path le plus pertinent
        if (PROJECT_ROOT / local_latest).exists():
            local_path = local_latest
            status = "public" if public_uuid else "local_only"
        elif local_fallback and (PROJECT_ROOT / local_fallback).exists():
            local_path = local_fallback
            status = "local_fallback"
        else:
            local_path = local_latest
            status = "online_only" if public_uuid else "missing"
        mock_cards.append({
            **card,
            "status": status,
            "local_path_latest": local_path,
            "online_url": (
                f"{metabase_url}/api/public/card/{public_uuid}/query/png"
                if public_uuid else None
            ),
        })

    reports_dir = PROJECT_ROOT / cfg["export"]["reports_dir"]
    reports_dir.mkdir(parents=True, exist_ok=True)
    run_date = datetime.now()

    print(f"\n📝 Génération des rapports → {reports_dir.relative_to(PROJECT_ROOT)}/")
    generate_all_reports(cfg, mock_cards, reports_dir, run_date)
    print("\n✅ Rapports générés.")


if __name__ == "__main__":
    main()

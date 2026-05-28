#!/usr/bin/env python3
"""
Metabase Export — Electio-Analytics
====================================
Télécharge les PNGs des cards Metabase et génère des rapports Markdown.

Modes de téléchargement (par ordre de priorité) :
  1. Lien public (public_uuid dans metabase_config.json) — sans authentification
  2. API authentifiée (card_id + credentials) — session token Metabase
  3. Fallback local (local_fallback) — copie depuis graphiques/phase4/

Usage :
    python scripts/visualisation/metabase_export.py
    python scripts/visualisation/metabase_export.py --config metabase_config.json
    python scripts/visualisation/metabase_export.py --no-download   # Markdown seulement
    python scripts/visualisation/metabase_export.py --list-cards    # Lister les cards dispo
"""

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

# ─── Dépendances optionnelles ───────────────────────────────────────────────

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ─── Constantes ──────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DEFAULT = PROJECT_ROOT / "metabase_config.json"
TIMEOUT = 30   # secondes
RETRY = 3      # tentatives par card


# ─── Client Metabase ─────────────────────────────────────────────────────────

class MetabaseClient:
    """Client léger pour l'API Metabase."""

    def __init__(self, base_url: str):
        if not HAS_REQUESTS:
            raise RuntimeError(
                "La bibliothèque 'requests' est requise.\n"
                "  pip install requests"
            )
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self._token: Optional[str] = None

    # ── Authentification ──────────────────────────────────────────────────

    def authenticate(self, username: str, password: str) -> bool:
        """Ouvre une session Metabase. Retourne True si succès."""
        try:
            resp = self.session.post(
                f"{self.base_url}/api/session",
                json={"username": username, "password": password},
                timeout=TIMEOUT,
            )
            if resp.status_code == 200:
                self._token = resp.json().get("id")
                self.session.headers["X-Metabase-Session"] = self._token
                print(f"  ✔ Authentification Metabase OK (session: {self._token[:8]}…)")
                return True
            else:
                print(f"  ✗ Authentification échouée — HTTP {resp.status_code}")
                return False
        except requests.RequestException as exc:
            print(f"  ✗ Connexion Metabase impossible : {exc}")
            return False

    def is_authenticated(self) -> bool:
        return self._token is not None

    # ── Téléchargement public (UUID) ──────────────────────────────────────

    def download_public_card_png(
        self,
        public_uuid: str,
        output_path: Path,
        width: int = 1200,
        height: int = 628,
    ) -> bool:
        """Télécharge le PNG d'une card via son lien public (sans auth)."""
        url = f"{self.base_url}/api/public/card/{public_uuid}/query/png"
        return self._download_png(url, output_path, auth=False, width=width, height=height)

    # ── Téléchargement authentifié (card_id) ─────────────────────────────

    def download_card_png(
        self,
        card_id: int,
        output_path: Path,
        width: int = 1200,
        height: int = 628,
    ) -> bool:
        """Télécharge le PNG d'une card via son ID (session requise)."""
        if not self.is_authenticated():
            print("    ⚠ Session non ouverte — lancer authenticate() d'abord")
            return False
        url = f"{self.base_url}/api/card/{card_id}/query/png"
        return self._download_png(url, output_path, auth=True, width=width, height=height)

    # ── Interne ───────────────────────────────────────────────────────────

    def _download_png(
        self,
        url: str,
        output_path: Path,
        auth: bool = True,
        width: int = 1200,
        height: int = 628,
    ) -> bool:
        """Appelle l'URL et écrit le PNG sur disque. Retente RETRY fois."""
        params = {"width": width, "height": height}
        for attempt in range(1, RETRY + 1):
            try:
                resp = self.session.get(url, params=params, timeout=TIMEOUT, stream=True)
                if resp.status_code == 200:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    size_kb = output_path.stat().st_size // 1024
                    print(f"    ✔ {output_path.name} ({size_kb} Ko)")
                    return True
                elif resp.status_code == 404:
                    print(f"    ✗ Card introuvable — {url}")
                    return False
                else:
                    print(f"    ⚠ HTTP {resp.status_code} (tentative {attempt}/{RETRY})")
                    time.sleep(2 ** attempt)
            except requests.RequestException as exc:
                print(f"    ⚠ Erreur réseau : {exc} (tentative {attempt}/{RETRY})")
                time.sleep(2 ** attempt)
        return False

    # ── Utilitaires ───────────────────────────────────────────────────────

    def list_cards(self) -> list[dict]:
        """Liste toutes les cards Metabase (authentification requise)."""
        if not self.is_authenticated():
            return []
        try:
            resp = self.session.get(f"{self.base_url}/api/card", timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp.json().get("data", resp.json())
            return []
        except requests.RequestException:
            return []

    def public_card_png_url(self, public_uuid: str) -> str:
        """Retourne l'URL publique du PNG d'une card (pour l'embarquer dans le Markdown)."""
        return f"{self.base_url}/api/public/card/{public_uuid}/query/png"


# ─── Fonctions d'export ───────────────────────────────────────────────────────

def load_config(config_path: Path) -> dict:
    """Charge et valide le fichier de configuration."""
    if not config_path.exists():
        sys.exit(f"✗ Fichier de config introuvable : {config_path}")
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg


def resolve_output_dirs(cfg: dict, run_date: datetime) -> tuple[Path, Path, Path]:
    """Retourne (export_dir_latest, export_dir_dated, reports_dir)."""
    root = PROJECT_ROOT
    export_base = root / cfg["export"]["output_dir"]
    dated = export_base / run_date.strftime("%Y-%m-%d")
    latest = export_base / "latest"
    reports = root / cfg["export"]["reports_dir"]
    for d in (dated, latest, reports):
        d.mkdir(parents=True, exist_ok=True)
    return latest, dated, reports


def purge_old_exports(export_base: Path, keep_days: int):
    """Supprime les dossiers datés plus vieux que keep_days."""
    cutoff = datetime.now() - timedelta(days=keep_days)
    for child in export_base.iterdir():
        if child.is_dir() and child.name != "latest":
            try:
                dir_date = datetime.strptime(child.name, "%Y-%m-%d")
                if dir_date < cutoff:
                    shutil.rmtree(child)
                    print(f"  🗑  Historique supprimé : {child.name}")
            except ValueError:
                pass  # dossier non daté → ignorer


def export_cards(
    cfg: dict,
    client: MetabaseClient,
    latest_dir: Path,
    dated_dir: Path,
    download: bool = True,
) -> list[dict]:
    """
    Pour chaque card du config :
      1. Tente le téléchargement (public UUID → auth → fallback local)
      2. Copie dans latest/ et dated/
    Retourne la liste enrichie (ajout de 'status', 'local_path', 'online_url').
    """
    results = []
    export_cfg = cfg["export"]
    width = export_cfg.get("image_width", 1200)
    height = export_cfg.get("image_height", 628)

    for card in cfg["cards"]:
        slug = card["slug"]
        title = card["title"]
        filename = card["filename"]
        public_uuid = card.get("public_uuid", "").strip()
        card_id = card.get("card_id")
        fallback = card.get("local_fallback", "")

        print(f"\n  → {title}")

        dated_path = dated_dir / filename
        latest_path = latest_dir / filename
        online_url = None
        status = "pending"

        if download:
            # ── Mode 1 : lien public ────────────────────────────────────
            if public_uuid:
                online_url = client.public_card_png_url(public_uuid)
                ok = client.download_public_card_png(public_uuid, dated_path, width, height)
                if ok:
                    shutil.copy2(dated_path, latest_path)
                    status = "public"

            # ── Mode 2 : API authentifiée ───────────────────────────────
            if status == "pending" and card_id and client.is_authenticated():
                ok = client.download_card_png(card_id, dated_path, width, height)
                if ok:
                    shutil.copy2(dated_path, latest_path)
                    status = "authenticated"

            # ── Mode 3 : fallback local ─────────────────────────────────
            if status == "pending" and fallback:
                fallback_path = PROJECT_ROOT / fallback
                if fallback_path.exists():
                    shutil.copy2(fallback_path, dated_path)
                    shutil.copy2(fallback_path, latest_path)
                    print(f"    ↩ Fallback local : {fallback}")
                    status = "local_fallback"
                else:
                    print(f"    ✗ Fallback introuvable : {fallback}")
                    status = "missing"

            if status == "pending":
                print("    ✗ Aucune source disponible (configurer public_uuid ou card_id)")
                status = "missing"
        else:
            # --no-download : on référence quand même les URLs online si UUID dispo
            if public_uuid:
                online_url = client.public_card_png_url(public_uuid)
                status = "online_only"
            elif latest_path.exists():
                status = "local_only"
            else:
                status = "missing"

        results.append({
            **card,
            "status": status,
            "local_path_latest": str(latest_path.relative_to(PROJECT_ROOT)),
            "local_path_dated": str(dated_path.relative_to(PROJECT_ROOT)),
            "online_url": online_url,
        })

    return results


# ─── Point d'entrée ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Exporte les visualisations Metabase et génère des rapports Markdown"
    )
    parser.add_argument(
        "--config", default=str(CONFIG_DEFAULT),
        help="Chemin vers metabase_config.json"
    )
    parser.add_argument(
        "--no-download", action="store_true",
        help="Génère uniquement le Markdown sans télécharger les images"
    )
    parser.add_argument(
        "--list-cards", action="store_true",
        help="Liste les cards disponibles dans Metabase et quitte"
    )
    args = parser.parse_args()

    print("\n" + "═" * 60)
    print("   METABASE EXPORT — Electio-Analytics")
    print("═" * 60)

    cfg = load_config(Path(args.config))
    run_date = datetime.now()

    if not HAS_REQUESTS:
        print("\n⚠  'requests' non installé — pip install requests")
        print("   Mode dégradé : génération Markdown sans téléchargement.")
        args.no_download = True

    client = MetabaseClient(cfg["metabase_url"])

    # ── Authentification (si credentials fournis) ─────────────────────────
    creds = cfg.get("credentials", {})
    username = creds.get("username", "")
    password = creds.get("password", "")
    authenticated = False
    if username and password and "VOTRE" not in password:
        print(f"\n🔑 Authentification → {cfg['metabase_url']} …")
        authenticated = client.authenticate(username, password)

    # ── --list-cards ──────────────────────────────────────────────────────
    if args.list_cards:
        if not authenticated:
            print("\n✗ --list-cards nécessite une authentification valide dans le config.")
            sys.exit(1)
        cards = client.list_cards()
        print(f"\n{'ID':>6}  {'Nom':<50}  {'Collection'}")
        print("─" * 75)
        for c in sorted(cards, key=lambda x: x.get("id", 0)):
            col = (c.get("collection") or {}).get("name", "—")
            print(f"{c['id']:>6}  {c['name']:<50}  {col}")
        return

    # ── Répertoires de sortie ─────────────────────────────────────────────
    latest_dir, dated_dir, reports_dir = resolve_output_dirs(cfg, run_date)
    print(f"\n📁 Export  → {cfg['export']['output_dir']}/")
    print(f"📄 Rapports → {cfg['export']['reports_dir']}/")

    # ── Téléchargement des cards ──────────────────────────────────────────
    print(f"\n📥 Téléchargement des visualisations ({len(cfg['cards'])} cards)…")
    cards_result = export_cards(
        cfg, client, latest_dir, dated_dir,
        download=not args.no_download,
    )

    # ── Génération des rapports Markdown ──────────────────────────────────
    print("\n📝 Génération des rapports Markdown…")
    from generate_reports import generate_all_reports
    generate_all_reports(cfg, cards_result, reports_dir, run_date)

    # ── Purge historique ──────────────────────────────────────────────────
    if cfg["export"].get("keep_history") and not args.no_download:
        keep_days = cfg["export"].get("history_days", 30)
        export_base = PROJECT_ROOT / cfg["export"]["output_dir"]
        purge_old_exports(export_base, keep_days)

    # ── Résumé ────────────────────────────────────────────────────────────
    ok = [c for c in cards_result if c["status"] not in ("missing",)]
    print(f"\n{'═' * 60}")
    print(f"   ✅ {len(ok)}/{len(cards_result)} visualisations exportées")
    print(f"   📄 Rapport → {reports_dir}/synthese_latest.md")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()

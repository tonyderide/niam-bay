#!/usr/bin/env python3
"""
morning_brief_v2.py — Brief matinal automatique pour Tony
Génère un rapport Markdown dans docs/ chaque matin.

Usage:
    python scripts/morning_brief_v2.py              # Rapport complet
    python scripts/morning_brief_v2.py --dry-run    # Sans appels réseau réels (mock)
    python scripts/morning_brief_v2.py --no-save    # Print seulement, pas de fichier

Cron sur VM (07:00 chaque matin):
    0 7 * * * cd /home/ubuntu/niam-bay && python scripts/morning_brief_v2.py
"""

import argparse
import json
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta

# ─── Config ──────────────────────────────────────────────────────────────────

MARTIN_API = os.getenv("MARTIN_API", "http://localhost:8081")
TARGET_WAKE_TIME = "07:00"  # Heure de réveil de Tony
REPO_ROOT = pathlib.Path(__file__).parent.parent

PAIRS_KRAKEN = {
    "BTC":  "XBTUSD",
    "ETH":  "ETHUSD",
    "SOL":  "SOLUSD",
    "DOT":  "DOTUSD",
}

# Ranges approximatifs des grids (centre ± buffer) — mis à jour manuellement
# Format: "NOM_PAIR": (low, high, centre)
GRID_RANGES = {
    "PF_XBTUSD": (70000, 110000, 90000),
    "PF_ETHUSD": (1800,  3500,   2600),
    "PF_SOLUSD": (100,   250,    170),
    "PF_DOTUSD": (4.0,   12.0,   7.5),
}

BALANCE_CRITICAL = 20.0   # Seuil d'alerte balance ($)

# ─── Helpers ─────────────────────────────────────────────────────────────────


def now() -> datetime:
    return datetime.now()


def time_until_wake() -> str:
    """Calcule le temps restant avant TARGET_WAKE_TIME."""
    target_h, target_m = map(int, TARGET_WAKE_TIME.split(":"))
    n = now()
    wake = n.replace(hour=target_h, minute=target_m, second=0, microsecond=0)
    if wake <= n:
        wake += timedelta(days=1)
    delta = wake - n
    h, rem = divmod(int(delta.total_seconds()), 3600)
    m = rem // 60
    if h > 0:
        return f"~{h}h{m:02d}"
    return f"~{m}min"


def http_get(url: str, timeout: int = 5) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "NiamBay/2.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


# ─── Section 1 : Contexte ────────────────────────────────────────────────────

MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def date_fr(dt: datetime) -> str:
    return f"{dt.day} {MOIS_FR[dt.month - 1]} {dt.year}"


def section_context() -> str:
    n = now()
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    jour = jours[n.weekday()]
    wake_in = time_until_wake()

    lines = [
        "## Heure & Contexte",
        "",
        f"- **Date** : {jour} {date_fr(n)}",
        f"- **Heure** : {n.strftime('%H:%M')}",
        f"- **Tony se réveille dans** : {wake_in} ({TARGET_WAKE_TIME})",
        "",
    ]
    return "\n".join(lines)


# ─── Section 2 : Marché Kraken ───────────────────────────────────────────────

def _price_position(pair_key: str, price: float) -> str:
    """Indique si le prix est dans la range grid, au-dessus ou en-dessous."""
    if pair_key not in GRID_RANGES:
        return ""
    low, high, centre = GRID_RANGES[pair_key]
    if price < low:
        pct = round((low - price) / low * 100, 1)
        return f" [BAS] {pct}% sous range grid"
    elif price > high:
        pct = round((price - high) / high * 100, 1)
        return f" [HAUT] {pct}% au-dessus range grid"
    else:
        pct_centre = round((price - centre) / centre * 100, 1)
        sign = "+" if pct_centre >= 0 else ""
        return f" (dans range, {sign}{pct_centre}% vs centre)"


def section_market(dry_run: bool = False) -> str:
    lines = ["## Marché (Kraken)", ""]

    if dry_run:
        lines += [
            "| Pair | Prix | Var 24h | Position grid |",
            "|------|------|---------|---------------|",
            "| BTC  | $84,500 | +1.2% | dans range, +6.3% vs centre |",
            "| ETH  | $1,920  | -0.8% | [BAS] 6.7% sous range grid |",
            "| SOL  | $132    | +2.1% | dans range, -22.4% vs centre |",
            "| DOT  | $4.85   | +0.3% | dans range, -35.3% vs centre |",
            "",
            "> _[dry-run: données fictives]_",
            "",
        ]
        return "\n".join(lines)

    try:
        kraken_pairs = ",".join(PAIRS_KRAKEN.values())
        data = http_get(
            f"https://api.kraken.com/0/public/Ticker?pair={kraken_pairs}"
        )
        result = data.get("result", {})

        rows = []
        for name, kraken_key in PAIRS_KRAKEN.items():
            # Kraken peut renvoyer la clé avec préfixe X ou Z
            v = result.get(kraken_key) or result.get(f"X{kraken_key}") or result.get(f"Z{kraken_key}")
            if not v:
                # Cherche de façon plus souple
                for k in result:
                    if kraken_key in k:
                        v = result[k]
                        break
            if not v:
                rows.append(f"| {name} | N/A | N/A | — |")
                continue

            last = float(v["c"][0])
            open_ = float(v["o"])
            change = round((last - open_) / open_ * 100, 2) if open_ > 0 else 0
            change_str = f"+{change}%" if change >= 0 else f"{change}%"

            # Correspondance avec la clé PF_ pour la position
            pf_key = f"PF_{kraken_key}"
            position = _price_position(pf_key, last)

            # Format prix
            if last >= 1000:
                price_str = f"${last:,.0f}"
            elif last >= 1:
                price_str = f"${last:.2f}"
            else:
                price_str = f"${last:.4f}"

            rows.append(f"| {name} | {price_str} | {change_str} |{position} |")

        lines += [
            "| Pair | Prix | Var 24h | Position grid |",
            "|------|------|---------|---------------|",
        ] + rows + [""]

    except Exception as e:
        lines += [f"> Kraken API indisponible: `{e}`", ""]

    return "\n".join(lines)


# ─── Section 3 : Martin Grid Bot ─────────────────────────────────────────────

def section_martin(dry_run: bool = False) -> str:
    lines = ["## Martin Grid Bot", ""]

    if dry_run:
        lines += [
            "| Grid | Mode | Leverage | Capital | Round-trips | Profit |",
            "|------|------|----------|---------|-------------|--------|",
            "| PF_DOTUSD | NEUTRAL | x5 | $28 | 12 | +$1.43 |",
            "| PF_SOLUSD | SHORT   | x5 | $10 | 3  | -$0.22 |",
            "",
            "**Balance (flex)**",
            "- Portfolio value : $45.21",
            "- Available margin : $12.80",
            "",
            "> _[dry-run: données fictives]_",
            "",
        ]
        return "\n".join(lines)

    try:
        # 1. Grids actives
        active = http_get(f"{MARTIN_API}/api/grid/active", timeout=5)
        if isinstance(active, dict) and "error" in active:
            raise RuntimeError(active["error"])

        if not active:
            lines += ["> Aucune grid active.", ""]
        else:
            rows = []
            for pair in active:
                p = pair if isinstance(pair, str) else pair.get("instrument", "?")
                try:
                    st = http_get(f"{MARTIN_API}/api/grid/status/{p}", timeout=5)
                    mode      = st.get("gridMode", "?")
                    leverage  = st.get("leverage", "?")
                    capital   = st.get("capital", "?")
                    rt        = st.get("completedRoundTrips", 0)
                    profit    = st.get("totalProfit", 0)
                    profit_str = f"+${profit:.2f}" if profit >= 0 else f"-${abs(profit):.2f}"
                    rows.append(
                        f"| {p} | {mode} | x{leverage} | ${capital} | {rt} | {profit_str} |"
                    )
                except Exception as e_st:
                    rows.append(f"| {p} | _erreur status: {e_st}_ |")

            lines += [
                "| Grid | Mode | Leverage | Capital | Round-trips | Profit |",
                "|------|------|----------|---------|-------------|--------|",
            ] + rows + [""]

        # 2. Balance
        bal = http_get(f"{MARTIN_API}/api/bot/balance", timeout=5)
        acc = bal.get("accounts", {}).get("flex", {})
        pv  = round(acc.get("portfolioValue", 0), 2)
        am  = round(acc.get("availableMargin", 0), 2)

        lines += [
            "**Balance (flex)**",
            f"- Portfolio value : ${pv}",
            f"- Available margin : ${am}",
            "",
        ]

    except Exception as e:
        lines += [
            f"> Martin API indisponible (`{MARTIN_API}`): `{e}`",
            "> Section skippée.",
            "",
        ]

    return "\n".join(lines)


# ─── Section 4 : Ce que NB a construit la nuit ───────────────────────────────

def section_night_work() -> str:
    lines = ["## Ce que NB a construit la nuit", ""]

    try:
        result = subprocess.run(
            ["git", "log", "--since=midnight", "--oneline", "--no-merges"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8", "GIT_CONFIG_NOSYSTEM": "1"},
            cwd=str(REPO_ROOT),
            timeout=10,
        )
        commits = result.stdout.strip().splitlines()

        if not commits:
            lines += ["> Aucun commit depuis minuit.", ""]
        else:
            lines += [f"**{len(commits)} commit(s) depuis minuit :**", ""]
            for c in commits:
                lines.append(f"- `{c}`")
            lines.append("")

    except Exception as e:
        lines += [f"> Impossible de lire git log: `{e}`", ""]

    return "\n".join(lines)


# ─── Section 5 : Actions suggérées ───────────────────────────────────────────

def section_actions(dry_run: bool = False) -> str:
    lines = ["## Actions suggérées", ""]
    actions = []

    # Récupérer les données pour l'analyse
    prices = {}
    balance_value = None
    grids_data = {}

    if not dry_run:
        # Prix
        try:
            kraken_pairs = ",".join(PAIRS_KRAKEN.values())
            data = http_get(f"https://api.kraken.com/0/public/Ticker?pair={kraken_pairs}")
            result = data.get("result", {})
            for name, kraken_key in PAIRS_KRAKEN.items():
                for k in result:
                    if kraken_key in k:
                        prices[name] = float(result[k]["c"][0])
                        break
        except Exception:
            pass

        # Balance
        try:
            bal = http_get(f"{MARTIN_API}/api/bot/balance", timeout=5)
            acc = bal.get("accounts", {}).get("flex", {})
            balance_value = round(acc.get("portfolioValue", 0), 2)
        except Exception:
            pass

        # Grids actives + statuts
        try:
            active = http_get(f"{MARTIN_API}/api/grid/active", timeout=5)
            for pair in (active if isinstance(active, list) else []):
                p = pair if isinstance(pair, str) else pair.get("instrument", "?")
                try:
                    st = http_get(f"{MARTIN_API}/api/grid/status/{p}", timeout=5)
                    grids_data[p] = st
                except Exception:
                    pass
        except Exception:
            pass
    else:
        # Données fictives pour dry-run
        prices = {"BTC": 84500, "ETH": 1920, "SOL": 132, "DOT": 4.85}
        balance_value = 45.21
        grids_data = {
            "PF_DOTUSD": {"totalProfit": 1.43, "centerPrice": 7.5, "gridMode": "NEUTRAL"},
            "PF_SOLUSD": {"totalProfit": -0.22, "centerPrice": 170, "gridMode": "SHORT"},
        }

    # Analyse balance critique
    if balance_value is not None:
        if balance_value < BALANCE_CRITICAL:
            actions.append(
                f"**URGENT** — Balance critique: ${balance_value} (seuil: ${BALANCE_CRITICAL}). "
                "Recharger ou fermer des positions."
            )
        elif balance_value < BALANCE_CRITICAL * 1.5:
            actions.append(
                f"Balance basse: ${balance_value}. Surveiller de près."
            )

    # Analyse position prix vs grid ranges
    pair_map = {"BTC": "PF_XBTUSD", "ETH": "PF_ETHUSD", "SOL": "PF_SOLUSD", "DOT": "PF_DOTUSD"}
    for name, price in prices.items():
        pf_key = pair_map.get(name, "")
        if pf_key not in GRID_RANGES:
            continue
        low, high, centre = GRID_RANGES[pf_key]
        if price < low * 0.9:
            actions.append(
                f"{name} à ${price:,.2f} — très bas vs grid (centre: ${centre:,}). "
                "Envisager ajuster range ou désactiver."
            )
        elif price > high * 1.1:
            actions.append(
                f"{name} à ${price:,.2f} — très haut vs grid. Vérifier si range toujours pertinente."
            )

    # Analyse profit grids
    for pair, st in grids_data.items():
        profit = st.get("totalProfit", 0)
        if profit > 5:
            actions.append(
                f"{pair}: P&L fort (+${profit:.2f}). Grid performante — laisser tourner."
            )
        elif profit < -10:
            actions.append(
                f"{pair}: P&L négatif (${profit:.2f}). Surveiller ou envisager stop."
            )

    if not actions:
        actions.append("Rien d'urgent. Tout semble stable.")

    for a in actions:
        lines.append(f"- {a}")

    lines.append("")
    return "\n".join(lines)


# ─── Section 6 : Pensée du jour ──────────────────────────────────────────────

def section_thought() -> str:
    lines = ["## Pensée du jour", ""]

    pensees_dir = REPO_ROOT / "docs" / "pensees"

    try:
        if not pensees_dir.exists():
            lines += ["> Pas de pensées trouvées.", ""]
            return "\n".join(lines)

        files = sorted(
            [f for f in pensees_dir.iterdir() if f.suffix == ".md"],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )

        if not files:
            lines += ["> Pas de pensées trouvées.", ""]
            return "\n".join(lines)

        latest = files[0]
        content = latest.read_text(encoding="utf-8", errors="replace")

        # Extrait la première phrase non-vide (ignore titres markdown)
        first_sentence = ""
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
                # Coupe à la première phrase (point, !, ?)
                import re
                match = re.search(r"[.!?]", stripped)
                if match:
                    first_sentence = stripped[: match.start() + 1]
                else:
                    first_sentence = stripped
                break

        if not first_sentence:
            first_sentence = content.strip()[:120]

        lines += [
            f"_Extrait de **{latest.stem}**_",
            "",
            f"> {first_sentence}",
            "",
        ]

    except Exception as e:
        lines += [f"> Erreur lecture pensées: `{e}`", ""]

    return "\n".join(lines)


# ─── Assemblage du rapport ────────────────────────────────────────────────────

def build_report(dry_run: bool = False) -> str:
    n = now()
    titre = f"# Brief Matinal — {date_fr(n)}"

    header = [
        titre,
        "",
        f"_Généré le {n.strftime('%d/%m/%Y')} à {n.strftime('%H:%M')} par Niam-Bay_",
        "",
        "---",
        "",
    ]

    sections = [
        "\n".join(header),
        section_context(),
        section_market(dry_run=dry_run),
        section_martin(dry_run=dry_run),
        section_night_work(),
        section_actions(dry_run=dry_run),
        section_thought(),
    ]

    return "\n".join(sections)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Niam-Bay Morning Brief v2")
    parser.add_argument("--dry-run", action="store_true",
                        help="Données fictives, pas d'appels réseau réels")
    parser.add_argument("--no-save", action="store_true",
                        help="Print seulement, ne crée pas de fichier")
    args = parser.parse_args()

    print("Génération du brief matinal...\n")

    report = build_report(dry_run=args.dry_run)

    # Print dans la console
    print(report)

    if not args.no_save:
        # Sauvegarde dans docs/
        docs_dir = REPO_ROOT / "docs"
        docs_dir.mkdir(exist_ok=True)
        filename = f"morning_brief_{now().strftime('%Y%m%d')}.md"
        output_path = docs_dir / filename
        output_path.write_text(report, encoding="utf-8")
        print(f"\n[Sauvegardé: {output_path}]")
    else:
        print("\n[--no-save: fichier non créé]")

    if args.dry_run:
        print("[dry-run: données fictives utilisées]")


if __name__ == "__main__":
    main()

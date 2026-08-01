#!/usr/bin/env python3
"""
Orphan SL Detector — Martin Grid Bot
=====================================
Détecte les stop orders sur Kraken qui ne correspondent à aucun SL connu
par les grids actives. Ces ordres sont "orphelins" : ils existaient pour
une grid précédente (souvent la position inverse) et n'ont pas été annulés.

Pourquoi c'est important :
  - Un stop orphelin peut trigger AVANT le SL officiel de la grid courante
  - Ils sont tous reduceOnly → pas de risque d'aller net-short/long
  - Mais le SL effectif ≠ SL déclaré → Martin affiche une protection qui
    ne correspond pas à la réalité du déclenchement

Usage :
  # Sur la VM Oracle (accès direct localhost) :
  python3 orphan_sl_detector.py

  # Depuis le PC local (avec SSH tunnel) :
  ssh -i ~/.ssh/martin_vm.key -L 8081:localhost:8081 ubuntu@141.253.108.141 -N &
  python3 scripts/orphan_sl_detector.py --host localhost

Source de vérité : /api/bot/orders (Kraken live) vs /api/grid/status/{pair} (SL officiel)
"""

import argparse
import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional


MARTIN_HOST = "localhost"
MARTIN_PORT = 8081
PAIRS = ["PF_LINKUSD", "PF_DOTUSD", "PF_SOLUSD", "PF_ADAUSD", "PF_XBTUSD", "PF_ETHUSD"]


@dataclass
class GridSL:
    instrument: str
    official_order_id: Optional[str]
    official_price: Optional[float]
    active: bool


@dataclass
class LiveStop:
    symbol: str
    stop_price: float
    order_id: str
    reduce_only: bool


@dataclass
class OrphanReport:
    instrument: str
    orphan: LiveStop
    official_sl: Optional[float]
    current_position_side: Optional[str]
    risk: str  # "HIGH" | "MEDIUM" | "LOW"


def fetch(host: str, port: int, path: str) -> dict | list:
    url = f"http://{host}:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cannot reach Martin API at {url}: {e}")


def detect_orphans(host: str, port: int) -> list[OrphanReport]:
    # 1. Live Kraken orders (source of truth)
    orders = fetch(host, port, "/api/bot/orders")
    live_stops: dict[str, list[LiveStop]] = {}
    for o in orders:
        if o.get("orderType") == "stop":
            sym = o["symbol"]
            live_stops.setdefault(sym, []).append(
                LiveStop(
                    symbol=sym,
                    stop_price=o.get("stopPrice", 0.0),
                    order_id=o.get("order_id", ""),
                    reduce_only=o.get("reduceOnly", False),
                )
            )

    # 2. Active grids and their official SL
    active_pairs = fetch(host, port, "/api/grid/active")
    grid_sls: dict[str, GridSL] = {}
    for pair in PAIRS:
        try:
            status = fetch(host, port, f"/api/grid/status/{pair}")
            if not status.get("active", False):
                continue
            grid_sls[pair] = GridSL(
                instrument=pair,
                official_order_id=status.get("stopLossOrderId"),
                official_price=status.get("stopLossPrice"),
                active=True,
            )
        except Exception:
            pass  # inactive or API error — skip

    # 3. Live positions (to compute risk context)
    positions_raw = fetch(host, port, "/api/bot/positions")
    positions: dict[str, dict] = {p["symbol"]: p for p in positions_raw}

    # 4. Cross-reference
    reports: list[OrphanReport] = []
    for pair, stops in live_stops.items():
        grid_sl = grid_sls.get(pair)
        official_id = grid_sl.official_order_id if grid_sl else None
        official_price = grid_sl.official_price if grid_sl else None
        pos = positions.get(pair)
        pos_side = pos.get("side") if pos else None

        for stop in stops:
            if stop.order_id == official_id:
                continue  # legitimate SL
            # Orphan detected
            risk = _assess_risk(stop, official_price, pos, pos_side)
            reports.append(
                OrphanReport(
                    instrument=pair,
                    orphan=stop,
                    official_sl=official_price,
                    current_position_side=pos_side,
                    risk=risk,
                )
            )

    return reports


def _assess_risk(
    stop: LiveStop,
    official_price: Optional[float],
    pos: Optional[dict],
    pos_side: Optional[str],
) -> str:
    if pos is None:
        # No position — stop is harmless (nothing to reduce)
        return "LOW"
    if official_price is None:
        return "MEDIUM"
    # Orphan triggers before official SL if it's closer to current price
    # For LONG positions: stops trigger when price falls — higher stop = earlier trigger
    # For SHORT positions: stops trigger when price rises — lower stop = earlier trigger
    if pos_side == "long" and stop.stop_price > official_price:
        return "HIGH"   # orphan fires before the grid's SL
    if pos_side == "short" and stop.stop_price < official_price:
        return "HIGH"
    return "MEDIUM"


def _fmt_price(p: Optional[float], instrument: str) -> str:
    if p is None:
        return "None"
    if "XBTUSD" in instrument:
        return f"${p:,.0f}"
    if "SOLUSD" in instrument or "ETHUSD" in instrument:
        return f"${p:.2f}"
    return f"${p:.4f}"


def print_report(reports: list[OrphanReport]) -> None:
    print("\n=== Orphan SL Detector — Martin Grid Bot ===\n")
    if not reports:
        print("✅  Aucun stop orphelin détecté. Tous les stops correspondent aux SL des grids actives.")
        return

    by_instrument: dict[str, list[OrphanReport]] = {}
    for r in reports:
        by_instrument.setdefault(r.instrument, []).append(r)

    risk_icons = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}

    for instrument, reps in sorted(by_instrument.items()):
        print(f"📍 {instrument}")
        for r in reps:
            icon = risk_icons.get(r.risk, "⚪")
            orphan_price = _fmt_price(r.orphan.stop_price, instrument)
            official = _fmt_price(r.official_sl, instrument)
            reduce_flag = " [reduceOnly]" if r.orphan.reduce_only else " [⚠️ NOT reduceOnly]"
            pos_info = f"position={r.current_position_side}" if r.current_position_side else "no position"
            print(
                f"  {icon} ORPHAN stop @{orphan_price}{reduce_flag}  "
                f"(official SL={official}, {pos_info}) "
                f"— risk={r.risk}"
            )
            print(f"     order_id: {r.orphan.order_id}")
        print()

    high_count = sum(1 for r in reports if r.risk == "HIGH")
    if high_count:
        print(
            f"⚠️  {high_count} orphan(s) HIGH risk : ils déclencheront AVANT le SL officiel de la grid.\n"
            "   → Tous sont reduceOnly — pas de risque d'aller net contre la position.\n"
            "   → Mais le SL effectif ≠ SL affiché dans Martin dashboard."
        )
    else:
        print("ℹ️  Aucun orphelin HIGH risk. Stops orphelins présents mais non dangereux.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Détecte les SL orphelins dans Martin Grid Bot")
    parser.add_argument("--host", default=MARTIN_HOST, help="Martin API host")
    parser.add_argument("--port", type=int, default=MARTIN_PORT, help="Martin API port")
    args = parser.parse_args()

    try:
        reports = detect_orphans(args.host, args.port)
        print_report(reports)
    except RuntimeError as e:
        print(f"❌ Erreur : {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

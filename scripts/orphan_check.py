#!/usr/bin/env python3
"""
orphan_check.py — cycle 218, 2026-07-06

Capteur des positions Kraken qui n'appartiennent à aucune grid Martin active.
Rend explicite le pattern "grid mécanique + short discrétionnaire" observé cycle 217.

Sans jugement : tout ce qui est dans /api/bot/positions mais pas dans /api/grid/active
est marqué "orphelin". Cela peut être :
  - une position discrétionnaire ouverte par Tony hors bot (cas normal, cf. TRB cycle 217)
  - une position zombie laissée par une grid stoppée (cas anormal, cf. BUG-002 cycle 143)
  - une position ouverte pendant un déploiement en cours (transitoire)

Le script ne décide rien. Il liste, chiffre, propose une catégorie probable via un
heuristique simple (présence SL+TP explicites → discrétionnaire ; sinon zombie candidat).
"""

from __future__ import annotations
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone

VM_HOST = "ubuntu@141.253.108.141"
SSH_KEY = "/home/tony/.ssh/martin_vm.key"
API_BASE = "http://localhost:8081"


def curl(path: str) -> str:
    cmd = [
        "ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", VM_HOST,
        f"curl -s {API_BASE}{path}",
    ]
    return subprocess.check_output(cmd, text=True, timeout=15)


def classify(symbol: str, orders: list[dict]) -> str:
    """Heuristique simple pour catégoriser une position orpheline."""
    sym_orders = [o for o in orders if o.get("symbol") == symbol]
    has_sl = any(o.get("orderType") == "stop" and o.get("reduceOnly") for o in sym_orders)
    has_tp = any(o.get("orderType") == "take_profit" and o.get("reduceOnly") for o in sym_orders)
    if has_sl and has_tp:
        return "DISCRETIONARY (SL+TP encadrement complet)"
    if has_sl and not has_tp:
        return "DISCRETIONARY-partial (SL seul, TP manquant)"
    if not has_sl:
        return "ZOMBIE-CANDIDATE (aucun SL sur exchange)"
    return "UNCLASSIFIED"


def format_usd(x: float) -> str:
    sign = "+" if x >= 0 else ""
    return f"{sign}${x:.2f}"


def build_report(active: set, positions: list[dict], orders: list[dict]) -> dict:
    """Structure the analysis as a dict — useful for --json or programmatic callers."""
    orphans_raw = [p for p in positions if p.get("symbol") not in active]
    grid_positions = [p for p in positions if p.get("symbol") in active]

    orphans = []
    total_orphan_upnl = 0.0
    for p in orphans_raw:
        upnl = float(p.get("unrealizedPnl", 0) or 0)
        total_orphan_upnl += upnl
        notional = float(p.get("size", 0)) * float(p.get("price", 0))
        orphans.append({
            "symbol": p["symbol"],
            "side": p["side"],
            "size": p["size"],
            "price": p["price"],
            "notional": round(notional, 2),
            "unrealizedPnl": round(upnl, 4),
            "classification": classify(p["symbol"], orders),
        })

    all_discretionary = all(
        o["classification"].startswith("DISCRETIONARY") for o in orphans
    )
    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "active_grids": sorted(active),
        "positions_count": len(positions),
        "orders_count": len(orders),
        "grid_positions": [
            {
                "symbol": p["symbol"],
                "side": p["side"],
                "size": p["size"],
                "price": p["price"],
                "unrealizedPnl": round(float(p.get("unrealizedPnl", 0) or 0), 4),
            }
            for p in grid_positions
        ],
        "orphans": orphans,
        "total_orphan_upnl": round(total_orphan_upnl, 4),
        "status": "OK" if all_discretionary or not orphans else "ZOMBIE_SUSPECTED",
        "exit_code": 0 if all_discretionary or not orphans else 1,
    }


def print_human(report: dict) -> None:
    ts = report["timestamp"].replace("T", " ")
    print(f"# orphan_check — {ts}\n")
    active = report["active_grids"]
    print(f"Grids actives Martin : {active if active else '(aucune)'}")
    print(f"Positions Kraken     : {report['positions_count']}")
    print(f"Orders live Kraken   : {report['orders_count']}\n")

    grids = report["grid_positions"]
    print(f"## Positions rattachées à une grid ({len(grids)})\n")
    if not grids:
        print("(aucune)\n")
    for p in grids:
        print(
            f"- {p['symbol']:12} {p['side']:5} size={p['size']:>8} "
            f"@ ${p['price']:.4f} uPnL={format_usd(p['unrealizedPnl'])}"
        )

    orphans = report["orphans"]
    print(f"\n## Positions ORPHELINES — hors grid active ({len(orphans)})\n")
    if not orphans:
        print("(aucune orpheline détectée — compte 100 % piloté par grids)")
        return
    for o in orphans:
        print(
            f"- {o['symbol']:12} {o['side']:5} size={o['size']:>8} "
            f"@ ${o['price']:.4f}  notional ~${o['notional']:.2f}  "
            f"uPnL={format_usd(o['unrealizedPnl'])}\n"
            f"  → {o['classification']}"
        )
    print(f"\nTotal uPnL orphelin : {format_usd(report['total_orphan_upnl'])}")
    if report["status"] == "ZOMBIE_SUSPECTED":
        print("\n⚠️  Au moins une orpheline classée ZOMBIE-CANDIDATE — inspecter avant tout redeploy.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--json", action="store_true", help="Output structured JSON instead of human report.")
    args = parser.parse_args()

    try:
        active_raw = curl("/api/grid/active")
        positions_raw = curl("/api/bot/positions")
        orders_raw = curl("/api/bot/orders")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"ERROR fetching from Martin API: {e}", file=sys.stderr)
        return 2

    try:
        active = set(json.loads(active_raw))
        positions = json.loads(positions_raw)
        orders = json.loads(orders_raw)
    except json.JSONDecodeError as e:
        print(f"ERROR parsing JSON: {e}", file=sys.stderr)
        return 2

    report = build_report(active, positions, orders)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_human(report)

    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())

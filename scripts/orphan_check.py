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


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

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

    print(f"# orphan_check — {ts}\n")
    print(f"Grids actives Martin : {sorted(active) if active else '(aucune)'}")
    print(f"Positions Kraken     : {len(positions)}")
    print(f"Orders live Kraken   : {len(orders)}\n")

    orphans = [p for p in positions if p.get("symbol") not in active]
    grid_positions = [p for p in positions if p.get("symbol") in active]

    print(f"## Positions rattachées à une grid ({len(grid_positions)})\n")
    if not grid_positions:
        print("(aucune)\n")
    for p in grid_positions:
        upnl = p.get("unrealizedPnl", 0) or 0
        print(
            f"- {p['symbol']:12} {p['side']:5} size={p['size']:>8} "
            f"@ ${p['price']:.4f} uPnL={format_usd(upnl)}"
        )

    print(f"\n## Positions ORPHELINES — hors grid active ({len(orphans)})\n")
    if not orphans:
        print("(aucune orpheline détectée — compte 100 % piloté par grids)")
        return 0

    total_orphan_upnl = 0.0
    for p in orphans:
        upnl = p.get("unrealizedPnl", 0) or 0
        total_orphan_upnl += upnl
        cat = classify(p["symbol"], orders)
        notional = float(p.get("size", 0)) * float(p.get("price", 0))
        print(
            f"- {p['symbol']:12} {p['side']:5} size={p['size']:>8} "
            f"@ ${p['price']:.4f}  notional ~${notional:.2f}  "
            f"uPnL={format_usd(upnl)}\n"
            f"  → {cat}"
        )

    print(f"\nTotal uPnL orphelin : {format_usd(total_orphan_upnl)}")
    return 0 if all(
        classify(p["symbol"], orders).startswith("DISCRETIONARY") for p in orphans
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())

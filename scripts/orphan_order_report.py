#!/usr/bin/env python3
"""
orphan_order_report.py — cycle 265, 2026-08-06

Complète orphan_check.py : analyse les ORDRES sur positions orphelines.

Un ordre sur une position orpheline peut être :
  - reduceOnly=true  → referme la position (SL, TP, closeOnly LMT) — OK
  - reduceOnly=false → peut AJOUTER à la position — DANGEREUX si non voulu

Ce cas s'est présenté cycle 265 : SOL orphan SHORT 0.16u, sell lmt @74.46 reduceOnly=false.
Si SOL monte à 74.46, l'ordre ouvre un nouveau SHORT 0.16u au lieu de fermer.

Usage:
  python scripts/orphan_order_report.py
  python scripts/orphan_order_report.py --json
  python scripts/orphan_order_report.py --symbol PF_SOLUSD
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


def order_price(order: dict) -> float | None:
    return order.get("limitPrice") or order.get("stopPrice")


def order_type_label(order: dict) -> str:
    t = order.get("orderType", "?")
    side = order.get("side", "?")
    price = order_price(order)
    price_str = f"@{price:.4f}" if price else ""
    ro = "reduceOnly" if order.get("reduceOnly") else "NOT-reduceOnly"
    return f"{side} {t} {price_str} [{ro}]"


def risk_level(pos: dict, order: dict) -> str:
    """
    Assess risk of an order on an orphan position.
    RISK if order could add to exposure (non-reduceOnly + direction that opens).
    """
    if order.get("reduceOnly"):
        return "OK"

    pos_side = pos["side"]  # "long" or "short"
    ord_side = order.get("side", "")  # "buy" or "sell"

    # Order adds to position if same direction
    opens_long = ord_side == "buy" and pos_side == "long"
    opens_short = ord_side == "sell" and pos_side == "short"

    if opens_long or opens_short:
        return "WARN:adds-exposure"

    # Opposite direction without reduceOnly = opens a new opposing position
    return "WARN:opens-opposite"


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyse orders on orphan positions")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--symbol", help="Filter by symbol (e.g. PF_SOLUSD)")
    args = parser.parse_args()

    try:
        active_raw = curl("/api/grid/active")
        positions_raw = curl("/api/bot/positions")
        orders_raw = curl("/api/bot/orders")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    try:
        active = set(json.loads(active_raw))
        positions = json.loads(positions_raw)
        orders = json.loads(orders_raw)
    except json.JSONDecodeError as e:
        print(f"ERROR parsing JSON: {e}", file=sys.stderr)
        return 2

    orphan_positions = [p for p in positions if p.get("symbol") not in active]
    if args.symbol:
        orphan_positions = [p for p in orphan_positions if p.get("symbol") == args.symbol]

    report_items = []
    has_risk = False

    for pos in orphan_positions:
        sym = pos["symbol"]
        sym_orders = [o for o in orders if o.get("symbol") == sym]

        order_analysis = []
        for o in sym_orders:
            risk = risk_level(pos, o)
            if risk != "OK":
                has_risk = True
            order_analysis.append({
                "order_id": o.get("order_id", "?")[:12],
                "label": order_type_label(o),
                "reduceOnly": bool(o.get("reduceOnly")),
                "risk": risk,
            })

        report_items.append({
            "symbol": sym,
            "side": pos["side"],
            "size": pos["size"],
            "entry_price": pos["price"],
            "unrealized_pnl": round(float(pos.get("unrealizedPnl", 0) or 0), 4),
            "orders": order_analysis,
        })

    result = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "active_grids": sorted(active),
        "orphan_count": len(orphan_positions),
        "has_risk": has_risk,
        "positions": report_items,
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return 1 if has_risk else 0

    # Human report
    ts = result["timestamp"].replace("T", " ")
    print(f"# orphan_order_report — {ts}\n")
    print(f"Grids actives : {sorted(active) if active else '(aucune)'}")
    print(f"Positions orphelines : {len(orphan_positions)}\n")

    if not orphan_positions:
        print("Aucune position orpheline. Compte 100% grid-piloted.")
        return 0

    for item in result["positions"]:
        sym = item["symbol"]
        upnl_sign = "+" if item["unrealized_pnl"] >= 0 else ""
        print(f"## {sym}  {item['side'].upper()}  {item['size']}u @ ${item['entry_price']:.4f}  "
              f"uPnL {upnl_sign}${item['unrealized_pnl']:.4f}")
        if not item["orders"]:
            print("  (aucun ordre live sur ce symbole)")
        for o in item["orders"]:
            risk_tag = "✓" if o["risk"] == "OK" else f"⚠️  {o['risk']}"
            print(f"  [{o['order_id']}...] {o['label']}  {risk_tag}")
        print()

    if has_risk:
        print("⚠️  RISQUE DÉTECTÉ : au moins un ordre non-reduceOnly sur position orpheline.")
        print("   → Vérifier manuellement via Kraken Pro et canceller si non voulu.")
        return 1

    print("✓ Tous les ordres sur positions orphelines sont reduceOnly — aucun risque d'ajout d'exposition.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

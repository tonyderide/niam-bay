#!/usr/bin/env python3
"""
Position Tracker — Martin Grid Bot
====================================
Lit /api/bot/positions + /api/bot/orders et génère un rapport structuré
avec distance SL, perte max si SL fire, et state de chaque position.

Usage :
  # Depuis le PC local (SSH tunnel requis) :
  ssh -i ~/.ssh/martin_vm.key -L 8081:localhost:8081 ubuntu@141.253.108.141 -N &
  python3 scripts/position_tracker.py

  # Sur la VM directement :
  python3 position_tracker.py

  # Via SSH one-shot :
  ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "python3 /path/to/position_tracker.py"
"""

import json
import urllib.request
import urllib.error
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

MARTIN_HOST = "localhost"
MARTIN_PORT = 8081
BASE = f"http://{MARTIN_HOST}:{MARTIN_PORT}"


def fetch(path: str) -> Union[dict, list]:
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[ERROR] {path}: {e}", file=sys.stderr)
        return {}


@dataclass
class SLOrder:
    price: float
    order_id: str


@dataclass
class TPOrder:
    price: float
    order_id: str


@dataclass
class Position:
    symbol: str
    side: str           # "long" | "short"
    size: float
    entry: float        # avg entry price
    current: float      # derived from unrealizedPnl
    upnl: float         # unrealized PnL in USD
    sl: Optional[SLOrder] = None
    tp: Optional[TPOrder] = None
    extra_limits: list = field(default_factory=list)  # non-SL/TP lmt orders

    @property
    def upnl_pct(self) -> float:
        notional = self.size * self.entry
        return (self.upnl / notional * 100) if notional else 0.0

    @property
    def dist_sl_pct(self) -> Optional[float]:
        if not self.sl:
            return None
        # For long: SL below current, distance = (current - sl) / current
        # For short: SL above current, distance = (sl - current) / current
        if self.side == "long":
            return (self.current - self.sl.price) / self.current * 100
        else:
            return (self.sl.price - self.current) / self.current * 100

    @property
    def loss_at_sl(self) -> Optional[float]:
        """Additional P&L delta if SL fires from current price."""
        if not self.sl:
            return None
        if self.side == "long":
            return self.size * (self.sl.price - self.current)  # negative = loss
        else:
            return self.size * (self.current - self.sl.price)  # positive = gain (SL cuts short loss)

    @property
    def total_at_sl(self) -> Optional[float]:
        """Total P&L from entry if SL fires."""
        if not self.sl:
            return None
        if self.side == "long":
            return self.size * (self.sl.price - self.entry)
        else:
            return self.size * (self.entry - self.sl.price)

    @property
    def dist_tp_pct(self) -> Optional[float]:
        if not self.tp:
            return None
        if self.side == "long":
            return (self.tp.price - self.current) / self.current * 100
        else:
            return (self.current - self.tp.price) / self.current * 100

    @property
    def gain_at_tp(self) -> Optional[float]:
        if not self.tp:
            return None
        if self.side == "long":
            return self.size * (self.tp.price - self.entry)
        else:
            return self.size * (self.entry - self.tp.price)


def derive_current(side: str, size: float, entry: float, upnl: float) -> float:
    """Derive current price from unrealized PnL."""
    if side == "long":
        return entry + upnl / size if size else entry
    else:
        return entry - upnl / size if size else entry


def build_positions(raw_pos: list, raw_orders: list) -> List[Position]:
    # Index orders by symbol
    by_symbol: Dict[str, list] = {}
    for o in raw_orders:
        s = o.get("symbol", "")
        by_symbol.setdefault(s, []).append(o)

    positions = []
    for p in raw_pos:
        sym = p["symbol"]
        side = p["side"]
        size = float(p["size"])
        entry = float(p["price"])
        upnl = float(p.get("unrealizedPnl", 0))
        current = derive_current(side, size, entry, upnl)

        pos = Position(
            symbol=sym,
            side=side,
            size=size,
            entry=entry,
            current=current,
            upnl=upnl,
        )

        orders = by_symbol.get(sym, [])
        for o in orders:
            ot = o.get("orderType", "")
            o_side = o.get("side", "")
            reduce = o.get("reduceOnly", False)
            sp = o.get("stopPrice")
            lp = o.get("limitPrice")
            oid = o.get("order_id", "?")

            if ot == "stop" and reduce:
                # SL: stop order reduceOnly
                if sp:
                    pos.sl = SLOrder(price=float(sp), order_id=oid)
            elif ot == "take_profit" and reduce:
                if sp:
                    pos.tp = TPOrder(price=float(sp), order_id=oid)
            elif ot == "lmt" and reduce and lp:
                # Limit take-profit (some grids use lmt reduceOnly as TP)
                if not pos.tp:
                    pos.tp = TPOrder(price=float(lp), order_id=oid)
            elif ot == "lmt" and not reduce and lp:
                pos.extra_limits.append(float(lp))

        positions.append(pos)
    return positions


def fmt_price(sym: str, price: float) -> str:
    if "XBT" in sym:
        return f"${price:,.2f}"
    elif price >= 10:
        return f"${price:.4f}"
    elif price >= 1:
        return f"${price:.4f}"
    else:
        return f"${price:.5f}"


def render(positions: List[Position], balance: dict) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("  POSITION TRACKER — Martin")
    lines.append("=" * 60)

    flex = balance.get("accounts", {}).get("flex", {})
    pv = flex.get("portfolioValue", 0)
    bv = flex.get("balanceValue", 0)
    upnl_total = flex.get("pnl", 0)
    avail = flex.get("availableMargin", 0)
    dd_pct = (upnl_total / bv * 100) if bv else 0

    lines.append(f"\nPortfolio : ${pv:.2f} (déposé ${bv:.2f})")
    lines.append(f"uPnL total: ${upnl_total:+.2f} ({dd_pct:+.1f}%)")
    lines.append(f"Marge dispo: ${avail:.2f}")

    if not positions:
        lines.append("\nAucune position ouverte.")
        return "\n".join(lines)

    lines.append(f"\n{len(positions)} position(s) ouvertes :\n")

    for pos in positions:
        side_icon = "▲ LONG" if pos.side == "long" else "▼ SHORT"
        lines.append(f"  {pos.symbol}  {side_icon}  {pos.size}u")
        lines.append(f"    Entrée  : {fmt_price(pos.symbol, pos.entry)}")
        lines.append(f"    Actuel  : {fmt_price(pos.symbol, pos.current)}")
        lines.append(f"    uPnL    : ${pos.upnl:+.4f}  ({pos.upnl_pct:+.2f}%)")

        if pos.sl:
            dist = pos.dist_sl_pct
            loss_delta = pos.loss_at_sl
            total_loss = pos.total_at_sl
            dist_str = f"{dist:.2f}%" if dist is not None else "?"
            delta_str = f"${loss_delta:+.2f}" if loss_delta is not None else "?"
            total_str = f"${total_loss:+.2f}" if total_loss is not None else "?"
            sl_icon = "🔴 SL PROCHE" if dist is not None and dist < 5 else "🟡 SL" if dist is not None and dist < 15 else "✅ SL"
            lines.append(f"    {sl_icon}     : {fmt_price(pos.symbol, pos.sl.price)}  (−{dist_str} actuel → delta {delta_str} / total {total_str})")
        else:
            lines.append(f"    ⚠️  PAS DE SL DÉTECTÉ")

        if pos.tp:
            dist_tp = pos.dist_tp_pct
            gain = pos.gain_at_tp
            dist_str = f"{dist_tp:.2f}%" if dist_tp is not None else "?"
            gain_str = f"${gain:+.2f}" if gain is not None else "?"
            lines.append(f"    TP      : {fmt_price(pos.symbol, pos.tp.price)}  (+{dist_str} → gain {gain_str})")

        if pos.extra_limits:
            lmt_str = "  ".join(fmt_price(pos.symbol, p) for p in sorted(pos.extra_limits))
            lines.append(f"    Lmt ord : {lmt_str}")

        lines.append("")

    # Risk summary
    total_sl_exposure = sum(
        p.loss_at_sl for p in positions if p.loss_at_sl is not None and p.loss_at_sl < 0
    )
    lines.append("-" * 60)
    lines.append(f"Perte max si tous SL fire : ${total_sl_exposure:+.2f}")
    lines.append(f"Portfolio post-SL (pire cas) : ${pv + total_sl_exposure:.2f}")
    lines.append("=" * 60)

    return "\n".join(lines)


def main():
    print("Fetching positions...", file=sys.stderr)
    raw_pos = fetch("/api/bot/positions")
    raw_orders = fetch("/api/bot/orders")
    balance = fetch("/api/bot/balance")

    if not isinstance(raw_pos, list):
        print("[ERROR] /api/bot/positions returned unexpected format", file=sys.stderr)
        raw_pos = []
    if not isinstance(raw_orders, list):
        raw_orders = []

    positions = build_positions(raw_pos, raw_orders)
    print(render(positions, balance))


if __name__ == "__main__":
    main()

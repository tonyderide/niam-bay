"""
v17 Strategy Backtest — Tony deploy 2026-05-18 00:48 UTC
Cycle 58 — 2026-05-18

Tony pushed strategy v17 overnight ("consensus 8 sources REDUCE"):
  - 3 grids LINK + ADA + ETH (drop BTC, DOT, SOL)
  - capital $25/grid, leverage 7x, spacing 3.0%, 4 levels, maxLoss 10%
  - totalCapital $75 (down from $138)
  - lastDeployment.success=false (gate CLOSED RSI 25.95 at the moment)

Question for the backtest:
  Empirically valider le choix "wider spacing 3.0%" vs "tighter 1.5%"
  sur les 3 paires retenues, sur 30 jours 1min Binance.

3 configs comparées par paire:
  A) v17 Tony      — spacing 3.0%, 4 levels  (le nouveau)
  B) v17 tight     — spacing 1.5%, 4 levels  (variante)
  C) v17 medium    — spacing 2.0%, 4 levels  (compromis)

Pour chaque (pair × config):
  - realized PnL, fills, RT, hard-stop fired
  - max drawdown unrealized
  - efficacité = realized PnL / fills count

Pas de gate ni de pause. On veut savoir si le grid SEUL avec ces paramètres tient.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple

ROOT = Path("/home/tony/projets/tonyderide/niam-bay")
CACHE = ROOT / "ai-lab/darwin/data_cache"
sys.path.insert(0, str(ROOT / "ai-lab/darwin"))

from ppt_pause_backtest import GridState, load_candles


def run_grid_no_pause(candles_1m: List[List], spacing_pct: float, levels: int,
                     capital: float = 25.0, leverage: int = 7,
                     max_loss_pct: float = 0.10) -> Dict:
    if not candles_1m:
        return {"error": "no data"}

    center_price = candles_1m[0][1]  # open of first candle
    grid = GridState(
        center_price=center_price,
        capital_usd=capital,
        leverage=leverage,
        levels_count=levels,
        spacing_pct=spacing_pct,
        fees_pct=0.0005,
        max_loss_pct=max_loss_pct,
    )

    max_drawdown_pct = 0.0
    last_event_ms = candles_1m[-1][0]

    for cd in candles_1m:
        ts_ms, o, h, low, close, vol = cd
        result = grid.tick(low, high=h, close=close)
        # track max unrealized drawdown as pct of capital
        upnl = grid.unrealized(close)
        dd_pct = -upnl / capital if upnl < 0 else 0.0
        if dd_pct > max_drawdown_pct:
            max_drawdown_pct = dd_pct
        if result == "STOP":
            last_event_ms = ts_ms
            break

    final_close = candles_1m[-1][4]
    total_pnl = grid.total_pnl(final_close)
    realized = grid.realized_pnl
    unrealized = grid.unrealized(final_close)

    # estimate round-trips: a RT = matched buy+sell pair → realized profit
    # heuristic: pair fills count // 2 = approx RT count (NEUTRAL has equal buy/sell pairs)
    rt_count = grid.fills // 2

    return {
        "fills": grid.fills,
        "rt_approx": rt_count,
        "realized_pnl": round(realized, 4),
        "unrealized_pnl_final": round(unrealized, 4),
        "total_pnl": round(total_pnl, 4),
        "max_drawdown_pct": round(max_drawdown_pct * 100, 2),
        "stopped": grid.stopped,
        "stop_reason": grid.stop_reason,
        "position_remaining": round(grid.position_units, 6),
        "center_price": round(center_price, 6),
        "candles_processed": min(len(candles_1m),
                                  next((i for i, c in enumerate(candles_1m) if c[0] >= last_event_ms), len(candles_1m))),
        "duration_days": round((candles_1m[-1][0] - candles_1m[0][0]) / (86400_000), 1),
    }


def format_row(label: str, r: Dict) -> str:
    if "error" in r:
        return f"  {label:18s}: ERROR — {r['error']}"
    stopped = "STOP" if r["stopped"] else "OK  "
    return (f"  {label:18s}: PnL=${r['total_pnl']:+7.3f} "
            f"realized=${r['realized_pnl']:+7.3f} fills={r['fills']:3d} RT≈{r['rt_approx']:3d} "
            f"maxDD={r['max_drawdown_pct']:5.2f}% [{stopped}]")


def main():
    pairs = [
        ("LINK", CACHE / "binance_LINKUSDT_1min_30d.json"),
        ("ADA",  CACHE / "binance_ADAUSDT_1min_30d.json"),
        ("ETH",  CACHE / "binance_ETHUSDT_1min_30d.json"),
    ]
    configs = [
        ("A v17 Tony 3.0%",  3.0,  4),
        ("B v17 tight 1.5%", 1.5,  4),
        ("C v17 med 2.0%",   2.0,  4),
        ("D v17 wide 4.0%",  4.0,  4),  # control: even wider
        ("E v17 6 lvl 2.0%", 2.0,  6),  # control: more levels
    ]

    print("=" * 78)
    print("V17 STRATEGY BACKTEST — Cycle 58 — 2026-05-18")
    print(f"Data: 30j 1min Binance | grid params: $25 cap, 7x lev, maxLoss 10%")
    print("=" * 78)

    totals = {label: {"pnl": 0.0, "fills": 0, "rt": 0, "stops": 0} for label, _, _ in configs}

    for pair_name, path in pairs:
        candles = load_candles(path)
        if not candles:
            print(f"\n{pair_name}: data missing at {path}")
            continue
        print(f"\n{pair_name} ({len(candles)} candles, "
              f"{round((candles[-1][0]-candles[0][0])/86400_000,1)}j):")
        for label, spacing, lvls in configs:
            r = run_grid_no_pause(candles, spacing/100.0, lvls)
            totals[label]["pnl"] += r.get("total_pnl", 0.0)
            totals[label]["fills"] += r.get("fills", 0)
            totals[label]["rt"] += r.get("rt_approx", 0)
            if r.get("stopped"):
                totals[label]["stops"] += 1
            print(format_row(label, r))

    print("\n" + "=" * 78)
    print("PORTFOLIO TOTALS (3 paires LINK+ADA+ETH cumulés):")
    print("=" * 78)
    for label, _, _ in configs:
        t = totals[label]
        marker = "  ←Tony" if "Tony" in label else ""
        print(f"  {label:18s}: ΣPnL=${t['pnl']:+8.3f} Σfills={t['fills']:3d} "
              f"ΣRT≈{t['rt']:3d} stops={t['stops']}/3{marker}")

    # rank by total PnL
    ranked = sorted(totals.items(), key=lambda kv: -kv[1]["pnl"])
    print("\nRanking (best → worst total PnL):")
    for i, (label, t) in enumerate(ranked, 1):
        print(f"  {i}. {label:18s} ${t['pnl']:+.3f}")

    print("\nNOTE: backtest sans gate ni pause — montre le comportement du grid")
    print("seul. Le live ajoute RegimeGate (skip si conditions hors IQR) qui filtre")
    print("les régimes hostiles. v17 Tony bénéficie aussi de l'auto-unstuck.")


if __name__ == "__main__":
    main()

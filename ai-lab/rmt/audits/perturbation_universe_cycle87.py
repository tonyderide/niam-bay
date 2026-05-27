"""Cycle 87 — Perturbation test: does the anchor edge scale to N=4?

Cycle 85b (N=3) showed the BTC-anchor effect: with BTC in the universe,
min-variance beats eq-weight by ~+0.32 Sharpe; without BTC, +0.03 Sharpe.

Open question cycle 86: does the edge **scale** when N moves from 3 to 4?
Two competing scenarios:
  H_scale  : adding a 4th asset preserves or grows the edge (anchor still dominant)
  H_dilute : adding a 4th asset dilutes the BTC weight too much, edge erodes

Test universes:
  LINK+ADA+ETH+BTC   : Option B candidate (3 alts + BTC anchor)
  LINK+ADA+SOL+BTC   : alts variation with BTC anchor
  ETH+SOL+BTC+LINK   : majors-heavy + BTC anchor
  LINK+ADA+SOL+ETH   : 4 alts, no anchor (control)
  LINK+ADA+ETH+SOL   : permutation of above (sanity)

Verdict rule:
  If BTC-universes ΔSharpe stays >= +0.25 → H_scale (Option B confirmed for N=4)
  If BTC-universes ΔSharpe drops to ~+0.10 or less → H_dilute (cap N=3 with BTC)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from rmt.data_loader import load_panel_returns
from rmt.martin_allocation import allocate_capital

TOTAL_CAPITAL = 120.0
TF = "4h"
WINDOW = 360
REBALANCE_STEP = 42
ANNUALIZE = 6 * 365


def realized_sharpe(returns: pd.Series, ann: int = ANNUALIZE) -> float:
    if returns.std() <= 0 or len(returns) == 0:
        return 0.0
    return float(returns.mean() / returns.std() * np.sqrt(ann))


def max_drawdown(returns: pd.Series) -> float:
    cum = returns.cumsum()
    peak = cum.cummax()
    dd = cum - peak
    return float(dd.min())


def walk_forward(rets, strategy_fn, window=WINDOW, step=REBALANCE_STEP):
    n = len(rets)
    out_chunks = []
    t = window
    while t + step <= n:
        train = rets.iloc[t - window : t]
        weights = strategy_fn(train)
        oos = rets.iloc[t : t + step]
        port = (oos * weights.reindex(oos.columns).values).sum(axis=1)
        out_chunks.append(port)
        t += step
    return pd.concat(out_chunks) if out_chunks else pd.Series(dtype=float)


def eq_strategy(train):
    n = train.shape[1]
    return pd.Series([1.0 / n] * n, index=train.columns)


def mv_floor_10_strategy(train):
    alloc = allocate_capital(
        train,
        total_capital=TOTAL_CAPITAL,
        method="raw",
        min_capital_per_pair=10.0,
    )
    return pd.Series(alloc) / TOTAL_CAPITAL


UNIVERSES = [
    ("LINK_ADA_ETH_BTC", ["LINK", "ADA", "ETH", "BTC"], "Option B candidate"),
    ("LINK_ADA_SOL_BTC", ["LINK", "ADA", "SOL", "BTC"], "alts + BTC anchor"),
    ("ETH_SOL_BTC_LINK", ["ETH",  "SOL", "BTC", "LINK"], "majors + BTC anchor"),
    ("LINK_ADA_SOL_ETH", ["LINK", "ADA", "SOL", "ETH"], "4 alts no anchor"),
    ("LINK_ADA_ETH_SOL", ["LINK", "ADA", "ETH", "SOL"], "permutation no anchor"),
]


def main():
    print("=== Cycle 87 — Perturbation N=4: does anchor edge scale? ===\n")

    rows = []
    for name, pairs, desc in UNIVERSES:
        try:
            rets = load_panel_returns(pairs, tf=TF)
        except FileNotFoundError as e:
            print(f"{name}  SKIP  {e}")
            continue

        oos_eq = walk_forward(rets, eq_strategy)
        oos_mv = walk_forward(rets, mv_floor_10_strategy)

        sh_eq, sh_mv = realized_sharpe(oos_eq), realized_sharpe(oos_mv)
        dd_eq, dd_mv = max_drawdown(oos_eq), max_drawdown(oos_mv)

        weights_path = []
        t = WINDOW
        while t + REBALANCE_STEP <= len(rets):
            train = rets.iloc[t - WINDOW : t]
            w = mv_floor_10_strategy(train)
            weights_path.append(w)
            t += REBALANCE_STEP
        avg_w = pd.DataFrame(weights_path).mean()

        anchor = "BTC" if "BTC" in pairs else ("ETH" if "ETH" in pairs else pairs[0])
        anchor_weight = float(avg_w[anchor])

        delta_sharpe = sh_mv - sh_eq
        dd_ratio = dd_mv / dd_eq if dd_eq != 0 else float("nan")

        rows.append({
            "universe": name,
            "desc": desc,
            "n": len(pairs),
            "sh_eq": sh_eq,
            "sh_mv": sh_mv,
            "delta_sharpe": delta_sharpe,
            "dd_eq": dd_eq,
            "dd_mv": dd_mv,
            "dd_ratio": dd_ratio,
            "anchor": anchor,
            "anchor_avg_weight": anchor_weight,
            "n_periods": len(oos_eq),
        })

        print(f"{name:18s}  {desc}")
        print(f"  Sharpe  eq={sh_eq:+.3f}  mv={sh_mv:+.3f}  Δ={delta_sharpe:+.3f}")
        print(f"  maxDD   eq={dd_eq:+.3f}  mv={dd_mv:+.3f}  ratio={dd_ratio:.2f}")
        print(f"  Anchor {anchor} avg weight in mv: {anchor_weight:.1%}")
        print()

    df = pd.DataFrame(rows)
    out_csv = Path(__file__).parent / "perturbation_universe_cycle87_results.csv"
    df.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}\n")

    print("=== Hypothesis verdict ===")
    with_btc = [r for r in rows if "BTC" in r["universe"]]
    no_btc = [r for r in rows if "BTC" not in r["universe"]]
    if with_btc and no_btc:
        avg_with_btc = np.mean([r["delta_sharpe"] for r in with_btc])
        avg_no_btc = np.mean([r["delta_sharpe"] for r in no_btc])
        diff = avg_with_btc - avg_no_btc
        print(f"avg ΔSharpe with-BTC universes (N=4):    {avg_with_btc:+.3f}")
        print(f"avg ΔSharpe no-BTC universes (N=4):      {avg_no_btc:+.3f}")
        print(f"diff (BTC effect at N=4):                {diff:+.3f}")
        print()
        print("Compare to cycle 85b (N=3): with-BTC=+0.320, no-BTC=+0.026, diff=+0.294")
        if avg_with_btc >= 0.25:
            print("  → H_scale supported: anchor edge survives at N=4 (Option B confirmed)")
        elif avg_with_btc < 0.10:
            print("  → H_dilute supported: keep N=3 with BTC")
        else:
            print("  → partial: edge present but eroded vs N=3, judgment call")


if __name__ == "__main__":
    main()

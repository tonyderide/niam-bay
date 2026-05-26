"""Cycle 85b — Perturbation test: is the cycle 85 finding about N or about anchor presence?

Cycle 85 (LINK+ADA+ETH) showed ΔSharpe min-variance vs eq-weight dropped from
+0.25 (cycle 82, 5 pairs with BTC) to +0.09 (3 pairs, no BTC). Two competing
hypotheses:
  H_N    : it's the universe size N that matters (N=3 → low edge regardless)
  H_anch : it's the absence of a low-vol anchor like BTC that matters

Test by running walk-forward on additional 3-pair universes and ranking edge:
  - LINK+ADA+SOL  : 3 alts, no anchor (similar to c85)         → predict c85-like
  - LINK+ADA+BTC  : 3 pairs WITH BTC anchor                     → H_anch predicts >>c85
  - ETH+SOL+BTC   : 3 majors with anchor                        → H_anch predicts >>c85
  - LINK+ADA+ETH  : c85 baseline (re-run for sanity)            → reproduces c85

If LINK+ADA+BTC and ETH+SOL+BTC restore the +0.25 edge, H_anch wins.
If they stay at +0.09, H_N wins.
If results are mixed, it's both.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from rmt.data_loader import load_panel_returns
from rmt.martin_allocation import allocate_capital, min_variance_allocation


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
    alloc = allocate_capital(train, total_capital=TOTAL_CAPITAL, method="raw", min_capital_per_pair=10.0)
    return pd.Series(alloc) / TOTAL_CAPITAL


UNIVERSES = [
    ("LINK_ADA_ETH",  ["LINK", "ADA", "ETH"],  "baseline c85"),
    ("LINK_ADA_SOL",  ["LINK", "ADA", "SOL"],  "3 alts no anchor"),
    ("LINK_ADA_BTC",  ["LINK", "ADA", "BTC"],  "3 with BTC anchor"),
    ("ETH_SOL_BTC",   ["ETH",  "SOL", "BTC"],  "3 majors with anchor"),
]


def main():
    print("=== Cycle 85b — Perturbation: N vs anchor hypothesis ===\n")

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

        # mv weight on the anchor candidate (BTC if present, else ETH if present, else first)
        weights_path = []
        t = WINDOW
        while t + REBALANCE_STEP <= len(rets):
            train = rets.iloc[t - WINDOW : t]
            w = mv_floor_10_strategy(train)
            weights_path.append(w)
            t += REBALANCE_STEP
        avg_w = pd.DataFrame(weights_path).mean()

        anchor = "BTC" if "BTC" in pairs else ("ETH" if "ETH" in pairs else pairs[0])
        anchor_weight = avg_w[anchor]

        delta_sharpe = sh_mv - sh_eq
        dd_ratio = dd_mv / dd_eq if dd_eq != 0 else float("nan")

        rows.append({
            "universe": name,
            "desc": desc,
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

        print(f"{name:16s}  {desc}")
        print(f"  Sharpe  eq={sh_eq:+.3f}  mv_floor10={sh_mv:+.3f}  Δ={delta_sharpe:+.3f}")
        print(f"  maxDD   eq={dd_eq:+.3f}  mv_floor10={dd_mv:+.3f}  ratio={dd_ratio:.2f}")
        print(f"  Anchor {anchor} avg weight in mv: {anchor_weight:.1%}")
        print()

    df = pd.DataFrame(rows)
    out_csv = Path(__file__).parent / "perturbation_universe_cycle85b_results.csv"
    df.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}\n")

    print("=== Hypothesis verdict ===")
    if len(rows) >= 3:
        anchor_universes = [r for r in rows if r["anchor"] == "BTC"]
        no_btc_universes = [r for r in rows if r["anchor"] != "BTC"]
        if anchor_universes and no_btc_universes:
            avg_with_btc = np.mean([r["delta_sharpe"] for r in anchor_universes])
            avg_no_btc = np.mean([r["delta_sharpe"] for r in no_btc_universes])
            print(f"avg ΔSharpe with-BTC universes:    {avg_with_btc:+.3f}")
            print(f"avg ΔSharpe no-BTC universes:      {avg_no_btc:+.3f}")
            diff = avg_with_btc - avg_no_btc
            print(f"diff (BTC effect):                 {diff:+.3f}")
            if diff > 0.10:
                print("  → H_anch supported (BTC presence matters)")
            elif diff < 0.05:
                print("  → H_N supported (N=3 floors the edge regardless)")
            else:
                print("  → mixed; needs more universes to disambiguate")


if __name__ == "__main__":
    main()

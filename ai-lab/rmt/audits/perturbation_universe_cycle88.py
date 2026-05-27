"""Cycle 88 — Perturbation N=5: where does the anchor edge erode?

Cycle 85b (N=3): with-BTC ΔSharpe=+0.320, no-BTC=+0.026, BTC effect=+0.294
Cycle 87 (N=4) : with-BTC ΔSharpe=+0.302, no-BTC=-0.032, BTC effect=+0.334
  → edge survives, BTC weight drops 82% → 64.8% but anchor still dominant.

Cycle 88 (N=5): does the edge keep scaling, or do we hit the frontier
where dilution finally kills it?

Test universes:
  LINK+ADA+SOL+ETH+BTC  : Option C candidate (4 alts + BTC anchor)
  LINK+ADA+SOL+BTC+AVAX : alts + BTC + 1 extra alt (AVAX)
  ETH+SOL+BTC+LINK+ADA  : permutation (must match Option C)
  LINK+ADA+SOL+ETH+AVAX : 5 alts no anchor (control)
  LINK+ADA+SOL+ETH+APT  : 5 alts no anchor variation

Hypotheses (rule cycle 86: publish refutability condition with the rule):
  H_robust : avg ΔSharpe with-BTC ≥ +0.25 → anchor edge scales further (Option C viable)
  H_erode  : avg ΔSharpe with-BTC ∈ [+0.10, +0.25) → partial erosion, judgment call
  H_dies   : avg ΔSharpe with-BTC < +0.10 → frontier reached, cap N=4 with BTC

Pre-registered: this script is committed BEFORE the run reads results.
The verdict block at the bottom applies the seuils mechanically.
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
    ("LINK_ADA_SOL_ETH_BTC", ["LINK", "ADA", "SOL", "ETH", "BTC"], "Option C candidate (4 alts + BTC)"),
    ("LINK_ADA_SOL_BTC_AVAX", ["LINK", "ADA", "SOL", "BTC", "AVAX"], "alts + BTC + AVAX"),
    ("ETH_SOL_BTC_LINK_ADA", ["ETH", "SOL", "BTC", "LINK", "ADA"], "permutation Option C (sanity)"),
    ("LINK_ADA_SOL_ETH_AVAX", ["LINK", "ADA", "SOL", "ETH", "AVAX"], "5 alts no anchor"),
    ("LINK_ADA_SOL_ETH_APT", ["LINK", "ADA", "SOL", "ETH", "APT"], "5 alts no anchor variation"),
]


def main():
    print("=== Cycle 88 — Perturbation N=5: where does the edge erode? ===\n")

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

        print(f"{name:24s}  {desc}")
        print(f"  Sharpe  eq={sh_eq:+.3f}  mv={sh_mv:+.3f}  Δ={delta_sharpe:+.3f}")
        print(f"  maxDD   eq={dd_eq:+.3f}  mv={dd_mv:+.3f}  ratio={dd_ratio:.2f}")
        print(f"  Anchor {anchor} avg weight in mv: {anchor_weight:.1%}")
        print()

    df = pd.DataFrame(rows)
    out_csv = Path(__file__).parent / "perturbation_universe_cycle88_results.csv"
    df.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}\n")

    print("=== Hypothesis verdict ===")
    with_btc = [r for r in rows if "BTC" in r["universe"]]
    no_btc = [r for r in rows if "BTC" not in r["universe"]]
    if with_btc and no_btc:
        avg_with_btc = np.mean([r["delta_sharpe"] for r in with_btc])
        avg_no_btc = np.mean([r["delta_sharpe"] for r in no_btc])
        diff = avg_with_btc - avg_no_btc
        print(f"avg ΔSharpe with-BTC universes (N=5):    {avg_with_btc:+.3f}")
        print(f"avg ΔSharpe no-BTC universes (N=5):      {avg_no_btc:+.3f}")
        print(f"diff (BTC effect at N=5):                {diff:+.3f}")
        print()
        print("Compare:")
        print("  cycle 85b (N=3): with-BTC=+0.320, no-BTC=+0.026, diff=+0.294")
        print("  cycle 87  (N=4): with-BTC=+0.302, no-BTC=-0.032, diff=+0.334")
        print()
        if avg_with_btc >= 0.25:
            print("  → H_robust supported: anchor edge survives at N=5 (Option C viable)")
        elif avg_with_btc >= 0.10:
            print("  → H_erode supported: partial erosion, N=5 marginal vs N=3/4")
        else:
            print("  → H_dies supported: frontier reached, cap N=4 with BTC")


if __name__ == "__main__":
    main()

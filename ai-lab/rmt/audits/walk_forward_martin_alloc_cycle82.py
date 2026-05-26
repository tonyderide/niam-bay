"""Cycle 82 — Walk-forward OOS validation of martin_allocation.

In-sample (cycle 81) showed min-variance with $10 floor beats equal-weight by
+0.037 Sharpe on the last 60d. That's the *fit*, not the prediction. RESULTS.md
predicts ~+0.5 Sharpe gain over a 3-year horizon. The honest test is OOS:

  At each rebalance date t:
    1. Compute weights from data[t-window : t]   (training)
    2. Hold those weights over data[t : t+rebalance_step]  (OOS)
    3. Record realized portfolio returns
  At the end:
    Stitch all OOS returns end-to-end → realized 3-year Sharpe per strategy.

Strategies compared:
  - eq           : equal-weight (baseline)
  - mv_uncon     : min-variance, no floor (often corner-solution to BTC)
  - mv_floor_05  : $5/pair floor (Martin lot-size realistic)
  - mv_floor_10  : $10/pair floor
  - clip_floor_10: RMT clipping + $10 floor (verifies cycle 80 finding at small N)

If mv_floor_10 beats eq by ≥ +0.3 Sharpe OOS over 3 years, RESULTS.md claim is
confirmed in the regime that matters (out-of-sample).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from rmt.data_loader import load_panel_returns
from rmt.martin_allocation import (
    allocate_capital,
    equal_weight_allocation,
    min_variance_allocation,
)


PAIRS = ["BTC", "ETH", "SOL", "LINK", "ADA"]
TOTAL_CAPITAL = 120.0
TF = "4h"
WINDOW = 360          # 60 days at 4h = 360 candles
REBALANCE_STEP = 42   # weekly rebalance = 7d × 6 candles/day
ANNUALIZE = 6 * 365   # 4h periods per year


def realized_sharpe(returns: pd.Series, ann: int = ANNUALIZE) -> float:
    if returns.std() <= 0 or len(returns) == 0:
        return 0.0
    return float(returns.mean() / returns.std() * np.sqrt(ann))


def max_drawdown(returns: pd.Series) -> float:
    """Max drawdown of cumulative log-return curve."""
    cum = returns.cumsum()
    peak = cum.cummax()
    dd = cum - peak
    return float(dd.min())


def walk_forward(
    rets: pd.DataFrame,
    strategy_fn,
    window: int = WINDOW,
    step: int = REBALANCE_STEP,
) -> pd.Series:
    """Apply strategy_fn(returns[t-window:t]) → weights, hold for `step` steps.

    strategy_fn: callable returning pd.Series(weights, index=pairs).
    Returns: pd.Series of OOS portfolio log-returns indexed by date.
    """
    n = len(rets)
    out_chunks = []
    t = window
    while t + step <= n:
        train = rets.iloc[t - window : t]
        weights = strategy_fn(train)
        # Hold over next `step` candles (OOS).
        oos = rets.iloc[t : t + step]
        port = (oos * weights.reindex(oos.columns).values).sum(axis=1)
        out_chunks.append(port)
        t += step
    return pd.concat(out_chunks) if out_chunks else pd.Series(dtype=float)


def eq_strategy(train: pd.DataFrame) -> pd.Series:
    n = train.shape[1]
    return pd.Series([1.0 / n] * n, index=train.columns)


def mv_uncon_strategy(train: pd.DataFrame) -> pd.Series:
    return min_variance_allocation(train, method="raw")


def make_floor_strategy(method: str, floor_usd: float, total: float):
    def fn(train: pd.DataFrame) -> pd.Series:
        alloc = allocate_capital(
            train, total_capital=total, method=method, min_capital_per_pair=floor_usd
        )
        return pd.Series(alloc) / total  # normalize to weights
    return fn


def main():
    print("=== Cycle 82 — Walk-forward OOS validation min-variance ===\n")
    print(f"Pairs: {PAIRS}")
    print(f"Total capital: ${TOTAL_CAPITAL}")
    print(f"TF: {TF}, window: {WINDOW} (60d), rebalance every {REBALANCE_STEP} (7d)")
    print()

    rets = load_panel_returns(PAIRS, tf=TF)
    print(f"Loaded {rets.shape[0]} {TF} candles, {rets.shape[1]} pairs")
    print(f"Range: {rets.index.min()} → {rets.index.max()}")
    n_rebal = (len(rets) - WINDOW) // REBALANCE_STEP
    print(f"Rebalances available: {n_rebal}")
    print()

    strategies = {
        "eq":            eq_strategy,
        "mv_uncon":      mv_uncon_strategy,
        "mv_floor_5":    make_floor_strategy("raw", 5.0, TOTAL_CAPITAL),
        "mv_floor_10":   make_floor_strategy("raw", 10.0, TOTAL_CAPITAL),
        "mv_floor_15":   make_floor_strategy("raw", 15.0, TOTAL_CAPITAL),
        "clip_floor_10": make_floor_strategy("clip", 10.0, TOTAL_CAPITAL),
    }

    results = {}
    for name, fn in strategies.items():
        oos = walk_forward(rets, fn, window=WINDOW, step=REBALANCE_STEP)
        sharpe = realized_sharpe(oos)
        cum = oos.sum()
        vol_ann = oos.std() * np.sqrt(ANNUALIZE)
        dd = max_drawdown(oos)
        results[name] = {
            "sharpe_oos": sharpe,
            "cum_log_return": cum,
            "vol_ann": float(vol_ann),
            "max_drawdown_log": dd,
            "n_periods": len(oos),
        }
        print(f"{name:14s}  Sharpe={sharpe:+.3f}  cumLogRet={cum:+.4f}  "
              f"volAnn={vol_ann:.2%}  maxDD={dd:.4f}  n={len(oos)}")
    print()

    sh_eq = results["eq"]["sharpe_oos"]
    print("=== Δ Sharpe vs equal-weight (OOS, 3y) ===")
    for name, r in results.items():
        if name == "eq":
            continue
        delta = r["sharpe_oos"] - sh_eq
        verdict = "PROMISE HELD" if name == "mv_floor_10" and delta >= 0.3 else ""
        print(f"  {name:14s}  Δ={delta:+.3f}  {verdict}")
    print()

    # --- Save CSV ---
    out_csv = Path(__file__).parent / "walk_forward_martin_alloc_cycle82_results.csv"
    df = pd.DataFrame(results).T
    df.index.name = "strategy"
    df.to_csv(out_csv)
    print(f"Wrote {out_csv}")

    # --- Stability: average weights over the walk-forward path ---
    print("\n=== Average weights over walk-forward path ===")
    all_weights = []
    t = WINDOW
    while t + REBALANCE_STEP <= len(rets):
        train = rets.iloc[t - WINDOW : t]
        w = make_floor_strategy("raw", 10.0, TOTAL_CAPITAL)(train)
        all_weights.append(w)
        t += REBALANCE_STEP
    avg_w = pd.DataFrame(all_weights).mean()
    std_w = pd.DataFrame(all_weights).std()
    print(f"mv_floor_10 average weight (±std) over {len(all_weights)} rebalances:")
    for p in PAIRS:
        print(f"  {p}: {avg_w[p]:.1%} ± {std_w[p]:.1%}")


if __name__ == "__main__":
    main()

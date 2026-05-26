"""Cycle 85 — Walk-forward OOS on Martin's REAL deployable universe (3 pairs).

Cycle 82 ran on 5 pairs BTC+ETH+SOL+LINK+ADA — but BTC absorbed 57.7% weight,
which is the cycle 82 finding. The Martin live universe is now LINK + ADA + ETH
(after DOT removal cycle 84). The honest question: does min-variance still beat
equal-weight on the SMALLER universe Martin will actually trade?

If yes → reco cycle 82 transfers to Martin live.
If no → BTC anchor was load-bearing, reco must be tempered.

Walk-forward design identical to cycle 82:
  - 4h candles, 60d window (360 candles), weekly rebalance (42 candles)
  - 3-year horizon (2023-01 → 2026-01)
  - Strategies: eq, mv_uncon, mv_floor_05, mv_floor_10, mv_floor_15, clip_floor_10
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
    min_variance_allocation,
)


PAIRS = ["LINK", "ADA", "ETH"]
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


def walk_forward(
    rets: pd.DataFrame,
    strategy_fn,
    window: int = WINDOW,
    step: int = REBALANCE_STEP,
) -> pd.Series:
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
        return pd.Series(alloc) / total
    return fn


def main():
    print("=== Cycle 85 — Walk-forward OOS on REAL Martin universe (3 pairs) ===\n")
    print(f"Pairs: {PAIRS} (Martin live universe after DOT removal cycle 84)")
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
    dd_eq = results["eq"]["max_drawdown_log"]
    print("=== Δ Sharpe vs equal-weight (OOS, 3y) ===")
    for name, r in results.items():
        if name == "eq":
            continue
        delta = r["sharpe_oos"] - sh_eq
        dd_ratio = r["max_drawdown_log"] / dd_eq if dd_eq != 0 else float("nan")
        verdict = "PROMISE HELD" if name == "mv_floor_10" and delta >= 0.3 else ""
        print(f"  {name:14s}  ΔSharpe={delta:+.3f}  DDratio={dd_ratio:.2f}  {verdict}")
    print()

    out_csv = Path(__file__).parent / "walk_forward_martin_alloc_cycle85_results.csv"
    df = pd.DataFrame(results).T
    df.index.name = "strategy"
    df.to_csv(out_csv)
    print(f"Wrote {out_csv}")

    print("\n=== Average weights mv_floor_10 over walk-forward path ===")
    all_weights = []
    t = WINDOW
    while t + REBALANCE_STEP <= len(rets):
        train = rets.iloc[t - WINDOW : t]
        w = make_floor_strategy("raw", 10.0, TOTAL_CAPITAL)(train)
        all_weights.append(w)
        t += REBALANCE_STEP
    avg_w = pd.DataFrame(all_weights).mean()
    std_w = pd.DataFrame(all_weights).std()
    print(f"Average weight (±std) over {len(all_weights)} rebalances:")
    for p in PAIRS:
        print(f"  {p}: {avg_w[p]:.1%} ± {std_w[p]:.1%}")

    print("\n=== Comparison vs cycle 82 (5-pair universe with BTC) ===")
    try:
        c82 = pd.read_csv(
            Path(__file__).parent / "walk_forward_martin_alloc_cycle82_results.csv",
            index_col="strategy",
        )
        print(f"{'strategy':14s}  {'c85 Sharpe':>11s}  {'c82 Sharpe':>11s}  {'Δ':>7s}")
        for name in results:
            c85 = results[name]["sharpe_oos"]
            c82_val = c82.loc[name, "sharpe_oos"] if name in c82.index else float("nan")
            d = c85 - c82_val if not pd.isna(c82_val) else float("nan")
            print(f"{name:14s}  {c85:+11.3f}  {c82_val:+11.3f}  {d:+7.3f}")
    except FileNotFoundError:
        print("  (cycle 82 results CSV not found, skipping comparison)")


if __name__ == "__main__":
    main()

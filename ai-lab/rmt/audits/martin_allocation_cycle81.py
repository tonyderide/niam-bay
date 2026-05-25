"""Cycle 81 — empirical validation of min-variance allocation for Martin.

Uses the 5 canonical Martin pairs (BTC/ETH/SOL/LINK/ADA), 4h candles, last
60 days, and compares equal-weight vs min-variance capital allocation.

Output: weights, allocated USD per pair, realized 60d Sharpe of each
portfolio if those weights had been held over the lookback period.

This is an in-sample sanity check, NOT a walk-forward backtest. The point
is to verify that the new `martin_allocation` module produces sensible
weights on real Martin universe data and that the Sharpe improvement
predicted by RESULTS.md (~+0.5) is visible at the small N=5 case.
"""

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


# Martin universe (canonical 5)
PAIRS = ["BTC", "ETH", "SOL", "LINK", "ADA"]
TOTAL_CAPITAL = 120.0  # ~ current Martin portfolio
WINDOW_4H = 360  # 60 days at 4h candles
ANNUALIZE_4H = 6 * 365  # 4h periods per year


def realized_sharpe(rets: pd.DataFrame, weights: pd.Series, ann: int) -> float:
    """Compute annualized Sharpe of weighted-portfolio returns over `rets`."""
    port = (rets * weights.values).sum(axis=1)
    if port.std() <= 0:
        return 0.0
    return float(port.mean() / port.std() * np.sqrt(ann))


def main():
    print("=== Cycle 81 — Min-variance allocation, real Martin universe ===\n")

    df = load_panel_returns(PAIRS, tf="4h")
    print(f"Loaded {df.shape[0]} 4h candles, {df.shape[1]} pairs")
    print(f"Range: {df.index.min()} → {df.index.max()}\n")

    # Use last 60 days only for both estimation and realized check (in-sample).
    recent = df.tail(WINDOW_4H)
    print(f"Recent window: {recent.shape[0]} candles (last 60d)\n")

    # --- Vol & correlation snapshot ---
    print("Annualized vol per pair (last 60d):")
    for p in PAIRS:
        vol = recent[p].std() * np.sqrt(ANNUALIZE_4H)
        print(f"  {p}: {vol:.2%}")
    print()
    print("Correlation matrix (last 60d):")
    print(recent.corr().round(3))
    print()

    # --- Equal-weight baseline ---
    eq = equal_weight_allocation(PAIRS, TOTAL_CAPITAL)
    eq_weights = pd.Series({p: 1.0 / len(PAIRS) for p in PAIRS})
    print("Equal-weight allocation ($120 total):")
    for p, c in eq.items():
        print(f"  {p}: ${c:.2f} ({eq_weights[p]:.1%})")
    sh_eq = realized_sharpe(recent, eq_weights, ANNUALIZE_4H)
    print(f"  → in-sample Sharpe (last 60d): {sh_eq:.3f}\n")

    # --- Min-variance allocation (raw, unconstrained) ---
    mv_weights = min_variance_allocation(recent, method="raw")
    mv_alloc = allocate_capital(recent, TOTAL_CAPITAL, method="raw")
    print("Min-variance allocation (raw, unconstrained, $120 total):")
    for p in PAIRS:
        print(f"  {p}: ${mv_alloc[p]:.2f} ({mv_weights[p]:.1%})")
    sh_mv = realized_sharpe(recent, mv_weights, ANNUALIZE_4H)
    print(f"  → in-sample Sharpe (last 60d): {sh_mv:.3f}\n")

    # --- Min-variance with $10 floor per pair (Martin-realistic) ---
    floor = 10.0
    mv_alloc_floor = allocate_capital(
        recent, TOTAL_CAPITAL, method="raw", min_capital_per_pair=floor
    )
    weights_floor = pd.Series(
        {p: mv_alloc_floor[p] / TOTAL_CAPITAL for p in PAIRS}
    )
    print(
        f"Min-variance with min ${floor}/pair floor (Martin-deployable):"
    )
    for p in PAIRS:
        print(
            f"  {p}: ${mv_alloc_floor[p]:.2f} ({weights_floor[p]:.1%})"
        )
    sh_floor = realized_sharpe(recent, weights_floor, ANNUALIZE_4H)
    print(f"  → in-sample Sharpe (last 60d): {sh_floor:.3f}\n")

    # --- Clip (RMT) for comparison ---
    clip_weights = min_variance_allocation(recent, method="clip")
    sh_clip = realized_sharpe(recent, clip_weights, ANNUALIZE_4H)

    # --- Summary ---
    print("=== Summary ===")
    print(f"  Sharpe eq:                  {sh_eq:.3f}")
    print(f"  Sharpe mv (unconstrained):  {sh_mv:.3f}  (Δ vs eq = {sh_mv - sh_eq:+.3f})")
    print(f"  Sharpe mv (${floor}/pair floor): {sh_floor:.3f}  (Δ vs eq = {sh_floor - sh_eq:+.3f})")
    print(f"  Sharpe clip:                {sh_clip:.3f}  (Δ vs raw mv = {sh_clip - sh_mv:+.3f})")
    print()
    print("Allocation diff ($) vs equal-weight:")
    for p in PAIRS:
        delta = mv_alloc[p] - eq[p]
        print(f"  {p}: {delta:+.2f}")
    print()

    # Save CSV for reproducibility
    out_csv = Path(__file__).parent / "martin_allocation_cycle81_results.csv"
    rows = []
    for p in PAIRS:
        rows.append(
            {
                "pair": p,
                "vol_60d_ann": recent[p].std() * np.sqrt(ANNUALIZE_4H),
                "weight_eq": eq_weights[p],
                "weight_mv": mv_weights[p],
                "capital_eq": eq[p],
                "capital_mv": mv_alloc[p],
            }
        )
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}")


if __name__ == "__main__":
    main()

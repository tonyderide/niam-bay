"""Min-variance capital allocation for Martin grids.

Wraps the existing RMT min-variance optimizer in a Martin-friendly interface:
takes a returns DataFrame of N active pairs + a total USD capital, returns a
dict mapping each pair to its allocated USD capital.

Per RESULTS.md cycle 79 (Task 7+8): min-variance Markowitz with raw sample
covariance beats equal-weight by ~0.5+ Sharpe across all tested windows. At
N=7-8 (current Martin universe), RMT cleaning (clip/lp) adds zero value and
can hurt (cycle 80: lp -0.039 Sharpe systematic). Default method here is
"raw" — the empirically validated optimum for small N.

Usage:
    weights = min_variance_allocation(returns_df, method="raw")
    capital = allocate_capital(returns_df, total_capital=120.0)
    # capital = {"PF_LINKUSD": 38.5, "PF_DOTUSD": 42.1, ...}

This module does NOT touch Martin VM or deploy anything. It is a pure-function
interface ready to be wired into Martin's allocator at a later point.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from rmt.backtest import _cov_from_returns, min_variance_weights


def min_variance_allocation(
    returns: pd.DataFrame,
    method: str = "raw",
    window: int | None = None,
) -> pd.Series:
    """Compute min-variance long-only weights for the columns of `returns`.

    Args:
        returns: DataFrame (T, N) of periodic returns, one column per pair.
            Column names are preserved on the output Series.
        method: covariance estimator. One of "raw" (default, recommended for
            N<30), "clip" (Marchenko-Pastur, useful at N≥30), "lp"
            (Ledoit-Péché, useful at N≥50). At small N, "raw" is the
            empirically validated optimum (cycle 79+80 findings).
        window: if set, restrict the covariance estimate to the last `window`
            rows of `returns`. RESULTS.md recommends 1440 (60d at 1h candles).

    Returns:
        Series of weights indexed by `returns.columns`, summing to 1.0, all
        entries in [0, 1].

    Raises:
        ValueError: if returns has fewer than 2 rows, or contains NaN.
    """
    if returns.isna().any().any():
        raise ValueError("returns contains NaN; align/clean before passing in")
    if window is not None:
        returns = returns.tail(window)
    if len(returns) < 2:
        raise ValueError(f"need at least 2 observations, got {len(returns)}")
    cov = _cov_from_returns(returns.values, method)
    w = min_variance_weights(cov)
    return pd.Series(w, index=returns.columns, name="weight")


def allocate_capital(
    returns: pd.DataFrame,
    total_capital: float,
    method: str = "raw",
    window: int | None = None,
    min_capital_per_pair: float = 0.0,
) -> dict[str, float]:
    """Allocate USD capital across active pairs by min-variance weights.

    Args:
        returns: DataFrame (T, N) of periodic returns.
        total_capital: total USD to distribute.
        method: covariance estimator (see `min_variance_allocation`).
        window: lookback restriction (see `min_variance_allocation`).
        min_capital_per_pair: if > 0, every pair receives at least this much
            USD and the remaining `total_capital - N * min_capital_per_pair`
            is split by min-variance weights. Useful to guarantee grids are
            actually deployable (Kraken Futures lot-size floor).

    Returns:
        dict mapping pair name → USD capital. Sum equals `total_capital`
        (modulo float rounding < 1e-9).

    Raises:
        ValueError: if `min_capital_per_pair * N > total_capital`.
    """
    weights = min_variance_allocation(returns, method=method, window=window)
    N = len(weights)
    floor = N * min_capital_per_pair
    if floor > total_capital + 1e-9:
        raise ValueError(
            f"min_capital_per_pair={min_capital_per_pair} × N={N} = {floor} "
            f"exceeds total_capital={total_capital}"
        )
    free = total_capital - floor
    alloc = {
        pair: float(min_capital_per_pair + w * free)
        for pair, w in weights.items()
    }
    return alloc


def equal_weight_allocation(
    pairs: list[str], total_capital: float
) -> dict[str, float]:
    """Baseline for comparison: split capital equally across pairs.

    Args:
        pairs: list of pair names.
        total_capital: total USD to distribute.

    Returns:
        dict mapping pair → total_capital / len(pairs).
    """
    if not pairs:
        return {}
    per_pair = total_capital / len(pairs)
    return {p: per_pair for p in pairs}

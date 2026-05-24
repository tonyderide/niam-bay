"""Walk-forward Markowitz backtest with 4 covariance estimators.

Methods:
- eq:   equal-weight 1/N (no covariance needed)
- raw:  sample covariance (np.cov), no cleaning
- clip: Marchenko-Pastur eigenvalue clipping (Laloux 1999)
- lp:   Ledoit-Péché optimal nonlinear shrinkage
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from rmt.cleaning import clip_mp, shrink_lp


def min_variance_weights(cov: np.ndarray) -> np.ndarray:
    """Min-variance long-only weights subject to sum(w)=1, w_i in [0,1].

    Uses scipy.optimize.minimize SLSQP. Returns equal-weight on optimizer failure (fallback).

    Args:
        cov: NxN positive (semi)definite covariance matrix.

    Returns:
        1-D array of length N summing to 1 with all entries in [0, 1].
    """
    N = cov.shape[0]
    w0 = np.full(N, 1.0 / N)
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    bounds = [(0.0, 1.0)] * N
    res = minimize(
        lambda w: w @ cov @ w,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=cons,
        options={"ftol": 1e-10, "maxiter": 200},
    )
    if not res.success:
        return w0
    return res.x


def _cov_from_returns(rets: np.ndarray, method: str) -> np.ndarray:
    """Estimate covariance under one of: raw, clip, lp, eq.

    eq returns sample covariance as a sentinel (weights will be equal anyway).

    Args:
        rets: (T, N) array of returns.
        method: one of "raw", "clip", "lp", "eq".

    Returns:
        NxN covariance matrix.

    Raises:
        ValueError: if fewer than 2 observations or unknown method.
    """
    if rets.shape[0] < 2:
        raise ValueError("need at least 2 observations")
    cov_sample = np.cov(rets.T, ddof=1)
    if method in ("raw", "eq"):
        return cov_sample
    stds = np.sqrt(np.diag(cov_sample))
    # Avoid div-by-zero on degenerate columns
    stds = np.where(stds > 1e-12, stds, 1e-12)
    corr = cov_sample / np.outer(stds, stds)
    np.fill_diagonal(corr, 1.0)
    N, T = rets.shape[1], rets.shape[0]
    c = N / T
    if method == "clip":
        corr_clean = clip_mp(corr, c=c)
    elif method == "lp":
        corr_clean = shrink_lp(corr, c=c)
    else:
        raise ValueError(f"unknown method: {method}")
    return corr_clean * np.outer(stds, stds)


def walk_forward(
    returns: pd.DataFrame, window: int, rebalance_freq: int = 24
) -> dict[str, pd.Series]:
    """Walk-forward backtest of 4 portfolio methods: eq, raw, clip, lp.

    At each rebalance date t:
      - train on returns[t-window : t]
      - compute weights per method
      - apply weights to next rebalance_freq periods (out-of-sample)

    Args:
        returns: (T, N) DataFrame of period returns indexed by timestamp.
        window:  number of in-sample periods for covariance estimation.
        rebalance_freq: number of out-of-sample periods between rebalances.

    Returns:
        dict mapping method_name → Series of portfolio returns indexed by timestamp.
    """
    methods = ["eq", "raw", "clip", "lp"]
    out: dict[str, list[tuple]] = {m: [] for m in methods}
    n_periods, N = returns.shape

    for t in range(window, n_periods, rebalance_freq):
        train = returns.iloc[t - window : t].values
        for method in methods:
            if method == "eq":
                w = np.full(N, 1.0 / N)
            else:
                cov = _cov_from_returns(train, method)
                w = min_variance_weights(cov)
            future_idx_end = min(t + rebalance_freq, n_periods)
            for k in range(t, future_idx_end):
                r_t = returns.iloc[k].values
                port_ret = float(w @ r_t)
                out[method].append((returns.index[k], port_ret))

    result = {}
    for method, rows in out.items():
        if rows:
            ts, vals = zip(*rows)
            result[method] = pd.Series(vals, index=pd.DatetimeIndex(ts))
        else:
            result[method] = pd.Series(dtype=float)
    return result


def summary_stats(pnl: pd.Series, periods_per_year: int = 24 * 365) -> dict:
    """Compute annualized Sharpe, max drawdown, total return, n_periods.

    Args:
        pnl: Series of period returns.
        periods_per_year: annualization factor (default 24*365 for hourly crypto).

    Returns:
        dict with keys: sharpe, max_dd, total_return, n_periods.
    """
    if len(pnl) == 0:
        return {"sharpe": 0.0, "max_dd": 0.0, "total_return": 0.0, "n_periods": 0}
    mean = pnl.mean() * periods_per_year
    vol = pnl.std() * np.sqrt(periods_per_year)
    sharpe = float(mean / vol) if vol > 0 else 0.0
    cumret = (1 + pnl).cumprod()
    peak = cumret.cummax()
    dd = (cumret - peak) / peak
    return {
        "sharpe": sharpe,
        "max_dd": float(dd.min()),
        "total_return": float(cumret.iloc[-1] - 1),
        "n_periods": len(pnl),
    }

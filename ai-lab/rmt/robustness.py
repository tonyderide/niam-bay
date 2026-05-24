"""Sensitivity analysis: how Sharpe of each method varies with training window."""
import pandas as pd
from rmt.backtest import walk_forward, summary_stats


def sweep_window(
    returns: pd.DataFrame,
    windows: list[int],
    rebalance: int,
    periods_per_year: int,
) -> pd.DataFrame:
    """Return DataFrame with one row per (window, method) and columns sharpe/max_dd/total_return."""
    rows = []
    for w in windows:
        pnls = walk_forward(returns, window=w, rebalance_freq=rebalance)
        for method, pnl in pnls.items():
            s = summary_stats(pnl, periods_per_year=periods_per_year)
            rows.append({
                "window": w,
                "method": method,
                "sharpe": s["sharpe"],
                "max_dd": s["max_dd"],
                "total_return": s["total_return"],
                "n_periods": s["n_periods"],
            })
    return pd.DataFrame(rows)

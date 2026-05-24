import numpy as np
import pandas as pd
import pytest

from rmt.backtest import min_variance_weights, walk_forward, summary_stats


def test_min_variance_weights_long_only_sum_to_one():
    np.random.seed(0)
    N = 4
    cov = np.eye(N) + 0.1 * np.ones((N, N))
    w = min_variance_weights(cov)
    assert w.shape == (N,)
    np.testing.assert_allclose(w.sum(), 1.0, atol=1e-9)
    assert (w >= -1e-10).all()


def test_walk_forward_returns_per_method():
    np.random.seed(0)
    T, N = 500, 4
    rets = pd.DataFrame(
        np.random.randn(T, N) * 0.01,
        columns=["BTC", "ETH", "SOL", "LINK"],
        index=pd.date_range("2025-01-01", periods=T, freq="1h"),
    )
    result = walk_forward(rets, window=100, rebalance_freq=24)
    assert set(result.keys()) >= {"eq", "raw", "clip", "lp"}
    for method, s in result.items():
        assert isinstance(s, pd.Series)
        assert len(s) > 0


def test_summary_stats_basic():
    pnl = pd.Series([0.01, -0.005, 0.02, 0.001, -0.01])
    s = summary_stats(pnl, periods_per_year=252)
    assert "sharpe" in s
    assert "max_dd" in s
    assert "total_return" in s
    assert s["n_periods"] == 5

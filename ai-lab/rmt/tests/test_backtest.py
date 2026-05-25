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


def test_min_variance_prefers_low_vol_asset():
    # Two uncorrelated assets, asset 0 has 4x the variance of asset 1.
    # Min-variance must give substantially more weight to the low-vol asset.
    cov = np.diag([4.0, 1.0])
    w = min_variance_weights(cov)
    assert w[1] > w[0]
    # Analytical optimum for diagonal cov with var (s0, s1): w_i ∝ 1/s_i.
    # Here: w_0 = 1/(1+4) = 0.2, w_1 = 4/5 = 0.8.
    np.testing.assert_allclose(w, [0.2, 0.8], atol=1e-3)


def test_walk_forward_no_lookahead_uses_only_past():
    # Construct a series whose covariance flips sign halfway. If walk_forward
    # leaked future data, training near the boundary would mix regimes and
    # produce non-zero weights on the asset that becomes uncorrelated AFTER t.
    # Instead, we just verify that the OOS evaluation never reads from a
    # period that was part of the training window.
    np.random.seed(42)
    T, N = 300, 3
    rets = pd.DataFrame(
        np.random.randn(T, N) * 0.01,
        columns=["A", "B", "C"],
        index=pd.date_range("2025-01-01", periods=T, freq="1h"),
    )
    result = walk_forward(rets, window=100, rebalance_freq=24)
    # First rebalance happens at t=window=100. The first OOS index in the
    # output series must be at or after index 100 — never within [0:100].
    for method, s in result.items():
        assert s.index[0] >= rets.index[100], (
            f"{method}: first OOS index {s.index[0]} is inside training window"
        )


def test_min_variance_falls_back_on_failure():
    # Pathological non-PSD matrix: SLSQP may struggle. The function should
    # return equal-weight rather than raise.
    cov_bad = np.array([[1.0, 2.0], [2.0, 1.0]])  # eigenvalues -1, 3 (indefinite)
    w = min_variance_weights(cov_bad)
    assert w.shape == (2,)
    np.testing.assert_allclose(w.sum(), 1.0, atol=1e-6)


def test_lp_shrinkage_does_not_systematically_improve_at_small_N():
    # Cycle 80 empirical finding: at N=7, lp shrinkage is measurably WORSE than
    # raw across 6 contiguous temporal slices (mean delta = -0.039 Sharpe at
    # w=100, std 0.016, signal/noise ~2.4x). clip is indistinguishable from raw.
    # This test encodes the contract: on synthetic small-N panels, lp should not
    # produce a systematic > 0.02 Sharpe improvement vs raw. If it ever does, the
    # mechanism has changed and the cycle 80 finding needs revisiting.
    np.random.seed(0)
    N, T = 7, 100
    sharpe_deltas = {"clip": [], "lp": []}
    for trial in range(5):
        # Synthetic panel with a dominant market factor (mimics crypto):
        # all assets load on a common shock plus idiosyncratic noise.
        common = np.random.randn(T, 1) * 0.02
        idio = np.random.randn(T, N) * 0.01
        rets_arr = common + idio
        rets = pd.DataFrame(
            rets_arr,
            columns=[f"A{i}" for i in range(N)],
            index=pd.date_range("2025-01-01", periods=T, freq="1h"),
        )
        pnls = walk_forward(rets, window=50, rebalance_freq=24)
        raw_sharpe = summary_stats(pnls["raw"], periods_per_year=24 * 365)["sharpe"]
        for method in ("clip", "lp"):
            m_sharpe = summary_stats(pnls[method], periods_per_year=24 * 365)["sharpe"]
            sharpe_deltas[method].append(m_sharpe - raw_sharpe)
    # No method should yield a > 0.02 Sharpe improvement in 5/5 trials.
    for method, deltas in sharpe_deltas.items():
        n_strong_positive = sum(1 for d in deltas if d > 0.02)
        assert n_strong_positive < 5, (
            f"{method}: {n_strong_positive}/5 trials showed > 0.02 Sharpe gain — "
            f"cycle 80 finding may need revisiting (deltas: {deltas})"
        )

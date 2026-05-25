"""Behavioral tests for the Martin allocation wrapper.

These tests pin the contracts of `min_variance_allocation` and
`allocate_capital`. They are NOT performance tests — backtest comparisons
live in `tests/test_backtest.py`. The point here is interface stability
and edge-case behavior.
"""

import numpy as np
import pandas as pd
import pytest

from rmt.martin_allocation import (
    allocate_capital,
    equal_weight_allocation,
    min_variance_allocation,
)


def _gen_returns(T: int, N: int, seed: int = 0, vols=None) -> pd.DataFrame:
    """Generate a synthetic returns DataFrame.

    Args:
        T: number of periods.
        N: number of assets.
        seed: numpy RNG seed.
        vols: optional length-N list of stds (default all 0.01).

    Returns:
        DataFrame indexed 1h, columns "P0".."P{N-1}".
    """
    rng = np.random.default_rng(seed)
    if vols is None:
        vols = [0.01] * N
    data = rng.standard_normal((T, N)) * np.asarray(vols)
    return pd.DataFrame(
        data,
        columns=[f"P{i}" for i in range(N)],
        index=pd.date_range("2025-01-01", periods=T, freq="1h"),
    )


def test_weights_sum_to_one_and_nonneg():
    rets = _gen_returns(T=500, N=4)
    w = min_variance_allocation(rets)
    assert isinstance(w, pd.Series)
    assert list(w.index) == ["P0", "P1", "P2", "P3"]
    np.testing.assert_allclose(w.sum(), 1.0, atol=1e-9)
    assert (w >= -1e-10).all()


def test_low_vol_pair_gets_more_weight():
    rets = _gen_returns(T=500, N=2, vols=[0.04, 0.01])  # P0 4x vol of P1
    w = min_variance_allocation(rets)
    assert w["P1"] > w["P0"]
    # Analytical inverse-variance: w_P1 ≈ 16/17, w_P0 ≈ 1/17 for diag cov
    # with 4x std. With finite-sample noise the bound is looser.
    assert w["P1"] > 0.8


def test_allocate_capital_sums_to_total():
    rets = _gen_returns(T=500, N=5)
    alloc = allocate_capital(rets, total_capital=120.0)
    assert set(alloc.keys()) == set(rets.columns)
    assert sum(alloc.values()) == pytest.approx(120.0, abs=1e-9)
    assert all(v >= 0 for v in alloc.values())


def test_allocate_capital_window_uses_recent_tail():
    """Capital allocation must change if recent regime differs from full sample."""
    T, N = 1000, 3
    rng = np.random.default_rng(42)
    # First half: P0 quiet (vol 0.005), second half: P0 explodes (vol 0.05)
    block1 = rng.standard_normal((T // 2, N)) * np.array([0.005, 0.01, 0.01])
    block2 = rng.standard_normal((T // 2, N)) * np.array([0.05, 0.01, 0.01])
    data = np.vstack([block1, block2])
    rets = pd.DataFrame(
        data,
        columns=["P0", "P1", "P2"],
        index=pd.date_range("2025-01-01", periods=T, freq="1h"),
    )
    alloc_full = allocate_capital(rets, total_capital=100.0)
    alloc_recent = allocate_capital(rets, total_capital=100.0, window=200)
    # Full-sample sees P0 with mixed vol → moderate weight.
    # Recent window sees P0 with high vol → low weight.
    assert alloc_recent["P0"] < alloc_full["P0"]


def test_min_capital_per_pair_respected():
    rets = _gen_returns(T=500, N=4)
    alloc = allocate_capital(
        rets, total_capital=120.0, min_capital_per_pair=10.0
    )
    assert all(v >= 10.0 - 1e-9 for v in alloc.values())
    assert sum(alloc.values()) == pytest.approx(120.0, abs=1e-9)


def test_min_capital_too_large_raises():
    rets = _gen_returns(T=500, N=4)
    with pytest.raises(ValueError, match="exceeds total_capital"):
        allocate_capital(rets, total_capital=30.0, min_capital_per_pair=10.0)


def test_nan_returns_rejected():
    rets = _gen_returns(T=100, N=3)
    rets.iloc[5, 1] = np.nan
    with pytest.raises(ValueError, match="NaN"):
        min_variance_allocation(rets)


def test_single_row_rejected():
    rets = _gen_returns(T=1, N=3)
    with pytest.raises(ValueError, match="at least 2"):
        min_variance_allocation(rets)


def test_equal_weight_allocation_baseline():
    alloc = equal_weight_allocation(["A", "B", "C"], total_capital=120.0)
    assert alloc == {"A": 40.0, "B": 40.0, "C": 40.0}


def test_equal_weight_allocation_empty():
    assert equal_weight_allocation([], total_capital=100.0) == {}


def test_method_raw_default_matches_explicit():
    """Sanity: default method='raw' should equal explicit raw."""
    rets = _gen_returns(T=500, N=4)
    w_default = min_variance_allocation(rets)
    w_explicit = min_variance_allocation(rets, method="raw")
    np.testing.assert_array_equal(w_default.values, w_explicit.values)


def test_method_clip_indistinguishable_from_raw_at_small_N():
    """At N=7, T=720 (c=N/T=0.01), clip ≈ raw per RESULTS.md.

    Confirms the empirical finding: don't bother with RMT cleaning at this
    pair count. Output should match within tight tolerance.
    """
    rng = np.random.default_rng(7)
    T, N = 720, 7
    rets = pd.DataFrame(
        rng.standard_normal((T, N)) * 0.01,
        columns=[f"P{i}" for i in range(N)],
        index=pd.date_range("2024-01-01", periods=T, freq="1h"),
    )
    w_raw = min_variance_allocation(rets, method="raw")
    w_clip = min_variance_allocation(rets, method="clip")
    # At c=0.01 the MP bulk is degenerate; clip should collapse to raw.
    np.testing.assert_allclose(w_raw.values, w_clip.values, atol=1e-6)


def test_realistic_5_pair_universe_smoke():
    """End-to-end smoke: 5 Martin-like pairs, 30d hourly, 120 USD capital."""
    rng = np.random.default_rng(123)
    T = 720  # 30 days at 1h
    pairs = ["PF_XBTUSD", "PF_ETHUSD", "PF_LINKUSD", "PF_DOTUSD", "PF_ADAUSD"]
    # Crypto-like vols: BTC quieter than alts
    vols = [0.008, 0.012, 0.020, 0.022, 0.025]
    rets = pd.DataFrame(
        rng.standard_normal((T, len(pairs))) * np.asarray(vols),
        columns=pairs,
        index=pd.date_range("2025-12-01", periods=T, freq="1h"),
    )
    alloc = allocate_capital(rets, total_capital=120.0, window=720)
    # BTC (lowest vol) should get the largest slice on min-variance.
    assert alloc["PF_XBTUSD"] == max(alloc.values())
    # Highest-vol pair (ADA) should get less than equal-weight share.
    assert alloc["PF_ADAUSD"] < 120.0 / 5
    # Sum check.
    assert sum(alloc.values()) == pytest.approx(120.0, abs=1e-9)

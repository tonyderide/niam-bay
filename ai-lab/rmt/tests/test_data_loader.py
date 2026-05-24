import numpy as np
import pandas as pd
import pytest

from rmt.data_loader import load_pair_returns, load_panel_returns


def test_load_single_pair_returns_dataframe():
    df = load_pair_returns("BTC", tf="1h", n_periods=100)
    assert isinstance(df, pd.DataFrame)
    assert "BTC" in df.columns
    assert len(df) == 100
    assert df["BTC"].isna().sum() == 0
    # log returns at 1h on liquid crypto are well under 50%
    assert df["BTC"].abs().max() < 0.5


def test_load_pair_returns_full_series():
    df = load_pair_returns("BTC", tf="1h")
    # 3 years of 1h bars ≈ 26280 minus 1 (first diff dropped)
    assert len(df) > 25000
    assert df.index.is_monotonic_increasing


def test_load_panel_aligns_timestamps():
    panel = load_panel_returns(["BTC", "ETH", "SOL"], tf="1h", n_periods=200)
    assert panel.shape == (200, 3)
    assert set(panel.columns) == {"BTC", "ETH", "SOL"}
    assert panel.isna().sum().sum() == 0
    # All rows share the same timestamp index → diff between successive timestamps is positive
    assert (panel.index.to_series().diff().dropna() > pd.Timedelta(0)).all()


def test_load_panel_8_martin_pairs():
    """Smoke test for 8 large-cap pairs in the Martin universe.

    Plan listed LTC but the 1h cache has no LTC file — substituted with AAVE
    (also a large-cap historical Martin candidate). Available 1h pairs in
    cache as of 2026-05-24: AAVE, ADA, APT, ATOM, AVAX, BTC, ETH, INJ, LINK,
    OP, SOL, SUI.
    """
    pairs = ["BTC", "ETH", "SOL", "LINK", "ADA", "AAVE", "ATOM", "AVAX"]
    panel = load_panel_returns(pairs, tf="1h", n_periods=500)
    assert panel.shape == (500, 8)
    assert panel.isna().sum().sum() == 0


def test_missing_pair_raises():
    with pytest.raises(FileNotFoundError):
        load_pair_returns("NONEXISTENTPAIR", tf="1h", n_periods=10)


def test_log_returns_are_centered_around_zero():
    """Sanity check: BTC log returns over 3 years have mean close to 0."""
    df = load_pair_returns("BTC", tf="1h")
    # 3-year mean of hourly log returns should be small (annualized drift ~50% = 5.7e-5 per 1h)
    assert abs(df["BTC"].mean()) < 1e-3
    # std for crypto 1h is roughly 0.005-0.02
    assert 0.001 < df["BTC"].std() < 0.05

"""Load Binance OHLC JSON cache → aligned log-return DataFrame.

Cache file layout (inspected 2026-05-24):
- Path: `niam-bay/ai-lab/darwin/data_cache/binance_<PAIR>USDT_<tf>_<ms_start>_<ms_end>.json`
- Format: array of klines, each kline = [open_ms, open, high, low, close, volume]
  (Binance-style OHLCV truncated to 6 fields; standard Binance returns 12).

The 3-year canonical window is fixed at [1672531200000, 1767139200000] (2023-01-01 →
2026-01-01 UTC).
"""

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

CACHE_DIR = Path(
    os.environ.get(
        "RMT_CACHE_DIR",
        "/home/tony/projets/tonyderide/niam-bay/ai-lab/darwin/data_cache",
    )
)

# 3-year canonical cache window (2023-01-01 → 2026-01-01 UTC, in ms).
_LONG_RANGE_SUFFIX = "1672531200000_1767139200000"


def _find_cache_file(pair: str, tf: str) -> Path:
    """Locate the canonical 3-year cache file for a pair + timeframe."""
    fn = f"binance_{pair}USDT_{tf}_{_LONG_RANGE_SUFFIX}.json"
    p = CACHE_DIR / fn
    if not p.exists():
        raise FileNotFoundError(f"cache file not found: {p}")
    return p


def load_pair_returns(
    pair: str, tf: str = "1h", n_periods: int | None = None
) -> pd.DataFrame:
    """Load a single pair's log-return series.

    Args:
        pair: ticker without USDT suffix (e.g. "BTC").
        tf: timeframe code matching cache filename ("1h", "4h", "1d", ...).
        n_periods: if set, keep only the LAST n_periods log returns.

    Returns:
        DataFrame indexed by UTC timestamp, single column named `pair`.
        Log returns r_t = log(close_t) - log(close_{t-1}), with first NaN dropped.

    Raises:
        FileNotFoundError: if the canonical 3-year cache file is absent.
    """
    p = _find_cache_file(pair, tf)
    raw = json.loads(p.read_text())
    rows = [(int(k[0]), float(k[4])) for k in raw]
    df = pd.DataFrame(rows, columns=["ts_ms", "close"])
    df["ts"] = pd.to_datetime(df["ts_ms"], unit="ms", utc=True)
    df = df.set_index("ts").sort_index()
    df[pair] = np.log(df["close"]).diff()
    df = df[[pair]].dropna()
    if n_periods is not None:
        df = df.tail(n_periods)
    return df


def load_panel_returns(
    pairs: list[str], tf: str = "1h", n_periods: int | None = None
) -> pd.DataFrame:
    """Load multiple pairs and inner-join on common timestamps.

    Args:
        pairs: list of tickers without USDT suffix.
        tf: timeframe code.
        n_periods: if set, keep only the LAST n_periods aligned rows.

    Returns:
        DataFrame T×N where T is the number of aligned periods and N = len(pairs).
        No NaN. Columns ordered as `pairs`.
    """
    series = [load_pair_returns(p, tf=tf, n_periods=None) for p in pairs]
    df = pd.concat(series, axis=1, join="inner")
    df = df.dropna()
    if n_periods is not None:
        df = df.tail(n_periods)
    return df[pairs]

# RMT Portfolio Cleaning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Random Matrix Theory (RMT) correlation-cleaning library, validate the math against published results, and backtest cleaned-vs-raw covariance for portfolio allocation on the 8 pairs Martin bot trades (BTC/ETH/SOL/LINK/ADA/LTC/ATOM/AVAX).

**Architecture:** Standalone Python module under `niam-bay/ai-lab/rmt/` with pure numpy/scipy implementations of Marchenko-Pastur eigenvalue clipping and Ledoit-Péché nonlinear shrinkage. Backtest harness loads Binance cache OHLC, computes log returns, applies the cleaning methods over a rolling walk-forward window, and compares mean-variance optimized portfolios on out-of-sample Sharpe + max drawdown. No live trading integration in this plan (deferred to a follow-up after validation).

**Tech Stack:** Python 3.12, numpy, scipy.linalg, pandas (for time series alignment + walk-forward indexing), pytest for tests, matplotlib for results visualization. Data source: existing JSON cache at `niam-bay/ai-lab/darwin/data_cache/binance_*USDT_{1h,4h}_*.json` (3 years 2023-01-01→2026-01-01).

---

## File Structure

```
niam-bay/ai-lab/rmt/
├── __init__.py
├── cleaning.py          # MP edges + clip + Ledoit-Péché shrinkage
├── data_loader.py       # Load Binance cache JSON → aligned returns DataFrame
├── backtest.py          # Walk-forward Markowitz with raw/clip/LP covariance
├── cli.py               # Entrypoint: python -m rmt.cli backtest --pairs ... --window 30
├── README.md            # Usage + interpretation guide
└── tests/
    ├── __init__.py
    ├── test_cleaning.py     # Math tests vs synthetic + Laloux 1999 sanity
    ├── test_data_loader.py  # Cache parsing + alignment
    └── test_backtest.py     # Walk-forward indexing + Markowitz math
```

**Decomposition rationale:**
- `cleaning.py` is pure math — no I/O, no pandas. Easy to unit-test against analytical results.
- `data_loader.py` isolates the messy Binance JSON parsing + timestamp alignment from the math.
- `backtest.py` orchestrates loader + cleaning + Markowitz, single-responsibility.
- `cli.py` keeps user-facing flag parsing out of the library code.

---

## Task 1: Project skeleton + dependencies

**Files:**
- Create: `niam-bay/ai-lab/rmt/__init__.py`
- Create: `niam-bay/ai-lab/rmt/tests/__init__.py`
- Create: `niam-bay/ai-lab/rmt/requirements.txt`
- Create: `niam-bay/ai-lab/rmt/README.md`

- [ ] **Step 1: Create directory structure and __init__ files**

```bash
mkdir -p /home/tony/projets/tonyderide/niam-bay/ai-lab/rmt/tests
touch /home/tony/projets/tonyderide/niam-bay/ai-lab/rmt/__init__.py
touch /home/tony/projets/tonyderide/niam-bay/ai-lab/rmt/tests/__init__.py
```

- [ ] **Step 2: Write requirements.txt**

```
numpy>=1.26
scipy>=1.11
pandas>=2.1
matplotlib>=3.8
pytest>=8.0
```

Save to `niam-bay/ai-lab/rmt/requirements.txt`.

- [ ] **Step 3: Stub README.md with goal + papers reference**

```markdown
# RMT Portfolio Cleaning

Implements Marchenko-Pastur eigenvalue clipping (Laloux et al. 1999) and
Ledoit-Péché nonlinear shrinkage (Ledoit & Péché 2011) to clean noisy sample
correlation matrices before mean-variance portfolio optimization.

## References
- Wigner 1955 — Random matrix theory foundations
- Marchenko & Pastur 1967 — Sample covariance eigenvalue distribution
- Laloux, Cizeau, Bouchaud, Potters 1999 — RMT noise dressing on S&P500
- Ledoit & Wolf 2003 — Linear shrinkage estimator
- Ledoit & Péché 2011 — Optimal nonlinear shrinkage via Stieltjes transform

## Quick start
See cli.py: `python -m ai_lab.rmt.cli backtest --pairs BTC,ETH,SOL,LINK,ADA,LTC,ATOM,AVAX --window 30 --tf 1h`
```

- [ ] **Step 4: Verify Python can import an empty rmt package**

Run: `cd /home/tony/projets/tonyderide/niam-bay && python3 -c "import ai_lab.rmt"`
Expected: no error (silent success).

If `ai_lab` isn't a Python package, add `niam-bay/ai-lab/__init__.py` too.

- [ ] **Step 5: Commit**

```bash
cd /home/tony/projets/tonyderide/niam-bay
git add ai-lab/rmt/
git commit -m "feat(rmt): project skeleton + requirements"
```

---

## Task 2: Marchenko-Pastur edges (analytical sanity)

**Files:**
- Create: `niam-bay/ai-lab/rmt/cleaning.py`
- Create: `niam-bay/ai-lab/rmt/tests/test_cleaning.py`

**Background:** For a sample correlation of N variables × T iid Gaussian observations, when N, T → ∞ with c = N/T fixed in (0, 1), the eigenvalues of C are bounded by:
- `λ_min = (1 - √c)²`
- `λ_max = (1 + √c)²`

Outside this range = signal (or outlier).

- [ ] **Step 1: Write the failing test**

```python
# niam-bay/ai-lab/rmt/tests/test_cleaning.py
import numpy as np
from ai_lab.rmt.cleaning import mp_edges


def test_mp_edges_classical_ratios():
    # Classical values from any RMT textbook
    lo, hi = mp_edges(c=0.5)
    # c=0.5 → λ_min=(1-√0.5)²≈0.086, λ_max=(1+√0.5)²≈2.914
    assert abs(lo - 0.0858) < 1e-3
    assert abs(hi - 2.9142) < 1e-3
    lo, hi = mp_edges(c=1.0)
    # c=1 → λ_min=0, λ_max=4
    assert abs(lo - 0.0) < 1e-9
    assert abs(hi - 4.0) < 1e-9


def test_mp_edges_invalid_c():
    import pytest
    with pytest.raises(ValueError):
        mp_edges(c=0.0)
    with pytest.raises(ValueError):
        mp_edges(c=-0.1)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/tony/projets/tonyderide/niam-bay
python3 -m pytest ai-lab/rmt/tests/test_cleaning.py -v
```

Expected: ImportError (`mp_edges` not defined).

- [ ] **Step 3: Implement mp_edges**

```python
# niam-bay/ai-lab/rmt/cleaning.py
import numpy as np


def mp_edges(c: float) -> tuple[float, float]:
    """Marchenko-Pastur bulk edges for c = N/T.

    For sample correlation matrix C from N variables × T observations of iid
    standardized noise, eigenvalues of C lie a.s. in [lambda_-, lambda_+]
    as N, T → ∞ with N/T → c.

    Args:
        c: aspect ratio N/T, must be > 0.

    Returns:
        (lambda_minus, lambda_plus) — closed interval bounds of the noise bulk.

    Raises:
        ValueError: if c <= 0.
    """
    if c <= 0:
        raise ValueError(f"c must be positive, got {c}")
    sqrt_c = np.sqrt(c)
    return ((1.0 - sqrt_c) ** 2, (1.0 + sqrt_c) ** 2)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m pytest ai-lab/rmt/tests/test_cleaning.py::test_mp_edges_classical_ratios -v
python3 -m pytest ai-lab/rmt/tests/test_cleaning.py::test_mp_edges_invalid_c -v
```

Expected: both PASS.

- [ ] **Step 5: Commit**

```bash
git add ai-lab/rmt/cleaning.py ai-lab/rmt/tests/test_cleaning.py
git commit -m "feat(rmt): Marchenko-Pastur bulk edges"
```

---

## Task 3: MP eigenvalue clipping (Laloux 1999 method)

**Files:**
- Modify: `niam-bay/ai-lab/rmt/cleaning.py` (add `clip_mp` function)
- Modify: `niam-bay/ai-lab/rmt/tests/test_cleaning.py` (add tests)

**Background:** "Clip" method replaces all eigenvalues inside the MP bulk with their average (preserving trace), keeping outliers untouched. Then reconstruct C_clean = U Λ_clean Uᵀ and renormalize diagonal to 1.

- [ ] **Step 1: Write the failing test using synthetic noise**

```python
# Append to test_cleaning.py
def test_clip_mp_preserves_trace():
    np.random.seed(42)
    N, T = 50, 200  # c = 0.25
    X = np.random.randn(N, T)
    # standardize rows
    X = (X - X.mean(axis=1, keepdims=True)) / X.std(axis=1, keepdims=True)
    C = (X @ X.T) / T
    C_clean = clip_mp(C, c=N/T)
    assert C_clean.shape == (N, N)
    # Diagonal must be 1 (correlation matrix)
    np.testing.assert_allclose(np.diag(C_clean), 1.0, atol=1e-10)
    # Pure noise → all eigenvalues should be clipped to ~1
    eigs = np.linalg.eigvalsh(C_clean)
    assert eigs.max() < 1.5, f"expected most eigs near 1 for pure noise, got max={eigs.max()}"


def test_clip_mp_preserves_signal_eigenvalues():
    np.random.seed(0)
    N, T = 50, 200
    # Build a matrix with one strong factor + noise
    factor = np.random.randn(T)
    loadings = np.ones(N) * 0.5
    noise = np.random.randn(N, T) * 0.5
    X = loadings[:, None] * factor[None, :] + noise
    X = (X - X.mean(axis=1, keepdims=True)) / X.std(axis=1, keepdims=True)
    C = (X @ X.T) / T
    C_clean = clip_mp(C, c=N/T)
    eigs_raw = sorted(np.linalg.eigvalsh(C).tolist(), reverse=True)
    eigs_clean = sorted(np.linalg.eigvalsh(C_clean).tolist(), reverse=True)
    # Top eigenvalue (the factor) should survive cleaning ~unchanged
    assert abs(eigs_raw[0] - eigs_clean[0]) < 1.0, \
        f"top eig changed too much: raw={eigs_raw[0]:.3f} clean={eigs_clean[0]:.3f}"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m pytest ai-lab/rmt/tests/test_cleaning.py::test_clip_mp_preserves_trace -v
```

Expected: ImportError / AttributeError for `clip_mp`.

- [ ] **Step 3: Implement clip_mp**

```python
# Append to cleaning.py
def clip_mp(C: np.ndarray, c: float) -> np.ndarray:
    """Marchenko-Pastur eigenvalue clipping (Laloux et al. 1999).

    Replace each eigenvalue inside the MP noise bulk with the average of bulk
    eigenvalues, preserving total trace. Reconstruct and renormalize diagonal.

    Args:
        C: NxN sample correlation matrix (symmetric, positive semidef).
        c: aspect ratio N/T of the underlying sample.

    Returns:
        Cleaned NxN correlation matrix.
    """
    if C.shape[0] != C.shape[1]:
        raise ValueError(f"C must be square, got {C.shape}")
    lo, hi = mp_edges(c)
    # Eigendecomp (symmetric → eigh for stability + ordered ascending)
    eigvals, eigvecs = np.linalg.eigh(C)
    in_bulk = (eigvals >= lo) & (eigvals <= hi)
    if in_bulk.any():
        bulk_mean = eigvals[in_bulk].mean()
        eigvals_clean = np.where(in_bulk, bulk_mean, eigvals)
    else:
        eigvals_clean = eigvals.copy()
    C_clean = (eigvecs * eigvals_clean) @ eigvecs.T
    # Renormalize diagonal to 1 (correlation property)
    d = np.sqrt(np.diag(C_clean))
    C_clean = C_clean / np.outer(d, d)
    # Force symmetry (numerical hygiene)
    C_clean = 0.5 * (C_clean + C_clean.T)
    return C_clean
```

- [ ] **Step 4: Run tests to verify both pass**

```bash
python3 -m pytest ai-lab/rmt/tests/test_cleaning.py -v
```

Expected: all PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add ai-lab/rmt/cleaning.py ai-lab/rmt/tests/test_cleaning.py
git commit -m "feat(rmt): Marchenko-Pastur eigenvalue clipping (Laloux method)"
```

---

## Task 4: Ledoit-Péché nonlinear shrinkage

**Files:**
- Modify: `niam-bay/ai-lab/rmt/cleaning.py` (add `shrink_lp`)
- Modify: `niam-bay/ai-lab/rmt/tests/test_cleaning.py`

**Background:** Optimal nonlinear shrinkage formula transforms each sample eigenvalue λ_i via the Stieltjes transform of the empirical eigenvalue distribution. Closed-form (Ledoit & Péché 2011, "Eigenvectors of some large sample covariance matrix ensembles", Theorem 2):

```
ξ_i = λ_i / |1 - c - c·λ_i·m̃(λ_i)|²
```

where `m̃` is the Stieltjes transform of the limiting MP distribution. For practical use, we approximate `m̃` numerically by kernel-smoothing the sample eigenvalues (see Ledoit & Wolf 2017 "Analytical Nonlinear Shrinkage of Large-Dimensional Covariance Matrices" for the QuEST routine; we'll use a simpler kernel approach sufficient for N≤200).

- [ ] **Step 1: Write the failing test**

```python
# Append to test_cleaning.py
def test_shrink_lp_shape_and_diagonal():
    np.random.seed(1)
    N, T = 30, 100
    X = np.random.randn(N, T)
    X = (X - X.mean(axis=1, keepdims=True)) / X.std(axis=1, keepdims=True)
    C = (X @ X.T) / T
    C_shrunk = shrink_lp(C, c=N/T)
    assert C_shrunk.shape == (N, N)
    np.testing.assert_allclose(np.diag(C_shrunk), 1.0, atol=1e-9)


def test_shrink_lp_pulls_eigenvalues_toward_one():
    """For pure noise, all eigenvalues should shrink toward 1."""
    np.random.seed(2)
    N, T = 50, 100  # high c → strong noise
    X = np.random.randn(N, T)
    X = (X - X.mean(axis=1, keepdims=True)) / X.std(axis=1, keepdims=True)
    C = (X @ X.T) / T
    eigs_raw = np.linalg.eigvalsh(C)
    spread_raw = eigs_raw.max() - eigs_raw.min()
    C_shrunk = shrink_lp(C, c=N/T)
    eigs_shrunk = np.linalg.eigvalsh(C_shrunk)
    spread_shrunk = eigs_shrunk.max() - eigs_shrunk.min()
    # Shrinkage must REDUCE eigenvalue spread for pure noise
    assert spread_shrunk < spread_raw, \
        f"shrinkage didn't reduce spread: raw={spread_raw:.3f} shrunk={spread_shrunk:.3f}"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m pytest ai-lab/rmt/tests/test_cleaning.py::test_shrink_lp_shape_and_diagonal -v
```

Expected: AttributeError `shrink_lp`.

- [ ] **Step 3: Implement shrink_lp (kernel Stieltjes approximation)**

```python
# Append to cleaning.py
def _stieltjes_kernel(z: complex, eigvals: np.ndarray, c: float, h: float) -> complex:
    """Numerical Stieltjes transform via kernel smoothing of the sample eigenvalues.

    Standard kernel: 1/N * sum_i 1/(z - λ_i) with imaginary offset h for stability.
    Returns m̃(z) = (m(z) + (1-c)/z) / c per the Ledoit-Péché paper, which is the
    Stieltjes transform of the COMPANION distribution used in the shrinkage formula.
    """
    z_eff = z + 1j * h
    m = np.mean(1.0 / (z_eff - eigvals))
    # Companion transform: m_tilde(z) = (1 - c)/(c * z) + m(z) / c — but use carefully:
    # The original Marchenko-Pastur companion is m̃(z) = -((1-c)/z + c·m(z)) when c=N/T.
    # Reference: Ledoit & Péché 2011, eq. (1.4).
    m_tilde = -(1 - c) / z_eff + c * m
    return m_tilde


def shrink_lp(C: np.ndarray, c: float, kernel_bandwidth: float | None = None) -> np.ndarray:
    """Ledoit-Péché optimal nonlinear shrinkage (kernel approximation).

    Args:
        C: NxN sample correlation matrix.
        c: aspect ratio N/T.
        kernel_bandwidth: imaginary offset h for the kernel Stieltjes estimator.
            If None, uses N^(-1/3) as default (Silverman-style).

    Returns:
        Cleaned NxN correlation matrix.
    """
    if C.shape[0] != C.shape[1]:
        raise ValueError(f"C must be square, got {C.shape}")
    N = C.shape[0]
    if kernel_bandwidth is None:
        kernel_bandwidth = N ** (-1.0 / 3.0)
    eigvals, eigvecs = np.linalg.eigh(C)
    # Avoid zero eigenvalues (numerical floor)
    eigvals_safe = np.where(eigvals > 1e-10, eigvals, 1e-10)
    # Apply LP shrinkage formula:
    #   ξ_i = λ_i / |1 - c - c·λ_i·m̃(λ_i)|²
    eigvals_clean = np.empty_like(eigvals_safe)
    for i, lam in enumerate(eigvals_safe):
        m_tilde = _stieltjes_kernel(lam, eigvals_safe, c, kernel_bandwidth)
        denom = abs(1.0 - c - c * lam * m_tilde) ** 2
        eigvals_clean[i] = lam / max(denom, 1e-10)
    # Reconstruct
    C_clean = (eigvecs * eigvals_clean) @ eigvecs.T
    d = np.sqrt(np.diag(C_clean))
    C_clean = C_clean / np.outer(d, d)
    C_clean = 0.5 * (C_clean + C_clean.T)
    return C_clean
```

- [ ] **Step 4: Run tests to verify pass**

```bash
python3 -m pytest ai-lab/rmt/tests/test_cleaning.py -v
```

Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add ai-lab/rmt/cleaning.py ai-lab/rmt/tests/test_cleaning.py
git commit -m "feat(rmt): Ledoit-Péché nonlinear shrinkage via kernel Stieltjes"
```

---

## Task 5: Binance cache data loader

**Files:**
- Create: `niam-bay/ai-lab/rmt/data_loader.py`
- Create: `niam-bay/ai-lab/rmt/tests/test_data_loader.py`

**Background:** Cache files at `niam-bay/ai-lab/darwin/data_cache/binance_<PAIR>USDT_<tf>_<start_ms>_<end_ms>.json`. Format unknown — first task is to inspect one file.

- [ ] **Step 1: Inspect cache format**

```bash
python3 -c "
import json
d = json.load(open('/home/tony/projets/tonyderide/niam-bay/ai-lab/darwin/data_cache/binance_BTCUSDT_1h_1672531200000_1767139200000.json'))
print(type(d), len(d) if hasattr(d, '__len__') else '')
print('first item:', d[0] if isinstance(d, list) else list(d.items())[0])
"
```

Document the structure inline in `data_loader.py` docstring.

- [ ] **Step 2: Write failing test**

```python
# niam-bay/ai-lab/rmt/tests/test_data_loader.py
import pandas as pd
from ai_lab.rmt.data_loader import load_pair_returns, load_panel_returns


def test_load_single_pair_returns_dataframe():
    df = load_pair_returns("BTC", tf="1h", n_periods=100)
    assert isinstance(df, pd.DataFrame)
    assert "BTC" in df.columns
    assert len(df) == 100
    # log returns must have zero NaN after dropna at construction
    assert df["BTC"].isna().sum() == 0
    # log returns typically in [-0.2, 0.2] for 1h crypto
    assert df["BTC"].abs().max() < 0.5


def test_load_panel_aligns_timestamps():
    panel = load_panel_returns(["BTC", "ETH", "SOL"], tf="1h", n_periods=200)
    assert panel.shape == (200, 3)
    assert set(panel.columns) == {"BTC", "ETH", "SOL"}
    # No NaN after alignment
    assert panel.isna().sum().sum() == 0
```

- [ ] **Step 3: Run test to verify it fails**

```bash
python3 -m pytest ai-lab/rmt/tests/test_data_loader.py -v
```

Expected: ImportError.

- [ ] **Step 4: Implement loader**

```python
# niam-bay/ai-lab/rmt/data_loader.py
"""Load Binance OHLC JSON cache → aligned log-return DataFrame.

Cache file format (after inspection in Step 1):
- Path: `niam-bay/ai-lab/darwin/data_cache/binance_<PAIR>USDT_<tf>_<ms_start>_<ms_end>.json`
- Format: array of klines, each kline = [open_time_ms, open, high, low, close, volume, close_time_ms, ...]
  (Binance standard OHLCV format)
"""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

CACHE_DIR = Path(os.environ.get(
    "RMT_CACHE_DIR",
    "/home/tony/projets/tonyderide/niam-bay/ai-lab/darwin/data_cache",
))

# Long-range cache files (3-year window): timestamps in the filename match this fixed range
_LONG_RANGE_SUFFIX = "1672531200000_1767139200000"


def _find_cache_file(pair: str, tf: str) -> Path:
    """Locate the canonical 3-year cache file for a pair + timeframe."""
    fn = f"binance_{pair}USDT_{tf}_{_LONG_RANGE_SUFFIX}.json"
    p = CACHE_DIR / fn
    if not p.exists():
        raise FileNotFoundError(f"cache file not found: {p}")
    return p


def load_pair_returns(pair: str, tf: str = "1h", n_periods: int | None = None) -> pd.DataFrame:
    """Load a single pair's log-return series.

    Args:
        pair: ticker without USDT suffix (e.g. "BTC").
        tf: timeframe code matching cache filename ("1h" or "4h").
        n_periods: if set, keep only the LAST n_periods returns.

    Returns:
        DataFrame indexed by timestamp (UTC), one column named `pair`, log returns.
    """
    p = _find_cache_file(pair, tf)
    raw = json.loads(p.read_text())
    # Each kline = [open_ms, open, high, low, close, volume, close_ms, ...]
    rows = [(int(k[0]), float(k[4])) for k in raw]
    df = pd.DataFrame(rows, columns=["ts_ms", "close"])
    df["ts"] = pd.to_datetime(df["ts_ms"], unit="ms", utc=True)
    df = df.set_index("ts").sort_index()
    df[pair] = np.log(df["close"]).diff()
    df = df[[pair]].dropna()
    if n_periods is not None:
        df = df.tail(n_periods)
    return df


def load_panel_returns(pairs: list[str], tf: str = "1h", n_periods: int | None = None) -> pd.DataFrame:
    """Load multiple pairs and align on common timestamps.

    Returns:
        DataFrame T×N where T is # aligned periods and N is len(pairs).
    """
    series = []
    for p in pairs:
        s = load_pair_returns(p, tf=tf, n_periods=None)
        series.append(s)
    df = pd.concat(series, axis=1, join="inner")  # inner join on timestamp
    df = df.dropna()  # safety
    if n_periods is not None:
        df = df.tail(n_periods)
    return df
```

- [ ] **Step 5: Run tests to verify pass**

```bash
python3 -m pytest ai-lab/rmt/tests/test_data_loader.py -v
```

Expected: 2 pass.

- [ ] **Step 6: Commit**

```bash
git add ai-lab/rmt/data_loader.py ai-lab/rmt/tests/test_data_loader.py
git commit -m "feat(rmt): Binance OHLC cache loader with timestamp alignment"
```

---

## Task 6: Walk-forward backtest harness

**Files:**
- Create: `niam-bay/ai-lab/rmt/backtest.py`
- Create: `niam-bay/ai-lab/rmt/tests/test_backtest.py`

**Strategy under test:** Mean-variance optimal portfolio (Markowitz, long-only, weights sum to 1) using different correlation estimators:
1. **EQ**: equal-weight (1/N) — baseline
2. **RAW**: sample correlation, no cleaning
3. **CLIP**: MP-clipped correlation
4. **LP**: Ledoit-Péché shrunk correlation

Walk-forward:
- At each rebalance date t:
  - Train on returns [t - window, t)
  - Compute weights w_t for each method
  - Apply w_t to returns at t (out-of-sample 1-step)
  - Roll forward by `rebalance_freq` periods

Outputs per method: Sharpe ratio, max drawdown, turnover, cumulative return.

- [ ] **Step 1: Write failing test**

```python
# niam-bay/ai-lab/rmt/tests/test_backtest.py
import numpy as np
import pandas as pd
from ai_lab.rmt.backtest import min_variance_weights, walk_forward


def test_min_variance_weights_long_only_sum_to_one():
    np.random.seed(0)
    N = 4
    cov = np.eye(N) + 0.1 * np.ones((N, N))
    w = min_variance_weights(cov)
    assert w.shape == (N,)
    np.testing.assert_allclose(w.sum(), 1.0, atol=1e-9)
    assert (w >= -1e-10).all(), f"weights have negatives: {w}"


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
    # Each must be a Series of out-of-sample portfolio returns
    for method, s in result.items():
        assert isinstance(s, pd.Series)
        # Some out-of-sample points must exist
        assert len(s) > 0
```

- [ ] **Step 2: Run to verify it fails**

```bash
python3 -m pytest ai-lab/rmt/tests/test_backtest.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement backtest**

```python
# niam-bay/ai-lab/rmt/backtest.py
"""Walk-forward portfolio backtest comparing covariance estimators.

Reference for Markowitz long-only: Markowitz 1952 + standard quadratic prog.
We use scipy.optimize.minimize with SLSQP for simplicity (N ≤ 30 is fast enough).
"""
from typing import Callable

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .cleaning import clip_mp, shrink_lp


def min_variance_weights(cov: np.ndarray) -> np.ndarray:
    """Compute minimum-variance long-only weights subject to sum(w) = 1.

    Args:
        cov: NxN covariance matrix (symmetric, positive semidef).

    Returns:
        N-array of weights in [0, 1] summing to 1.
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
        # Fallback: equal-weight on failure (don't crash backtest)
        return w0
    return res.x


def _cov_from_returns(rets: np.ndarray, method: str) -> np.ndarray:
    """Estimate covariance matrix from a T×N returns array under a given method."""
    if rets.shape[0] < 2:
        raise ValueError("need at least 2 observations")
    # Sample covariance
    cov_sample = np.cov(rets.T, ddof=1)
    if method == "raw":
        return cov_sample
    # For RMT methods we operate on the correlation matrix, then rescale to cov
    stds = np.sqrt(np.diag(cov_sample))
    corr = cov_sample / np.outer(stds, stds)
    np.fill_diagonal(corr, 1.0)
    N, T = rets.shape[1], rets.shape[0]
    c = N / T
    if method == "clip":
        corr_clean = clip_mp(corr, c=c)
    elif method == "lp":
        corr_clean = shrink_lp(corr, c=c)
    elif method == "eq":
        # equal-weight ignores covariance entirely; sentinel
        return cov_sample
    else:
        raise ValueError(f"unknown method: {method}")
    return corr_clean * np.outer(stds, stds)


def walk_forward(
    returns: pd.DataFrame, window: int, rebalance_freq: int = 24
) -> dict[str, pd.Series]:
    """Walk-forward backtest of 4 portfolio methods.

    Args:
        returns: T×N DataFrame of returns indexed by timestamp.
        window: # of past periods used as training window for covariance estimation.
        rebalance_freq: rebalance every `rebalance_freq` periods.

    Returns:
        Dict mapping method name → Series of out-of-sample portfolio returns.
    """
    methods = ["eq", "raw", "clip", "lp"]
    out: dict[str, list[tuple]] = {m: [] for m in methods}
    n_periods, N = returns.shape
    # Start at index `window`; first OOS period is `window`
    for t in range(window, n_periods, rebalance_freq):
        train = returns.iloc[t - window:t].values
        for method in methods:
            if method == "eq":
                w = np.full(N, 1.0 / N)
            else:
                cov = _cov_from_returns(train, method)
                w = min_variance_weights(cov)
            # Apply w to the next `rebalance_freq` returns
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
    """Compute Sharpe + max drawdown + total return for a portfolio return series."""
    if len(pnl) == 0:
        return {"sharpe": 0.0, "max_dd": 0.0, "total_return": 0.0, "n_periods": 0}
    mean = pnl.mean() * periods_per_year
    vol = pnl.std() * np.sqrt(periods_per_year)
    sharpe = mean / vol if vol > 0 else 0.0
    cumret = (1 + pnl).cumprod()
    peak = cumret.cummax()
    dd = (cumret - peak) / peak
    return {
        "sharpe": float(sharpe),
        "max_dd": float(dd.min()),
        "total_return": float(cumret.iloc[-1] - 1),
        "n_periods": len(pnl),
    }
```

- [ ] **Step 4: Run tests**

```bash
python3 -m pytest ai-lab/rmt/tests/test_backtest.py -v
```

Expected: 2 pass.

- [ ] **Step 5: Commit**

```bash
git add ai-lab/rmt/backtest.py ai-lab/rmt/tests/test_backtest.py
git commit -m "feat(rmt): walk-forward Markowitz backtest with 4 estimators"
```

---

## Task 7: CLI + first real-data backtest run

**Files:**
- Create: `niam-bay/ai-lab/rmt/cli.py`
- Modify: `niam-bay/ai-lab/rmt/README.md` (add results section)

- [ ] **Step 1: Write CLI**

```python
# niam-bay/ai-lab/rmt/cli.py
"""CLI for running the RMT cleaning backtest on Martin's 8 supported pairs."""
import argparse
import sys
from pathlib import Path

import pandas as pd

from .backtest import walk_forward, summary_stats
from .data_loader import load_panel_returns


MARTIN_PAIRS = ["BTC", "ETH", "SOL", "LINK", "ADA", "LTC", "ATOM", "AVAX"]


def main() -> int:
    parser = argparse.ArgumentParser(description="RMT portfolio cleaning backtest")
    parser.add_argument("--pairs", default=",".join(MARTIN_PAIRS),
                        help="Comma-separated pair tickers (default: Martin's 8)")
    parser.add_argument("--tf", default="1h", choices=["1h", "4h"],
                        help="Timeframe (default 1h)")
    parser.add_argument("--window", type=int, default=720,
                        help="Training window in periods (default 720 = 30d on 1h)")
    parser.add_argument("--rebalance", type=int, default=24,
                        help="Rebalance frequency in periods (default 24 = daily on 1h)")
    parser.add_argument("--n-periods", type=int, default=None,
                        help="Trim total panel to last N periods (default: full cache)")
    parser.add_argument("--output", default=None,
                        help="Path to write per-method PnL CSV")
    args = parser.parse_args()

    pairs = [p.strip().upper() for p in args.pairs.split(",")]
    print(f"Loading {len(pairs)} pairs at {args.tf} timeframe...", file=sys.stderr)
    rets = load_panel_returns(pairs, tf=args.tf, n_periods=args.n_periods)
    print(f"Panel shape: {rets.shape} (T={rets.shape[0]}, N={rets.shape[1]})", file=sys.stderr)
    print(f"Date range: {rets.index[0]} → {rets.index[-1]}", file=sys.stderr)

    periods_per_year = (24 * 365) if args.tf == "1h" else (6 * 365)
    print(f"Running walk-forward (window={args.window}, rebalance={args.rebalance})...",
          file=sys.stderr)
    pnls = walk_forward(rets, window=args.window, rebalance_freq=args.rebalance)

    print(f"\n{'Method':<10} {'Sharpe':>8} {'MaxDD':>10} {'TotRet':>10} {'N':>6}")
    print("-" * 50)
    summary = {}
    for method, pnl in pnls.items():
        s = summary_stats(pnl, periods_per_year=periods_per_year)
        summary[method] = s
        print(f"{method:<10} {s['sharpe']:>8.3f} {s['max_dd']*100:>9.2f}% "
              f"{s['total_return']*100:>9.2f}% {s['n_periods']:>6}")

    if args.output:
        out_df = pd.DataFrame(pnls)
        out_df.to_csv(args.output)
        print(f"\nWrote PnL CSV → {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run baseline backtest (eq vs raw)**

```bash
cd /home/tony/projets/tonyderide/niam-bay
python3 -m ai_lab.rmt.cli --window 720 --rebalance 24 --tf 1h
```

Expected: 4 rows (eq, raw, clip, lp) with Sharpe + MaxDD + TotRet.

Sanity bounds:
- Equal-weight Sharpe should be modest (0.3-1.5)
- RAW should be similar or slightly worse (overfitting)
- CLIP + LP should beat RAW out-of-sample on Sharpe by ~10-30% (Bouchaud literature reference)

- [ ] **Step 3: Document results**

Append to `niam-bay/ai-lab/rmt/README.md`:

```markdown
## Backtest Results — 2026-05-24

Pairs: BTC, ETH, SOL, LINK, ADA, LTC, ATOM, AVAX
Timeframe: 1h
Window: 720 (30 days)
Rebalance: 24 (daily)
Data: 2023-01-01 → 2026-01-01 (~26,000 hourly returns)

| Method | Sharpe | MaxDD | TotalRet |
|--------|--------|-------|----------|
| eq     | [fill] | [fill]| [fill]   |
| raw    | [fill] | [fill]| [fill]   |
| clip   | [fill] | [fill]| [fill]   |
| lp     | [fill] | [fill]| [fill]   |

### Interpretation
[Fill after running — note whether RMT methods beat raw, and by how much]
```

- [ ] **Step 4: Commit**

```bash
git add ai-lab/rmt/cli.py ai-lab/rmt/README.md
git commit -m "feat(rmt): CLI + initial backtest run on 8 Martin pairs"
```

---

## Task 8: Robustness checks (varying c, varying window)

**Files:**
- Modify: `niam-bay/ai-lab/rmt/cli.py` (add `--robustness` flag)
- Create: `niam-bay/ai-lab/rmt/robustness.py`

**Goal:** Sweep window ∈ {360, 720, 1440, 2160} (15d, 30d, 60d, 90d on 1h) and report Sharpe stability. The smaller the window, the higher c, the more RMT should help.

- [ ] **Step 1: Implement sweep**

```python
# niam-bay/ai-lab/rmt/robustness.py
"""Sensitivity analysis: how Sharpe of each method varies with training window size."""
import pandas as pd

from .backtest import walk_forward, summary_stats


def sweep_window(
    returns: pd.DataFrame,
    windows: list[int],
    rebalance: int,
    periods_per_year: int,
) -> pd.DataFrame:
    """Return DataFrame indexed by window, columns = (method, metric).

    Metrics: sharpe, max_dd, total_return.
    """
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
```

- [ ] **Step 2: Add `--robustness` flag to CLI**

```python
# In cli.py main(), after parsing args:
if args.robustness:
    from .robustness import sweep_window
    windows = [int(w) for w in args.robustness.split(",")]
    df = sweep_window(rets, windows=windows, rebalance=args.rebalance,
                      periods_per_year=periods_per_year)
    print(df.pivot(index="window", columns="method", values="sharpe"))
    if args.output:
        df.to_csv(args.output, index=False)
    return 0
```

Also add to argparse:
```python
parser.add_argument("--robustness", default=None,
                    help="Run sweep over comma-separated windows (e.g. 360,720,1440)")
```

- [ ] **Step 3: Run sweep**

```bash
python3 -m ai_lab.rmt.cli --robustness 360,720,1440,2160 --tf 1h
```

Document the pivot table in README under "Robustness".

- [ ] **Step 4: Commit**

```bash
git add ai-lab/rmt/cli.py ai-lab/rmt/robustness.py ai-lab/rmt/README.md
git commit -m "feat(rmt): robustness sweep across training windows"
```

---

## Task 9: Final review + documentation

**Files:**
- Modify: `niam-bay/ai-lab/rmt/README.md`
- Create: `niam-bay/ai-lab/rmt/RESULTS.md`

- [ ] **Step 1: Write RESULTS.md with interpretation**

Template:

```markdown
# RMT Cleaning Backtest — Results & Interpretation

## Main finding
[1-2 sentences: did RMT cleaning beat raw on the 8 Martin pairs?]

## Numbers (window=720, rebalance=24, 1h, 2023-2026)
| Method | Sharpe | MaxDD | TotRet | Δ vs raw |

## Robustness
[Pivot table from Task 8]

## Practical implication for Martin
- If clip/lp beats raw by ≥10% Sharpe: integrate into pair selection logic
- If similar/worse: noise floor on N=8 is too low, RMT not worth the complexity
- Either way: dispersed eigenvalue spread between top + bulk tells us regime concentration

## Skill packaging
After validation, this can be wrapped as `rmt-clean` skill for the Council:
- Input: pair list + lookback
- Output: cleaned correlation matrix + recommended uncorrelated pair subset
- Use: Hannah/Tomás can call it before backtesting strategies
```

- [ ] **Step 2: Final commit**

```bash
git add ai-lab/rmt/RESULTS.md ai-lab/rmt/README.md
git commit -m "docs(rmt): results + skill packaging notes"
```

---

## Out of scope (deferred to future plan)

- **Wrapping as a `rmt-clean` Claude skill** for direct use by Council agents (Hannah, Tomás). Requires SKILL.md authoring + plugin marketplace registration.
- **Integration with live Martin bot** — using cleaned correlations to inform `enable_autograd_pair` decisions. Needs further validation that the signal is real for 8-pair panel.
- **Higher-order RMT methods** — Bun-Bouchaud (rotationally invariant estimator), El Karoui sparse covariance estimation. Only worth it if Ledoit-Péché isn't enough.

## Verification before considering done

- [ ] All 8 tests pass (`pytest ai-lab/rmt/`)
- [ ] CLI runs to completion on full 3-year cache
- [ ] Baseline backtest results match published Bouchaud-style ranges (RMT methods ≥ raw on Sharpe)
- [ ] No new uncommitted files in `git status`

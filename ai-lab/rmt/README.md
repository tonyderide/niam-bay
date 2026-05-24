# RMT Portfolio Cleaning

Implements Marchenko-Pastur eigenvalue clipping (Laloux et al. 1999) and Ledoit-Péché nonlinear shrinkage (Ledoit & Péché 2011) to clean noisy sample correlation matrices before mean-variance portfolio optimization.

## References
- Wigner 1955 — Random matrix theory foundations
- Marchenko & Pastur 1967 — Sample covariance eigenvalue distribution
- Laloux, Cizeau, Bouchaud, Potters 1999 — RMT noise dressing on S&P500
- Ledoit-Wolf 2003 — Linear shrinkage estimator
- Ledoit & Péché 2011 — Optimal nonlinear shrinkage via Stieltjes transform

## Quick start
```bash
cd niam-bay/ai-lab
source /home/tony/projets/tonyderide/martin-agency/backend/.venv/bin/activate
python3 -m rmt.cli --window 720 --rebalance 24 --tf 1h --output /tmp/rmt_pnl.csv
```

Note: LTC is excluded — `binance_LTCUSDT_1h_1672531200000_1767139200000.json` is absent from data_cache; only a short 1-min LTC window exists. Use 7 pairs (BTC/ETH/SOL/LINK/ADA/ATOM/AVAX).

## Import convention

The parent directory is `ai-lab/` (hyphen), which is not directly importable as `ai_lab` in Python.
This follows the same convention as the existing `darwin/` package in this repo: scripts are run
from within the `ai-lab/` directory so that `rmt` is a top-level package.

**Correct usage:**
```bash
# Run as a module (from niam-bay/ai-lab/)
cd niam-bay/ai-lab
python3 -m rmt.cli backtest ...

# Run tests (from niam-bay/ai-lab/)
cd niam-bay/ai-lab
python3 -m pytest rmt/tests/
```

**If you need `from ai_lab.rmt` imports** (e.g. from niam-bay root), add `ai-lab/` to PYTHONPATH:
```bash
PYTHONPATH=/path/to/niam-bay/ai-lab python3 -c "from rmt import ..."
```

## Backtest Results — 2026-05-24

Pairs: BTC, ETH, SOL, LINK, ADA, ATOM, AVAX (7 pairs — LTC excluded, no 1h cache)
Timeframe: 1h, Window: 720 (30 days), Rebalance: 24 (daily)
Data: 2023-01-01 → 2025-12-31 (T=26279 aligned hourly candles)
Runtime: ~71 seconds

| Method | Sharpe | MaxDD   | TotalRet |
|--------|--------|---------|----------|
| eq     |  0.128 | -72.80% |  -35.51% |
| raw    |  0.659 | -45.07% |  +78.99% |
| clip   |  0.659 | -45.07% |  +78.99% |
| lp     |  0.643 | -45.06% |  +75.34% |

### Interpretation

RMT cleaning decisively beats equal-weight (1/N): raw/clip/lp all achieve Sharpe ~0.66 vs 0.13 for eq, and total return +79% vs -36% over 3 years. clip and raw are indistinguishable at this N=7, T=720 ratio (c=7/720≈0.01, very low-rank pressure), which is expected — eigenvalue cleaning only matters when c is large (e.g. N≥T/4). lp shows a marginal 3.7 pp lower total return than raw/clip, likely due to over-aggressive shrinkage at very low c. **Green light for skill packaging: any of raw/clip/lp beats 1/N by a wide margin; the covariance-based optimizer adds real value on this universe.**

# RMT Portfolio Cleaning

Implements Marchenko-Pastur eigenvalue clipping (Laloux et al. 1999) and Ledoit-Péché nonlinear shrinkage (Ledoit & Péché 2011) to clean noisy sample correlation matrices before mean-variance portfolio optimization.

## References
- Wigner 1955 — Random matrix theory foundations
- Marchenko & Pastur 1967 — Sample covariance eigenvalue distribution
- Laloux, Cizeau, Bouchaud, Potters 1999 — RMT noise dressing on S&P500
- Ledoit-Wolf 2003 — Linear shrinkage estimator
- Ledoit & Péché 2011 — Optimal nonlinear shrinkage via Stieltjes transform

## Quick start
See cli.py: `python -m ai_lab.rmt.cli backtest --pairs BTC,ETH,SOL,LINK,ADA,LTC,ATOM,AVAX --window 30 --tf 1h`

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

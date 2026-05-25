"""Cycle 80 empirical validation — RMT cleaning deviation at small N.

Cycle 79 finding: at w=50 and w=100 on the canonical 3-year panel, clip and lp
degrade Sharpe slightly vs raw (clip -0.009, lp -0.024 at w=50). RESULTS.md
claims "indistinguishable" — imprecise.

This script splits the 3-year panel into multiple non-overlapping temporal slices
and re-runs walk_forward at w=50 and w=100 on each slice. Goal: check if the
clip<raw and lp<raw degradations are systematic across regimes, or an artefact
of one specific period in the full backtest.

Methodology:
- 6 slices of ~3500 hourly periods each (~5 months), non-overlapping, covering
  2023-01 → 2025-12.
- For each slice + window in {50, 100}, run walk_forward and record Sharpe per
  method.
- Report: (a) per-slice deltas vs raw, (b) sign frequency, (c) magnitude stats.

Result is purely descriptive — no doc rewriting, just data Tony can integrate
into RESULTS.md if he chooses.
"""

import sys
from pathlib import Path

# Allow running standalone: python validate_w50_cycle80.py
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from rmt.backtest import walk_forward, summary_stats
from rmt.data_loader import load_panel_returns
from rmt.cli import MARTIN_PAIRS

PERIODS_PER_YEAR = 24 * 365
N_SLICES = 6
SLICE_WINDOWS = [50, 100]
REBALANCE = 24


def slice_panel(rets: pd.DataFrame, n_slices: int) -> list[pd.DataFrame]:
    """Cut the panel into n_slices non-overlapping contiguous slices."""
    T = rets.shape[0]
    chunk = T // n_slices
    return [rets.iloc[i * chunk : (i + 1) * chunk] for i in range(n_slices)]


def run_one(rets: pd.DataFrame, window: int) -> dict[str, float]:
    """Walk-forward + Sharpe per method for a single slice + window."""
    pnls = walk_forward(rets, window=window, rebalance_freq=REBALANCE)
    return {
        m: summary_stats(pnl, periods_per_year=PERIODS_PER_YEAR)["sharpe"]
        for m, pnl in pnls.items()
    }


def main() -> int:
    print(f"Loading {len(MARTIN_PAIRS)} pairs at 1h timeframe...", file=sys.stderr)
    rets = load_panel_returns(MARTIN_PAIRS, tf="1h")
    print(f"Panel: T={rets.shape[0]}, N={rets.shape[1]} "
          f"({rets.index[0].date()} → {rets.index[-1].date()})", file=sys.stderr)

    slices = slice_panel(rets, N_SLICES)
    print(f"\nSplit into {N_SLICES} contiguous slices of "
          f"~{slices[0].shape[0]} rows each.\n", file=sys.stderr)

    rows = []
    for w in SLICE_WINDOWS:
        for i, sl in enumerate(slices):
            label = f"{sl.index[0].date()} → {sl.index[-1].date()}"
            sharpe = run_one(sl, w)
            row = {"window": w, "slice": i, "period": label, **sharpe}
            row["clip_minus_raw"] = sharpe["clip"] - sharpe["raw"]
            row["lp_minus_raw"] = sharpe["lp"] - sharpe["raw"]
            rows.append(row)
            print(f"  w={w} slice={i} ({label}): "
                  f"eq={sharpe['eq']:+.3f}  raw={sharpe['raw']:+.3f}  "
                  f"clip={sharpe['clip']:+.3f}  lp={sharpe['lp']:+.3f}  "
                  f"Δclip={row['clip_minus_raw']:+.3f}  "
                  f"Δlp={row['lp_minus_raw']:+.3f}")

    df = pd.DataFrame(rows)
    print(f"\n{'='*80}")
    print("Deviation summary across slices")
    print(f"{'='*80}")
    for w in SLICE_WINDOWS:
        sub = df[df.window == w]
        clip_neg = (sub.clip_minus_raw < 0).sum()
        lp_neg = (sub.lp_minus_raw < 0).sum()
        clip_pos = (sub.clip_minus_raw > 0).sum()
        lp_pos = (sub.lp_minus_raw > 0).sum()
        print(f"\nwindow={w}  (N slices = {len(sub)})")
        print(f"  clip vs raw : neg={clip_neg}  pos={clip_pos}  "
              f"mean Δ={sub.clip_minus_raw.mean():+.4f}  "
              f"std Δ={sub.clip_minus_raw.std():.4f}  "
              f"median Δ={sub.clip_minus_raw.median():+.4f}")
        print(f"  lp   vs raw : neg={lp_neg}    pos={lp_pos}    "
              f"mean Δ={sub.lp_minus_raw.mean():+.4f}  "
              f"std Δ={sub.lp_minus_raw.std():.4f}  "
              f"median Δ={sub.lp_minus_raw.median():+.4f}")

    # Persist for posterity
    out = Path(__file__).parent / "validate_w50_cycle80_results.csv"
    df.to_csv(out, index=False)
    print(f"\nWrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""CLI for running the RMT cleaning backtest on Martin's supported pairs."""
import argparse
import sys
from pathlib import Path

import pandas as pd

from rmt.backtest import walk_forward, summary_stats
from rmt.data_loader import load_panel_returns


# LTC is excluded: binance_LTCUSDT_1h_1672531200000_1767139200000.json is absent
# from the data_cache directory.  Only the short 1-minute window for LTC exists
# (binance_LTCUSDT_1min_1709251200000_1714435200000.json), so the canonical 3-year
# hourly dataset was never cached.  Drop to 7 pairs.
MARTIN_PAIRS = ["BTC", "ETH", "SOL", "LINK", "ADA", "ATOM", "AVAX"]


def main() -> int:
    parser = argparse.ArgumentParser(description="RMT portfolio cleaning backtest")
    parser.add_argument("--pairs", default=",".join(MARTIN_PAIRS))
    parser.add_argument("--tf", default="1h", choices=["1h", "4h"])
    parser.add_argument("--window", type=int, default=720,
                        help="Training window in periods (default 720 = 30d on 1h)")
    parser.add_argument("--rebalance", type=int, default=24,
                        help="Rebalance frequency in periods (default 24 = daily on 1h)")
    parser.add_argument("--n-periods", type=int, default=None,
                        help="Trim total panel to last N periods")
    parser.add_argument("--output", default=None,
                        help="Path to write per-method PnL CSV")
    parser.add_argument("--robustness", default=None,
                        help="Run sweep over comma-separated windows (e.g. 100,200,500,720)")
    args = parser.parse_args()

    pairs = [p.strip().upper() for p in args.pairs.split(",")]
    print(f"Loading {len(pairs)} pairs at {args.tf} timeframe...", file=sys.stderr)
    rets = load_panel_returns(pairs, tf=args.tf, n_periods=args.n_periods)
    print(f"Panel shape: {rets.shape} (T={rets.shape[0]}, N={rets.shape[1]})", file=sys.stderr)
    print(f"Date range: {rets.index[0]} → {rets.index[-1]}", file=sys.stderr)

    periods_per_year = (24 * 365) if args.tf == "1h" else (6 * 365)

    if args.robustness:
        from rmt.robustness import sweep_window
        windows = sorted(set(int(w) for w in args.robustness.split(",")))
        print(f"Sweep windows: {windows}", file=sys.stderr)
        df = sweep_window(rets, windows=windows, rebalance=args.rebalance,
                          periods_per_year=periods_per_year)
        pivot = df.pivot(index="window", columns="method", values="sharpe")
        pivot = pivot[["eq", "raw", "clip", "lp"]]  # explicit column order
        print(f"\nSharpe ratios by training window (rebalance={args.rebalance}):\n")
        print(pivot.to_string(float_format=lambda x: f"{x:.3f}"))
        if args.output:
            df.to_csv(args.output, index=False)
            print(f"\nWrote sweep CSV → {args.output}", file=sys.stderr)
        return 0

    print(f"Running walk-forward (window={args.window}, rebalance={args.rebalance})...",
          file=sys.stderr)
    pnls = walk_forward(rets, window=args.window, rebalance_freq=args.rebalance)

    print(f"\n{'Method':<10} {'Sharpe':>8} {'MaxDD':>10} {'TotRet':>10} {'N':>6}")
    print("-" * 50)
    summary = {}
    for method in ["eq", "raw", "clip", "lp"]:  # explicit order
        pnl = pnls[method]
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

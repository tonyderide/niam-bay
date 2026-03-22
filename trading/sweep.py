"""
Niam-Bay Strategy Sweep — Test ALL combinations
================================================
Grid: 7 pairs x 6 spacings x 4 levels x 3 leverages x 3 timeframes = 1512
Mean Reversion: 3 pairs x 3 EMA x 3 RSI x 3 BB x 3 timeframes = 243 (with timeframes)
Breakout: 3 pairs x 4 lookback x 3 vol_mult x 3 timeframes = 108 (with timeframes)
Total: ~1863 combinations
"""

import copy
import sys
import time
from pathlib import Path

# Add parent to path so we can import backtest
sys.path.insert(0, str(Path(__file__).parent))

from backtest import (
    Backtester, GridStrategy, MeanReversionStrategy, BreakoutStrategy,
    load_candles, Results
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CAPITAL = 100.0
MAKER_FEE = 0.0002
TAKER_FEE = 0.0005
DATA_DIR = Path(__file__).parent / "data"

# Map friendly names to file prefixes
PAIR_MAP = {
    "ETH": "XETHZUSD",
    "BTC": "XXBTZUSD",
    "SOL": "SOLUSD",
    "XRP": "XXRPZUSD",
    "ADA": "ADAUSD",
    "LINK": "LINKUSD",
    "DOT": "DOTUSD",
}

TIMEFRAMES = ["1m", "5m", "15m"]

# ---------------------------------------------------------------------------
# Data cache
# ---------------------------------------------------------------------------
_cache = {}

def get_candles(pair: str, tf: str):
    key = (pair, tf)
    if key not in _cache:
        prefix = PAIR_MAP[pair]
        path = DATA_DIR / f"{prefix}_{tf}.csv"
        if not path.exists():
            return None
        _cache[key] = load_candles(path)
    return _cache[key]

# ---------------------------------------------------------------------------
# Result storage
# ---------------------------------------------------------------------------
all_results = []  # list of dicts

def run_one(name: str, strategy, candles, leverage: float):
    bt = Backtester(candles, strategy, capital=CAPITAL, leverage=leverage,
                    maker_fee=MAKER_FEE, taker_fee=TAKER_FEE)
    res = bt.run()
    return {
        "name": name,
        "net_profit": res.net_profit,
        "total_profit": res.total_profit,
        "total_fees": res.total_fees,
        "trades": res.total_trades,
        "win_rate": res.win_rate,
        "max_drawdown": res.max_drawdown,
        "sharpe": res.sharpe_ratio,
        "profit_factor": res.profit_factor,
    }

# ---------------------------------------------------------------------------
# Sweep 1: Grid
# ---------------------------------------------------------------------------
def sweep_grid():
    pairs = ["ETH", "BTC", "SOL", "XRP", "ADA", "LINK", "DOT"]
    spacings = [0.3, 0.5, 0.7, 1.0, 1.5, 2.0]
    levels_list = [3, 5, 8, 10]
    leverages = [3, 5, 10]
    count = 0

    for pair in pairs:
        for tf in TIMEFRAMES:
            candles = get_candles(pair, tf)
            if candles is None:
                continue
            for spacing in spacings:
                for levels in levels_list:
                    for lev in leverages:
                        strat = GridStrategy(spacing_pct=spacing, levels=levels)
                        name = f"Grid|{pair}|{tf}|sp={spacing}%|lv={levels}|{lev}x"
                        r = run_one(name, strat, candles, lev)
                        all_results.append(r)
                        count += 1
    return count

# ---------------------------------------------------------------------------
# Sweep 2: Mean Reversion
# ---------------------------------------------------------------------------
def sweep_mean_reversion():
    pairs = ["ETH", "SOL", "XRP"]
    ema_periods = [10, 20, 50]
    rsi_periods = [7, 14, 21]
    bb_periods = [15, 20, 30]
    count = 0

    for pair in pairs:
        for tf in TIMEFRAMES:
            candles = get_candles(pair, tf)
            if candles is None:
                continue
            for ema in ema_periods:
                for rsi in rsi_periods:
                    for bb in bb_periods:
                        strat = MeanReversionStrategy(ema_period=ema, rsi_period=rsi, bb_period=bb)
                        name = f"MeanRev|{pair}|{tf}|ema={ema}|rsi={rsi}|bb={bb}"
                        # Mean reversion at 1x leverage (conservative)
                        r = run_one(name, strat, candles, 1.0)
                        all_results.append(r)
                        # Also test with 3x and 5x
                        for lev in [3, 5]:
                            strat2 = MeanReversionStrategy(ema_period=ema, rsi_period=rsi, bb_period=bb)
                            name2 = f"MeanRev|{pair}|{tf}|ema={ema}|rsi={rsi}|bb={bb}|{lev}x"
                            r2 = run_one(name2, strat2, candles, lev)
                            all_results.append(r2)
                        count += 3
    return count

# ---------------------------------------------------------------------------
# Sweep 3: Breakout
# ---------------------------------------------------------------------------
def sweep_breakout():
    pairs = ["ETH", "SOL", "BTC"]
    lookbacks = [10, 20, 30, 50]
    vol_mults = [1.5, 2.0, 3.0]
    count = 0

    for pair in pairs:
        for tf in TIMEFRAMES:
            candles = get_candles(pair, tf)
            if candles is None:
                continue
            for lb in lookbacks:
                for vm in vol_mults:
                    strat = BreakoutStrategy(lookback=lb, volume_mult=vm)
                    name = f"Breakout|{pair}|{tf}|lb={lb}|vol={vm}x"
                    r = run_one(name, strat, candles, 1.0)
                    all_results.append(r)
                    # Also 3x and 5x
                    for lev in [3, 5]:
                        strat2 = BreakoutStrategy(lookback=lb, volume_mult=vm)
                        name2 = f"Breakout|{pair}|{tf}|lb={lb}|vol={vm}x|{lev}x"
                        r2 = run_one(name2, strat2, candles, lev)
                        all_results.append(r2)
                    count += 3
    return count

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 80)
    print("  NIAM-BAY STRATEGY SWEEP")
    print(f"  Capital: ${CAPITAL}  |  Maker: {MAKER_FEE*100:.2f}%  |  Taker: {TAKER_FEE*100:.2f}%")
    print("=" * 80)
    print()

    t0 = time.time()

    print("[1/3] Grid sweep ...")
    n1 = sweep_grid()
    print(f"  -> {n1} combinations tested")

    print("[2/3] Mean Reversion sweep ...")
    n2 = sweep_mean_reversion()
    print(f"  -> {n2} combinations tested")

    print("[3/3] Breakout sweep ...")
    n3 = sweep_breakout()
    print(f"  -> {n3} combinations tested")

    elapsed = time.time() - t0
    print(f"\nTotal: {len(all_results)} backtests in {elapsed:.1f}s")

    # Sort by net_profit descending
    all_results.sort(key=lambda x: x["net_profit"], reverse=True)

    # Print TOP 20
    print()
    print("=" * 120)
    print("  TOP 20 MOST PROFITABLE STRATEGIES")
    print("=" * 120)
    header = f"{'#':>3} {'Strategy':<55} {'Net$':>10} {'Gross$':>10} {'Fees$':>8} {'Trades':>6} {'Win%':>6} {'MaxDD%':>7} {'Sharpe':>7} {'PF':>7}"
    print(header)
    print("-" * 120)

    for i, r in enumerate(all_results[:20]):
        pf_str = f"{r['profit_factor']:.2f}" if r['profit_factor'] < 1e6 else "inf"
        print(f"{i+1:>3} {r['name']:<55} {r['net_profit']:>+10.2f} {r['total_profit']:>+10.2f} {r['total_fees']:>8.2f} {r['trades']:>6} {r['win_rate']*100:>5.1f}% {r['max_drawdown']*100:>6.2f}% {r['sharpe']:>7.2f} {pf_str:>7}")

    print("=" * 120)

    # Also print BOTTOM 5 (worst)
    print()
    print("  BOTTOM 5 (worst)")
    print("-" * 120)
    for i, r in enumerate(all_results[-5:]):
        pf_str = f"{r['profit_factor']:.2f}" if r['profit_factor'] < 1e6 else "inf"
        print(f"  {r['name']:<55} {r['net_profit']:>+10.2f} {r['trades']:>6} {r['win_rate']*100:>5.1f}% {r['max_drawdown']*100:>6.2f}%")
    print()

    # Stats summary
    profitable = [r for r in all_results if r['net_profit'] > 0]
    print(f"Profitable: {len(profitable)}/{len(all_results)} ({len(profitable)/len(all_results)*100:.1f}%)")
    print(f"Best net: ${all_results[0]['net_profit']:+.2f}")
    print(f"Worst net: ${all_results[-1]['net_profit']:+.2f}")
    avg_net = sum(r['net_profit'] for r in all_results) / len(all_results)
    print(f"Average net: ${avg_net:+.2f}")
    print()

    # Group by strategy type
    for stype in ["Grid", "MeanRev", "Breakout"]:
        subset = [r for r in all_results if r['name'].startswith(stype)]
        if not subset:
            continue
        prof = [r for r in subset if r['net_profit'] > 0]
        best = max(subset, key=lambda x: x['net_profit'])
        print(f"  {stype:12s}: {len(prof):>4}/{len(subset)} profitable | Best: {best['name']} -> ${best['net_profit']:+.2f}")

    # Save full results to file
    out_path = Path(__file__).parent / "research" / "sweep-results.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Strategy Sweep Results\n\n")
        f.write(f"Capital: ${CAPITAL} | Maker: {MAKER_FEE*100:.2f}% | Taker: {TAKER_FEE*100:.2f}%\n")
        f.write(f"Total backtests: {len(all_results)}\n")
        f.write(f"Profitable: {len(profitable)}/{len(all_results)}\n\n")

        f.write("## TOP 20\n\n")
        f.write(f"| # | Strategy | Net$ | Gross$ | Fees$ | Trades | Win% | MaxDD% | Sharpe | PF |\n")
        f.write(f"|---|----------|------|--------|-------|--------|------|--------|--------|----|\n")
        for i, r in enumerate(all_results[:20]):
            pf_str = f"{r['profit_factor']:.2f}" if r['profit_factor'] < 1e6 else "inf"
            f.write(f"| {i+1} | {r['name']} | {r['net_profit']:+.2f} | {r['total_profit']:+.2f} | {r['total_fees']:.2f} | {r['trades']} | {r['win_rate']*100:.1f}% | {r['max_drawdown']*100:.2f}% | {r['sharpe']:.2f} | {pf_str} |\n")

        f.write("\n## ALL RESULTS (sorted by net profit)\n\n")
        f.write(f"| # | Strategy | Net$ | Trades | Win% | MaxDD% | Sharpe | PF |\n")
        f.write(f"|---|----------|------|--------|------|--------|--------|----|\n")
        for i, r in enumerate(all_results):
            pf_str = f"{r['profit_factor']:.2f}" if r['profit_factor'] < 1e6 else "inf"
            f.write(f"| {i+1} | {r['name']} | {r['net_profit']:+.2f} | {r['trades']} | {r['win_rate']*100:.1f}% | {r['max_drawdown']*100:.2f}% | {r['sharpe']:.2f} | {pf_str} |\n")

        # Recommendation
        best = all_results[0]
        f.write(f"\n## RECOMMENDATION\n\n")
        f.write(f"**Deploy: {best['name']}**\n\n")
        f.write(f"- Net Profit: ${best['net_profit']:+.2f}\n")
        f.write(f"- Win Rate: {best['win_rate']*100:.1f}%\n")
        f.write(f"- Max Drawdown: {best['max_drawdown']*100:.2f}%\n")
        f.write(f"- Sharpe Ratio: {best['sharpe']:.2f}\n")
        f.write(f"- Profit Factor: {best['profit_factor']:.2f}\n")
        f.write(f"- Total Trades: {best['trades']}\n")

    print(f"\nFull results saved to: {out_path}")

    # Final recommendation
    best = all_results[0]
    print()
    print("=" * 80)
    print("  RECOMMENDATION: THE STRATEGY TO DEPLOY")
    print("=" * 80)
    print(f"  {best['name']}")
    print(f"  Net Profit:    ${best['net_profit']:+.2f} (on ${CAPITAL} capital)")
    print(f"  Return:        {best['net_profit']/CAPITAL*100:+.1f}%")
    print(f"  Win Rate:      {best['win_rate']*100:.1f}%")
    print(f"  Max Drawdown:  {best['max_drawdown']*100:.2f}%")
    print(f"  Sharpe Ratio:  {best['sharpe']:.2f}")
    print(f"  Profit Factor: {best['profit_factor']:.2f}")
    print(f"  Total Trades:  {best['trades']}")
    print("=" * 80)


if __name__ == "__main__":
    main()

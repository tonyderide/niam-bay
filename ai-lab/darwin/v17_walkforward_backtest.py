"""
v17 Strategy Walk-Forward Backtest
Cycle 59 — 2026-05-18 12h Paris

Cycle 58 backtest used a buggy simulator (short-side PnL accounting wrong).
Cycle 59 fixes the simulator (see ppt_pause_backtest.py GridState._record_fill
rewrite) and runs walk-forward across 4 regime windows.

Question: Tony's choice of spacing 3.0% for v17 — does it hold across regimes,
or was it artifact of buggy 30d backtest?

Windows (LINK + ADA + ETH 1min Binance):
  W1 = 2024-03-01 → 2024-04-30 (60j)  — Bear
  W2 = 2024-10-01 → 2024-12-31 (91j)  — Strong Bull
  W3 = 2025-02-01 → 2025-03-31 (58j)  — Strong Bear
  W4 = 2026-04-12 → 2026-05-12 (30j)  — Mild Bull (recent)

5 configs:
  A) v17 Tony 3.0% / 4 levels
  B) v17 tight 1.5% / 4 levels
  C) v17 med 2.0% / 4 levels
  D) v17 wide 4.0% / 4 levels
  E) v17 6lv 2.0% / 6 levels

Output: heatmap [config × window] of mean PnL across pairs, plus stop count.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict

ROOT = Path("/home/tony/projets/tonyderide/niam-bay")
CACHE = ROOT / "ai-lab/darwin/data_cache"
sys.path.insert(0, str(ROOT / "ai-lab/darwin"))

from ppt_pause_backtest import GridState, load_candles
from v17_strategy_backtest import run_grid_no_pause


WINDOWS = [
    ("W1 bear 60j",   "1709251200000_1714435200000", "2024-03-01"),
    ("W2 bull 91j",   "1727740800000_1735603200000", "2024-10-01"),
    ("W3 bear 58j",   "1738368000000_1743379200000", "2025-02-01"),
    ("W4 mild+ 30j",  "30d",                          "2026-04-12"),
]

PAIRS = ["LINK", "ADA", "ETH"]

CONFIGS = [
    ("A v17 Tony 3.0%",  3.0,  4),
    ("B v17 tight 1.5%", 1.5,  4),
    ("C v17 med 2.0%",   2.0,  4),
    ("D v17 wide 4.0%",  4.0,  4),
    ("E v17 6lv 2.0%",   2.0,  6),
]


def path_for(pair: str, window_suffix: str) -> Path:
    return CACHE / f"binance_{pair}USDT_1min_{window_suffix}.json"


def main():
    print("=" * 84)
    print("V17 STRATEGY WALK-FORWARD BACKTEST — Cycle 59 — 2026-05-18")
    print("Simulator with cycle 59 fix (short-side _record_fill rewrite)")
    print(f"Grid params: $25 cap, 7x lev, maxLoss 10%, NEUTRAL, no gate, no pause")
    print("=" * 84)

    # results[config][window] = {pair: pnl}
    results = {cfg[0]: {w[0]: {} for w in WINDOWS} for cfg in CONFIGS}
    stops = {cfg[0]: {w[0]: 0 for w in WINDOWS} for cfg in CONFIGS}
    pair_change = {pair: {w[0]: 0.0 for w in WINDOWS} for pair in PAIRS}

    for win_name, suffix, start_date in WINDOWS:
        print(f"\n--- {win_name} (start {start_date}) ---")
        for pair in PAIRS:
            path = path_for(pair, suffix)
            candles = load_candles(path)
            if not candles:
                print(f"  {pair}: MISSING {path.name}")
                continue
            first = candles[0][4]
            last = candles[-1][4]
            chg = (last - first) / first * 100
            pair_change[pair][win_name] = chg
            print(f"  {pair}: {len(candles)} candles, "
                  f"{round((candles[-1][0]-candles[0][0])/86400_000,1)}j, "
                  f"price {chg:+.1f}%")
            for label, spacing, lvls in CONFIGS:
                r = run_grid_no_pause(candles, spacing / 100.0, lvls)
                pnl = r.get("total_pnl", 0.0)
                results[label][win_name][pair] = pnl
                if r.get("stopped"):
                    stops[label][win_name] += 1
                tag = "STOP" if r.get("stopped") else "ok  "
                print(f"     {label:18s}: PnL=${pnl:+7.3f} "
                      f"fills={r.get('fills',0):2d} maxDD={r.get('max_drawdown_pct',0):5.2f}% [{tag}]")

    # heatmap: rows = configs, cols = windows, cell = sum PnL across 3 pairs
    print("\n" + "=" * 84)
    print("HEATMAP — ΣPnL across 3 pairs (LINK+ADA+ETH) per (config × window)")
    print("=" * 84)
    header = f"{'config':<18}|" + "|".join(f"{w[0]:>14s}" for w in WINDOWS) + "|" + f"{'TOTAL':>10s}"
    print(header)
    print("-" * len(header))
    config_totals = {}
    for label, _, _ in CONFIGS:
        row = f"{label:<18}|"
        total = 0.0
        for w in WINDOWS:
            wn = w[0]
            s = sum(results[label][wn].values())
            sc = stops[label][wn]
            cell = f"${s:+7.2f} ({sc}st)"
            row += f"{cell:>14s}|"
            total += s
        config_totals[label] = total
        row += f" ${total:+8.2f}"
        print(row)

    # also print per-pair direction reference
    print("\n" + "=" * 84)
    print("REGIME REFERENCE — price change per (pair × window)")
    print("=" * 84)
    print(f"{'pair':<6}|" + "|".join(f"{w[0]:>14s}" for w in WINDOWS))
    for pair in PAIRS:
        row = f"{pair:<6}|"
        for w in WINDOWS:
            row += f"{pair_change[pair][w[0]]:>+13.1f}%|"
        print(row)

    # final ranking by TOTAL across all windows
    print("\n" + "=" * 84)
    print("FINAL RANKING by total PnL across all 4 windows × 3 pairs (~239 days):")
    print("=" * 84)
    ranked = sorted(config_totals.items(), key=lambda kv: -kv[1])
    for i, (label, t) in enumerate(ranked, 1):
        marker = "  ← Tony v17" if "Tony" in label else ""
        print(f"  {i}. {label:<18}  ${t:+8.2f}{marker}")

    # variance check: rank stability across windows
    print("\n" + "=" * 84)
    print("STABILITY — rank of each config per window (1=best, 5=worst)")
    print("=" * 84)
    print(f"{'config':<18}|" + "|".join(f"{w[0]:>14s}" for w in WINDOWS) + "|  meanRank")
    cfg_ranks = {label: [] for label, _, _ in CONFIGS}
    for w in WINDOWS:
        wn = w[0]
        sums = [(label, sum(results[label][wn].values())) for label, _, _ in CONFIGS]
        sums.sort(key=lambda kv: -kv[1])  # best first
        for rank_idx, (label, _) in enumerate(sums, 1):
            cfg_ranks[label].append(rank_idx)
    for label, _, _ in CONFIGS:
        ranks = cfg_ranks[label]
        mean_rank = sum(ranks) / len(ranks)
        row = f"{label:<18}|" + "|".join(f"{r:>14d}" for r in ranks) + f"|  {mean_rank:.2f}"
        print(row)

    print("\nINTERPRETATION:")
    print("- Best total PnL across regimes = most robust spacing.")
    print("- Lowest mean rank = most consistently top.")
    print("- High stop count across windows = config breaks easily in trends.")
    print("- NEUTRAL grid in any strong trend loses by design; gate (not modeled")
    print("  here) is what saves the bot in production.")


if __name__ == "__main__":
    main()

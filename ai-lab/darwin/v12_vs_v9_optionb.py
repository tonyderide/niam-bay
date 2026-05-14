#!/usr/bin/env python3
"""V12 (3%) vs V9 (1.5%) on the exact Option B failure window — cycle 39.

The question cycle 38 left open: would a wider grid (V12's 3% spacing)
have survived the DOT cascade that killed Option B v9 (1.5% spacing)?

Replay the same window (2026-05-11 13:00 UTC -> 2026-05-12 22:00 UTC)
on DOT 1min, comparing:
  - v9_config  : 1.5% spacing, 4 levels, $46 cap, 7x lev, maxLoss 10%
  - v12_config : 3.0% spacing, 4 levels, $25 cap, 7x lev, maxLoss 10%
  - v12_50cap  : same v12 but $50 cap (matches Option B exposure)

Same auto-unstuck logic (2/3/4%) — but the trim thresholds are independent
of spacing, so v12 grids only trim when price drops 2/3/4% from a center
that is itself a wider envelope. In practice: v12 trims fire when price
is already outside the first buy level.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "data_cache"
OPTIONB_FILE = CACHE_DIR / "binance_DOTUSDT_1min_optionb.json"

FEE_RT_PCT = 0.08
UNSTUCK_LVL1_PCT = 2.0
UNSTUCK_LVL2_PCT = 3.0
UNSTUCK_FULL_PCT = 4.0


def simulate(candles, spacing_pct, levels, capital, leverage, max_loss_pct):
    notional_total = capital * leverage
    notional_per_level = notional_total / levels
    max_loss_usd = capital * max_loss_pct / 100.0

    center = candles[0][4]
    level_prices = []
    for k in range(levels):
        offset = (k - levels / 2 + 0.5) * spacing_pct / 100.0
        level_prices.append(center * (1 + offset))

    position_size = 0.0
    entry_avg = 0.0
    realized = 0.0
    level_filled = [False] * levels
    sell_armed = [False] * levels
    unstuck1_done = False
    unstuck2_done = False
    hard_stop = False
    full_close = False
    trims = []
    rt_count = 0
    upnl_max_neg = 0.0

    for bar in candles:
        ts, o, h, l, c, _ = bar
        if hard_stop or full_close:
            break

        if position_size > 0:
            upnl = position_size * (c - entry_avg) - position_size * c * FEE_RT_PCT / 200.0
            if upnl < upnl_max_neg:
                upnl_max_neg = upnl
            if upnl <= -max_loss_usd:
                realized += upnl
                position_size = 0.0
                hard_stop = True
                break

            drop_pct = (center - c) / center * 100.0
            if not unstuck1_done and drop_pct >= UNSTUCK_LVL1_PCT:
                trim_size = position_size * 0.25
                pnl = trim_size * (c - entry_avg) - trim_size * c * FEE_RT_PCT / 200.0
                realized += pnl
                position_size -= trim_size
                unstuck1_done = True
                trims.append(("lvl1", drop_pct, pnl))
            elif unstuck1_done and not unstuck2_done and drop_pct >= UNSTUCK_LVL2_PCT:
                trim_size = position_size * 0.25
                pnl = trim_size * (c - entry_avg) - trim_size * c * FEE_RT_PCT / 200.0
                realized += pnl
                position_size -= trim_size
                unstuck2_done = True
                trims.append(("lvl2", drop_pct, pnl))
            elif unstuck2_done and drop_pct >= UNSTUCK_FULL_PCT:
                pnl = position_size * (c - entry_avg) - position_size * c * FEE_RT_PCT / 200.0
                realized += pnl
                trims.append(("full", drop_pct, pnl))
                position_size = 0.0
                full_close = True
                break

        n_buys = levels // 2
        for i in range(n_buys):
            if level_filled[i]:
                continue
            if l <= level_prices[i]:
                fill_price = level_prices[i]
                size = notional_per_level / fill_price
                new_total = position_size + size
                entry_avg = (entry_avg * position_size + fill_price * size) / new_total
                position_size = new_total
                level_filled[i] = True
                sell_armed[i + n_buys] = True

        for i in range(n_buys, levels):
            if not sell_armed[i]:
                continue
            if h >= level_prices[i] and position_size > 0:
                fill_price = level_prices[i]
                buy_idx = i - n_buys
                buy_size = notional_per_level / level_prices[buy_idx]
                size = min(buy_size, position_size)
                pnl = size * (fill_price - entry_avg) - size * fill_price * FEE_RT_PCT / 200.0
                realized += pnl
                position_size -= size
                sell_armed[i] = False
                level_filled[buy_idx] = False
                rt_count += 1

    if position_size > 0 and not hard_stop and not full_close:
        last_price = candles[-1][4]
        pnl = position_size * (last_price - entry_avg) - position_size * last_price * FEE_RT_PCT / 200.0
        realized += pnl

    return {
        "spacing_pct": spacing_pct,
        "capital": capital,
        "realized_pnl_usd": round(realized, 4),
        "realized_pnl_pct_cap": round(realized / capital * 100, 2),
        "hard_stop": hard_stop,
        "full_close": full_close,
        "rt_count": rt_count,
        "trim_count": len(trims),
        "trims": trims,
        "upnl_max_neg": round(upnl_max_neg, 4),
        "center": round(center, 5),
        "lowest_level": round(min(level_prices), 5),
    }


def main():
    print("V12 (3%) vs V9 (1.5%) — Option B replay on DOT")
    print("Window: 2026-05-11 13:00 -> 2026-05-12 22:00 UTC (50h)")
    print()

    candles = json.load(open(OPTIONB_FILE))
    print(f"Loaded {len(candles)} candles ({(candles[-1][0]-candles[0][0])/3600000:.1f}h)")
    print(f"Price range: ${min(c[3] for c in candles):.4f} -> ${max(c[2] for c in candles):.4f}")
    print(f"DOT close at t0: ${candles[0][4]:.4f} | DOT close at end: ${candles[-1][4]:.4f}")
    print()

    configs = [
        ("v9_1.5%_$46",  1.5, 4, 46.0, 7, 10),
        ("v12_3.0%_$25", 3.0, 4, 25.0, 7, 10),
        ("v12_3.0%_$50", 3.0, 4, 50.0, 7, 10),
        ("v12_3.0%_$46", 3.0, 4, 46.0, 7, 10),
        ("wide_5.0%_$46", 5.0, 4, 46.0, 7, 10),
        ("wide_7.0%_$46", 7.0, 4, 46.0, 7, 10),
    ]

    results = []
    for label, spacing, levels, cap, lev, ml in configs:
        r = simulate(candles, spacing, levels, cap, lev, ml)
        r["label"] = label
        results.append(r)
        print(f"\n{label}:")
        print(f"  spacing={spacing}% cap=${cap} max_loss=${cap*ml/100:.2f}")
        print(f"  center=${r['center']:.4f} lowest_buy=${r['lowest_level']:.4f}")
        print(f"  realized=${r['realized_pnl_usd']:+.4f} ({r['realized_pnl_pct_cap']:+.2f}% cap)")
        print(f"  uPnL_max_neg=${r['upnl_max_neg']:+.4f}")
        print(f"  RT={r['rt_count']} trims={r['trim_count']} "
              f"HARD_STOP={r['hard_stop']} FULL_CLOSE={r['full_close']}")
        for t in r["trims"]:
            print(f"    trim {t[0]}: drop={t[1]:.2f}% pnl=${t[2]:+.4f}")

    print("\n=== COMPARATIVE ===")
    print(f"  {'config':>15} | {'PnL $':>9} | {'%cap':>7} | {'RT':>3} | {'trims':>5} | {'HS':>3} | {'FC':>3} | {'maxNegUPnL':>11}")
    for r in results:
        print(f"  {r['label']:>15} | ${r['realized_pnl_usd']:>+7.4f} | "
              f"{r['realized_pnl_pct_cap']:>+6.2f}% | "
              f"{r['rt_count']:>3} | {r['trim_count']:>5} | "
              f"{'Y' if r['hard_stop'] else 'N':>3} | "
              f"{'Y' if r['full_close'] else 'N':>3} | "
              f"${r['upnl_max_neg']:>+9.4f}")

    out = Path(__file__).parent / "v12_vs_v9_results.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\nResults: {out}")


if __name__ == "__main__":
    main()

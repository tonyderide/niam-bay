#!/usr/bin/env python3
"""V12 multi-pair backtest with optional trend filter (cycle 39).

Validates Tony's current deploy v12 (LINK+ADA+LTC+ATOM+AVAX, 5 grids
$25 each, 3% spacing, 7x lev, maxLoss 10%, auto-unstuck progressive)
on 30d of 1min OHLC and tests whether adding the cycle 38-recommended
EMA-spread trend filter would have improved outcomes.

Two questions:
  Q1. Does v12 survive a 30d replay (includes Option B failure window)?
  Q2. Would an EMA50/EMA200 spread filter (skip grid open when spread
      magnitude > T%) have prevented losses, especially the DOT-style
      cascade in strong downtrends?

The grid restarts after every HARD STOP or full close (auto-relaunch
behavior). With the filter, restart is delayed until spread normalizes.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from collections import deque

CACHE_DIR = Path(__file__).parent / "data_cache"

# V12 per-pair config (from /home/ubuntu/martin/config/strategy.json)
V12_CONFIG = {
    "LINKUSDT": {"spacing_pct": 3.0, "levels": 4, "cap": 25.0, "lev": 7, "max_loss_pct": 10},
    "ADAUSDT":  {"spacing_pct": 3.0, "levels": 4, "cap": 25.0, "lev": 7, "max_loss_pct": 10},
    "LTCUSDT":  {"spacing_pct": 3.0, "levels": 4, "cap": 25.0, "lev": 7, "max_loss_pct": 10},
    "ATOMUSDT": {"spacing_pct": 2.0, "levels": 4, "cap": 25.0, "lev": 7, "max_loss_pct": 10},
    "AVAXUSDT": {"spacing_pct": 3.0, "levels": 4, "cap": 25.0, "lev": 7, "max_loss_pct": 10},
}

FEE_RT_PCT = 0.08          # 0.04% per side x 2 (Kraken Futures taker approx)
UNSTUCK_LVL1_PCT = 2.0
UNSTUCK_LVL2_PCT = 3.0
UNSTUCK_FULL_PCT = 4.0
EMA_SHORT = 50
EMA_LONG = 200
# Spread = (ema_short - ema_long) / ema_long * 100. Positive = uptrend, negative = downtrend.


def compute_emas(candles):
    """Compute EMA_50 and EMA_200 of close price across the candle series."""
    closes = [c[4] for c in candles]
    ema50 = [None] * len(closes)
    ema200 = [None] * len(closes)
    k50 = 2.0 / (EMA_SHORT + 1)
    k200 = 2.0 / (EMA_LONG + 1)
    e50, e200 = None, None
    for i, p in enumerate(closes):
        if i == 0:
            e50 = p
            e200 = p
        else:
            e50 = p * k50 + e50 * (1 - k50)
            e200 = p * k200 + e200 * (1 - k200)
        if i >= EMA_SHORT:
            ema50[i] = e50
        if i >= EMA_LONG:
            ema200[i] = e200
    return ema50, ema200


def simulate_pair(candles, cfg, trend_filter_pct=None, ema_short=None, ema_long=None):
    """Simulate a single pair grid across the candle series.

    trend_filter_pct: if not None, skip starting/restarting a grid when
                     |ema50-ema200|/ema200 * 100 > trend_filter_pct
    Returns dict with realized_pnl, hard_stop_count, full_close_count,
    rt_count, trim_count, blocks_due_to_filter, grids_started.
    """
    spacing = cfg["spacing_pct"]
    levels = cfg["levels"]
    capital = cfg["cap"]
    leverage = cfg["lev"]
    max_loss_usd = capital * cfg["max_loss_pct"] / 100.0
    notional_total = capital * leverage
    notional_per_level = notional_total / levels

    state = {
        "active": False,
        "center": 0.0,
        "level_prices": [],
        "position_size": 0.0,
        "entry_avg": 0.0,
        "level_filled": [False] * levels,
        "sell_armed": [False] * levels,
        "unstuck1_done": False,
        "unstuck2_done": False,
    }

    realized = 0.0
    rt_count = 0
    trim_count = 0
    hard_stop_count = 0
    full_close_count = 0
    blocks = 0
    grids_started = 0
    last_close_idx = -1  # bar index after which a new grid can start

    def start_grid(price):
        state["active"] = True
        state["center"] = price
        state["level_prices"] = []
        for k in range(levels):
            offset = (k - levels / 2 + 0.5) * spacing / 100.0
            state["level_prices"].append(price * (1 + offset))
        state["position_size"] = 0.0
        state["entry_avg"] = 0.0
        state["level_filled"] = [False] * levels
        state["sell_armed"] = [False] * levels
        state["unstuck1_done"] = False
        state["unstuck2_done"] = False

    for idx, bar in enumerate(candles):
        ts, o, h, l, c, _ = bar

        # Wait for warmup if filter requested
        if trend_filter_pct is not None and idx <= EMA_LONG:
            continue

        # Start a new grid if not active
        if not state["active"]:
            # Apply trend filter if requested
            if trend_filter_pct is not None:
                e50 = ema_short[idx]
                e200 = ema_long[idx]
                if e50 is None or e200 is None:
                    continue
                spread_pct = (e50 - e200) / e200 * 100.0
                if abs(spread_pct) > trend_filter_pct:
                    blocks += 1
                    continue
            start_grid(c)
            grids_started += 1
            continue

        # Active grid logic
        # 1. HARD STOP check (uPnL on close)
        if state["position_size"] > 0:
            upnl = state["position_size"] * (c - state["entry_avg"])
            upnl -= state["position_size"] * c * FEE_RT_PCT / 200.0
            if upnl <= -max_loss_usd:
                realized += upnl
                state["position_size"] = 0.0
                state["active"] = False
                hard_stop_count += 1
                last_close_idx = idx
                continue

            # 2. Auto-unstuck (drop_pct from center)
            drop_pct = (state["center"] - c) / state["center"] * 100.0
            if not state["unstuck1_done"] and drop_pct >= UNSTUCK_LVL1_PCT:
                trim_size = state["position_size"] * 0.25
                pnl = trim_size * (c - state["entry_avg"]) - trim_size * c * FEE_RT_PCT / 200.0
                realized += pnl
                state["position_size"] -= trim_size
                state["unstuck1_done"] = True
                trim_count += 1
            elif state["unstuck1_done"] and not state["unstuck2_done"] and drop_pct >= UNSTUCK_LVL2_PCT:
                trim_size = state["position_size"] * 0.25
                pnl = trim_size * (c - state["entry_avg"]) - trim_size * c * FEE_RT_PCT / 200.0
                realized += pnl
                state["position_size"] -= trim_size
                state["unstuck2_done"] = True
                trim_count += 1
            elif state["unstuck2_done"] and drop_pct >= UNSTUCK_FULL_PCT:
                pnl = state["position_size"] * (c - state["entry_avg"])
                pnl -= state["position_size"] * c * FEE_RT_PCT / 200.0
                realized += pnl
                state["position_size"] = 0.0
                state["active"] = False
                full_close_count += 1
                last_close_idx = idx
                continue

        # 3. Process buy fills (lower half levels)
        n_buys = levels // 2
        for i in range(n_buys):
            if state["level_filled"][i]:
                continue
            if l <= state["level_prices"][i]:
                fill_price = state["level_prices"][i]
                size = notional_per_level / fill_price
                new_total = state["position_size"] + size
                state["entry_avg"] = (
                    state["entry_avg"] * state["position_size"] + fill_price * size
                ) / new_total
                state["position_size"] = new_total
                state["level_filled"][i] = True
                state["sell_armed"][i + n_buys] = True

        # 4. Process sell fills (upper half levels)
        for i in range(n_buys, levels):
            if not state["sell_armed"][i]:
                continue
            if h >= state["level_prices"][i] and state["position_size"] > 0:
                fill_price = state["level_prices"][i]
                buy_idx = i - n_buys
                buy_size = notional_per_level / state["level_prices"][buy_idx]
                size = min(buy_size, state["position_size"])
                pnl = size * (fill_price - state["entry_avg"]) - size * fill_price * FEE_RT_PCT / 200.0
                realized += pnl
                state["position_size"] -= size
                state["sell_armed"][i] = False
                state["level_filled"][buy_idx] = False
                rt_count += 1

    # End: close any residual position at last close
    if state["active"] and state["position_size"] > 0:
        last_price = candles[-1][4]
        pnl = state["position_size"] * (last_price - state["entry_avg"])
        pnl -= state["position_size"] * last_price * FEE_RT_PCT / 200.0
        realized += pnl

    return {
        "realized_pnl_usd": round(realized, 4),
        "realized_pnl_pct_cap": round(realized / capital * 100, 2),
        "hard_stop_count": hard_stop_count,
        "full_close_count": full_close_count,
        "rt_count": rt_count,
        "trim_count": trim_count,
        "grids_started": grids_started,
        "blocks_by_filter": blocks,
    }


def run_scenario(label, trend_filter_pct):
    pair_results = {}
    portfolio_pnl = 0.0
    portfolio_cap = 0.0
    for symbol, cfg in V12_CONFIG.items():
        f = CACHE_DIR / f"binance_{symbol}_1min_30d.json"
        candles = json.load(open(f))
        ema50, ema200 = (None, None)
        if trend_filter_pct is not None:
            ema50, ema200 = compute_emas(candles)
        r = simulate_pair(candles, cfg, trend_filter_pct, ema50, ema200)
        pair_results[symbol] = r
        portfolio_pnl += r["realized_pnl_usd"]
        portfolio_cap += cfg["cap"]
    return {
        "label": label,
        "trend_filter_pct": trend_filter_pct,
        "portfolio_pnl_usd": round(portfolio_pnl, 4),
        "portfolio_pnl_pct_cap": round(portfolio_pnl / portfolio_cap * 100, 2),
        "portfolio_cap": portfolio_cap,
        "per_pair": pair_results,
    }


def main():
    print("V12 multi-pair backtest — cycle 39 / 2026-05-13")
    print("Config: LINK+ADA+LTC+AVAX 3.0% / ATOM 2.0% — $25 cap × 7x lev × 4 levels — maxLoss 10%")
    print(f"Window: 30d 1min (covers Option B failure 11-12/05)")
    print()

    scenarios = [
        ("baseline_no_filter", None),
        ("filter_1.0pct", 1.0),
        ("filter_1.5pct", 1.5),
        ("filter_2.0pct", 2.0),
        ("filter_2.5pct", 2.5),
        ("filter_3.0pct", 3.0),
    ]

    all_results = []
    for label, tf in scenarios:
        r = run_scenario(label, tf)
        all_results.append(r)
        print(f"\n{label} (filter={tf}%) → portfolio "
              f"${r['portfolio_pnl_usd']:+.2f} "
              f"({r['portfolio_pnl_pct_cap']:+.2f}% of ${r['portfolio_cap']:.0f} cap)")
        for sym, pr in r["per_pair"].items():
            print(f"  {sym:10s} ${pr['realized_pnl_usd']:+8.4f} "
                  f"({pr['realized_pnl_pct_cap']:+6.2f}% cap) "
                  f"grids={pr['grids_started']:3d} hs={pr['hard_stop_count']} "
                  f"fc={pr['full_close_count']} RT={pr['rt_count']:3d} "
                  f"trims={pr['trim_count']:3d} blocks={pr['blocks_by_filter']:5d}")

    print("\n=== COMPARATIVE TABLE ===")
    print(f"  {'label':>20}  {'filter':>7}  {'pnl_usd':>10}  {'pnl%cap':>9}  {'blocks_total':>13}")
    for r in all_results:
        blocks_total = sum(p["blocks_by_filter"] for p in r["per_pair"].values())
        f = "none" if r["trend_filter_pct"] is None else f"{r['trend_filter_pct']:.1f}%"
        print(f"  {r['label']:>20}  {f:>7}  ${r['portfolio_pnl_usd']:>+9.2f}  "
              f"{r['portfolio_pnl_pct_cap']:>+8.2f}%  {blocks_total:>13d}")

    baseline = all_results[0]
    print(f"\n=== DELTA vs baseline ===")
    for r in all_results[1:]:
        delta = r["portfolio_pnl_usd"] - baseline["portfolio_pnl_usd"]
        verdict = "GAIN" if delta > 0.05 else ("EQUAL" if abs(delta) <= 0.05 else "LOSS")
        print(f"  {r['label']:>20}: delta={delta:+.4f}$ ({verdict} vs no_filter)")

    out_path = Path(__file__).parent / "v12_backtest_results.json"
    out_path.write_text(json.dumps(all_results, indent=2))
    print(f"\nResults saved: {out_path}")


if __name__ == "__main__":
    main()

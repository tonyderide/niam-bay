"""
Post-stop naked position analyzer — Cycle 41 follow-up to Cycle 40 proposal.

Question: When AutoGrid stops a grid on regime break and leaves residual
positions naked, which exit strategy maximizes expected PnL?

Three strategies tested at each EMA200-break-with-RSI-oversold event:
  Option 1 — HOLD: do nothing, exit at +24h mark
  Option 2 — MARKET CLOSE: close immediately at event price (taker fee 0.04%)
  Option 3 — TIGHT SL X%: place SL at -X% from event price; if hit within 24h
            realize -X%, else hold to +24h. Tested for X in {0.5, 1.0, 1.5, 2.0}.

All returns expressed as pct of notional. Includes Kraken-Futures-typical
fees:
  - Taker fee: 0.04% per side (0.08% RT)
  - We model the "exit" trade only; the entry already happened pre-event.

Reuses event detection from ema200_break_analyzer.py (67 events, 30d window).

Output: per-strategy PnL distribution + decision matrix.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data_cache"
BTC = DATA_DIR / "binance_BTCUSDT_1min_30d.json"

HORIZON_MIN = 1440          # exit at +24h if nothing else triggers
RSI_OVERSOLD = 30
PERSIST_BARS = 5
EVENT_GAP = 240
TAKER_FEE_PCT = 0.04        # Kraken Futures taker
SLIPPAGE_PCT = 0.02         # extra cost when SL fires (worst tick)

SL_LEVELS_PCT = [0.5, 1.0, 1.5, 2.0]


def load(path):
    with open(path) as f:
        return json.load(f)


def ema(values, period):
    k = 2.0 / (period + 1)
    out = [None] * len(values)
    if len(values) < period:
        return out
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    for i in range(period, len(values)):
        out[i] = values[i] * k + out[i - 1] * (1 - k)
    return out


def rsi(values, period=14):
    out = [None] * len(values)
    if len(values) < period + 1:
        return out
    gains, losses = [], []
    for i in range(1, period + 1):
        d = values[i] - values[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        out[period] = 100
    else:
        rs = avg_gain / avg_loss
        out[period] = 100 - 100 / (1 + rs)
    for i in range(period + 1, len(values)):
        d = values[i] - values[i - 1]
        g = max(d, 0)
        l = max(-d, 0)
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
        if avg_loss == 0:
            out[i] = 100
        else:
            rs = avg_gain / avg_loss
            out[i] = 100 - 100 / (1 + rs)
    return out


def find_events(closes, ema200_vals, rsi_vals):
    events = []
    last_event_idx = -EVENT_GAP - 1
    n = len(closes)
    for i in range(200, n - HORIZON_MIN - 1):
        if ema200_vals[i] is None or ema200_vals[i - 1] is None:
            continue
        if rsi_vals[i] is None:
            continue
        crossed = closes[i - 1] >= ema200_vals[i - 1] and closes[i] < ema200_vals[i]
        if not crossed:
            continue
        confirmed = all(
            closes[i + k] < ema200_vals[i + k]
            for k in range(PERSIST_BARS)
        )
        if not confirmed:
            continue
        rsi_window = [rsi_vals[i + k] for k in range(PERSIST_BARS) if rsi_vals[i + k] is not None]
        if not rsi_window or min(rsi_window) > RSI_OVERSOLD:
            continue
        if i - last_event_idx < EVENT_GAP:
            continue
        last_event_idx = i
        events.append(i)
    return events


def simulate_hold(closes, idx, horizon):
    """Exit at +horizon, taker fee at close."""
    p0 = closes[idx]
    p_exit = closes[idx + horizon]
    gross_pct = (p_exit - p0) / p0 * 100
    return gross_pct - TAKER_FEE_PCT


def simulate_close(closes, idx):
    """Close at event price (with taker fee)."""
    return -TAKER_FEE_PCT


def simulate_tight_sl(closes, idx, horizon, sl_pct):
    """Place sell-stop at p0 * (1 - sl_pct/100). If low touches SL → exit at
    SL minus slippage. Else hold to horizon."""
    p0 = closes[idx]
    sl_price = p0 * (1 - sl_pct / 100)
    for k in range(1, horizon + 1):
        if closes[idx + k] <= sl_price:
            # SL triggered; effective exit = sl_price * (1 - slippage/100)
            exit_price = sl_price * (1 - SLIPPAGE_PCT / 100)
            gross_pct = (exit_price - p0) / p0 * 100
            return gross_pct - TAKER_FEE_PCT
    # Never triggered: hold to horizon
    p_exit = closes[idx + horizon]
    gross_pct = (p_exit - p0) / p0 * 100
    return gross_pct - TAKER_FEE_PCT


def stats(values):
    vals = sorted([v for v in values if v is not None])
    if not vals:
        return None
    n = len(vals)
    mean = sum(vals) / n
    median = vals[n // 2]
    pct_positive = sum(1 for v in vals if v > 0) / n * 100
    p10 = vals[max(0, n // 10)]
    p90 = vals[min(n - 1, 9 * n // 10)]
    worst5 = sum(vals[:max(1, n // 20)]) / max(1, n // 20)
    return {
        "n": n,
        "mean_pct": round(mean, 3),
        "median_pct": round(median, 3),
        "pct_positive": round(pct_positive, 1),
        "min_pct": round(vals[0], 3),
        "max_pct": round(vals[-1], 3),
        "p10": round(p10, 3),
        "p90": round(p90, 3),
        "worst5_mean": round(worst5, 3),
    }


def main():
    print("Loading BTC 30d 1min cache...")
    raw = load(BTC)
    closes = [bar[4] for bar in raw]
    timestamps = [bar[0] for bar in raw]
    print(f"  {len(closes)} 1-min candles")

    print("Computing EMA200 + RSI14...")
    ema200_vals = ema(closes, 200)
    rsi_vals = rsi(closes, 14)

    print(f"Finding events...")
    events = find_events(closes, ema200_vals, rsi_vals)
    print(f"  {len(events)} qualifying events")

    if not events:
        print("No events. Abort.")
        return

    strategies = {}

    # Option 1: HOLD
    hold = [simulate_hold(closes, idx, HORIZON_MIN) for idx in events]
    strategies["1_HOLD_24h"] = hold

    # Option 2: MARKET CLOSE
    close = [simulate_close(closes, idx) for idx in events]
    strategies["2_MARKET_CLOSE"] = close

    # Option 3: TIGHT SL (multiple levels)
    for sl_pct in SL_LEVELS_PCT:
        key = f"3_SL_{sl_pct}pct"
        strategies[key] = [simulate_tight_sl(closes, idx, HORIZON_MIN, sl_pct) for idx in events]

    print("\nPer-strategy PnL distribution (% of notional, includes fees + slippage):")
    print(f"{'strategy':>20} {'n':>4} {'mean':>8} {'median':>8} {'pos%':>6} {'p10':>8} {'p90':>8} {'min':>8} {'worst5':>8}")
    results = {}
    for name, vals in strategies.items():
        s = stats(vals)
        results[name] = s
        print(f"{name:>20} {s['n']:>4} {s['mean_pct']:>8} {s['median_pct']:>8} "
              f"{s['pct_positive']:>6} {s['p10']:>8} {s['p90']:>8} {s['min_pct']:>8} {s['worst5_mean']:>8}")

    # Decision matrix: rank by mean, by p10 (worst-case appetite)
    print("\nRanking by mean expected return:")
    by_mean = sorted(results.items(), key=lambda x: -x[1]["mean_pct"])
    for i, (name, s) in enumerate(by_mean, 1):
        print(f"  {i}. {name:<20} mean={s['mean_pct']:+.3f}%  worst5={s['worst5_mean']:+.3f}%")

    print("\nRanking by worst-5% (tail risk minimization):")
    by_p10 = sorted(results.items(), key=lambda x: -x[1]["worst5_mean"])
    for i, (name, s) in enumerate(by_p10, 1):
        print(f"  {i}. {name:<20} worst5={s['worst5_mean']:+.3f}%  mean={s['mean_pct']:+.3f}%")

    # Sharpe-style return/risk per strategy
    print("\nReturn-to-risk approximation (mean / |worst5|):")
    for name, s in results.items():
        denom = abs(s["worst5_mean"]) if s["worst5_mean"] != 0 else 0.001
        ratio = s["mean_pct"] / denom
        print(f"  {name:<20} ratio={ratio:+.3f}")

    # Practical translation to current Tony situation:
    # 3 naked positions ~$135 notional total
    print("\nApplied to current uPnL -$1.55 / $135 notional (cycle 40 state):")
    notional = 135
    for name, s in results.items():
        mean_dollar = s["mean_pct"] / 100 * notional
        worst5_dollar = s["worst5_mean"] / 100 * notional
        print(f"  {name:<20} mean ${mean_dollar:+.2f}  worst5 ${worst5_dollar:+.2f}")

    # Save
    out = {
        "config": {
            "rsi_threshold": RSI_OVERSOLD,
            "horizon_min": HORIZON_MIN,
            "taker_fee_pct": TAKER_FEE_PCT,
            "slippage_pct": SLIPPAGE_PCT,
            "sl_levels_tested": SL_LEVELS_PCT,
        },
        "n_events": len(events),
        "per_strategy_stats": results,
    }
    out_path = Path(__file__).parent / "post_stop_naked_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()

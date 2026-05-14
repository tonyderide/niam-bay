"""
EMA200 break + oversold analyzer.

Question: When BTC breaks below its EMA200 with RSI in oversold zone, does it
bounce back (mean revert) or does it continue lower (trend continuation)?

This gives Tony a base rate to inform the "hold naked positions vs close
market" decision when AutoGrid stops grids on regime break.

Loads binance_BTCUSDT_1min_30d.json (~30 days of 1min OHLC), computes EMA200
and RSI14, identifies break events, and measures forward returns at multiple
horizons.

Output: empirical distribution + percentages.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data_cache"
BTC = DATA_DIR / "binance_BTCUSDT_1min_30d.json"

# Forward horizons in minutes
HORIZONS = [30, 60, 180, 360, 720, 1440]

# Break event criteria
RSI_OVERSOLD = 30       # current RSI<=30 (today's BTC = 27, stricter match)
PERSIST_BARS = 5        # must stay below EMA200 for >=5 bars (filters wicks)
EVENT_GAP = 240         # don't double-count events <240min apart


def load(path):
    with open(path) as f:
        return json.load(f)


def ema(values, period):
    """Standard EMA. Seeds with SMA(period) then EMA recursion."""
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
    """Standard Wilder RSI."""
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
    """Find moments where close crosses below EMA200 AND stays below for
    PERSIST_BARS AND RSI dips below threshold within window."""
    events = []
    last_event_idx = -EVENT_GAP - 1
    n = len(closes)
    for i in range(200, n - max(HORIZONS) - 1):
        if ema200_vals[i] is None or ema200_vals[i - 1] is None:
            continue
        if rsi_vals[i] is None:
            continue
        # Cross detection: prev close >= prev EMA200, current close < current EMA200
        crossed = closes[i - 1] >= ema200_vals[i - 1] and closes[i] < ema200_vals[i]
        if not crossed:
            continue
        # Confirm persistence: stays below for PERSIST_BARS
        confirmed = all(
            closes[i + k] < ema200_vals[i + k]
            for k in range(PERSIST_BARS)
        )
        if not confirmed:
            continue
        # RSI must hit oversold within PERSIST_BARS
        rsi_window = [rsi_vals[i + k] for k in range(PERSIST_BARS) if rsi_vals[i + k] is not None]
        if not rsi_window or min(rsi_window) > RSI_OVERSOLD:
            continue
        # De-duplicate events too close together
        if i - last_event_idx < EVENT_GAP:
            continue
        last_event_idx = i
        events.append(i)
    return events


def forward_returns(closes, event_idx):
    """Return pct change from event_idx to event_idx + horizon for each horizon."""
    p0 = closes[event_idx]
    returns = {}
    for h in HORIZONS:
        if event_idx + h >= len(closes):
            returns[h] = None
        else:
            returns[h] = (closes[event_idx + h] - p0) / p0 * 100
    return returns


def stats(values):
    """Mean, median, %positive, min, max, p10, p90."""
    vals = sorted([v for v in values if v is not None])
    if not vals:
        return None
    n = len(vals)
    mean = sum(vals) / n
    median = vals[n // 2]
    pct_positive = sum(1 for v in vals if v > 0) / n * 100
    p10 = vals[max(0, n // 10)]
    p90 = vals[min(n - 1, 9 * n // 10)]
    return {
        "n": n,
        "mean_pct": round(mean, 3),
        "median_pct": round(median, 3),
        "pct_positive": round(pct_positive, 1),
        "min_pct": round(vals[0], 3),
        "max_pct": round(vals[-1], 3),
        "p10": round(p10, 3),
        "p90": round(p90, 3),
    }


def main():
    print("Loading BTC 30d 1min cache...")
    raw = load(BTC)
    closes = [bar[4] for bar in raw]
    timestamps = [bar[0] for bar in raw]
    print(f"  {len(closes)} 1-min candles from {timestamps[0]} to {timestamps[-1]}")

    print("Computing EMA200 + RSI14...")
    ema200_vals = ema(closes, 200)
    rsi_vals = rsi(closes, 14)

    print(f"Finding break events (RSI<={RSI_OVERSOLD}, persist>={PERSIST_BARS}m, gap>={EVENT_GAP}m)...")
    events = find_events(closes, ema200_vals, rsi_vals)
    print(f"  {len(events)} qualifying events in 30d window")
    if not events:
        print("No events found. Exiting.")
        return

    # Print event details
    print("\nEvent details:")
    print(f"{'idx':>6} {'time':>14} {'price':>10} {'ema200':>10} {'rsi':>6}")
    for idx in events:
        ts_str = str(timestamps[idx])[:13]
        print(f"{idx:>6} {ts_str:>14} {closes[idx]:>10.1f} {ema200_vals[idx]:>10.1f} {rsi_vals[idx]:>6.1f}")

    # Per-horizon stats
    print("\nForward returns from event:")
    print(f"{'horizon':>10} {'n':>4} {'mean%':>8} {'median%':>8} {'pos%':>6} {'p10':>8} {'p90':>8} {'min':>8} {'max':>8}")
    by_horizon = {h: [] for h in HORIZONS}
    for idx in events:
        ret = forward_returns(closes, idx)
        for h, r in ret.items():
            if r is not None:
                by_horizon[h].append(r)

    horizon_names = {30: "+30min", 60: "+1h", 180: "+3h", 360: "+6h", 720: "+12h", 1440: "+24h"}
    results = {}
    for h in HORIZONS:
        s = stats(by_horizon[h])
        if s:
            results[horizon_names[h]] = s
            print(f"{horizon_names[h]:>10} {s['n']:>4} {s['mean_pct']:>8} {s['median_pct']:>8} "
                  f"{s['pct_positive']:>6} {s['p10']:>8} {s['p90']:>8} {s['min_pct']:>8} {s['max_pct']:>8}")

    # Recovery analysis: did price get back above EMA200 within X hours?
    print("\nRecovery to EMA200 analysis:")
    print(f"{'horizon':>10} {'recovered':>10} {'pct':>6}")
    for h in [60, 180, 360, 720, 1440]:
        recovered = 0
        denom = 0
        for idx in events:
            if idx + h >= len(closes):
                continue
            denom += 1
            for k in range(1, h + 1):
                if ema200_vals[idx + k] is None:
                    continue
                if closes[idx + k] >= ema200_vals[idx + k]:
                    recovered += 1
                    break
        if denom:
            pct = recovered / denom * 100
            print(f"{horizon_names[h]:>10} {recovered}/{denom:<3} {pct:>5.1f}%")

    # Save output JSON for cross-referencing
    out = {
        "config": {
            "rsi_threshold": RSI_OVERSOLD,
            "persist_bars": PERSIST_BARS,
            "event_gap_min": EVENT_GAP,
            "horizons_min": HORIZONS,
        },
        "n_events": len(events),
        "events": [
            {"idx": idx, "ts": timestamps[idx], "close": closes[idx],
             "ema200": ema200_vals[idx], "rsi": rsi_vals[idx]}
            for idx in events
        ],
        "horizon_stats": results,
    }
    out_path = Path(__file__).parent / "ema200_break_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()

"""
Time-to-recovery on 3y BTC 1H — extends cycle 43 finding.

The 30d 1min cache had no event lasting >6h post-EMA200 break (because the
window was structurally bullish). This script uses the 3y BTC 1H cache —
which spans Jan 2023 to Dec 2025 and contains real bear regimes —
to ask: how often historically does BTC stay below its (1H) EMA200 for
14h or more after a fresh oversold break?

Same logic as time_to_recovery_analyzer.py but on 1H bars and with longer
horizons.

Output: empirical distribution of time-to-recovery on 1H TF over 3y, plus
positioning of the live case 0513-event in this distribution.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data_cache"
BTC_1H = DATA_DIR / "binance_BTCUSDT_1h_1672531200000_1767139200000.json"

RSI_OVERSOLD = 30
PERSIST_BARS = 3       # 3h persist on 1H TF (was 5min on 1min TF)
EVENT_GAP = 24         # 24h gap between events (was 240min)
MAX_LOOK = 720         # 30d cap

# Buckets in HOURS for CDF
CDF_BUCKETS_H = [1, 2, 4, 6, 12, 24, 48, 72, 120, 168, 336, 720]


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
    for i in range(200, n - PERSIST_BARS - 1):
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


def time_to_recovery(closes, ema200_vals, idx, max_look=MAX_LOOK):
    n = len(closes)
    for k in range(1, max_look + 1):
        if idx + k >= n:
            return None
        if ema200_vals[idx + k] is None:
            continue
        if closes[idx + k] >= ema200_vals[idx + k]:
            return k
    return None


def empirical_cdf(values, buckets):
    n_total = len(values)
    if n_total == 0:
        return {}
    cdf = {}
    for b in buckets:
        n_le = sum(1 for v in values if v is not None and v <= b)
        cdf[b] = round(n_le / n_total * 100, 1)
    return cdf


def fmt_hours(h):
    if h is None:
        return "OFF"
    if h < 24:
        return f"{h}h"
    elif h < 168:
        return f"{h / 24:.1f}d"
    else:
        return f"{h / 168:.1f}w"


def main():
    print("Loading BTC 3y 1H cache...")
    raw = load(BTC_1H)
    closes = [bar[4] for bar in raw]
    timestamps = [bar[0] for bar in raw]
    print(f"  {len(closes)} 1H candles ({(len(closes)) / 24 / 365:.1f}y)")

    print("Computing EMA200 + RSI14 on 1H TF...")
    ema200_vals = ema(closes, 200)
    rsi_vals = rsi(closes, 14)

    print(f"Finding events (RSI<={RSI_OVERSOLD}, persist={PERSIST_BARS}h, gap={EVENT_GAP}h)...")
    events = find_events(closes, ema200_vals, rsi_vals)
    print(f"  {len(events)} events in 3y\n")

    if not events:
        print("No events found.")
        return

    # Compute time-to-recovery in hours
    ttrs = []
    for idx in events:
        ttr = time_to_recovery(closes, ema200_vals, idx)
        ttrs.append(ttr)

    # Distribution stats
    valid = [t for t in ttrs if t is not None]
    off_chart = sum(1 for t in ttrs if t is None)
    print(f"Time-to-recovery stats (1H TF, 3y span):")
    print(f"  Total events:           {len(ttrs)}")
    print(f"  Recovered <= 30d:       {len(valid)}")
    print(f"  Off-chart (>30d):       {off_chart}")

    if valid:
        sorted_v = sorted(valid)
        n_v = len(sorted_v)
        print(f"  Min:    {fmt_hours(sorted_v[0]):>6}")
        print(f"  Median: {fmt_hours(sorted_v[n_v // 2]):>6}")
        print(f"  Mean:   {sum(sorted_v) / n_v:.1f}h")
        print(f"  P90:    {fmt_hours(sorted_v[min(n_v - 1, 9 * n_v // 10)]):>6}")
        print(f"  P95:    {fmt_hours(sorted_v[min(n_v - 1, 19 * n_v // 20)]):>6}")
        print(f"  Max:    {fmt_hours(sorted_v[-1]):>6}")

    cdf = empirical_cdf(ttrs, CDF_BUCKETS_H)
    print(f"\nEmpirical CDF (% recovered by bucket, 1H TF):")
    for b in CDF_BUCKETS_H:
        bar = "#" * int(cdf[b] / 2)
        print(f"  <= {b:>4}h ({fmt_hours(b)}): {cdf[b]:>5.1f}% {bar}")

    # Live case sits at ~14h (since event 0513:16h25 UTC, now 0514:10h23 UTC)
    print(f"\nLive case positioning:")
    print(f"  Event time: 0513:16h25 UTC")
    print(f"  Now (analysis): 0514:10h23 UTC")
    print(f"  Elapsed: ~18h, BTC still below EMA200")

    pct_take_more_than_18h = sum(
        1 for t in ttrs if t is None or t > 18
    ) / len(ttrs) * 100
    pct_take_more_than_24h = sum(
        1 for t in ttrs if t is None or t > 24
    ) / len(ttrs) * 100
    pct_take_more_than_72h = sum(
        1 for t in ttrs if t is None or t > 72
    ) / len(ttrs) * 100
    print(f"  Historical events taking >18h: {pct_take_more_than_18h:.1f}%")
    print(f"  Historical events taking >24h: {pct_take_more_than_24h:.1f}%")
    print(f"  Historical events taking >72h: {pct_take_more_than_72h:.1f}%")

    # Top 5 longest historical events for context
    print(f"\nTop 10 longest recoveries (real bear episodes):")
    indexed = sorted(
        [(i, ttr) for i, ttr in zip(events, ttrs) if ttr is not None],
        key=lambda x: -x[1]
    )[:10]
    import datetime
    for idx, ttr in indexed:
        ts = datetime.datetime.fromtimestamp(timestamps[idx] / 1000, datetime.UTC)
        print(f"  {ts.strftime('%Y-%m-%d %H:%M')} UTC - "
              f"price ${closes[idx]:.0f} - took {fmt_hours(ttr)} to recover")

    # Off-chart episodes
    if off_chart > 0:
        print(f"\nOff-chart episodes ({off_chart}, never recovered <=30d):")
        for idx, ttr in zip(events, ttrs):
            if ttr is None:
                ts = datetime.datetime.fromtimestamp(timestamps[idx] / 1000, datetime.UTC)
                print(f"  {ts.strftime('%Y-%m-%d %H:%M')} UTC - "
                      f"price ${closes[idx]:.0f}")

    # Save
    out = {
        "config": {
            "tf_hours": 1,
            "rsi_threshold": RSI_OVERSOLD,
            "persist_bars": PERSIST_BARS,
            "event_gap_h": EVENT_GAP,
            "max_look_h": MAX_LOOK,
            "data_span_y": round((len(closes)) / 24 / 365, 2),
        },
        "n_events": len(events),
        "n_off_chart": off_chart,
        "ttrs_hours": ttrs,
        "cdf_pct_by_bucket_h": cdf,
        "live_case_18h": {
            "elapsed_h": 18,
            "pct_historical_taking_more_or_off": round(pct_take_more_than_18h, 2),
            "pct_historical_taking_more_24h_or_off": round(pct_take_more_than_24h, 2),
            "pct_historical_taking_more_72h_or_off": round(pct_take_more_than_72h, 2),
        },
    }
    out_path = Path(__file__).parent / "time_to_recovery_3y_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()

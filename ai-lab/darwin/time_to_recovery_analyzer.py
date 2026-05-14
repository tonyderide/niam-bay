"""
Time-to-recovery analyzer — Cycle 43 follow-up to cycle 41.

Cycle 41 claimed "100% of 67 EMA200-break-RSI-oversold events recovered above
EMA200 within 6h". Cycle 41 then concluded "the historical pattern is broken"
because the live event of 0513:16h25 had not recovered by 0513:22h25.

Two questions cycle 43 wants to answer:

  1. What is the FULL time-to-recovery distribution across the 67 events?
     (cycle 41 only reported the 6h cumulative bucket. We want the empirical
     CDF in minutes — to know if our live case is in the tail or off-chart.)

  2. Was any event in the cache "still naked" at 14h+ post-break, like our
     live case (0514:10h23 = ~18h post-event 0513:16h25)?

For each qualifying event, we measure the first minute k>=1 where
close[idx+k] >= ema200_vals[idx+k]. If never recovers within the cache window,
record as None (off-chart).

Also produces an empirical CDF (1, 2, 5, 10, 30, 60, 120, 180, 360, 720, 1440
minute buckets).
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data_cache"
BTC = DATA_DIR / "binance_BTCUSDT_1min_30d.json"

RSI_OVERSOLD = 30
PERSIST_BARS = 5
EVENT_GAP = 240
MAX_LOOK = 4320  # 72h cap on per-event search

CDF_BUCKETS_MIN = [1, 2, 5, 10, 15, 30, 60, 120, 180, 360, 720, 1440, 2880, 4320]


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
    """First k>=1 such that close[idx+k] >= ema200_vals[idx+k].
    Returns int (minutes) or None if not recovered within max_look or
    cache runs out."""
    n = len(closes)
    for k in range(1, max_look + 1):
        if idx + k >= n:
            return None  # ran off cache
        if ema200_vals[idx + k] is None:
            continue
        if closes[idx + k] >= ema200_vals[idx + k]:
            return k
    return None  # never within max_look


def empirical_cdf(values, buckets):
    """For each bucket, % of events recovered <= bucket minutes."""
    n_total = len(values)
    if n_total == 0:
        return {}
    cdf = {}
    for b in buckets:
        n_le = sum(1 for v in values if v is not None and v <= b)
        cdf[b] = round(n_le / n_total * 100, 1)
    return cdf


def main():
    print("Loading BTC 30d 1min cache...")
    raw = load(BTC)
    closes = [bar[4] for bar in raw]
    timestamps = [bar[0] for bar in raw]
    n = len(closes)
    print(f"  {n} 1-min candles "
          f"({(n - 1) / 60 / 24:.1f}d span)")

    print("Computing EMA200 + RSI14...")
    ema200_vals = ema(closes, 200)
    rsi_vals = rsi(closes, 14)

    print(f"Finding events (RSI<={RSI_OVERSOLD}, persist={PERSIST_BARS})...")
    events = find_events(closes, ema200_vals, rsi_vals)
    print(f"  {len(events)} events\n")

    if not events:
        print("No events found.")
        return

    # Compute time-to-recovery for each
    ttrs = []
    print(f"{'idx':>6} {'time':>14} {'close':>10} {'ema200':>10} "
          f"{'rsi':>6} {'ttr_min':>10}")
    for idx in events:
        ttr = time_to_recovery(closes, ema200_vals, idx)
        ttrs.append(ttr)
        ts_str = str(timestamps[idx])[:13]
        ttr_str = str(ttr) if ttr is not None else "OFF-CHART"
        print(f"{idx:>6} {ts_str:>14} {closes[idx]:>10.1f} "
              f"{ema200_vals[idx]:>10.1f} {rsi_vals[idx]:>6.1f} "
              f"{ttr_str:>10}")

    # Distribution stats
    valid_ttrs = [t for t in ttrs if t is not None]
    off_chart = sum(1 for t in ttrs if t is None)
    print(f"\nTime-to-recovery stats:")
    print(f"  Total events:            {len(ttrs)}")
    print(f"  Recovered in window:     {len(valid_ttrs)}")
    print(f"  Off-chart (>{MAX_LOOK}min): {off_chart}")
    if valid_ttrs:
        sorted_ttrs = sorted(valid_ttrs)
        n_v = len(sorted_ttrs)
        print(f"  Min:    {sorted_ttrs[0]:>5} min")
        print(f"  Max:    {sorted_ttrs[-1]:>5} min")
        print(f"  Median: {sorted_ttrs[n_v // 2]:>5} min")
        mean = sum(sorted_ttrs) / n_v
        print(f"  Mean:   {mean:>5.0f} min")
        print(f"  P10:    {sorted_ttrs[n_v // 10]:>5} min")
        print(f"  P90:    {sorted_ttrs[min(n_v - 1, 9 * n_v // 10)]:>5} min")
        print(f"  P95:    {sorted_ttrs[min(n_v - 1, 19 * n_v // 20)]:>5} min")

    # Empirical CDF
    cdf = empirical_cdf(ttrs, CDF_BUCKETS_MIN)
    print(f"\nEmpirical CDF (% recovered by bucket):")
    for b in CDF_BUCKETS_MIN:
        bar = "#" * int(cdf[b] / 2)
        print(f"  <= {b:>4}min ({b // 60:>2}h): {cdf[b]:>5.1f}% {bar}")

    # Cycle 41 retrospective: was the 6h claim right?
    pct_under_6h = cdf[360]
    print(f"\nCycle 41 retrospective:")
    print(f"  Claim: '100% recovered within 6h'")
    print(f"  Reality: {pct_under_6h}% recovered <= 360min (6h)")
    print(f"  Off-chart at 72h:  {off_chart}/{len(ttrs)} = "
          f"{off_chart / len(ttrs) * 100:.1f}%")

    # Live case comparison
    print(f"\nLive case (event 0513:16h25 UTC):")
    print(f"  Time elapsed at this analysis: ~18h (1080 min)")
    print(f"  Recovery happened: NO (BTC still under EMA200)")
    pct_take_more_than_18h = sum(
        1 for t in ttrs if t is None or t > 1080
    ) / len(ttrs) * 100
    print(f"  Historical events that took >18h or never: "
          f"{pct_take_more_than_18h:.1f}%")
    if pct_take_more_than_18h < 5:
        print(f"  → Live case is in the tail (<5% of historical)")
    elif pct_take_more_than_18h < 15:
        print(f"  → Live case is uncommon but not extreme (5-15%)")
    else:
        print(f"  → Live case is within normal range ({pct_take_more_than_18h:.1f}%)")

    # Save
    out = {
        "config": {
            "rsi_threshold": RSI_OVERSOLD,
            "persist_bars": PERSIST_BARS,
            "event_gap_min": EVENT_GAP,
            "max_look_min": MAX_LOOK,
        },
        "n_events": len(events),
        "n_off_chart": off_chart,
        "ttrs_min": ttrs,
        "events": [
            {"idx": idx, "ts": timestamps[idx], "ttr_min": ttr}
            for idx, ttr in zip(events, ttrs)
        ],
        "cdf_pct_by_bucket_min": cdf,
        "cycle_41_retrospective": {
            "claimed_6h_recovery_pct": 100.0,
            "actual_6h_recovery_pct": pct_under_6h,
        },
        "live_case_18h": {
            "elapsed_min_approx": 1080,
            "pct_historical_taking_more_or_off": round(pct_take_more_than_18h, 2),
        },
    }
    out_path = Path(__file__).parent / "time_to_recovery_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()

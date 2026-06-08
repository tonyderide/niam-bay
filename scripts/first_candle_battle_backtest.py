"""
First-Candle "Battle" Backtest — does the first candle after market open predict the day?

Hypothesis (Tony): at market open buyers vs sellers fight in the first candle;
its direction then tells us if the session goes up or down -> one winning trade/day.

We test this honestly on BTCUSDT (Binance), ~12 months of 15m klines.
Two "opens": Wall Street 14:30 UTC, and daily 00:00 UTC.
First-candle windows: 15m, 30m, 60m. Session horizon after the open candle.

For each (open, window): signal = sign(close-open) of first candle.
  FOLLOW: trade in the candle's direction, exit at session end.
  FADE:   trade opposite.
  BREAKOUT: enter on break of first-candle high (long) / low (short), exit session end.
Report hit-rate + mean return per trade + expectancy + cumulative.
"""
import time, datetime as dt
import requests
import pandas as pd
import numpy as np

SYMBOL = "BTCUSDT"
INTERVAL = "15m"
MS = {"15m": 15*60*1000}
MONTHS = 12

def fetch_klines(symbol, interval, start_ms, end_ms):
    out = []
    url = "https://api.binance.com/api/v3/klines"
    cur = start_ms
    while cur < end_ms:
        r = requests.get(url, params={"symbol":symbol,"interval":interval,
                                      "startTime":cur,"endTime":end_ms,"limit":1000}, timeout=20)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        out.extend(batch)
        cur = batch[-1][0] + 1
        if len(batch) < 1000:
            break
        time.sleep(0.15)
    return out

end = int(time.time()*1000)
start = end - MONTHS*30*24*60*60*1000
print(f"Fetching {SYMBOL} {INTERVAL} ~{MONTHS} months ...")
raw = fetch_klines(SYMBOL, INTERVAL, start, end)
df = pd.DataFrame(raw, columns=["openTime","open","high","low","close","vol","closeTime",
                                "qav","trades","tbav","tbqav","ignore"])
for c in ["open","high","low","close"]:
    df[c] = df[c].astype(float)
df["ts"] = pd.to_datetime(df["openTime"], unit="ms", utc=True)
df = df[["ts","open","high","low","close"]].set_index("ts").sort_index()
print(f"  {len(df)} candles  {df.index[0]}  ->  {df.index[-1]}")

def session_test(open_hour, open_min, window_min, horizon_hours):
    """Return dict of stats for FOLLOW / FADE / BREAKOUT at a given open."""
    days = pd.unique(df.index.date)
    rows = []
    wcount = window_min // 15
    for d in days:
        day_start = pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=open_hour, minutes=open_min)
        win = df.loc[day_start: day_start + pd.Timedelta(minutes=window_min) - pd.Timedelta(seconds=1)]
        if len(win) < wcount:
            continue
        first_open = win["open"].iloc[0]
        first_close = win["close"].iloc[-1]
        hi = win["high"].max(); lo = win["low"].min()
        entry_time = day_start + pd.Timedelta(minutes=window_min)
        exit_time = day_start + pd.Timedelta(hours=horizon_hours)
        path = df.loc[entry_time: exit_time]
        if len(path) < 2:
            continue
        entry_px = path["open"].iloc[0]
        exit_px = path["close"].iloc[-1]
        sig = np.sign(first_close - first_open)  # battle outcome
        if sig == 0:
            continue
        # FOLLOW
        follow_ret = sig * (exit_px - entry_px) / entry_px
        # FADE
        fade_ret = -follow_ret
        # BREAKOUT: whichever side breaks first within the path
        bo_ret = np.nan; bo_dir = 0
        for _, c in path.iterrows():
            if c["high"] >= hi and c["low"] <= lo:
                bo_dir = sig  # both -> default to battle dir
                break
            if c["high"] >= hi:
                bo_dir = 1; break
            if c["low"] <= lo:
                bo_dir = -1; break
        if bo_dir != 0:
            bo_ret = bo_dir * (exit_px - entry_px) / entry_px
        rows.append((follow_ret, fade_ret, bo_ret))
    if not rows:
        return None
    arr = pd.DataFrame(rows, columns=["follow","fade","breakout"])
    res = {}
    for col in ["follow","fade","breakout"]:
        s = arr[col].dropna()
        if len(s)==0:
            continue
        res[col] = dict(n=len(s), hit=float((s>0).mean()), mean=float(s.mean()),
                        cum=float(s.sum()), median=float(s.median()))
    return res

CONFIGS = [
    ("US open 14:30 UTC", 14, 30),
    ("Daily 00:00 UTC",    0,  0),
]
WINDOWS = [15, 30, 60]
HORIZON = {  # hours after open to exit
    "US open 14:30 UTC": 6.5,   # cash session
    "Daily 00:00 UTC":   24,    # full day
}

print("\n" + "="*92)
print(f"{'OPEN':<18}{'win':>4}{'strat':>10}{'N':>6}{'hit%':>8}{'mean%':>9}{'cum%':>9}")
print("="*92)
for name, oh, om in CONFIGS:
    for w in WINDOWS:
        r = session_test(oh, om, w, HORIZON[name])
        if not r:
            continue
        for strat in ["follow","fade","breakout"]:
            if strat not in r: continue
            x = r[strat]
            print(f"{name:<18}{w:>4}{strat:>10}{x['n']:>6}{x['hit']*100:>7.1f}{x['mean']*100:>9.3f}{x['cum']*100:>9.1f}")
    print("-"*92)

# Stability: last 3 months vs full, for the simplest config (US open, 60m, follow)
print("\nSTABILITY CHECK — US open, 60m window, FOLLOW:")
recent = df[df.index >= df.index[-1] - pd.Timedelta(days=90)]
full_df = df
for label, sub in [("full 12mo", df), ("last 3mo", recent)]:
    globals()['df'] = sub
    r = session_test(14, 30, 60, 6.5)
    if r and 'follow' in r:
        x = r['follow']
        print(f"  {label:<10} N={x['n']:>3}  hit={x['hit']*100:5.1f}%  mean={x['mean']*100:+.3f}%  cum={x['cum']*100:+.1f}%")
globals()['df'] = full_df
print("\nNote: costs (fees+slippage) ~0.04-0.10% round-trip NOT yet deducted.")
print("Edge must clear that per trade to be real.")

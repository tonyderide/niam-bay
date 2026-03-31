#!/usr/bin/env python3
"""Scan top 15 Kraken Futures pairs — EMA_TREND signal + grid potential."""

import urllib.request
import json
import time
import math
from datetime import datetime

PAIRS = [
    ("PF_XBTUSD", "XXBTZUSD"),
    ("PF_ETHUSD", "XETHZUSD"),
    ("PF_SOLUSD", "SOLUSD"),
    ("PF_TAOUSD", "TAOUSD"),
    ("PF_XRPUSD", "XRPUSD"),
    ("PF_ZECUSD", "ZECUSD"),
    ("PF_ADAUSD", "ADAUSD"),
    ("PF_DOGEUSD", "XDGUSD"),
    ("PF_SUIUSD", "SUIUSD"),
    ("PF_LINKUSD", "LINKUSD"),
    ("PF_AVAXUSD", "AVAXUSD"),
    ("PF_NEARUSD", "NEARUSD"),
    ("PF_LTCUSD", "XLTCZUSD"),
    ("PF_XLMUSD", "XXLMZUSD"),
    ("PF_DOTUSD", "DOTUSD"),
]

def ema(data, period):
    k = 2 / (period + 1)
    result = [sum(data[:period]) / period]
    for i in range(period, len(data)):
        result.append(data[i] * k + result[-1] * (1 - k))
    return result

def rsi(closes, period=14):
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    rs = avg_gain / max(avg_loss, 1e-10)
    rsi_values = [100 - 100/(1+rs)]
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period-1) + gains[i]) / period
        avg_loss = (avg_loss * (period-1) + losses[i]) / period
        rs = avg_gain / max(avg_loss, 1e-10)
        rsi_values.append(100 - 100/(1+rs))
    return rsi_values

def atr(highs, lows, closes, period=14):
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
        trs.append(tr)
    if len(trs) < period:
        return 0
    atr_val = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr_val = (atr_val * (period-1) + trs[i]) / period
    return atr_val

def fetch_ohlc(spot_pair):
    url = f"https://api.kraken.com/0/public/OHLC?pair={spot_pair}&interval=60"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    if data.get("error") and len(data["error"]) > 0:
        raise Exception(f"API error: {data['error']}")
    result_key = [k for k in data["result"] if k != "last"][0]
    candles = data["result"][result_key]
    # Take last 250
    candles = candles[-250:]
    opens = [float(c[1]) for c in candles]
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    closes = [float(c[4]) for c in candles]
    return opens, highs, lows, closes

def fmt_price(p):
    if p >= 1000:
        return f"{p:,.1f}"
    elif p >= 1:
        return f"{p:.3f}"
    else:
        return f"{p:.5f}"

def main():
    results = []
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    for futures_pair, spot_pair in PAIRS:
        try:
            opens, highs, lows, closes = fetch_ohlc(spot_pair)
            price = closes[-1]

            ema50 = ema(closes, 50)
            ema200 = ema(closes, 200)
            rsi_vals = rsi(closes)
            atr_val = atr(highs, lows, closes)

            current_ema50 = ema50[-1]
            current_ema200 = ema200[-1]
            current_rsi = rsi_vals[-1]
            volatility = (atr_val / price) * 100 if price > 0 else 0

            # Signal
            if current_ema50 > current_ema200 and current_rsi > 50:
                signal = "OPEN"
            elif current_rsi < 35:
                signal = "DANGER"
            else:
                signal = "WAIT"

            # Grid potential
            if volatility > 2 and signal == "OPEN":
                grid_pot = "HIGH"
            elif volatility > 1:
                grid_pot = "MEDIUM"
            else:
                grid_pot = "LOW"

            results.append({
                "pair": futures_pair,
                "price": price,
                "ema50": current_ema50,
                "ema200": current_ema200,
                "rsi": current_rsi,
                "signal": signal,
                "volatility": volatility,
                "grid_pot": grid_pot,
            })
            print(f"  OK: {futures_pair} — {signal} (RSI {current_rsi:.1f})")
        except Exception as e:
            print(f"  SKIP: {futures_pair} — {e}")

        time.sleep(1)

    # Sort: OPEN first (by RSI desc), then WAIT (by RSI desc), then DANGER
    signal_order = {"OPEN": 0, "WAIT": 1, "DANGER": 2}
    results.sort(key=lambda r: (signal_order.get(r["signal"], 9), -r["rsi"]))

    # Build table
    header = "| Pair | Price | EMA50 | EMA200 | RSI | Signal | Volatility% | Grid Potential |"
    sep    = "|------|-------|-------|--------|-----|--------|-------------|----------------|"
    rows = [header, sep]
    for r in results:
        sig_emoji = {"OPEN": "🟢", "WAIT": "🟡", "DANGER": "🔴"}.get(r["signal"], "")
        row = f"| {r['pair']} | {fmt_price(r['price'])} | {fmt_price(r['ema50'])} | {fmt_price(r['ema200'])} | {r['rsi']:.1f} | {sig_emoji} {r['signal']} | {r['volatility']:.2f}% | {r['grid_pot']} |"
        rows.append(row)

    table = "\n".join(rows)

    # Summary
    open_count = sum(1 for r in results if r["signal"] == "OPEN")
    danger_count = sum(1 for r in results if r["signal"] == "DANGER")
    wait_count = sum(1 for r in results if r["signal"] == "WAIT")
    high_grid = [r["pair"] for r in results if r["grid_pot"] == "HIGH"]

    summary = f"""## Summary
- **OPEN**: {open_count} pairs
- **WAIT**: {wait_count} pairs
- **DANGER**: {danger_count} pairs
- **Best grid candidates**: {', '.join(high_grid) if high_grid else 'None'}
"""

    md = f"""# SCAN Multi-Crypto — EMA Trend + Grid Potential

> Scan date: {now}
> Source: Kraken Spot 1H candles (250 periods)
> Indicators: EMA50, EMA200, RSI(14), ATR(14)

{summary}
## Results

{table}

## Legend
- **OPEN** = EMA50 > EMA200 AND RSI > 50 (bullish trend confirmed)
- **WAIT** = Conditions not met yet
- **DANGER** = RSI < 35 (oversold / potential crash)
- **Volatility%** = ATR(14) / Price * 100
- **Grid Potential**: HIGH (vol>2% + OPEN), MEDIUM (vol>1%), LOW (vol<1%)
"""

    # Print
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print("\n" + "="*80)
    print(md)

    # Save
    output_path = "C:/Users/tony_/Documents/niam-bay/trading/SCAN_MULTI_CRYPTO.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"\nSaved to {output_path}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Download historical candle data from Kraken public API.
Saves OHLCV CSVs for multiple pairs and intervals.
"""

import urllib.request
import urllib.error
import json
import csv
import os
import time
from datetime import datetime

BASE_URL = "https://api.kraken.com/0/public"

PAIRS = [
    "XETHZUSD",
    "XXBTZUSD",
    "SOLUSD",
    "XXRPZUSD",
    "ADAUSD",
    "LINKUSD",
    "DOTUSD",
]

INTERVALS = [1, 5, 15]  # minutes

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def api_get(endpoint, params=None):
    """GET request to Kraken public API, returns parsed JSON."""
    url = f"{BASE_URL}/{endpoint}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "niam-bay/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    if data.get("error") and len(data["error"]) > 0:
        raise RuntimeError(f"Kraken API error: {data['error']}")
    return data["result"]


def download_ohlc(pair, interval):
    """Download OHLC candles and save to CSV. Returns row count."""
    result = api_get("OHLC", {"pair": pair, "interval": interval})
    # Result keys vary — pick the one that isn't 'last'
    candle_key = [k for k in result if k != "last"][0]
    candles = result[candle_key]

    filename = f"{pair}_{interval}m.csv"
    filepath = os.path.join(DATA_DIR, filename)

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for c in candles:
            # Kraken OHLC: [time, open, high, low, close, vwap, volume, count]
            ts = datetime.fromtimestamp(c[0], tz=None).strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([ts, c[1], c[2], c[3], c[4], c[6]])

    return len(candles)


def get_tickers(pairs):
    """Fetch ticker info for all pairs in one call."""
    pair_str = ",".join(pairs)
    return api_get("Ticker", {"pair": pair_str})


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print("=" * 70)
    print("  Kraken Historical Data Downloader")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # --- Download OHLC candles ---
    total_files = 0
    for pair in PAIRS:
        for interval in INTERVALS:
            try:
                count = download_ohlc(pair, interval)
                total_files += 1
                print(f"  [OK] {pair} {interval}m — {count} candles")
            except Exception as e:
                print(f"  [ERR] {pair} {interval}m — {e}")
            time.sleep(2)  # rate limit

    print(f"\nSaved {total_files} CSV files to {DATA_DIR}\n")

    # --- Ticker summary ---
    print("-" * 70)
    print(f"  {'Pair':<14} {'Price':>12} {'24h Change':>12} {'24h Volume':>16}")
    print("-" * 70)

    tickers = {}
    for pair in PAIRS:
        try:
            result = get_tickers([pair])
            tickers.update(result)
        except Exception as e:
            print(f"  {pair:<14} — ticker error: {e}")
        time.sleep(1)

    for pair in PAIRS:
        # Ticker keys may differ from pair name — find the matching key
        key = None
        for k in tickers:
            if pair in k or k in pair or pair.replace("X", "", 1) in k:
                key = k
                break
        if key is None:
            # Fallback: try exact match
            key = pair

        if key not in tickers:
            print(f"  {pair:<14} — ticker not found")
            continue

        t = tickers[key]
        # t['c'] = [price, lot_volume], t['o'] = today's open, t['v'] = [today, 24h]
        price = float(t["c"][0])
        open_24h = float(t["o"])
        change_pct = ((price - open_24h) / open_24h) * 100 if open_24h else 0
        volume_24h = float(t["v"][1])

        sign = "+" if change_pct >= 0 else ""
        print(f"  {pair:<14} {price:>12.4f} {sign}{change_pct:>10.2f}% {volume_24h:>16.2f}")

    print("-" * 70)
    print("Done.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fetch 30 days of PF_ETHUSD 5-minute OHLC from Kraken Futures API."""
import requests
import time
import json
from datetime import datetime, timedelta

INSTRUMENT = "PF_ETHUSD"
INTERVAL = "5m"
DAYS = 30

def fetch_all():
    now_ms = int(datetime.now().timestamp() * 1000)
    start_ms = int((datetime.now() - timedelta(days=DAYS)).timestamp() * 1000)

    all_candles = []
    seen_ts = set()
    to_ms = now_ms

    print(f"Fetching {DAYS} days of {INSTRUMENT} {INTERVAL} candles from Kraken Futures...")

    while to_ms > start_ms:
        url = f"https://futures.kraken.com/api/charts/v1/trade/{INSTRUMENT}/{INTERVAL}?to={to_ms}"

        try:
            resp = requests.get(url, timeout=30)
            data = resp.json()
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(3)
            continue

        candles = data.get("candles", [])
        if not candles:
            break

        new_count = 0
        for c in candles:
            ts = int(c["time"])
            if ts not in seen_ts and ts >= start_ms:
                seen_ts.add(ts)
                all_candles.append({
                    "ts": ts // 1000,
                    "open": float(c["open"]),
                    "high": float(c["high"]),
                    "low": float(c["low"]),
                    "close": float(c["close"]),
                    "volume": float(c["volume"])
                })
                new_count += 1

        if new_count == 0:
            break

        # Go further back
        oldest = min(int(c["time"]) for c in candles)
        if oldest >= to_ms:
            break
        to_ms = oldest - 1

        print(f"  {len(all_candles)} candles... (back to {datetime.fromtimestamp(oldest/1000).strftime('%Y-%m-%d %H:%M')})")
        time.sleep(1)

    all_candles.sort(key=lambda c: c["ts"])

    outfile = "/home/tony/projet/niam-bay/trading/eth_5m_30d.json"
    with open(outfile, "w") as f:
        json.dump(all_candles, f)

    days_covered = (all_candles[-1]["ts"] - all_candles[0]["ts"]) / 86400 if all_candles else 0
    print(f"\nDone: {len(all_candles)} candles ({days_covered:.1f} days)")
    print(f"Period: {datetime.fromtimestamp(all_candles[0]['ts'])} -> {datetime.fromtimestamp(all_candles[-1]['ts'])}")

if __name__ == "__main__":
    fetch_all()

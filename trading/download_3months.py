"""
Download 3 months of OHLC data from CryptoCompare.
- Hourly data: full 3 months (main backtest data)
- Minute data: last 7 days (validation)

CryptoCompare returns max 2000 candles per call.
3 months hourly ~= 2160 candles -> 2 calls.
"""
import urllib.request, json, time, csv, sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

PAIRS = ["ETH", "ADA", "SOL"]

def fetch_cc(fsym, tsym, endpoint, limit=2000, toTs=None):
    """Fetch from CryptoCompare API."""
    url = f"https://min-api.cryptocompare.com/data/v2/{endpoint}?fsym={fsym}&tsym={tsym}&limit={limit}"
    if toTs:
        url += f"&toTs={toTs}"
    req = urllib.request.Request(url, headers={"User-Agent": "NiamBay/1.0"})
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode())
    if data.get("Response") == "Error":
        print(f"  API Error: {data.get('Message', 'unknown')}")
        return [], None
    candles = data.get("Data", {}).get("Data", [])
    time_from = data.get("Data", {}).get("TimeFrom")
    return candles, time_from


def download_hourly(symbol, months=3):
    """Download hourly OHLC, paginating backwards."""
    all_candles = []
    toTs = None  # Start from now

    print(f"\n{'='*60}")
    print(f"Downloading {symbol}/USD — {months} months HOURLY")
    print(f"{'='*60}")

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=months * 30.5)
    cutoff_ts = int(cutoff.timestamp())

    calls = 0
    while True:
        candles, time_from = fetch_cc(symbol, "USD", "histohour", limit=2000, toTs=toTs)
        calls += 1

        if not candles:
            break

        # Filter candles before cutoff
        filtered = [c for c in candles if c["time"] >= cutoff_ts]
        all_candles.extend(filtered)

        first_ts = candles[0]["time"]
        last_ts = candles[-1]["time"]
        print(f"  Call {calls}: got {len(candles)} candles ({len(filtered)} kept), "
              f"{datetime.fromtimestamp(first_ts, tz=timezone.utc).strftime('%Y-%m-%d')} -> "
              f"{datetime.fromtimestamp(last_ts, tz=timezone.utc).strftime('%Y-%m-%d')}")

        # If we've gone past our cutoff, stop
        if first_ts <= cutoff_ts:
            break

        # Paginate backwards
        toTs = first_ts
        time.sleep(0.5)

    # Deduplicate and sort
    seen = set()
    unique = []
    for c in all_candles:
        if c["time"] not in seen:
            seen.add(c["time"])
            unique.append(c)
    unique.sort(key=lambda x: x["time"])

    # Write CSV
    out_file = DATA_DIR / f"{symbol}USD_1h_3mo.csv"
    with open(out_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for c in unique:
            ts = datetime.fromtimestamp(c["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([ts, c["open"], c["high"], c["low"], c["close"], c.get("volumefrom", 0)])

    print(f"  SAVED: {out_file} — {len(unique)} candles")
    if unique:
        print(f"  Range: {datetime.fromtimestamp(unique[0]['time'], tz=timezone.utc)} -> "
              f"{datetime.fromtimestamp(unique[-1]['time'], tz=timezone.utc)}")

    return out_file


def download_minute(symbol):
    """Download last 7 days of minute data for validation."""
    print(f"\n  Downloading {symbol}/USD — 7 days MINUTE (validation)")

    all_candles = []
    toTs = None

    now = datetime.now(timezone.utc)
    cutoff_ts = int((now - timedelta(days=7)).timestamp())

    calls = 0
    while True:
        candles, _ = fetch_cc(symbol, "USD", "histominute", limit=2000, toTs=toTs)
        calls += 1

        if not candles:
            break

        filtered = [c for c in candles if c["time"] >= cutoff_ts]
        all_candles.extend(filtered)

        first_ts = candles[0]["time"]
        print(f"    Call {calls}: {len(candles)} candles ({len(filtered)} kept)")

        if first_ts <= cutoff_ts:
            break

        toTs = first_ts
        time.sleep(0.5)

    # Deduplicate and sort
    seen = set()
    unique = []
    for c in all_candles:
        if c["time"] not in seen:
            seen.add(c["time"])
            unique.append(c)
    unique.sort(key=lambda x: x["time"])

    out_file = DATA_DIR / f"{symbol}USD_1m_7d.csv"
    with open(out_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for c in unique:
            ts = datetime.fromtimestamp(c["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([ts, c["open"], c["high"], c["low"], c["close"], c.get("volumefrom", 0)])

    print(f"    SAVED: {out_file} — {len(unique)} candles")
    return out_file


if __name__ == "__main__":
    for sym in PAIRS:
        download_hourly(sym, months=3)
        download_minute(sym)
        print()

    print("\nAll downloads complete!")

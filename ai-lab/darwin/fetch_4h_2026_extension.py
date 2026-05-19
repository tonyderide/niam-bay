"""Cycle 61 — extend 4h cache from 2026-01-01 to 2026-05-19.

The historical 4h cache binance_{PAIR}USDT_4h_*.json stops 2025-12-31. W4 of
the cycle 60 walk-forward (window 2026-04-12 → 2026-05-12) cannot evaluate the
4h regime gate because the 4h history ends ~4 months before W4 starts. Result:
W4 is empty (UNKNOWN, 0 trades) in cycle 60.

This script fetches the missing 2026 segment and writes one extended file per
pair: binance_{PAIR}USDT_4h_extended.json (2023-01-01 → today). The walk-forward
loader (build_gate_for_pair) is patched separately to prefer the extended file.

Binance public klines endpoint, 4h interval, no auth required.
"""
import json
import datetime
import time
import urllib.request
from pathlib import Path

CACHE_DIR = Path("/home/tony/projets/tonyderide/niam-bay/ai-lab/darwin/data_cache")
PAIRS = ["BTCUSDT", "ETHUSDT", "LINKUSDT", "ADAUSDT", "DOTUSDT", "SOLUSDT"]
# 2026-01-01 00:00 UTC -> 2026-05-19 06:00 UTC (today, last closed bar)
START_MS = int(datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
END_MS = int(datetime.datetime(2026, 5, 19, 6, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
HIST_FILE_TPL = "binance_{p}_4h_1672531200000_1767139200000.json"
EXTENDED_FILE_TPL = "binance_{p}_4h_extended.json"


def fetch_4h(pair: str, start_ms: int, end_ms: int) -> list:
    """Fetch 4h klines from Binance public API. Returns list of [ts, o, h, l, c, v]."""
    out = []
    cursor = start_ms
    while cursor < end_ms:
        url = (f"https://api.binance.com/api/v3/klines?symbol={pair}"
               f"&interval=4h&startTime={cursor}&endTime={end_ms}&limit=1000")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "niambay/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                d = json.loads(resp.read())
        except Exception as e:
            print(f"    err {pair}: {e}")
            time.sleep(2)
            continue
        if not d:
            break
        # Binance returns [openTime, o, h, l, c, vol, closeTime, ...]. Keep first 6 floats.
        out.extend([[int(k[0]), float(k[1]), float(k[2]),
                     float(k[3]), float(k[4]), float(k[5])] for k in d])
        last_close = int(d[-1][6])
        if last_close <= cursor:
            break
        cursor = last_close + 1
        if len(d) < 1000:
            break
        time.sleep(0.10)
    return out


def main():
    for pair in PAIRS:
        hist_path = CACHE_DIR / HIST_FILE_TPL.format(p=pair)
        ext_path = CACHE_DIR / EXTENDED_FILE_TPL.format(p=pair)

        hist = []
        if hist_path.exists():
            hist = json.loads(hist_path.read_text())
            print(f"{pair}: hist {len(hist)} bars, last {datetime.datetime.fromtimestamp(hist[-1][0]/1000, datetime.timezone.utc).isoformat()}")
        else:
            print(f"{pair}: no historical 4h file, starting from 2023-01-01")
            full_start = int(datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
            hist = fetch_4h(pair, full_start, START_MS)
            print(f"  fetched full history: {len(hist)} bars")

        # Decide what to fetch: from max(hist last, START_MS) → END_MS
        gap_start = hist[-1][0] + 1 if hist else START_MS
        if gap_start >= END_MS:
            print(f"  no extension needed (last bar covers end)")
            ext = hist
        else:
            new_bars = fetch_4h(pair, gap_start, END_MS)
            print(f"  fetched {len(new_bars)} new 4h bars")
            # dedup by timestamp
            seen = {c[0] for c in hist}
            new_unique = [c for c in new_bars if c[0] not in seen]
            ext = hist + new_unique

        ext_path.write_text(json.dumps(ext))
        first_iso = datetime.datetime.fromtimestamp(ext[0][0]/1000, datetime.timezone.utc).isoformat()
        last_iso = datetime.datetime.fromtimestamp(ext[-1][0]/1000, datetime.timezone.utc).isoformat()
        print(f"  -> {ext_path.name}: {len(ext)} bars, {first_iso} → {last_iso}")
        print()


if __name__ == "__main__":
    main()

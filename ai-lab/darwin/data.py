"""Fetch OHLC candles from Kraken Futures public API."""
import urllib.request
import json

KRAKEN_OHLC_URL = "https://futures.kraken.com/api/charts/v1/trade/{symbol}/{interval}"

# Kraken API accepts string intervals, not minutes
_INTERVAL_MAP = {
    1: "1m", 5: "5m", 15: "15m", 30: "30m",
    60: "1h", 240: "4h", 720: "12h", 1440: "1d",
}

def fetch_ohlc(symbol: str = "PF_SOLUSD", interval: int = 60, count: int = 2160) -> list[dict]:
    """Fetch OHLC candles. interval in minutes. count=2160 = 90 days of 1h candles.
    API returns up to 2000 candles max per request."""
    interval_str = _INTERVAL_MAP.get(interval, "1h")
    url = KRAKEN_OHLC_URL.format(symbol=symbol, interval=interval_str)
    req = urllib.request.Request(url, headers={"User-Agent": "darwin/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())

    candles = []
    for c in data.get("candles", [])[-count:]:
        candles.append({
            "timestamp": c["time"],
            "open": float(c["open"]),
            "high": float(c["high"]),
            "low": float(c["low"]),
            "close": float(c["close"]),
            "volume": float(c.get("volume", 0)),
        })
    return candles

def fetch_multi(symbols: list[str] = None, interval: int = 60, count: int = 2160) -> dict[str, list[dict]]:
    """Fetch OHLC for multiple symbols."""
    symbols = symbols or ["PF_SOLUSD", "PF_DOTUSD", "PF_ADAUSD"]
    return {s: fetch_ohlc(s, interval, count) for s in symbols}

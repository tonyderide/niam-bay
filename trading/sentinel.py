#!/usr/bin/env python3
"""
Sentinel — 24/7 trading watchdog for Martin Grid.

Runs on Oracle VM (141.253.108.141).
Monitors market conditions (Triple Lock), Martin grid health, and auto-stops
grids when danger thresholds are hit.

No external dependencies. Pure stdlib.
"""

import json
import math
import time
import signal
import sys
import os
import logging
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

# ─────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────

TELEGRAM_TOKEN = "7913168011:AAG76RsddMBpUnveiEdK2HSk4PQLS7Ab454"
TELEGRAM_CHAT_ID = "6574420846"

CHANNEL_FILE = "/home/ubuntu/niam-bay-channel.md"
LOG_FILE = "/home/ubuntu/sentinel.log"

MARTIN_BASE = "http://localhost:8081"

KRAKEN_API = "https://api.kraken.com/0/public"

# Pairs to watch — Kraken pair names
WATCH_PAIRS = {
    "XETHZUSD": "ETH/USD",
    "SOLUSD":   "SOL/USD",
    "DOTUSD":   "DOT/USD",
}

CHECK_INTERVAL = 300  # 5 minutes
OHLC_INTERVAL = 240   # 4h candles (minutes)
CANDLES_NEEDED = 210   # enough for EMA(200) + some margin

# Thresholds
TRIPLE_LOCK_ADX_MAX = 25
TRIPLE_LOCK_BB_WIDTH_MAX = 0.08  # 8%
LOSS_WARN_PCT = 5.0
LOSS_STOP_PCT = 10.0
MAXLOSS_PROXIMITY_PCT = 0.80  # warn at 80% of range consumed
PRICE_MOVE_ALERT_PCT = 3.0    # 3% in 1h

# ─────────────────────────────────────────────────────────────────────
# GLOBAL STATE
# ─────────────────────────────────────────────────────────────────────

running = True
state = {
    "triple_lock": {},       # pair -> bool (True = TRADE)
    "active_grids": set(),   # grid IDs currently active
    "last_rt_counts": {},    # grid_id -> round_trip count
    "price_history_1h": {},  # pair -> list of (ts, price) last 1h
}

# ─────────────────────────────────────────────────────────────────────
# LOGGING — silent when nothing happens
# ─────────────────────────────────────────────────────────────────────

logger = logging.getLogger("sentinel")
logger.setLevel(logging.INFO)

_file_handler = logging.FileHandler(LOG_FILE)
_file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(_file_handler)


def log(msg):
    """Log only meaningful events."""
    logger.info(msg)


# ─────────────────────────────────────────────────────────────────────
# SIGNAL HANDLER
# ─────────────────────────────────────────────────────────────────────

def _shutdown(signum, frame):
    global running
    log(f"Received signal {signum}, shutting down gracefully...")
    running = False


signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)


# ─────────────────────────────────────────────────────────────────────
# HTTP HELPERS
# ─────────────────────────────────────────────────────────────────────

def http_get(url, timeout=15):
    """GET request, returns parsed JSON or None on failure."""
    try:
        req = Request(url, headers={"User-Agent": "niam-bay-sentinel/1.0"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def http_post(url, data=None, timeout=15):
    """POST request, returns parsed JSON or None on failure."""
    try:
        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, headers={
            "User-Agent": "niam-bay-sentinel/1.0",
            "Content-Type": "application/json",
        })
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────────────────────────────

def send_telegram(text):
    """Send message via Telegram bot. Fire and forget."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
        }).encode()
        req = Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "User-Agent": "niam-bay-sentinel/1.0",
        })
        urlopen(req, timeout=10)
    except Exception as e:
        log(f"Telegram send failed: {e}")


# ─────────────────────────────────────────────────────────────────────
# CHANNEL FILE
# ─────────────────────────────────────────────────────────────────────

def write_channel(text):
    """Append alert to channel file AND send Telegram."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = f"\n---\n**[{now}]** {text}\n"
    try:
        with open(CHANNEL_FILE, "a") as f:
            f.write(entry)
    except Exception as e:
        log(f"Channel write failed: {e}")
    send_telegram(text)
    log(f"ALERT: {text}")


# ─────────────────────────────────────────────────────────────────────
# KRAKEN DATA
# ─────────────────────────────────────────────────────────────────────

def fetch_ohlc(pair, interval=OHLC_INTERVAL):
    """Fetch OHLC candles from Kraken. Returns list of [ts, o, h, l, c, vol]."""
    url = f"{KRAKEN_API}/OHLC?pair={pair}&interval={interval}"
    data = http_get(url)
    if not data or data.get("error"):
        return []
    result = data.get("result", {})
    for k, v in result.items():
        if k != "last":
            return v
    return []


def fetch_ticker(pair):
    """Fetch current ticker. Returns (price, open_24h) or (None, None)."""
    url = f"{KRAKEN_API}/Ticker?pair={pair}"
    data = http_get(url)
    if not data or data.get("error"):
        return None, None
    result = data.get("result", {})
    for k, v in result.items():
        price = float(v["c"][0])
        open_24h = float(v["o"])
        return price, open_24h
    return None, None


# ─────────────────────────────────────────────────────────────────────
# INDICATORS (pure Python)
# ─────────────────────────────────────────────────────────────────────

def calc_ema(closes, period):
    """Exponential Moving Average. Returns list same length as closes (NaN-padded)."""
    if len(closes) < period:
        return [None] * len(closes)
    k = 2.0 / (period + 1)
    ema = [None] * (period - 1)
    # seed with SMA
    sma = sum(closes[:period]) / period
    ema.append(sma)
    for i in range(period, len(closes)):
        ema.append(closes[i] * k + ema[-1] * (1 - k))
    return ema


def calc_rsi(closes, period=14):
    """RSI(period). Returns list same length as closes."""
    if len(closes) < period + 1:
        return [None] * len(closes)
    rsi = [None] * period
    gains = []
    losses = []
    for i in range(1, period + 1):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        rsi.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi.append(100.0 - 100.0 / (1.0 + rs))
    for i in range(period + 1, len(closes)):
        delta = closes[i] - closes[i - 1]
        gain = max(delta, 0)
        loss = max(-delta, 0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        if avg_loss == 0:
            rsi.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100.0 - 100.0 / (1.0 + rs))
    return rsi


def calc_adx(highs, lows, closes, period=14):
    """ADX(period). Returns list same length as input."""
    n = len(closes)
    if n < period * 2 + 1:
        return [None] * n

    # True Range, +DM, -DM
    tr_list = []
    plus_dm = []
    minus_dm = []
    for i in range(1, n):
        h = highs[i]
        l = lows[i]
        pc = closes[i - 1]
        tr_list.append(max(h - l, abs(h - pc), abs(l - pc)))
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        plus_dm.append(up if (up > down and up > 0) else 0)
        minus_dm.append(down if (down > up and down > 0) else 0)

    # Smoothed TR, +DM, -DM (Wilder's smoothing)
    atr = sum(tr_list[:period])
    apdm = sum(plus_dm[:period])
    amdm = sum(minus_dm[:period])

    dx_list = []

    for i in range(period, len(tr_list)):
        atr = atr - atr / period + tr_list[i]
        apdm = apdm - apdm / period + plus_dm[i]
        amdm = amdm - amdm / period + minus_dm[i]

        plus_di = 100 * apdm / atr if atr != 0 else 0
        minus_di = 100 * amdm / atr if atr != 0 else 0
        di_sum = plus_di + minus_di
        dx = 100 * abs(plus_di - minus_di) / di_sum if di_sum != 0 else 0
        dx_list.append(dx)

    # ADX = smoothed DX
    if len(dx_list) < period:
        return [None] * n

    adx_val = sum(dx_list[:period]) / period
    adx_result = [None] * (n - len(dx_list) + period - 1)
    adx_result.append(adx_val)

    for i in range(period, len(dx_list)):
        adx_val = (adx_val * (period - 1) + dx_list[i]) / period
        adx_result.append(adx_val)

    # Pad to match input length
    while len(adx_result) < n:
        adx_result.insert(0, None)

    return adx_result


def calc_bb_width(closes, period=20, std_mult=2.0):
    """Bollinger Bands width as fraction of middle band. Returns list."""
    n = len(closes)
    if n < period:
        return [None] * n

    result = [None] * (period - 1)
    for i in range(period - 1, n):
        window = closes[i - period + 1: i + 1]
        sma = sum(window) / period
        variance = sum((x - sma) ** 2 for x in window) / period
        std = math.sqrt(variance)
        upper = sma + std_mult * std
        lower = sma - std_mult * std
        width = (upper - lower) / sma if sma != 0 else 0
        result.append(width)
    return result


# ─────────────────────────────────────────────────────────────────────
# TRIPLE LOCK CHECK
# ─────────────────────────────────────────────────────────────────────

def check_triple_lock(pair):
    """
    Triple Lock: (price > EMA200) AND (ADX < 25) AND (BB width < 8%)
    Returns (is_trade: bool, details: str) or (None, error_msg).
    """
    candles = fetch_ohlc(pair)
    if not candles or len(candles) < CANDLES_NEEDED:
        return None, f"Not enough candles for {pair}: got {len(candles) if candles else 0}"

    closes = [float(c[4]) for c in candles]
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]

    price = closes[-1]

    ema200 = calc_ema(closes, 200)
    ema50 = calc_ema(closes, 50)
    ema20 = calc_ema(closes, 20)
    rsi14 = calc_rsi(closes, 14)
    adx14 = calc_adx(highs, lows, closes, 14)
    bb_w = calc_bb_width(closes, 20, 2.0)

    e200 = ema200[-1]
    e50 = ema50[-1]
    e20 = ema20[-1]
    rsi = rsi14[-1]
    adx = adx14[-1]
    bbw = bb_w[-1]

    if any(v is None for v in [e200, adx, bbw]):
        return None, f"Indicators not ready for {pair}"

    above_ema200 = price > e200
    adx_low = adx < TRIPLE_LOCK_ADX_MAX
    bb_narrow = bbw < TRIPLE_LOCK_BB_WIDTH_MAX

    is_trade = above_ema200 and adx_low and bb_narrow

    details = (
        f"{WATCH_PAIRS.get(pair, pair)} ${price:.2f} | "
        f"EMA20={e20:.2f} EMA50={e50:.2f} EMA200={e200:.2f} | "
        f"RSI={rsi:.1f} ADX={adx:.1f} BB%={bbw*100:.1f}% | "
        f"{'TRADE' if is_trade else 'NO TRADE'} "
        f"[{'OK' if above_ema200 else 'X'} P>EMA200] "
        f"[{'OK' if adx_low else 'X'} ADX<{TRIPLE_LOCK_ADX_MAX}] "
        f"[{'OK' if bb_narrow else 'X'} BB<{TRIPLE_LOCK_BB_WIDTH_MAX*100:.0f}%]"
    )
    return is_trade, details


# ─────────────────────────────────────────────────────────────────────
# MARTIN GRID MONITORING
# ─────────────────────────────────────────────────────────────────────

def martin_get(endpoint):
    """GET Martin API endpoint."""
    return http_get(f"{MARTIN_BASE}{endpoint}")


def martin_post(endpoint, data=None):
    """POST Martin API endpoint."""
    return http_post(f"{MARTIN_BASE}{endpoint}", data)


def get_active_grids():
    """Get list of active grids. Returns list of grid dicts or []."""
    data = martin_get("/api/grid/active")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("grids", data.get("data", []))
    return []


def get_balance():
    """Get balance info. Returns dict or None."""
    return martin_get("/api/balance")


def get_status():
    """Get Martin status. Returns dict or None."""
    return martin_get("/api/status")


def stop_grid(grid_id):
    """Stop a specific grid."""
    log(f"AUTO-STOP grid {grid_id}")
    result = martin_post(f"/api/grid/{grid_id}/stop")
    return result


def stop_all_grids():
    """Emergency stop all grids."""
    log("EMERGENCY STOP ALL GRIDS")
    grids = get_active_grids()
    for g in grids:
        gid = g.get("id", g.get("grid_id", "unknown"))
        stop_grid(gid)
    # Also try a global stop endpoint
    martin_post("/api/grid/stop-all")


# ─────────────────────────────────────────────────────────────────────
# PRICE MOVEMENT TRACKING
# ─────────────────────────────────────────────────────────────────────

def track_price(pair, price):
    """Track price for 1h movement detection. Returns move_pct or None."""
    now = time.time()
    if pair not in state["price_history_1h"]:
        state["price_history_1h"][pair] = []

    history = state["price_history_1h"][pair]
    history.append((now, price))

    # Keep only last 1h
    cutoff = now - 3600
    state["price_history_1h"][pair] = [(t, p) for t, p in history if t >= cutoff]
    history = state["price_history_1h"][pair]

    if len(history) < 2:
        return None

    oldest_price = history[0][1]
    if oldest_price == 0:
        return None

    move_pct = abs(price - oldest_price) / oldest_price * 100
    return move_pct


# ─────────────────────────────────────────────────────────────────────
# MAIN CHECK CYCLE
# ─────────────────────────────────────────────────────────────────────

def check_markets():
    """Check all markets — Triple Lock + price moves."""
    for pair, name in WATCH_PAIRS.items():
        try:
            # Triple Lock
            is_trade, details = check_triple_lock(pair)

            if is_trade is not None:
                prev = state["triple_lock"].get(pair)
                if prev is not None and prev != is_trade:
                    if is_trade:
                        write_channel(
                            f"TRIPLE LOCK ON {name}\n"
                            f"Conditions favorables — opportunite de grid.\n"
                            f"{details}"
                        )
                    else:
                        write_channel(
                            f"TRIPLE LOCK OFF {name}\n"
                            f"Conditions defavorables — danger.\n"
                            f"{details}"
                        )
                state["triple_lock"][pair] = is_trade

            # Price movement
            price, _ = fetch_ticker(pair)
            if price:
                move = track_price(pair, price)
                if move is not None and move >= PRICE_MOVE_ALERT_PCT:
                    write_channel(
                        f"MOUVEMENT {name}: {move:.1f}% en 1h (prix: ${price:.2f})"
                    )

            # Rate limit
            time.sleep(2)

        except Exception as e:
            log(f"Market check error for {pair}: {e}")


def check_martin():
    """Check Martin grid health."""
    try:
        grids = get_active_grids()
        balance_data = get_balance()
        status_data = get_status()

        current_grid_ids = set()

        for g in grids:
            gid = g.get("id", g.get("grid_id", "unknown"))
            current_grid_ids.add(gid)

            pair = g.get("pair", g.get("symbol", "???"))
            price = g.get("current_price", g.get("price", 0))
            lower = g.get("lower_bound", g.get("lower", g.get("range_low", 0)))
            upper = g.get("upper_bound", g.get("upper", g.get("range_high", 0)))
            pnl = g.get("unrealized_pnl", g.get("pnl", g.get("unrealized", 0)))
            rt_count = g.get("round_trips", g.get("rt", g.get("round_trip_count", 0)))

            # Ensure numeric
            try:
                price = float(price)
                lower = float(lower)
                upper = float(upper)
                pnl = float(pnl) if pnl else 0
                rt_count = int(rt_count) if rt_count else 0
            except (ValueError, TypeError):
                continue

            # --- Check: price out of range → auto stop ---
            if price > 0 and lower > 0 and upper > 0:
                if price < lower or price > upper:
                    write_channel(
                        f"PRIX HORS RANGE grid {gid} ({pair})\n"
                        f"Prix: ${price:.2f}, Range: ${lower:.2f}-${upper:.2f}\n"
                        f"AUTO-STOP de cette grid."
                    )
                    stop_grid(gid)
                    continue

            # --- Check: MaxLoss proximity ---
            if price > 0 and lower > 0 and upper > 0:
                range_size = upper - lower
                mid = (upper + lower) / 2
                if range_size > 0:
                    # Distance from nearest bound as fraction of half-range
                    dist_to_lower = price - lower
                    dist_to_upper = upper - price
                    min_dist = min(dist_to_lower, dist_to_upper)
                    half_range = range_size / 2

                    if min_dist / half_range < (1 - MAXLOSS_PROXIMITY_PCT):
                        bound_name = "LOWER" if dist_to_lower < dist_to_upper else "UPPER"
                        bound_val = lower if dist_to_lower < dist_to_upper else upper
                        write_channel(
                            f"MAXLOSS PROCHE grid {gid} ({pair})\n"
                            f"Prix: ${price:.2f}, {bound_name} bound: ${bound_val:.2f}\n"
                            f"Distance: {min_dist:.2f} ({min_dist/half_range*100:.0f}% du demi-range)"
                        )

            # --- Check: new round-trip ---
            prev_rt = state["last_rt_counts"].get(gid, 0)
            if rt_count > prev_rt and prev_rt > 0:
                write_channel(
                    f"ROUND-TRIP grid {gid} ({pair})\n"
                    f"RT #{rt_count} complete. PnL: {pnl:+.2f} USD"
                )
            state["last_rt_counts"][gid] = rt_count

        # --- Check: grid disappeared (maxLoss hit) ---
        for old_gid in state["active_grids"] - current_grid_ids:
            write_channel(
                f"GRID DISPARUE: {old_gid}\n"
                f"MaxLoss probablement atteint."
            )

        state["active_grids"] = current_grid_ids

        # --- Check: portfolio loss ---
        if balance_data:
            total = float(balance_data.get("total", balance_data.get("equity", 0)) or 0)
            available = float(balance_data.get("available", balance_data.get("free", 0)) or 0)
            unrealized = float(balance_data.get("unrealized_pnl",
                              balance_data.get("unrealized", 0)) or 0)

            if total > 0 and unrealized < 0:
                loss_pct = abs(unrealized) / total * 100

                if loss_pct >= LOSS_STOP_PCT:
                    write_channel(
                        f"PERTE > {LOSS_STOP_PCT}% — AUTO-STOP TOUTES LES GRIDS\n"
                        f"Perte non-realisee: {unrealized:.2f} USD ({loss_pct:.1f}% du portfolio)\n"
                        f"Balance: {total:.2f} USD"
                    )
                    stop_all_grids()

                elif loss_pct >= LOSS_WARN_PCT:
                    write_channel(
                        f"PERTE > {LOSS_WARN_PCT}%\n"
                        f"Perte non-realisee: {unrealized:.2f} USD ({loss_pct:.1f}% du portfolio)\n"
                        f"Balance: {total:.2f} USD"
                    )

    except Exception as e:
        log(f"Martin check error: {e}")


# ─────────────────────────────────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────────────────────────────────

def startup_report():
    """Initial status report on startup."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"Sentinel demarre — {now}"]

    for pair, name in WATCH_PAIRS.items():
        price, _ = fetch_ticker(pair)
        if price:
            lines.append(f"  {name}: ${price:.2f}")
        time.sleep(1)

    grids = get_active_grids()
    lines.append(f"  Martin: {len(grids)} grid(s) active(s)")

    msg = "\n".join(lines)
    write_channel(msg)


# ─────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────

def main():
    log("=== Sentinel starting ===")

    # Init channel file if needed
    if not os.path.exists(CHANNEL_FILE):
        try:
            with open(CHANNEL_FILE, "w") as f:
                f.write("# Niam-Bay Sentinel Channel\n")
        except Exception:
            pass

    startup_report()

    cycle = 0
    while running:
        cycle += 1
        try:
            check_markets()
            check_martin()
        except Exception as e:
            log(f"Cycle {cycle} error: {e}")

        # Sleep in small increments for responsive shutdown
        wait_until = time.time() + CHECK_INTERVAL
        while running and time.time() < wait_until:
            time.sleep(5)

    log("=== Sentinel stopped ===")
    send_telegram("Sentinel arrete.")


if __name__ == "__main__":
    main()

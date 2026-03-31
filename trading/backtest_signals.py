#!/usr/bin/env python3
"""
Backtest Signals — Multi-signal comparison on 90 days, multi-pairs
===================================================================
Teste 5 signaux d'entree sur 90 jours de donnees 1h pour BTC, ETH, SOL, DOT:

  a) EMA_TREND:       EMA50 > EMA200 AND RSI > 50
  b) EMA_CONFIRMED:   EMA50 > EMA200 for 3 consecutive AND RSI > 50 for 2 consecutive
  c) RSI_VETO:        EMA_TREND but NEVER open if RSI < 35
  d) STOCH_VETO:      EMA_TREND but NEVER open if RSI < 35 AND Stoch < 20
  e) BASELINE:        No filter (always on)

Grid NEUTRAL x5, spacing 1%, 10 niveaux, capital $20, max loss 15%

Sortie: trading/RESULTATS_EXTENDED.md (updated with signal comparison)
"""

import json
import math
import os
import time
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime, timezone

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RESULTS_MD = os.path.join(BASE_DIR, "RESULTATS_EXTENDED.md")
RESULTS_JSON = os.path.join(BASE_DIR, "results_signals.json")

PAIRS = {
    "BTC/USD": "XXBTZUSD",
    "ETH/USD": "XETHZUSD",
    "SOL/USD": "SOLUSD",
    "DOT/USD": "DOTUSD",
}

SIGNAL_NAMES = ["BASELINE", "EMA_TREND", "EMA_CONFIRMED", "RSI_VETO", "STOCH_VETO"]

CAPITAL = 20.0
LEVERAGE = 5
NUM_LEVELS = 10
SPACING_PCT = 1.0
MAX_LOSS_PCT = 15.0

MAKER_FEE = 0.0002
TAKER_FEE = 0.0005
FEE_PER_RT = MAKER_FEE + TAKER_FEE

DAYS = 90

# ============================================================
# 1. DATA FETCHING
# ============================================================

def fetch_kraken_ohlc(pair, interval=60, since=None):
    url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}"
    if since:
        url += f"&since={since}"
    req = urllib.request.Request(url, headers={"User-Agent": "niam-bay-signals/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        print(f"    ERROR: {e}")
        return None, None
    if data.get("error"):
        print(f"    Kraken error: {data['error']}")
        return None, None
    result = data.get("result", {})
    last_ts = result.get("last")
    ohlc_key = [k for k in result.keys() if k != "last"]
    if not ohlc_key:
        return None, None
    raw = result[ohlc_key[0]]
    candles = []
    for row in raw:
        ts = int(row[0])
        candles.append({
            "time": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[6]),
        })
    return candles, last_ts


def _load_csv(filepath):
    """Load candles from a CSV file (timestamp,open,high,low,close,volume)."""
    import csv
    candles = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts_str = row["timestamp"]
            # Parse timestamp, assume UTC if no timezone
            if "+" in ts_str or ts_str.endswith("Z"):
                dt = datetime.fromisoformat(ts_str)
            else:
                dt = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
            candles.append({
                "time": dt.isoformat(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            })
    return candles


# CSV files from download_3months.py (CryptoCompare, ~2196 candles = 3 months)
CSV_MAP = {
    "XXBTZUSD": os.path.join(DATA_DIR, "XXBTZUSD_1h_3mo.csv"),
    "XETHZUSD": os.path.join(DATA_DIR, "ETHUSD_1h_3mo.csv"),
    "SOLUSD": os.path.join(DATA_DIR, "SOLUSD_1h_3mo.csv"),
    "DOTUSD": os.path.join(DATA_DIR, "DOTUSD_1h_3mo.csv"),
}


def load_or_fetch_pair(pair_name, kraken_pair, days=DAYS):
    cache_file = os.path.join(DATA_DIR, f"{kraken_pair.lower()}_1h_{days}d.json")

    # 1. Try JSON cache
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            raw = json.load(f)
        file_age = time.time() - os.path.getmtime(cache_file)
        if file_age < 6 * 3600 and len(raw) > days * 20:
            print(f"    Cache: {len(raw)} candles")
            return _parse_candles(raw)

    # 2. Try CSV files (3 months data from CryptoCompare)
    csv_path = CSV_MAP.get(kraken_pair)
    if csv_path and os.path.exists(csv_path):
        print(f"    CSV: {csv_path}...", end="", flush=True)
        csv_candles = _load_csv(csv_path)

        # Also fetch latest from Kraken to fill gap from CSV end to now
        kraken_candles, _ = fetch_kraken_ohlc(kraken_pair, interval=60)
        if kraken_candles:
            csv_candles.extend(kraken_candles)

        # Deduplicate
        seen = set()
        unique = []
        for c in csv_candles:
            ts = c["time"]
            if ts not in seen:
                seen.add(ts)
                unique.append(c)
        unique.sort(key=lambda x: x["time"])

        print(f" {len(unique)} candles (CSV + Kraken)")

        # Cache the result
        with open(cache_file, "w") as f:
            json.dump(unique, f)
        return _parse_candles(unique)

    # 3. Fallback: fetch from Kraken API (max ~720 candles = 30 days)
    print(f"    Fetching {pair_name} from Kraken...", end="", flush=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    now_ts = int(time.time())
    start_ts = now_ts - (days * 24 * 3600)
    all_candles = []
    since = start_ts

    for attempt in range(6):
        batch, last = fetch_kraken_ohlc(kraken_pair, interval=60, since=since)
        if not batch:
            break
        all_candles.extend(batch)
        last_candle_ts = _iso_to_ts(batch[-1]["time"])
        print(".", end="", flush=True)
        if last_candle_ts >= now_ts - 3600:
            break
        if last and int(last) > since:
            since = int(last)
        else:
            since = int(last_candle_ts) + 1
        time.sleep(1.5)

    print(f" {len(all_candles)} candles (Kraken only)")

    seen = set()
    unique = []
    for c in all_candles:
        ts = c["time"]
        if ts not in seen:
            seen.add(ts)
            unique.append(c)
    unique.sort(key=lambda x: x["time"])

    with open(cache_file, "w") as f:
        json.dump(unique, f)
    return _parse_candles(unique)


def _iso_to_ts(iso_str):
    return datetime.fromisoformat(iso_str).timestamp()


def _parse_candles(raw):
    candles = []
    for c in raw:
        candles.append({
            "time": datetime.fromisoformat(c["time"]) if isinstance(c["time"], str) else c["time"],
            "open": c["open"],
            "high": c["high"],
            "low": c["low"],
            "close": c["close"],
            "volume": c["volume"],
        })
    return candles


# ============================================================
# 2. INDICATORS
# ============================================================

def calc_ema(prices, period):
    if len(prices) < period:
        return [None] * len(prices)
    result = [None] * (period - 1)
    sma = sum(prices[:period]) / period
    result.append(sma)
    k = 2 / (period + 1)
    for i in range(period, len(prices)):
        result.append(prices[i] * k + result[-1] * (1 - k))
    return result


def calc_rsi(prices, period=14):
    if len(prices) < period + 1:
        return [None] * len(prices)
    result = [None] * period
    gains, losses = [], []
    for i in range(1, period + 1):
        d = prices[i] - prices[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    avg_g = sum(gains) / period
    avg_l = sum(losses) / period

    def rsi_val(ag, al):
        if al == 0:
            return 100.0
        return 100 - (100 / (1 + ag / al))

    result.append(rsi_val(avg_g, avg_l))
    for i in range(period + 1, len(prices)):
        d = prices[i] - prices[i - 1]
        avg_g = (avg_g * (period - 1) + max(d, 0)) / period
        avg_l = (avg_l * (period - 1) + max(-d, 0)) / period
        result.append(rsi_val(avg_g, avg_l))
    return result


def calc_stochastic(highs, lows, closes, k_period=14):
    n = len(closes)
    k_list = [None] * n
    for i in range(k_period - 1, n):
        lo = min(lows[i - k_period + 1: i + 1])
        hi = max(highs[i - k_period + 1: i + 1])
        if hi == lo:
            k_list[i] = 50.0
        else:
            k_list[i] = (closes[i] - lo) / (hi - lo) * 100
    return k_list


# ============================================================
# 3. SIGNALS
# ============================================================

def compute_all_signals(candles):
    """Compute all 5 signals for each candle."""
    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    n = len(candles)

    ema50 = calc_ema(closes, 50)
    ema200 = calc_ema(closes, 200)
    rsi14 = calc_rsi(closes, 14)
    stoch_k = calc_stochastic(highs, lows, closes, k_period=14)

    # Pre-compute EMA_TREND raw boolean for consecutive tracking
    ema_trend_raw = []
    rsi_above_50_raw = []
    for i in range(n):
        et = (ema50[i] is not None and ema200[i] is not None
              and ema50[i] > ema200[i]
              and rsi14[i] is not None and rsi14[i] > 50)
        ema_trend_raw.append(et)

        ema_cross = (ema50[i] is not None and ema200[i] is not None
                     and ema50[i] > ema200[i])
        rsi_ok = (rsi14[i] is not None and rsi14[i] > 50)
        rsi_above_50_raw.append(rsi_ok)

    # For EMA_CONFIRMED: track consecutive candles
    ema_cross_consec = [0] * n
    rsi_above_consec = [0] * n
    for i in range(n):
        ema_cross = (ema50[i] is not None and ema200[i] is not None
                     and ema50[i] > ema200[i])
        if ema_cross:
            ema_cross_consec[i] = (ema_cross_consec[i - 1] + 1) if i > 0 else 1
        rsi_ok = (rsi14[i] is not None and rsi14[i] > 50)
        if rsi_ok:
            rsi_above_consec[i] = (rsi_above_consec[i - 1] + 1) if i > 0 else 1

    signals = []
    circuit_breaker_rsi_events = 0
    circuit_breaker_stoch_events = 0

    for i in range(n):
        rsi_val = rsi14[i]
        stoch_val = stoch_k[i]

        # a) EMA_TREND
        ema_trend = ema_trend_raw[i]

        # b) EMA_CONFIRMED: 3 consecutive EMA cross + 2 consecutive RSI > 50
        ema_confirmed = (ema_cross_consec[i] >= 3 and rsi_above_consec[i] >= 2)

        # c) RSI_VETO: EMA_TREND but circuit breaker if RSI < 35
        rsi_veto_blocked = (rsi_val is not None and rsi_val < 35)
        rsi_veto = ema_trend and not rsi_veto_blocked
        if ema_trend and rsi_veto_blocked:
            circuit_breaker_rsi_events += 1

        # d) STOCH_VETO: EMA_TREND but circuit breaker if RSI < 35 AND Stoch < 20
        stoch_veto_blocked = (rsi_val is not None and rsi_val < 35
                              and stoch_val is not None and stoch_val < 20)
        stoch_veto = ema_trend and not stoch_veto_blocked
        if ema_trend and stoch_veto_blocked:
            circuit_breaker_stoch_events += 1

        signals.append({
            "BASELINE": True,
            "EMA_TREND": ema_trend,
            "EMA_CONFIRMED": ema_confirmed,
            "RSI_VETO": rsi_veto,
            "STOCH_VETO": stoch_veto,
            "rsi": rsi_val,
            "stoch_k": stoch_val,
            "ema50": ema50[i],
            "ema200": ema200[i],
        })

    return signals, circuit_breaker_rsi_events, circuit_breaker_stoch_events


# ============================================================
# 4. GRID SIMULATION
# ============================================================

def simulate_grid(candles, signals, signal_key,
                  capital=CAPITAL, leverage=LEVERAGE,
                  num_levels=NUM_LEVELS, spacing_pct=SPACING_PCT,
                  max_loss_pct=MAX_LOSS_PCT):
    n = len(candles)
    notional = (capital * leverage) / num_levels

    equity = capital
    peak_eq = capital
    max_dd = 0.0
    total_pnl = 0.0
    round_trips = 0
    wins = 0
    losses_count = 0
    open_pos = []
    daily_pnl = defaultdict(float)
    stopped = False
    recenterings = 0
    trade_pnls = []

    in_grid = False
    grid_center = None
    grid_low = None
    grid_high = None
    grid_levels = []
    filled_buys = set()
    filled_sells = set()
    spacing = 0.0
    signal_active_candles = 0
    entries = 0

    current_streak = 0
    max_consec_wins = 0
    max_consec_losses = 0

    def build_grid(center):
        nonlocal grid_center, grid_low, grid_high, grid_levels
        nonlocal filled_buys, filled_sells, spacing
        spacing = center * spacing_pct / 100
        grid_center = center
        grid_low = center - spacing * num_levels / 2
        grid_high = center + spacing * num_levels / 2
        grid_levels = [grid_low + i * spacing for i in range(num_levels + 1)]
        grid_levels.sort()
        filled_buys = set()
        filled_sells = set()

    def record_trade(pnl_n):
        nonlocal wins, losses_count, current_streak, max_consec_wins, max_consec_losses
        trade_pnls.append(pnl_n)
        if pnl_n > 0:
            wins += 1
            current_streak = (current_streak + 1) if current_streak > 0 else 1
            max_consec_wins = max(max_consec_wins, current_streak)
        else:
            losses_count += 1
            current_streak = (current_streak - 1) if current_streak < 0 else -1
            max_consec_losses = max(max_consec_losses, abs(current_streak))

    def close_all(price, day_key):
        nonlocal total_pnl, equity, round_trips
        for pos in list(open_pos):
            side, entry, size = pos
            if side == "long":
                pnl_g = (price - entry) / entry * size
            else:
                pnl_g = (entry - price) / entry * size
            fee = size * FEE_PER_RT
            pnl_n = pnl_g - fee
            total_pnl += pnl_n
            equity += pnl_n
            daily_pnl[day_key] += pnl_n
            round_trips += 1
            record_trade(pnl_n)
        open_pos.clear()

    for i, candle in enumerate(candles):
        dt = candle["time"]
        o, h, l, c = candle["open"], candle["high"], candle["low"], candle["close"]
        day_key = dt.strftime("%Y-%m-%d") if hasattr(dt, 'strftime') else str(dt)[:10]
        active = signals[i][signal_key]

        if active:
            signal_active_candles += 1

        if active and not in_grid:
            build_grid(c)
            in_grid = True
            entries += 1
        elif not active and in_grid:
            close_all(c, day_key)
            in_grid = False
            grid_levels = []

        if not in_grid:
            if equity > peak_eq:
                peak_eq = equity
            continue

        for level in grid_levels:
            if level < l or level > h:
                continue
            if level < grid_center and level not in filled_buys:
                closed = False
                for j, pos in enumerate(open_pos):
                    if pos[0] == "short":
                        ep, sz = pos[1], pos[2]
                        pnl_g = (ep - level) / ep * sz
                        fee = sz * FEE_PER_RT
                        pnl_n = pnl_g - fee
                        total_pnl += pnl_n
                        equity += pnl_n
                        daily_pnl[day_key] += pnl_n
                        round_trips += 1
                        record_trade(pnl_n)
                        open_pos.pop(j)
                        closed = True
                        break
                if not closed:
                    open_pos.append(("long", level, notional))
                filled_buys.add(level)
            elif level >= grid_center and level not in filled_sells:
                closed = False
                for j, pos in enumerate(open_pos):
                    if pos[0] == "long":
                        ep, sz = pos[1], pos[2]
                        pnl_g = (level - ep) / ep * sz
                        fee = sz * FEE_PER_RT
                        pnl_n = pnl_g - fee
                        total_pnl += pnl_n
                        equity += pnl_n
                        daily_pnl[day_key] += pnl_n
                        round_trips += 1
                        record_trade(pnl_n)
                        open_pos.pop(j)
                        closed = True
                        break
                if not closed:
                    open_pos.append(("short", level, notional))
                filled_sells.add(level)

        if c < grid_low * 0.98 or c > grid_high * 1.02:
            close_all(c, day_key)
            build_grid(c)
            recenterings += 1

        unrealized = sum(
            ((c - ep) / ep * sz if sd == "long" else (ep - c) / ep * sz)
            for sd, ep, sz in open_pos
        )
        current_eq = equity + unrealized
        if current_eq > peak_eq:
            peak_eq = current_eq
        dd = (peak_eq - current_eq) / peak_eq * 100 if peak_eq > 0 else 0
        if dd > max_dd:
            max_dd = dd

        if dd > max_loss_pct:
            close_all(c, day_key)
            stopped = True
            break

    if open_pos and not stopped:
        last = candles[-1]
        lk = last["time"].strftime("%Y-%m-%d") if hasattr(last["time"], 'strftime') else str(last["time"])[:10]
        close_all(last["close"], lk)

    days_total = (candles[-1]["time"] - candles[0]["time"]).total_seconds() / 86400
    win_rate = wins / round_trips * 100 if round_trips > 0 else 0.0
    pnl_per_day = total_pnl / days_total if days_total > 0 else 0.0

    daily_returns = list(daily_pnl.values())
    if len(daily_returns) > 1:
        mean_r = sum(daily_returns) / len(daily_returns)
        std_r = math.sqrt(sum((r - mean_r) ** 2 for r in daily_returns) / (len(daily_returns) - 1))
        sharpe = (mean_r / std_r) * math.sqrt(365) if std_r > 0 else 0.0
    else:
        sharpe = 0.0

    best_trade = max(trade_pnls) if trade_pnls else 0.0
    worst_trade = min(trade_pnls) if trade_pnls else 0.0

    return {
        "round_trips": round_trips,
        "wins": wins,
        "losses": losses_count,
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "pnl_pct": total_pnl / capital * 100,
        "max_drawdown_pct": max_dd,
        "sharpe": sharpe,
        "best_trade": best_trade,
        "worst_trade": worst_trade,
        "max_consec_wins": max_consec_wins,
        "max_consec_losses": max_consec_losses,
        "pnl_per_day": pnl_per_day,
        "days": days_total,
        "signal_active_candles": signal_active_candles,
        "signal_active_pct": signal_active_candles / len(candles) * 100 if candles else 0,
        "entries": entries,
        "stopped": stopped,
    }


# ============================================================
# 5. REPORT
# ============================================================

def generate_report(all_results, pair_meta, cb_stats, output_path):
    lines = []
    lines.append("# Resultats Backtest Etendu (90 jours)")
    lines.append("")
    lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("**Auteur:** Niam-Bay")
    lines.append("**Script:** `trading/backtest_signals.py`")
    lines.append("")

    all_starts = [m["period_start"] for m in pair_meta.values()]
    all_ends = [m["period_end"] for m in pair_meta.values()]
    lines.append(f"## Periode: {min(all_starts)} -> {max(all_ends)}")
    lines.append("")

    lines.append("## Parametres")
    lines.append("")
    lines.append("| Parametre | Valeur |")
    lines.append("|-----------|--------|")
    lines.append("| Grid mode | NEUTRAL |")
    lines.append(f"| Capital | ${CAPITAL:.0f} |")
    lines.append(f"| Levier | x{LEVERAGE} |")
    lines.append(f"| Niveaux | {NUM_LEVELS} |")
    lines.append(f"| Spacing | {SPACING_PCT}% |")
    lines.append(f"| Max loss stop | {MAX_LOSS_PCT}% |")
    lines.append(f"| Donnees | {DAYS} jours, candles 1h, Kraken API |")
    lines.append("")
    lines.append("## Signaux testes")
    lines.append("")
    lines.append("| Signal | Description |")
    lines.append("|--------|-------------|")
    lines.append("| BASELINE | Pas de filtre (grid toujours active) |")
    lines.append("| EMA_TREND | EMA50 > EMA200 AND RSI > 50 |")
    lines.append("| EMA_CONFIRMED | EMA50 > EMA200 pour 3 candles consecutives AND RSI > 50 pour 2 consecutives |")
    lines.append("| RSI_VETO | EMA_TREND + circuit breaker si RSI < 35 |")
    lines.append("| STOCH_VETO | EMA_TREND + circuit breaker si RSI < 35 ET Stoch < 20 |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Per pair
    for pair_name in PAIRS:
        if pair_name not in all_results:
            continue

        meta = pair_meta[pair_name]
        lines.append(f"## {pair_name}")
        lines.append("")
        lines.append(f"- Candles: {meta['candles']} | Periode: {meta['period_start']} -> {meta['period_end']}")
        lines.append(f"- Open: ${meta['open']:,.2f} | Close: ${meta['close']:,.2f} | HODL: {meta['hodl_pct']:+.2f}%")
        lines.append("")

        lines.append("| Signal | Win Rate | PnL$ | PnL% | Max DD | Sharpe | Trades | Time Active | Consec W/L |")
        lines.append("|--------|----------|------|------|--------|--------|--------|-------------|------------|")

        for sig_name in SIGNAL_NAMES:
            r = all_results[pair_name][sig_name]
            stop_mark = " STOP" if r["stopped"] else ""
            lines.append(
                f"| {sig_name} "
                f"| {r['win_rate']:.1f}% "
                f"| ${r['total_pnl']:+.2f} "
                f"| {r['pnl_pct']:+.1f}% "
                f"| {r['max_drawdown_pct']:.2f}%{stop_mark} "
                f"| {r['sharpe']:.2f} "
                f"| {r['round_trips']} "
                f"| {r['signal_active_pct']:.1f}% "
                f"| {r['max_consec_wins']}/{r['max_consec_losses']} |"
            )

        lines.append(f"| HODL | - | - | {meta['hodl_pct']:+.2f}% | - | - | - | - | - |")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Aggregate comparison
    lines.append("## Meilleur Signal Global")
    lines.append("")
    lines.append("| Signal | Avg Win Rate | Avg PnL% | Avg Max DD | Avg Sharpe | Pairs Stopped |")
    lines.append("|--------|-------------|----------|------------|------------|---------------|")

    best_signal = None
    best_avg_sharpe = -999

    for sig_name in SIGNAL_NAMES:
        wr_list = []
        pnl_list = []
        dd_list = []
        sharpe_list = []
        stops = 0
        for pair_name in PAIRS:
            if pair_name not in all_results:
                continue
            r = all_results[pair_name][sig_name]
            wr_list.append(r["win_rate"])
            pnl_list.append(r["pnl_pct"])
            dd_list.append(r["max_drawdown_pct"])
            sharpe_list.append(r["sharpe"])
            if r["stopped"]:
                stops += 1

        if not wr_list:
            continue

        avg_wr = sum(wr_list) / len(wr_list)
        avg_pnl = sum(pnl_list) / len(pnl_list)
        avg_dd = sum(dd_list) / len(dd_list)
        avg_sharpe = sum(sharpe_list) / len(sharpe_list)

        lines.append(
            f"| {sig_name} "
            f"| {avg_wr:.1f}% "
            f"| {avg_pnl:+.1f}% "
            f"| {avg_dd:.2f}% "
            f"| {avg_sharpe:.2f} "
            f"| {stops}/{len(wr_list)} |"
        )

        if avg_sharpe > best_avg_sharpe:
            best_avg_sharpe = avg_sharpe
            best_signal = sig_name

    lines.append("")

    if best_signal:
        lines.append(f"**Recommandation: {best_signal}** (meilleur Sharpe moyen: {best_avg_sharpe:.2f})")
    lines.append("")

    # Circuit breaker analysis
    lines.append("## Circuit Breaker Analysis")
    lines.append("")
    lines.append("Nombre de candles ou le circuit breaker aurait bloque EMA_TREND:")
    lines.append("")
    lines.append("| Paire | RSI_VETO events | STOCH_VETO events |")
    lines.append("|-------|-----------------|-------------------|")
    for pair_name in PAIRS:
        if pair_name not in cb_stats:
            continue
        cb = cb_stats[pair_name]
        lines.append(f"| {pair_name} | {cb['rsi_events']} | {cb['stoch_events']} |")
    lines.append("")

    # Analysis text
    total_rsi = sum(cb["rsi_events"] for cb in cb_stats.values())
    total_stoch = sum(cb["stoch_events"] for cb in cb_stats.values())
    lines.append(f"- **RSI_VETO** aurait bloque {total_rsi} candles au total (RSI < 35 pendant EMA_TREND)")
    lines.append(f"- **STOCH_VETO** aurait bloque {total_stoch} candles (RSI < 35 ET Stoch < 20 pendant EMA_TREND)")
    lines.append("")

    # Check if veto improved results
    for pair_name in PAIRS:
        if pair_name not in all_results:
            continue
        r_ema = all_results[pair_name]["EMA_TREND"]
        r_veto = all_results[pair_name]["RSI_VETO"]
        if r_veto["max_drawdown_pct"] < r_ema["max_drawdown_pct"]:
            dd_save = r_ema["max_drawdown_pct"] - r_veto["max_drawdown_pct"]
            lines.append(f"- **{pair_name}**: RSI_VETO a reduit le DD de {dd_save:.2f}pp")
        elif r_veto["max_drawdown_pct"] == r_ema["max_drawdown_pct"]:
            lines.append(f"- **{pair_name}**: RSI_VETO = meme DD que EMA_TREND (pas d'impact)")
        else:
            lines.append(f"- **{pair_name}**: RSI_VETO n'a pas ameliore le DD")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Fichiers")
    lines.append("")
    lines.append("- Script: `trading/backtest_signals.py`")
    lines.append("- Resultats JSON: `trading/results_signals.json`")
    lines.append(f"- Cache: `trading/data/`")
    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Rapport: {output_path}")


# ============================================================
# 6. MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 65)
    print("BACKTEST SIGNALS — Multi-signal, multi-paires, 90 jours")
    print("=" * 65)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    all_results = {}
    pair_meta = {}
    cb_stats = {}

    for pair_name, kraken_pair in PAIRS.items():
        print(f"[{pair_name}]")
        candles = load_or_fetch_pair(pair_name, kraken_pair, days=DAYS)

        if not candles or len(candles) < 210:
            print(f"  SKIP: {len(candles) if candles else 0} candles (<210)")
            continue

        now_ts = candles[-1]["time"].timestamp()
        cutoff_ts = now_ts - (DAYS * 24 * 3600)
        candles = [c for c in candles if c["time"].timestamp() >= cutoff_ts]

        if len(candles) < 210:
            print(f"  SKIP apres filtre: {len(candles)} candles (<210)")
            continue

        t0 = candles[0]["time"]
        t1 = candles[-1]["time"]
        days_total = (t1 - t0).total_seconds() / 86400

        meta = {
            "period_start": t0.strftime("%Y-%m-%d"),
            "period_end": t1.strftime("%Y-%m-%d"),
            "candles": len(candles),
            "days": days_total,
            "open": candles[0]["open"],
            "close": candles[-1]["close"],
            "high": max(c["high"] for c in candles),
            "low": min(c["low"] for c in candles),
            "hodl_pct": (candles[-1]["close"] - candles[0]["open"]) / candles[0]["open"] * 100,
        }
        pair_meta[pair_name] = meta

        print(f"  {meta['period_start']} -> {meta['period_end']} ({days_total:.0f}j, {len(candles)} candles)")

        # Compute signals
        signals, rsi_events, stoch_events = compute_all_signals(candles)
        cb_stats[pair_name] = {"rsi_events": rsi_events, "stoch_events": stoch_events}

        # Run all simulations
        pair_results = {}
        for sig_name in SIGNAL_NAMES:
            print(f"  {sig_name}...", end="", flush=True)
            r = simulate_grid(candles, signals, sig_name)
            pair_results[sig_name] = r
            print(f" WR {r['win_rate']:.1f}% PnL ${r['total_pnl']:+.2f} DD {r['max_drawdown_pct']:.2f}%")

        all_results[pair_name] = pair_results
        print()

    if not all_results:
        print("ERREUR: aucune paire testee.")
        exit(1)

    # Save JSON
    json_out = {}
    for pair_name, results in all_results.items():
        json_out[pair_name] = {
            sig_name: {k: v for k, v in r.items()}
            for sig_name, r in results.items()
        }
    with open(RESULTS_JSON, "w") as f:
        json.dump({"meta": pair_meta, "cb_stats": cb_stats, "results": json_out}, f, indent=2, default=str)
    print(f"  JSON: {RESULTS_JSON}")

    # Generate report
    generate_report(all_results, pair_meta, cb_stats, RESULTS_MD)

    # Final summary table
    print()
    print("=" * 80)
    print("TABLEAU FINAL — Meilleur signal par paire")
    print("=" * 80)
    print(f"{'Paire':<10} {'Signal':<16} {'WR':>6} {'PnL%':>7} {'MaxDD':>7} {'Sharpe':>7}")
    print("-" * 60)

    for pair_name in PAIRS:
        if pair_name not in all_results:
            continue
        best_sig = None
        best_sh = -999
        for sig_name in SIGNAL_NAMES:
            r = all_results[pair_name][sig_name]
            if r["sharpe"] > best_sh:
                best_sh = r["sharpe"]
                best_sig = sig_name
        r = all_results[pair_name][best_sig]
        print(f"  {pair_name:<10} {best_sig:<16} {r['win_rate']:5.1f}% {r['pnl_pct']:+6.1f}% {r['max_drawdown_pct']:6.2f}% {r['sharpe']:+6.2f}")

    print()
    print("Done.")

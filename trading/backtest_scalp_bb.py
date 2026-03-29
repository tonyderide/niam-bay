#!/usr/bin/env python
"""
Backtest Scalp Bollinger Bands — ETH, DOT, SOL sur 3 mois Kraken 1h
Compare: Scalp BB / Grid classique x5 / Cash / Grid + Scalp combiné
"""

import json
import time
import urllib.request
import math
from datetime import datetime, timezone
from collections import defaultdict
from itertools import product

# === CONFIG ===
PAIRS = {
    "ETHUSD": "XETHZUSD",
    "DOTUSD": "DOTUSD",
    "SOLUSD": "SOLUSD",
}
INTERVAL = 60  # 1h
SINCE = int(time.time()) - 90 * 86400  # 3 months ago
BB_PERIOD = 20
BB_STD = 2
CAPITAL = 16.0
LEVERAGE = 2
TRADING_HOURS = range(8, 22)  # 08:00-21:59 UTC
TP_OPTIONS = [0.005, 0.01, 0.02]  # 0.5%, 1%, 2%
SL_OPTIONS = [0.005, 0.01, 0.02]  # 0.5%, 1%, 2%
KRAKEN_FEE = 0.0026  # taker fee 0.26%


def fetch_ohlc(pair_key, pair_api):
    """Fetch 1h candles from Kraken. Paginate if needed."""
    all_candles = []
    since = SINCE
    print(f"  Fetching {pair_key}...")
    while True:
        url = f"https://api.kraken.com/0/public/OHLC?pair={pair_key}&interval={INTERVAL}&since={since}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "niam-bay-backtest"})
            resp = urllib.request.urlopen(req, timeout=30)
            data = json.loads(resp.read())
        except Exception as e:
            print(f"    Error fetching {pair_key}: {e}")
            time.sleep(2)
            continue

        if data.get("error") and len(data["error"]) > 0:
            print(f"    API error: {data['error']}")
            break

        result = data.get("result", {})
        # Find the candle key (might differ from pair_key)
        candle_key = None
        for k in result:
            if k != "last":
                candle_key = k
                break
        if not candle_key:
            break

        candles = result[candle_key]
        if not candles:
            break

        all_candles.extend(candles)
        new_since = result.get("last", 0)
        if new_since <= since or len(candles) < 500:
            break
        since = new_since
        time.sleep(1)  # rate limit

    # Parse: [time, open, high, low, close, vwap, volume, count]
    parsed = []
    seen = set()
    for c in all_candles:
        ts = int(c[0])
        if ts in seen:
            continue
        seen.add(ts)
        parsed.append({
            "ts": ts,
            "dt": datetime.fromtimestamp(ts, tz=timezone.utc),
            "open": float(c[1]),
            "high": float(c[2]),
            "low": float(c[3]),
            "close": float(c[4]),
            "volume": float(c[6]),
        })
    parsed.sort(key=lambda x: x["ts"])
    print(f"    Got {len(parsed)} candles from {parsed[0]['dt'].strftime('%Y-%m-%d')} to {parsed[-1]['dt'].strftime('%Y-%m-%d')}")
    return parsed


def calc_bollinger(candles, period=BB_PERIOD, std_mult=BB_STD):
    """Calculate Bollinger Bands on close prices."""
    closes = [c["close"] for c in candles]
    upper, middle, lower = [], [], []
    for i in range(len(closes)):
        if i < period - 1:
            upper.append(None)
            middle.append(None)
            lower.append(None)
            continue
        window = closes[i - period + 1: i + 1]
        sma = sum(window) / period
        variance = sum((x - sma) ** 2 for x in window) / period
        std = math.sqrt(variance)
        middle.append(sma)
        upper.append(sma + std_mult * std)
        lower.append(sma - std_mult * std)
    return upper, middle, lower


def backtest_scalp_bb(candles, tp_pct, sl_pct, capital=CAPITAL, leverage=LEVERAGE):
    """Run scalp BB backtest with given TP/SL."""
    upper, middle, lower = calc_bollinger(candles)

    balance = capital
    position = None  # {"side": "long"/"short", "entry": price, "size": units}
    trades = []
    peak_balance = capital
    max_drawdown = 0
    hour_profits = defaultdict(float)
    hour_counts = defaultdict(int)

    for i in range(len(candles)):
        if upper[i] is None:
            continue

        c = candles[i]
        hour = c["dt"].hour
        price = c["close"]
        high = c["high"]
        low = c["low"]

        # Check exit on current candle (using high/low)
        if position:
            entry = position["entry"]
            side = position["side"]
            size = position["size"]

            if side == "long":
                # Check SL first (low of candle)
                sl_price = entry * (1 - sl_pct)
                tp_price = entry * (1 + tp_pct)
                if low <= sl_price:
                    pnl = -sl_pct * size * leverage - 2 * KRAKEN_FEE * size * leverage
                    balance += pnl
                    trades.append({"side": "long", "entry": entry, "exit": sl_price, "pnl": pnl, "result": "SL", "hour": position["hour"]})
                    hour_profits[position["hour"]] += pnl
                    hour_counts[position["hour"]] += 1
                    position = None
                elif high >= tp_price:
                    pnl = tp_pct * size * leverage - 2 * KRAKEN_FEE * size * leverage
                    balance += pnl
                    trades.append({"side": "long", "entry": entry, "exit": tp_price, "pnl": pnl, "result": "TP", "hour": position["hour"]})
                    hour_profits[position["hour"]] += pnl
                    hour_counts[position["hour"]] += 1
                    position = None
            else:  # short
                sl_price = entry * (1 + sl_pct)
                tp_price = entry * (1 - tp_pct)
                if high >= sl_price:
                    pnl = -sl_pct * size * leverage - 2 * KRAKEN_FEE * size * leverage
                    balance += pnl
                    trades.append({"side": "short", "entry": entry, "exit": sl_price, "pnl": pnl, "result": "SL", "hour": position["hour"]})
                    hour_profits[position["hour"]] += pnl
                    hour_counts[position["hour"]] += 1
                    position = None
                elif low <= tp_price:
                    pnl = tp_pct * size * leverage - 2 * KRAKEN_FEE * size * leverage
                    balance += pnl
                    trades.append({"side": "short", "entry": entry, "exit": tp_price, "pnl": pnl, "result": "TP", "hour": position["hour"]})
                    hour_profits[position["hour"]] += pnl
                    hour_counts[position["hour"]] += 1
                    position = None

        # Track drawdown
        if balance > peak_balance:
            peak_balance = balance
        dd = (peak_balance - balance) / peak_balance
        if dd > max_drawdown:
            max_drawdown = dd

        # Only enter during trading hours, no existing position
        if position is None and hour in TRADING_HOURS:
            size = balance  # use full balance as margin
            if price <= lower[i]:
                position = {"side": "long", "entry": price, "size": size, "hour": hour}
            elif price >= upper[i]:
                position = {"side": "short", "entry": price, "size": size, "hour": hour}

    # Close any remaining position at last close
    if position and len(candles) > 0:
        entry = position["entry"]
        price = candles[-1]["close"]
        side = position["side"]
        size = position["size"]
        if side == "long":
            pnl_pct = (price - entry) / entry
        else:
            pnl_pct = (entry - price) / entry
        pnl = pnl_pct * size * leverage - 2 * KRAKEN_FEE * size * leverage
        balance += pnl
        trades.append({"side": side, "entry": entry, "exit": price, "pnl": pnl, "result": "CLOSE", "hour": position["hour"]})

    # Stats
    n_trades = len(trades)
    wins = sum(1 for t in trades if t["pnl"] > 0)
    win_rate = wins / n_trades * 100 if n_trades > 0 else 0
    total_pnl = balance - capital
    days = (candles[-1]["ts"] - candles[0]["ts"]) / 86400 if len(candles) > 1 else 1
    profit_per_day = total_pnl / days if days > 0 else 0

    # Best hour
    best_hour = None
    best_hour_pnl = -999
    for h, p in hour_profits.items():
        if p > best_hour_pnl:
            best_hour_pnl = p
            best_hour = h

    return {
        "n_trades": n_trades,
        "wins": wins,
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "final_balance": balance,
        "max_drawdown": max_drawdown * 100,
        "profit_per_day": profit_per_day,
        "best_hour": best_hour,
        "best_hour_pnl": best_hour_pnl,
        "days": days,
        "trades": trades,
    }


def backtest_grid(candles, capital=CAPITAL, leverage=5, spacing_pct=0.01, n_levels=10):
    """Simulate a simple grid strategy x5 spacing 1%."""
    balance = capital
    peak_balance = capital
    max_drawdown = 0
    trades = []

    # Grid: place buy/sell orders around current price at spacing intervals
    # Simplified: at each candle, check if price moved enough to trigger grid levels
    grid_size = capital * leverage / n_levels  # $ per grid level
    last_price = candles[BB_PERIOD]["close"] if len(candles) > BB_PERIOD else candles[0]["close"]
    active_buys = []
    active_sells = []

    def reset_grid(ref_price):
        buys = []
        sells = []
        for l in range(1, n_levels // 2 + 1):
            buys.append(ref_price * (1 - l * spacing_pct))
            sells.append(ref_price * (1 + l * spacing_pct))
        return buys, sells

    active_buys, active_sells = reset_grid(last_price)
    round_trips = 0

    for i in range(BB_PERIOD, len(candles)):
        c = candles[i]
        low = c["low"]
        high = c["high"]

        # Check buy fills
        filled_buys = [p for p in active_buys if low <= p]
        for buy_price in sorted(filled_buys, reverse=True):
            # Buy filled, immediately place sell at buy_price + spacing
            sell_target = buy_price * (1 + spacing_pct)
            active_buys.remove(buy_price)
            active_sells.append(sell_target)

        # Check sell fills
        filled_sells = [p for p in active_sells if high >= p]
        for sell_price in sorted(filled_sells):
            # Sell filled = round trip complete
            profit = grid_size * spacing_pct * leverage - 2 * KRAKEN_FEE * grid_size * leverage
            balance += profit
            round_trips += 1
            active_sells.remove(sell_price)
            # Replace buy level
            buy_target = sell_price * (1 - spacing_pct)
            active_buys.append(buy_target)
            trades.append({"pnl": profit, "ts": c["ts"]})

        # Drawdown from price move (unrealized)
        if balance > peak_balance:
            peak_balance = balance
        dd = (peak_balance - balance) / peak_balance if peak_balance > 0 else 0
        if dd > max_drawdown:
            max_drawdown = dd

        # Reset grid if price drifted too far (> 5%)
        if abs(c["close"] - last_price) / last_price > 0.05:
            active_buys, active_sells = reset_grid(c["close"])
            last_price = c["close"]

    total_pnl = balance - capital
    days = (candles[-1]["ts"] - candles[0]["ts"]) / 86400 if len(candles) > 1 else 1

    return {
        "n_trades": round_trips,
        "total_pnl": total_pnl,
        "final_balance": balance,
        "max_drawdown": max_drawdown * 100,
        "profit_per_day": total_pnl / days if days > 0 else 0,
        "days": days,
    }


def backtest_combined(candles, tp_pct, sl_pct, capital=CAPITAL):
    """Grid x5 + Scalp BB simultaneous. Split capital 50/50."""
    grid_capital = capital * 0.5
    scalp_capital = capital * 0.5

    # Run grid with half capital
    grid_res = backtest_grid(candles, capital=grid_capital, leverage=5, spacing_pct=0.01)

    # Run scalp with half capital
    scalp_res = backtest_scalp_bb(candles, tp_pct, sl_pct, capital=scalp_capital, leverage=2)

    total_pnl = grid_res["total_pnl"] + scalp_res["total_pnl"]
    final_balance = capital + total_pnl
    days = grid_res["days"]

    return {
        "grid_pnl": grid_res["total_pnl"],
        "scalp_pnl": scalp_res["total_pnl"],
        "total_pnl": total_pnl,
        "final_balance": final_balance,
        "n_trades_grid": grid_res["n_trades"],
        "n_trades_scalp": scalp_res["n_trades"],
        "profit_per_day": total_pnl / days if days > 0 else 0,
        "max_drawdown_grid": grid_res["max_drawdown"],
        "max_drawdown_scalp": scalp_res["max_drawdown"],
        "days": days,
    }


def fmt_pct(v):
    return f"{v:.1f}%"


def fmt_usd(v):
    return f"${v:.2f}"


def main():
    print("=" * 70)
    print("BACKTEST SCALP BOLLINGER BANDS — 3 mois Kraken 1h")
    print(f"Capital: ${CAPITAL} | Leverage: x{LEVERAGE} | BB({BB_PERIOD},{BB_STD})")
    print(f"Trading hours: 08:00-22:00 UTC | Fee: {KRAKEN_FEE*100:.2f}%")
    print("=" * 70)

    # Fetch data
    print("\n>>> Fetching OHLC data from Kraken...")
    all_data = {}
    for pair_key, pair_api in PAIRS.items():
        all_data[pair_key] = fetch_ohlc(pair_key, pair_api)
        time.sleep(1)

    # Results storage
    all_results = {}
    best_overall = {"pnl": -9999, "config": None}

    for pair_key, candles in all_data.items():
        print(f"\n{'='*70}")
        print(f"  {pair_key} — {len(candles)} candles")
        print(f"{'='*70}")

        # === SCALP BB ===
        print(f"\n--- Scalp BB Results ---")
        print(f"{'TP':>6} {'SL':>6} | {'Trades':>6} {'WR':>6} {'PnL':>10} {'DD':>8} {'$/day':>8} {'BestH':>6}")
        print("-" * 70)

        pair_results = []
        for tp, sl in product(TP_OPTIONS, SL_OPTIONS):
            res = backtest_scalp_bb(candles, tp, sl)
            pair_results.append((tp, sl, res))
            print(f"{tp*100:>5.1f}% {sl*100:>5.1f}% | {res['n_trades']:>6} {res['win_rate']:>5.1f}% {fmt_usd(res['total_pnl']):>10} {fmt_pct(res['max_drawdown']):>8} {fmt_usd(res['profit_per_day']):>8} {res['best_hour'] or '-':>6}")

            if res["total_pnl"] > best_overall["pnl"]:
                best_overall = {"pnl": res["total_pnl"], "config": f"{pair_key} TP={tp*100:.1f}% SL={sl*100:.1f}%", "res": res}

        # === GRID x5 ===
        print(f"\n--- Grid x5 spacing 1% ---")
        grid_res = backtest_grid(candles)
        print(f"  Trades: {grid_res['n_trades']} | PnL: {fmt_usd(grid_res['total_pnl'])} | DD: {fmt_pct(grid_res['max_drawdown'])} | $/day: {fmt_usd(grid_res['profit_per_day'])}")

        # === CASH ===
        first_price = candles[0]["close"]
        last_price = candles[-1]["close"]
        hold_return = (last_price - first_price) / first_price * CAPITAL
        print(f"\n--- Cash (hold) ---")
        print(f"  Price: {first_price:.2f} -> {last_price:.2f} ({(last_price-first_price)/first_price*100:+.1f}%)")
        print(f"  If held with capital: {fmt_usd(hold_return)} return")

        # === COMBINED Grid + Scalp ===
        print(f"\n--- Grid + Scalp BB Combined (50/50 capital) ---")
        print(f"{'TP':>6} {'SL':>6} | {'Grid$':>8} {'Scalp$':>8} {'Total$':>10} {'$/day':>8}")
        print("-" * 60)
        for tp, sl in product(TP_OPTIONS, SL_OPTIONS):
            comb = backtest_combined(candles, tp, sl)
            print(f"{tp*100:>5.1f}% {sl*100:>5.1f}% | {fmt_usd(comb['grid_pnl']):>8} {fmt_usd(comb['scalp_pnl']):>8} {fmt_usd(comb['total_pnl']):>10} {fmt_usd(comb['profit_per_day']):>8}")

        all_results[pair_key] = {
            "scalp": pair_results,
            "grid": grid_res,
            "hold_return": hold_return,
        }

    # === BEST OVERALL ===
    print(f"\n{'='*70}")
    print(f"  BEST OVERALL SCALP BB CONFIG")
    print(f"{'='*70}")
    if best_overall["config"]:
        r = best_overall["res"]
        print(f"  Config: {best_overall['config']}")
        print(f"  Trades: {r['n_trades']} | Win Rate: {r['win_rate']:.1f}%")
        print(f"  PnL: {fmt_usd(r['total_pnl'])} | Final: {fmt_usd(r['final_balance'])}")
        print(f"  Max DD: {fmt_pct(r['max_drawdown'])} | $/day: {fmt_usd(r['profit_per_day'])}")
        print(f"  Best hour: {r['best_hour']}:00 UTC ({fmt_usd(r['best_hour_pnl'])})")

    return all_results, best_overall


if __name__ == "__main__":
    results, best = main()

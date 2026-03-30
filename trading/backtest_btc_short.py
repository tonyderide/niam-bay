#!/usr/bin/env python3
"""
Backtest Martin Grid SHORT vs NEUTRAL vs LONG sur BTC/USD
Parametres Session 84 : centre ~66482$, range [64820-68144], 10 levels, x5, 15$ capital
Donnees: Kraken OHLC locales (15min, ~8 jours)
"""

import csv
import json
from collections import defaultdict
from datetime import datetime

# === 1. LOAD DATA ===

def load_csv_candles(filepath):
    candles = []
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            candles.append({
                "time": datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S"),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            })
    return candles


# === 2. GRID SIMULATION ENGINE ===

MAKER_FEE = 0.0002   # Kraken Futures maker
TAKER_FEE = 0.0005   # Kraken Futures taker
FEE_PER_RT = MAKER_FEE + TAKER_FEE

def simulate_martin_grid(candles, capital, leverage, center, range_low, range_high,
                          num_levels, mode="NEUTRAL", max_loss_pct=15):
    """
    mode: SHORT | NEUTRAL | LONG
    - SHORT: sell at levels above center, buy-to-cover below. Profits when price drops.
    - LONG: buy at levels below center, sell-to-close above. Profits when price rises.
    - NEUTRAL: both sides around center.
    """
    if not candles or num_levels < 2:
        return None

    spacing = (range_high - range_low) / num_levels
    notional_per_level = (capital * leverage) / num_levels

    # Build grid levels
    levels = []
    for i in range(num_levels + 1):
        price = range_low + i * spacing
        levels.append(price)
    levels.sort()

    equity = capital
    peak_equity = capital
    max_drawdown = 0.0
    max_drawdown_pct = 0.0
    total_pnl = 0.0
    round_trips = 0
    wins = 0
    losses = 0
    open_positions = []
    daily_pnl = defaultdict(float)
    equity_curve = []
    recenterings = 0
    stopped = False

    filled_buys = set()
    filled_sells = set()

    orig_center = center
    orig_spacing = spacing

    for ci, candle in enumerate(candles):
        dt = candle["time"]
        o, h, l, c = candle["open"], candle["high"], candle["low"], candle["close"]
        day_key = dt.strftime("%Y-%m-%d")

        for level in levels:
            if level < l or level > h:
                continue

            if mode == "SHORT":
                if level >= center and level not in filled_sells:
                    size_usd = notional_per_level
                    open_positions.append(("short", level, size_usd))
                    filled_sells.add(level)

                elif level < center and level not in filled_buys:
                    closed = False
                    for j, pos in enumerate(open_positions):
                        if pos[0] == "short":
                            entry_price = pos[1]
                            size_usd = pos[2]
                            pnl_gross = (entry_price - level) / entry_price * size_usd
                            fee = size_usd * FEE_PER_RT
                            pnl_net = pnl_gross - fee
                            total_pnl += pnl_net
                            equity += pnl_net
                            daily_pnl[day_key] += pnl_net
                            round_trips += 1
                            if pnl_net > 0: wins += 1
                            else: losses += 1
                            open_positions.pop(j)
                            filled_buys.add(level)
                            closed = True
                            break
                    if not closed:
                        filled_buys.add(level)

            elif mode == "LONG":
                if level <= center and level not in filled_buys:
                    size_usd = notional_per_level
                    open_positions.append(("long", level, size_usd))
                    filled_buys.add(level)

                elif level > center and level not in filled_sells:
                    closed = False
                    for j, pos in enumerate(open_positions):
                        if pos[0] == "long":
                            entry_price = pos[1]
                            size_usd = pos[2]
                            pnl_gross = (level - entry_price) / entry_price * size_usd
                            fee = size_usd * FEE_PER_RT
                            pnl_net = pnl_gross - fee
                            total_pnl += pnl_net
                            equity += pnl_net
                            daily_pnl[day_key] += pnl_net
                            round_trips += 1
                            if pnl_net > 0: wins += 1
                            else: losses += 1
                            open_positions.pop(j)
                            filled_sells.add(level)
                            closed = True
                            break
                    if not closed:
                        filled_sells.add(level)

            elif mode == "NEUTRAL":
                if level < center and level not in filled_buys:
                    closed_short = False
                    for j, pos in enumerate(open_positions):
                        if pos[0] == "short":
                            entry_price = pos[1]
                            size_usd = pos[2]
                            pnl_gross = (entry_price - level) / entry_price * size_usd
                            fee = size_usd * FEE_PER_RT
                            pnl_net = pnl_gross - fee
                            total_pnl += pnl_net
                            equity += pnl_net
                            daily_pnl[day_key] += pnl_net
                            round_trips += 1
                            if pnl_net > 0: wins += 1
                            else: losses += 1
                            open_positions.pop(j)
                            closed_short = True
                            break
                    if not closed_short:
                        open_positions.append(("long", level, notional_per_level))
                    filled_buys.add(level)

                elif level >= center and level not in filled_sells:
                    closed_long = False
                    for j, pos in enumerate(open_positions):
                        if pos[0] == "long":
                            entry_price = pos[1]
                            size_usd = pos[2]
                            pnl_gross = (level - entry_price) / entry_price * size_usd
                            fee = size_usd * FEE_PER_RT
                            pnl_net = pnl_gross - fee
                            total_pnl += pnl_net
                            equity += pnl_net
                            daily_pnl[day_key] += pnl_net
                            round_trips += 1
                            if pnl_net > 0: wins += 1
                            else: losses += 1
                            open_positions.pop(j)
                            closed_long = True
                            break
                    if not closed_long:
                        open_positions.append(("short", level, notional_per_level))
                    filled_sells.add(level)

        # Recenter if price outside range by 2%
        if c < range_low * 0.98 or c > range_high * 1.02:
            for pos in open_positions:
                side, entry_price, size_usd = pos
                if side == "long":
                    pnl_gross = (c - entry_price) / entry_price * size_usd
                elif side == "short":
                    pnl_gross = (entry_price - c) / entry_price * size_usd
                fee = size_usd * FEE_PER_RT
                pnl_net = pnl_gross - fee
                total_pnl += pnl_net
                equity += pnl_net
                daily_pnl[day_key] += pnl_net
                round_trips += 1
                if pnl_net > 0: wins += 1
                else: losses += 1

            open_positions = []
            filled_buys = set()
            filled_sells = set()
            recenterings += 1

            center = c
            range_low = c - (orig_spacing * num_levels / 2)
            range_high = c + (orig_spacing * num_levels / 2)
            levels = []
            for i in range(num_levels + 1):
                price = range_low + i * orig_spacing
                levels.append(price)
            levels.sort()

        # Unrealized PnL
        unrealized = 0.0
        for pos in open_positions:
            side, entry_price, size_usd = pos
            if side == "long":
                unrealized += (c - entry_price) / entry_price * size_usd
            elif side == "short":
                unrealized += (entry_price - c) / entry_price * size_usd

        current_equity = equity + unrealized
        equity_curve.append((dt.isoformat(), current_equity, c))

        if current_equity > peak_equity:
            peak_equity = current_equity
        dd = peak_equity - current_equity
        dd_pct = dd / peak_equity * 100 if peak_equity > 0 else 0
        if dd_pct > max_drawdown_pct:
            max_drawdown_pct = dd_pct
            max_drawdown = dd

        if max_loss_pct and dd_pct > max_loss_pct:
            for pos in open_positions:
                side, entry_price, size_usd = pos
                if side == "long":
                    pnl_gross = (c - entry_price) / entry_price * size_usd
                elif side == "short":
                    pnl_gross = (entry_price - c) / entry_price * size_usd
                fee = size_usd * FEE_PER_RT
                pnl_net = pnl_gross - fee
                total_pnl += pnl_net
                equity += pnl_net
            open_positions = []
            stopped = True
            break

    # Close remaining
    if open_positions and not stopped:
        last_price = candles[-1]["close"]
        for pos in open_positions:
            side, entry_price, size_usd = pos
            if side == "long":
                pnl_gross = (last_price - entry_price) / entry_price * size_usd
            elif side == "short":
                pnl_gross = (entry_price - last_price) / entry_price * size_usd
            fee = size_usd * FEE_PER_RT
            pnl_net = pnl_gross - fee
            total_pnl += pnl_net
            equity += pnl_net

    win_rate = wins / round_trips * 100 if round_trips > 0 else 0
    final_price = candles[-1]["close"]
    initial_price = candles[0]["close"]
    hodl_pct = (final_price - initial_price) / initial_price * 100

    total_seconds = (candles[-1]["time"] - candles[0]["time"]).total_seconds()
    days = total_seconds / 86400
    pnl_per_day = total_pnl / days if days > 0 else 0

    return {
        "mode": mode,
        "capital": capital,
        "leverage": leverage,
        "center_initial": orig_center,
        "range_low_initial": range_low,
        "range_high_initial": range_high,
        "num_levels": num_levels,
        "spacing": orig_spacing,
        "round_trips": round_trips,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "pnl_pct": total_pnl / capital * 100,
        "max_drawdown": max_drawdown,
        "max_drawdown_pct": max_drawdown_pct,
        "recenterings": recenterings,
        "stopped": stopped,
        "pnl_per_day": pnl_per_day,
        "days": days,
        "initial_price": initial_price,
        "final_price": final_price,
        "hodl_pct": hodl_pct,
        "equity_curve": equity_curve,
        "daily_pnl": dict(daily_pnl),
    }


# === 3. MAIN ===

if __name__ == "__main__":
    DATA_PATH = "/sessions/loving-exciting-meitner/mnt/niam-bay/trading/data/XXBTZUSD_15m.csv"

    print("Loading BTC/USD 15m OHLC data...")
    candles = load_csv_candles(DATA_PATH)
    print(f"  Loaded {len(candles)} candles")

    if not candles:
        print("ERROR: No candles loaded")
        exit(1)

    t0 = candles[0]["time"]
    t1 = candles[-1]["time"]
    price_open = candles[0]["open"]
    price_close = candles[-1]["close"]
    price_high = max(c["high"] for c in candles)
    price_low = min(c["low"] for c in candles)
    days = (t1 - t0).total_seconds() / 86400
    hodl_pct = (price_close - price_open) / price_open * 100

    print(f"\n{'='*60}")
    print(f"BTC/USD DATA STATS")
    print(f"{'='*60}")
    print(f"  Period:    {t0} -> {t1} ({days:.1f} days)")
    print(f"  Open:      ${price_open:,.2f}")
    print(f"  Close:     ${price_close:,.2f}")
    print(f"  High:      ${price_high:,.2f}")
    print(f"  Low:       ${price_low:,.2f}")
    print(f"  HODL:      {hodl_pct:+.2f}%")

    # Session 84 parameters
    CAPITAL = 15.0
    LEVERAGE = 5
    NUM_LEVELS = 10
    MAX_LOSS_PCT = 15

    # Original Session 84 params
    S84_CENTER = 66482.0
    S84_LOW = 64820.0
    S84_HIGH = 68144.0
    S84_SPACING = (S84_HIGH - S84_LOW) / NUM_LEVELS  # 332.4

    # Adapted params: same spacing (~332$), centered on actual data
    actual_mid = (price_high + price_low) / 2
    adapted_center = round(actual_mid, -1)
    adapted_low = adapted_center - (S84_SPACING * NUM_LEVELS / 2)
    adapted_high = adapted_center + (S84_SPACING * NUM_LEVELS / 2)

    print(f"\n{'='*60}")
    print(f"SESSION 84 ORIGINAL PARAMS")
    print(f"{'='*60}")
    print(f"  Centre:    ${S84_CENTER:,.0f}")
    print(f"  Range:     [${S84_LOW:,.0f} - ${S84_HIGH:,.0f}]")
    print(f"  Spacing:   ${S84_SPACING:,.1f} (~{S84_SPACING/S84_CENTER*100:.2f}%)")
    print(f"  Levels:    {NUM_LEVELS}")
    print(f"  Levier:    x{LEVERAGE}")
    print(f"  Capital:   ${CAPITAL}")

    print(f"\n{'='*60}")
    print(f"ADAPTED PARAMS (centered on data)")
    print(f"{'='*60}")
    print(f"  Centre:    ${adapted_center:,.0f}")
    print(f"  Range:     [${adapted_low:,.0f} - ${adapted_high:,.0f}]")
    print(f"  Spacing:   ${S84_SPACING:,.1f} (~{S84_SPACING/adapted_center*100:.2f}%)")

    modes = ["SHORT", "NEUTRAL", "LONG"]

    # === Test 1: Adapted params, with max loss ===
    print(f"\n{'='*60}")
    print(f"TEST 1: ADAPTED PARAMS + MAX LOSS {MAX_LOSS_PCT}%")
    print(f"{'='*60}")

    results_adapted = {}
    for mode in modes:
        r = simulate_martin_grid(
            candles, CAPITAL, LEVERAGE, adapted_center,
            adapted_low, adapted_high, NUM_LEVELS,
            mode=mode, max_loss_pct=MAX_LOSS_PCT
        )
        results_adapted[mode] = r
        print(f"\n  {mode}:")
        print(f"    RT: {r['round_trips']} | WR: {r['win_rate']:.1f}% | PnL: ${r['total_pnl']:+.2f} ({r['pnl_pct']:+.1f}%) | MaxDD: {r['max_drawdown_pct']:.1f}% | Recenter: {r['recenterings']} | Stop: {r['stopped']} | $/day: ${r['pnl_per_day']:+.3f}")

    # === Test 2: Adapted params, NO max loss ===
    print(f"\n{'='*60}")
    print(f"TEST 2: ADAPTED PARAMS + NO MAX LOSS")
    print(f"{'='*60}")

    results_nolimit = {}
    for mode in modes:
        r = simulate_martin_grid(
            candles, CAPITAL, LEVERAGE, adapted_center,
            adapted_low, adapted_high, NUM_LEVELS,
            mode=mode, max_loss_pct=None
        )
        results_nolimit[mode] = r
        print(f"\n  {mode}:")
        print(f"    RT: {r['round_trips']} | WR: {r['win_rate']:.1f}% | PnL: ${r['total_pnl']:+.2f} ({r['pnl_pct']:+.1f}%) | MaxDD: {r['max_drawdown_pct']:.1f}% | Recenter: {r['recenterings']} | $/day: ${r['pnl_per_day']:+.3f}")

    # === Test 3: Original session 84 params ===
    print(f"\n{'='*60}")
    print(f"TEST 3: ORIGINAL SESSION 84 PARAMS + MAX LOSS {MAX_LOSS_PCT}%")
    print(f"{'='*60}")

    results_orig = {}
    for mode in modes:
        r = simulate_martin_grid(
            candles, CAPITAL, LEVERAGE, S84_CENTER,
            S84_LOW, S84_HIGH, NUM_LEVELS,
            mode=mode, max_loss_pct=MAX_LOSS_PCT
        )
        results_orig[mode] = r
        print(f"\n  {mode}:")
        print(f"    RT: {r['round_trips']} | WR: {r['win_rate']:.1f}% | PnL: ${r['total_pnl']:+.2f} ({r['pnl_pct']:+.1f}%) | MaxDD: {r['max_drawdown_pct']:.1f}% | Recenter: {r['recenterings']} | Stop: {r['stopped']} | $/day: ${r['pnl_per_day']:+.3f}")

    # === Test 4: Wider spacing variants ===
    print(f"\n{'='*60}")
    print(f"TEST 4: SPACING SENSITIVITY (SHORT mode)")
    print(f"{'='*60}")

    for spacing_mult in [0.5, 1.0, 1.5, 2.0]:
        sp = S84_SPACING * spacing_mult
        low = adapted_center - sp * NUM_LEVELS / 2
        high = adapted_center + sp * NUM_LEVELS / 2
        r = simulate_martin_grid(
            candles, CAPITAL, LEVERAGE, adapted_center,
            low, high, NUM_LEVELS,
            mode="SHORT", max_loss_pct=None
        )
        print(f"\n  Spacing ${sp:,.0f} ({sp/adapted_center*100:.2f}%):")
        print(f"    RT: {r['round_trips']} | WR: {r['win_rate']:.1f}% | PnL: ${r['total_pnl']:+.2f} ({r['pnl_pct']:+.1f}%) | MaxDD: {r['max_drawdown_pct']:.1f}% | Recenter: {r['recenterings']}")

    # === SUMMARY ===
    print(f"\n{'='*60}")
    print(f"SUMMARY TABLE (Adapted Params, Max Loss {MAX_LOSS_PCT}%)")
    print(f"{'='*60}")
    print(f"{'Mode':<10} {'RTs':>5} {'WR':>6} {'PnL':>10} {'PnL%':>8} {'MaxDD':>8} {'$/day':>8} {'Rcntr':>6} {'Stop':>5}")
    print("-" * 73)
    for mode in modes:
        r = results_adapted[mode]
        print(f"{mode:<10} {r['round_trips']:>5} {r['win_rate']:>5.1f}% ${r['total_pnl']:>+8.2f} {r['pnl_pct']:>+7.1f}% {r['max_drawdown_pct']:>7.1f}% ${r['pnl_per_day']:>+6.3f} {r['recenterings']:>6} {'YES' if r['stopped'] else 'no':>5}")
    print(f"{'HODL':<10} {'':>5} {'':>6} {'':>10} {hodl_pct:>+7.1f}% {'':>8}")
    print(f"{'CASH':<10} {'':>5} {'':>6} {'$0.00':>10} {'+0.0%':>8} {'0.0%':>8}")

    print(f"\n{'='*60}")
    print(f"SUMMARY TABLE (Adapted Params, NO Max Loss)")
    print(f"{'='*60}")
    print(f"{'Mode':<10} {'RTs':>5} {'WR':>6} {'PnL':>10} {'PnL%':>8} {'MaxDD':>8} {'$/day':>8} {'Rcntr':>6}")
    print("-" * 68)
    for mode in modes:
        r = results_nolimit[mode]
        print(f"{mode:<10} {r['round_trips']:>5} {r['win_rate']:>5.1f}% ${r['total_pnl']:>+8.2f} {r['pnl_pct']:>+7.1f}% {r['max_drawdown_pct']:>7.1f}% ${r['pnl_per_day']:>+6.3f} {r['recenterings']:>6}")

    # Daily PnL breakdown for best mode
    print(f"\n{'='*60}")
    print(f"DAILY PnL BREAKDOWN (SHORT, adapted, no limit)")
    print(f"{'='*60}")
    r_short = results_nolimit["SHORT"]
    for day in sorted(r_short["daily_pnl"].keys()):
        print(f"  {day}: ${r_short['daily_pnl'][day]:+.4f}")

    # Save JSON
    output = {
        "data_file": DATA_PATH,
        "candle_count": len(candles),
        "interval": "15min",
        "period_start": t0.isoformat(),
        "period_end": t1.isoformat(),
        "btc_open": price_open,
        "btc_close": price_close,
        "btc_high": price_high,
        "btc_low": price_low,
        "hodl_pct": round(hodl_pct, 2),
        "days": round(days, 1),
        "session84_params": {"center": S84_CENTER, "range_low": S84_LOW, "range_high": S84_HIGH, "spacing": S84_SPACING},
        "adapted_params": {"center": adapted_center, "range_low": adapted_low, "range_high": adapted_high, "spacing": S84_SPACING},
    }
    for label, res in [("adapted_maxloss", results_adapted), ("adapted_nolimit", results_nolimit), ("original_maxloss", results_orig)]:
        output[label] = {}
        for mode in modes:
            r = res[mode]
            output[label][mode] = {
                "round_trips": r["round_trips"], "wins": r["wins"], "losses": r["losses"],
                "win_rate": round(r["win_rate"], 1), "total_pnl": round(r["total_pnl"], 4),
                "pnl_pct": round(r["pnl_pct"], 2), "max_drawdown_pct": round(r["max_drawdown_pct"], 2),
                "recenterings": r["recenterings"], "stopped": r["stopped"],
                "pnl_per_day": round(r["pnl_per_day"], 4), "days": round(r["days"], 1),
            }

    with open("/sessions/loving-exciting-meitner/backtest_results_btc.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n\nResults saved to backtest_results_btc.json")

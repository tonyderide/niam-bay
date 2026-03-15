#!/usr/bin/env python3
"""
Optimize M4 Asymmetric Martingale — grid search on TP/SL/multiplier/doublings.
With slippage + Monte Carlo.
"""
import requests
import random
import json
from datetime import datetime
from dataclasses import dataclass
from itertools import product

CAPITAL = 15.0
TAKER_FEE = 0.05 / 100
INSTRUMENT = "PF_ETHUSD"
SLIPPAGE_MIN = 0.005 / 100
SLIPPAGE_MAX = 0.02 / 100
RUNS = 5

def fetch_candles(resolution="5m"):
    url = f"https://futures.kraken.com/api/charts/v1/trade/{INSTRUMENT}/{resolution}"
    resp = requests.get(url, timeout=30)
    data = resp.json()
    candles = []
    for c in data.get("candles", []):
        candles.append({
            "ts": int(c["time"]) // 1000,
            "open": float(c["open"]),
            "high": float(c["high"]),
            "low": float(c["low"]),
            "close": float(c["close"]),
            "volume": float(c["volume"])
        })
    candles.sort(key=lambda x: x["ts"])
    return candles

def extract_ticks(candles):
    ticks = []
    for c in candles:
        o, h, l, cl = c["open"], c["high"], c["low"], c["close"]
        ticks.append(o)
        if h != o: ticks.append(h)
        if l != h and l != o: ticks.append(l)
        if cl != l: ticks.append(cl)
    return ticks

@dataclass
class Result:
    tp_pct: float
    sl_pct: float
    leverage: int
    stake: float
    mult: float
    max_d: int
    trades: int = 0
    wins: int = 0
    pnl: float = 0.0
    max_drawdown: float = 0.0
    fees: float = 0.0
    blown: int = 0
    worst_pnl: float = 0.0
    best_pnl: float = 0.0

def simulate(ticks, tp_pct, sl_pct, leverage, initial_stake, mult, max_doublings, seed):
    random.seed(seed)
    pnl = 0.0
    peak = 0.0
    max_dd = 0.0
    fees = 0.0
    trades = 0
    wins = 0
    blown = 0

    current_stake = initial_stake
    current_doubling = 0
    direction = "LONG"
    in_trade = False
    entry = 0
    tp_price = 0
    sl_price = 0

    for price in ticks:
        if not in_trade:
            if current_doubling > max_doublings:
                blown += 1
                current_stake = initial_stake
                current_doubling = 0
                direction = "LONG"
                continue

            slip = random.uniform(SLIPPAGE_MIN, SLIPPAGE_MAX)
            if direction == "LONG":
                entry = price * (1 + slip)
                tp_price = entry * (1 + tp_pct)
                sl_price = entry * (1 - sl_pct)
            else:
                entry = price * (1 - slip)
                tp_price = entry * (1 - tp_pct)
                sl_price = entry * (1 + sl_pct)
            in_trade = True
            continue

        hit_tp = False
        hit_sl = False
        if direction == "LONG":
            if price >= tp_price: hit_tp = True
            elif price <= sl_price: hit_sl = True
        else:
            if price <= tp_price: hit_tp = True
            elif price >= sl_price: hit_sl = True

        if hit_tp or hit_sl:
            slip = random.uniform(SLIPPAGE_MIN, SLIPPAGE_MAX)
            base_exit = tp_price if hit_tp else sl_price
            if direction == "LONG":
                exit_price = base_exit * (1 - slip)
            else:
                exit_price = base_exit * (1 + slip)

            notional = current_stake * leverage
            if direction == "LONG":
                gross = notional * (exit_price - entry) / entry
            else:
                gross = notional * (entry - exit_price) / entry

            fee = notional * TAKER_FEE * 2
            net = gross - fee
            pnl += net
            fees += fee
            trades += 1

            if pnl > peak: peak = pnl
            dd = peak - pnl
            if dd > max_dd: max_dd = dd

            if hit_tp:
                wins += 1
                current_stake = initial_stake
                current_doubling = 0
                # Keep same direction on win (trend following)
            else:
                current_stake = min(current_stake * mult, CAPITAL)
                current_doubling += 1
                direction = "SHORT" if direction == "LONG" else "LONG"

            in_trade = False

    return trades, wins, pnl, max_dd, fees, blown

def main():
    print("Fetching data...")
    candles_5m = fetch_candles("5m")
    candles_15m = fetch_candles("15m")
    days_5m = (candles_5m[-1]["ts"] - candles_5m[0]["ts"]) / 86400
    days_15m = (candles_15m[-1]["ts"] - candles_15m[0]["ts"]) / 86400
    ticks_5m = extract_ticks(candles_5m)
    ticks_15m = extract_ticks(candles_15m)
    print(f"5m: {len(candles_5m)} candles ({days_5m:.1f}d) | 15m: {len(candles_15m)} candles ({days_15m:.1f}d)")

    # Grid search parameters
    TP_RANGE = [0.008, 0.01, 0.012, 0.015, 0.018, 0.02, 0.025, 0.03, 0.035, 0.04, 0.05]
    SL_RANGE = [0.002, 0.003, 0.004, 0.005, 0.006, 0.008, 0.01, 0.012, 0.015]
    LEVERAGE = [5, 10]
    STAKE = [0.5, 1.0, 1.5, 2.0]
    MULT = [1.5, 2.0, 2.5, 3.0]
    MAX_D = [3, 4, 5]

    combos = list(product(TP_RANGE, SL_RANGE, LEVERAGE, STAKE, MULT, MAX_D))
    # Filter: TP must be > SL (asymmetric)
    combos = [(tp, sl, lev, st, m, d) for tp, sl, lev, st, m, d in combos if tp >= sl * 2]
    print(f"\n{len(combos)} combinations to test...")

    results_15m = []

    for i, (tp, sl, lev, st, m, d) in enumerate(combos):
        if i % 500 == 0:
            print(f"  {i}/{len(combos)}...")

        # Run on 15m (more data = more reliable)
        run_pnls = []
        run_trades = []
        run_wins = []
        run_dd = []
        run_fees = []
        run_blown = []

        for run in range(RUNS):
            t, w, p, dd, f, b = simulate(ticks_15m, tp, sl, lev, st, m, d, seed=run*42+7)
            run_pnls.append(p)
            run_trades.append(t)
            run_wins.append(w)
            run_dd.append(dd)
            run_fees.append(f)
            run_blown.append(b)

        avg_pnl = sum(run_pnls) / RUNS
        worst = min(run_pnls)
        best = max(run_pnls)
        avg_trades = sum(run_trades) / RUNS
        avg_wins = sum(run_wins) / RUNS
        avg_dd = sum(run_dd) / RUNS
        avg_fees = sum(run_fees) / RUNS
        avg_blown = sum(run_blown) / RUNS

        if avg_trades > 0:
            results_15m.append({
                "tp": tp, "sl": sl, "lev": lev, "stake": st, "mult": m, "max_d": d,
                "trades": avg_trades, "wr": avg_wins/avg_trades*100 if avg_trades else 0,
                "avg_pnl": avg_pnl, "worst": worst, "best": best,
                "roi": avg_pnl / CAPITAL * 100,
                "dd": avg_dd, "fees": avg_fees, "blown": avg_blown,
                "rr": tp/sl,
            })

    # Sort by avg_pnl
    results_15m.sort(key=lambda x: x["avg_pnl"], reverse=True)

    print(f"\n{'='*140}")
    print(f"TOP 50 CONFIGS — 15m ({days_15m:.0f} days) — {RUNS} Monte Carlo runs with slippage")
    print(f"{'='*140}")
    print(f"{'Rank':<5} {'TP%':>6} {'SL%':>6} {'R:R':>5} {'Lev':>4} {'Stake':>6} {'Mult':>5} {'MaxD':>5} {'Trades':>7} {'WR%':>7} {'AvgPnL':>9} {'Worst':>9} {'Best':>9} {'ROI%':>8} {'MaxDD':>8} {'Fees':>8} {'Blown':>6}")
    print("-" * 140)

    for i, r in enumerate(results_15m[:50]):
        print(f"{i+1:<5} {r['tp']*100:>5.1f}% {r['sl']*100:>5.2f}% {r['rr']:>4.1f} {r['lev']:>4} {r['stake']:>5.1f}$ {r['mult']:>4.1f}x {r['max_d']:>5} {r['trades']:>7.0f} {r['wr']:>6.1f}% {r['avg_pnl']:>+8.2f} {r['worst']:>+8.2f} {r['best']:>+8.2f} {r['roi']:>+7.1f}% {r['dd']:>7.2f} {r['fees']:>7.2f} {r['blown']:>5.0f}")

    # Also show top by worst-case (most robust)
    robust = sorted([r for r in results_15m if r["worst"] > 0], key=lambda x: x["worst"], reverse=True)
    print(f"\n{'='*140}")
    print(f"TOP 30 MOST ROBUST (positive even in worst case)")
    print(f"{'='*140}")
    print(f"{'Rank':<5} {'TP%':>6} {'SL%':>6} {'R:R':>5} {'Lev':>4} {'Stake':>6} {'Mult':>5} {'MaxD':>5} {'Trades':>7} {'WR%':>7} {'AvgPnL':>9} {'Worst':>9} {'Best':>9} {'ROI%':>8} {'MaxDD':>8} {'Fees':>8} {'Blown':>6}")
    print("-" * 140)

    for i, r in enumerate(robust[:30]):
        print(f"{i+1:<5} {r['tp']*100:>5.1f}% {r['sl']*100:>5.2f}% {r['rr']:>4.1f} {r['lev']:>4} {r['stake']:>5.1f}$ {r['mult']:>4.1f}x {r['max_d']:>5} {r['trades']:>7.0f} {r['wr']:>6.1f}% {r['avg_pnl']:>+8.2f} {r['worst']:>+8.2f} {r['best']:>+8.2f} {r['roi']:>+7.1f}% {r['dd']:>7.2f} {r['fees']:>7.2f} {r['blown']:>5.0f}")

    # Top by ROI/DD ratio (risk-adjusted)
    risk_adj = sorted([r for r in results_15m if r["dd"] > 0 and r["avg_pnl"] > 0], key=lambda x: x["avg_pnl"] / x["dd"], reverse=True)
    print(f"\n{'='*140}")
    print(f"TOP 30 BEST RISK-ADJUSTED (PnL / MaxDrawdown)")
    print(f"{'='*140}")
    print(f"{'Rank':<5} {'TP%':>6} {'SL%':>6} {'R:R':>5} {'Lev':>4} {'Stake':>6} {'Mult':>5} {'MaxD':>5} {'Trades':>7} {'WR%':>7} {'AvgPnL':>9} {'Worst':>9} {'PnL/DD':>8} {'ROI%':>8} {'MaxDD':>8}")
    print("-" * 140)

    for i, r in enumerate(risk_adj[:30]):
        ratio = r["avg_pnl"] / r["dd"]
        print(f"{i+1:<5} {r['tp']*100:>5.1f}% {r['sl']*100:>5.2f}% {r['rr']:>4.1f} {r['lev']:>4} {r['stake']:>5.1f}$ {r['mult']:>4.1f}x {r['max_d']:>5} {r['trades']:>7.0f} {r['wr']:>6.1f}% {r['avg_pnl']:>+8.2f} {r['worst']:>+8.2f} {ratio:>7.2f}x {r['roi']:>+7.1f}% {r['dd']:>7.2f}")

if __name__ == "__main__":
    main()

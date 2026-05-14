#!/usr/bin/env python3
"""Trend-Follower backtest sweep on 22 cryptos.

Strategy:
- Compute EMA50, EMA200, RSI on 1min closes
- Long entry: EMA50 crosses above EMA200 AND RSI > 50
- Short entry: EMA50 crosses below EMA200 AND RSI < 50
- Exit: trailing stop X% or counter-cross
- Cap: $30 per pair, lev 7x, fees 0.05% RT (taker for entry/exit)
"""
import json, time, urllib.request
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "data_cache"
PAIRS = {
    "BTC": "BTCUSDT", "ETH": "ETHUSDT", "LINK": "LINKUSDT", "SOL": "SOLUSDT",
    "DOT": "DOTUSDT", "ADA": "ADAUSDT", "LTC": "LTCUSDT", "ATOM": "ATOMUSDT",
    "AVAX": "AVAXUSDT", "AAVE": "AAVEUSDT", "UNI": "UNIUSDT", "INJ": "INJUSDT",
    "NEAR": "NEARUSDT", "FIL": "FILUSDT", "DOGE": "DOGEUSDT", "XRP": "XRPUSDT",
    "OP": "OPUSDT", "ARB": "ARBUSDT", "APT": "APTUSDT", "SUI": "SUIUSDT",
    "TIA": "TIAUSDT",
}
TRAIL_STOPS = [0.015, 0.020, 0.025, 0.030]  # 1.5%, 2%, 2.5%, 3%
RSI_FILTERS = [True, False]
CAPITAL = 30.0
LEVERAGE = 7
FEE_RT = 0.001  # 0.05% × 2 (taker entry + taker exit)
DAYS_BACK = 30


def fetch_binance(pair, days=DAYS_BACK):
    cache = CACHE_DIR / f"binance_{pair}_1min_{days}d.json"
    if cache.exists():
        return json.loads(cache.read_text())
    return []


def ema(values, period):
    if len(values) < period:
        return [values[0]] * len(values) if values else []
    k = 2.0 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def rsi(closes, period=14):
    if len(closes) < period + 1:
        return [50.0] * len(closes)
    out = [50.0] * period
    gains = losses = 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i-1]
        if d > 0: gains += d
        else: losses -= d
    avg_g = gains / period
    avg_l = losses / period
    rs = avg_g / avg_l if avg_l > 0 else 999
    out.append(100 - 100 / (1 + rs))
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i-1]
        g = d if d > 0 else 0
        l = -d if d < 0 else 0
        avg_g = (avg_g * (period - 1) + g) / period
        avg_l = (avg_l * (period - 1) + l) / period
        rs = avg_g / avg_l if avg_l > 0 else 999
        out.append(100 - 100 / (1 + rs))
    return out


def simulate(candles, trail_pct, use_rsi_filter):
    if len(candles) < 250:
        return None
    closes = [c[4] for c in candles]
    ema50 = ema(closes, 50)
    ema200 = ema(closes, 200)
    rsi_vals = rsi(closes)

    notional = CAPITAL * LEVERAGE
    pnl_net = 0.0
    eq = CAPITAL
    peak = CAPITAL
    max_dd = 0.0
    trades = []
    pos = 0  # 0=flat, 1=long, -1=short
    entry = 0.0
    high_since = 0.0
    low_since = 0.0
    prev_above = ema50[200] > ema200[200] if len(ema50) > 200 else False

    for i in range(201, len(candles)):
        price = closes[i]
        above = ema50[i] > ema200[i]
        # Detect cross
        cross_up = above and not prev_above
        cross_dn = (not above) and prev_above
        prev_above = above

        # Manage existing position
        if pos == 1:
            if price > high_since: high_since = price
            stop = high_since * (1 - trail_pct)
            if price <= stop or cross_dn:
                # exit
                ret = (price - entry) / entry
                trade_pnl = notional * ret - FEE_RT * notional
                pnl_net += trade_pnl
                trades.append(trade_pnl)
                pos = 0
        elif pos == -1:
            if price < low_since: low_since = price
            stop = low_since * (1 + trail_pct)
            if price >= stop or cross_up:
                ret = (entry - price) / entry
                trade_pnl = notional * ret - FEE_RT * notional
                pnl_net += trade_pnl
                trades.append(trade_pnl)
                pos = 0

        # New entries (after exit if needed)
        if pos == 0:
            if cross_up and (not use_rsi_filter or rsi_vals[i] > 50):
                pos = 1
                entry = price
                high_since = price
            elif cross_dn and (not use_rsi_filter or rsi_vals[i] < 50):
                pos = -1
                entry = price
                low_since = price

        eq = CAPITAL + pnl_net
        if eq > peak: peak = eq
        if (peak - eq) > max_dd: max_dd = peak - eq

    pnl_pct = pnl_net / CAPITAL * 100
    n = len(trades)
    wins = sum(1 for t in trades if t > 0)
    win_rate = wins / n * 100 if n else 0
    avg_win = sum(t for t in trades if t > 0) / wins if wins else 0
    avg_loss = sum(t for t in trades if t <= 0) / (n - wins) if (n - wins) > 0 else 0
    calmar = round(pnl_pct / (max_dd / CAPITAL * 100), 2) if max_dd > 0 else 999
    return {
        "trades": n, "wins": wins, "win_rate": round(win_rate, 1),
        "pnl_net": round(pnl_net, 4), "pnl_pct": round(pnl_pct, 2),
        "max_dd": round(max_dd, 4), "calmar": calmar,
        "avg_win": round(avg_win, 4), "avg_loss": round(avg_loss, 4),
    }


def main():
    print(f"Trend-Follower sweep | cap=${CAPITAL} lev={LEVERAGE}x fee_rt={FEE_RT*100}%")
    print(f"Pairs={len(PAIRS)} trail_stops={TRAIL_STOPS} rsi_filter={RSI_FILTERS}")
    results = []
    for name, sym in PAIRS.items():
        d = fetch_binance(sym)
        if not d:
            print(f"  SKIP {name}: no cache")
            continue
        for ts in TRAIL_STOPS:
            for rf in RSI_FILTERS:
                r = simulate(d, ts, rf)
                if r is None: continue
                r["pair"] = name; r["trail"] = ts; r["rsi_filter"] = rf
                results.append(r)

    results.sort(key=lambda x: -x["pnl_net"])
    print(f"\n=== TOP 25 par PnL net 30d ===")
    print(f"{'pair':6}{'trail':8}{'rsi':6}{'trades':8}{'win%':7}{'PnL$':10}{'PnL%':8}{'maxDD$':9}{'Calmar':8}")
    for r in results[:25]:
        print(f"{r['pair']:6}{r['trail']*100:6.1f}% {'Y' if r['rsi_filter'] else 'N':5}{r['trades']:7d}{r['win_rate']:6.1f}%{r['pnl_net']:+8.3f}  {r['pnl_pct']:+6.2f}%{r['max_dd']:+8.3f} {r['calmar']:7.2f}")

    # Best per pair (PnL > 0)
    best = {}
    for r in results:
        if r["pnl_net"] <= 0: continue
        if r["pair"] not in best or r["pnl_net"] > best[r["pair"]]["pnl_net"]:
            best[r["pair"]] = r
    print(f"\n=== Meilleur par pair (PnL > 0) — {len(best)}/{len(PAIRS)} profitables ===")
    for p, r in sorted(best.items(), key=lambda x: -x[1]["pnl_net"]):
        print(f"  {p:6} trail={r['trail']*100:.1f}% rsi={'Y' if r['rsi_filter'] else 'N'} → {r['trades']} trades WR={r['win_rate']}% PnL=${r['pnl_net']:+.3f} ({r['pnl_pct']:+.2f}%) Calmar={r['calmar']}")

    # Portfolio top-N
    profitable = sorted(best.values(), key=lambda x: -x["pnl_net"])
    print(f"\n=== Portfolios ===")
    for n in [3, 5, 8]:
        if len(profitable) < n: continue
        top = profitable[:n]
        total_pnl = sum(r["pnl_net"] for r in top)
        total_cap = n * CAPITAL
        print(f"  Top-{n}: {', '.join(r['pair'] for r in top)} → ${total_pnl:+.2f} / ${total_cap} = {total_pnl/total_cap*100:+.2f}% net 30d")

    Path("trend_sweep_results.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Momentum/Breakout backtest sweep on 22 cryptos.

Strategy:
- Detect 1h pump: close[i] / close[i-60] > pump_threshold
- Confirm with volume spike: vol[i-60..i] / vol[i-360..i-60] > vol_mult
- Enter long, trail stop X%, take profit at 2x risk OR counter-pump
- Cap $30, lev 7x, fees 0.05% RT
"""
import json
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
PUMP_THRESHOLDS = [0.02, 0.03, 0.05]  # 2/3/5% pump 1h
VOL_MULTS = [1.5, 2.0, 3.0]
TRAIL_STOPS = [0.02, 0.03]
CAPITAL = 30.0
LEVERAGE = 7
FEE_RT = 0.001
DAYS_BACK = 30


def fetch_binance(pair, days=DAYS_BACK):
    cache = CACHE_DIR / f"binance_{pair}_1min_{days}d.json"
    if cache.exists():
        return json.loads(cache.read_text())
    return []


def simulate(candles, pump_th, vol_mult, trail_pct):
    if len(candles) < 500:
        return None
    closes = [c[4] for c in candles]
    vols = [c[5] for c in candles]

    notional = CAPITAL * LEVERAGE
    pnl_net = 0.0
    trades = []
    pos = 0
    entry = 0.0
    high_since = 0.0
    cooldown = 0  # min between trades

    for i in range(360, len(candles)):
        if cooldown > 0:
            cooldown -= 1
            continue
        price = closes[i]

        if pos == 1:
            if price > high_since: high_since = price
            stop = high_since * (1 - trail_pct)
            # Take profit if up by 2x risk (= 2 × trail_pct from entry)
            tp = entry * (1 + 2 * trail_pct)
            if price <= stop or price >= tp:
                ret = (price - entry) / entry
                trade_pnl = notional * ret - FEE_RT * notional
                pnl_net += trade_pnl
                trades.append(trade_pnl)
                pos = 0
                cooldown = 60  # 1h cooldown
            continue

        # Detect entry
        # Pump : close[i] / close[i-60] > 1 + pump_th
        if closes[i-60] <= 0: continue
        ret_1h = closes[i] / closes[i-60] - 1
        if ret_1h < pump_th:
            continue
        # Volume confirmation : vol last 1h vs vol previous 5h
        vol_1h = sum(vols[i-60:i])
        vol_5h_prev = sum(vols[i-360:i-60]) / 5.0
        if vol_5h_prev <= 0: continue
        if vol_1h / vol_5h_prev < vol_mult:
            continue
        # Entry confirmed
        pos = 1
        entry = price
        high_since = price

    pnl_pct = pnl_net / CAPITAL * 100
    n = len(trades)
    wins = sum(1 for t in trades if t > 0)
    win_rate = wins / n * 100 if n else 0
    return {
        "trades": n, "win_rate": round(win_rate, 1),
        "pnl_net": round(pnl_net, 4), "pnl_pct": round(pnl_pct, 2),
    }


def main():
    print(f"Momentum sweep | cap=${CAPITAL} lev={LEVERAGE}x fee_rt={FEE_RT*100}%")
    print(f"Pairs={len(PAIRS)} pump_th={PUMP_THRESHOLDS} vol_mult={VOL_MULTS} trail={TRAIL_STOPS}")
    results = []
    for name, sym in PAIRS.items():
        d = fetch_binance(sym)
        if not d:
            print(f"  SKIP {name}: no cache")
            continue
        for pt in PUMP_THRESHOLDS:
            for vm in VOL_MULTS:
                for ts in TRAIL_STOPS:
                    r = simulate(d, pt, vm, ts)
                    if r is None: continue
                    r["pair"] = name; r["pump"] = pt; r["vol_mult"] = vm; r["trail"] = ts
                    results.append(r)

    results.sort(key=lambda x: -x["pnl_net"])
    print(f"\n=== TOP 25 par PnL net 30d ===")
    print(f"{'pair':6}{'pump%':7}{'volX':6}{'trail':7}{'trades':8}{'win%':7}{'PnL$':10}{'PnL%':8}")
    for r in results[:25]:
        print(f"{r['pair']:6}{r['pump']*100:5.1f}%{r['vol_mult']:5.1f} {r['trail']*100:5.1f}%{r['trades']:7d}{r['win_rate']:6.1f}%{r['pnl_net']:+8.3f}  {r['pnl_pct']:+6.2f}%")

    best = {}
    for r in results:
        if r["pnl_net"] <= 0: continue
        if r["pair"] not in best or r["pnl_net"] > best[r["pair"]]["pnl_net"]:
            best[r["pair"]] = r
    print(f"\n=== Meilleur par pair (PnL>0) — {len(best)}/{len(PAIRS)} ===")
    for p, r in sorted(best.items(), key=lambda x: -x[1]["pnl_net"]):
        print(f"  {p:6} pump={r['pump']*100:.0f}% volX={r['vol_mult']} trail={r['trail']*100:.1f}% → {r['trades']} trades WR={r['win_rate']}% PnL=${r['pnl_net']:+.3f}")

    profitable = sorted(best.values(), key=lambda x: -x["pnl_net"])
    print(f"\n=== Portfolios ===")
    for n in [3, 5, 8]:
        if len(profitable) < n: continue
        top = profitable[:n]
        total_pnl = sum(r["pnl_net"] for r in top)
        total_cap = n * CAPITAL
        print(f"  Top-{n}: {', '.join(r['pair'] for r in top)} → ${total_pnl:+.2f} / ${total_cap} = {total_pnl/total_cap*100:+.2f}% net 30d")

    Path("momentum_sweep_results.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

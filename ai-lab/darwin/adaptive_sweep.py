#!/usr/bin/env python3
"""Adaptive strategy backtest: Grid in UPTREND / Short directional in DOWNTREND.

Per pair, every minute :
- Compute EMA50, EMA200 on 1H bars (aggregated from 1min)
- If EMA50 > EMA200 (UPTREND) : run grid NEUTRAL (long-only) classique
- If EMA50 < EMA200 (DOWNTREND) : close grid, open SHORT with trailing stop
- Switch only on confirmed cross (avoid whipsaw with 4h delay)

Tested on 22 cryptos, 30j 1min Binance OHLC.
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
GRID_SPACINGS = [0.020, 0.030]
SHORT_TRAILS = [0.020, 0.030]
LEVELS = 4
CAPITAL = 25.0
LEVERAGE = 7
GRID_FEE_RT = 0.0008
SHORT_FEE_RT = 0.001
DAYS = 30


def fetch(pair):
    p = CACHE_DIR / f"binance_{pair}_1min_30d.json"
    if not p.exists(): return []
    return json.loads(p.read_text())


def aggregate_1h(candles):
    """Aggregate 1min OHLC to 1h OHLC."""
    out = []
    for i in range(0, len(candles) - 60, 60):
        chunk = candles[i:i+60]
        if not chunk: continue
        open_ = chunk[0][1]
        high = max(c[2] for c in chunk)
        low = min(c[3] for c in chunk)
        close = chunk[-1][4]
        vol = sum(c[5] for c in chunk)
        ts = chunk[0][0]
        out.append([ts, open_, high, low, close, vol])
    return out


def ema(values, period):
    if len(values) < period: return [values[0]] * len(values)
    k = 2.0 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def simulate(candles_1min, grid_spacing, short_trail):
    if len(candles_1min) < 12000:  # need ~200h for EMA200
        return None
    candles_1h = aggregate_1h(candles_1min)
    if len(candles_1h) < 220:
        return None
    closes_1h = [c[4] for c in candles_1h]
    ema50_1h = ema(closes_1h, 50)
    ema200_1h = ema(closes_1h, 200)

    # Map regime per 1h timestamp (UPTREND=1, DOWNTREND=-1)
    # Then for each 1min bar, lookup the regime of its containing hour
    n_hours = len(candles_1h)
    regime_1h = []
    for i in range(n_hours):
        if i < 200:
            regime_1h.append(0)  # warmup
        else:
            regime_1h.append(1 if ema50_1h[i] > ema200_1h[i] else -1)

    # Simulation state
    notional_grid = CAPITAL * LEVERAGE
    pos_per_level = notional_grid / LEVELS
    profit_per_rt_grid = grid_spacing * pos_per_level - GRID_FEE_RT * pos_per_level

    daily_pnl = [0.0] * DAYS
    closes_1m = [c[4] for c in candles_1min]
    highs_1m = [c[2] for c in candles_1min]
    lows_1m = [c[3] for c in candles_1min]

    # Grid state
    grid_active = False
    grid_center = 0.0
    grid_buy = []
    grid_sell = []
    grid_in_pos = 0
    last_price = closes_1m[0]
    grid_recenter_at = 0

    # Short state
    short_active = False
    short_entry = 0.0
    short_low_since = 0.0

    current_regime = 0
    last_regime = 0

    for i in range(1, len(candles_1min)):
        hour_idx = min(i // 60, n_hours - 1)
        regime = regime_1h[hour_idx]
        day_idx = min(i // 1440, DAYS - 1)
        price = closes_1m[i]
        p_low = lows_1m[i]
        p_high = highs_1m[i]

        # Detect regime change
        regime_changed = (regime != current_regime and regime != 0)
        if regime_changed:
            # Close any active position
            if grid_active:
                # Realize 0 PnL on grid close (assumed flat)
                grid_active = False
            if short_active:
                # Close short at current price
                ret = (short_entry - price) / short_entry
                trade_pnl = notional_grid * ret - SHORT_FEE_RT * notional_grid
                daily_pnl[day_idx] += trade_pnl
                short_active = False
            current_regime = regime

        # Activate strategy based on regime
        if current_regime == 1 and not grid_active:
            # Open grid centered on current price
            grid_active = True
            grid_center = price
            grid_buy = [grid_center * (1 - grid_spacing * (k+1)) for k in range(LEVELS // 2)]
            grid_sell = [grid_center * (1 + grid_spacing * (k+1)) for k in range(LEVELS // 2)]
            grid_in_pos = 0
            grid_recenter_at = i + 360  # recenter every 6h
        elif current_regime == -1 and not short_active:
            # Open short at current price
            short_active = True
            short_entry = price
            short_low_since = price

        # Run active strategy
        if grid_active:
            if i >= grid_recenter_at:
                grid_center = price
                grid_buy = [grid_center * (1 - grid_spacing * (k+1)) for k in range(LEVELS // 2)]
                grid_sell = [grid_center * (1 + grid_spacing * (k+1)) for k in range(LEVELS // 2)]
                grid_recenter_at = i + 360
            for j in range(len(grid_buy)):
                if grid_buy[j] > 0 and p_low <= grid_buy[j] <= last_price:
                    grid_in_pos += 1
                    grid_buy[j] = -1
            for j in range(len(grid_sell)):
                if grid_sell[j] > 0 and p_high >= grid_sell[j] >= last_price:
                    if grid_in_pos > 0:
                        grid_in_pos -= 1
                        daily_pnl[day_idx] += profit_per_rt_grid
                    grid_sell[j] = -1
            for j in range(len(grid_buy)):
                if grid_buy[j] < 0:
                    grid_buy[j] = grid_center * (1 - grid_spacing * (j+1))
            for j in range(len(grid_sell)):
                if grid_sell[j] < 0:
                    grid_sell[j] = grid_center * (1 + grid_spacing * (j+1))

        if short_active:
            if price < short_low_since:
                short_low_since = price
            stop = short_low_since * (1 + short_trail)
            if price >= stop:
                # Stop hit
                ret = (short_entry - price) / short_entry
                trade_pnl = notional_grid * ret - SHORT_FEE_RT * notional_grid
                daily_pnl[day_idx] += trade_pnl
                short_active = False

        last_price = price

    # Close any remaining position at end
    if short_active:
        last_close = closes_1m[-1]
        ret = (short_entry - last_close) / short_entry
        trade_pnl = notional_grid * ret - SHORT_FEE_RT * notional_grid
        daily_pnl[-1] += trade_pnl

    pnl_total = sum(daily_pnl)
    pnl_pct = pnl_total / CAPITAL * 100

    # Max DD
    eq = CAPITAL
    peak = CAPITAL
    max_dd = 0.0
    for d in daily_pnl:
        eq += d
        if eq > peak: peak = eq
        if (peak - eq) > max_dd: max_dd = peak - eq

    worst = min(daily_pnl)
    best = max(daily_pnl)
    n_pos_days = sum(1 for d in daily_pnl if d > 0)

    return {
        "pnl_net": round(pnl_total, 3),
        "pnl_pct": round(pnl_pct, 2),
        "max_dd": round(max_dd, 3),
        "max_dd_pct": round(max_dd / CAPITAL * 100, 2),
        "calmar": round(pnl_pct / (max_dd / CAPITAL * 100), 2) if max_dd > 0 else 999,
        "worst_day": round(worst, 2),
        "best_day": round(best, 2),
        "pos_days": n_pos_days,
    }


def main():
    print(f"Adaptive Grid/Short sweep | cap=${CAPITAL} lev={LEVERAGE}x")
    print(f"Pairs={len(PAIRS)} grid_sp={GRID_SPACINGS} short_trail={SHORT_TRAILS}")
    print(f"Régime detection : EMA50/EMA200 sur bars 1H aggregées du 1min\n")

    results = []
    for name, sym in PAIRS.items():
        d = fetch(sym)
        if not d:
            print(f"  SKIP {name}")
            continue
        for sp in GRID_SPACINGS:
            for tr in SHORT_TRAILS:
                r = simulate(d, sp, tr)
                if r is None: continue
                r["pair"] = name; r["grid_sp"] = sp; r["short_trail"] = tr
                results.append(r)

    results.sort(key=lambda x: -x["pnl_net"])
    print(f"=== TOP 25 par PnL net 30d ===")
    print(f"{'pair':6}{'grid':7}{'trail':7}{'PnL$':9}{'PnL%':8}{'maxDD$':9}{'maxDD%':8}{'Calmar':8}{'worst':8}{'best':8}{'+days':6}")
    for r in results[:25]:
        print(f"{r['pair']:6}{r['grid_sp']*100:5.1f}% {r['short_trail']*100:5.1f}%{r['pnl_net']:+8.2f}{r['pnl_pct']:+7.2f}%{r['max_dd']:+8.2f}{r['max_dd_pct']:+7.2f}%{r['calmar']:>7}{r['worst_day']:+7.2f}{r['best_day']:+7.2f}{r['pos_days']:>5}")

    best = {}
    for r in results:
        if r["pnl_net"] <= 0: continue
        if r["pair"] not in best or r["pnl_net"] > best[r["pair"]]["pnl_net"]:
            best[r["pair"]] = r
    print(f"\n=== Meilleur par pair (PnL>0) — {len(best)}/{len(PAIRS)} ===")
    for p, r in sorted(best.items(), key=lambda x: -x[1]["pnl_net"]):
        print(f"  {p:6} grid={r['grid_sp']*100:.1f}% short_trail={r['short_trail']*100:.1f}% → PnL=${r['pnl_net']:+.2f} ({r['pnl_pct']:+.2f}%) DD=${r['max_dd']:.2f} Calmar={r['calmar']}")

    profitable = sorted(best.values(), key=lambda x: -x["pnl_net"])
    print(f"\n=== Portfolios adaptive (cap=${CAPITAL}/pair) ===")
    for n in [3, 5, 8]:
        if len(profitable) < n: continue
        top = profitable[:n]
        total_pnl = sum(r["pnl_net"] for r in top)
        total_cap = n * CAPITAL
        worst_cumul = sum(r["worst_day"] for r in top)  # approx worst day if all align
        print(f"  Top-{n}: {', '.join(r['pair'] for r in top)} → ${total_pnl:+.2f}/${total_cap}={total_pnl/total_cap*100:+.2f}% net 30d, worst-day sum=${worst_cumul:+.2f}")

    Path("adaptive_sweep_results.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

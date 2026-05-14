#!/usr/bin/env python3
"""High-frequency sweep: tight spacings (0.2% to 1.5%), small capital ($5/pair),
many crypto pairs, target = MAX RTs/day net of fees.

Tony brief 0512: "trade peu mais souvent, 5 EUR par crypto, max trades."
Granularity 1min for robustness, 30 days. Gate V4 RSI+ATR.

Output: ranked by RTs/day AND by net PnL %. Show fee-eaten candidates.
"""
import json, time, urllib.request
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)

# Wide pair universe — anything with $5M+ daily vol on Binance
PAIRS = {
    "LTC": "LTCUSDT", "ATOM": "ATOMUSDT", "AVAX": "AVAXUSDT", "AAVE": "AAVEUSDT",
    "UNI": "UNIUSDT", "INJ": "INJUSDT", "NEAR": "NEARUSDT", "FIL": "FILUSDT",
    "XRP": "XRPUSDT", "DOGE": "DOGEUSDT",
    "LINK": "LINKUSDT", "SOL": "SOLUSDT", "DOT": "DOTUSDT", "ADA": "ADAUSDT",
    "MATIC": "MATICUSDT", "ETH": "ETHUSDT", "BTC": "BTCUSDT",
    "OP": "OPUSDT", "ARB": "ARBUSDT", "APT": "APTUSDT",
    "SUI": "SUIUSDT", "TIA": "TIAUSDT",
}

SPACINGS = [0.002, 0.003, 0.004, 0.005, 0.007, 0.010, 0.015]  # tight!
LEVELS_LIST = [4, 6, 8, 10, 12]
CAPITAL_PER_PAIR = 5.0   # Tony brief: $5/crypto
LEVERAGE = 7
FEE_RT = 0.0008  # ~0.04% × 2 (maker)
DAYS_BACK = 30

RSI_MIN, RSI_MAX = 36.0, 66.0
ATR_MIN, ATR_MAX = 1.12, 2.17


def fetch_binance(pair, days=DAYS_BACK):
    cache = CACHE_DIR / f"binance_{pair}_1min_{days}d.json"
    if cache.exists() and (time.time() - cache.stat().st_mtime) < 6 * 3600:
        return json.loads(cache.read_text())
    out = []
    end_ms = int(time.time() * 1000)
    cursor = end_ms - days * 86400 * 1000
    while cursor < end_ms:
        url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=1m&startTime={cursor}&endTime={end_ms}&limit=1000"
        try:
            d = json.loads(urllib.request.urlopen(url, timeout=20).read())
        except Exception as e:
            print(f"  fetch err {pair}: {e}"); break
        if not d: break
        out.extend([[int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in d])
        last_close = int(d[-1][6])
        if last_close <= cursor: break
        cursor = last_close + 1
        if len(d) < 1000: break
        time.sleep(0.12)
    cache.write_text(json.dumps(out))
    return out


def rsi_series(closes, period=14):
    if len(closes) < period + 1: return [50.0] * len(closes)
    rsi = [50.0] * period
    gains = losses = 0.0
    for i in range(1, period + 1):
        delta = closes[i] - closes[i-1]
        if delta > 0: gains += delta
        else: losses -= delta
    avg_g = gains / period
    avg_l = losses / period
    rs = avg_g / avg_l if avg_l > 0 else 999
    rsi.append(100 - 100 / (1 + rs))
    for i in range(period + 1, len(closes)):
        delta = closes[i] - closes[i-1]
        g = delta if delta > 0 else 0
        l = -delta if delta < 0 else 0
        avg_g = (avg_g * (period - 1) + g) / period
        avg_l = (avg_l * (period - 1) + l) / period
        rs = avg_g / avg_l if avg_l > 0 else 999
        rsi.append(100 - 100 / (1 + rs))
    return rsi


def atr_pct_series(highs, lows, closes, period=14):
    if len(closes) < period + 1: return [1.0] * len(closes)
    trs = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        trs.append(tr)
    atr = [trs[0]] * period
    a = sum(trs[:period]) / period
    atr.append(a)
    for i in range(period + 1, len(closes)):
        a = (a * (period - 1) + trs[i]) / period
        atr.append(a)
    return [(atr[i] / closes[i] * 100) if closes[i] > 0 else 1.0 for i in range(len(closes))]


def gate_open(rsi, atr_pct):
    return RSI_MIN <= rsi <= RSI_MAX and ATR_MIN <= atr_pct <= ATR_MAX


def simulate(candles, spacing_pct, n_levels, capital, leverage):
    if len(candles) < 60: return None
    closes = [c[4] for c in candles]
    highs = [c[2] for c in candles]
    lows = [c[3] for c in candles]
    rsi = rsi_series(closes)
    atr = atr_pct_series(highs, lows, closes)

    # buy_levels = below center, sell = above; long-only grid
    # On price cross down a buy → fill, increment buy_count
    # On price cross up a sell → fill, increment sell_count
    # RT = min(buy_count, sell_count); profit per RT = spacing × position_value × leverage - 2*fee
    fills_b = fills_s = 0
    rts = 0
    pnl_net = 0.0
    eq_curve = [capital]
    peak = capital
    max_dd = 0.0
    in_pos = 0
    pos_per_level = (capital * leverage) / n_levels
    profit_per_rt = spacing_pct * pos_per_level - FEE_RT * pos_per_level

    # Recenter every 6 hours = 360 1-min bars, only if gate OPEN
    recenter_period = 360
    next_recenter = recenter_period
    center = closes[0]
    half_span = spacing_pct * (n_levels // 2)
    upper = center * (1 + half_span)
    lower = center * (1 - half_span)
    buy_grid = [center * (1 - spacing_pct * (i+1)) for i in range(n_levels // 2)]
    sell_grid = [center * (1 + spacing_pct * (i+1)) for i in range(n_levels // 2)]

    last_price = closes[0]
    for i in range(1, len(candles)):
        if i >= next_recenter and gate_open(rsi[i], atr[i]):
            center = closes[i]
            buy_grid = [center * (1 - spacing_pct * (k+1)) for k in range(n_levels // 2)]
            sell_grid = [center * (1 + spacing_pct * (k+1)) for k in range(n_levels // 2)]
            next_recenter = i + recenter_period

        if not gate_open(rsi[i], atr[i]):
            last_price = closes[i]
            continue

        p_low = lows[i]
        p_high = highs[i]
        # buy fills: any buy level between p_low and last_price (or p_high) gets filled
        for j, lvl in enumerate(buy_grid):
            if p_low <= lvl <= last_price:
                fills_b += 1
                in_pos += 1
                # mark this level filled — re-set above current to avoid double-fill same bar
                buy_grid[j] = -1
        for j, lvl in enumerate(sell_grid):
            if p_high >= lvl >= last_price:
                fills_s += 1
                if in_pos > 0:
                    in_pos -= 1
                    rts += 1
                    pnl_net += profit_per_rt
                sell_grid[j] = -1

        # restore filled levels at next bar (simplified: replenish if center stable)
        for j, lvl in enumerate(buy_grid):
            if lvl < 0:
                buy_grid[j] = center * (1 - spacing_pct * (j+1))
        for j, lvl in enumerate(sell_grid):
            if lvl < 0:
                sell_grid[j] = center * (1 + spacing_pct * (j+1))

        last_price = closes[i]
        eq = capital + pnl_net
        eq_curve.append(eq)
        if eq > peak: peak = eq
        dd = peak - eq
        if dd > max_dd: max_dd = dd

    pnl_pct = pnl_net / capital * 100
    rt_per_day = rts / DAYS_BACK
    fills_per_day = (fills_b + fills_s) / DAYS_BACK
    calmar = round(pnl_pct / (max_dd / capital * 100), 2) if max_dd > 0 else 999
    return {
        "rts": rts, "fills_b": fills_b, "fills_s": fills_s,
        "pnl_net": round(pnl_net, 4),
        "pnl_pct": round(pnl_pct, 2),
        "rt_per_day": round(rt_per_day, 2),
        "fills_per_day": round(fills_per_day, 2),
        "max_dd": round(max_dd, 4),
        "calmar": calmar,
    }


def main():
    print(f"Capital per pair: ${CAPITAL_PER_PAIR} | Leverage: {LEVERAGE}x | Fee RT: {FEE_RT*100}%")
    print(f"Pairs: {len(PAIRS)} | Spacings: {SPACINGS} | Levels: {LEVELS_LIST}")

    all_data = {}
    for name, sym in PAIRS.items():
        print(f"loading {name} ({sym})...")
        d = fetch_binance(sym)
        if not d:
            print(f"  SKIP {name}: no data")
            continue
        print(f"  {len(d)} candles ({len(d)/(86400/60):.1f}d)")
        all_data[name] = d

    print(f"\nRunning {len(all_data)} × {len(SPACINGS)} × {len(LEVELS_LIST)} = {len(all_data)*len(SPACINGS)*len(LEVELS_LIST)} simulations...\n")

    results = []
    for name, candles in all_data.items():
        for sp in SPACINGS:
            for lv in LEVELS_LIST:
                r = simulate(candles, sp, lv, CAPITAL_PER_PAIR, LEVERAGE)
                if r is None: continue
                r["pair"] = name; r["spacing"] = sp; r["levels"] = lv
                results.append(r)

    # Top 25 by net PnL
    results.sort(key=lambda x: -x["pnl_net"])
    print("=== TOP 25 par PnL net 30d ===")
    print(f"{'pair':6}{'sp%':6}{'lv':4}{'RT':5}{'RT/d':6}{'fills/d':9}{'PnL$':11}{'PnL%':8}{'maxDD$':9}{'Calmar':8}")
    for r in results[:25]:
        print(f"{r['pair']:6}{r['spacing']*100:5.2f}%{r['levels']:4d}{r['rts']:5d}{r['rt_per_day']:6.2f}{r['fills_per_day']:9.2f}  {r['pnl_net']:+8.4f}{r['pnl_pct']:+7.2f}%{r['max_dd']:+8.4f} {r['calmar']:7.2f}")

    # Top 25 by RT/day (Tony brief: max trades)
    results.sort(key=lambda x: -x["rt_per_day"])
    print("\n=== TOP 25 par RT/day (Tony brief: max trades) ===")
    print(f"{'pair':6}{'sp%':6}{'lv':4}{'RT':5}{'RT/d':6}{'fills/d':9}{'PnL$':11}{'PnL%':8}")
    for r in results[:25]:
        print(f"{r['pair']:6}{r['spacing']*100:5.2f}%{r['levels']:4d}{r['rts']:5d}{r['rt_per_day']:6.2f}{r['fills_per_day']:9.2f}  {r['pnl_net']:+8.4f}{r['pnl_pct']:+7.2f}%")

    # Best per pair (max RT/day with PnL > 0)
    best_per_pair = {}
    for r in results:
        if r["pnl_net"] <= 0: continue
        if r["pair"] not in best_per_pair or r["rt_per_day"] > best_per_pair[r["pair"]]["rt_per_day"]:
            best_per_pair[r["pair"]] = r
    print("\n=== Meilleur RT/day par pair (PnL > 0) ===")
    for p, r in sorted(best_per_pair.items(), key=lambda x: -x[1]["rt_per_day"]):
        print(f"  {p:6} sp={r['spacing']*100:.2f}% lv={r['levels']:2d} → RT/d={r['rt_per_day']:.2f} fills/d={r['fills_per_day']:.2f} PnL=${r['pnl_net']:+.4f} ({r['pnl_pct']:+.2f}%)")

    # Portfolio: combine all pairs that hit PnL > 0
    profitable = [v for v in best_per_pair.values()]
    profitable.sort(key=lambda x: -x["pnl_pct"])
    print(f"\n=== Portfolio: {len(profitable)} pairs profitables (5$ each) ===")
    total_cap = len(profitable) * CAPITAL_PER_PAIR
    total_pnl = sum(r["pnl_net"] for r in profitable)
    total_rt = sum(r["rts"] for r in profitable)
    print(f"  Capital total: ${total_cap}")
    print(f"  PnL net 30d:   ${total_pnl:+.2f} ({total_pnl/total_cap*100:+.2f}%)")
    print(f"  Total RTs:     {total_rt} ({total_rt/DAYS_BACK:.1f}/day)")

    out_path = Path(__file__).parent / "highfreq_sweep_1min_results.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nFull: {out_path}")


if __name__ == "__main__":
    main()

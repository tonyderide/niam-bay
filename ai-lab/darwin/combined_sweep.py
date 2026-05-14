#!/usr/bin/env python3
"""Combined backtest: Grid + Momentum sur le même portefeuille.

Simule les 2 stratégies tournant en parallèle sur la même période 30j 1min.
Track le PnL combiné jour par jour pour mesurer :
- Drawdown réel combiné (vs somme naïve)
- Corrélation des returns entre stratégies
- Allocation capital optimale
"""
import json
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "data_cache"

# === SETUP : 2 portfolios à tester ===
GRID_PAIRS = ["LTC", "ATOM", "AVAX"]   # Top-3 grid backtest
MOMENTUM_PAIRS = ["INJ", "SUI", "OP"]  # Top-3 momentum backtest

# Best params from individual sweeps
GRID_PARAMS = {
    "LTC":  {"sym": "LTCUSDT",  "spacing": 0.030, "levels": 4},
    "ATOM": {"sym": "ATOMUSDT", "spacing": 0.020, "levels": 4},
    "AVAX": {"sym": "AVAXUSDT", "spacing": 0.030, "levels": 4},
}
MOMENTUM_PARAMS = {
    "INJ": {"sym": "INJUSDT", "pump": 0.02, "vol_mult": 1.5, "trail": 0.03},
    "SUI": {"sym": "SUIUSDT", "pump": 0.03, "vol_mult": 2.0, "trail": 0.03},
    "OP":  {"sym": "OPUSDT",  "pump": 0.02, "vol_mult": 1.5, "trail": 0.03},
}

LEVERAGE = 7
GRID_FEE_RT = 0.0008  # maker
MOM_FEE_RT = 0.001    # taker x2

# 3 allocations à tester
ALLOCATIONS = [
    {"name": "A_60grid_40mom", "grid_per_pair": 16, "mom_per_pair": 17},
    {"name": "B_30grid_70mom", "grid_per_pair": 13, "mom_per_pair": 19},
    {"name": "C_pure_momentum", "grid_per_pair": 0,  "mom_per_pair": 26},
    {"name": "D_pure_grid",    "grid_per_pair": 25, "mom_per_pair": 0},
]

DAYS = 30
MINUTES_PER_DAY = 1440

# Gate V4 thresholds (pour grid)
RSI_MIN, RSI_MAX = 36.0, 66.0
ATR_MIN, ATR_MAX = 1.12, 2.17


def fetch(pair):
    p = CACHE_DIR / f"binance_{pair}_1min_30d.json"
    if not p.exists(): return []
    return json.loads(p.read_text())


def ema(values, period):
    if len(values) < period: return [values[0]] * len(values)
    k = 2.0 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def rsi_series(closes, period=14):
    if len(closes) < period + 1: return [50.0] * len(closes)
    out = [50.0] * period
    g = l = 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i-1]
        if d > 0: g += d
        else: l -= d
    avg_g = g / period; avg_l = l / period
    rs = avg_g / avg_l if avg_l > 0 else 999
    out.append(100 - 100 / (1 + rs))
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i-1]
        ga = d if d > 0 else 0
        la = -d if d < 0 else 0
        avg_g = (avg_g * (period - 1) + ga) / period
        avg_l = (avg_l * (period - 1) + la) / period
        rs = avg_g / avg_l if avg_l > 0 else 999
        out.append(100 - 100 / (1 + rs))
    return out


def atr_pct(highs, lows, closes, period=14):
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


def simulate_grid_daily(candles, spacing, levels, capital, lev):
    """Returns daily PnL series (list of size 30)."""
    if len(candles) < 60 or capital <= 0:
        return [0.0] * DAYS
    closes = [c[4] for c in candles]
    highs = [c[2] for c in candles]
    lows = [c[3] for c in candles]
    rsi = rsi_series(closes)
    atr = atr_pct(highs, lows, closes)
    pos_per_level = (capital * lev) / levels
    profit_per_rt = spacing * pos_per_level - GRID_FEE_RT * pos_per_level

    center = closes[0]
    half = spacing * (levels // 2)
    buy_grid = [center * (1 - spacing * (k+1)) for k in range(levels // 2)]
    sell_grid = [center * (1 + spacing * (k+1)) for k in range(levels // 2)]
    in_pos = 0
    daily_pnl = [0.0] * DAYS
    last_price = closes[0]
    next_recenter = 360

    for i in range(1, len(candles)):
        day_idx = min(i // MINUTES_PER_DAY, DAYS - 1)
        if i >= next_recenter and gate_open(rsi[i], atr[i]):
            center = closes[i]
            buy_grid = [center * (1 - spacing * (k+1)) for k in range(levels // 2)]
            sell_grid = [center * (1 + spacing * (k+1)) for k in range(levels // 2)]
            next_recenter = i + 360
        if not gate_open(rsi[i], atr[i]):
            last_price = closes[i]; continue
        p_low = lows[i]; p_high = highs[i]
        for j, lvl in enumerate(buy_grid):
            if p_low <= lvl <= last_price:
                in_pos += 1
                buy_grid[j] = -1
        for j, lvl in enumerate(sell_grid):
            if p_high >= lvl >= last_price:
                if in_pos > 0:
                    in_pos -= 1
                    daily_pnl[day_idx] += profit_per_rt
                sell_grid[j] = -1
        for j in range(len(buy_grid)):
            if buy_grid[j] < 0: buy_grid[j] = center * (1 - spacing * (j+1))
        for j in range(len(sell_grid)):
            if sell_grid[j] < 0: sell_grid[j] = center * (1 + spacing * (j+1))
        last_price = closes[i]
    return daily_pnl


def simulate_momentum_daily(candles, pump_th, vol_mult, trail_pct, capital, lev):
    if len(candles) < 500 or capital <= 0:
        return [0.0] * DAYS
    closes = [c[4] for c in candles]
    vols = [c[5] for c in candles]
    notional = capital * lev
    daily_pnl = [0.0] * DAYS
    pos = 0; entry = 0.0; high_since = 0.0
    cooldown = 0
    pos_open_day = 0

    for i in range(360, len(candles)):
        day_idx = min(i // MINUTES_PER_DAY, DAYS - 1)
        if cooldown > 0:
            cooldown -= 1; continue
        price = closes[i]
        if pos == 1:
            if price > high_since: high_since = price
            stop = high_since * (1 - trail_pct)
            tp = entry * (1 + 2 * trail_pct)
            if price <= stop or price >= tp:
                ret = (price - entry) / entry
                trade_pnl = notional * ret - MOM_FEE_RT * notional
                # Attribuer le PnL au jour de fermeture
                daily_pnl[day_idx] += trade_pnl
                pos = 0; cooldown = 60
            continue
        if closes[i-60] <= 0: continue
        ret_1h = closes[i] / closes[i-60] - 1
        if ret_1h < pump_th: continue
        vol_1h = sum(vols[i-60:i])
        vol_5h = sum(vols[i-360:i-60]) / 5.0
        if vol_5h <= 0: continue
        if vol_1h / vol_5h < vol_mult: continue
        pos = 1; entry = price; high_since = price; pos_open_day = day_idx
    return daily_pnl


def run_allocation(alloc):
    name = alloc["name"]
    g_cap = alloc["grid_per_pair"]
    m_cap = alloc["mom_per_pair"]
    total_cap = g_cap * len(GRID_PAIRS) + m_cap * len(MOMENTUM_PAIRS)

    # Per-pair daily PnL
    grid_daily = []
    for p in GRID_PAIRS:
        cd = fetch(GRID_PARAMS[p]["sym"])
        d = simulate_grid_daily(cd, GRID_PARAMS[p]["spacing"], GRID_PARAMS[p]["levels"], g_cap, LEVERAGE)
        grid_daily.append(d)
    mom_daily = []
    for p in MOMENTUM_PAIRS:
        cd = fetch(MOMENTUM_PARAMS[p]["sym"])
        d = simulate_momentum_daily(cd, MOMENTUM_PARAMS[p]["pump"], MOMENTUM_PARAMS[p]["vol_mult"],
                                     MOMENTUM_PARAMS[p]["trail"], m_cap, LEVERAGE)
        mom_daily.append(d)

    # Combined daily PnL
    combined = [0.0] * DAYS
    grid_total = [0.0] * DAYS
    mom_total = [0.0] * DAYS
    for d in range(DAYS):
        gd = sum(s[d] for s in grid_daily)
        md = sum(s[d] for s in mom_daily)
        grid_total[d] = gd
        mom_total[d] = md
        combined[d] = gd + md

    # Equity curve
    equity = [total_cap]
    for d in range(DAYS):
        equity.append(equity[-1] + combined[d])
    pnl_total = sum(combined)
    pnl_pct = pnl_total / total_cap * 100 if total_cap > 0 else 0

    # Max DD on equity
    peak = total_cap
    max_dd = 0.0
    for eq in equity[1:]:
        if eq > peak: peak = eq
        dd = peak - eq
        if dd > max_dd: max_dd = dd

    # Naive sum of individual contributions
    naive_total = sum(grid_total) + sum(mom_total)

    # Worst single day
    worst_day = min(combined)
    best_day = max(combined)

    # Correlation grid_total vs mom_total
    n = DAYS
    mg = sum(grid_total) / n
    mm = sum(mom_total) / n
    num = sum((grid_total[d] - mg) * (mom_total[d] - mm) for d in range(n))
    sg = (sum((x - mg) ** 2 for x in grid_total) / n) ** 0.5
    sm = (sum((x - mm) ** 2 for x in mom_total) / n) ** 0.5
    corr = num / (n * sg * sm) if sg > 0 and sm > 0 else 0.0

    return {
        "name": name,
        "total_cap": total_cap,
        "grid_pnl_30d": round(sum(grid_total), 2),
        "mom_pnl_30d": round(sum(mom_total), 2),
        "combined_pnl_30d": round(pnl_total, 2),
        "pnl_pct_30d": round(pnl_pct, 2),
        "max_dd": round(max_dd, 2),
        "max_dd_pct": round(max_dd / total_cap * 100, 2) if total_cap > 0 else 0,
        "calmar": round(pnl_pct / (max_dd / total_cap * 100), 2) if max_dd > 0 else 999,
        "worst_day": round(worst_day, 2),
        "best_day": round(best_day, 2),
        "corr_grid_mom": round(corr, 3),
        "live_derate_50pct": round(pnl_pct / 2, 2),
    }


def main():
    print(f"Combined sweep — Grid+Momentum sur même portefeuille (30j 1min)")
    print(f"Grid pairs: {GRID_PAIRS}  | Momentum pairs: {MOMENTUM_PAIRS}")
    print(f"Lev={LEVERAGE}x  fees: grid {GRID_FEE_RT*100}%/RT, mom {MOM_FEE_RT*100}%/RT\n")

    results = []
    for alloc in ALLOCATIONS:
        r = run_allocation(alloc)
        results.append(r)

    print(f"{'Allocation':22}{'Cap':6}{'PnL$':9}{'PnL%':8}{'MaxDD$':9}{'MaxDD%':8}{'Calmar':8}{'Worst':8}{'Best':8}{'Corr':7}{'Live%':7}")
    for r in results:
        print(f"{r['name']:22}{r['total_cap']:>6}{r['combined_pnl_30d']:+8.2f}{r['pnl_pct_30d']:+7.2f}%{r['max_dd']:+8.2f}{r['max_dd_pct']:+7.2f}%{r['calmar']:>7}{r['worst_day']:+7.2f}{r['best_day']:+7.2f}{r['corr_grid_mom']:+6.2f}{r['live_derate_50pct']:+6.2f}%")

    print(f"\n=== Détails par allocation ===")
    for r in results:
        print(f"\n{r['name']}: cap={r['total_cap']}$")
        print(f"  Grid contribution : ${r['grid_pnl_30d']:+.2f} ({r['grid_pnl_30d']/r['total_cap']*100:+.2f}%)")
        print(f"  Momentum contrib  : ${r['mom_pnl_30d']:+.2f} ({r['mom_pnl_30d']/r['total_cap']*100:+.2f}%)")
        print(f"  Combined          : ${r['combined_pnl_30d']:+.2f} ({r['pnl_pct_30d']:+.2f}%)")
        print(f"  Max DD            : ${r['max_dd']:.2f} ({r['max_dd_pct']:.2f}%)")
        print(f"  Worst day         : ${r['worst_day']:+.2f}")
        print(f"  Calmar            : {r['calmar']}")
        print(f"  Corr grid<->mom   : {r['corr_grid_mom']}  (proche 0 = décorrélé = bon)")
        print(f"  Live derate 50%   : {r['live_derate_50pct']:+.2f}% / 30j")

    Path("combined_sweep_results.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Backtest des 3 stratégies Reddit les plus prometteuses + walk-forward.

Strategies testées :
1. DONCHIAN 20/55 Turtle (daily) — robuste cross-régime, breakout high20 / exit low10, stop 2×ATR(20)
2. TREND EMA+ATR (4h) — long si EMA20>EMA50 & ATR rising, exit close<EMA50, stop 2×ATR
3. CONNORS RSI2 (daily) — long si close<SMA200 & RSI(2)<10, exit close>SMA5

Tous avec amendements traders : cap $25, lev 3x, walk-forward W1+W2 train, W0+W3 valid.
"""
import json, time, urllib.request, datetime, math
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "data_cache"

PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT", "AVAXUSDT"]

WINDOWS = {
    "W0_current_30j":  None,
    "W1_2024_bull":    ("2024-03-01", "2024-04-30"),
    "W2_2024_transit": ("2024-10-01", "2024-12-31"),
    "W3_2025_chop":    ("2025-02-01", "2025-03-31"),
}
TRAIN_WINDOWS = ["W1_2024_bull", "W2_2024_transit"]
VALID_WINDOWS = ["W0_current_30j", "W3_2025_chop"]

CAPITAL = 25.0
LEVERAGE = 3
FEE_RT = 0.001  # taker (most strats use market exit on stop)


def to_ms(date_str):
    return int(datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(
        tzinfo=datetime.timezone.utc).timestamp() * 1000)


def fetch_binance_range(pair, start_ms, end_ms):
    cache = CACHE_DIR / f"binance_{pair}_1min_{start_ms}_{end_ms}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    out = []
    cursor = start_ms
    while cursor < end_ms:
        url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=1m&startTime={cursor}&endTime={end_ms}&limit=1000"
        try:
            d = json.loads(urllib.request.urlopen(url, timeout=20).read())
        except Exception as e:
            print(f"    fetch err {pair}: {e}"); time.sleep(2); continue
        if not d: break
        out.extend([[int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in d])
        last_close = int(d[-1][6])
        if last_close <= cursor: break
        cursor = last_close + 1
        if len(d) < 1000: break
        time.sleep(0.10)
    cache.write_text(json.dumps(out))
    return out


def fetch_binance_30d(pair):
    p = CACHE_DIR / f"binance_{pair}_1min_30d.json"
    if p.exists(): return json.loads(p.read_text())
    return []


def aggregate(candles, period_min):
    """Aggregate 1min OHLCV to N-minute bars."""
    out = []
    for i in range(0, len(candles) - period_min, period_min):
        chunk = candles[i:i+period_min]
        if not chunk: continue
        out.append([chunk[0][0], chunk[0][1],
                    max(c[2] for c in chunk),
                    min(c[3] for c in chunk),
                    chunk[-1][4],
                    sum(c[5] for c in chunk)])
    return out


def ema(values, period):
    if len(values) < period: return [values[0]] * len(values)
    k = 2.0 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def sma(values, period):
    n = len(values)
    out = [values[0]] * n
    csum = 0.0
    for i in range(n):
        csum += values[i]
        if i >= period:
            csum -= values[i - period]
        if i >= period - 1:
            out[i] = csum / period
    return out


def rsi(closes, period=14):
    n = len(closes)
    if n < period + 1: return [50.0] * n
    out = [50.0] * period
    g = l = 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i-1]
        if d > 0: g += d
        else: l -= d
    avg_g = g / period; avg_l = l / period
    rs = avg_g / avg_l if avg_l > 0 else 999
    out.append(100 - 100 / (1 + rs))
    for i in range(period + 1, n):
        d = closes[i] - closes[i-1]
        ga = d if d > 0 else 0
        la = -d if d < 0 else 0
        avg_g = (avg_g * (period - 1) + ga) / period
        avg_l = (avg_l * (period - 1) + la) / period
        rs = avg_g / avg_l if avg_l > 0 else 999
        out.append(100 - 100 / (1 + rs))
    return out


def atr(highs, lows, closes, period=14):
    n = len(closes)
    if n < period + 1: return [0.0] * n
    trs = [highs[0] - lows[0]]
    for i in range(1, n):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        trs.append(tr)
    out = [0.0] * period
    a = sum(trs[:period]) / period
    out.append(a)
    for i in range(period + 1, n):
        a = (a * (period - 1) + trs[i]) / period
        out.append(a)
    return out


def donchian(values, period):
    """Returns (high_n, low_n) rolling."""
    n = len(values)
    high_n = [0.0] * n
    low_n = [0.0] * n
    for i in range(n):
        lo = max(0, i - period + 1)
        sub = values[lo:i+1]
        high_n[i] = max(sub)
        low_n[i] = min(sub)
    return high_n, low_n


def stats_from_trades(trades, n_bars):
    n = len(trades)
    if n == 0:
        return {"trades": 0, "pnl_total": 0, "pnl_pct": 0, "sharpe": 0,
                "win_rate": 0, "max_dd_pct": 0}
    pnl_total = sum(t["pnl"] for t in trades)
    pnl_pct = pnl_total / CAPITAL * 100
    wins = sum(1 for t in trades if t["pnl"] > 0)
    win_rate = wins / n * 100

    eq_curve = [CAPITAL] * n_bars
    cum = 0
    for t in trades:
        cum += t["pnl"]
        for j in range(t["exit_idx"], n_bars):
            eq_curve[j] = CAPITAL + cum
    peak = CAPITAL; max_dd = 0
    for eq in eq_curve:
        if eq > peak: peak = eq
        if (peak - eq) > max_dd: max_dd = peak - eq

    # Sharpe (use daily sample if enough)
    bars_per_day = n_bars / 30 if n_bars > 30 else 1
    sample_step = max(1, int(bars_per_day))
    daily_eq = [eq_curve[d] for d in range(0, n_bars, sample_step)]
    if len(daily_eq) < 5:
        sharpe = 0
    else:
        rets = [(daily_eq[i] - daily_eq[i-1]) / daily_eq[i-1] for i in range(1, len(daily_eq))]
        if len(rets) >= 2:
            mean_r = sum(rets) / len(rets)
            var = sum((r - mean_r) ** 2 for r in rets) / len(rets)
            std_r = math.sqrt(var)
            sharpe = (mean_r / std_r * math.sqrt(365)) if std_r > 0 else 0
        else:
            sharpe = 0

    return {
        "trades": n, "pnl_total": round(pnl_total, 3),
        "pnl_pct": round(pnl_pct, 2), "sharpe": round(sharpe, 2),
        "win_rate": round(win_rate, 1),
        "max_dd_pct": round(max_dd / CAPITAL * 100, 2),
    }


# ============== STRATEGY 1: DONCHIAN 20/55 TURTLE ==============

def sim_donchian(candles_1min, n_high=20, n_exit=10, atr_period=20, sl_mult=2.0):
    """Donchian breakout long-only (no short pour simplicity, $134 cap)."""
    candles = aggregate(candles_1min, 1440)  # daily bars
    if len(candles) < 60:
        return None
    closes = [c[4] for c in candles]
    highs = [c[2] for c in candles]
    lows = [c[3] for c in candles]
    hi_n, _ = donchian(highs, n_high)
    _, lo_n = donchian(lows, n_exit)
    atr_v = atr(highs, lows, closes, atr_period)
    notional = CAPITAL * LEVERAGE

    trades = []
    pos = 0
    entry_price = 0.0
    entry_idx = 0
    sl_level = 0.0

    for i in range(max(n_high, atr_period) + 5, len(candles)):
        if pos == 1:
            # Exit on hit lo_exit OR stop loss
            hit_sl = (lows[i] <= sl_level)
            hit_exit = (closes[i] < lo_n[i-1])
            if hit_sl or hit_exit:
                exit_price = sl_level if hit_sl else closes[i]
                ret = (exit_price - entry_price) / entry_price
                pnl = notional * ret - FEE_RT * notional
                trades.append({"entry_idx": entry_idx, "exit_idx": i,
                              "side": "L", "pnl": pnl, "reason": "SL" if hit_sl else "EXIT"})
                pos = 0

        if pos == 0:
            # Long entry on breakout above hi_n
            if highs[i] >= hi_n[i-1] and atr_v[i] > 0:
                pos = 1
                entry_price = hi_n[i-1]
                entry_idx = i
                sl_level = entry_price - sl_mult * atr_v[i]

    # Close at end
    if pos == 1:
        ret = (closes[-1] - entry_price) / entry_price
        pnl = notional * ret - FEE_RT * notional
        trades.append({"entry_idx": entry_idx, "exit_idx": len(candles)-1,
                      "side": "L", "pnl": pnl, "reason": "END"})

    return stats_from_trades(trades, len(candles))


# ============== STRATEGY 2: TREND EMA+ATR (4H) ==============

def sim_trend_ema(candles_1min, ema_fast=20, ema_slow=50, atr_period=14, sl_mult=2.0):
    """Long quand EMA20>EMA50 & ATR rising sur 3 bars, exit close<EMA50, stop 2×ATR."""
    candles = aggregate(candles_1min, 240)  # 4h bars
    if len(candles) < 100:
        return None
    closes = [c[4] for c in candles]
    highs = [c[2] for c in candles]
    lows = [c[3] for c in candles]
    e_fast = ema(closes, ema_fast)
    e_slow = ema(closes, ema_slow)
    atr_v = atr(highs, lows, closes, atr_period)
    notional = CAPITAL * LEVERAGE

    trades = []
    pos = 0
    entry_price = 0.0
    entry_idx = 0
    sl_level = 0.0

    for i in range(max(ema_slow, atr_period) + 5, len(candles)):
        if pos == 1:
            # Exit
            hit_sl = (lows[i] <= sl_level)
            hit_exit = (closes[i] < e_slow[i])
            if hit_sl or hit_exit:
                exit_price = sl_level if hit_sl else closes[i]
                ret = (exit_price - entry_price) / entry_price
                pnl = notional * ret - FEE_RT * notional
                trades.append({"entry_idx": entry_idx, "exit_idx": i,
                              "side": "L", "pnl": pnl, "reason": "SL" if hit_sl else "EXIT"})
                pos = 0

        if pos == 0:
            # Entry: EMA fast > EMA slow AND ATR rising over last 3 bars
            cond_trend = e_fast[i] > e_slow[i]
            cond_atr_rising = (atr_v[i] > atr_v[i-1] > atr_v[i-2]) if i >= 2 else False
            if cond_trend and cond_atr_rising and atr_v[i] > 0:
                pos = 1
                entry_price = closes[i]
                entry_idx = i
                sl_level = entry_price - sl_mult * atr_v[i]

    if pos == 1:
        ret = (closes[-1] - entry_price) / entry_price
        pnl = notional * ret - FEE_RT * notional
        trades.append({"entry_idx": entry_idx, "exit_idx": len(candles)-1,
                      "side": "L", "pnl": pnl, "reason": "END"})

    return stats_from_trades(trades, len(candles))


# ============== STRATEGY 3: CONNORS RSI2 (DAILY) ==============

def sim_connors(candles_1min, sma_long=200, sma_short=5, rsi_period=2, rsi_threshold=10):
    """Long si close<SMA200 & RSI(2)<10, exit quand close>SMA5."""
    candles = aggregate(candles_1min, 1440)  # daily
    if len(candles) < sma_long + 20:
        return None
    closes = [c[4] for c in candles]
    sma200 = sma(closes, sma_long)
    sma5 = sma(closes, sma_short)
    rsi2 = rsi(closes, rsi_period)
    notional = CAPITAL * LEVERAGE

    trades = []
    pos = 0
    entry_price = 0.0
    entry_idx = 0

    for i in range(sma_long + 5, len(candles)):
        if pos == 1:
            # Exit when close > SMA5
            if closes[i] > sma5[i]:
                ret = (closes[i] - entry_price) / entry_price
                pnl = notional * ret - FEE_RT * notional
                trades.append({"entry_idx": entry_idx, "exit_idx": i,
                              "side": "L", "pnl": pnl, "reason": "EXIT"})
                pos = 0

        if pos == 0:
            # Entry : close<SMA200 AND RSI2<threshold
            if closes[i] < sma200[i] and rsi2[i] < rsi_threshold:
                pos = 1
                entry_price = closes[i]
                entry_idx = i

    if pos == 1:
        ret = (closes[-1] - entry_price) / entry_price
        pnl = notional * ret - FEE_RT * notional
        trades.append({"entry_idx": entry_idx, "exit_idx": len(candles)-1,
                      "side": "L", "pnl": pnl, "reason": "END"})

    return stats_from_trades(trades, len(candles))


# ============== MAIN ==============

STRATEGIES = {
    "donchian_20_10": lambda c: sim_donchian(c, 20, 10),
    "donchian_55_20": lambda c: sim_donchian(c, 55, 20),
    "trend_ema_4h":   lambda c: sim_trend_ema(c, 20, 50),
    "connors_rsi2":   lambda c: sim_connors(c, 200, 5, 2, 10),
}


def main():
    print(f"=== REDDIT STRATEGIES BACKTEST + WALK-FORWARD ===")
    print(f"Cap=${CAPITAL} lev={LEVERAGE}x fee_rt={FEE_RT*100}%")
    print(f"Pairs: {PAIRS}\n")

    all_results = {}
    for win_name, win_dates in WINDOWS.items():
        print(f"=== {win_name} {win_dates if win_dates else '(current 30j)'} ===")
        all_results[win_name] = []
        for pair in PAIRS:
            if win_dates is None:
                d = fetch_binance_30d(pair)
            else:
                start_ms = to_ms(win_dates[0]); end_ms = to_ms(win_dates[1])
                d = fetch_binance_range(pair, start_ms, end_ms)
            if len(d) < 12000:
                continue
            for strat_name, strat_fn in STRATEGIES.items():
                try:
                    r = strat_fn(d)
                except Exception as e:
                    print(f"    err {pair} {strat_name}: {e}")
                    continue
                if r is None: continue
                r["pair"] = pair.replace("USDT", "")
                r["strategy"] = strat_name
                all_results[win_name].append(r)

        results = sorted(all_results[win_name], key=lambda x: -x["sharpe"])
        n_pos = sum(1 for r in results if r["pnl_total"] > 0)
        print(f"  → {n_pos}/{len(results)} combos positifs. Top 10 Sharpe :")
        print(f"  {'pair':6}{'strategy':18}{'trades':8}{'win%':7}{'PnL$':9}{'PnL%':8}{'MaxDD%':8}{'Sharpe':8}")
        for r in results[:10]:
            print(f"  {r['pair']:6}{r['strategy']:18}{r['trades']:>7}{r['win_rate']:>6.1f}%{r['pnl_total']:+8.2f}{r['pnl_pct']:+7.2f}%{r['max_dd_pct']:+7.2f}%{r['sharpe']:>7}")
        print()

    # Walk-forward
    print(f"=== WALK-FORWARD VALIDATION ===")
    train_combos = {}
    for w in TRAIN_WINDOWS:
        for r in all_results[w]:
            key = (r["pair"], r["strategy"])
            if key not in train_combos:
                train_combos[key] = {"sharpes": [], "pnls": []}
            train_combos[key]["sharpes"].append(r["sharpe"])
            train_combos[key]["pnls"].append(r["pnl_pct"])
    train_ranked = []
    for key, c in train_combos.items():
        if len(c["sharpes"]) < 2: continue
        mean_sh = sum(c["sharpes"]) / 2
        mean_pnl = sum(c["pnls"]) / 2
        train_ranked.append((key, mean_sh, mean_pnl, c["sharpes"], c["pnls"]))
    train_ranked.sort(key=lambda x: -x[1])

    print(f"Top 10 combos sur TRAIN :")
    for key, mean_sh, mean_pnl, sharpes, pnls in train_ranked[:10]:
        print(f"  {key} → mean_Sh={mean_sh:.2f} (W1={sharpes[0]:.2f}, W2={sharpes[1]:.2f}) mean_PnL%={mean_pnl:+.1f}")

    print(f"\nVALIDATION OUT-OF-SAMPLE (top 8) :")
    for key, mean_sh_train, mean_pnl_train, _, _ in train_ranked[:8]:
        valid_data = []
        for w in VALID_WINDOWS:
            for r in all_results[w]:
                if (r["pair"], r["strategy"]) == key:
                    valid_data.append((w, r["sharpe"], r["pnl_pct"]))
        if not valid_data:
            print(f"  {key} → no valid data")
            continue
        mean_sh_v = sum(x[1] for x in valid_data) / len(valid_data)
        mean_pnl_v = sum(x[2] for x in valid_data) / len(valid_data)
        verdict = "✅ OK" if mean_sh_v > 1.0 else ("⚠️ WEAK" if mean_sh_v > 0 else "❌ BROKEN")
        print(f"  {key}")
        print(f"    TRAIN Sharpe={mean_sh_train:+.2f} PnL%={mean_pnl_train:+.1f}")
        print(f"    VALID Sharpe={mean_sh_v:+.2f} PnL%={mean_pnl_v:+.1f}  {verdict}")
        for w, sh, pn in valid_data:
            print(f"      {w}: Sh={sh:.2f} PnL%={pn:.1f}")

    Path("reddit_strats_results.json").write_text(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()

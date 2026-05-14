#!/usr/bin/env python3
"""Donchian Channel backtest étendu — 3 ans daily, BTC/ETH/SOL.

Test multiple variantes (20/10, 55/20, etc) avec long+short, stop ATR.
Walk-forward strict : 2023+H1-2024 train (18 mois) → H2-2024+2025 valid (18 mois).
"""
import json, time, urllib.request, datetime, math
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)

PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

# Variantes à tester
DONCHIAN_PARAMS = [
    (10, 5), (20, 10), (30, 15), (55, 20), (100, 40),
]
ATR_STOP_MULTS = [1.5, 2.0, 3.0]
ENABLE_SHORT = [True, False]

CAPITAL = 25.0
LEVERAGE = 3
FEE_RT = 0.001  # taker
ATR_PERIOD = 20

# Periods (daily candles)
START_DATE = "2023-01-01"
END_DATE = "2025-12-31"

# Walk-forward split (date)
SPLIT_DATE = "2024-07-01"  # 18 mo train / 18 mo valid


def to_ms(date_str):
    return int(datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(
        tzinfo=datetime.timezone.utc).timestamp() * 1000)


def fetch_daily(pair, start_ms, end_ms):
    """Fetch daily OHLCV from Binance."""
    cache = CACHE_DIR / f"binance_{pair}_1d_{start_ms}_{end_ms}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    out = []
    cursor = start_ms
    while cursor < end_ms:
        url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=1d&startTime={cursor}&endTime={end_ms}&limit=1000"
        try:
            d = json.loads(urllib.request.urlopen(url, timeout=20).read())
        except Exception as e:
            print(f"  fetch err {pair}: {e}"); time.sleep(2); continue
        if not d: break
        out.extend([[int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in d])
        last_close = int(d[-1][6])
        if last_close <= cursor: break
        cursor = last_close + 1
        if len(d) < 1000: break
        time.sleep(0.10)
    cache.write_text(json.dumps(out))
    return out


def atr(highs, lows, closes, period=20):
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


def donchian_channel(highs, lows, period):
    n = len(highs)
    hi = [0.0] * n; lo = [0.0] * n
    for i in range(n):
        start = max(0, i - period + 1)
        sub_h = highs[start:i+1]
        sub_l = lows[start:i+1]
        hi[i] = max(sub_h)
        lo[i] = min(sub_l)
    return hi, lo


def simulate(candles, n_entry, n_exit, atr_mult, allow_short):
    if len(candles) < max(n_entry, ATR_PERIOD) + 10:
        return None
    closes = [c[4] for c in candles]
    highs = [c[2] for c in candles]
    lows = [c[3] for c in candles]
    times = [c[0] for c in candles]
    hi_n, lo_n = donchian_channel(highs, lows, n_entry)
    hi_x, lo_x = donchian_channel(highs, lows, n_exit)
    atr_v = atr(highs, lows, closes, ATR_PERIOD)
    notional = CAPITAL * LEVERAGE

    trades = []
    pos = 0
    entry_price = 0.0
    entry_idx = 0
    sl_level = 0.0
    last_n_entry_warmup = max(n_entry, ATR_PERIOD)

    for i in range(last_n_entry_warmup + 1, len(candles)):
        if pos == 1:
            hit_sl = (lows[i] <= sl_level)
            hit_exit = (closes[i] < lo_x[i-1])
            if hit_sl or hit_exit:
                exit_price = sl_level if hit_sl else closes[i]
                ret = (exit_price - entry_price) / entry_price
                pnl = notional * ret - FEE_RT * notional
                trades.append({"entry_idx": entry_idx, "exit_idx": i, "side": "L", "pnl": pnl,
                               "entry_t": times[entry_idx], "exit_t": times[i],
                               "reason": "SL" if hit_sl else "EXIT"})
                pos = 0
        elif pos == -1:
            hit_sl = (highs[i] >= sl_level)
            hit_exit = (closes[i] > hi_x[i-1])
            if hit_sl or hit_exit:
                exit_price = sl_level if hit_sl else closes[i]
                ret = (entry_price - exit_price) / entry_price
                pnl = notional * ret - FEE_RT * notional
                trades.append({"entry_idx": entry_idx, "exit_idx": i, "side": "S", "pnl": pnl,
                               "entry_t": times[entry_idx], "exit_t": times[i],
                               "reason": "SL" if hit_sl else "EXIT"})
                pos = 0

        if pos == 0:
            # Entry conditions
            if highs[i] >= hi_n[i-1] and atr_v[i] > 0:
                pos = 1
                entry_price = hi_n[i-1]
                entry_idx = i
                sl_level = entry_price - atr_mult * atr_v[i]
            elif allow_short and lows[i] <= lo_n[i-1] and atr_v[i] > 0:
                pos = -1
                entry_price = lo_n[i-1]
                entry_idx = i
                sl_level = entry_price + atr_mult * atr_v[i]

    # Close remaining
    if pos != 0:
        exit_price = closes[-1]
        if pos == 1:
            ret = (exit_price - entry_price) / entry_price
        else:
            ret = (entry_price - exit_price) / entry_price
        pnl = notional * ret - FEE_RT * notional
        trades.append({"entry_idx": entry_idx, "exit_idx": len(candles)-1,
                       "side": "L" if pos == 1 else "S", "pnl": pnl,
                       "entry_t": times[entry_idx], "exit_t": times[-1],
                       "reason": "END"})
    return trades, candles


def stats(trades, candles):
    n = len(trades)
    if n == 0:
        return {"trades": 0, "pnl_total": 0, "pnl_pct": 0, "sharpe": 0,
                "win_rate": 0, "max_dd_pct": 0, "calmar": 0,
                "n_long": 0, "n_short": 0}
    pnl_total = sum(t["pnl"] for t in trades)
    pnl_pct = pnl_total / CAPITAL * 100
    wins = sum(1 for t in trades if t["pnl"] > 0)
    win_rate = wins / n * 100
    n_long = sum(1 for t in trades if t["side"] == "L")
    n_short = n - n_long

    n_bars = len(candles)
    eq = [CAPITAL] * n_bars
    cum = 0
    for t in trades:
        cum += t["pnl"]
        for j in range(t["exit_idx"], n_bars):
            eq[j] = CAPITAL + cum
    peak = CAPITAL; max_dd = 0
    for e in eq:
        if e > peak: peak = e
        if (peak - e) > max_dd: max_dd = peak - e
    max_dd_pct = max_dd / CAPITAL * 100

    # Daily Sharpe (already daily bars)
    rets = [(eq[i] - eq[i-1]) / eq[i-1] for i in range(1, n_bars) if eq[i-1] > 0]
    if len(rets) >= 2:
        mean_r = sum(rets) / len(rets)
        var = sum((r - mean_r) ** 2 for r in rets) / len(rets)
        std_r = math.sqrt(var)
        sharpe = (mean_r / std_r * math.sqrt(365)) if std_r > 0 else 0
    else:
        sharpe = 0
    calmar = pnl_pct / max_dd_pct if max_dd_pct > 0 else 999

    return {
        "trades": n, "pnl_total": round(pnl_total, 2),
        "pnl_pct": round(pnl_pct, 2), "sharpe": round(sharpe, 2),
        "win_rate": round(win_rate, 1),
        "max_dd_pct": round(max_dd_pct, 2),
        "calmar": round(calmar, 2),
        "n_long": n_long, "n_short": n_short,
    }


def split_train_valid(candles, split_date):
    split_ms = to_ms(split_date)
    train = [c for c in candles if c[0] < split_ms]
    valid = [c for c in candles if c[0] >= split_ms]
    return train, valid


def main():
    print(f"=== DONCHIAN LONG BACKTEST 2023-2025 ===")
    print(f"Pairs: {PAIRS}  Cap=${CAPITAL} lev={LEVERAGE}x fee_rt={FEE_RT*100}%")
    print(f"Variants: {DONCHIAN_PARAMS}  ATR stops: {ATR_STOP_MULTS}  Short: {ENABLE_SHORT}")
    print(f"Period: {START_DATE} → {END_DATE}")
    print(f"Train/valid split: {SPLIT_DATE}\n")

    start_ms = to_ms(START_DATE); end_ms = to_ms(END_DATE)

    full_results = []
    train_results = []
    valid_results = []

    for pair in PAIRS:
        print(f"  fetching {pair} daily...", end="", flush=True)
        d = fetch_daily(pair, start_ms, end_ms)
        print(f" {len(d)} candles ({len(d)/365:.1f}y)")
        if len(d) < 200:
            continue
        train_candles, valid_candles = split_train_valid(d, SPLIT_DATE)
        print(f"    train={len(train_candles)} valid={len(valid_candles)}")
        for n_ent, n_xt in DONCHIAN_PARAMS:
            for atr_m in ATR_STOP_MULTS:
                for short in ENABLE_SHORT:
                    # FULL period
                    res = simulate(d, n_ent, n_xt, atr_m, short)
                    if res:
                        s = stats(*res)
                        s.update({"pair": pair.replace("USDT", ""),
                                  "n_ent": n_ent, "n_xt": n_xt, "atr_m": atr_m, "short": short,
                                  "phase": "FULL"})
                        full_results.append(s)
                    # TRAIN
                    res = simulate(train_candles, n_ent, n_xt, atr_m, short)
                    if res:
                        s = stats(*res)
                        s.update({"pair": pair.replace("USDT", ""),
                                  "n_ent": n_ent, "n_xt": n_xt, "atr_m": atr_m, "short": short,
                                  "phase": "TRAIN"})
                        train_results.append(s)
                    # VALID
                    res = simulate(valid_candles, n_ent, n_xt, atr_m, short)
                    if res:
                        s = stats(*res)
                        s.update({"pair": pair.replace("USDT", ""),
                                  "n_ent": n_ent, "n_xt": n_xt, "atr_m": atr_m, "short": short,
                                  "phase": "VALID"})
                        valid_results.append(s)

    # Print top 15 FULL
    print(f"\n=== TOP 15 FULL PERIOD (3 ans, par Sharpe) ===")
    full_results.sort(key=lambda x: -x["sharpe"])
    print(f"{'pair':6}{'N_ent':6}{'N_xt':6}{'atr':5}{'short':6}{'tr':4}{'L':4}{'S':4}{'win%':6}{'PnL$':10}{'PnL%':9}{'DD%':7}{'Sharpe':8}{'Calmar':7}")
    for r in full_results[:15]:
        print(f"{r['pair']:6}{r['n_ent']:>5}{r['n_xt']:>5}{r['atr_m']:>4}{'Y' if r['short'] else 'N':>5}{r['trades']:>4}{r['n_long']:>4}{r['n_short']:>4}{r['win_rate']:>5.1f}%{r['pnl_total']:+9.2f}{r['pnl_pct']:+7.1f}%{r['max_dd_pct']:>6.1f}%{r['sharpe']:>7}{r['calmar']:>7}")

    # Walk-forward : top 5 train → check valid
    print(f"\n=== WALK-FORWARD : top 8 TRAIN (18 mois) → out-of-sample VALID (18 mois) ===")
    train_results.sort(key=lambda x: -x["sharpe"])
    print(f"  Top 8 by TRAIN Sharpe :")
    for r in train_results[:8]:
        # Find matching valid
        v = next((v for v in valid_results
                  if v["pair"] == r["pair"] and v["n_ent"] == r["n_ent"]
                  and v["n_xt"] == r["n_xt"] and v["atr_m"] == r["atr_m"]
                  and v["short"] == r["short"]), None)
        verdict = "?"
        v_str = "(no valid)"
        if v:
            v_str = f"VALID Sh={v['sharpe']:+.2f} PnL%={v['pnl_pct']:+.1f} DD={v['max_dd_pct']:.1f}% trades={v['trades']}"
            verdict = "✅ OK" if v["sharpe"] > 0.8 else ("⚠️ WEAK" if v["sharpe"] > 0 else "❌ BROKEN")
        print(f"  {r['pair']:6} N={r['n_ent']}/{r['n_xt']} atr={r['atr_m']} short={'Y' if r['short'] else 'N'}")
        print(f"    TRAIN Sh={r['sharpe']:+.2f} PnL%={r['pnl_pct']:+.1f} DD={r['max_dd_pct']:.1f}% trades={r['trades']}")
        print(f"    {v_str}  {verdict}")

    Path("donchian_long_results.json").write_text(json.dumps({
        "full": full_results, "train": train_results, "valid": valid_results
    }, indent=2))


if __name__ == "__main__":
    main()

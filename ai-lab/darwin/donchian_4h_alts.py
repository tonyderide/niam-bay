#!/usr/bin/env python3
"""Donchian backtest étendu — 4h + 1h, 12 paires, walk-forward strict.

Vise à régler les 2 problèmes du daily backtest :
1. Sample size trop petit (8 trades) → 4h donne 50-100 trades par window
2. BTC/ETH/SOL only → tester aussi alts pour diversifier

Pairs: BTC, ETH, SOL, LINK, AVAX, ADA, ATOM, AAVE, INJ, APT, OP, SUI
Timeframes: 4h + 1h
Walk-forward: jan 2023-juin 2024 train / juil 2024-déc 2025 valid
"""
import json, time, urllib.request, datetime, math
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)

PAIRS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT", "AVAXUSDT", "ADAUSDT",
    "ATOMUSDT", "AAVEUSDT", "INJUSDT", "APTUSDT", "OPUSDT", "SUIUSDT",
]

TIMEFRAMES = [
    ("4h", "4h", 240),  # name, binance interval, period_min
    ("1h", "1h", 60),
]

DONCHIAN_PARAMS = [
    (10, 5), (20, 10), (30, 15), (55, 20), (100, 40),
]
ATR_STOP_MULTS = [1.5, 2.0, 3.0]
ENABLE_SHORT = [True, False]

CAPITAL = 25.0
LEVERAGE = 3
FEE_RT = 0.001
ATR_PERIOD = 20

START_DATE = "2023-01-01"
END_DATE = "2025-12-31"
SPLIT_DATE = "2024-07-01"


def to_ms(date_str):
    return int(datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(
        tzinfo=datetime.timezone.utc).timestamp() * 1000)


def fetch_kline(pair, interval, start_ms, end_ms):
    cache = CACHE_DIR / f"binance_{pair}_{interval}_{start_ms}_{end_ms}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    out = []
    cursor = start_ms
    while cursor < end_ms:
        url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval={interval}&startTime={cursor}&endTime={end_ms}&limit=1000"
        try:
            d = json.loads(urllib.request.urlopen(url, timeout=20).read())
        except Exception as e:
            print(f"    fetch err {pair}-{interval}: {e}"); time.sleep(2); continue
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
        s = max(0, i - period + 1)
        hi[i] = max(highs[s:i+1])
        lo[i] = min(lows[s:i+1])
    return hi, lo


def simulate(candles, n_entry, n_exit, atr_mult, allow_short):
    if len(candles) < max(n_entry, ATR_PERIOD) + 10:
        return None
    closes = [c[4] for c in candles]
    highs = [c[2] for c in candles]
    lows = [c[3] for c in candles]
    hi_n, lo_n = donchian_channel(highs, lows, n_entry)
    hi_x, lo_x = donchian_channel(highs, lows, n_exit)
    atr_v = atr(highs, lows, closes, ATR_PERIOD)
    notional = CAPITAL * LEVERAGE

    trades = []
    pos = 0
    entry_price = 0.0; entry_idx = 0; sl_level = 0.0
    warmup = max(n_entry, ATR_PERIOD)

    for i in range(warmup + 1, len(candles)):
        if pos == 1:
            hit_sl = (lows[i] <= sl_level)
            hit_exit = (closes[i] < lo_x[i-1])
            if hit_sl or hit_exit:
                exit_price = sl_level if hit_sl else closes[i]
                ret = (exit_price - entry_price) / entry_price
                pnl = notional * ret - FEE_RT * notional
                trades.append({"entry_idx": entry_idx, "exit_idx": i, "side": "L", "pnl": pnl})
                pos = 0
        elif pos == -1:
            hit_sl = (highs[i] >= sl_level)
            hit_exit = (closes[i] > hi_x[i-1])
            if hit_sl or hit_exit:
                exit_price = sl_level if hit_sl else closes[i]
                ret = (entry_price - exit_price) / entry_price
                pnl = notional * ret - FEE_RT * notional
                trades.append({"entry_idx": entry_idx, "exit_idx": i, "side": "S", "pnl": pnl})
                pos = 0

        if pos == 0:
            if highs[i] >= hi_n[i-1] and atr_v[i] > 0:
                pos = 1; entry_price = hi_n[i-1]; entry_idx = i
                sl_level = entry_price - atr_mult * atr_v[i]
            elif allow_short and lows[i] <= lo_n[i-1] and atr_v[i] > 0:
                pos = -1; entry_price = lo_n[i-1]; entry_idx = i
                sl_level = entry_price + atr_mult * atr_v[i]

    if pos != 0:
        exit_price = closes[-1]
        ret = (exit_price - entry_price) / entry_price if pos == 1 else (entry_price - exit_price) / entry_price
        pnl = notional * ret - FEE_RT * notional
        trades.append({"entry_idx": entry_idx, "exit_idx": len(candles)-1,
                       "side": "L" if pos == 1 else "S", "pnl": pnl})
    return trades, candles


def stats(trades, candles):
    n = len(trades)
    if n == 0:
        return {"trades": 0, "pnl_total": 0, "pnl_pct": 0, "sharpe": 0,
                "win_rate": 0, "max_dd_pct": 0, "n_long": 0, "n_short": 0}
    pnl_total = sum(t["pnl"] for t in trades)
    pnl_pct = pnl_total / CAPITAL * 100
    wins = sum(1 for t in trades if t["pnl"] > 0)
    win_rate = wins / n * 100
    n_long = sum(1 for t in trades if t["side"] == "L")
    n_short = n - n_long

    n_bars = len(candles)
    eq = [CAPITAL] * n_bars; cum = 0
    for t in trades:
        cum += t["pnl"]
        for j in range(t["exit_idx"], n_bars):
            eq[j] = CAPITAL + cum
    peak = CAPITAL; max_dd = 0
    for e in eq:
        if e > peak: peak = e
        if (peak - e) > max_dd: max_dd = peak - e
    max_dd_pct = max_dd / CAPITAL * 100

    # Sharpe: sample equity at daily resolution
    bars_per_day = max(1, int(n_bars / 540))  # ~18 months / 540 days
    daily_eq = [eq[d] for d in range(0, n_bars, bars_per_day)]
    if len(daily_eq) < 5:
        sharpe = 0
    else:
        rets = [(daily_eq[i] - daily_eq[i-1]) / daily_eq[i-1] for i in range(1, len(daily_eq)) if daily_eq[i-1] > 0]
        if len(rets) >= 2:
            mean_r = sum(rets) / len(rets)
            var = sum((r - mean_r) ** 2 for r in rets) / len(rets)
            std_r = math.sqrt(var)
            sharpe = (mean_r / std_r * math.sqrt(365)) if std_r > 0 else 0
        else:
            sharpe = 0
    return {
        "trades": n, "pnl_total": round(pnl_total, 2),
        "pnl_pct": round(pnl_pct, 2), "sharpe": round(sharpe, 2),
        "win_rate": round(win_rate, 1),
        "max_dd_pct": round(max_dd_pct, 2),
        "n_long": n_long, "n_short": n_short,
    }


def main():
    print(f"=== DONCHIAN 4H + 1H × 12 ALTS — WALK-FORWARD ===")
    print(f"Pairs: {len(PAIRS)} | TFs: {[t[0] for t in TIMEFRAMES]} | params: {DONCHIAN_PARAMS}")
    print(f"Period: {START_DATE} → {END_DATE} | Split: {SPLIT_DATE}\n")

    start_ms = to_ms(START_DATE); end_ms = to_ms(END_DATE)
    split_ms = to_ms(SPLIT_DATE)

    train_results = []
    valid_results = []
    full_results = []

    for tf_name, tf_interval, tf_min in TIMEFRAMES:
        print(f"\n=== TIMEFRAME {tf_name} ===")
        for pair in PAIRS:
            print(f"  fetching {pair}-{tf_name}...", end="", flush=True)
            d = fetch_kline(pair, tf_interval, start_ms, end_ms)
            print(f" {len(d)} candles ({len(d)*tf_min/1440:.1f}j)")
            if len(d) < 200:
                continue
            train_c = [c for c in d if c[0] < split_ms]
            valid_c = [c for c in d if c[0] >= split_ms]
            for n_e, n_x in DONCHIAN_PARAMS:
                for atr_m in ATR_STOP_MULTS:
                    for short in ENABLE_SHORT:
                        for label, candles, target in [("FULL", d, full_results),
                                                       ("TRAIN", train_c, train_results),
                                                       ("VALID", valid_c, valid_results)]:
                            res = simulate(candles, n_e, n_x, atr_m, short)
                            if res:
                                s = stats(*res)
                                s.update({"pair": pair.replace("USDT", ""),
                                          "tf": tf_name, "n_e": n_e, "n_x": n_x,
                                          "atr_m": atr_m, "short": short, "phase": label})
                                target.append(s)

    print(f"\n=== TOP 20 par phase FULL (3 ans) — Sharpe ===")
    full_results.sort(key=lambda x: -x["sharpe"])
    print(f"{'pair':6}{'tf':4}{'N':8}{'atr':5}{'sh':4}{'tr':5}{'L':4}{'S':4}{'win%':6}{'PnL$':10}{'PnL%':9}{'DD%':7}{'Sharpe':8}")
    for r in full_results[:20]:
        print(f"{r['pair']:6}{r['tf']:4}{r['n_e']}/{r['n_x']:<5}{r['atr_m']:>4}{'Y' if r['short'] else 'N':>3}{r['trades']:>5}{r['n_long']:>4}{r['n_short']:>4}{r['win_rate']:>5.1f}%{r['pnl_total']:+9.2f}{r['pnl_pct']:+7.1f}%{r['max_dd_pct']:>6.1f}%{r['sharpe']:>7}")

    # WALK-FORWARD
    print(f"\n=== WALK-FORWARD : top 15 TRAIN → VALID out-of-sample ===")
    train_results.sort(key=lambda x: -x["sharpe"])

    candidates_ok = []
    for tr in train_results[:30]:
        v = next((v for v in valid_results
                  if v["pair"] == tr["pair"] and v["tf"] == tr["tf"]
                  and v["n_e"] == tr["n_e"] and v["n_x"] == tr["n_x"]
                  and v["atr_m"] == tr["atr_m"] and v["short"] == tr["short"]), None)
        if not v: continue
        if v["sharpe"] > 0.7 and v["max_dd_pct"] < 60:
            candidates_ok.append((tr, v))

    print(f"  CANDIDATS OK (Sharpe valid > 0.7 ET DD < 60%) : {len(candidates_ok)}")
    print(f"  {'pair':6}{'tf':4}{'N':8}{'atr':5}{'sh':4}{'tr.Sh':7}{'tr.PnL':9}{'tr.DD':8}{'va.Sh':7}{'va.PnL':9}{'va.DD':8}{'va.tr':6}")
    for tr, v in sorted(candidates_ok, key=lambda x: -x[1]["sharpe"])[:25]:
        print(f"  {tr['pair']:6}{tr['tf']:4}{tr['n_e']}/{tr['n_x']:<5}{tr['atr_m']:>4}{'Y' if tr['short'] else 'N':>3}{tr['sharpe']:>6.2f}{tr['pnl_pct']:+8.1f}%{tr['max_dd_pct']:>7.1f}%{v['sharpe']:>6.2f}{v['pnl_pct']:+8.1f}%{v['max_dd_pct']:>7.1f}%{v['trades']:>5}")

    Path("donchian_4h_alts_results.json").write_text(json.dumps({
        "full": full_results, "train": train_results, "valid": valid_results,
        "candidates_ok": [{"train": tr, "valid": v} for tr, v in candidates_ok]
    }, indent=2))


if __name__ == "__main__":
    main()

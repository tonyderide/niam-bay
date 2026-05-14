#!/usr/bin/env python3
"""Mean Reversion + ATR Filter Backtest sur BTC/ETH.

Strategie (per Fischer 2019 SSRN + Kris Longmore 2024 blog) :
- Timeframe : 1H (aggregé du 1min)
- z-score = (close - MA_N) / std_N sur N bars
- Entry LONG  si z < -z_threshold  AND  atr_pct_rank in [atr_min, atr_max]
- Entry SHORT si z > +z_threshold  AND  atr_pct_rank in [atr_min, atr_max]
- Exit       quand z retourne à 0 OU signal opposé OU stop temps 48h
- Filtre régime : ATR% percentile rank 30-70 (évite trending fort et flat-line mort)

Tests sur 4 windows historiques pour valider robustesse.
"""
import json, time, urllib.request, datetime, math
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)

PAIRS = ["BTCUSDT", "ETHUSDT"]

WINDOWS = {
    "W0_current_30j":  None,
    "W1_2024_bull":    ("2024-03-01", "2024-04-30"),
    "W2_2024_transit": ("2024-10-01", "2024-12-31"),
    "W3_2025_chop":    ("2025-02-01", "2025-03-31"),
}

# Grid search params
Z_THRESHOLDS = [1.5, 2.0, 2.5]
MA_PERIODS = [20, 50]
ATR_RANGES = [(30, 70), (20, 80), (40, 60)]  # percentile rank ranges

CAPITAL = 40.0
LEVERAGE = 5
FEE_RT = 0.001  # 0.05% taker x 2
MAX_HOLD_HOURS = 48


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
    if p.exists():
        return json.loads(p.read_text())
    return []


def aggregate_1h(candles):
    out = []
    for i in range(0, len(candles) - 60, 60):
        chunk = candles[i:i+60]
        if not chunk: continue
        out.append([chunk[0][0], chunk[0][1],
                    max(c[2] for c in chunk),
                    min(c[3] for c in chunk),
                    chunk[-1][4],
                    sum(c[5] for c in chunk)])
    return out


def rolling_mean_std(values, window):
    """Returns (mean[], std[]) — std is 0 before window."""
    n = len(values)
    means = [0.0] * n
    stds = [0.0] * n
    csum = 0.0
    csum2 = 0.0
    for i in range(n):
        csum += values[i]
        csum2 += values[i] * values[i]
        if i >= window:
            csum -= values[i - window]
            csum2 -= values[i - window] * values[i - window]
        if i >= window - 1:
            mean = csum / window
            var = csum2 / window - mean * mean
            means[i] = mean
            stds[i] = math.sqrt(max(0, var))
    return means, stds


def atr_pct_series(highs, lows, closes, period=14):
    n = len(closes)
    if n < period + 1:
        return [0.0] * n
    trs = [highs[0] - lows[0]]
    for i in range(1, n):
        tr = max(highs[i] - lows[i],
                 abs(highs[i] - closes[i-1]),
                 abs(lows[i] - closes[i-1]))
        trs.append(tr)
    atr = [0.0] * period
    a = sum(trs[:period]) / period
    atr.append(a)
    for i in range(period + 1, n):
        a = (a * (period - 1) + trs[i]) / period
        atr.append(a)
    return [(atr[i] / closes[i] * 100) if closes[i] > 0 else 0.0 for i in range(n)]


def percentile_rank(values, window):
    """For each i, return percentile rank of values[i] within values[max(0,i-window):i+1].
    Result in [0, 100]."""
    n = len(values)
    out = [50.0] * n
    for i in range(n):
        lo = max(0, i - window)
        sub = values[lo:i+1]
        below = sum(1 for v in sub if v < values[i])
        out[i] = below / len(sub) * 100 if sub else 50.0
    return out


def simulate(candles_1min, z_threshold, ma_period, atr_min, atr_max):
    if len(candles_1min) < 12000:
        return None
    candles_1h = aggregate_1h(candles_1min)
    if len(candles_1h) < max(ma_period, 200) + 20:
        return None
    closes = [c[4] for c in candles_1h]
    highs = [c[2] for c in candles_1h]
    lows = [c[3] for c in candles_1h]

    means, stds = rolling_mean_std(closes, ma_period)
    atr_pct = atr_pct_series(highs, lows, closes, 14)
    atr_rank = percentile_rank(atr_pct, 200)

    notional = CAPITAL * LEVERAGE
    trades = []  # list of (entry_time_idx, exit_time_idx, side, pnl)
    pos = 0
    entry_price = 0.0
    entry_idx = 0

    for i in range(max(ma_period, 215), len(closes)):
        if stds[i] <= 0:
            continue
        z = (closes[i] - means[i]) / stds[i]
        regime_ok = atr_min <= atr_rank[i] <= atr_max

        if pos == 1:  # long open
            # Exit: z >= 0 (return to mean) OR z > +z_threshold (reversal) OR max hold
            if z >= 0 or z > z_threshold or (i - entry_idx) >= MAX_HOLD_HOURS:
                exit_price = closes[i]
                ret = (exit_price - entry_price) / entry_price
                pnl = notional * ret - FEE_RT * notional
                trades.append((entry_idx, i, "LONG", pnl))
                pos = 0
        elif pos == -1:  # short open
            if z <= 0 or z < -z_threshold or (i - entry_idx) >= MAX_HOLD_HOURS:
                exit_price = closes[i]
                ret = (entry_price - exit_price) / entry_price
                pnl = notional * ret - FEE_RT * notional
                trades.append((entry_idx, i, "SHORT", pnl))
                pos = 0

        # New entries (only if flat and regime OK)
        if pos == 0 and regime_ok:
            if z < -z_threshold:
                pos = 1
                entry_price = closes[i]
                entry_idx = i
            elif z > z_threshold:
                pos = -1
                entry_price = closes[i]
                entry_idx = i

    # Close any open position at last bar
    if pos != 0:
        exit_price = closes[-1]
        if pos == 1:
            ret = (exit_price - entry_price) / entry_price
        else:
            ret = (entry_price - exit_price) / entry_price
        pnl = notional * ret - FEE_RT * notional
        trades.append((entry_idx, len(closes) - 1, "LONG" if pos == 1 else "SHORT", pnl))

    # Stats
    n = len(trades)
    if n == 0:
        return {"trades": 0, "pnl_total": 0, "pnl_pct": 0, "sharpe": 0,
                "calmar": 0, "max_dd": 0, "max_dd_pct": 0, "win_rate": 0,
                "avg_win": 0, "avg_loss": 0, "hours_data": len(closes)}
    pnl_total = sum(t[3] for t in trades)
    pnl_pct = pnl_total / CAPITAL * 100
    wins = [t[3] for t in trades if t[3] > 0]
    losses = [t[3] for t in trades if t[3] <= 0]
    win_rate = len(wins) / n * 100
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0

    # Equity curve hour by hour
    eq_curve = [CAPITAL] * len(closes)
    cum_pnl = 0
    for t in trades:
        cum_pnl += t[3]
        for j in range(t[1], len(closes)):
            eq_curve[j] = CAPITAL + cum_pnl
    peak = CAPITAL
    max_dd = 0.0
    for eq in eq_curve:
        if eq > peak: peak = eq
        if (peak - eq) > max_dd: max_dd = peak - eq
    max_dd_pct = max_dd / CAPITAL * 100

    # Sharpe : compute daily returns from equity
    daily_eq = []
    for d in range(0, len(eq_curve), 24):
        if d + 24 <= len(eq_curve):
            daily_eq.append(eq_curve[d + 23])
    if len(daily_eq) < 5:
        sharpe = 0
    else:
        daily_returns = [(daily_eq[i] - daily_eq[i-1]) / daily_eq[i-1] for i in range(1, len(daily_eq))]
        if len(daily_returns) < 2:
            sharpe = 0
        else:
            mean_r = sum(daily_returns) / len(daily_returns)
            var = sum((r - mean_r) ** 2 for r in daily_returns) / len(daily_returns)
            std_r = math.sqrt(var)
            sharpe = (mean_r / std_r * math.sqrt(365)) if std_r > 0 else 0

    calmar = pnl_pct / max_dd_pct if max_dd_pct > 0 else 999

    return {
        "trades": n,
        "pnl_total": round(pnl_total, 3),
        "pnl_pct": round(pnl_pct, 2),
        "sharpe": round(sharpe, 2),
        "calmar": round(calmar, 2),
        "max_dd": round(max_dd, 2),
        "max_dd_pct": round(max_dd_pct, 2),
        "win_rate": round(win_rate, 1),
        "avg_win": round(avg_win, 3),
        "avg_loss": round(avg_loss, 3),
        "hours_data": len(closes),
    }


def main():
    print(f"Mean Reversion + ATR filter sweep")
    print(f"Pairs: {PAIRS}  Capital=${CAPITAL} lev={LEVERAGE}x fee_rt={FEE_RT*100}%")
    print(f"Grid: z={Z_THRESHOLDS} MA={MA_PERIODS} atr_ranges={ATR_RANGES}")
    print()

    all_results = {}

    for win_name, win_dates in WINDOWS.items():
        print(f"=== {win_name} {win_dates if win_dates else '(current 30j)'} ===")
        all_results[win_name] = []
        for pair in PAIRS:
            if win_dates is None:
                d = fetch_binance_30d(pair)
            else:
                start_ms = to_ms(win_dates[0])
                end_ms = to_ms(win_dates[1])
                print(f"  fetching {pair}...", end="", flush=True)
                d = fetch_binance_range(pair, start_ms, end_ms)
                print(f" {len(d)} candles")
            if len(d) < 12000:
                print(f"  SKIP {pair}: not enough data ({len(d)})")
                continue
            for z in Z_THRESHOLDS:
                for ma in MA_PERIODS:
                    for atr_min, atr_max in ATR_RANGES:
                        r = simulate(d, z, ma, atr_min, atr_max)
                        if r is None: continue
                        r["pair"] = pair.replace("USDT", "")
                        r["z"] = z; r["ma"] = ma
                        r["atr_min"] = atr_min; r["atr_max"] = atr_max
                        all_results[win_name].append(r)

        # Print top results for this window
        results = all_results[win_name]
        results.sort(key=lambda x: -x["sharpe"])  # rank by Sharpe (filter robustness)
        print(f"  Top 8 by Sharpe :")
        print(f"  {'pair':6}{'z':5}{'MA':4}{'atr':8}{'trades':8}{'win%':7}{'PnL$':9}{'PnL%':8}{'MaxDD%':8}{'Sharpe':8}{'Calmar':8}")
        for r in results[:8]:
            print(f"  {r['pair']:6}{r['z']:>4}{r['ma']:>4} {r['atr_min']}-{r['atr_max']:<3}{r['trades']:>7}{r['win_rate']:>6.1f}%{r['pnl_total']:+8.2f}{r['pnl_pct']:+7.2f}%{r['max_dd_pct']:+7.2f}%{r['sharpe']:>7}{r['calmar']:>7}")
        print()

    # Cross-window robustness check for "consensus best" param set
    print(f"=== ROBUSTESSE : meilleurs paramètres cross-window ===")
    # For each combo (pair, z, ma, atr), compute mean Sharpe across windows
    combos = {}
    for win_name, results in all_results.items():
        for r in results:
            key = (r["pair"], r["z"], r["ma"], r["atr_min"], r["atr_max"])
            if key not in combos:
                combos[key] = {"sharpes": [], "pnls": [], "dds": [], "n": 0}
            combos[key]["sharpes"].append(r["sharpe"])
            combos[key]["pnls"].append(r["pnl_pct"])
            combos[key]["dds"].append(r["max_dd_pct"])
            combos[key]["n"] += 1

    # Only consider combos tested on >= 3 windows
    robust = []
    for key, c in combos.items():
        if c["n"] < 3: continue
        mean_sharpe = sum(c["sharpes"]) / c["n"]
        min_sharpe = min(c["sharpes"])
        mean_pnl = sum(c["pnls"]) / c["n"]
        max_dd = max(c["dds"])
        robust.append({"key": key, "mean_sharpe": mean_sharpe, "min_sharpe": min_sharpe,
                       "mean_pnl": mean_pnl, "max_dd_worst": max_dd})

    # Best by min_sharpe (worst-case Sharpe across windows)
    robust.sort(key=lambda x: -x["min_sharpe"])
    print(f"{'pair':6}{'z':5}{'MA':4}{'atr':8}{'mean_Sh':10}{'min_Sh':10}{'mean_PnL%':12}{'worst_DD%':10}")
    for r in robust[:15]:
        p, z, ma, am, ax = r["key"]
        print(f"{p:6}{z:>4}{ma:>4} {am}-{ax:<3}{r['mean_sharpe']:>9.2f}{r['min_sharpe']:>9.2f}{r['mean_pnl']:>+11.2f}{r['max_dd_worst']:>+9.2f}")

    Path("meanrev_atr_results.json").write_text(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()

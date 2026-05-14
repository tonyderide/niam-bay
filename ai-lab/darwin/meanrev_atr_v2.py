#!/usr/bin/env python3
"""Mean Reversion + ATR v2 — TOUS amendements traders appliqués.

Changes vs v1 :
1. Cap $25 (vs $40)
2. Lev 3x (vs 5x)
3. Hold max 24h (vs 48h)
4. Fees maker 0.04% RT (vs taker 0.10%) - assume post-only entry possible
5. ATR lookback 720h (vs 200h) - capture régimes mensuels
6. Stop loss hard -3% prix (=-9% capital strat à lev 3x)
7. Funding cost modélisé : -0.03%/jour si LONG, +0.03%/jour si SHORT
8. Walk-forward validation : optimise sur W1+W2, valide out-of-sample W3+W0 SANS re-tuning
9. ETH only (top combo précédent)
"""
import json, time, urllib.request, datetime, math
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "data_cache"

PAIRS = ["ETHUSDT", "BTCUSDT"]  # ETH primary, BTC secondaire pour comparaison

WINDOWS = {
    "W0_current_30j":  None,
    "W1_2024_bull":    ("2024-03-01", "2024-04-30"),
    "W2_2024_transit": ("2024-10-01", "2024-12-31"),
    "W3_2025_chop":    ("2025-02-01", "2025-03-31"),
}
TRAIN_WINDOWS = ["W1_2024_bull", "W2_2024_transit"]
VALID_WINDOWS = ["W0_current_30j", "W3_2025_chop"]

# Grid search params (réduit vs v1 pour limiter overfit)
Z_THRESHOLDS = [2.0, 2.5]
MA_PERIODS = [50]  # MA=20 trop court selon Quant
ATR_RANGES = [(40, 60), (30, 70)]  # 2 ranges seulement

# AMENDMENTS
CAPITAL = 25.0          # was 40
LEVERAGE = 3            # was 5
FEE_RT = 0.0004         # was 0.001 (maker post-only)
MAX_HOLD_HOURS = 24     # was 48
STOP_LOSS_PCT = 0.03    # NEW: -3% from entry price
ATR_LOOKBACK = 720      # was 200 (30j vs 8j)
FUNDING_DAILY = 0.0003  # 0.03%/jour (3x 0.01%/8h)


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
    n = len(values)
    means = [0.0] * n; stds = [0.0] * n
    csum = 0.0; csum2 = 0.0
    for i in range(n):
        csum += values[i]; csum2 += values[i] * values[i]
        if i >= window:
            csum -= values[i - window]; csum2 -= values[i - window] * values[i - window]
        if i >= window - 1:
            mean = csum / window
            var = csum2 / window - mean * mean
            means[i] = mean; stds[i] = math.sqrt(max(0, var))
    return means, stds


def atr_pct_series(highs, lows, closes, period=14):
    n = len(closes)
    if n < period + 1: return [0.0] * n
    trs = [highs[0] - lows[0]]
    for i in range(1, n):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        trs.append(tr)
    atr = [0.0] * period
    a = sum(trs[:period]) / period
    atr.append(a)
    for i in range(period + 1, n):
        a = (a * (period - 1) + trs[i]) / period
        atr.append(a)
    return [(atr[i] / closes[i] * 100) if closes[i] > 0 else 0.0 for i in range(n)]


def percentile_rank(values, window):
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
    min_warmup = max(ma_period, ATR_LOOKBACK)
    if len(candles_1h) < min_warmup + 50:
        return None
    closes = [c[4] for c in candles_1h]
    highs = [c[2] for c in candles_1h]
    lows = [c[3] for c in candles_1h]

    means, stds = rolling_mean_std(closes, ma_period)
    atr_pct = atr_pct_series(highs, lows, closes, 14)
    atr_rank = percentile_rank(atr_pct, ATR_LOOKBACK)

    notional = CAPITAL * LEVERAGE
    trades = []
    pos = 0
    entry_price = 0.0
    entry_idx = 0

    for i in range(min_warmup + 5, len(closes)):
        if stds[i] <= 0: continue
        z = (closes[i] - means[i]) / stds[i]
        regime_ok = atr_min <= atr_rank[i] <= atr_max
        price = closes[i]

        if pos != 0:
            hold_hours = i - entry_idx
            # Stop loss hard (AMENDMENT 6)
            if pos == 1:
                sl_price = entry_price * (1 - STOP_LOSS_PCT)
                hit_sl = (lows[i] <= sl_price)
            else:
                sl_price = entry_price * (1 + STOP_LOSS_PCT)
                hit_sl = (highs[i] >= sl_price)
            # Exit conditions
            time_exit = (hold_hours >= MAX_HOLD_HOURS)
            if pos == 1:
                signal_exit = (z >= 0 or z > z_threshold)
            else:
                signal_exit = (z <= 0 or z < -z_threshold)

            if hit_sl or time_exit or signal_exit:
                if hit_sl:
                    exit_price = sl_price  # assume SL hits at SL price
                else:
                    exit_price = price
                if pos == 1:
                    ret = (exit_price - entry_price) / entry_price
                else:
                    ret = (entry_price - exit_price) / entry_price
                # Funding: pay funding pendant la duration (AMENDMENT 7)
                hours_held = i - entry_idx
                funding_cost = FUNDING_DAILY * (hours_held / 24.0) * notional
                # Long bias = paye funding ; short bias = reçoit. Mais conservatif on assume coût moyen.
                if pos == 1:
                    funding_impact = -funding_cost  # long paye
                else:
                    funding_impact = +funding_cost  # short reçoit
                pnl = notional * ret - FEE_RT * notional + funding_impact
                trades.append((entry_idx, i, "LONG" if pos == 1 else "SHORT",
                              pnl, "SL" if hit_sl else ("TIME" if time_exit else "SIGNAL")))
                pos = 0

        if pos == 0 and regime_ok:
            if z < -z_threshold:
                pos = 1; entry_price = closes[i]; entry_idx = i
            elif z > z_threshold:
                pos = -1; entry_price = closes[i]; entry_idx = i

    # Close at last bar
    if pos != 0:
        exit_price = closes[-1]
        if pos == 1:
            ret = (exit_price - entry_price) / entry_price
        else:
            ret = (entry_price - exit_price) / entry_price
        hours_held = len(closes) - 1 - entry_idx
        funding_cost = FUNDING_DAILY * (hours_held / 24.0) * notional
        funding_impact = -funding_cost if pos == 1 else +funding_cost
        pnl = notional * ret - FEE_RT * notional + funding_impact
        trades.append((entry_idx, len(closes) - 1, "LONG" if pos == 1 else "SHORT", pnl, "END"))

    n = len(trades)
    if n == 0:
        return {"trades": 0, "pnl_total": 0, "pnl_pct": 0, "sharpe": 0,
                "calmar": 0, "max_dd_pct": 0, "win_rate": 0, "n_sl": 0}
    pnl_total = sum(t[3] for t in trades)
    pnl_pct = pnl_total / CAPITAL * 100
    wins = [t[3] for t in trades if t[3] > 0]
    win_rate = len(wins) / n * 100
    n_sl = sum(1 for t in trades if t[4] == "SL")
    n_time = sum(1 for t in trades if t[4] == "TIME")

    eq_curve = [CAPITAL] * len(closes)
    cum_pnl = 0
    for t in trades:
        cum_pnl += t[3]
        for j in range(t[1], len(closes)):
            eq_curve[j] = CAPITAL + cum_pnl
    peak = CAPITAL; max_dd = 0
    for eq in eq_curve:
        if eq > peak: peak = eq
        if (peak - eq) > max_dd: max_dd = peak - eq
    max_dd_pct = max_dd / CAPITAL * 100

    daily_eq = [eq_curve[d + 23] for d in range(0, len(eq_curve) - 23, 24)]
    if len(daily_eq) < 5:
        sharpe = 0
    else:
        daily_returns = [(daily_eq[i] - daily_eq[i-1]) / daily_eq[i-1] for i in range(1, len(daily_eq))]
        if len(daily_returns) >= 2:
            mean_r = sum(daily_returns) / len(daily_returns)
            var = sum((r - mean_r) ** 2 for r in daily_returns) / len(daily_returns)
            std_r = math.sqrt(var)
            sharpe = (mean_r / std_r * math.sqrt(365)) if std_r > 0 else 0
        else:
            sharpe = 0

    calmar = pnl_pct / max_dd_pct if max_dd_pct > 0 else 999

    return {
        "trades": n, "pnl_total": round(pnl_total, 3),
        "pnl_pct": round(pnl_pct, 2), "sharpe": round(sharpe, 2),
        "calmar": round(calmar, 2), "max_dd_pct": round(max_dd_pct, 2),
        "win_rate": round(win_rate, 1), "n_sl": n_sl, "n_time": n_time,
    }


def main():
    print(f"=== MEAN REV ATR v2 — AMENDMENTS TRADERS ===")
    print(f"Cap=${CAPITAL} lev={LEVERAGE}x fee_rt={FEE_RT*100}% (maker post-only)")
    print(f"hold_max={MAX_HOLD_HOURS}h SL={STOP_LOSS_PCT*100}% atr_lookback={ATR_LOOKBACK}h funding={FUNDING_DAILY*100}%/jour")
    print(f"Train windows: {TRAIN_WINDOWS}  / Validation hold-out: {VALID_WINDOWS}\n")

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
                print(f"  SKIP {pair}")
                continue
            for z in Z_THRESHOLDS:
                for ma in MA_PERIODS:
                    for atr_min, atr_max in ATR_RANGES:
                        r = simulate(d, z, ma, atr_min, atr_max)
                        if r is None: continue
                        r["pair"] = pair.replace("USDT", ""); r["z"] = z; r["ma"] = ma
                        r["atr_min"] = atr_min; r["atr_max"] = atr_max
                        all_results[win_name].append(r)
        results = all_results[win_name]
        results.sort(key=lambda x: -x["sharpe"])
        print(f"  All combos:")
        print(f"  {'pair':6}{'z':5}{'MA':4}{'atr':8}{'trades':8}{'win%':7}{'PnL$':9}{'PnL%':8}{'MaxDD%':8}{'Sharpe':8}{'SLs':5}")
        for r in results:
            print(f"  {r['pair']:6}{r['z']:>4}{r['ma']:>4} {r['atr_min']}-{r['atr_max']:<3}{r['trades']:>7}{r['win_rate']:>6.1f}%{r['pnl_total']:+8.2f}{r['pnl_pct']:+7.2f}%{r['max_dd_pct']:+7.2f}%{r['sharpe']:>7}{r['n_sl']:>4}")
        print()

    # WALK-FORWARD : pick top combo on TRAIN windows, evaluate OUT-OF-SAMPLE on VALID windows
    print(f"=== WALK-FORWARD VALIDATION ===")
    print(f"Train (optimize): {TRAIN_WINDOWS}")
    print(f"Validate (out-of-sample): {VALID_WINDOWS}\n")

    train_combos = {}
    for w in TRAIN_WINDOWS:
        for r in all_results[w]:
            key = (r["pair"], r["z"], r["ma"], r["atr_min"], r["atr_max"])
            if key not in train_combos:
                train_combos[key] = []
            train_combos[key].append(r["sharpe"])
    # Pick top 3 by mean Sharpe on train
    train_ranked = sorted(train_combos.items(),
                          key=lambda x: -sum(x[1])/len(x[1]) if len(x[1]) >= 2 else -999)
    print(f"Top 3 combos sur TRAIN (mean Sharpe W1+W2) :")
    for key, sharpes in train_ranked[:3]:
        print(f"  {key} → mean_Sharpe TRAIN = {sum(sharpes)/len(sharpes):.2f}  (W1={sharpes[0]:.2f}, W2={sharpes[1]:.2f})")
    print()

    print(f"Validation OUT-OF-SAMPLE sur W0+W3 :")
    for key, train_sharpes in train_ranked[:3]:
        valid_sharpes = []
        valid_pnls = []
        for w in VALID_WINDOWS:
            for r in all_results[w]:
                rk = (r["pair"], r["z"], r["ma"], r["atr_min"], r["atr_max"])
                if rk == key:
                    valid_sharpes.append(r["sharpe"])
                    valid_pnls.append(r["pnl_pct"])
        if not valid_sharpes:
            continue
        mean_train = sum(train_sharpes) / len(train_sharpes)
        mean_valid = sum(valid_sharpes) / len(valid_sharpes)
        mean_pnl_valid = sum(valid_pnls) / len(valid_pnls)
        verdict = "OK" if mean_valid > 1.0 else ("WEAK" if mean_valid > 0 else "BROKEN")
        print(f"  {key}")
        print(f"    train_Sharpe={mean_train:+.2f}, valid_Sharpe={mean_valid:+.2f}, valid_PnL%={mean_pnl_valid:+.2f}% → {verdict}")
        print(f"    detailed valid : W0={valid_sharpes[0] if valid_sharpes else 'na':.2f}, W3={valid_sharpes[1] if len(valid_sharpes)>1 else 'na':.2f}")

    Path("meanrev_atr_v2_results.json").write_text(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Momentum v2 — walk-forward validation + trader amendments.

vs v1 :
1. Cap $25 (vs $30)
2. Lev 3x (vs 7x)
3. Fees taker 0.10% RT (momentum requires market entry, no maker possible)
4. Funding cost -0.03%/jour si LONG bias
5. Walk-forward : optimise sur W1+W2, valide out-of-sample W0+W3 SANS re-tuning
6. Param grid réduit pour éviter overfit
7. Stop loss EXPLICITE -3% from entry (au lieu de juste trail)
8. Test sur 8 pairs (top v1 + controls)
"""
import json, time, urllib.request, datetime, math
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "data_cache"

# Top from v1 + controls
PAIRS = ["INJUSDT", "APTUSDT", "OPUSDT", "SUIUSDT", "TIAUSDT",
         "AAVEUSDT", "AVAXUSDT", "LTCUSDT"]

WINDOWS = {
    "W0_current_30j":  None,
    "W1_2024_bull":    ("2024-03-01", "2024-04-30"),
    "W2_2024_transit": ("2024-10-01", "2024-12-31"),
    "W3_2025_chop":    ("2025-02-01", "2025-03-31"),
}
TRAIN_WINDOWS = ["W1_2024_bull", "W2_2024_transit"]
VALID_WINDOWS = ["W0_current_30j", "W3_2025_chop"]

# Reduced param grid (anti-overfit)
PUMP_THRESHOLDS = [0.02, 0.03]
VOL_MULTS = [1.5, 2.0]
TRAIL_STOPS = [0.025, 0.030]

# AMENDMENTS
CAPITAL = 25.0
LEVERAGE = 3
FEE_RT = 0.001       # taker 0.05% × 2 (market entry mandatory for momentum)
HARD_SL_PCT = 0.030  # NEW: hard SL -3% from entry (in addition to trailing)
FUNDING_DAILY = 0.0003  # 0.03%/jour funding cost (long bias)
COOLDOWN_MIN = 60    # 1h cooldown between trades same pair


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


def simulate(candles, pump_th, vol_mult, trail_pct):
    if len(candles) < 500:
        return None
    closes = [c[4] for c in candles]
    highs = [c[2] for c in candles]
    lows = [c[3] for c in candles]
    vols = [c[5] for c in candles]
    notional = CAPITAL * LEVERAGE

    trades = []
    pos = 0
    entry_price = 0.0
    entry_idx = 0
    high_since = 0.0
    cooldown = 0

    for i in range(360, len(candles)):
        if cooldown > 0:
            cooldown -= 1
            continue
        price = closes[i]

        if pos == 1:
            # Update trailing high
            if price > high_since: high_since = price
            trail_stop = high_since * (1 - trail_pct)
            hard_sl = entry_price * (1 - HARD_SL_PCT)
            # Use the higher of trail and hard SL
            effective_sl = max(trail_stop, hard_sl)
            # Take profit at 2x risk = 2 × trail from entry
            tp = entry_price * (1 + 2 * trail_pct)

            # Exit conditions
            hit_sl = (lows[i] <= effective_sl)
            hit_tp = (highs[i] >= tp)
            if hit_sl or hit_tp:
                exit_price = effective_sl if hit_sl else tp
                ret = (exit_price - entry_price) / entry_price
                # Funding cost (long pays)
                hours_held = (i - entry_idx) / 60.0
                funding_cost = FUNDING_DAILY * (hours_held / 24.0) * notional
                pnl = notional * ret - FEE_RT * notional - funding_cost
                trades.append((entry_idx, i, "LONG", pnl, "SL" if hit_sl else "TP"))
                pos = 0
                cooldown = COOLDOWN_MIN
            continue

        # New entry
        if closes[i-60] <= 0: continue
        ret_1h = closes[i] / closes[i-60] - 1
        if ret_1h < pump_th: continue
        vol_1h = sum(vols[i-60:i])
        vol_5h = sum(vols[i-360:i-60]) / 5.0
        if vol_5h <= 0: continue
        if vol_1h / vol_5h < vol_mult: continue

        pos = 1
        entry_price = price
        high_since = price
        entry_idx = i

    # Close remaining position
    if pos == 1:
        exit_price = closes[-1]
        ret = (exit_price - entry_price) / entry_price
        hours_held = (len(candles) - 1 - entry_idx) / 60.0
        funding_cost = FUNDING_DAILY * (hours_held / 24.0) * notional
        pnl = notional * ret - FEE_RT * notional - funding_cost
        trades.append((entry_idx, len(candles) - 1, "LONG", pnl, "END"))

    n = len(trades)
    if n == 0:
        return {"trades": 0, "pnl_total": 0, "pnl_pct": 0, "sharpe": 0,
                "win_rate": 0, "max_dd_pct": 0, "n_sl": 0, "n_tp": 0}
    pnl_total = sum(t[3] for t in trades)
    pnl_pct = pnl_total / CAPITAL * 100
    wins = [t[3] for t in trades if t[3] > 0]
    win_rate = len(wins) / n * 100
    n_sl = sum(1 for t in trades if t[4] == "SL")
    n_tp = sum(1 for t in trades if t[4] == "TP")

    # Equity curve at minute granularity
    eq_curve = [CAPITAL] * len(candles)
    cum_pnl = 0
    for t in trades:
        cum_pnl += t[3]
        for j in range(t[1], len(candles)):
            eq_curve[j] = CAPITAL + cum_pnl
    peak = CAPITAL; max_dd = 0
    for eq in eq_curve:
        if eq > peak: peak = eq
        if (peak - eq) > max_dd: max_dd = peak - eq
    max_dd_pct = max_dd / CAPITAL * 100

    # Daily Sharpe : sample equity every 1440 min
    daily_eq = [eq_curve[d + 1439] for d in range(0, len(eq_curve) - 1439, 1440)]
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

    return {
        "trades": n, "pnl_total": round(pnl_total, 3),
        "pnl_pct": round(pnl_pct, 2), "sharpe": round(sharpe, 2),
        "win_rate": round(win_rate, 1), "max_dd_pct": round(max_dd_pct, 2),
        "n_sl": n_sl, "n_tp": n_tp,
    }


def main():
    print(f"=== MOMENTUM v2 — WALK-FORWARD + AMENDMENTS ===")
    print(f"Cap=${CAPITAL} lev={LEVERAGE}x fee_rt={FEE_RT*100}% (taker)")
    print(f"hard_SL={HARD_SL_PCT*100}% funding={FUNDING_DAILY*100}%/jour cooldown={COOLDOWN_MIN}min")
    print(f"Train: {TRAIN_WINDOWS}  / Validation: {VALID_WINDOWS}\n")

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
                print(f"  SKIP {pair} ({len(d)} candles)")
                continue
            for pt in PUMP_THRESHOLDS:
                for vm in VOL_MULTS:
                    for ts in TRAIL_STOPS:
                        r = simulate(d, pt, vm, ts)
                        if r is None: continue
                        r["pair"] = pair.replace("USDT", "")
                        r["pump"] = pt; r["vol_mult"] = vm; r["trail"] = ts
                        all_results[win_name].append(r)
        results = all_results[win_name]
        # Top 10 by Sharpe
        results.sort(key=lambda x: -x["sharpe"])
        n_pos = sum(1 for r in results if r["pnl_total"] > 0)
        print(f"  → {n_pos}/{len(results)} combos positifs. Top 10 Sharpe :")
        print(f"  {'pair':6}{'pump':6}{'volX':6}{'trail':7}{'trades':8}{'win%':7}{'PnL$':9}{'PnL%':8}{'MaxDD%':8}{'Sharpe':8}")
        for r in results[:10]:
            print(f"  {r['pair']:6}{r['pump']*100:5.1f}%{r['vol_mult']:5.1f} {r['trail']*100:5.1f}%{r['trades']:>7}{r['win_rate']:>6.1f}%{r['pnl_total']:+8.2f}{r['pnl_pct']:+7.2f}%{r['max_dd_pct']:+7.2f}%{r['sharpe']:>7}")
        print()

    # WALK-FORWARD
    print(f"=== WALK-FORWARD VALIDATION ===")
    train_combos = {}
    for w in TRAIN_WINDOWS:
        for r in all_results[w]:
            key = (r["pair"], r["pump"], r["vol_mult"], r["trail"])
            if key not in train_combos:
                train_combos[key] = {"sharpes": [], "pnls": []}
            train_combos[key]["sharpes"].append(r["sharpe"])
            train_combos[key]["pnls"].append(r["pnl_pct"])

    # Filter combos tested on both train windows
    train_ranked = []
    for key, c in train_combos.items():
        if len(c["sharpes"]) < 2: continue
        mean_sh = sum(c["sharpes"]) / 2
        mean_pnl = sum(c["pnls"]) / 2
        train_ranked.append((key, mean_sh, mean_pnl, c["sharpes"], c["pnls"]))
    train_ranked.sort(key=lambda x: -x[1])

    print(f"Top 5 combos sur TRAIN :")
    for key, mean_sh, mean_pnl, sharpes, pnls in train_ranked[:5]:
        print(f"  {key} → mean_Sh={mean_sh:.2f} (W1={sharpes[0]:.2f}, W2={sharpes[1]:.2f}) mean_PnL%={mean_pnl:.1f}")
    print()

    # Validate top 5 on VALID windows
    print(f"VALIDATION OUT-OF-SAMPLE :")
    for key, mean_sh_train, mean_pnl_train, _, _ in train_ranked[:5]:
        valid_sharpes = []
        valid_pnls = []
        for w in VALID_WINDOWS:
            for r in all_results[w]:
                rk = (r["pair"], r["pump"], r["vol_mult"], r["trail"])
                if rk == key:
                    valid_sharpes.append((w, r["sharpe"], r["pnl_pct"]))
        if not valid_sharpes:
            print(f"  {key} → no valid data, skip")
            continue
        mean_sh_valid = sum(s[1] for s in valid_sharpes) / len(valid_sharpes)
        mean_pnl_valid = sum(s[2] for s in valid_sharpes) / len(valid_sharpes)
        verdict = "✅ OK" if mean_sh_valid > 1.0 else ("⚠️ WEAK" if mean_sh_valid > 0 else "❌ BROKEN")
        print(f"  {key}")
        print(f"    TRAIN Sharpe={mean_sh_train:.2f} PnL%={mean_pnl_train:.1f}")
        print(f"    VALID Sharpe={mean_sh_valid:.2f} PnL%={mean_pnl_valid:.1f}  {verdict}")
        for w, sh, pn in valid_sharpes:
            print(f"      {w}: Sharpe={sh:.2f} PnL%={pn:.1f}")

    Path("momentum_v2_results.json").write_text(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()

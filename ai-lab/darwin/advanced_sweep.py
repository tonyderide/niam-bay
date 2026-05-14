#!/usr/bin/env python3
"""Advanced backtest: validate Tier-1 techniques from research agents.

Features tested (on top of best volume config):
- A. ATR-dynamic spacing: spacing = ATR_4h_pct / k  (k=1.5, 2, 3)
- B. Trend gate: skip grid if |EMA50-EMA200|/close > strong_trend_pct
- C. Asymmetric grid: shift center upward in uptrend, downward in downtrend
- D. Per-level TripleBarrier-lite: each level kills itself after N candles unfilled

Output: PnL net, RTs, Calmar, DD per variant vs baseline.
"""
import json, time
from pathlib import Path
from datetime import datetime

CACHE_DIR = Path(__file__).parent / "data_cache"
# Top configs from previous sweeps
TARGETS = [
    {"pair": "DOT",  "spacing": 0.020, "levels": 4, "volume_mode": "vwap+spike2x"},
    {"pair": "LINK", "spacing": 0.030, "levels": 4, "volume_mode": "spike_avoid_2x"},
    {"pair": "ADA",  "spacing": 0.030, "levels": 4, "volume_mode": "all3"},
]
CAPITAL = 46.0
LEVERAGE = 5
FEE_RT = 0.0008
RSI_MIN, RSI_MAX = 36.0, 66.0
ATR_MIN, ATR_MAX = 1.12, 2.17

PAIR_BIN = {"DOT": "DOTUSDT", "LINK": "LINKUSDT", "ADA": "ADAUSDT",
            "SOL": "SOLUSDT", "BTC": "BTCUSDT", "ETH": "ETHUSDT"}

# Advanced variants to test
VARIANTS = [
    {"name": "baseline_static", "atr_k": None, "trend_skip_pct": None, "asym_shift": 0.0, "level_timeout_bars": None},
    {"name": "atr_k=1.5",       "atr_k": 1.5,  "trend_skip_pct": None, "asym_shift": 0.0, "level_timeout_bars": None},
    {"name": "atr_k=2.0",       "atr_k": 2.0,  "trend_skip_pct": None, "asym_shift": 0.0, "level_timeout_bars": None},
    {"name": "atr_k=3.0",       "atr_k": 3.0,  "trend_skip_pct": None, "asym_shift": 0.0, "level_timeout_bars": None},
    {"name": "trend_skip_5pct", "atr_k": None, "trend_skip_pct": 5.0,  "asym_shift": 0.0, "level_timeout_bars": None},
    {"name": "trend_skip_3pct", "atr_k": None, "trend_skip_pct": 3.0,  "asym_shift": 0.0, "level_timeout_bars": None},
    {"name": "asym_buy_uptrend","atr_k": None, "trend_skip_pct": None, "asym_shift": 0.3, "level_timeout_bars": None},
    {"name": "level_timeout_1440","atr_k": None, "trend_skip_pct": None, "asym_shift": 0.0, "level_timeout_bars": 1440},  # 24h
    {"name": "level_timeout_720","atr_k": None, "trend_skip_pct": None, "asym_shift": 0.0, "level_timeout_bars": 720},  # 12h
    # Combinations
    {"name": "ATR2.0+trend5",   "atr_k": 2.0,  "trend_skip_pct": 5.0,  "asym_shift": 0.0, "level_timeout_bars": None},
    {"name": "ATR2.0+trend5+asym","atr_k": 2.0,"trend_skip_pct": 5.0,  "asym_shift": 0.3, "level_timeout_bars": None},
    {"name": "ATR2.0+trend3+timeout24h","atr_k":2.0,"trend_skip_pct":3.0,"asym_shift":0.0,"level_timeout_bars":1440},
]


def load(pair_bin):
    f = CACHE_DIR / f"binance_{pair_bin}_1min_30d.json"
    return json.loads(f.read_text()) if f.exists() else None


def rsi_series(closes, period=14):
    out = [None] * len(closes)
    if len(closes) < period + 1: return out
    g, l = 0.0, 0.0
    for i in range(1, period+1):
        d = closes[i] - closes[i-1]
        if d > 0: g += d
        else: l -= d
    ag, al = g/period, l/period
    out[period] = 100 - 100/(1 + ag/al) if al else 100
    for i in range(period+1, len(closes)):
        d = closes[i] - closes[i-1]
        ag = (ag*(period-1) + max(d, 0))/period
        al = (al*(period-1) + max(-d, 0))/period
        out[i] = 100 - 100/(1 + ag/al) if al else 100
    return out


def atr_series(highs, lows, closes, period=14):
    """Returns absolute ATR (not %). Use atr/close for percentage."""
    out = [None] * len(closes)
    trs = [highs[0]-lows[0]]
    for i in range(1, len(closes)):
        trs.append(max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])))
    if len(trs) < period: return out
    cur = sum(trs[:period])/period
    out[period-1] = cur
    for i in range(period, len(trs)):
        cur = (cur*(period-1) + trs[i])/period
        out[i] = cur
    return out


def ema_series(closes, period):
    out = [None] * len(closes)
    if len(closes) < period: return out
    k = 2 / (period + 1)
    seed = sum(closes[:period]) / period
    out[period-1] = seed
    cur = seed
    for i in range(period, len(closes)):
        cur = closes[i] * k + cur * (1 - k)
        out[i] = cur
    return out


def resample_4h_with_vol(candles):
    bucket_ms = 4*3600*1000
    out = []; cur = None; o_ = h_ = l_ = c_ = v_ = pv = None
    for k in candles:
        ts, o, h, l, c, v = k
        b = (ts // bucket_ms) * bucket_ms
        if cur is None:
            cur = b; o_, h_, l_, c_, v_, pv = o, h, l, c, v, ((h+l+c)/3)*v
        elif b != cur:
            out.append([cur, o_, h_, l_, c_, v_, pv])
            cur = b; o_, h_, l_, c_, v_, pv = o, h, l, c, v, ((h+l+c)/3)*v
        else:
            h_ = max(h_, h); l_ = min(l_, l); c_ = c; v_ += v; pv += ((h+l+c)/3)*v
    if cur is not None: out.append([cur, o_, h_, l_, c_, v_, pv])
    return out


def simulate(candles, base_spacing, n_levels, vol_mode, variant):
    """Simulate grid with all features. Returns metrics."""
    if len(candles) < 200: return None
    ts = [c[0] for c in candles]; h = [c[2] for c in candles]
    l = [c[3] for c in candles]; cl = [c[4] for c in candles]

    # 4h aggregation for gate signals
    h4 = resample_4h_with_vol(candles)
    h4c = [k[4] for k in h4]; h4h = [k[2] for k in h4]; h4l = [k[3] for k in h4]
    h4v = [k[5] for k in h4]; h4pv = [k[6] for k in h4]
    h4rsi = rsi_series(h4c)
    h4_atr_abs = atr_series(h4h, h4l, h4c)
    h4_atr_pct = [a/c*100 if (a is not None and c) else None for a, c in zip(h4_atr_abs, h4c)]
    h4_ema50 = ema_series(h4c, 50)
    h4_ema200 = ema_series(h4c, 200) if len(h4c) >= 200 else [None] * len(h4c)

    # Rolling avg volume + VWAP (6 bars = 24h)
    def rolling_avg(arr, n):
        out = [None] * len(arr)
        for i in range(n-1, len(arr)):
            out[i] = sum(arr[i-n+1:i+1]) / n
        return out
    avg_vol = rolling_avg(h4v, 6)
    vwap = [None] * len(h4)
    for i in range(5, len(h4)):
        s_pv = sum(h4pv[i-5:i+1]); s_v = sum(h4v[i-5:i+1])
        vwap[i] = s_pv / s_v if s_v > 0 else None

    # Volume mode params
    vm_min = vm_spike = None; vm_vwap = False
    if vol_mode == "vwap+spike2x":
        vm_spike = 2.0; vm_vwap = True
    elif vol_mode == "spike_avoid_2x":
        vm_spike = 2.0
    elif vol_mode == "all3":
        vm_min = 1.0; vm_spike = 2.0; vm_vwap = True

    snapshots = []
    for i, k in enumerate(h4):
        rsi_ok = h4rsi[i] is not None and RSI_MIN <= h4rsi[i] <= RSI_MAX
        atr_ok = h4_atr_pct[i] is not None and ATR_MIN <= h4_atr_pct[i] <= ATR_MAX
        vol_ok = True
        if vm_min is not None and (avg_vol[i] is None or h4v[i] < avg_vol[i] * vm_min): vol_ok = False
        if vm_spike is not None and avg_vol[i] is not None and h4v[i] > avg_vol[i] * vm_spike: vol_ok = False
        # Trend gate: skip if abs(EMA50-EMA200)/close > threshold
        trend_ok = True
        if variant["trend_skip_pct"] is not None:
            if h4_ema50[i] is not None and h4_ema200[i] is not None:
                trend_strength = abs(h4_ema50[i] - h4_ema200[i]) / h4c[i] * 100
                if trend_strength > variant["trend_skip_pct"]: trend_ok = False
        # Trend direction for asymmetric grid
        trend_dir = 0
        if h4_ema50[i] is not None and h4_ema200[i] is not None:
            trend_dir = 1 if h4_ema50[i] > h4_ema200[i] else -1
        # Effective spacing: ATR-based or static
        if variant["atr_k"] is not None and h4_atr_pct[i] is not None:
            eff_spacing = (h4_atr_pct[i] / 100) / variant["atr_k"]
            eff_spacing = max(0.005, min(0.05, eff_spacing))  # clamp 0.5%-5%
        else:
            eff_spacing = base_spacing
        gate = rsi_ok and atr_ok and vol_ok and trend_ok
        center_price = vwap[i] if (vm_vwap and vwap[i] is not None) else None
        snapshots.append((k[0], gate, center_price, eff_spacing, trend_dir))

    notional = CAPITAL * LEVERAGE
    grid = None; rts = []; fills_b = fills_s = 0; opens = closes = 0
    cur_realized = 0.0; gate_idx = 0

    for i in range(20, len(candles)):
        bar_h, bar_l, bar_c = h[i], l[i], cl[i]
        while gate_idx + 1 < len(snapshots) and snapshots[gate_idx+1][0] <= ts[i]:
            gate_idx += 1
        g_open = snapshots[gate_idx][1]
        snap_center = snapshots[gate_idx][2]
        snap_spacing = snapshots[gate_idx][3]
        trend_dir = snapshots[gate_idx][4]

        if grid is None and g_open:
            center = snap_center if snap_center is not None else bar_c
            size_per = (notional / n_levels) / center
            # Asymmetric shift: if uptrend and asym_shift > 0, shift levels down (more buys cheaper)
            asym = variant["asym_shift"] * trend_dir
            levels = []
            for k_ in range(n_levels):
                offset = (k_ - n_levels/2 + 0.5 - asym) * snap_spacing
                price = center * (1 + offset)
                side = "buy" if offset < 0 else "sell"
                levels.append({"price": price, "side": side,
                               "status": "PLACED" if side == "buy" else "WAITING",
                               "placed_at_bar": i})
            grid = {"center": center, "levels": levels, "pos": 0.0, "entry_avg": 0.0,
                    "size_per": size_per}
            opens += 1

        if grid is not None and not g_open and grid["pos"] < 1e-9:
            grid = None; closes += 1; continue
        if grid is not None and bar_l <= grid["center"] * 0.97 and grid["pos"] > 0:
            pnl = grid["pos"] * (grid["center"]*0.97 - grid["entry_avg"]) - FEE_RT * grid["pos"] * grid["center"]*0.97
            cur_realized += pnl; grid["pos"] = 0
            grid = None; closes += 1; continue
        if grid is None: continue

        # Level timeout: cancel placed buy levels older than N bars
        if variant["level_timeout_bars"] is not None:
            for lvl in grid["levels"]:
                if lvl["status"] == "PLACED" and lvl["side"] == "buy":
                    if i - lvl["placed_at_bar"] > variant["level_timeout_bars"]:
                        lvl["status"] = "TIMED_OUT"

        for lvl in grid["levels"]:
            if lvl["status"] != "PLACED": continue
            if lvl["side"] == "buy" and bar_l <= lvl["price"]:
                fp = lvl["price"]; new_total = grid["pos"] + grid["size_per"]
                grid["entry_avg"] = (grid["entry_avg"]*grid["pos"] + fp*grid["size_per"]) / new_total
                grid["pos"] = new_total; lvl["status"] = "FILLED_BUY"; fills_b += 1
                next_sell = fp * (1 + snap_spacing); found = False
                for s in grid["levels"]:
                    if s["status"] == "WAITING" and abs(s["price"] - next_sell)/next_sell < 0.005:
                        s["status"] = "PLACED"; s["placed_at_bar"] = i; found = True; break
                if not found:
                    grid["levels"].append({"price": next_sell, "side": "sell", "status": "PLACED", "placed_at_bar": i})
            elif lvl["side"] == "sell" and bar_h >= lvl["price"] and grid["pos"] >= grid["size_per"] - 1e-9:
                fp = lvl["price"]
                pnl = grid["size_per"] * (fp - grid["entry_avg"]) - FEE_RT * grid["size_per"] * fp
                cur_realized += pnl; grid["pos"] -= grid["size_per"]
                if grid["pos"] < 1e-9: grid["pos"] = 0
                lvl["status"] = "FILLED_SELL"; fills_s += 1; rts.append(pnl)

    if grid is not None and grid["pos"] > 0:
        pnl = grid["pos"] * (cl[-1] - grid["entry_avg"]) - FEE_RT * grid["pos"] * cl[-1]
        cur_realized += pnl; rts.append(pnl)

    dur_days = (ts[-1] - ts[0]) / 86400000
    return {
        "rts": len(rts), "fills_b": fills_b, "fills_s": fills_s, "opens": opens,
        "pnl_net": round(cur_realized, 4),
        "pnl_pct": round(cur_realized / CAPITAL * 100, 2),
        "fills_per_day": round((fills_b + fills_s) / max(dur_days, 0.001), 2),
    }


def main():
    print(f"Advanced sweep — {len(TARGETS)} target pairs × {len(VARIANTS)} variants = {len(TARGETS)*len(VARIANTS)} simulations\n")

    cache = {}
    for t in TARGETS:
        c = load(PAIR_BIN[t["pair"]])
        if c: cache[t["pair"]] = c

    all_results = []
    for t in TARGETS:
        if t["pair"] not in cache: continue
        baseline_result = None
        per_target_results = []
        for v in VARIANTS:
            r = simulate(cache[t["pair"]], t["spacing"], t["levels"], t["volume_mode"], v)
            if r is None: continue
            r.update({"pair": t["pair"], "spacing_base": t["spacing"], "levels": t["levels"],
                      "vol_mode": t["volume_mode"], "variant": v["name"]})
            if v["name"] == "baseline_static": baseline_result = r
            per_target_results.append(r)
            all_results.append(r)
        # Print per-target comparison
        print(f"=== {t['pair']} (base {t['spacing']*100:.1f}% × {t['levels']}lv + {t['volume_mode']}) ===")
        print(f"{'variant':30} {'RT':4} {'fills/d':8} {'PnL$':9} {'PnL%':7} {'Δvs baseline':14}")
        base_pnl = baseline_result["pnl_net"] if baseline_result else 0
        for r in per_target_results:
            delta = r["pnl_net"] - base_pnl
            mark = " ★" if delta > 0.5 else (" ✓" if delta > 0 else ("" if abs(delta) < 0.01 else " ↓"))
            print(f"  {r['variant']:30} {r['rts']:3}  {r['fills_per_day']:6}  {r['pnl_net']:+8.3f}  {r['pnl_pct']:+6.2f}%  Δ={delta:+7.3f}{mark}")
        print()

    # Cross-target sum per variant (portfolio view)
    print("=== Portfolio sum per variant (3 pairs combined) ===")
    by_variant = {}
    for r in all_results:
        if r["variant"] not in by_variant:
            by_variant[r["variant"]] = {"pnl_net": 0, "rts": 0, "fills": 0, "pairs": []}
        by_variant[r["variant"]]["pnl_net"] += r["pnl_net"]
        by_variant[r["variant"]]["rts"] += r["rts"]
        by_variant[r["variant"]]["fills"] += r["fills_b"] + r["fills_s"]
        by_variant[r["variant"]]["pairs"].append(r["pair"])

    sorted_v = sorted(by_variant.items(), key=lambda x: -x[1]["pnl_net"])
    base_portfolio_pnl = by_variant["baseline_static"]["pnl_net"]
    print(f"{'variant':30} {'PnL$':9} {'PnL%':7} {'RT':4} {'fills':6} {'Δvs baseline':14}")
    for vname, d in sorted_v:
        delta = d["pnl_net"] - base_portfolio_pnl
        mark = " ★" if delta > 1 else (" ✓" if delta > 0.01 else "")
        print(f"  {vname:30} {d['pnl_net']:+8.3f}  {d['pnl_net']/(CAPITAL*3)*100:+6.2f}%  {d['rts']:3}  {d['fills']:4}   Δ={delta:+6.3f}{mark}")

    out = Path(__file__).parent / "advanced_sweep_results.json"
    out.write_text(json.dumps(all_results, indent=2))
    print(f"\nFull: {out}")


if __name__ == "__main__":
    main()

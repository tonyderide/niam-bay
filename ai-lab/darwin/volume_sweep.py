#!/usr/bin/env python3
"""Volume-aware grid sweep: tests volume filters + VWAP center.

Tests:
- baseline (no volume filter)
- min_vol: only open grid when vol(rolling 24h) > pair_avg × threshold
- spike_avoid: skip grid open if vol > avg × spike_multiplier
- vwap_center: use VWAP(rolling 4h) as grid center instead of close
- combined: min_vol + spike_avoid + vwap
"""
import json, time
from pathlib import Path
from datetime import datetime

CACHE_DIR = Path(__file__).parent / "data_cache"
PAIRS = {"LINK": "LINKUSDT", "SOL": "SOLUSDT", "DOT": "DOTUSDT",
         "BTC": "BTCUSDT", "ETH": "ETHUSDT", "ADA": "ADAUSDT"}
# Top configs from previous sweep
CONFIGS = [
    ("DOT", 0.015, 4), ("DOT", 0.010, 4), ("DOT", 0.020, 4),
    ("LINK", 0.030, 4), ("ADA", 0.030, 4),
    ("DOT", 0.015, 6), ("LINK", 0.020, 6), ("ADA", 0.020, 6),  # for comparison with current spacing
    ("DOT", 0.020, 6),  # current
]
CAPITAL = 46.0
LEVERAGE = 5
FEE_RT = 0.0008
RSI_MIN, RSI_MAX = 36.0, 66.0
ATR_MIN, ATR_MAX = 1.12, 2.17

VOLUME_MODES = [
    {"name": "baseline", "min_vol_mult": None, "skip_spike_mult": None, "use_vwap": False},
    {"name": "min_vol_1.0", "min_vol_mult": 1.0, "skip_spike_mult": None, "use_vwap": False},
    {"name": "min_vol_1.5", "min_vol_mult": 1.5, "skip_spike_mult": None, "use_vwap": False},
    {"name": "spike_avoid_3x", "min_vol_mult": None, "skip_spike_mult": 3.0, "use_vwap": False},
    {"name": "spike_avoid_2x", "min_vol_mult": None, "skip_spike_mult": 2.0, "use_vwap": False},
    {"name": "vwap_only", "min_vol_mult": None, "skip_spike_mult": None, "use_vwap": True},
    {"name": "vwap+spike2x", "min_vol_mult": None, "skip_spike_mult": 2.0, "use_vwap": True},
    {"name": "all3", "min_vol_mult": 1.0, "skip_spike_mult": 2.0, "use_vwap": True},
]


def load(pair):
    f = CACHE_DIR / f"binance_{pair}_1min_30d.json"
    if not f.exists(): return None
    return json.loads(f.read_text())


def rsi_series(closes, period=14):
    out = [None] * len(closes)
    if len(closes) < period + 1: return out
    g, l = 0.0, 0.0
    for i in range(1, period + 1):
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


def atr_pct(highs, lows, closes, period=14):
    out = [None] * len(closes)
    trs = [highs[0]-lows[0]]
    for i in range(1, len(closes)):
        trs.append(max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])))
    if len(trs) < period: return out
    cur = sum(trs[:period])/period
    out[period-1] = (cur/closes[period-1])*100 if closes[period-1] else None
    for i in range(period, len(trs)):
        cur = (cur*(period-1) + trs[i])/period
        out[i] = (cur/closes[i])*100 if closes[i] else None
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


def simulate(candles, spacing, n_levels, mode):
    if len(candles) < 200: return None
    ts = [c[0] for c in candles]; h = [c[2] for c in candles]
    l = [c[3] for c in candles]; cl = [c[4] for c in candles]; vol = [c[5] for c in candles]

    h4 = resample_4h_with_vol(candles)
    h4c = [k[4] for k in h4]; h4h = [k[2] for k in h4]; h4l = [k[3] for k in h4]
    h4v = [k[5] for k in h4]; h4pv = [k[6] for k in h4]
    h4rsi = rsi_series(h4c); h4atr = atr_pct(h4h, h4l, h4c)

    # Rolling avg volume (last 24h = 6 buckets 4h)
    def rolling_avg(arr, n):
        out = [None] * len(arr)
        for i in range(n-1, len(arr)):
            out[i] = sum(arr[i-n+1:i+1]) / n
        return out
    avg_vol = rolling_avg(h4v, 6)

    # VWAP from rolling 4h pv/v
    def rolling_vwap(pv_arr, v_arr, n):
        out = [None] * len(pv_arr)
        for i in range(n-1, len(pv_arr)):
            s_pv = sum(pv_arr[i-n+1:i+1])
            s_v = sum(v_arr[i-n+1:i+1])
            out[i] = s_pv / s_v if s_v > 0 else None
        return out
    vwap = rolling_vwap(h4pv, h4v, 6)

    # Build per-bar gate snapshot
    snapshots = []
    for i, k in enumerate(h4):
        rsi_ok = h4rsi[i] is not None and RSI_MIN <= h4rsi[i] <= RSI_MAX
        atr_ok = h4atr[i] is not None and ATR_MIN <= h4atr[i] <= ATR_MAX
        vol_ok = True
        if mode["min_vol_mult"] is not None:
            if avg_vol[i] is None or h4v[i] < avg_vol[i] * mode["min_vol_mult"]:
                vol_ok = False
        if mode["skip_spike_mult"] is not None:
            if avg_vol[i] is not None and h4v[i] > avg_vol[i] * mode["skip_spike_mult"]:
                vol_ok = False
        gate = rsi_ok and atr_ok and vol_ok
        center_price = vwap[i] if (mode["use_vwap"] and vwap[i] is not None) else None
        snapshots.append((k[0], gate, center_price))

    notional = CAPITAL * LEVERAGE
    grid = None; rts = []; fills_b = fills_s = 0; opens = closes = 0
    cur_realized = 0.0; gate_idx = 0

    for i in range(20, len(candles)):
        bar_h, bar_l, bar_c = h[i], l[i], cl[i]
        while gate_idx + 1 < len(snapshots) and snapshots[gate_idx+1][0] <= ts[i]:
            gate_idx += 1
        g_open = snapshots[gate_idx][1]
        snap_center = snapshots[gate_idx][2]

        if grid is None and g_open:
            center = snap_center if snap_center is not None else bar_c
            size_per = (notional / n_levels) / center
            levels = []
            for k_ in range(n_levels):
                offset = (k_ - n_levels/2 + 0.5) * spacing
                price = center * (1 + offset)
                side = "buy" if offset < 0 else "sell"
                levels.append({"price": price, "side": side,
                               "status": "PLACED" if side == "buy" else "WAITING"})
            grid = {"center": center, "levels": levels, "pos": 0.0, "entry_avg": 0.0,
                    "size_per": size_per}; opens += 1

        if grid is not None and not g_open and grid["pos"] < 1e-9:
            grid = None; closes += 1; continue
        if grid is not None and bar_l <= grid["center"] * 0.97 and grid["pos"] > 0:
            pnl = grid["pos"] * (grid["center"]*0.97 - grid["entry_avg"]) - FEE_RT * grid["pos"] * grid["center"]*0.97
            cur_realized += pnl; grid["pos"] = 0
            grid = None; closes += 1; continue
        if grid is None: continue

        for lvl in grid["levels"]:
            if lvl["status"] != "PLACED": continue
            if lvl["side"] == "buy" and bar_l <= lvl["price"]:
                fp = lvl["price"]; new_total = grid["pos"] + grid["size_per"]
                grid["entry_avg"] = (grid["entry_avg"]*grid["pos"] + fp*grid["size_per"]) / new_total
                grid["pos"] = new_total; lvl["status"] = "FILLED_BUY"; fills_b += 1
                next_sell = fp * (1 + spacing); found = False
                for s in grid["levels"]:
                    if s["status"] == "WAITING" and abs(s["price"] - next_sell)/next_sell < 0.005:
                        s["status"] = "PLACED"; found = True; break
                if not found:
                    grid["levels"].append({"price": next_sell, "side": "sell", "status": "PLACED"})
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
        "annualized": round(cur_realized / CAPITAL * 100 * 365 / dur_days, 1) if dur_days else 0,
        "fills_per_day": round((fills_b + fills_s) / max(dur_days, 0.001), 2),
    }


def main():
    print(f"Volume-aware sweep — {len(CONFIGS)} configs × {len(VOLUME_MODES)} volume modes\n")

    cache_data = {}
    for label, pair in PAIRS.items():
        c = load(pair)
        if c: cache_data[label] = c

    results = []
    for label, sp, lv in CONFIGS:
        if label not in cache_data: continue
        for mode in VOLUME_MODES:
            r = simulate(cache_data[label], sp, lv, mode)
            if r is None: continue
            r.update({"pair": label, "spacing": sp, "levels": lv, "mode": mode["name"]})
            results.append(r)

    # Sort by PnL net
    results.sort(key=lambda x: x["pnl_net"], reverse=True)

    print(f"=== TOP 20 (par PnL net) ===")
    print(f"{'pair':5} {'sp%':6} {'lv':3} {'mode':18} {'RT':4} {'fills/d':8} {'PnL$':8} {'PnL%':7} {'annual%':9}")
    for r in results[:20]:
        print(f"{r['pair']:5} {r['spacing']*100:5.2f}% {r['levels']:2}  {r['mode']:18} {r['rts']:3}  {r['fills_per_day']:6}  {r['pnl_net']:+7.3f}  {r['pnl_pct']:+6.2f}%  {r['annualized']:+8.1f}%")

    # Per-config best mode
    print("\n=== Best volume mode per config ===")
    by_config = {}
    for r in results:
        key = (r["pair"], r["spacing"], r["levels"])
        if key not in by_config or r["pnl_net"] > by_config[key]["pnl_net"]:
            by_config[key] = r
    for (pair, sp, lv), r in sorted(by_config.items(), key=lambda x: -x[1]["pnl_net"]):
        baseline = next((x for x in results if x["pair"]==pair and x["spacing"]==sp and x["levels"]==lv and x["mode"]=="baseline"), None)
        delta = r["pnl_net"] - baseline["pnl_net"] if baseline else 0
        sign = "↑" if delta > 0 else ("↓" if delta < 0 else "=")
        print(f"  {pair:4} sp={sp*100:.1f}% lv={lv} → best={r['mode']:14} PnL=${r['pnl_net']:+.2f} (vs baseline ${baseline['pnl_net']:+.2f} {sign}${abs(delta):.2f})")

    out = Path(__file__).parent / "volume_sweep_results.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\nFull: {out}")


if __name__ == "__main__":
    main()

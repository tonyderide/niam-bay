#!/usr/bin/env python3
"""Backtest segmenté JOUR vs NUIT sur config Option B (DOT/LINK/ADA).

Compare:
  - 24/7 (current Martin)
  - Day only (7h-22h Paris = 5h-20h UTC)
  - Night only (22h-7h Paris = 20h-5h UTC)
  - Weekday only (lundi-vendredi)
  - Weekend only
"""
import json, time
from pathlib import Path
from datetime import datetime, timezone

CACHE_DIR = Path(__file__).parent / "data_cache"
PAIRS = {"DOT": "DOTUSDT", "LINK": "LINKUSDT", "ADA": "ADAUSDT"}
CONFIGS = [
    {"pair": "DOT",  "spacing": 0.015, "levels": 4},
    {"pair": "LINK", "spacing": 0.030, "levels": 4},
    {"pair": "ADA",  "spacing": 0.030, "levels": 4},
]
CAPITAL = 46.0
LEVERAGE = 7  # Option B
FEE_RT = 0.0008
RSI_MIN, RSI_MAX = 36.0, 66.0
ATR_MIN, ATR_MAX = 1.12, 2.17

# Time windows (UTC hours)
TIME_WINDOWS = {
    "24/7":         {"hours": None,           "days": None},
    "day_paris":    {"hours": (5, 20),        "days": None},   # 7h-22h Paris
    "night_paris":  {"hours_inv": (5, 20),    "days": None},   # 22h-7h Paris
    "weekday":      {"hours": None,           "days": (0, 4)}, # Mon-Fri
    "weekend":      {"hours": None,           "days": (5, 6)}, # Sat-Sun
    "us_open":      {"hours": (13, 21),       "days": None},   # 15h-23h Paris (NYSE)
    "eu_open":      {"hours": (7, 16),        "days": None},   # 9h-18h Paris
    "asia_open":    {"hours": (23, 8),        "days": None},   # 1h-10h Paris (Tokyo)
}


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


def resample_4h(candles):
    bucket = 4*3600*1000
    out = []; cur = None; o_ = h_ = l_ = c_ = None
    for k in candles:
        ts, o, h, l, c, v = k
        b = (ts // bucket) * bucket
        if cur is None: cur=b; o_,h_,l_,c_ = o,h,l,c
        elif b != cur:
            out.append([cur, o_, h_, l_, c_])
            cur=b; o_,h_,l_,c_ = o,h,l,c
        else:
            h_ = max(h_, h); l_ = min(l_, l); c_ = c
    if cur is not None: out.append([cur, o_, h_, l_, c_])
    return out


def in_window(ts_ms, window):
    """Check if a UTC timestamp falls within the specified window."""
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    hour, weekday = dt.hour, dt.weekday()

    # Day filter
    if window.get("days") is not None:
        d_start, d_end = window["days"]
        if not (d_start <= weekday <= d_end):
            return False

    # Hour filter — straight window
    if window.get("hours") is not None:
        h_start, h_end = window["hours"]
        if h_start <= h_end:  # normal range
            if not (h_start <= hour < h_end):
                return False
        else:  # wraps midnight (e.g., 23-8)
            if not (hour >= h_start or hour < h_end):
                return False

    # Hour filter — inverted window (e.g., night = NOT 5-20)
    if window.get("hours_inv") is not None:
        h_start, h_end = window["hours_inv"]
        if h_start <= hour < h_end:
            return False

    return True


def simulate(candles, spacing, n_levels, window):
    """Run grid; only OPEN new grids when timestamp is within the window."""
    if len(candles) < 200: return None
    ts = [c[0] for c in candles]; h = [c[2] for c in candles]
    l = [c[3] for c in candles]; cl = [c[4] for c in candles]

    h4 = resample_4h(candles)
    h4c = [k[4] for k in h4]; h4h = [k[2] for k in h4]; h4l = [k[3] for k in h4]
    h4_rsi = rsi_series(h4c); h4_atrp = atr_pct(h4h, h4l, h4c)
    h4_gate = [(k[0], (h4_rsi[i] is not None and h4_atrp[i] is not None
                       and RSI_MIN <= h4_rsi[i] <= RSI_MAX
                       and ATR_MIN <= h4_atrp[i] <= ATR_MAX)) for i, k in enumerate(h4)]

    notional = CAPITAL * LEVERAGE
    grid = None; rts = []; fills_b = fills_s = 0
    cur_realized = 0.0; gate_idx = 0
    in_window_minutes = 0

    for i in range(20, len(candles)):
        bar_h, bar_l, bar_c = h[i], l[i], cl[i]
        bar_in_window = in_window(ts[i], window)
        if bar_in_window:
            in_window_minutes += 1

        while gate_idx + 1 < len(h4_gate) and h4_gate[gate_idx+1][0] <= ts[i]:
            gate_idx += 1
        g_open = h4_gate[gate_idx][1] if gate_idx < len(h4_gate) else False

        # Only OPEN new grids if in window (positions can still close anytime)
        if grid is None and g_open and bar_in_window:
            center = bar_c
            size_per = (notional / n_levels) / center
            levels = []
            for k_ in range(n_levels):
                offset = (k_ - n_levels/2 + 0.5) * spacing
                price = center * (1 + offset)
                side = "buy" if offset < 0 else "sell"
                levels.append({"price": price, "side": side,
                               "status": "PLACED" if side == "buy" else "WAITING"})
            grid = {"center": center, "levels": levels, "pos": 0.0, "entry_avg": 0.0,
                    "size_per": size_per}

        if grid is not None and not g_open and grid["pos"] < 1e-9:
            grid = None; continue
        if grid is not None and bar_l <= grid["center"] * 0.97 and grid["pos"] > 0:
            pnl = grid["pos"] * (grid["center"]*0.97 - grid["entry_avg"]) - FEE_RT * grid["pos"] * grid["center"]*0.97
            cur_realized += pnl; grid["pos"] = 0
            grid = None; continue
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

    return {
        "rts": len(rts), "fills_b": fills_b, "fills_s": fills_s,
        "pnl_net": round(cur_realized, 4),
        "window_minutes": in_window_minutes,
        "window_hours": round(in_window_minutes / 60, 1),
    }


def main():
    print(f"Day/Night sweep — Option B (DOT 1.5%/4, LINK 3%/4, ADA 3%/4) × 7x lev\n")

    cache = {}
    for c in CONFIGS:
        d = load(PAIRS[c["pair"]])
        if d: cache[c["pair"]] = d

    results = {}
    for window_name, window in TIME_WINDOWS.items():
        results[window_name] = {"pairs": {}, "total_pnl": 0, "total_rts": 0, "total_fills": 0, "hours": 0}
        for c in CONFIGS:
            if c["pair"] not in cache: continue
            r = simulate(cache[c["pair"]], c["spacing"], c["levels"], window)
            if r is None: continue
            results[window_name]["pairs"][c["pair"]] = r
            results[window_name]["total_pnl"] += r["pnl_net"]
            results[window_name]["total_rts"] += r["rts"]
            results[window_name]["total_fills"] += r["fills_b"] + r["fills_s"]
            results[window_name]["hours"] = r["window_hours"]

    print(f"{'Window':16} {'Hours':7} {'Total PnL$':12} {'PnL%':7} {'$/h':8} {'RTs':5} {'fills':6}")
    print("─" * 75)
    total_capital = 3 * CAPITAL
    for name, r in results.items():
        pnl = r["total_pnl"]
        pct = pnl / total_capital * 100
        per_hour = pnl / max(r["hours"], 0.001)
        print(f"{name:16} {r['hours']:6.0f}h  ${pnl:+8.3f}  {pct:+6.2f}%  ${per_hour:+6.4f}/h  {r['total_rts']:4}  {r['total_fills']:5}")

    print("\n=== Per pair × window ===")
    print(f"{'Pair':5} {'Window':16} {'PnL$':10} {'RTs':5} {'fills/h':9}")
    for c in CONFIGS:
        p = c["pair"]
        for w_name in TIME_WINDOWS:
            r = results[w_name]["pairs"].get(p)
            if r:
                fills_h = (r["fills_b"] + r["fills_s"]) / max(r["window_hours"], 0.001)
                print(f"{p:5} {w_name:16} ${r['pnl_net']:+7.3f}  {r['rts']:3}  {fills_h:6.3f}")

    print("\n=== Verdict ===")
    base = results["24/7"]["total_pnl"]
    print(f"Baseline 24/7: ${base:+.3f} ({results['24/7']['hours']:.0f}h)")
    for name in ["day_paris", "night_paris", "weekday", "weekend", "us_open", "eu_open", "asia_open"]:
        r = results[name]
        pnl = r["total_pnl"]
        pct_of_base = pnl / base * 100 if base else 0
        per_h = pnl / max(r["hours"], 0.001)
        base_per_h = base / max(results["24/7"]["hours"], 0.001)
        efficiency = per_h / base_per_h * 100 if base_per_h else 0
        print(f"  {name:14}: ${pnl:+6.3f} = {pct_of_base:5.1f}% of total in {r['hours']:.0f}h | $/h efficiency = {efficiency:5.1f}% of 24/7")

    out = Path(__file__).parent / "day_night_results.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\nFull: {out}")


if __name__ == "__main__":
    main()

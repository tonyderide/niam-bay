#!/usr/bin/env python3
"""Near-tick backtest: 1-second OHLC from Binance, 7 days.

Same grid sweep + volume modes as comprehensive_sweep but at 1s granularity.
Compare vs 1min results to see if tick precision matters.
"""
import json, time, urllib.request
from pathlib import Path
from datetime import datetime

CACHE_DIR = Path(__file__).parent / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)

PAIRS = {"DOT": "DOTUSDT", "LINK": "LINKUSDT", "ADA": "ADAUSDT"}
SPACINGS = [0.005, 0.008, 0.010, 0.015, 0.020, 0.025, 0.030]
LEVELS_LIST = [4, 6, 8]
CAPITAL = 46.0
LEVERAGE = 5
FEE_RT = 0.0008
DAYS_BACK = 7  # 7 days × 86400s = 604800 candles per pair, ~50MB JSON each

RSI_MIN, RSI_MAX = 36.0, 66.0
ATR_MIN, ATR_MAX = 1.12, 2.17


def fetch_binance_1s(pair, days=DAYS_BACK):
    """Fetch 1s OHLC from Binance, paginated. Cached on disk."""
    cache = CACHE_DIR / f"binance_{pair}_1s_{days}d.json"
    if cache.exists() and (time.time() - cache.stat().st_mtime) < 12 * 3600:
        return json.loads(cache.read_text())
    out = []
    end_ms = int(time.time() * 1000)
    cursor = end_ms - days * 86400 * 1000
    t_start = time.time()
    n_calls = 0
    while cursor < end_ms:
        url = (f"https://api.binance.com/api/v3/klines?symbol={pair}"
               f"&interval=1s&startTime={cursor}&endTime={end_ms}&limit=1000")
        try:
            d = json.loads(urllib.request.urlopen(url, timeout=30).read())
        except Exception as e:
            print(f"  err {pair}: {e}"); time.sleep(2); continue
        if not d: break
        out.extend([[int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in d])
        last_close = int(d[-1][6])
        if last_close <= cursor: break
        cursor = last_close + 1
        n_calls += 1
        if n_calls % 100 == 0:
            elapsed = time.time() - t_start
            pct = (cursor - (end_ms - days*86400*1000)) / (days*86400*1000) * 100
            print(f"  {pair}: {n_calls} calls, {len(out)} candles, {pct:.1f}%, {elapsed:.0f}s elapsed")
        if len(d) < 1000: break
        time.sleep(0.08)  # ~12 req/s rate limit
    cache.write_text(json.dumps(out))
    print(f"  cached {len(out)} candles for {pair} in {time.time()-t_start:.0f}s")
    return out


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
    """Aggregate 1s to 4h. ts in ms."""
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


def simulate(candles, spacing, n_levels, vol_mode="vwap+spike2x"):
    if len(candles) < 200: return None
    ts = [c[0] for c in candles]; h = [c[2] for c in candles]
    l = [c[3] for c in candles]; cl = [c[4] for c in candles]

    h4 = resample_4h(candles)
    h4c = [k[4] for k in h4]; h4h = [k[2] for k in h4]; h4l = [k[3] for k in h4]
    h4v = [k[5] for k in h4]; h4pv = [k[6] for k in h4]
    h4rsi = rsi_series(h4c); h4atr = atr_pct(h4h, h4l, h4c)

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

    vm_min = vm_spike = None; vm_vwap = False
    if vol_mode == "vwap+spike2x": vm_spike = 2.0; vm_vwap = True
    elif vol_mode == "spike_avoid_2x": vm_spike = 2.0
    elif vol_mode == "all3": vm_min = 1.0; vm_spike = 2.0; vm_vwap = True

    snapshots = []
    for i, k in enumerate(h4):
        rsi_ok = h4rsi[i] is not None and RSI_MIN <= h4rsi[i] <= RSI_MAX
        atr_ok = h4atr[i] is not None and ATR_MIN <= h4atr[i] <= ATR_MAX
        vol_ok = True
        if vm_min is not None and (avg_vol[i] is None or h4v[i] < avg_vol[i] * vm_min): vol_ok = False
        if vm_spike is not None and avg_vol[i] is not None and h4v[i] > avg_vol[i] * vm_spike: vol_ok = False
        gate = rsi_ok and atr_ok and vol_ok
        center_price = vwap[i] if (vm_vwap and vwap[i] is not None) else None
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
                    "size_per": size_per}
            opens += 1

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
        "dur_days": round(dur_days, 2),
    }


def main():
    print(f"Near-tick sweep (1s OHLC) — {DAYS_BACK} days × 3 pairs × {len(SPACINGS)}sp × {len(LEVELS_LIST)}lv\n")

    cache_data = {}
    for label, pair in PAIRS.items():
        print(f"fetching {label} ({pair}) 1s × {DAYS_BACK}d...")
        c = fetch_binance_1s(pair, days=DAYS_BACK)
        if c and len(c) >= 1000:
            cache_data[label] = c
            print(f"  {len(c)} candles ({(c[-1][0]-c[0][0])/86400000:.2f}d)\n")
        else:
            print(f"  FAIL ({len(c) if c else 0})\n")

    results = []
    print(f"Running {len(cache_data)} × {len(SPACINGS)} × {len(LEVELS_LIST)} = {len(cache_data)*len(SPACINGS)*len(LEVELS_LIST)} simulations...\n")
    for label, candles in cache_data.items():
        for sp in SPACINGS:
            for lv in LEVELS_LIST:
                r = simulate(candles, sp, lv)
                if r is None: continue
                r["pair"] = label; r["spacing"] = sp; r["levels"] = lv
                results.append(r)

    results.sort(key=lambda x: x["pnl_net"], reverse=True)

    print("=== TOP 20 (par PnL net, 1s granularity) ===")
    print(f"{'pair':5} {'sp%':6} {'lv':3} {'RT':4} {'fills/d':8} {'PnL$':9} {'PnL%':7} {'annual%':9}")
    for r in results[:20]:
        print(f"{r['pair']:5} {r['spacing']*100:5.2f}% {r['levels']:2}  {r['rts']:3}  {r['fills_per_day']:6}  {r['pnl_net']:+8.3f}  {r['pnl_pct']:+6.2f}%  {r['annualized']:+8.1f}%")

    best_per_pair = {}
    for r in results:
        if r["pair"] not in best_per_pair or r["pnl_net"] > best_per_pair[r["pair"]]["pnl_net"]:
            best_per_pair[r["pair"]] = r

    print("\n=== Best per pair (1s) ===")
    portfolio_pnl = 0
    for p, r in sorted(best_per_pair.items(), key=lambda x: -x[1]["pnl_net"]):
        print(f"  {p:5} sp={r['spacing']*100:.1f}% lv={r['levels']} → RT={r['rts']} PnL=${r['pnl_net']:+.2f} ({r['pnl_pct']:+.1f}%) over {r['dur_days']:.1f}d")
        portfolio_pnl += r["pnl_net"]
    print(f"\nPortfolio top-3 ({DAYS_BACK}d window): ${portfolio_pnl:+.2f} / ${3*CAPITAL} = {portfolio_pnl/(3*CAPITAL)*100:+.2f}% net")

    out = Path(__file__).parent / "sweep_1s_results.json"
    out.write_text(json.dumps({"generated_at": datetime.utcnow().isoformat(),
                               "config": {"interval": "1s", "days": DAYS_BACK},
                               "all_results": results, "best_per_pair": best_per_pair}, indent=2))
    print(f"\nFull: {out}")


if __name__ == "__main__":
    main()

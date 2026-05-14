#!/usr/bin/env python3
"""Comprehensive sweep: grid spacing × levels × pairs at 1min, with Binance data.
Computes: RTs, fills/day, net PnL after fees, max DD, Calmar.
Also tests parallel-grids portfolio.
"""
import json, time, urllib.request
from pathlib import Path
from datetime import datetime

CACHE_DIR = Path(__file__).parent / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)

PAIRS = {"LINK": "LINKUSDT", "SOL": "SOLUSDT", "DOT": "DOTUSDT",
         "BTC": "BTCUSDT", "ETH": "ETHUSDT", "ADA": "ADAUSDT"}
SPACINGS = [0.005, 0.008, 0.010, 0.015, 0.020, 0.025, 0.030]
LEVELS_LIST = [4, 6, 8, 10]
CAPITAL_PER_PAIR = 46.0
LEVERAGE = 5
FEE_RT = 0.0008  # Kraken maker fees ~0.04% × 2 sides
DAYS_BACK = 30

# Gate V4 (RSI + ATR seuls) — calculated on 4h aggregated bars
RSI_MIN, RSI_MAX = 36.0, 66.0
ATR_MIN, ATR_MAX = 1.12, 2.17


def fetch_binance(pair, days=DAYS_BACK):
    cache = CACHE_DIR / f"binance_{pair}_1min_{days}d.json"
    if cache.exists() and (time.time() - cache.stat().st_mtime) < 6 * 3600:
        return json.loads(cache.read_text())
    out = []
    end_ms = int(time.time() * 1000)
    cursor = end_ms - days * 86400 * 1000
    while cursor < end_ms:
        url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=1m&startTime={cursor}&endTime={end_ms}&limit=1000"
        try:
            d = json.loads(urllib.request.urlopen(url, timeout=20).read())
        except Exception as e:
            print(f"  fetch err {pair}: {e}"); break
        if not d: break
        out.extend([[int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in d])
        last_close = int(d[-1][6])
        if last_close <= cursor: break
        cursor = last_close + 1
        if len(d) < 1000: break
        time.sleep(0.12)
    cache.write_text(json.dumps(out))
    return out


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


def resample_4h(candles):
    bucket_ms = 4*3600*1000
    out, cur, o_, h_, l_, c_ = [], None, None, None, None, None
    for k in candles:
        ts, o, h, l, c, _ = k
        b = (ts // bucket_ms) * bucket_ms
        if cur is None: cur=b; o_,h_,l_,c_ = o,h,l,c
        elif b != cur:
            out.append([cur, o_, h_, l_, c_])
            cur=b; o_,h_,l_,c_ = o,h,l,c
        else:
            h_ = max(h_, h); l_ = min(l_, l); c_ = c
    if cur is not None: out.append([cur, o_, h_, l_, c_])
    return out


def simulate_grid(candles, spacing_pct, n_levels, capital=CAPITAL_PER_PAIR, gate=True):
    if len(candles) < 200: return None
    ts = [c[0] for c in candles]
    h = [c[2] for c in candles]; l = [c[3] for c in candles]; cl = [c[4] for c in candles]

    # Gate from 4h aggregation
    h4 = resample_4h(candles)
    h4c = [k[4] for k in h4]; h4h = [k[2] for k in h4]; h4l = [k[3] for k in h4]
    h4_rsi = rsi_series(h4c); h4_atrp = atr_pct(h4h, h4l, h4c)
    h4_gate = [(k[0], (h4_rsi[i] is not None and h4_atrp[i] is not None
                       and RSI_MIN <= h4_rsi[i] <= RSI_MAX
                       and ATR_MIN <= h4_atrp[i] <= ATR_MAX)) for i, k in enumerate(h4)]

    notional = capital * LEVERAGE
    grid = None; rts = []; fills_b = fills_s = 0
    opens = closes = 0
    equity_curve = []  # for DD/Sharpe
    cur_realized = 0.0
    gate_idx = 0

    for i in range(20, len(candles)):
        bar_h, bar_l, bar_c = h[i], l[i], cl[i]
        while gate_idx + 1 < len(h4_gate) and h4_gate[gate_idx+1][0] <= ts[i]:
            gate_idx += 1
        g_open = h4_gate[gate_idx][1] if gate_idx < len(h4_gate) else False
        if not gate: g_open = True

        if grid is None and g_open:
            center = bar_c
            size_per = (notional / n_levels) / center
            levels = []
            for k in range(n_levels):
                offset = (k - n_levels/2 + 0.5) * spacing_pct
                price = center * (1 + offset)
                side = "buy" if offset < 0 else "sell"
                levels.append({"price": price, "side": side,
                               "status": "PLACED" if side == "buy" else "WAITING"})
            grid = {"center": center, "levels": levels, "pos": 0.0, "entry_avg": 0.0,
                    "size_per": size_per}
            opens += 1

        if grid is not None and not g_open and grid["pos"] < 1e-9:
            grid = None; closes += 1; equity_curve.append(cur_realized); continue
        # Grid SL -3% from center (production behavior)
        if grid is not None and bar_l <= grid["center"] * 0.97 and grid["pos"] > 0:
            pnl = grid["pos"] * (grid["center"]*0.97 - grid["entry_avg"]) - FEE_RT * grid["pos"] * grid["center"]*0.97
            cur_realized += pnl; grid["pos"] = 0
            grid = None; closes += 1; equity_curve.append(cur_realized); continue
        if grid is None:
            equity_curve.append(cur_realized); continue

        for lvl in grid["levels"]:
            if lvl["status"] != "PLACED": continue
            if lvl["side"] == "buy" and bar_l <= lvl["price"]:
                fp = lvl["price"]
                new_total = grid["pos"] + grid["size_per"]
                grid["entry_avg"] = (grid["entry_avg"]*grid["pos"] + fp*grid["size_per"]) / new_total
                grid["pos"] = new_total
                lvl["status"] = "FILLED_BUY"; fills_b += 1
                # Arm a sell at next level above
                next_sell = fp * (1 + spacing_pct)
                found = False
                for s in grid["levels"]:
                    if s["status"] == "WAITING" and abs(s["price"] - next_sell)/next_sell < 0.005:
                        s["status"] = "PLACED"; found = True; break
                if not found:
                    grid["levels"].append({"price": next_sell, "side": "sell", "status": "PLACED"})
            elif lvl["side"] == "sell" and bar_h >= lvl["price"] and grid["pos"] >= grid["size_per"] - 1e-9:
                fp = lvl["price"]
                pnl = grid["size_per"] * (fp - grid["entry_avg"]) - FEE_RT * grid["size_per"] * fp
                cur_realized += pnl
                grid["pos"] -= grid["size_per"]
                if grid["pos"] < 1e-9: grid["pos"] = 0
                lvl["status"] = "FILLED_SELL"; fills_s += 1
                rts.append(pnl)
        equity_curve.append(cur_realized)

    # Close remaining position
    if grid is not None and grid["pos"] > 0:
        pnl = grid["pos"] * (cl[-1] - grid["entry_avg"]) - FEE_RT * grid["pos"] * cl[-1]
        cur_realized += pnl
        rts.append(pnl)

    # Stats
    if not equity_curve: equity_curve = [0]
    peak = equity_curve[0]
    max_dd = 0
    for e in equity_curve:
        if e > peak: peak = e
        dd = peak - e
        if dd > max_dd: max_dd = dd

    dur_days = (ts[-1] - ts[0]) / 86400000
    return {
        "rts": len(rts), "fills_b": fills_b, "fills_s": fills_s,
        "opens": opens, "closes": closes,
        "pnl_net": round(cur_realized, 4),
        "pnl_pct": round(cur_realized / capital * 100, 2),
        "annualized": round(cur_realized / capital * 100 * 365 / dur_days, 1) if dur_days else 0,
        "max_dd": round(max_dd, 4),
        "calmar": round((cur_realized / max(max_dd, 0.01)) * (365/dur_days), 2) if dur_days else 0,
        "avg_pnl_rt": round(cur_realized/len(rts), 4) if rts else 0,
        "fills_per_day": round((fills_b + fills_s) / max(dur_days, 0.001), 2),
        "dur_days": round(dur_days, 1),
    }


def main():
    print(f"Comprehensive sweep — {len(PAIRS)} pairs × {len(SPACINGS)} spacings × {len(LEVELS_LIST)} levels = {len(PAIRS)*len(SPACINGS)*len(LEVELS_LIST)} combos")
    print(f"Fees: {FEE_RT*100:.2f}% RT  |  Capital/pair: ${CAPITAL_PER_PAIR}  |  Window: {DAYS_BACK}d 1min\n")

    cache_data = {}
    for label, pair in PAIRS.items():
        print(f"loading {label} ({pair})...")
        c = fetch_binance(pair, days=DAYS_BACK)
        if c and len(c) >= 1000:
            cache_data[label] = c
            print(f"  {len(c)} candles ({(c[-1][0]-c[0][0])/86400000:.1f}d)")
        else:
            print(f"  FAIL")

    results = []
    print(f"\nRunning {len(cache_data)} × {len(SPACINGS)} × {len(LEVELS_LIST)} = {len(cache_data)*len(SPACINGS)*len(LEVELS_LIST)} simulations...\n")
    for label, candles in cache_data.items():
        for sp in SPACINGS:
            for lv in LEVELS_LIST:
                r = simulate_grid(candles, sp, lv)
                if r is None: continue
                r["pair"] = label; r["spacing"] = sp; r["levels"] = lv
                results.append(r)

    # Sort by net PnL desc
    results.sort(key=lambda x: x["pnl_net"], reverse=True)

    print("=== TOP 20 par PnL net 30d ===")
    print(f"{'pair':5} {'sp%':6} {'lv':3} {'RT':4} {'fills/d':8} {'PnL$':9} {'PnL%':7} {'maxDD$':8} {'Calmar':7} {'annual%':9}")
    for r in results[:20]:
        print(f"{r['pair']:5} {r['spacing']*100:5.2f}% {r['levels']:2}  {r['rts']:3}  {r['fills_per_day']:6}  {r['pnl_net']:+8.3f}  {r['pnl_pct']:+6.2f}%  {r['max_dd']:7.3f}  {r['calmar']:6}  {r['annualized']:+8.1f}%")

    # Cross-pair top-1
    best_per_pair = {}
    for r in results:
        if r["pair"] not in best_per_pair or r["pnl_net"] > best_per_pair[r["pair"]]["pnl_net"]:
            best_per_pair[r["pair"]] = r

    print("\n=== Best per pair ===")
    for p, r in sorted(best_per_pair.items(), key=lambda x: -x[1]["pnl_net"]):
        print(f"  {p:5} sp={r['spacing']*100:.1f}% lv={r['levels']} → RT={r['rts']} PnL=${r['pnl_net']:+.2f} ({r['pnl_pct']:+.1f}%) Calmar={r['calmar']}")

    # Portfolio: top 3 pairs combined
    print("\n=== Portfolio top-3 (sum) ===")
    sorted_pairs = sorted(best_per_pair.values(), key=lambda x: -x["pnl_net"])
    for n in [2, 3, 4]:
        top = sorted_pairs[:n]
        if len(top) < n: continue
        total_pnl = sum(r["pnl_net"] for r in top)
        total_cap = n * CAPITAL_PER_PAIR
        total_rt = sum(r["rts"] for r in top)
        total_fills = sum((r["fills_b"]+r["fills_s"]) for r in top)
        pairs_used = ", ".join(r["pair"] for r in top)
        print(f"  Top-{n}: {pairs_used} → ${total_pnl:+.2f}/{total_cap}$ = {total_pnl/total_cap*100:+.2f}% net, {total_rt} RT, {total_fills} fills")

    out = Path(__file__).parent / "comprehensive_sweep_results.json"
    out.write_text(json.dumps({"generated_at": datetime.utcnow().isoformat(),
                               "config": {"fee_rt": FEE_RT, "capital_per_pair": CAPITAL_PER_PAIR, "days": DAYS_BACK},
                               "top20": results[:20], "best_per_pair": best_per_pair,
                               "all_results": results}, indent=2))
    print(f"\nFull: {out}")


if __name__ == "__main__":
    main()

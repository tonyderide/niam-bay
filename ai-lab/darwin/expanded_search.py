#!/usr/bin/env python3
"""Expanded search: 12 pairs × grid sweep + Darwin skill evolution.

New pairs added: AVAX, MATIC, XRP, NEAR, OP, ARB (+ existing 6).
Goal: find pairs/configs that beat current top (DOT 1.5%/4, LINK 3%/4, ADA 3%/4).
"""
import json, time, urllib.request, sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from agent import create_random_agent, SKILL_POOL
from arena import Arena
from evolution import select_survivors, evolve_generation

CACHE_DIR = Path(__file__).parent / "data_cache"

# Existing + new pairs
PAIRS = {
    "LINK": "LINKUSDT", "SOL": "SOLUSDT", "DOT": "DOTUSDT",
    "BTC": "BTCUSDT", "ETH": "ETHUSDT", "ADA": "ADAUSDT",
    "AVAX": "AVAXUSDT", "XRP": "XRPUSDT", "NEAR": "NEARUSDT",
    "OP": "OPUSDT", "ARB": "ARBUSDT", "MATIC": "POLUSDT",
}
NEW_PAIRS = ["AVAX", "XRP", "NEAR", "OP", "ARB", "MATIC"]

# Grid sweep params
SPACINGS = [0.005, 0.008, 0.010, 0.015, 0.020, 0.025, 0.030]
LEVELS_LIST = [4, 6]
CAPITAL = 46.0
LEVERAGE = 7  # match Option B
FEE_RT = 0.0008
DAYS_BACK = 30

RSI_MIN, RSI_MAX = 36.0, 66.0
ATR_MIN, ATR_MAX = 1.12, 2.17

# Darwin params
POP_SIZE = 60
GENERATIONS = 40
MUTATION_RATE = 0.25
KILL_RATIO = 0.3
NUM_SKILLS_INIT = 5


def fetch_binance(pair, days=DAYS_BACK):
    cache = CACHE_DIR / f"binance_{pair}_1min_{days}d.json"
    if cache.exists() and (time.time() - cache.stat().st_mtime) < 12 * 3600:
        return json.loads(cache.read_text())
    out = []
    end_ms = int(time.time() * 1000)
    cursor = end_ms - days * 86400 * 1000
    while cursor < end_ms:
        url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=1m&startTime={cursor}&endTime={end_ms}&limit=1000"
        try:
            d = json.loads(urllib.request.urlopen(url, timeout=20).read())
        except Exception as e:
            print(f"  err {pair}: {e}"); break
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


def simulate_grid(candles, spacing, n_levels, capital=CAPITAL):
    if len(candles) < 200: return None
    ts = [c[0] for c in candles]; h = [c[2] for c in candles]
    l = [c[3] for c in candles]; cl = [c[4] for c in candles]

    h4 = resample_4h(candles)
    h4c = [k[4] for k in h4]; h4h = [k[2] for k in h4]; h4l = [k[3] for k in h4]
    h4_rsi = rsi_series(h4c); h4_atrp = atr_pct(h4h, h4l, h4c)
    h4_gate = [(k[0], (h4_rsi[i] is not None and h4_atrp[i] is not None
                       and RSI_MIN <= h4_rsi[i] <= RSI_MAX
                       and ATR_MIN <= h4_atrp[i] <= ATR_MAX)) for i, k in enumerate(h4)]

    notional = capital * LEVERAGE
    grid = None; rts = []; fills_b = fills_s = 0
    cur_realized = 0.0; gate_idx = 0

    for i in range(20, len(candles)):
        bar_h, bar_l, bar_c = h[i], l[i], cl[i]
        while gate_idx + 1 < len(h4_gate) and h4_gate[gate_idx+1][0] <= ts[i]:
            gate_idx += 1
        g_open = h4_gate[gate_idx][1] if gate_idx < len(h4_gate) else False

        if grid is None and g_open:
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

    dur_days = (ts[-1] - ts[0]) / 86400000
    return {
        "rts": len(rts), "fills_b": fills_b, "fills_s": fills_s,
        "pnl_net": round(cur_realized, 4),
        "pnl_pct": round(cur_realized / capital * 100, 2),
        "fills_per_day": round((fills_b + fills_s) / max(dur_days, 0.001), 2),
    }


def darwin_one(label, candles):
    if not candles or len(candles) < 800: return None
    raw_candles = [{"timestamp": int(k[0]), "open": float(k[1]), "high": float(k[2]),
                    "low": float(k[3]), "close": float(k[4]), "volume": float(k[5])} for k in candles]
    q_size = len(raw_candles) // 4
    quarters = [raw_candles[i*q_size:(i+1)*q_size] for i in range(4)]

    agents = [create_random_agent(num_skills=NUM_SKILLS_INIT, generation=0) for _ in range(POP_SIZE)]
    arena = Arena(candles=quarters[0])
    for gen in range(GENERATIONS):
        arena.evaluate(agents)
        select_survivors(agents, KILL_RATIO)
        agents = evolve_generation(agents, target_size=POP_SIZE, kill_ratio=0, mutation_rate=MUTATION_RATE)

    for a in agents: a.alive = True
    arena.evaluate(agents)
    q_pnl = {a.agent_id: {"Q1": a.fitness} for a in agents}
    for qi in range(1, 4):
        ta = Arena(candles=quarters[qi]); ta.evaluate(agents)
        for a in agents:
            q_pnl[a.agent_id][f"Q{qi+1}"] = a.fitness

    best = max(agents, key=lambda a: (sum(1 for v in q_pnl[a.agent_id].values() if v>0), sum(q_pnl[a.agent_id].values())))
    bq = q_pnl[best.agent_id]
    pos_q = sum(1 for v in bq.values() if v>0)
    return {"label": label, "skills": best.skills,
            "quarters": {k: round(v, 2) for k, v in bq.items()},
            "positive_quarters": pos_q,
            "total_pnl": round(sum(bq.values()), 2)}


def main():
    print(f"Expanded search — {len(PAIRS)} pairs (6 nouveaux: {NEW_PAIRS})\n")

    cache_data = {}
    for label, pair in PAIRS.items():
        is_new = label in NEW_PAIRS
        if is_new:
            print(f"fetching new pair {label} ({pair})...")
        c = fetch_binance(pair, days=DAYS_BACK)
        if c and len(c) >= 1000:
            cache_data[label] = c
            if is_new: print(f"  {len(c)} candles ({(c[-1][0]-c[0][0])/86400000:.1f}d)")
        else:
            print(f"  FAIL {label}")

    # PART 1: Grid sweep on ALL pairs
    print(f"\n=== PART 1: Grid sweep on {len(cache_data)} pairs ===")
    grid_results = []
    for label, candles in cache_data.items():
        for sp in SPACINGS:
            for lv in LEVELS_LIST:
                r = simulate_grid(candles, sp, lv)
                if r is None: continue
                r["pair"] = label; r["spacing"] = sp; r["levels"] = lv
                grid_results.append(r)

    grid_results.sort(key=lambda x: x["pnl_net"], reverse=True)

    # Best per pair
    best_per_pair = {}
    for r in grid_results:
        if r["pair"] not in best_per_pair or r["pnl_net"] > best_per_pair[r["pair"]]["pnl_net"]:
            best_per_pair[r["pair"]] = r

    print("\n  Best grid config per pair (lev=7, fees 0.08%, 30d):")
    for p, r in sorted(best_per_pair.items(), key=lambda x: -x[1]["pnl_net"]):
        mark = " ★ NEW" if p in NEW_PAIRS else ""
        print(f"    {p:6} sp={r['spacing']*100:.1f}% lv={r['levels']} → RT={r['rts']:3} fills/d={r['fills_per_day']:.2f} PnL=${r['pnl_net']:+.2f} ({r['pnl_pct']:+.1f}%){mark}")

    # PART 2: Darwin skill search on NEW pairs only (existing already done)
    print(f"\n=== PART 2: Darwin skills on {len(NEW_PAIRS)} new pairs ===")
    darwin_results = []
    for label in NEW_PAIRS:
        if label not in cache_data: continue
        print(f"  {label}...")
        t0 = time.time()
        r = darwin_one(label, cache_data[label])
        if r:
            darwin_results.append(r)
            print(f"    done in {time.time()-t0:.0f}s | best={r['positive_quarters']}/4Q tot=${r['total_pnl']:+.2f}")
            print(f"    skills: {list(r['skills'].keys()) if isinstance(r['skills'], dict) else r['skills']}")
            print(f"    quarters: {r['quarters']}")

    darwin_results.sort(key=lambda x: (x["positive_quarters"], x["total_pnl"]), reverse=True)

    # SUMMARY
    print("\n=== SUMMARY: vs Current Option B (DOT 1.5%/4 + LINK 3%/4 + ADA 3%/4 @ 7x) ===")
    current_pairs = ["DOT", "LINK", "ADA"]
    current_total = sum(best_per_pair.get(p, {}).get("pnl_net", 0) for p in current_pairs)
    print(f"  Current portfolio top-3: ${current_total:+.2f}/30d")
    print(f"\n  Candidates that BEAT current top-3 components:")
    base_threshold = min(best_per_pair[p]["pnl_net"] for p in current_pairs if p in best_per_pair)
    for p, r in sorted(best_per_pair.items(), key=lambda x: -x[1]["pnl_net"]):
        if r["pnl_net"] > base_threshold and p not in current_pairs:
            print(f"    {p:6} sp={r['spacing']*100:.1f}% lv={r['levels']} → ${r['pnl_net']:+.2f} (beats min current = ${base_threshold:+.2f})")

    out = Path(__file__).parent / "expanded_search_results.json"
    out.write_text(json.dumps({"generated_at": datetime.utcnow().isoformat(),
                               "grid_best_per_pair": best_per_pair,
                               "grid_top_20": grid_results[:20],
                               "darwin_new_pairs": darwin_results}, indent=2))
    print(f"\nFull: {out}")


if __name__ == "__main__":
    main()

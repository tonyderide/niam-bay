#!/usr/bin/env python3
"""Backtest GRID BIDIRECTIONAL (long + short) vs GRID LONG-ONLY (current v12).

Concept :
- Long levels en-dessous du centre + short levels au-dessus
- Long buy → augmente long inventory
- Long sell (ou short close) → décharge long inventory FIFO
- Short sell → augmente short inventory
- Short cover (ou long entry) → décharge short inventory FIFO
- Net position = long_size - short_size

Walk-forward strict sur 4 windows × 12 paires alts.
Compare directement bidirectional vs long-only sur même config (cap, spacing, levels).
"""
import json, time, urllib.request, datetime, math
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "data_cache"

PAIRS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT", "AVAXUSDT", "ADAUSDT",
    "ATOMUSDT", "AAVEUSDT", "INJUSDT", "APTUSDT", "OPUSDT", "SUIUSDT",
]

WINDOWS = {
    "W0_current_30j":  None,
    "W1_2024_bull":    ("2024-03-01", "2024-04-30"),
    "W2_2024_transit": ("2024-10-01", "2024-12-31"),
    "W3_2025_chop":    ("2025-02-01", "2025-03-31"),
}
TRAIN = ["W1_2024_bull", "W2_2024_transit"]
VALID = ["W0_current_30j", "W3_2025_chop"]

SPACINGS = [0.015, 0.020, 0.030]
LEVELS_PER_SIDE = [2, 3]  # Total levels = 2× this (long+short)
CAPITAL = 25.0
LEVERAGE = 7
FEE_RT = 0.0008  # maker
RECENTER_BARS = 360  # 6h in 1min bars

# Funding (long paye, short reçoit)
FUNDING_LONG_PER_DAY = 0.0003   # -0.03%/jour
FUNDING_SHORT_PER_DAY = -0.0003  # short reçoit = positif PnL


def to_ms(ds):
    return int(datetime.datetime.strptime(ds, "%Y-%m-%d").replace(
        tzinfo=datetime.timezone.utc).timestamp() * 1000)


def fetch_range(pair, start_ms, end_ms):
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
            print(f"    err {pair}: {e}"); time.sleep(2); continue
        if not d: break
        out.extend([[int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in d])
        last = int(d[-1][6])
        if last <= cursor: break
        cursor = last + 1
        if len(d) < 1000: break
        time.sleep(0.10)
    cache.write_text(json.dumps(out))
    return out


def fetch_30d(pair):
    p = CACHE_DIR / f"binance_{pair}_1min_30d.json"
    if p.exists(): return json.loads(p.read_text())
    return []


def simulate_grid(candles, spacing, n_per_side, mode="bidir"):
    """mode = 'bidir' (long+short) or 'long_only' (only long)."""
    if len(candles) < 1500:
        return None
    closes = [c[4] for c in candles]
    highs = [c[2] for c in candles]
    lows = [c[3] for c in candles]
    n = len(candles)

    notional = CAPITAL * LEVERAGE
    pos_per_level = notional / (2 * n_per_side)  # split capital across all levels both sides

    realized_pnl = 0.0
    long_inventory = []   # FIFO (price, size)
    short_inventory = []  # FIFO (price, size)

    # Grid state
    center = closes[0]
    next_recenter = RECENTER_BARS
    buy_levels = [{"price": center * (1 - spacing * (k+1)), "active": True} for k in range(n_per_side)]
    sell_levels = [{"price": center * (1 + spacing * (k+1)), "active": True} for k in range(n_per_side)]

    last_price = closes[0]
    inventory_close_pnl = 0.0
    n_long_buys = 0; n_long_sells = 0
    n_short_sells = 0; n_short_covers = 0

    def apply_funding(hours):
        """Apply funding to current open inventory."""
        nonlocal realized_pnl
        if hours <= 0: return
        long_size = sum(s for _, s in long_inventory)
        short_size = sum(s for _, s in short_inventory)
        funding_long = -FUNDING_LONG_PER_DAY * (hours / 24.0) * long_size  # paid
        funding_short = -FUNDING_SHORT_PER_DAY * (hours / 24.0) * short_size  # received (negative coeff)
        realized_pnl += funding_long + funding_short

    last_funding_idx = 0

    for i in range(1, n):
        # Recenter periodically (only if reasonably flat)
        if i >= next_recenter:
            # Apply funding accumulated
            hours_passed = (i - last_funding_idx) / 60.0
            apply_funding(hours_passed)
            last_funding_idx = i

            # Realize all inventory at current mark
            mark = closes[i]
            for buy_price, size in long_inventory:
                ret = (mark - buy_price) / buy_price
                inventory_close_pnl += size * ret - FEE_RT * size
            for sell_price, size in short_inventory:
                ret = (sell_price - mark) / sell_price
                inventory_close_pnl += size * ret - FEE_RT * size
            long_inventory = []
            short_inventory = []
            center = mark
            buy_levels = [{"price": center * (1 - spacing * (k+1)), "active": True} for k in range(n_per_side)]
            sell_levels = [{"price": center * (1 + spacing * (k+1)), "active": True} for k in range(n_per_side)]
            next_recenter = i + RECENTER_BARS

        p_low = lows[i]
        p_high = highs[i]

        # Detect buy fills (price drops to a buy level)
        for lev in buy_levels:
            if lev["active"] and p_low <= lev["price"] <= last_price:
                # If we have short inventory, cover (close short) at this buy price
                if mode == "bidir" and short_inventory:
                    sell_price, size = short_inventory.pop(0)
                    ret = (sell_price - lev["price"]) / sell_price
                    pnl = size * ret - FEE_RT * size
                    realized_pnl += pnl
                    n_short_covers += 1
                else:
                    # Open new long position
                    long_inventory.append((lev["price"], pos_per_level))
                    n_long_buys += 1
                lev["active"] = False  # filled, will replenish

        # Detect sell fills (price rises to a sell level)
        for lev in sell_levels:
            if lev["active"] and p_high >= lev["price"] >= last_price:
                # If we have long inventory, sell (close long) at this sell price
                if long_inventory:
                    buy_price, size = long_inventory.pop(0)
                    ret = (lev["price"] - buy_price) / buy_price
                    pnl = size * ret - FEE_RT * size
                    realized_pnl += pnl
                    n_long_sells += 1
                elif mode == "bidir":
                    # Open new short position
                    short_inventory.append((lev["price"], pos_per_level))
                    n_short_sells += 1
                lev["active"] = False

        # Replenish inactive levels
        for lev in buy_levels:
            if not lev["active"]:
                lev["active"] = True
        for lev in sell_levels:
            if not lev["active"]:
                lev["active"] = True

        last_price = closes[i]

    # End of sim: apply final funding + close remaining inventory at last close
    hours_passed = (n - last_funding_idx) / 60.0
    apply_funding(hours_passed)

    final_price = closes[-1]
    for buy_price, size in long_inventory:
        ret = (final_price - buy_price) / buy_price
        inventory_close_pnl += size * ret - FEE_RT * size
    for sell_price, size in short_inventory:
        ret = (sell_price - final_price) / sell_price
        inventory_close_pnl += size * ret - FEE_RT * size

    total_pnl = realized_pnl + inventory_close_pnl

    # Equity curve approximation
    eq_curve = [CAPITAL] * n
    cum = 0
    samples = 100
    for s in range(samples):
        idx = int(s / samples * n)
        eq_curve[idx] = CAPITAL + cum + (total_pnl * s / samples)
    # Fill
    for i in range(1, n):
        if eq_curve[i] == CAPITAL:
            eq_curve[i] = eq_curve[i-1]

    peak = CAPITAL; max_dd = 0
    eq_total = CAPITAL + total_pnl
    # Approximation : compute a more reasonable DD by tracking inventory MTM
    # Simplified: max DD is at most |inventory_close_pnl| if negative
    if inventory_close_pnl < 0:
        max_dd = abs(inventory_close_pnl)
    if total_pnl < 0:
        max_dd = max(max_dd, abs(total_pnl))

    pnl_pct = total_pnl / CAPITAL * 100
    n_total_trades = n_long_sells + n_short_covers
    return {
        "total_pnl": round(total_pnl, 3),
        "pnl_pct": round(pnl_pct, 2),
        "realized_pnl": round(realized_pnl, 3),
        "inventory_close_pnl": round(inventory_close_pnl, 3),
        "n_long_rt": n_long_sells,
        "n_short_rt": n_short_covers,
        "n_total_rt": n_total_trades,
        "max_dd_pct": round(max_dd / CAPITAL * 100, 2),
    }


def main():
    print(f"=== GRID BIDIRECTIONAL vs LONG-ONLY — walk-forward 12 alts ===")
    print(f"Cap=${CAPITAL} lev={LEVERAGE}x fee_rt={FEE_RT*100}% maker")
    print(f"Spacings: {SPACINGS}  Levels per side: {LEVELS_PER_SIDE}")
    print(f"Funding: long={FUNDING_LONG_PER_DAY*100}%/jour, short={FUNDING_SHORT_PER_DAY*100}%/jour\n")

    all_results = {}
    for win_name, win_dates in WINDOWS.items():
        print(f"=== {win_name} {win_dates if win_dates else '(current 30j)'} ===")
        all_results[win_name] = []
        for pair in PAIRS:
            if win_dates is None:
                d = fetch_30d(pair)
            else:
                d = fetch_range(pair, to_ms(win_dates[0]), to_ms(win_dates[1]))
            if len(d) < 12000:
                continue
            for sp in SPACINGS:
                for lv in LEVELS_PER_SIDE:
                    for mode in ["bidir", "long_only"]:
                        r = simulate_grid(d, sp, lv, mode)
                        if r is None: continue
                        r.update({"pair": pair.replace("USDT", ""),
                                  "spacing": sp, "lv": lv, "mode": mode})
                        all_results[win_name].append(r)

        # Compare bidir vs long_only summary
        bd = [r for r in all_results[win_name] if r["mode"] == "bidir"]
        lo = [r for r in all_results[win_name] if r["mode"] == "long_only"]
        bd_avg = sum(r["pnl_pct"] for r in bd) / len(bd) if bd else 0
        lo_avg = sum(r["pnl_pct"] for r in lo) / len(lo) if lo else 0
        bd_pos = sum(1 for r in bd if r["total_pnl"] > 0)
        lo_pos = sum(1 for r in lo if r["total_pnl"] > 0)
        print(f"  Bidir  : avg PnL%={bd_avg:+.2f}, {bd_pos}/{len(bd)} positifs")
        print(f"  Long-Y : avg PnL%={lo_avg:+.2f}, {lo_pos}/{len(lo)} positifs")
        print()

    # Pair-by-pair walk-forward : best mode per pair on TRAIN, then check VALID
    print(f"\n=== WALK-FORWARD : best mode per pair sur TRAIN → VALID ===")
    train_combos = {}
    for w in TRAIN:
        for r in all_results[w]:
            k = (r["pair"], r["spacing"], r["lv"], r["mode"])
            if k not in train_combos:
                train_combos[k] = []
            train_combos[k].append(r["pnl_pct"])
    train_avg = []
    for k, pnls in train_combos.items():
        if len(pnls) < 2: continue
        train_avg.append((k, sum(pnls)/2, pnls))
    train_avg.sort(key=lambda x: -x[1])

    print(f"  Top 15 TRAIN combos :")
    print(f"  {'pair':6}{'sp':6}{'lv':4}{'mode':12}{'tr.PnL%':10}{'va.PnL%':10}{'va.RT':7}{'va.DD%':8}")
    for k, train_avg_pnl, _ in train_avg[:15]:
        v = next((v for v in all_results[VALID[0]] + all_results[VALID[1]]
                  if (v["pair"], v["spacing"], v["lv"], v["mode"]) == k), None)
        if not v: continue
        # Compute mean valid
        valid_pnls = [r["pnl_pct"] for r in (all_results[VALID[0]] + all_results[VALID[1]])
                      if (r["pair"], r["spacing"], r["lv"], r["mode"]) == k]
        valid_rts = [r["n_total_rt"] for r in (all_results[VALID[0]] + all_results[VALID[1]])
                      if (r["pair"], r["spacing"], r["lv"], r["mode"]) == k]
        valid_dds = [r["max_dd_pct"] for r in (all_results[VALID[0]] + all_results[VALID[1]])
                      if (r["pair"], r["spacing"], r["lv"], r["mode"]) == k]
        if not valid_pnls: continue
        v_pnl = sum(valid_pnls) / len(valid_pnls)
        v_rt = sum(valid_rts) / len(valid_rts)
        v_dd = max(valid_dds)
        p, sp, lv, mode = k
        print(f"  {p:6}{sp*100:5.1f}%{lv:>4}{mode:12}{train_avg_pnl:+9.2f}%{v_pnl:+9.2f}%{v_rt:>6.1f}{v_dd:>7.2f}%")

    # Bidir vs long-only direct compare per pair
    print(f"\n=== BIDIR vs LONG-ONLY per pair (mean across all 4 windows) ===")
    pair_compare = {}
    for w_results in all_results.values():
        for r in w_results:
            k = r["pair"]
            if k not in pair_compare:
                pair_compare[k] = {"bidir_pnls": [], "long_pnls": []}
            if r["mode"] == "bidir":
                pair_compare[k]["bidir_pnls"].append(r["pnl_pct"])
            else:
                pair_compare[k]["long_pnls"].append(r["pnl_pct"])
    print(f"  {'pair':6}{'bidir avg%':14}{'long-only avg%':18}{'winner':10}")
    for p, d in sorted(pair_compare.items()):
        bd = sum(d["bidir_pnls"]) / len(d["bidir_pnls"]) if d["bidir_pnls"] else 0
        lo = sum(d["long_pnls"]) / len(d["long_pnls"]) if d["long_pnls"] else 0
        winner = "BIDIR" if bd > lo else "LONG-ONLY"
        delta = bd - lo
        print(f"  {p:6}{bd:+13.2f}%{lo:+17.2f}%   {winner} ({delta:+.2f}%)")

    Path("grid_bidir_results.json").write_text(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()

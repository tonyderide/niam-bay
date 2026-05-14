#!/usr/bin/env python3
"""Adaptive Grid+Short v2 — bugs fixed + multi-window historical test.

Bugs fixed vs v1:
- L88: grid PnL now tracks FIFO inventory of buy fills (real cost basis)
- L124: on regime UP->DOWN switch, mark-to-market the remaining grid inventory at current price
- L156: on recenter, realize inventory at current mark (treats as exit + re-entry)

Tests on 3 historical windows :
  W1: 2024-03-01 to 2024-04-30 (BTC bull pur post-halving)
  W2: 2024-10-01 to 2024-12-31 (BTC transition / accumulation)
  W3: 2025-02-01 to 2025-03-31 (BTC chop range)
Plus W0 (current 30j) for reference.
"""
import json, time, urllib.request, datetime
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)

# Top candidates from v1 backtest + controls
PAIRS = ["INJUSDT", "APTUSDT", "OPUSDT", "SUIUSDT", "TIAUSDT",
         "LTCUSDT", "ATOMUSDT", "AVAXUSDT", "LINKUSDT", "AAVEUSDT"]

WINDOWS = {
    "W0_current_30j": None,  # use existing cache
    "W1_2024_bull":   ("2024-03-01", "2024-04-30"),
    "W2_2024_transit":("2024-10-01", "2024-12-31"),
    "W3_2025_chop":   ("2025-02-01", "2025-03-31"),
}

GRID_SPACING = 0.020   # 2% (best from v1)
SHORT_TRAIL = 0.030    # 3% (best from v1)
LEVELS = 4
CAPITAL = 25.0
LEVERAGE = 7
GRID_FEE_RT = 0.0008
SHORT_FEE_RT = 0.001


def to_ms(date_str):
    return int(datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(
        tzinfo=datetime.timezone.utc).timestamp() * 1000)


def fetch_binance_range(pair, start_ms, end_ms):
    """Fetch 1min OHLC between start_ms and end_ms (inclusive)."""
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
    """Last 30 days from cache (existing pre-cached data)."""
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


def ema(values, period):
    if len(values) < period: return [values[0]] * len(values)
    k = 2.0 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def simulate_v2(candles_1min, grid_spacing, short_trail):
    """Returns dict with full PnL breakdown and equity curve."""
    if len(candles_1min) < 12000:
        return None
    candles_1h = aggregate_1h(candles_1min)
    if len(candles_1h) < 220:
        return None
    closes_1h = [c[4] for c in candles_1h]
    ema50_1h = ema(closes_1h, 50)
    ema200_1h = ema(closes_1h, 200)
    n_hours = len(candles_1h)

    regime_1h = []
    for i in range(n_hours):
        if i < 200:
            regime_1h.append(0)
        else:
            regime_1h.append(1 if ema50_1h[i] > ema200_1h[i] else -1)

    notional = CAPITAL * LEVERAGE
    pos_per_level = notional / LEVELS

    closes_1m = [c[4] for c in candles_1min]
    highs_1m = [c[2] for c in candles_1min]
    lows_1m = [c[3] for c in candles_1min]
    n = len(candles_1min)

    # PnL tracking
    realized_pnl = 0.0
    pnl_curve = [0.0]  # cumulative realized PnL
    grid_pnl_realized = 0.0
    short_pnl_realized = 0.0
    inventory_close_pnl = 0.0  # PnL from forced inventory closes (recenter or regime switch)

    # Grid state with inventory tracking (FIFO queue of buy fills with price)
    grid_active = False
    grid_center = 0.0
    grid_buy_levels = []   # list of (level_price, status:'PLACED'|'FILLED')
    grid_sell_levels = []  # list of (level_price, status:'PLACED'|'FILLED')
    grid_inventory = []    # FIFO queue of (buy_price, size=pos_per_level)
    last_price = closes_1m[0]
    grid_recenter_at = 0
    n_grid_fills_b = 0
    n_grid_fills_s = 0

    # Short state
    short_active = False
    short_entry = 0.0
    short_low_since = 0.0
    n_shorts = 0

    # Switch counts
    n_switches = 0

    current_regime = 0

    def close_grid_inventory(realize_price):
        """Mark-to-market all open longs in inventory at realize_price."""
        nonlocal grid_inventory, inventory_close_pnl
        total = 0.0
        for buy_price, size in grid_inventory:
            ret = (realize_price - buy_price) / buy_price
            pnl = size * ret - SHORT_FEE_RT * size  # taker exit fee
            total += pnl
        grid_inventory = []
        inventory_close_pnl += total
        return total

    def reset_grid_levels(center_price):
        nonlocal grid_buy_levels, grid_sell_levels
        grid_buy_levels = [[center_price * (1 - grid_spacing * (k+1)), 'PLACED']
                          for k in range(LEVELS // 2)]
        grid_sell_levels = [[center_price * (1 + grid_spacing * (k+1)), 'PLACED']
                           for k in range(LEVELS // 2)]

    for i in range(1, n):
        hour_idx = min(i // 60, n_hours - 1)
        regime = regime_1h[hour_idx]
        price = closes_1m[i]
        p_low = lows_1m[i]
        p_high = highs_1m[i]

        # Detect regime change
        regime_changed = (regime != current_regime and regime != 0)
        if regime_changed:
            n_switches += 1
            if grid_active:
                # FIX L124: realize inventory at current price (not "flat")
                close_grid_inventory(price)
                grid_active = False
            if short_active:
                ret = (short_entry - price) / short_entry
                pnl = notional * ret - SHORT_FEE_RT * notional
                short_pnl_realized += pnl
                realized_pnl += pnl
                short_active = False
            current_regime = regime

        # Activate strategy
        if current_regime == 1 and not grid_active:
            grid_active = True
            grid_center = price
            reset_grid_levels(grid_center)
            grid_inventory = []
            grid_recenter_at = i + 360
        elif current_regime == -1 and not short_active:
            short_active = True
            short_entry = price
            short_low_since = price
            n_shorts += 1

        # Grid execution
        if grid_active:
            # FIX L156: on recenter, realize inventory at current price
            if i >= grid_recenter_at:
                close_grid_inventory(price)
                grid_center = price
                reset_grid_levels(grid_center)
                grid_recenter_at = i + 360

            # Detect buy fills (price drops to a buy level)
            for lev in grid_buy_levels:
                if lev[1] == 'PLACED' and p_low <= lev[0] <= last_price:
                    # Buy fill at lev[0]: add to inventory
                    grid_inventory.append((lev[0], pos_per_level))
                    n_grid_fills_b += 1
                    lev[1] = 'FILLED'
            # Detect sell fills (price rises to a sell level + we have inventory)
            for lev in grid_sell_levels:
                if lev[1] == 'PLACED' and p_high >= lev[0] >= last_price:
                    if grid_inventory:
                        # FIFO: pop oldest buy
                        buy_price, size = grid_inventory.pop(0)
                        ret = (lev[0] - buy_price) / buy_price
                        pnl = size * ret - GRID_FEE_RT * size
                        grid_pnl_realized += pnl
                        realized_pnl += pnl
                        n_grid_fills_s += 1
                    lev[1] = 'FILLED'
            # Replenish filled levels (grid logic: re-place after fill)
            for lev in grid_buy_levels:
                if lev[1] == 'FILLED':
                    lev[1] = 'PLACED'
            for lev in grid_sell_levels:
                if lev[1] == 'FILLED':
                    lev[1] = 'PLACED'

        # Short execution
        if short_active:
            if price < short_low_since:
                short_low_since = price
            stop = short_low_since * (1 + short_trail)
            if price >= stop:
                ret = (short_entry - price) / short_entry
                pnl = notional * ret - SHORT_FEE_RT * notional
                short_pnl_realized += pnl
                realized_pnl += pnl
                short_active = False

        last_price = price
        pnl_curve.append(realized_pnl)

    # End of sim: close any remaining open positions at last close
    final_price = closes_1m[-1]
    if grid_active:
        close_grid_inventory(final_price)
    if short_active:
        ret = (short_entry - final_price) / short_entry
        pnl = notional * ret - SHORT_FEE_RT * notional
        short_pnl_realized += pnl
        realized_pnl += pnl

    # Add inventory_close_pnl to total
    realized_pnl_total = realized_pnl + inventory_close_pnl

    # Compute drawdown on the equity curve
    eq = CAPITAL + realized_pnl_total
    peak = CAPITAL
    max_dd = 0.0
    for cumul in pnl_curve:
        e = CAPITAL + cumul
        if e > peak: peak = e
        if (peak - e) > max_dd: max_dd = peak - e

    pnl_pct = realized_pnl_total / CAPITAL * 100
    return {
        "pnl_total": round(realized_pnl_total, 3),
        "pnl_pct": round(pnl_pct, 2),
        "grid_pnl": round(grid_pnl_realized, 3),
        "short_pnl": round(short_pnl_realized, 3),
        "inventory_close_pnl": round(inventory_close_pnl, 3),
        "max_dd": round(max_dd, 3),
        "max_dd_pct": round(max_dd / CAPITAL * 100, 2),
        "calmar": round(pnl_pct / (max_dd / CAPITAL * 100), 2) if max_dd > 0 else 999,
        "n_switches": n_switches,
        "n_grid_buys": n_grid_fills_b,
        "n_grid_sells": n_grid_fills_s,
        "n_shorts": n_shorts,
    }


def main():
    print(f"Adaptive v2 (bugs fixed) — multi-window historical sweep")
    print(f"Pairs: {len(PAIRS)} | grid_spacing={GRID_SPACING*100}% short_trail={SHORT_TRAIL*100}% lev={LEVERAGE}x")
    print()

    all_results = {}

    for win_name, win_dates in WINDOWS.items():
        print(f"=== {win_name} {win_dates if win_dates else '(cache existing 30j)'} ===")
        all_results[win_name] = []
        if win_dates is None:
            # Use existing cache
            for pair in PAIRS:
                d = fetch_binance_30d(pair)
                if not d:
                    print(f"  SKIP {pair}: no cache")
                    continue
                r = simulate_v2(d, GRID_SPACING, SHORT_TRAIL)
                if r is None:
                    print(f"  SKIP {pair}: not enough data")
                    continue
                r["pair"] = pair.replace("USDT", "")
                all_results[win_name].append(r)
        else:
            start_ms = to_ms(win_dates[0])
            end_ms = to_ms(win_dates[1])
            for pair in PAIRS:
                print(f"  fetching {pair}...", end="", flush=True)
                d = fetch_binance_range(pair, start_ms, end_ms)
                print(f" {len(d)} candles")
                if len(d) < 12000:
                    print(f"  SKIP {pair}: not enough data")
                    continue
                r = simulate_v2(d, GRID_SPACING, SHORT_TRAIL)
                if r is None: continue
                r["pair"] = pair.replace("USDT", "")
                all_results[win_name].append(r)

        # Print summary for this window
        results = all_results[win_name]
        results.sort(key=lambda x: -x["pnl_total"])
        print(f"  Top results:")
        print(f"  {'pair':6}{'PnL$':9}{'PnL%':8}{'grid$':9}{'short$':9}{'invclose$':11}{'maxDD%':8}{'switches':9}")
        for r in results[:10]:
            print(f"  {r['pair']:6}{r['pnl_total']:+8.2f}{r['pnl_pct']:+7.2f}%{r['grid_pnl']:+8.2f}{r['short_pnl']:+8.2f}{r['inventory_close_pnl']:+10.2f}{r['max_dd_pct']:+7.2f}%{r['n_switches']:>8}")
        n_profitable = sum(1 for r in results if r["pnl_total"] > 0)
        print(f"  → {n_profitable}/{len(results)} pairs profitable")
        print()

    # Cross-window comparison for top pairs
    print("=== CROSS-WINDOW pour Top-5 candidates (INJ, APT, OP, SUI, TIA) ===")
    candidates = ["INJ", "APT", "OP", "SUI", "TIA"]
    print(f"{'pair':6}", end="")
    for w in WINDOWS:
        print(f"{w:>22}", end="")
    print()
    for c in candidates:
        print(f"{c:6}", end="")
        for w in WINDOWS:
            r = next((x for x in all_results[w] if x["pair"] == c), None)
            if r:
                print(f"{r['pnl_total']:+8.2f}({r['pnl_pct']:+5.1f}%)  ", end="")
            else:
                print(f"{'n/a':>22}", end="")
        print()

    Path("adaptive_sweep_v2_results.json").write_text(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()

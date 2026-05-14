#!/usr/bin/env python3
"""Grid backtest at 1min on current Martin config (LINK+DOT+SOL × 2.0% × 6 levels × $46).

Mesure: nombre de positions prises (fills + RT), profit cumulé, profit moyen par RT.
Tony rule: petit profit mais profit régulier.
"""
import json, time, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path

# ── Config Martin actuelle ──
PAIRS = {"LINK": "LINKUSDT", "SOL": "SOLUSDT", "DOT": "DOTUSDT"}  # Binance symbols
CAPITAL_PER_PAIR = 46.0  # USD margin
LEVERAGE = 5
SPACING_PCT = 2.0  # 2.0%
LEVELS = 6  # 6 levels (3 buy + 3 sell typically)
FEE_RT = 0.0008  # 0.04% × 2 fills = 0.08% round-trip

# Gate V4 (RSI + ATR seuls)
RSI_MIN, RSI_MAX = 36.0, 66.0
ATR_MIN, ATR_MAX = 1.12, 2.17

# Backtest window
DAYS_BACK = 30  # 30 jours de 1min = 43200 candles
BARS = DAYS_BACK * 1440


CACHE_DIR = Path(__file__).parent / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)


def fetch_binance_1min(pair, days=DAYS_BACK, use_cache=True, refresh_max_age_hours=6):
    """Paginated fetch of 1min OHLC from Binance. Caches to disk; refreshes if older than N hours."""
    cache_file = CACHE_DIR / f"binance_{pair}_1min_{days}d.json"
    if use_cache and cache_file.exists():
        age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
        if age_hours < refresh_max_age_hours:
            print(f"  cache hit {pair} (age {age_hours:.1f}h)")
            return json.loads(cache_file.read_text())

    out = []
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - days * 86400 * 1000
    cursor = start_ms
    while cursor < end_ms:
        url = (f"https://api.binance.com/api/v3/klines?symbol={pair}"
               f"&interval=1m&startTime={cursor}&endTime={end_ms}&limit=1000")
        try:
            d = json.loads(urllib.request.urlopen(url, timeout=20).read())
        except Exception as e:
            print(f"  fetch err {pair}: {e}")
            break
        if not d:
            break
        out.extend([[int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in d])
        last_close = int(d[-1][6])
        if last_close <= cursor:
            break
        cursor = last_close + 1
        if len(d) < 1000:
            break
        time.sleep(0.15)
    cache_file.write_text(json.dumps(out))
    print(f"  saved cache {cache_file.name} ({len(out)} candles)")
    return out


def rsi_series(closes, period=14):
    out = [None] * len(closes)
    if len(closes) < period + 1:
        return out
    gains, losses = 0.0, 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        if d > 0: gains += d
        else: losses -= d
    avg_g, avg_l = gains / period, losses / period
    out[period] = 100 - 100 / (1 + (avg_g / avg_l)) if avg_l else 100
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        g = max(d, 0); l = max(-d, 0)
        avg_g = (avg_g * (period - 1) + g) / period
        avg_l = (avg_l * (period - 1) + l) / period
        out[i] = 100 - 100 / (1 + (avg_g / avg_l)) if avg_l else 100
    return out


def atr_pct_series(highs, lows, closes, period=14):
    """ATR as % of close."""
    out = [None] * len(closes)
    trs = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1])))
    if len(trs) < period:
        return out
    seed = sum(trs[:period]) / period
    out[period - 1] = (seed / closes[period - 1]) * 100 if closes[period-1] else None
    cur = seed
    for i in range(period, len(trs)):
        cur = (cur * (period - 1) + trs[i]) / period
        out[i] = (cur / closes[i]) * 100 if closes[i] else None
    return out


def resample_to_4h(candles):
    """Aggregate 1min candles to 4h candles. Returns [[ts_start, o, h, l, c], ...]"""
    bucket_ms = 4 * 3600 * 1000
    out = []
    cur_bucket = None
    o_, h_, l_, c_ = None, None, None, None
    for k in candles:
        ts, o, h, l, c, _ = k
        bucket = (ts // bucket_ms) * bucket_ms
        if cur_bucket is None:
            cur_bucket = bucket; o_, h_, l_, c_ = o, h, l, c
        elif bucket != cur_bucket:
            out.append([cur_bucket, o_, h_, l_, c_])
            cur_bucket = bucket; o_, h_, l_, c_ = o, h, l, c
        else:
            h_ = max(h_, h); l_ = min(l_, l); c_ = c
    if cur_bucket is not None:
        out.append([cur_bucket, o_, h_, l_, c_])
    return out


def simulate_grid(candles, pair_name):
    """Run 6-level neutral grid with V4 gate computed on 4h candles. Returns RT + PnL."""
    if len(candles) < 200:
        return None
    ts = [c[0] for c in candles]
    o = [c[1] for c in candles]; h = [c[2] for c in candles]; l = [c[3] for c in candles]; cl = [c[4] for c in candles]

    # Compute gate signals on 4h candles (matches prod behavior)
    h4 = resample_to_4h(candles)
    h4_close = [k[4] for k in h4]; h4_high = [k[2] for k in h4]; h4_low = [k[3] for k in h4]
    h4_rsi = rsi_series(h4_close)
    h4_atrp = atr_pct_series(h4_high, h4_low, h4_close)
    # Map: for each 1min ts, find the latest 4h gate snapshot
    h4_gate = []
    for idx, k in enumerate(h4):
        gate_open = (h4_rsi[idx] is not None and h4_atrp[idx] is not None
                     and RSI_MIN <= h4_rsi[idx] <= RSI_MAX
                     and ATR_MIN <= h4_atrp[idx] <= ATR_MAX)
        h4_gate.append((k[0], gate_open))

    grid = None  # active grid: {center, levels: [{price, side, status}], position_size, entry_avg, realized_pnl}
    rts = []
    fills_log = []
    grid_open_count = 0
    grid_close_count = 0

    notional = CAPITAL_PER_PAIR * LEVERAGE  # $46 × 5 = $230 total notional capacity
    size_per_level = notional / LEVELS / cl[0] if cl[0] else 0  # rough estimate, will adjust per grid

    gate_idx = 0
    for i in range(20, len(candles)):
        bar_high, bar_low, bar_close = h[i], l[i], cl[i]
        # Advance gate_idx to last 4h bucket whose start <= ts[i]
        while gate_idx + 1 < len(h4_gate) and h4_gate[gate_idx + 1][0] <= ts[i]:
            gate_idx += 1
        gate_open = h4_gate[gate_idx][1] if gate_idx < len(h4_gate) else False

        # 1. Open grid if gate OPEN and no active grid
        if grid is None and gate_open:
            center = bar_close
            size_per_level = (notional / LEVELS) / center
            levels = []
            for k in range(LEVELS):
                offset_pct = (k - LEVELS / 2 + 0.5) * SPACING_PCT / 100.0
                price = center * (1 + offset_pct)
                side = "buy" if offset_pct < 0 else "sell"
                # All buys placed initially; sells WAITING (only post above-center sells if room)
                levels.append({"price": price, "side": side, "status": "PLACED" if side == "buy" else "WAITING"})
            grid = {"center": center, "levels": levels, "position_size": 0.0, "entry_avg": 0.0,
                    "realized_pnl": 0.0, "started_at": ts[i]}
            grid_open_count += 1

        # 2. Match prod behavior: close grid only if gate CLOSED AND position_size == 0
        # Don't yank grids on every 1min gate flip — RSI is too volatile per-minute
        if grid is not None and not gate_open and grid["position_size"] < 1e-9:
            grid_close_count += 1
            grid = None
            continue
        # Grid SL: -3% from center (Martin prod)
        if grid is not None and bar_low <= grid["center"] * 0.97 and grid["position_size"] > 0:
            pnl = grid["position_size"] * (grid["center"] * 0.97 - grid["entry_avg"]) \
                - FEE_RT * grid["position_size"] * grid["center"] * 0.97
            grid["realized_pnl"] += pnl
            fills_log.append({"ts": ts[i], "pair": pair_name, "side": "SL-3pct",
                              "size": grid["position_size"], "price": grid["center"]*0.97, "pnl": pnl})
            grid["position_size"] = 0
            grid_close_count += 1
            grid = None
            continue

        if grid is None:
            continue

        # 3. Process fills within bar (low touches buy / high touches sell)
        for lvl in grid["levels"]:
            if lvl["status"] != "PLACED":
                continue
            if lvl["side"] == "buy" and bar_low <= lvl["price"]:
                # Buy filled
                fill_price = lvl["price"]
                cost = size_per_level * fill_price
                new_total = grid["position_size"] + size_per_level
                grid["entry_avg"] = (grid["entry_avg"] * grid["position_size"] + fill_price * size_per_level) / new_total
                grid["position_size"] = new_total
                lvl["status"] = "FILLED_BUY"
                fills_log.append({"ts": ts[i], "pair": pair_name, "side": "buy", "size": size_per_level,
                                  "price": fill_price})
                # Re-arm a sell at the next level above
                next_sell_price = fill_price * (1 + SPACING_PCT / 100.0)
                for s in grid["levels"]:
                    if s["status"] == "WAITING" and abs(s["price"] - next_sell_price) / next_sell_price < 0.005:
                        s["status"] = "PLACED"
                        break
                else:
                    grid["levels"].append({"price": next_sell_price, "side": "sell", "status": "PLACED"})

            elif lvl["side"] == "sell" and bar_high >= lvl["price"] and grid["position_size"] >= size_per_level - 1e-9:
                # Sell filled (TP)
                fill_price = lvl["price"]
                pnl = size_per_level * (fill_price - grid["entry_avg"]) - FEE_RT * size_per_level * fill_price
                grid["realized_pnl"] += pnl
                grid["position_size"] -= size_per_level
                if grid["position_size"] < 1e-9:
                    grid["position_size"] = 0.0
                lvl["status"] = "FILLED_SELL"
                rts.append({"ts": ts[i], "pair": pair_name, "pnl": pnl, "fill_price": fill_price,
                            "entry_avg": grid["entry_avg"]})
                fills_log.append({"ts": ts[i], "pair": pair_name, "side": "sell", "size": size_per_level,
                                  "price": fill_price, "pnl": pnl})

    # Close any remaining position at last bar
    if grid is not None and grid["position_size"] > 0:
        pnl = grid["position_size"] * (cl[-1] - grid["entry_avg"]) - FEE_RT * grid["position_size"] * cl[-1]
        grid["realized_pnl"] += pnl

    final_realized = (grid["realized_pnl"] if grid else 0) + sum(r["pnl"] for r in rts)
    duration_hours = (ts[-1] - ts[0]) / 3600000  # Binance ts is ms
    return {
        "pair": pair_name,
        "bars": len(candles),
        "duration_hours": round(duration_hours, 1),
        "duration_days": round(duration_hours / 24, 2),
        "rt_count": len(rts),
        "buy_fills": sum(1 for f in fills_log if f["side"] == "buy"),
        "sell_fills": sum(1 for f in fills_log if f["side"] == "sell"),
        "grid_opens": grid_open_count,
        "grid_closes": grid_close_count,
        "realized_pnl_usd": round(final_realized, 4),
        "avg_pnl_per_rt": round(final_realized / len(rts), 4) if rts else 0,
        "fills_per_day": round((sum(1 for f in fills_log if f["side"] in ("buy","sell"))) / max(duration_hours/24, 0.001), 2),
    }


def main():
    print(f"\nGrid Backtest 1min — Tony rule: petit profit mais profit régulier")
    print(f"Config: {LEVELS} levels × {SPACING_PCT}% spacing × ${CAPITAL_PER_PAIR}/pair × {LEVERAGE}x lev")
    print(f"Gate V4: RSI[{RSI_MIN},{RSI_MAX}] AND ATR%[{ATR_MIN},{ATR_MAX}]")
    print(f"Fees RT: {FEE_RT*100:.2f}%\n")

    summary = []
    for label, pair in PAIRS.items():
        print(f"[{datetime.utcnow().isoformat()}] fetching {pair} from Binance...")
        candles = fetch_binance_1min(pair, days=DAYS_BACK)
        if not candles:
            print(f"  SKIP {pair}: no data")
            continue
        print(f"  {pair}: {len(candles)} candles ({(candles[-1][0]-candles[0][0])/86400000:.1f} days)")
        r = simulate_grid(candles, label)
        if r:
            summary.append(r)
            print(f"  RT={r['rt_count']:3d} fills(b/s)={r['buy_fills']}/{r['sell_fills']} "
                  f"PnL=${r['realized_pnl_usd']:+.2f} avg/RT=${r['avg_pnl_per_rt']:+.4f} "
                  f"fills/day={r['fills_per_day']}")

    if not summary:
        print("\nNo results.")
        return

    print("\n=== AGGREGATE ===")
    total_rt = sum(r["rt_count"] for r in summary)
    total_pnl = sum(r["realized_pnl_usd"] for r in summary)
    total_capital = CAPITAL_PER_PAIR * len(summary)
    avg_days = sum(r["duration_days"] for r in summary) / len(summary)
    pnl_pct = total_pnl / total_capital * 100
    annualized = pnl_pct * (365 / avg_days) if avg_days > 0 else 0

    print(f"Window:          {avg_days:.1f} days × 1min candles")
    print(f"Total RTs:       {total_rt}")
    print(f"Total PnL:       ${total_pnl:+.4f} ({pnl_pct:+.2f}% on ${total_capital} capital)")
    print(f"Avg PnL per RT:  ${total_pnl/total_rt:+.4f}" if total_rt else "Avg PnL per RT:  N/A (0 RT)")
    print(f"Annualized:      {annualized:+.1f}%/an")
    print()
    for r in summary:
        print(f"  {r['pair']:6} : {r['rt_count']:3d} RT  ${r['realized_pnl_usd']:+.4f}  "
              f"{r['fills_per_day']} fills/day  (grid open/close: {r['grid_opens']}/{r['grid_closes']})")

    out_path = Path(__file__).parent / "grid_backtest_1min_results.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nFull results: {out_path}")


if __name__ == "__main__":
    main()

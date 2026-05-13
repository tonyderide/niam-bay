#!/usr/bin/env python3
"""ADCL (Anti-DCA Cooldown Lock) backtest — cycle 38 / 2026-05-13.

Goal: validate Tier 2 design proposed in cycle 37.
Replay the Option B test period (11/05 14h UTC -> 12/05 22h UTC, ~32h)
on DOT 1min candles with current Martin auto-unstuck logic, with and
without a 30 min cooldown lock on any buy level that was just trimmed.

Config matches Option B v9:
  - DOT 1.5% spacing, 4 levels, $25 capital, 7x leverage
  - auto-unstuck: trim 25% at -2%, trim 25% at -3%, full close at -4%
  - HARD STOP maxLoss at -10% of capital (-$2.50 per grid)

ADCL behavior:
  - When a trim fires at level N, mark level N + the immediate buy level
    below as paused for `cooldown_minutes` minutes
  - Skip placing fills at paused levels during the cooldown window
  - Cooldown clears automatically after the window expires

Output: side-by-side comparison of realized PnL, max drawdown,
number of trims, and number of HARD STOP triggers.
"""
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)

# ── Option B v9 config (DOT) — per memory.nb1 cycle 35 ──
# capital=$46 confirmed by HARD STOP value $4.60 = 10% maxLoss
SPACING_PCT = 1.5
LEVELS = 4
CAPITAL = 46.0
LEVERAGE = 7
FEE_RT_PCT = 0.08  # 0.04% * 2

# Auto-unstuck thresholds (% from grid center)
UNSTUCK_LVL1_PCT = 2.0   # trim 25%
UNSTUCK_LVL2_PCT = 3.0   # trim 25% more
UNSTUCK_FULL_PCT = 4.0   # close 100%
MAX_LOSS_PCT = 10.0      # HARD STOP on capital

# ── Replay window: Option B test period ──
# Deploy: 2026-05-11 13:00 UTC (approx, based on memory.nb1 deploy-0511:13h)
# End:    2026-05-12 22:00 UTC (50h test FIN per memory.nb1 status-0512:22h)
WINDOW_START_MS = int(datetime(2026, 5, 11, 13, 0, tzinfo=timezone.utc).timestamp() * 1000)
WINDOW_END_MS   = int(datetime(2026, 5, 12, 22, 0, tzinfo=timezone.utc).timestamp() * 1000)


def fetch_binance_1min(symbol, start_ms, end_ms):
    """Fetch 1min OHLC for a window from Binance public klines API. Cache to disk."""
    cache_file = CACHE_DIR / f"binance_{symbol}_1min_optionb.json"
    if cache_file.exists():
        age_h = (time.time() - cache_file.stat().st_mtime) / 3600
        if age_h < 24:
            print(f"  cache hit {symbol} (age {age_h:.1f}h)")
            return json.loads(cache_file.read_text())

    out, cursor = [], start_ms
    while cursor < end_ms:
        url = (f"https://api.binance.com/api/v3/klines?symbol={symbol}"
               f"&interval=1m&startTime={cursor}&endTime={end_ms}&limit=1000")
        try:
            d = json.loads(urllib.request.urlopen(url, timeout=20).read())
        except Exception as e:
            print(f"  fetch err {symbol}: {e}")
            break
        if not d:
            break
        out.extend([[int(k[0]), float(k[1]), float(k[2]), float(k[3]),
                     float(k[4]), float(k[5])] for k in d])
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


def simulate(candles, adcl_cooldown_min=0, mode="pause"):
    """Run the Option B DOT grid simulation. Returns metrics dict.

    adcl_cooldown_min: minutes of cooldown after a trim before the trimmed
                      buy levels can re-fill. 0 = original behavior (no ADCL).
    mode: "pause" = block for cooldown then resume; "cancel" = permanently cancel
          buy levels below the trim point; "recross" = resume only after price
          has crossed back above the level (mean-reversion confirmation).
    """
    if len(candles) < 10:
        return None

    notional_total = CAPITAL * LEVERAGE  # $175 total
    notional_per_level = notional_total / LEVELS  # ~$43.75
    max_loss_usd = CAPITAL * MAX_LOSS_PCT / 100.0  # $2.50

    # ── Set grid center at the first candle's close ──
    center = candles[0][4]
    # Levels symmetric around center: 2 buys below, 2 sells above (4 total)
    # Spacing: 1.5% per level
    level_prices = []
    for k in range(LEVELS):
        offset_pct = (k - LEVELS / 2 + 0.5) * SPACING_PCT / 100.0
        level_prices.append(center * (1 + offset_pct))
    # levels 0,1 = buys (below), 2,3 = sells (above)

    # State
    position_size = 0.0  # in units of DOT
    entry_avg = 0.0
    realized_pnl = 0.0
    level_filled = [False] * LEVELS    # was level filled (buys: bought; sells: only PLACED post-fill)
    sell_armed = [False] * LEVELS       # for sells: True only after corresponding buy filled
    level_pause_until_ms = [0] * LEVELS  # ADCL cooldown expiry per level
    level_cancelled = [False] * LEVELS   # cancel mode: permanently disable level
    level_recross_armed = [False] * LEVELS  # recross mode: True if waiting for cross above
    unstuck1_done = False
    unstuck2_done = False
    hard_stop_fired = False
    trims_log = []
    fills_log = []
    rt_log = []
    upnl_series = []
    cooldown_blocks = 0  # ADCL counter for diagnostics
    cooldown_minutes_ms = adcl_cooldown_min * 60 * 1000

    for bar in candles:
        ts, o, h, l, c, _ = bar
        if hard_stop_fired:
            break

        # 1. Check HARD STOP (uPnL on current close)
        if position_size > 0:
            upnl = position_size * (c - entry_avg) - position_size * c * FEE_RT_PCT / 200.0
            upnl_series.append({"ts": ts, "upnl": upnl, "pos": position_size, "price": c})
            if upnl <= -max_loss_usd:
                # HARD STOP - close everything at close price
                realized_pnl += upnl
                fills_log.append({"ts": ts, "side": "HARD_STOP", "size": position_size,
                                  "price": c, "pnl": upnl})
                position_size = 0.0
                entry_avg = 0.0
                hard_stop_fired = True
                continue

            # 2. Auto-unstuck triggers (compare current close vs center)
            drop_pct = (center - c) / center * 100.0
            if not unstuck1_done and drop_pct >= UNSTUCK_LVL1_PCT:
                trim_size = position_size * 0.25
                trim_price = c
                pnl = trim_size * (trim_price - entry_avg) - trim_size * trim_price * FEE_RT_PCT / 200.0
                realized_pnl += pnl
                position_size -= trim_size
                trims_log.append({"ts": ts, "level": "lvl1", "size": trim_size,
                                  "price": trim_price, "pnl": pnl, "drop_pct": drop_pct})
                unstuck1_done = True
                if adcl_cooldown_min > 0:
                    for i in (0, 1):
                        if mode == "pause":
                            level_pause_until_ms[i] = ts + cooldown_minutes_ms
                        elif mode == "cancel":
                            level_cancelled[i] = True
                        elif mode == "recross":
                            level_recross_armed[i] = True
                            level_pause_until_ms[i] = ts + cooldown_minutes_ms

            elif unstuck1_done and not unstuck2_done and drop_pct >= UNSTUCK_LVL2_PCT:
                trim_size = position_size * 0.25
                trim_price = c
                pnl = trim_size * (trim_price - entry_avg) - trim_size * trim_price * FEE_RT_PCT / 200.0
                realized_pnl += pnl
                position_size -= trim_size
                trims_log.append({"ts": ts, "level": "lvl2", "size": trim_size,
                                  "price": trim_price, "pnl": pnl, "drop_pct": drop_pct})
                unstuck2_done = True
                if adcl_cooldown_min > 0:
                    for i in (0, 1):
                        level_pause_until_ms[i] = ts + cooldown_minutes_ms

            elif unstuck2_done and drop_pct >= UNSTUCK_FULL_PCT:
                # Full close
                pnl = position_size * (c - entry_avg) - position_size * c * FEE_RT_PCT / 200.0
                realized_pnl += pnl
                trims_log.append({"ts": ts, "level": "full_close", "size": position_size,
                                  "price": c, "pnl": pnl, "drop_pct": drop_pct})
                fills_log.append({"ts": ts, "side": "FULL_CLOSE", "size": position_size,
                                  "price": c, "pnl": pnl})
                position_size = 0.0
                entry_avg = 0.0
                hard_stop_fired = True  # grid stops after full close (matches Martin behavior)
                continue

        # 2bis. Recross-mode: clear cooldown if price has reached back above level
        if mode == "recross":
            for i in (0, 1):
                if level_recross_armed[i] and h > level_prices[i] * 1.002:
                    # Mean-reversion confirmed — re-arm fills
                    level_recross_armed[i] = False
                    level_pause_until_ms[i] = 0

        # 3. Process buy fills (bar low touches buy levels 0, 1)
        for i in (0, 1):
            if level_filled[i]:
                continue
            if level_cancelled[i]:
                continue
            if l <= level_prices[i]:
                # ADCL: skip if level paused (pause mode) or recross-armed (recross mode)
                if ts < level_pause_until_ms[i] or level_recross_armed[i]:
                    cooldown_blocks += 1
                    continue

                # Fill the buy
                fill_price = level_prices[i]
                size = notional_per_level / fill_price
                new_total = position_size + size
                entry_avg = (entry_avg * position_size + fill_price * size) / new_total
                position_size = new_total
                level_filled[i] = True
                sell_armed[i + 2] = True  # arm the corresponding sell above
                fills_log.append({"ts": ts, "side": "buy", "size": size,
                                  "price": fill_price, "level": i})

        # 4. Process sell fills (bar high touches armed sell levels 2, 3)
        for i in (2, 3):
            if not sell_armed[i]:
                continue
            if h >= level_prices[i] and position_size > 0:
                fill_price = level_prices[i]
                # The corresponding buy level is i-2 (0 or 1)
                buy_size = notional_per_level / level_prices[i - 2]
                size = min(buy_size, position_size)
                pnl = size * (fill_price - entry_avg) - size * fill_price * FEE_RT_PCT / 200.0
                realized_pnl += pnl
                position_size -= size
                sell_armed[i] = False
                level_filled[i - 2] = False  # re-arm the buy for the next cycle
                # ADCL: clear cooldown when a sell fills (round trip complete)
                level_pause_until_ms[i - 2] = 0
                rt_log.append({"ts": ts, "pnl": pnl, "fill_price": fill_price,
                               "entry_avg": entry_avg})
                fills_log.append({"ts": ts, "side": "sell", "size": size,
                                  "price": fill_price, "pnl": pnl, "level": i})

    # Close any remaining position at last bar
    if position_size > 0 and not hard_stop_fired:
        last_price = candles[-1][4]
        pnl = position_size * (last_price - entry_avg) - position_size * last_price * FEE_RT_PCT / 200.0
        realized_pnl += pnl
        fills_log.append({"ts": candles[-1][0], "side": "end_close", "size": position_size,
                          "price": last_price, "pnl": pnl})

    # Compute max drawdown on uPnL series
    peak = 0.0
    max_dd = 0.0
    for s in upnl_series:
        if s["upnl"] > peak:
            peak = s["upnl"]
        dd = peak - s["upnl"]
        if dd > max_dd:
            max_dd = dd

    return {
        "adcl_cooldown_min": adcl_cooldown_min,
        "realized_pnl_usd": round(realized_pnl, 4),
        "realized_pnl_pct_cap": round(realized_pnl / CAPITAL * 100, 2),
        "hard_stop_fired": hard_stop_fired,
        "trims_count": len(trims_log),
        "trims_detail": [{"lvl": t["level"], "pnl": round(t["pnl"], 4),
                          "drop_pct": round(t["drop_pct"], 2)} for t in trims_log],
        "rt_count": len(rt_log),
        "buy_fills": sum(1 for f in fills_log if f["side"] == "buy"),
        "sell_fills": sum(1 for f in fills_log if f["side"] == "sell"),
        "max_drawdown_usd": round(max_dd, 4),
        "cooldown_blocks": cooldown_blocks,
        "center_price": round(center, 5),
    }


def main():
    print(f"\nADCL Backtest — Option B replay on DOT 1min")
    print(f"Window: {datetime.fromtimestamp(WINDOW_START_MS/1000, timezone.utc).isoformat()} "
          f"-> {datetime.fromtimestamp(WINDOW_END_MS/1000, timezone.utc).isoformat()}")
    print(f"Config: {LEVELS} lvl x {SPACING_PCT}% x ${CAPITAL} x {LEVERAGE}x")
    print(f"Unstuck: {UNSTUCK_LVL1_PCT}%/{UNSTUCK_LVL2_PCT}%/{UNSTUCK_FULL_PCT}% "
          f"| MaxLoss: {MAX_LOSS_PCT}% (${CAPITAL * MAX_LOSS_PCT / 100:.2f})")
    print()

    print(f"[{datetime.utcnow().isoformat()}] fetching DOTUSDT 1min Option B window...")
    candles = fetch_binance_1min("DOTUSDT", WINDOW_START_MS, WINDOW_END_MS)
    if not candles:
        print("No data, aborting.")
        return
    print(f"  {len(candles)} candles "
          f"({(candles[-1][0]-candles[0][0])/3600000:.1f} hours)")

    # 3 modes tested: pause (15/30/60min), cancel (permanent), recross (wait for mean-reversion)
    configs = [
        ("baseline", 0, "pause"),
        ("pause15",  15, "pause"),
        ("pause30",  30, "pause"),
        ("pause60",  60, "pause"),
        ("pause120", 120, "pause"),
        ("cancel",   30, "cancel"),
        ("recross30", 30, "recross"),
        ("recross120", 120, "recross"),
    ]
    results = []
    for label, cooldown, mode in configs:
        r = simulate(candles, adcl_cooldown_min=cooldown, mode=mode)
        r["label"] = label
        r["mode"] = mode
        results.append(r)
        print(f"\n  {label:11s} ({mode:8s} {cooldown:3d}min): "
              f"realized=${r['realized_pnl_usd']:+.4f} "
              f"({r['realized_pnl_pct_cap']:+.2f}% cap) "
              f"trims={r['trims_count']} RT={r['rt_count']} buys={r['buy_fills']} "
              f"hardstop={r['hard_stop_fired']} maxDD=${r['max_drawdown_usd']:.4f} "
              f"blocks={r['cooldown_blocks']}")

    print("\n=== COMPARATIVE TABLE ===")
    print(f"  {'label':>12}  {'mode':>9}  {'pnl_usd':>10}  {'pnl%cap':>9}  "
          f"{'trims':>6}  {'RT':>3}  {'buys':>5}  {'maxDD':>8}  {'blocks':>7}")
    for r in results:
        print(f"  {r['label']:>12}  {r['mode']:>9}  ${r['realized_pnl_usd']:>+9.4f}  "
              f"{r['realized_pnl_pct_cap']:>+8.2f}%  "
              f"{r['trims_count']:>6}  {r['rt_count']:>3}  {r['buy_fills']:>5}  "
              f"${r['max_drawdown_usd']:>7.4f}  {r['cooldown_blocks']:>7}")

    baseline = results[0]
    print("\n=== DELTA vs baseline ===")
    for r in results[1:]:
        delta_pnl = r["realized_pnl_usd"] - baseline["realized_pnl_usd"]
        delta_dd = baseline["max_drawdown_usd"] - r["max_drawdown_usd"]
        verdict = "GAIN" if delta_pnl > 0.01 else ("EQUAL" if abs(delta_pnl) <= 0.01 else "LOSS")
        print(f"  {r['label']:>12}: delta_pnl={delta_pnl:+.4f}$ delta_maxDD={delta_dd:+.4f}$ "
              f"({verdict} vs baseline)")

    out_path = Path(__file__).parent / "adcl_backtest_results.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nFull results: {out_path}")


if __name__ == "__main__":
    main()

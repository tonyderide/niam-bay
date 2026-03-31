#!/usr/bin/env python3
"""
Martin Grid Strategy Backtester
================================
Simulates the exact live Martin Grid config over 90 days of Kraken 1h candles.

Usage:
  python backtest_grid_strategy.py                        # all pairs, live config
  python backtest_grid_strategy.py --pair DOT             # single pair
  python backtest_grid_strategy.py --config aggressive    # preset config
  python backtest_grid_strategy.py --config conservative --pair SOL

Presets:
  conservative : x3, 1.0% spacing, 8 levels
  balanced     : x5, 0.7% spacing, 10 levels
  aggressive   : x10, 0.5% spacing, 10 levels (= live)
  vicky        : x10, 0.35-0.7% spacing, 8-12 levels
"""

import urllib.request
import urllib.error
import json
import math
import time
import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

# ── CONFIG ────────────────────────────────────────────────────────────────────

LIVE_CONFIG = {
    "DOT":  {"capital": 22, "leverage": 10, "spacing_pct": 0.50, "levels": 10},
    "AVAX": {"capital": 22, "leverage": 10, "spacing_pct": 0.60, "levels": 10},
    "SOL":  {"capital": 21, "leverage": 10, "spacing_pct": 0.70, "levels": 8},
    "LINK": {"capital": 22, "leverage": 10, "spacing_pct": 0.55, "levels": 10},
    "ATOM": {"capital": 22, "leverage": 10, "spacing_pct": 0.65, "levels": 6},
}

PRESETS = {
    "aggressive": {
        "DOT":  {"capital": 22, "leverage": 10, "spacing_pct": 0.50, "levels": 10},
        "AVAX": {"capital": 22, "leverage": 10, "spacing_pct": 0.50, "levels": 10},
        "SOL":  {"capital": 21, "leverage": 10, "spacing_pct": 0.50, "levels": 10},
        "LINK": {"capital": 22, "leverage": 10, "spacing_pct": 0.50, "levels": 10},
        "ATOM": {"capital": 22, "leverage": 10, "spacing_pct": 0.50, "levels": 10},
    },
    "conservative": {
        "DOT":  {"capital": 22, "leverage": 3, "spacing_pct": 1.00, "levels": 8},
        "AVAX": {"capital": 22, "leverage": 3, "spacing_pct": 1.00, "levels": 8},
        "SOL":  {"capital": 21, "leverage": 3, "spacing_pct": 1.00, "levels": 8},
        "LINK": {"capital": 22, "leverage": 3, "spacing_pct": 1.00, "levels": 8},
        "ATOM": {"capital": 22, "leverage": 3, "spacing_pct": 1.00, "levels": 8},
    },
    "balanced": {
        "DOT":  {"capital": 22, "leverage": 5, "spacing_pct": 0.70, "levels": 10},
        "AVAX": {"capital": 22, "leverage": 5, "spacing_pct": 0.70, "levels": 10},
        "SOL":  {"capital": 21, "leverage": 5, "spacing_pct": 0.70, "levels": 10},
        "LINK": {"capital": 22, "leverage": 5, "spacing_pct": 0.70, "levels": 10},
        "ATOM": {"capital": 22, "leverage": 5, "spacing_pct": 0.70, "levels": 10},
    },
    "vicky": {
        "DOT":  {"capital": 22, "leverage": 10, "spacing_pct": 0.45, "levels": 10},
        "AVAX": {"capital": 22, "leverage": 10, "spacing_pct": 0.50, "levels": 10},
        "SOL":  {"capital": 21, "leverage": 10, "spacing_pct": 0.70, "levels": 8},
        "LINK": {"capital": 22, "leverage": 10, "spacing_pct": 0.40, "levels": 12},
        "ATOM": {"capital": 22, "leverage": 10, "spacing_pct": 0.35, "levels": 12},
    },
}

PAIR_MAP = {
    "DOT": "DOTUSD", "AVAX": "AVAXUSD", "SOL": "SOLUSD",
    "LINK": "LINKUSD", "ATOM": "ATOMUSD",
}

MAKER_FEE = 0.0002      # 0.02% per fill
TAKER_FEE = 0.0005       # 0.05% orphan close
FUNDING_RATE = 0.0001    # 0.01% per 8h on open notional

KRAKEN_BASE = "https://api.kraken.com/0/public"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# ── KRAKEN DATA ───────────────────────────────────────────────────────────────

def _kraken_fetch(pair_symbol, interval, since_ts):
    """Single Kraken API call. Returns (candles_list, last_ts) or raises."""
    url = f"{KRAKEN_BASE}/OHLC?pair={pair_symbol}&interval={interval}&since={since_ts}"
    req = urllib.request.Request(url, headers={"User-Agent": "niam-bay-backtest/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    if data.get("error") and len(data["error"]) > 0:
        raise RuntimeError(f"Kraken: {data['error']}")
    result = data["result"]
    candle_key = [k for k in result if k != "last"][0]
    raw = result[candle_key]
    parsed = [(int(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[6])) for c in raw]
    return parsed, result.get("last", 0)


def fetch_ohlc(pair_symbol, days=90):
    """Fetch candles from Kraken. Uses best available interval for the requested period.

    Kraken returns max 720 candles per request.
    - 1h candles: ~30 days max
    - 4h candles: ~120 days max
    - For >30 days, we fetch 4h candles for the older period and 1h for the recent 30 days,
      then merge them (4h candles are split into the simulation as-is; the grid logic
      uses high/low so 4h resolution is acceptable).

    For <=30 days, we use pure 1h candles.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    cache_file = os.path.join(DATA_DIR, f"{pair_symbol}_{days}d.json")

    # Use cache if fresh (< 6 hours old)
    if os.path.exists(cache_file):
        age_h = (time.time() - os.path.getmtime(cache_file)) / 3600
        if age_h < 6:
            with open(cache_file) as f:
                candles = json.load(f)
            print(f"  [cache] {len(candles)} candles")
            return candles

    since = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    all_candles = []

    if days <= 30:
        # Pure 1h candles
        interval = 60
        label = "1h"
    else:
        # Use 4h candles for full coverage (720 * 4h = 120 days)
        interval = 240
        label = "4h"

    retries = 0
    while True:
        try:
            new_candles, last = _kraken_fetch(pair_symbol, interval, since)
        except Exception as e:
            retries += 1
            if retries > 5:
                print(f"  [FAIL] {e}")
                break
            print(f"  [retry] {e}")
            time.sleep(3)
            continue

        if not new_candles:
            break

        for c in new_candles:
            if not all_candles or c[0] > all_candles[-1][0]:
                all_candles.append(c)

        sys.stdout.write(".")
        sys.stdout.flush()

        if len(new_candles) < 720:
            break

        since = last
        time.sleep(1.1)

    print(f" {len(all_candles)} candles ({label})")

    with open(cache_file, "w") as f:
        json.dump(all_candles, f)

    return all_candles


# ── ADX CALCULATION ───────────────────────────────────────────────────────────

def calc_adx(highs, lows, closes, period=14):
    """Calculate ADX from arrays. Returns ADX value or None if not enough data."""
    n = len(closes)
    if n < period + 1:
        return None

    # True Range, +DM, -DM
    tr_list = []
    plus_dm_list = []
    minus_dm_list = []

    for i in range(1, n):
        h, l, pc = highs[i], lows[i], closes[i - 1]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        tr_list.append(tr)

        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]

        plus_dm = up if (up > down and up > 0) else 0
        minus_dm = down if (down > up and down > 0) else 0
        plus_dm_list.append(plus_dm)
        minus_dm_list.append(minus_dm)

    if len(tr_list) < period:
        return None

    # Smoothed averages (Wilder's method)
    atr = sum(tr_list[:period]) / period
    plus_di_smooth = sum(plus_dm_list[:period]) / period
    minus_di_smooth = sum(minus_dm_list[:period]) / period

    dx_values = []

    for i in range(period, len(tr_list)):
        atr = (atr * (period - 1) + tr_list[i]) / period
        plus_di_smooth = (plus_di_smooth * (period - 1) + plus_dm_list[i]) / period
        minus_di_smooth = (minus_di_smooth * (period - 1) + minus_dm_list[i]) / period

        if atr == 0:
            continue

        plus_di = 100 * plus_di_smooth / atr
        minus_di = 100 * minus_di_smooth / atr

        di_sum = plus_di + minus_di
        if di_sum == 0:
            dx_values.append(0)
        else:
            dx = 100 * abs(plus_di - minus_di) / di_sum
            dx_values.append(dx)

    if len(dx_values) < period:
        return None

    # ADX = smoothed average of DX
    adx = sum(dx_values[:period]) / period
    for i in range(period, len(dx_values)):
        adx = (adx * (period - 1) + dx_values[i]) / period

    return adx


# ── GRID SIMULATION ──────────────────────────────────────────────────────────

def simulate_pair(pair_name, candles, cfg):
    """Simulate Martin Grid strategy on one pair. Returns results dict."""
    capital = cfg["capital"]
    leverage = cfg["leverage"]
    spacing_pct = cfg["spacing_pct"]
    num_levels = cfg["levels"]
    spacing = spacing_pct / 100.0

    notional_per_level = (capital * leverage) / num_levels

    # Detect candle interval (hours) from timestamps
    if len(candles) >= 2:
        candle_hours = (candles[1][0] - candles[0][0]) / 3600
    else:
        candle_hours = 1
    funding_every_n = max(1, round(8 / candle_hours))  # fund every 8h

    # Results tracking
    round_trips = 0
    gross_profit = 0.0
    total_fees = 0.0
    orphan_costs = 0.0
    funding_paid = 0.0
    recenters = 0
    max_drawdown = 0.0
    peak_equity = capital
    adx_blocked = 0
    total_candles = 0

    monthly_profits = defaultdict(float)
    daily_profits = defaultdict(float)

    # Grid state
    initial_price = candles[0][3]  # open
    grid_center = initial_price

    def make_buy_levels(center):
        """Buy levels below center."""
        return [center * (1 - i * spacing) for i in range(1, num_levels + 1)]

    def make_sell_levels(center):
        """Sell levels above center."""
        return [center * (1 + i * spacing) for i in range(1, num_levels + 1)]

    buy_levels = make_buy_levels(grid_center)
    sell_levels = make_sell_levels(grid_center)

    # Open positions: list of (buy_price, notional)
    open_positions = []

    # Rolling window for ADX
    ADX_WINDOW = 30  # candles for ADX calculation (need period+1 minimum)
    highs_window = []
    lows_window = []
    closes_window = []

    # Track all realized PnL events for accurate Sharpe/PF
    rt_wins = 0.0       # sum of positive round-trip PnL
    rt_losses = 0.0     # sum of negative round-trip PnL (recenter orphans)

    for candle in candles:
        ts, o, h, l, c, vol = candle
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        month_key = dt.strftime("%Y-%m")
        day_key = dt.strftime("%Y-%m-%d")
        total_candles += 1

        # Update ADX window
        highs_window.append(h)
        lows_window.append(l)
        closes_window.append(c)
        if len(highs_window) > ADX_WINDOW:
            highs_window.pop(0)
            lows_window.pop(0)
            closes_window.pop(0)

        # ADX filter
        adx = calc_adx(highs_window, lows_window, closes_window, period=14)
        trending = adx is not None and adx > 25

        if trending:
            adx_blocked += 1

        # Funding cost on open positions (every 8h)
        if total_candles % funding_every_n == 0 and open_positions:
            total_open_notional = sum(n for _, n in open_positions)
            funding_cost = total_open_notional * FUNDING_RATE
            funding_paid += funding_cost

        # Check if price is outside grid range -> recenter
        grid_bottom = buy_levels[-1] if buy_levels else grid_center * (1 - num_levels * spacing)
        grid_top = sell_levels[-1] if sell_levels else grid_center * (1 + num_levels * spacing)

        needs_recenter = c < grid_bottom * 0.98 or c > grid_top * 1.02

        if needs_recenter:
            # Close orphan positions at market (taker fee)
            for bp, notl in open_positions:
                pnl = (c - bp) / bp * notl  # realized PnL (likely negative)
                close_fee = notl * TAKER_FEE
                orphan_costs += close_fee
                # The entry fee was already counted when position opened
                # Track this as realized loss
                if pnl < 0:
                    rt_losses += abs(pnl)
                else:
                    rt_wins += pnl
                gross_profit += pnl
                daily_profits[day_key] += pnl
                monthly_profits[month_key] += pnl

            open_positions = []
            recenters += 1

            # Recenter grid around current price
            grid_center = c
            buy_levels = make_buy_levels(grid_center)
            sell_levels = make_sell_levels(grid_center)

        if not trending and not needs_recenter:
            # Check buy fills (price dipped to buy level)
            new_buy_levels = []
            for bl in buy_levels:
                if l <= bl:
                    # Buy fill at limit (maker fee)
                    fee = notional_per_level * MAKER_FEE
                    total_fees += fee
                    open_positions.append((bl, notional_per_level))
                else:
                    new_buy_levels.append(bl)
            buy_levels = new_buy_levels

            # Check sell fills (price rose to sell level) - close oldest buy
            new_sell_levels = []
            for sl in sell_levels:
                if h >= sl and open_positions:
                    # Sell fill - close oldest position (FIFO)
                    bp, notl = open_positions.pop(0)
                    pnl = (sl - bp) / bp * notl
                    fee = notl * MAKER_FEE  # sell side maker fee
                    total_fees += fee
                    gross_profit += pnl
                    round_trips += 1
                    monthly_profits[month_key] += pnl
                    daily_profits[day_key] += pnl
                    if pnl >= 0:
                        rt_wins += pnl
                    else:
                        rt_losses += abs(pnl)
                elif h >= sl:
                    new_sell_levels.append(sl)
                else:
                    new_sell_levels.append(sl)
            sell_levels = new_sell_levels

            # Replenish grid levels if too many consumed
            if len(buy_levels) < num_levels // 2:
                buy_levels = make_buy_levels(grid_center)
                buy_levels = [bl for bl in buy_levels if bl < c][:num_levels]

            if len(sell_levels) < num_levels // 2:
                sell_levels = make_sell_levels(grid_center)
                sell_levels = [sl for sl in sell_levels if sl > c][:num_levels]

        # Track equity and drawdown
        unrealized = sum((c - bp) / bp * notl for bp, notl in open_positions)
        current_equity = capital + gross_profit - total_fees - orphan_costs - funding_paid + unrealized
        if current_equity > peak_equity:
            peak_equity = current_equity
        dd = (peak_equity - current_equity) / peak_equity * 100 if peak_equity > 0 else 0
        if dd > max_drawdown:
            max_drawdown = dd

    # Final unrealized
    last_close = candles[-1][4]
    final_unrealized = sum((last_close - bp) / bp * notl for bp, notl in open_positions)

    net_profit = gross_profit - total_fees - orphan_costs - funding_paid
    total_costs = total_fees + orphan_costs + funding_paid
    active_pct = (total_candles - adx_blocked) / total_candles * 100 if total_candles > 0 else 0

    # Sharpe ratio on daily net PnL (including all costs allocated proportionally)
    n_days = len(daily_profits)
    if n_days > 1:
        # Spread costs evenly across days for Sharpe
        cost_per_day = total_costs / n_days
        daily_net = [v - cost_per_day for v in daily_profits.values()]
        avg = sum(daily_net) / len(daily_net)
        var = sum((d - avg) ** 2 for d in daily_net) / (len(daily_net) - 1)
        std = math.sqrt(var) if var > 0 else 0.0001
        sharpe = (avg / std) * math.sqrt(365)
    else:
        sharpe = 0

    # Profit factor
    profit_factor = rt_wins / rt_losses if rt_losses > 0 else float("inf")

    return {
        "pair": pair_name,
        "config": cfg,
        "candle_count": total_candles,
        "round_trips": round_trips,
        "gross_profit": gross_profit,
        "total_fees": total_fees,
        "orphan_costs": orphan_costs,
        "funding_paid": funding_paid,
        "total_costs": total_costs,
        "net_profit": net_profit,
        "final_unrealized": final_unrealized,
        "max_drawdown_pct": max_drawdown,
        "recenters": recenters,
        "sharpe": sharpe,
        "profit_factor": profit_factor,
        "active_pct": active_pct,
        "adx_blocked": adx_blocked,
        "monthly_profits": dict(monthly_profits),
        "capital": capital,
        "roi_pct": (net_profit / capital) * 100 if capital > 0 else 0,
    }


# ── OUTPUT ────────────────────────────────────────────────────────────────────

def format_results(all_results, config_name):
    """Format results as markdown."""
    lines = []
    lines.append(f"# Backtest Results — Martin Grid Strategy")
    lines.append(f"")
    lines.append(f"**Config:** {config_name}")
    lines.append(f"**Period:** 90 days of 1h candles (Kraken)")
    lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"")
    lines.append(f"## Fee Structure")
    lines.append(f"- Maker fee: {MAKER_FEE*100:.2f}% per fill (both sides)")
    lines.append(f"- Taker fee: {TAKER_FEE*100:.2f}% orphan closes on recenter")
    lines.append(f"- Funding rate: {FUNDING_RATE*100:.3f}% per 8h on open notional")
    lines.append(f"- ADX filter: skip fills when ADX(14) > 25")
    lines.append(f"")

    # Per-pair results
    lines.append(f"## Per-Pair Results")
    lines.append(f"")
    lines.append(f"| Pair | Capital | Lev | Spacing | Lvls | RTs | Gross | Fees | Orphan | Funding | Net | ROI% | MaxDD% | Sharpe | PF | Active% |")
    lines.append(f"|------|---------|-----|---------|------|-----|-------|------|--------|---------|-----|------|--------|--------|----|---------| ")

    total_capital = 0
    total_gross = 0
    total_fees = 0
    total_orphan = 0
    total_funding = 0
    total_net = 0
    total_rts = 0
    combined_max_dd = 0

    for r in all_results:
        cfg = r["config"]
        lines.append(
            f"| {r['pair']} | ${cfg['capital']} | x{cfg['leverage']} | {cfg['spacing_pct']:.2f}% | "
            f"{cfg['levels']} | {r['round_trips']} | ${r['gross_profit']:.2f} | "
            f"${r['total_fees']:.2f} | ${r['orphan_costs']:.2f} | ${r['funding_paid']:.2f} | "
            f"${r['net_profit']:.2f} | {r['roi_pct']:.1f}% | {r['max_drawdown_pct']:.1f}% | "
            f"{r['sharpe']:.2f} | {r['profit_factor']:.2f} | {r['active_pct']:.0f}% |"
        )
        total_capital += cfg["capital"]
        total_gross += r["gross_profit"]
        total_fees += r["total_fees"]
        total_orphan += r["orphan_costs"]
        total_funding += r["funding_paid"]
        total_net += r["net_profit"]
        total_rts += r["round_trips"]
        if r["max_drawdown_pct"] > combined_max_dd:
            combined_max_dd = r["max_drawdown_pct"]

    lines.append(f"")
    lines.append(f"## Portfolio Summary")
    lines.append(f"")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Capital | ${total_capital} |")
    lines.append(f"| Total Round Trips | {total_rts} |")
    lines.append(f"| Gross Profit | ${total_gross:.2f} |")
    lines.append(f"| Total Fees (maker) | ${total_fees:.2f} |")
    lines.append(f"| Orphan Costs (taker) | ${total_orphan:.2f} |")
    lines.append(f"| Funding Paid | ${total_funding:.2f} |")
    lines.append(f"| **Net Profit** | **${total_net:.2f}** |")
    lines.append(f"| **Portfolio ROI** | **{(total_net/total_capital)*100:.1f}%** |")
    lines.append(f"| Max Drawdown (worst pair) | {combined_max_dd:.1f}% |")
    lines.append(f"| Monthly Avg Net | ${total_net/3:.2f} |")
    lines.append(f"")

    # Monthly breakdown
    lines.append(f"## Monthly Breakdown")
    lines.append(f"")
    all_months = set()
    for r in all_results:
        all_months.update(r["monthly_profits"].keys())
    all_months = sorted(all_months)

    if all_months:
        header = "| Month |" + "|".join(f" {r['pair']} " for r in all_results) + "| Total |"
        sep = "|-------|" + "|".join("------" for _ in all_results) + "|-------|"
        lines.append(header)
        lines.append(sep)

        for m in all_months:
            row = f"| {m} |"
            month_total = 0
            for r in all_results:
                val = r["monthly_profits"].get(m, 0)
                row += f" ${val:.2f} |"
                month_total += val
            row += f" ${month_total:.2f} |"
            lines.append(row)

    lines.append(f"")
    lines.append(f"## Per-Pair Details")
    lines.append(f"")

    for r in all_results:
        lines.append(f"### {r['pair']}")
        lines.append(f"- Candles processed: {r['candle_count']}")
        lines.append(f"- Round trips: {r['round_trips']}")
        lines.append(f"- Recenters: {r['recenters']}")
        lines.append(f"- ADX-blocked candles: {r['adx_blocked']} ({100-r['active_pct']:.0f}%)")
        lines.append(f"- Unrealized at end: ${r['final_unrealized']:.2f}")
        lines.append(f"")

    return "\n".join(lines)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Martin Grid Strategy Backtester")
    parser.add_argument("--pair", type=str, help="Test single pair (DOT, AVAX, SOL, LINK, ATOM)")
    parser.add_argument("--config", type=str, default="live",
                        help="Config preset: live, conservative, balanced, aggressive, vicky")
    parser.add_argument("--days", type=int, default=90, help="Number of days to backtest")
    args = parser.parse_args()

    # Select config
    config_name = args.config
    if config_name == "live":
        config = LIVE_CONFIG.copy()
    elif config_name in PRESETS:
        config = PRESETS[config_name].copy()
    else:
        print(f"Unknown config: {config_name}")
        print(f"Available: live, {', '.join(PRESETS.keys())}")
        sys.exit(1)

    # Filter to single pair if requested
    if args.pair:
        pair = args.pair.upper()
        if pair not in config:
            print(f"Unknown pair: {pair}")
            print(f"Available: {', '.join(config.keys())}")
            sys.exit(1)
        config = {pair: config[pair]}

    print(f"=" * 60)
    print(f"Martin Grid Backtester")
    print(f"Config: {config_name} | Days: {args.days}")
    print(f"Pairs: {', '.join(config.keys())}")
    print(f"=" * 60)

    # Fetch data and run simulation
    all_results = []
    for pair_name, cfg in config.items():
        kraken_pair = PAIR_MAP[pair_name]
        print(f"\n[{pair_name}] Fetching {args.days}d of 1h candles ({kraken_pair})", end="")
        candles = fetch_ohlc(kraken_pair, days=args.days)

        if not candles or len(candles) < 100:
            print(f"  [SKIP] Not enough candles ({len(candles) if candles else 0})")
            continue

        print(f"  [SIM] capital=${cfg['capital']}, x{cfg['leverage']}, "
              f"spacing={cfg['spacing_pct']}%, levels={cfg['levels']}")
        result = simulate_pair(pair_name, candles, cfg)
        all_results.append(result)
        print(f"  [DONE] {result['round_trips']} RTs, net=${result['net_profit']:.2f}, "
              f"ROI={result['roi_pct']:.1f}%, maxDD={result['max_drawdown_pct']:.1f}%")

    if not all_results:
        print("\nNo results to show.")
        sys.exit(1)

    # Format and save
    report = format_results(all_results, config_name)
    print(f"\n{'=' * 60}")
    print(report)

    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BACKTEST_LIVE_CONFIG.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    main()

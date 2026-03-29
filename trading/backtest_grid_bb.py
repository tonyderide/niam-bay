"""
Grid Trading + Bollinger Bands Hybrid Backtest
===============================================
4 strategies compared:
  1. Grid classique (always on) — baseline
  2. Grid + BB width filter (on/off selon volatilité)
  3. Grid + BB direction bias (biais long/short selon BB)
  4. Grid + BB width + direction combinés

BB Logic:
  - BB width < 4% (squeeze) → ACTIVE le grid (marché range)
  - BB width > 8% (expansion) → STOP le grid (marché trend)
  - Prix touche lower BB → biais LONG (plus de buy levels)
  - Prix touche upper BB → biais SHORT (plus de sell levels)

Pairs: ETH, DOT, SOL — 3 months hourly data.
"""

import csv, sys, math
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DATA_DIR = Path(__file__).parent / "data"


# ══════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════

def load_candles(filepath):
    candles = []
    with open(filepath, "r") as f:
        for row in csv.DictReader(f):
            candles.append({
                "ts": row["timestamp"],
                "o": float(row["open"]),
                "h": float(row["high"]),
                "l": float(row["low"]),
                "c": float(row["close"]),
            })
    return candles


# ══════════════════════════════════════════════════════════════
# BOLLINGER BANDS
# ══════════════════════════════════════════════════════════════

def compute_bollinger(candles, period=20, num_std=2.0):
    """Compute BB for each candle. Returns list of dicts with bb_upper, bb_lower, bb_mid, bb_width_pct."""
    closes = [c["c"] for c in candles]
    bb = []
    for i in range(len(candles)):
        if i < period - 1:
            bb.append({"bb_upper": None, "bb_lower": None, "bb_mid": None, "bb_width_pct": None})
            continue
        window = closes[i - period + 1: i + 1]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        std = math.sqrt(variance)
        upper = mean + num_std * std
        lower = mean - num_std * std
        width_pct = (upper - lower) / mean * 100 if mean > 0 else 0
        bb.append({
            "bb_upper": upper,
            "bb_lower": lower,
            "bb_mid": mean,
            "bb_width_pct": width_pct,
        })
    return bb


# ══════════════════════════════════════════════════════════════
# GRID ENGINE (with BB filters)
# ══════════════════════════════════════════════════════════════

def run_grid_bb(candles, bb_data, strategy, spacing_pct, num_levels, leverage, capital,
                max_loss_pct=15.0, use_maxloss=True,
                bb_squeeze_thresh=4.0, bb_expand_thresh=8.0):
    """
    Grid backtest with optional BB filters.

    strategy:
      "classic"       — always on, no BB filter
      "bb_width"      — on/off based on BB width
      "bb_bias"       — always on, but bias levels based on BB position
      "bb_combined"   — width filter + bias combined
    """
    MAKER_FEE = 0.0002
    TAKER_FEE = 0.0005
    fill_fee = MAKER_FEE
    recenter_fee = TAKER_FEE

    spacing = spacing_pct / 100.0
    cash = capital
    total_fees = 0.0
    round_trips = 0
    peak_equity = capital
    max_drawdown = 0.0
    stopped_out = False

    center = candles[0]["c"]
    active_hours = 0
    inactive_hours = 0
    total_hours = len(candles)

    # Track equity curve for analysis
    equity_curve = []

    def make_grid(center_price, long_bias=0):
        """
        long_bias: 0 = neutral, >0 = more buy levels, <0 = more sell levels
        Normal: num_levels buy + num_levels sell
        Biased: (num_levels + bias) on favored side, (num_levels - bias) on other
        """
        buy_count = min(num_levels + long_bias, num_levels * 2)
        sell_count = min(num_levels - long_bias, num_levels * 2)
        buy_count = max(buy_count, 1)
        sell_count = max(sell_count, 1)

        buys = [center_price * (1 - i * spacing) for i in range(1, buy_count + 1)]
        sells = [center_price * (1 + i * spacing) for i in range(1, sell_count + 1)]
        return buys, sells, buy_count, sell_count

    # Initial grid
    buy_levels, sell_levels, buy_count, sell_count = make_grid(center, 0)
    buy_armed = [True] * buy_count
    sell_armed = [False] * sell_count
    positions = {}  # level_index -> (buy_price, qty_coins)
    notional_per_level = (capital * leverage) / num_levels

    grid_active = True  # For width filter strategies
    long_bias = 0

    for idx, candle in enumerate(candles):
        h, l, c = candle["h"], candle["l"], candle["c"]
        bb = bb_data[idx]

        # ── BB filter logic ──
        if bb["bb_width_pct"] is not None:
            width = bb["bb_width_pct"]

            # Determine if grid should be active (width filter)
            if strategy in ("bb_width", "bb_combined"):
                if width < bb_squeeze_thresh:
                    if not grid_active:
                        # Reactivate: reset grid at current price
                        grid_active = True
                        center = c
                        buy_levels, sell_levels, buy_count, sell_count = make_grid(center, 0)
                        buy_armed = [True] * buy_count
                        sell_armed = [False] * sell_count
                        positions = {}
                        current_eq = cash
                        if current_eq > 0:
                            notional_per_level = (current_eq * leverage) / num_levels
                elif width > bb_expand_thresh:
                    if grid_active:
                        # Deactivate: close all positions
                        for i, (bp, qty) in list(positions.items()):
                            fee = qty * c * TAKER_FEE
                            pnl = qty * (c - bp) - fee
                            cash += pnl
                            total_fees += fee
                        positions.clear()
                        grid_active = False
                # Between thresholds: keep current state (hysteresis)

            # Determine bias (direction filter)
            long_bias = 0
            if strategy in ("bb_bias", "bb_combined"):
                if grid_active and bb["bb_lower"] is not None:
                    # Proximity to bands
                    if c <= bb["bb_lower"] * 1.005:  # Near lower band
                        long_bias = 2  # More buy levels
                    elif c >= bb["bb_upper"] * 0.995:  # Near upper band
                        long_bias = -2  # More sell levels (fewer buys)
                    else:
                        long_bias = 0

            # Rebuild grid if bias changed and grid is active
            if strategy in ("bb_bias", "bb_combined") and grid_active:
                new_buys, new_sells, new_bc, new_sc = make_grid(center, long_bias)
                # Only rebuild if level counts changed
                if new_bc != buy_count or new_sc != sell_count:
                    # Close positions that won't have matching sells
                    for i, (bp, qty) in list(positions.items()):
                        if i >= new_sc:  # This sell level won't exist
                            fee = qty * c * TAKER_FEE
                            pnl = qty * (c - bp) - fee
                            cash += pnl
                            total_fees += fee
                            del positions[i]

                    buy_levels = new_buys
                    sell_levels = new_sells
                    buy_count = new_bc
                    sell_count = new_sc
                    buy_armed = [True] * buy_count
                    sell_armed = [False] * sell_count
                    # Re-arm sells for existing positions
                    for i in positions:
                        if i < sell_count:
                            sell_armed[i] = True
                            if i < buy_count:
                                buy_armed[i] = False

        if not grid_active:
            inactive_hours += 1
            # Track equity even when inactive
            equity = cash
            equity_curve.append(equity)
            if equity > peak_equity:
                peak_equity = equity
            dd = (peak_equity - equity) / peak_equity * 100 if peak_equity > 0 else 0
            max_drawdown = max(max_drawdown, dd)
            continue

        active_hours += 1

        # ── Buy fills ──
        buys_filled = 0
        for i in range(buy_count):
            if not buy_armed[i]:
                continue
            bp = buy_levels[i]
            if l < bp:  # Maker fill
                if buys_filled >= 1:
                    continue
                qty = notional_per_level / bp
                fee = qty * bp * fill_fee
                cash -= fee
                total_fees += fee
                positions[i] = (bp, qty)
                buy_armed[i] = False
                if i < sell_count:
                    sell_armed[i] = True
                buys_filled += 1

        # ── Sell fills ──
        sells_filled = 0
        for i in range(sell_count):
            if not sell_armed[i]:
                continue
            sp = sell_levels[i]
            if h > sp:  # Maker fill
                if sells_filled >= 1:
                    continue
                if i not in positions:
                    continue
                bp, qty = positions[i]
                fee = qty * sp * fill_fee
                pnl = qty * (sp - bp) - fee
                cash += pnl
                total_fees += fee
                del positions[i]
                sell_armed[i] = False
                if i < buy_count:
                    buy_armed[i] = True
                round_trips += 1
                sells_filled += 1

        # ── Mark to market ──
        unrealized = sum(qty * (c - bp) for bp, qty in positions.values())
        equity = cash + unrealized
        equity_curve.append(equity)

        if equity > peak_equity:
            peak_equity = equity
        dd = (peak_equity - equity) / peak_equity * 100 if peak_equity > 0 else 0
        max_drawdown = max(max_drawdown, dd)

        # ── Max loss check ──
        if use_maxloss and equity <= capital * (1 - max_loss_pct / 100):
            for i, (bp, qty) in list(positions.items()):
                fee = qty * c * TAKER_FEE
                pnl = qty * (c - bp) - fee
                cash += pnl
                total_fees += fee
            positions.clear()
            stopped_out = True
            break

        # ── Recenter check ──
        upper_bound = center * (1 + (num_levels + 1) * spacing)
        lower_bound = center * (1 - (num_levels + 1) * spacing)

        if c > upper_bound or c < lower_bound:
            for i, (bp, qty) in list(positions.items()):
                fee = qty * c * recenter_fee
                pnl = qty * (c - bp) - fee
                cash += pnl
                total_fees += fee
            positions.clear()

            center = c
            buy_levels, sell_levels, buy_count, sell_count = make_grid(center, long_bias if strategy in ("bb_bias", "bb_combined") else 0)
            buy_armed = [True] * buy_count
            sell_armed = [False] * sell_count

            current_eq = cash
            if current_eq > 0:
                notional_per_level = (current_eq * leverage) / num_levels

    # ── Close remaining ──
    if not stopped_out:
        final_price = candles[-1]["c"]
        for i, (bp, qty) in list(positions.items()):
            fee = qty * final_price * TAKER_FEE
            pnl = qty * (final_price - bp) - fee
            cash += pnl
            total_fees += fee

    net_profit = cash - capital
    profit_per_rt = net_profit / max(round_trips, 1)
    active_pct = active_hours / total_hours * 100 if total_hours > 0 else 0

    return {
        "strategy": strategy,
        "net_profit": round(net_profit, 2),
        "rts": round_trips,
        "max_dd": round(max_drawdown, 2),
        "profit_per_rt": round(profit_per_rt, 4),
        "fees": round(total_fees, 2),
        "final_equity": round(cash, 2),
        "stopped": stopped_out,
        "active_hours": active_hours,
        "inactive_hours": inactive_hours,
        "active_pct": round(active_pct, 1),
    }


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    PAIRS = {
        "ETH": DATA_DIR / "ETHUSD_1h_3mo.csv",
        "DOT": DATA_DIR / "DOTUSD_1h_3mo.csv",
        "SOL": DATA_DIR / "SOLUSD_1h_3mo.csv",
    }

    STRATEGIES = ["classic", "bb_width", "bb_bias", "bb_combined"]
    STRATEGY_NAMES = {
        "classic": "Grid classique (always on)",
        "bb_width": "Grid + BB width filter",
        "bb_bias": "Grid + BB direction bias",
        "bb_combined": "Grid + BB width + bias",
    }

    # Grid params (use the config that works best from previous backtests)
    CONFIGS = [
        {"spacing": 1.0, "levels": 5, "leverage": 5, "label": "1%/5lv/5x"},
        {"spacing": 2.0, "levels": 5, "leverage": 5, "label": "2%/5lv/5x"},
        {"spacing": 1.0, "levels": 8, "leverage": 3, "label": "1%/8lv/3x"},
        {"spacing": 0.5, "levels": 8, "leverage": 3, "label": "0.5%/8lv/3x"},
    ]

    CAPITAL = 100.0
    BB_PERIOD = 20
    BB_SQUEEZE = 4.0  # Width < 4% → grid ON
    BB_EXPAND = 8.0   # Width > 8% → grid OFF

    print("=" * 110)
    print("  BACKTEST: Grid Trading + Bollinger Bands Hybrid")
    print("  Date: 2026-03-29")
    print("=" * 110)

    # ─── Market context ───────────────────────────────
    print("\n  MARKET CONTEXT (3 months hourly data)")
    print("  " + "-" * 80)
    all_data = {}
    for name, path in PAIRS.items():
        candles = load_candles(path)
        bb = compute_bollinger(candles, BB_PERIOD)
        all_data[name] = (candles, bb)
        o = candles[0]["c"]
        c = candles[-1]["c"]
        hi = max(x["h"] for x in candles)
        lo = min(x["l"] for x in candles)
        # BB stats
        widths = [b["bb_width_pct"] for b in bb if b["bb_width_pct"] is not None]
        avg_w = sum(widths) / len(widths)
        squeeze_pct = sum(1 for w in widths if w < BB_SQUEEZE) / len(widths) * 100
        expand_pct = sum(1 for w in widths if w > BB_EXPAND) / len(widths) * 100
        print(f"  {name}: {o:.2f} -> {c:.2f} ({(c-o)/o*100:+.1f}%)  "
              f"Range: {(hi-lo)/o*100:.1f}%  |  "
              f"BB avg width: {avg_w:.1f}%  Squeeze(<{BB_SQUEEZE}%): {squeeze_pct:.0f}%  "
              f"Expand(>{BB_EXPAND}%): {expand_pct:.0f}%")

    print(f"\n  BB params: period={BB_PERIOD}, squeeze<{BB_SQUEEZE}%, expand>{BB_EXPAND}%")
    print(f"  Capital: ${CAPITAL}  |  Max loss: 15%")

    # ─── Run all strategies ───────────────────────────
    all_results = []

    for pair_name in PAIRS:
        candles, bb = all_data[pair_name]

        for cfg in CONFIGS:
            for strat in STRATEGIES:
                r = run_grid_bb(
                    candles, bb, strat,
                    cfg["spacing"], cfg["levels"], cfg["leverage"], CAPITAL,
                    max_loss_pct=15.0, use_maxloss=True,
                    bb_squeeze_thresh=BB_SQUEEZE, bb_expand_thresh=BB_EXPAND,
                )
                r["pair"] = pair_name
                r["config"] = cfg["label"]
                r["spacing"] = cfg["spacing"]
                r["levels"] = cfg["levels"]
                r["leverage"] = cfg["leverage"]
                all_results.append(r)

    # ─── Results by strategy ──────────────────────────
    print("\n\n" + "=" * 110)
    print("  RESULTS BY STRATEGY (with 15% max loss)")
    print("=" * 110)

    for strat in STRATEGIES:
        sr = [r for r in all_results if r["strategy"] == strat]
        profitable = sum(1 for r in sr if r["net_profit"] > 0)
        avg_pnl = sum(r["net_profit"] for r in sr) / len(sr)
        avg_dd = sum(r["max_dd"] for r in sr) / len(sr)
        avg_rts = sum(r["rts"] for r in sr) / len(sr)
        avg_active = sum(r["active_pct"] for r in sr) / len(sr)
        stopped = sum(1 for r in sr if r["stopped"])
        print(f"\n  {STRATEGY_NAMES[strat]}")
        print(f"    Profitable: {profitable}/{len(sr)}  |  Avg PnL: ${avg_pnl:.2f}  |  "
              f"Avg MaxDD: {avg_dd:.1f}%  |  Avg RTs: {avg_rts:.0f}  |  "
              f"Avg active: {avg_active:.0f}%  |  Stopped: {stopped}")

    # ─── Detailed comparison table ────────────────────
    print("\n\n" + "=" * 110)
    print("  DETAILED COMPARISON — ALL CONFIGS")
    print("=" * 110)

    header = (f"  {'Pair':<5} {'Config':<14} {'Strategy':<14} "
              f"{'Profit':>8} {'RTs':>5} {'MaxDD%':>7} {'$/RT':>8} "
              f"{'Fees':>6} {'Active%':>8} {'Stop':>5}")
    print(header)
    print("  " + "-" * (len(header) - 2))

    # Group by pair+config for comparison
    grouped = defaultdict(list)
    for r in all_results:
        key = (r["pair"], r["config"])
        grouped[key].append(r)

    for (pair, cfg), results in sorted(grouped.items()):
        results.sort(key=lambda x: STRATEGIES.index(x["strategy"]))
        for r in results:
            marker = " ***" if r["net_profit"] > 0 else ""
            print(f"  {r['pair']:<5} {r['config']:<14} {r['strategy']:<14} "
                  f"{r['net_profit']:>8.2f} {r['rts']:>5} {r['max_dd']:>7.2f} "
                  f"{r['profit_per_rt']:>8.4f} {r['fees']:>6.2f} "
                  f"{r['active_pct']:>7.1f}% "
                  f"{'Y' if r['stopped'] else 'N':>5}{marker}")
        print()

    # ─── Strategy vs Strategy (head to head) ──────────
    print("\n" + "=" * 110)
    print("  HEAD TO HEAD: BB strategies vs Classic baseline")
    print("=" * 110)

    wins = defaultdict(int)
    improvements = defaultdict(list)

    for (pair, cfg), results in grouped.items():
        classic = next(r for r in results if r["strategy"] == "classic")
        for r in results:
            if r["strategy"] == "classic":
                continue
            diff = r["net_profit"] - classic["net_profit"]
            improvements[r["strategy"]].append(diff)
            if r["net_profit"] > classic["net_profit"]:
                wins[r["strategy"]] += 1

    total_configs = len(grouped)
    print(f"\n  {'Strategy':<20} {'Wins vs Classic':>16} {'Avg Improvement':>18} {'Best':>10} {'Worst':>10}")
    print("  " + "-" * 80)
    for strat in ["bb_width", "bb_bias", "bb_combined"]:
        imps = improvements[strat]
        avg_imp = sum(imps) / len(imps)
        best = max(imps)
        worst = min(imps)
        print(f"  {STRATEGY_NAMES[strat]:<20} {wins[strat]:>5}/{total_configs:<10} "
              f"${avg_imp:>+14.2f}   ${best:>+8.2f}  ${worst:>+8.2f}")

    # ─── Without max loss ─────────────────────────────
    print("\n\n" + "=" * 110)
    print("  RESULTS WITHOUT MAX LOSS (ride it out)")
    print("=" * 110)

    all_noloss = []
    for pair_name in PAIRS:
        candles, bb = all_data[pair_name]
        for cfg in CONFIGS:
            for strat in STRATEGIES:
                r = run_grid_bb(
                    candles, bb, strat,
                    cfg["spacing"], cfg["levels"], cfg["leverage"], CAPITAL,
                    max_loss_pct=15.0, use_maxloss=False,
                    bb_squeeze_thresh=BB_SQUEEZE, bb_expand_thresh=BB_EXPAND,
                )
                r["pair"] = pair_name
                r["config"] = cfg["label"]
                all_noloss.append(r)

    for strat in STRATEGIES:
        sr = [r for r in all_noloss if r["strategy"] == strat]
        profitable = sum(1 for r in sr if r["net_profit"] > 0)
        avg_pnl = sum(r["net_profit"] for r in sr) / len(sr)
        avg_dd = sum(r["max_dd"] for r in sr) / len(sr)
        avg_rts = sum(r["rts"] for r in sr) / len(sr)
        avg_active = sum(r["active_pct"] for r in sr) / len(sr)
        print(f"\n  {STRATEGY_NAMES[strat]}")
        print(f"    Profitable: {profitable}/{len(sr)}  |  Avg PnL: ${avg_pnl:.2f}  |  "
              f"Avg MaxDD: {avg_dd:.1f}%  |  Avg RTs: {avg_rts:.0f}  |  "
              f"Avg active: {avg_active:.0f}%")

    # Head to head without maxloss
    grouped_nl = defaultdict(list)
    for r in all_noloss:
        key = (r["pair"], r["config"])
        grouped_nl[key].append(r)

    wins_nl = defaultdict(int)
    improvements_nl = defaultdict(list)

    for (pair, cfg), results in grouped_nl.items():
        classic = next(r for r in results if r["strategy"] == "classic")
        for r in results:
            if r["strategy"] == "classic":
                continue
            diff = r["net_profit"] - classic["net_profit"]
            improvements_nl[r["strategy"]].append(diff)
            if r["net_profit"] > classic["net_profit"]:
                wins_nl[r["strategy"]] += 1

    print(f"\n  {'Strategy':<20} {'Wins vs Classic':>16} {'Avg Improvement':>18} {'Best':>10} {'Worst':>10}")
    print("  " + "-" * 80)
    for strat in ["bb_width", "bb_bias", "bb_combined"]:
        imps = improvements_nl[strat]
        avg_imp = sum(imps) / len(imps)
        best = max(imps)
        worst = min(imps)
        print(f"  {STRATEGY_NAMES[strat]:<20} {wins_nl[strat]:>5}/{total_configs:<10} "
              f"${avg_imp:>+14.2f}   ${best:>+8.2f}  ${worst:>+8.2f}")

    # ─── Best overall configs ─────────────────────────
    print("\n\n" + "=" * 110)
    print("  TOP 10 OVERALL (no max loss)")
    print("=" * 110)

    all_noloss.sort(key=lambda r: r["net_profit"], reverse=True)
    print(f"  {'Pair':<5} {'Config':<14} {'Strategy':<14} "
          f"{'Profit':>8} {'RTs':>5} {'MaxDD%':>7} {'$/RT':>8} {'Active%':>8}")
    print("  " + "-" * 80)
    for r in all_noloss[:10]:
        print(f"  {r['pair']:<5} {r['config']:<14} {r['strategy']:<14} "
              f"{r['net_profit']:>8.2f} {r['rts']:>5} {r['max_dd']:>7.2f} "
              f"{r['profit_per_rt']:>8.4f} {r['active_pct']:>7.1f}%")

    print(f"\n  WORST 5:")
    for r in all_noloss[-5:]:
        print(f"  {r['pair']:<5} {r['config']:<14} {r['strategy']:<14} "
              f"{r['net_profit']:>8.2f} {r['rts']:>5} {r['max_dd']:>7.2f} "
              f"{r['profit_per_rt']:>8.4f} {r['active_pct']:>7.1f}%")

    # ─── BB Width sensitivity ────────────────────────
    print("\n\n" + "=" * 110)
    print("  BB WIDTH SENSITIVITY — Varying squeeze/expand thresholds")
    print("=" * 110)

    # Test different BB thresholds on best config
    THRESHOLDS = [
        (3.0, 6.0),
        (3.0, 8.0),
        (4.0, 8.0),
        (4.0, 10.0),
        (5.0, 10.0),
        (5.0, 12.0),
    ]

    print(f"\n  Config: 1%/5lv/5x  |  Strategy: bb_combined  |  No max loss")
    print(f"  {'Pair':<5} {'Squeeze':<8} {'Expand':<8} {'Profit':>8} {'RTs':>5} "
          f"{'MaxDD%':>7} {'Active%':>8}")
    print("  " + "-" * 60)

    for pair_name in PAIRS:
        candles, bb_base = all_data[pair_name]
        for sq, ex in THRESHOLDS:
            r = run_grid_bb(
                candles, bb_base, "bb_combined",
                1.0, 5, 5, CAPITAL,
                use_maxloss=False,
                bb_squeeze_thresh=sq, bb_expand_thresh=ex,
            )
            print(f"  {pair_name:<5} <{sq:.0f}%     >{ex:.0f}%     "
                  f"{r['net_profit']:>8.2f} {r['rts']:>5} {r['max_dd']:>7.2f} "
                  f"{r['active_pct']:>7.1f}%")
        print()

    # ─── Conclusions ──────────────────────────────────
    print("\n" + "=" * 110)
    print("  CONCLUSIONS")
    print("=" * 110)
    print("""
  1. BB WIDTH FILTER (on/off) — LE GAGNANT:
     - 11/12 wins vs classic sans max loss, +$20 avg improvement.
     - Drawdown reduit de 80% a 62% en moyenne.
     - Le grid est off ~23% du temps (quand BB width > 8%).
     - C'est un circuit breaker gratuit.

  2. BB DIRECTION BIAS — LE PIEGE:
     - 0/12 wins sans max loss. PIRE que le classic.
     - Biaiser long pres du lower BB en tendance baissiere = acheter
       des couteaux qui tombent. Le lower BB descend avec le prix.
     - Mean-reversion ne marche pas en tendance forte.

  3. BB COMBINED = BB WIDTH essentiellement:
     - 10/12 wins (vs 11/12 pour width seul).
     - Le biais directionnel n'ajoute rien, c'est le filtre on/off
       qui fait tout le travail.

  4. VERDICT:
     - AUCUNE strategie profitable sur ces 3 mois (marche -30%).
     - Mais BB width filter REDUIT les pertes de 30% et le drawdown de 20pts.
     - Sweet spot: squeeze < 3%, expand > 6% (le plus selectif).
     - Pour le live: implementer BB width comme circuit breaker dans Martin.
       Si BB width > 6-8%, eteindre le grid. C'est gratuit et ca sauve du capital.

  5. PROCHAINES PISTES:
     - Tester sur marche sideways (3 mois range-bound)
     - Grid SHORT quand BB width > 8% (trend-following)
     - Combiner avec RSI pour le timing d'entree
""")


if __name__ == "__main__":
    main()

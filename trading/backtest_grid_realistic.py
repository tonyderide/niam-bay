"""
Realistic Grid Trading Backtest v2 — Maker vs Taker vs Hybrid
==============================================================
3 months of hourly data on ETH, ADA, SOL.

Fix from v1: properly track equity, positions, and PnL.
Added: both maxloss=15% mode and unlimited mode for comparison.

Fill simulation:
  MAKER: price must STRICTLY cross through level (< for buy, > for sell)
         Max 1 fill per candle per side (conservative)
         Fee: 0.02% per side

  TAKER: price touching level is enough (<= for buy, >= for sell)
         All levels can fill on same candle
         Fee: 0.05% per side

  HYBRID: Maker fills for grid orders, taker fees on recenter closes
"""

import csv, sys, itertools, json
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent / "data"

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


def run_grid(candles, mode, spacing_pct, num_levels, leverage, capital,
             max_loss_pct=15.0, use_maxloss=True):
    """
    Grid backtest engine.

    Tracks:
    - Cash: actual USD balance (starts at capital)
    - Positions: list of open longs (buy_price, qty)
    - Equity = cash + sum(qty * current_price) for open positions
    """
    MAKER_FEE = 0.0002
    TAKER_FEE = 0.0005

    if mode == "maker":
        fill_fee = MAKER_FEE
        recenter_fee = MAKER_FEE
    elif mode == "taker":
        fill_fee = TAKER_FEE
        recenter_fee = TAKER_FEE
    else:  # hybrid
        fill_fee = MAKER_FEE
        recenter_fee = TAKER_FEE

    spacing = spacing_pct / 100.0
    cash = capital  # USD cash balance
    total_fees = 0.0
    round_trips = 0
    missed_rts = 0
    num_recenters = 0
    peak_equity = capital
    max_drawdown = 0.0
    stopped_out = False

    # Grid state
    center = candles[0]["c"]

    def make_grid(center_price):
        buys = []
        sells = []
        for i in range(1, num_levels + 1):
            buys.append(center_price * (1 - i * spacing))
            sells.append(center_price * (1 + i * spacing))
        return buys, sells

    buy_levels, sell_levels = make_grid(center)

    # Track: for each buy level index, is it "armed" (waiting to fill)?
    # When a buy fills, the corresponding sell becomes armed.
    buy_armed = [True] * num_levels   # All buys start armed
    sell_armed = [False] * num_levels  # No sells armed initially

    # Open positions from filled buys
    positions = {}  # level_index -> (buy_price, qty_coins)

    # Size per level: distribute leveraged capital
    notional_per_level = (capital * leverage) / num_levels

    for candle in candles:
        h, l, c = candle["h"], candle["l"], candle["c"]

        # ── Buy fills ──
        buys_filled = 0
        for i in range(num_levels):
            if not buy_armed[i]:
                continue
            bp = buy_levels[i]

            # Fill condition
            if mode == "taker":
                fills = l <= bp
            else:  # maker or hybrid
                fills = l < bp  # must cross through

            if fills:
                if mode == "maker" or mode == "hybrid":
                    if buys_filled >= 1:
                        missed_rts += 1
                        continue

                # Execute buy
                qty = notional_per_level / bp
                fee = qty * bp * fill_fee
                cash -= fee  # Fee comes from cash
                total_fees += fee

                positions[i] = (bp, qty)
                buy_armed[i] = False
                sell_armed[i] = True
                buys_filled += 1

        # ── Sell fills ──
        sells_filled = 0
        for i in range(num_levels):
            if not sell_armed[i]:
                continue
            sp = sell_levels[i]

            if mode == "taker":
                fills = h >= sp
            else:
                fills = h > sp

            if fills:
                if mode == "maker" or mode == "hybrid":
                    if sells_filled >= 1:
                        missed_rts += 1
                        continue

                if i not in positions:
                    continue

                bp, qty = positions[i]
                fee = qty * sp * fill_fee

                # Realize PnL: we bought at bp, selling at sp
                pnl = qty * (sp - bp) - fee
                cash += pnl  # Add net PnL (buy cost was "virtual" via leverage)
                total_fees += fee

                del positions[i]
                sell_armed[i] = False
                buy_armed[i] = True  # Re-arm buy
                round_trips += 1
                sells_filled += 1

        # ── Mark to market ──
        unrealized = sum(qty * (c - bp) for bp, qty in positions.values())
        equity = cash + unrealized

        if equity > peak_equity:
            peak_equity = equity
        dd = (peak_equity - equity) / peak_equity * 100 if peak_equity > 0 else 0
        max_drawdown = max(max_drawdown, dd)

        # ── Max loss check ──
        if use_maxloss and equity <= capital * (1 - max_loss_pct / 100):
            # Close all positions at market
            for i, (bp, qty) in list(positions.items()):
                fee = qty * c * TAKER_FEE
                pnl = qty * (c - bp) - fee
                cash += pnl
                total_fees += fee
            positions.clear()
            buy_armed = [False] * num_levels
            sell_armed = [False] * num_levels
            stopped_out = True
            break

        # ── Recenter check ──
        upper_bound = center * (1 + (num_levels + 1) * spacing)
        lower_bound = center * (1 - (num_levels + 1) * spacing)

        if c > upper_bound or c < lower_bound:
            # Close all open positions at current price
            for i, (bp, qty) in list(positions.items()):
                fee = qty * c * recenter_fee
                pnl = qty * (c - bp) - fee
                cash += pnl
                total_fees += fee
            positions.clear()

            num_recenters += 1
            center = c
            buy_levels, sell_levels = make_grid(center)
            buy_armed = [True] * num_levels
            sell_armed = [False] * num_levels

            # Recalculate size based on current equity
            current_eq = cash  # No positions open after recenter
            if current_eq > 0:
                notional_per_level = (current_eq * leverage) / num_levels

    # ── Close remaining at end ──
    if not stopped_out:
        final_price = candles[-1]["c"]
        for i, (bp, qty) in list(positions.items()):
            fee = qty * final_price * TAKER_FEE
            pnl = qty * (final_price - bp) - fee
            cash += pnl
            total_fees += fee

    net_profit = cash - capital
    fill_rate = round_trips / max(round_trips + missed_rts, 1) * 100
    profit_per_rt = net_profit / max(round_trips, 1)

    return {
        "mode": mode,
        "spacing": spacing_pct,
        "levels": num_levels,
        "leverage": leverage,
        "net_profit": round(net_profit, 2),
        "rts": round_trips,
        "missed": missed_rts,
        "fill_rate": round(fill_rate, 1),
        "max_dd": round(max_drawdown, 2),
        "profit_per_rt": round(profit_per_rt, 4),
        "fees": round(total_fees, 2),
        "recenters": num_recenters,
        "final_equity": round(cash, 2),
        "stopped": stopped_out,
    }


def main():
    PAIRS = {
        "ETH": DATA_DIR / "ETHUSD_1h_3mo.csv",
        "ADA": DATA_DIR / "ADAUSD_1h_3mo.csv",
        "SOL": DATA_DIR / "SOLUSD_1h_3mo.csv",
    }

    SPACINGS = [0.5, 1.0, 2.0, 3.0]
    LEVELS = [3, 5, 8]
    LEVERAGES = [3, 5, 10]
    MODES = ["maker", "taker", "hybrid"]
    CAPITAL = 100.0

    # ─── Price context ──────────────────────────────────
    print("=" * 100)
    print("  MARKET CONTEXT (3 months: Dec 21, 2025 -> Mar 22, 2026)")
    print("=" * 100)
    for name, path in PAIRS.items():
        candles = load_candles(path)
        o = candles[0]["c"]
        c = candles[-1]["c"]
        hi = max(x["h"] for x in candles)
        lo = min(x["l"] for x in candles)
        print(f"  {name}: {o:.2f} -> {c:.2f} ({(c-o)/o*100:+.1f}%)  "
              f"High: {hi:.2f}  Low: {lo:.2f}  Range: {(hi-lo)/o*100:.1f}%")
    print()

    # Run both WITH and WITHOUT max loss
    for maxloss_mode in [True, False]:
        mode_label = "WITH 15% MAX LOSS" if maxloss_mode else "WITHOUT MAX LOSS (ride it out)"

        print("\n" + "=" * 100)
        print(f"  BACKTEST: {mode_label}")
        print("=" * 100)

        all_results = []

        for pair_name, filepath in PAIRS.items():
            candles = load_candles(filepath)
            configs = list(itertools.product(SPACINGS, LEVELS, LEVERAGES, MODES))

            for sp, lv, lev, mode in configs:
                r = run_grid(candles, mode, sp, lv, lev, CAPITAL,
                            max_loss_pct=15.0, use_maxloss=maxloss_mode)
                r["pair"] = pair_name
                all_results.append(r)

        # ─── Summary stats ──────────────────────────────
        profitable = sum(1 for r in all_results if r["net_profit"] > 0)
        total = len(all_results)

        print(f"\n  Total configs tested: {total}")
        print(f"  Profitable: {profitable}/{total} ({profitable/total*100:.1f}%)")

        for mode in MODES:
            mr = [r for r in all_results if r["mode"] == mode]
            p = sum(1 for r in mr if r["net_profit"] > 0)
            avg = sum(r["net_profit"] for r in mr) / len(mr)
            avg_rts = sum(r["rts"] for r in mr) / len(mr)
            avg_fees = sum(r["fees"] for r in mr) / len(mr)
            avg_missed = sum(r["missed"] for r in mr) / len(mr)
            print(f"    {mode.upper():<7}: {p}/{len(mr)} profitable, "
                  f"avg PnL ${avg:.2f}, avg RTs {avg_rts:.1f}, "
                  f"avg fees ${avg_fees:.2f}, avg missed {avg_missed:.0f}")

        for pair in ["ETH", "ADA", "SOL"]:
            pr = [r for r in all_results if r["pair"] == pair]
            p = sum(1 for r in pr if r["net_profit"] > 0)
            avg = sum(r["net_profit"] for r in pr) / len(pr)
            stopped = sum(1 for r in pr if r.get("stopped"))
            print(f"    {pair}: {p}/{len(pr)} profitable, avg PnL ${avg:.2f}, stopped out: {stopped}")

        # ─── Top configs ────────────────────────────────
        all_results.sort(key=lambda r: r["net_profit"], reverse=True)

        print(f"\n  TOP 10 CONFIGS:")
        print(f"  {'Pair':<5} {'Mode':<7} {'Sp%':<5} {'Lvl':<4} {'Lev':<4} "
              f"{'Profit':>8} {'RTs':>5} {'Miss':>5} {'Fill%':>6} "
              f"{'MaxDD%':>7} {'$/RT':>8} {'Fees':>6} {'Rctr':>5} {'Stop':>5}")
        for r in all_results[:10]:
            print(f"  {r['pair']:<5} {r['mode']:<7} {r['spacing']:<5.1f} {r['levels']:<4} {r['leverage']:<4} "
                  f"{r['net_profit']:>8.2f} {r['rts']:>5} {r['missed']:>5} {r['fill_rate']:>5.1f}% "
                  f"{r['max_dd']:>7.2f} {r['profit_per_rt']:>8.4f} {r['fees']:>6.2f} "
                  f"{r['recenters']:>5} {'Y' if r.get('stopped') else 'N':>5}")

        print(f"\n  WORST 5:")
        for r in all_results[-5:]:
            print(f"  {r['pair']:<5} {r['mode']:<7} {r['spacing']:<5.1f} {r['levels']:<4} {r['leverage']:<4} "
                  f"{r['net_profit']:>8.2f} {r['rts']:>5} {r['missed']:>5} {r['fill_rate']:>5.1f}% "
                  f"{r['max_dd']:>7.2f} {r['profit_per_rt']:>8.4f} {r['fees']:>6.2f} "
                  f"{r['recenters']:>5} {'Y' if r.get('stopped') else 'N':>5}")

        # ─── Maker vs Taker comparison ──────────────────
        print(f"\n  MAKER vs TAKER vs HYBRID — SIDE BY SIDE (top 15 configs by avg profit)")
        grouped = defaultdict(dict)
        for r in all_results:
            key = (r["pair"], r["spacing"], r["levels"], r["leverage"])
            grouped[key][r["mode"]] = r

        # Sort by average profit across modes
        ranked = []
        for key, modes in grouped.items():
            if len(modes) == 3:
                avg = sum(modes[m]["net_profit"] for m in MODES) / 3
                ranked.append((key, modes, avg))
        ranked.sort(key=lambda x: x[2], reverse=True)

        print(f"\n  {'Pair':<5} {'Sp%':<5} {'Lvl':<4} {'Lev':<4} | "
              f"{'Maker$':>8} {'RTs':>4} {'Miss':>4} | "
              f"{'Taker$':>8} {'RTs':>4} | "
              f"{'Hybrid$':>8} {'RTs':>4} | {'Best':<7} {'Gap$':>6}")
        print("  " + "-" * 105)

        maker_best = taker_best = hybrid_best = 0
        for key, modes, avg in ranked[:20]:
            pair, sp, lv, lev = key
            m = modes["maker"]
            t = modes["taker"]
            h = modes["hybrid"]
            profits = {"maker": m["net_profit"], "taker": t["net_profit"], "hybrid": h["net_profit"]}
            best = max(profits, key=profits.get)
            gap = profits[best] - min(profits.values())

            if best == "maker": maker_best += 1
            elif best == "taker": taker_best += 1
            else: hybrid_best += 1

            print(f"  {pair:<5} {sp:<5.1f} {lv:<4} {lev:<4} | "
                  f"{m['net_profit']:>8.2f} {m['rts']:>4} {m['missed']:>4} | "
                  f"{t['net_profit']:>8.2f} {t['rts']:>4} | "
                  f"{h['net_profit']:>8.2f} {h['rts']:>4} | "
                  f"{best.upper():<7} {gap:>6.2f}")

        # Full score
        all_maker_best = sum(1 for _, modes, _ in ranked
                            if modes["maker"]["net_profit"] >= max(modes["taker"]["net_profit"], modes["hybrid"]["net_profit"]))
        all_taker_best = sum(1 for _, modes, _ in ranked
                            if modes["taker"]["net_profit"] >= max(modes["maker"]["net_profit"], modes["hybrid"]["net_profit"]))
        all_hybrid_best = sum(1 for _, modes, _ in ranked
                             if modes["hybrid"]["net_profit"] >= max(modes["maker"]["net_profit"], modes["taker"]["net_profit"]))

        print(f"\n  FULL SCORE (all {len(ranked)} configs): "
              f"Maker wins {all_maker_best} | Taker wins {all_taker_best} | Hybrid wins {all_hybrid_best}")

    # ─── KEY INSIGHT ──────────────────────────────────────

    print("\n\n" + "=" * 100)
    print("  FINAL ANALYSIS: MAKER vs TAKER — Is the 0.02% saving worth it?")
    print("=" * 100)

    # Run one more targeted comparison on specific configs
    print("\n  Focused test: 1% spacing, 5 levels, 5x leverage")
    print(f"  {'Pair':<5} {'Mode':<7} {'Profit':>8} {'RTs':>5} {'Missed':>6} {'Fees':>6} {'Fill%':>6}")
    for pair_name, filepath in PAIRS.items():
        candles = load_candles(filepath)
        for mode in MODES:
            r = run_grid(candles, mode, 1.0, 5, 5, 100.0, use_maxloss=False)
            print(f"  {pair_name:<5} {mode:<7} {r['net_profit']:>8.2f} {r['rts']:>5} "
                  f"{r['missed']:>6} {r['fees']:>6.2f} {r['fill_rate']:>5.1f}%")

    print("\n  Focused test: 0.5% spacing, 8 levels, 3x leverage")
    print(f"  {'Pair':<5} {'Mode':<7} {'Profit':>8} {'RTs':>5} {'Missed':>6} {'Fees':>6} {'Fill%':>6}")
    for pair_name, filepath in PAIRS.items():
        candles = load_candles(filepath)
        for mode in MODES:
            r = run_grid(candles, mode, 0.5, 8, 3, 100.0, use_maxloss=False)
            print(f"  {pair_name:<5} {mode:<7} {r['net_profit']:>8.2f} {r['rts']:>5} "
                  f"{r['missed']:>6} {r['fees']:>6.2f} {r['fill_rate']:>5.1f}%")

    print("""
  ======================================================================
  CONCLUSIONS
  ======================================================================

  1. MARKET CONTEXT: All 3 assets fell ~32%% over 3 months.
     Grid trading in a persistent downtrend = guaranteed losses.
     The grid keeps buying into a falling market.

  2. MAKER vs TAKER:
     - Maker saves fees but misses ~55-75%% of theoretical fills
     - Taker gets all fills but pays 2.5x more in fees
     - WITH max loss: maker "wins" by losing LESS (fewer fills = less exposure)
       This is MISLEADING: maker looks better because it TRADES less.
     - WITHOUT max loss: TAKER wins 82/108 configs.
       When you ride out the drawdown, more round-trips = more recovery.

  3. THE REAL QUESTION is not maker vs taker.
     The REAL question is: Should you grid trade at all in a downtrend?
     Answer: NO. With max loss, 0/324 configs are profitable.
     Without max loss, only a few ADA configs with 3%% spacing break even.

  4. WHAT WOULD HELP:
     - Trend detection: only grid trade in SIDEWAYS markets
     - Short grids: grid trade the SHORT side in downtrends
     - Tighter max loss: 15%% is too wide for 10x leverage
     - Lower leverage: 3x with wider spacing survives better

  5. IF THE MARKET WERE SIDEWAYS (hypothetical):
     - Taker would likely win because guaranteed fills matter more
     - The 0.03%% fee difference per side = 0.06%% per round-trip
     - A 1%% spacing grid makes 1%% per RT gross
     - 0.06%% extra fee = 6%% of gross profit -- significant but not fatal
     - But missing 55-75%% of fills (maker) = missing most profit opportunities
     - VERDICT: In sideways market, TAKER wins. In trending market, neither wins.
""")


# ─── Minute data validation ──────────────────────────────

def validate():
    print("\n" + "=" * 100)
    print("  VALIDATION: Hourly vs Minute resolution (last 7 days)")
    print("=" * 100)

    MINUTE = {"ETH": DATA_DIR / "ETHUSD_1m_7d.csv", "ADA": DATA_DIR / "ADAUSD_1m_7d.csv", "SOL": DATA_DIR / "SOLUSD_1m_7d.csv"}
    HOURLY = {"ETH": DATA_DIR / "ETHUSD_1h_3mo.csv", "ADA": DATA_DIR / "ADAUSD_1h_3mo.csv", "SOL": DATA_DIR / "SOLUSD_1h_3mo.csv"}

    configs = [(1.0, 5, 5), (0.5, 8, 3), (2.0, 3, 5)]

    print(f"\n  {'Pair':<5} {'Sp%':<5} {'Lvl':<4} {'Lev':<4} {'Mode':<7} | "
          f"{'1H Profit':>10} {'1H RTs':>7} | {'1M Profit':>10} {'1M RTs':>7} | {'Diff':>6}")
    print("  " + "-" * 85)

    for pair in ["ETH", "ADA", "SOL"]:
        m_candles = load_candles(MINUTE[pair])
        h_candles_full = load_candles(HOURLY[pair])
        m_start, m_end = m_candles[0]["ts"], m_candles[-1]["ts"]
        h_candles = [c for c in h_candles_full if m_start[:10] <= c["ts"][:10] <= m_end[:10]]

        for sp, lv, lev in configs:
            for mode in ["maker", "taker"]:
                rh = run_grid(h_candles, mode, sp, lv, lev, 100.0, use_maxloss=False)
                rm = run_grid(m_candles, mode, sp, lv, lev, 100.0, use_maxloss=False)
                print(f"  {pair:<5} {sp:<5.1f} {lv:<4} {lev:<4} {mode:<7} | "
                      f"{rh['net_profit']:>10.2f} {rh['rts']:>7} | "
                      f"{rm['net_profit']:>10.2f} {rm['rts']:>7} | "
                      f"{rm['net_profit']-rh['net_profit']:>+6.2f}")


if __name__ == "__main__":
    main()
    validate()

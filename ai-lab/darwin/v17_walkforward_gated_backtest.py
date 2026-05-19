"""
v17 Strategy Walk-Forward Backtest — WITH RegimeGate applied
Cycle 60 — 2026-05-18 18h Paris

Cycle 59 ran walk-forward without the gate and concluded:
  - Tight 1.5% beats Tony 3.0% by 2× over 239d cumulative.
  - But gate (not modeled) is "the real edge — at regime permis by gate,
    tight 1.5% capture mieux que Tony 3.0%."

Cycle 60 measures CONDITIONAL alpha: when gate is OPEN, which spacing is best?
If the gate filters out bear/sideways, the loss-floor of Tony 3.0% (vs tight 1.5%)
might disappear or even invert.

Methodology:
  - Per-pair gate (Python port of RegimeGate.java, IQR bounds from prod
    defaults Vmix 2026-05-09).
  - Build PerPairGate from FULL 4h cache (3 years) → EMA200/ADX/RSI/ATR
    stabilized before any simulated window.
  - At each 1min tick, lookup current 4h bar gate state. If CLOSED, grid
    behaves close_only (no new buys, sells still fire). If OPEN, full freedom.
  - Initial deploy only if gate OPEN at window start; else grid is dormant
    until first OPEN tick.

Compare to cycle 59 to quantify "alpha of gate × spacing interaction".

4 windows × 3 pairs × 5 configs = 60 simulations.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple

ROOT = Path("/home/tony/projets/tonyderide/niam-bay")
CACHE = ROOT / "ai-lab/darwin/data_cache"
sys.path.insert(0, str(ROOT / "ai-lab/darwin"))

from ppt_pause_backtest import GridState, load_candles
from regime_gate_logic import PerPairGate, GateBounds


# Production V4 bounds (from /home/ubuntu/martin/.env on VM Oracle, 2026-05-19).
# These are the bounds Martin actually uses live, NOT the wide Java defaults.
# Only ATR% and RSI are restrictive; the other 3 are effectively no-op.
PROD_V4_BOUNDS = GateBounds(
    adx_min=0.0, adx_max=100.0,
    price_vs_ema200_min=-50.0, price_vs_ema200_max=50.0,
    ema_spread_min=-20.0, ema_spread_max=20.0,
    atr_pct_min=1.12, atr_pct_max=2.17,
    rsi_min=36.0, rsi_max=66.0,
)


WINDOWS = [
    ("W1 bear 60j",   "1709251200000_1714435200000", "2024-03-01"),
    ("W2 bull 91j",   "1727740800000_1735603200000", "2024-10-01"),
    ("W3 bear 58j",   "1738368000000_1743379200000", "2025-02-01"),
    ("W4 mild+ 30j",  "30d",                          "2026-04-12"),
]

PAIRS = ["LINK", "ADA", "ETH"]

CONFIGS = [
    ("A v17 Tony 3.0%",  3.0,  4),
    ("B v17 tight 1.5%", 1.5,  4),
    ("C v17 med 2.0%",   2.0,  4),
    ("D v17 wide 4.0%",  4.0,  4),
    ("E v17 6lv 2.0%",   2.0,  6),
]

FOUR_H_FILE = CACHE / "binance_{pair}USDT_4h_1672531200000_1767139200000.json"
FOUR_H_EXTENDED_FILE = CACHE / "binance_{pair}USDT_4h_extended.json"
ONE_MIN_FILE = CACHE / "binance_{pair}USDT_1min_{suffix}.json"


def load_1m(pair: str, suffix: str) -> List[List]:
    p = Path(str(ONE_MIN_FILE).format(pair=pair, suffix=suffix))
    if not p.exists():
        return []
    return load_candles(p)


def load_4h_or_none(pair: str) -> List[List]:
    # Cycle 61: prefer extended cache (2023-01 → 2026-05) when available,
    # falls back to historical cache stopping 2025-12-31 for older script runs.
    ext = Path(str(FOUR_H_EXTENDED_FILE).format(pair=pair))
    if ext.exists():
        return load_candles(ext)
    p = Path(str(FOUR_H_FILE).format(pair=pair))
    if not p.exists():
        return []
    return load_candles(p)


def _new_grid_at(center_price: float, capital: float, leverage: int,
                 spacing_pct: float, levels: int,
                 max_loss_pct: float = 0.10) -> GridState:
    return GridState(
        center_price=center_price, capital_usd=capital, leverage=leverage,
        levels_count=levels, spacing_pct=spacing_pct,
        fees_pct=0.0005, max_loss_pct=max_loss_pct,
    )


def run_grid_gated(candles_1m: List[List], spacing_pct: float, levels: int,
                   gate: PerPairGate,
                   capital: float = 25.0, leverage: int = 7,
                   max_loss_pct: float = 0.10) -> Dict:
    """Grid with production-realistic gate lifecycle.

    On each 4h tick where gate state changes:
      - OPEN → CLOSED: close existing position at market (mimics AutoGridScheduler
        stopping the grid), grid becomes dormant.
      - CLOSED → OPEN: deploy fresh grid at current market price (matches
        AutoGridScheduler launching a new grid on regime reopen). Cumulative
        realized PnL, fills count and stop count carry across deploys.

    Hard-stop fires on per-grid basis: if a grid's net (realized+unrealized) within
    that deploy hits -capital*maxLoss → close position, that deploy ends, but the
    pair can still re-deploy on the next gate open (with same capital baseline).
    """
    if not candles_1m:
        return {"error": "no data"}

    # cumulative across redeploys
    cum_realized = 0.0
    total_fills = 0
    total_stops = 0
    deploys = 0

    grid = None  # current deploy or None when dormant
    last_gate_state = None  # 'open', 'closed', None
    last_gate_idx = -2
    open_ticks = 0
    closed_ticks = 0
    max_dd_pct = 0.0

    def market_close(g: GridState, price: float) -> float:
        if g.position_units == 0:
            return 0.0
        pnl = (price - g.avg_entry) * g.position_units
        pnl -= price * abs(g.position_units) * g.fees_pct
        g.realized_pnl += pnl
        g.position_units = 0.0
        return pnl

    for cd in candles_1m:
        ts_ms, o, h, low, close_p, _vol = cd
        idx = gate._idx_for_ts(ts_ms)
        if idx != last_gate_idx:
            snap = gate.evaluate(ts_ms)
            new_state = (None if snap is None
                         else ('open' if snap.open else 'closed'))
            if new_state == 'open':
                open_ticks += 1
            elif new_state == 'closed':
                closed_ticks += 1

            if last_gate_state in ('open', None) and new_state == 'closed':
                # OPEN/UNKNOWN → CLOSED: market-close any running grid
                if grid is not None and not grid.stopped:
                    market_close(grid, close_p)
                    cum_realized += grid.realized_pnl
                    total_fills += grid.fills
                    grid = None
            elif (last_gate_state in (None, 'closed')) and new_state == 'open':
                # Deploy fresh grid at current price
                grid = _new_grid_at(close_p, capital, leverage,
                                    spacing_pct, levels, max_loss_pct)
                deploys += 1

            last_gate_state = new_state
            last_gate_idx = idx

        if grid is not None and not grid.stopped:
            result = grid.tick(low=low, high=h, close=close_p)
            upnl = grid.unrealized(close_p)
            dd = -upnl / capital if upnl < 0 else 0.0
            if dd > max_dd_pct:
                max_dd_pct = dd
            if result == "STOP":
                total_stops += 1
                cum_realized += grid.realized_pnl
                total_fills += grid.fills
                grid = None

    # finalize any still-running grid at last close
    final_close = candles_1m[-1][4]
    final_grid_unreal = 0.0
    if grid is not None and not grid.stopped:
        # Mark-to-market without forcing close (window ended naturally)
        final_grid_unreal = grid.unrealized(final_close)
        cum_realized += grid.realized_pnl
        total_fills += grid.fills

    total_pnl = cum_realized + final_grid_unreal

    return {
        "fills": total_fills,
        "rt_approx": total_fills // 2,
        "deploys": deploys,
        "realized_pnl": round(cum_realized, 4),
        "unrealized_pnl_final": round(final_grid_unreal, 4),
        "total_pnl": round(total_pnl, 4),
        "max_drawdown_pct": round(max_dd_pct * 100, 2),
        "stopped_count": total_stops,
        "gate_open_ticks": open_ticks,
        "gate_closed_ticks": closed_ticks,
        "gate_open_pct": (
            round(100 * open_ticks / (open_ticks + closed_ticks), 1)
            if (open_ticks + closed_ticks) > 0 else 0.0
        ),
    }


def build_gate_for_pair(pair: str, window_end_ms: int) -> PerPairGate:
    """Load full 4h cache for `pair`, truncate at `window_end_ms`,
    return ready-to-evaluate gate. If 4h cache absent OR window extends past
    cache end, fall back to resampling within-window 1min (less warmup)."""
    c4h = load_4h_or_none(pair)
    if c4h and c4h[-1][0] >= window_end_ms:
        truncated = [c for c in c4h if c[0] <= window_end_ms]
        return PerPairGate(candles_4h=truncated, bounds=PROD_V4_BOUNDS)
    return None  # caller decides fallback


def main():
    print("=" * 90)
    print("V17 WALK-FORWARD WITH RegimeGate V4 (per-pair) — Cycle 60 — 2026-05-19")
    print("Gate bounds (PROD VM .env, validated 2026-05-09 10-trader audit):")
    print(f"  ADX∈[0,100] pVsE200∈[-50,+50]% spread∈[-20,+20]% (all no-op)")
    print(f"  ATR%∈[{PROD_V4_BOUNDS.atr_pct_min:.2f},{PROD_V4_BOUNDS.atr_pct_max:.2f}] "
          f"RSI∈[{PROD_V4_BOUNDS.rsi_min:.0f},{PROD_V4_BOUNDS.rsi_max:.0f}]  ← restrictive")
    print("=" * 90)

    results = {cfg[0]: {w[0]: {} for w in WINDOWS} for cfg in CONFIGS}
    stops = {cfg[0]: {w[0]: 0 for w in WINDOWS} for cfg in CONFIGS}
    gate_open_summary = {w[0]: {} for w in WINDOWS}

    for win_name, suffix, start_date in WINDOWS:
        print(f"\n--- {win_name} (start {start_date}) ---")
        for pair in PAIRS:
            candles = load_1m(pair, suffix)
            if not candles:
                print(f"  {pair}: MISSING 1min data ({suffix})")
                continue
            window_end_ms = candles[-1][0]
            gate = build_gate_for_pair(pair, window_end_ms)
            if gate is None:
                # fallback: resample within-window 1min (limited warmup)
                gate = PerPairGate(candles_1m=candles, bounds=PROD_V4_BOUNDS)
                print(f"  {pair}: 4h cache misses {win_name}, fallback to in-window resample "
                      f"(gate may stay UNKNOWN if <210 bars)")
            first = candles[0][4]
            last = candles[-1][4]
            chg = (last - first) / first * 100
            print(f"  {pair}: {len(candles)} 1min candles ({(candles[-1][0]-candles[0][0])/86400_000:.1f}j) "
                  f"price {chg:+.1f}% | gate 4h bars: {gate._n}")
            # report gate OPEN coverage over the window
            window_start_ms = candles[0][0]
            o = c = 0
            for i in range(gate._n):
                if gate.h4[i][0] < window_start_ms or gate.h4[i][0] > window_end_ms:
                    continue
                snap = gate.evaluate(gate.h4[i][0])
                if snap is None: continue
                if snap.open: o += 1
                else: c += 1
            tot = o + c
            gate_pct = 100 * o / tot if tot else 0.0
            gate_open_summary[win_name][pair] = (o, c, gate_pct)
            print(f"     gate window: {o}/{tot} OPEN ({gate_pct:.0f}%)")

            for label, spacing, lvls in CONFIGS:
                r = run_grid_gated(candles, spacing/100.0, lvls, gate)
                pnl = r.get("total_pnl", 0.0)
                results[label][win_name][pair] = pnl
                if r.get("stopped"):
                    stops[label][win_name] += 1
                tag = "STOP" if r.get("stopped") else "ok  "
                print(f"     {label:18s}: PnL=${pnl:+7.3f} fills={r.get('fills',0):2d} "
                      f"maxDD={r.get('max_drawdown_pct',0):5.2f}% [{tag}]")

    # heatmap
    print("\n" + "=" * 90)
    print("HEATMAP — ΣPnL across 3 pairs (LINK+ADA+ETH) per (config × window) — gate ON")
    print("=" * 90)
    header = f"{'config':<18}|" + "|".join(f"{w[0]:>14s}" for w in WINDOWS) + "|" + f"{'TOTAL':>10s}"
    print(header)
    print("-" * len(header))
    config_totals = {}
    for label, _, _ in CONFIGS:
        row = f"{label:<18}|"
        total = 0.0
        for w in WINDOWS:
            wn = w[0]
            s = sum(results[label][wn].values())
            sc = stops[label][wn]
            cell = f"${s:+7.2f} ({sc}st)"
            row += f"{cell:>14s}|"
            total += s
        config_totals[label] = total
        row += f" ${total:+8.2f}"
        print(row)

    # gate coverage summary
    print("\n" + "=" * 90)
    print("GATE COVERAGE — % of in-window 4h bars where gate is OPEN")
    print("=" * 90)
    print(f"{'pair':<6}|" + "|".join(f"{w[0]:>14s}" for w in WINDOWS))
    for pair in PAIRS:
        row = f"{pair:<6}|"
        for w in WINDOWS:
            tup = gate_open_summary[w[0]].get(pair)
            if tup is None:
                row += f"{'n/a':>14s}|"
            else:
                _, _, pct = tup
                row += f"{pct:>13.0f}%|"
        print(row)

    # final ranking
    print("\n" + "=" * 90)
    print("FINAL RANKING by total PnL across all 4 windows × 3 pairs:")
    print("=" * 90)
    ranked = sorted(config_totals.items(), key=lambda kv: -kv[1])
    for i, (label, t) in enumerate(ranked, 1):
        marker = "  ← Tony v17" if "Tony" in label else ""
        print(f"  {i}. {label:<18}  ${t:+8.2f}{marker}")

    # rank stability
    print("\n" + "=" * 90)
    print("STABILITY — rank per window (1=best, 5=worst)")
    print("=" * 90)
    print(f"{'config':<18}|" + "|".join(f"{w[0]:>14s}" for w in WINDOWS) + "|  meanRank")
    cfg_ranks = {label: [] for label, _, _ in CONFIGS}
    for w in WINDOWS:
        wn = w[0]
        sums = [(label, sum(results[label][wn].values())) for label, _, _ in CONFIGS]
        sums.sort(key=lambda kv: -kv[1])
        for rank_idx, (label, _) in enumerate(sums, 1):
            cfg_ranks[label].append(rank_idx)
    for label, _, _ in CONFIGS:
        ranks = cfg_ranks[label]
        mean_rank = sum(ranks) / len(ranks)
        row = f"{label:<18}|" + "|".join(f"{r:>14d}" for r in ranks) + f"|  {mean_rank:.2f}"
        print(row)

    print("\nINTERPRETATION:")
    print("- Compare to cycle 59 no-gate ranking to see conditional alpha of gate × spacing.")
    print("- If Tony 3.0% climbs the ranking with gate ON, Tony's choice is validated for")
    print("  the bull/permis regime that the gate selects.")
    print("- If tight 1.5% still wins with gate ON, switch v17→v18 recommendation stands.")


if __name__ == "__main__":
    main()

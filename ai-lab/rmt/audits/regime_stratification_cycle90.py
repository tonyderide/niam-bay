"""Cycle 90 — Regime stratification of the anchor edge.

Cycles 85b/87/88/89 established that adding BTC to a Martin allocation universe
adds ~+0.13 to +0.32 ΔSharpe (min-variance vs equal-weight) across N ∈ {3,4,5,6,7}.
The 3-year backtest (2023-01 → 2026-01) aggregates across all market regimes.

Risk flagged at the end of cycle 89:
    "The walk-forward window is fixed; no stratification by regime (bull/bear/range).
     The BTC edge could be very different in pure bull (where BTC behaves like any alt)."

Cycle 90 answers that: re-compute ΔSharpe with-BTC vs no-BTC, *conditional* on the BTC
regime over the OOS chunk.

Methodology:
    1. Load BTC 4h prices on canonical 3-year window, compute EMA200 + EMA50.
    2. Classify each period into a regime:
         BULL    : BTC > EMA200 AND EMA200 slope > 0
         BEAR    : BTC < EMA200 AND EMA200 slope < 0
         RANGE   : otherwise (transitions, sideways)
    3. For each universe of cycle 89 (8 universes, N=6 and N=7):
       run walk-forward, label each OOS-42-chunk by the regime majority during it,
       then aggregate Sharpe per regime.
    4. Compute ΔSharpe (mv - eq) per regime per universe.
    5. Aggregate: avg ΔSharpe with-BTC vs no-BTC per regime.

Pre-registered hypotheses (rule cycle 86 — verdicts mechanical):

    H_uniform : ΔSharpe_with_BTC is similar (within ±0.10) across all 3 regimes
                → BTC anchor edge is universal, not a bear-window artefact.
                → confirms the rule survives regime decomposition.

    H_bear_concentrated : ΔSharpe_with_BTC is much larger (≥+0.20 diff) in BEAR than BULL
                → BTC anchor edge IS a bear-window phenomenon.
                → restricts the actionable rule: only useful when BTC regime is BEAR/RANGE.

    H_bull_kills : ΔSharpe_with_BTC ≤ 0 in BULL regime
                → BTC anchor *hurts* in bull markets (drag from defensive weight).
                → operational rule: disable anchor when BTC > EMA200 + slope up.

    H_mixed : trajectory doesn't fit any of the above cleanly.

Pre-registered BEFORE the run reads results.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from rmt.data_loader import load_panel_returns, load_pair_returns
from rmt.martin_allocation import allocate_capital

TOTAL_CAPITAL = 120.0
TF = "4h"
WINDOW = 360
REBALANCE_STEP = 42
ANNUALIZE = 6 * 365  # 4h candles per year ≈ 2190

EMA_FAST = 50
EMA_SLOW = 200


def realized_sharpe(returns: pd.Series, ann: int = ANNUALIZE) -> float:
    if returns.std() <= 0 or len(returns) == 0:
        return 0.0
    return float(returns.mean() / returns.std() * np.sqrt(ann))


def eq_strategy(train: pd.DataFrame) -> pd.Series:
    n = train.shape[1]
    return pd.Series([1.0 / n] * n, index=train.columns)


def mv_floor_10_strategy(train: pd.DataFrame) -> pd.Series:
    alloc = allocate_capital(
        train,
        total_capital=TOTAL_CAPITAL,
        method="raw",
        min_capital_per_pair=10.0,
    )
    return pd.Series(alloc) / TOTAL_CAPITAL


def build_btc_regime() -> pd.Series:
    """Return Series of regime labels indexed by 4h timestamps.

    Labels: 'BULL', 'BEAR', 'RANGE'.
    BTC log-returns are derived from canonical 3-year cache.
    """
    btc_rets = load_pair_returns("BTC", tf=TF)
    # cumulative log price (in arbitrary units; comparison is what matters)
    log_price = btc_rets["BTC"].cumsum()
    ema_fast = log_price.ewm(span=EMA_FAST, adjust=False).mean()
    ema_slow = log_price.ewm(span=EMA_SLOW, adjust=False).mean()
    slope = ema_slow.diff(EMA_FAST)  # slope over EMA_FAST candles

    regime = pd.Series("RANGE", index=log_price.index, dtype=object)
    bull_mask = (log_price > ema_slow) & (slope > 0)
    bear_mask = (log_price < ema_slow) & (slope < 0)
    regime[bull_mask] = "BULL"
    regime[bear_mask] = "BEAR"
    return regime


def walk_forward_with_regime(
    rets: pd.DataFrame,
    strategy_fn,
    regime_labels: pd.Series,
    window: int = WINDOW,
    step: int = REBALANCE_STEP,
) -> pd.DataFrame:
    """Run walk-forward and tag each OOS chunk with its dominant regime.

    Returns:
        DataFrame with columns: 'ret', 'regime'.
    """
    n = len(rets)
    out_chunks = []
    t = window
    while t + step <= n:
        train = rets.iloc[t - window : t]
        weights = strategy_fn(train)
        oos = rets.iloc[t : t + step]
        port = (oos * weights.reindex(oos.columns).values).sum(axis=1)
        # majority regime over OOS window
        oos_regimes = regime_labels.reindex(oos.index)
        if oos_regimes.isna().all():
            dominant = "RANGE"
        else:
            dominant = oos_regimes.value_counts().idxmax()
        chunk = pd.DataFrame({"ret": port, "regime": dominant})
        out_chunks.append(chunk)
        t += step
    return pd.concat(out_chunks) if out_chunks else pd.DataFrame(columns=["ret", "regime"])


UNIVERSES = [
    # Reuse cycle 89 universes for direct comparison
    ("N6_LINK_ADA_SOL_ETH_BTC_AVAX", ["LINK", "ADA", "SOL", "ETH", "BTC", "AVAX"], 6, True),
    ("N6_LINK_ADA_SOL_ETH_BTC_APT", ["LINK", "ADA", "SOL", "ETH", "BTC", "APT"], 6, True),
    ("N6_LINK_ADA_SOL_ETH_AVAX_APT", ["LINK", "ADA", "SOL", "ETH", "AVAX", "APT"], 6, False),
    ("N7_LINK_ADA_SOL_ETH_BTC_AVAX_APT", ["LINK", "ADA", "SOL", "ETH", "BTC", "AVAX", "APT"], 7, True),
    ("N7_LINK_ADA_SOL_ETH_BTC_AVAX_OP", ["LINK", "ADA", "SOL", "ETH", "BTC", "AVAX", "OP"], 7, True),
    ("N7_LINK_ADA_SOL_ETH_AVAX_APT_OP", ["LINK", "ADA", "SOL", "ETH", "AVAX", "APT", "OP"], 7, False),
    # Also re-add N=4 and N=5 anchors to cover the full trajectory under regime lens
    ("N4_LINK_ADA_BTC_ETH", ["LINK", "ADA", "BTC", "ETH"], 4, True),
    ("N4_LINK_ADA_SOL_ETH", ["LINK", "ADA", "SOL", "ETH"], 4, False),
    ("N5_LINK_ADA_SOL_ETH_BTC", ["LINK", "ADA", "SOL", "ETH", "BTC"], 5, True),
    ("N5_LINK_ADA_SOL_ETH_AVAX", ["LINK", "ADA", "SOL", "ETH", "AVAX"], 5, False),
]


def main():
    print("=== Cycle 90 — Regime stratification of the anchor edge ===\n")

    regime_labels = build_btc_regime()
    print("BTC regime label distribution (full 3-year cache, 4h candles):")
    print(regime_labels.value_counts().to_string())
    print(f"  total = {len(regime_labels)} candles\n")

    rows = []
    for name, pairs, n, has_btc in UNIVERSES:
        try:
            rets = load_panel_returns(pairs, tf=TF)
        except FileNotFoundError as e:
            print(f"{name:36s}  SKIP  {e}")
            continue

        df_eq = walk_forward_with_regime(rets, eq_strategy, regime_labels)
        df_mv = walk_forward_with_regime(rets, mv_floor_10_strategy, regime_labels)

        # Sharpe per regime for both strategies
        regimes = ["BULL", "BEAR", "RANGE"]
        per_regime = {}
        for reg in regimes:
            ret_eq = df_eq.loc[df_eq["regime"] == reg, "ret"]
            ret_mv = df_mv.loc[df_mv["regime"] == reg, "ret"]
            sh_eq = realized_sharpe(ret_eq)
            sh_mv = realized_sharpe(ret_mv)
            per_regime[reg] = {
                "sh_eq": sh_eq,
                "sh_mv": sh_mv,
                "delta": sh_mv - sh_eq,
                "n_chunks": int((df_eq["regime"] == reg).sum() // REBALANCE_STEP),
                "n_obs": int(len(ret_eq)),
            }

        # also total (no regime split)
        all_eq = realized_sharpe(df_eq["ret"])
        all_mv = realized_sharpe(df_mv["ret"])

        row = {
            "universe": name,
            "n": n,
            "has_btc": has_btc,
            "sh_eq_all": all_eq,
            "sh_mv_all": all_mv,
            "delta_all": all_mv - all_eq,
        }
        for reg in regimes:
            row[f"delta_{reg}"] = per_regime[reg]["delta"]
            row[f"n_obs_{reg}"] = per_regime[reg]["n_obs"]
        rows.append(row)

        print(f"{name:36s}  N={n}  has_BTC={has_btc}")
        print(f"  Δ all   = {row['delta_all']:+.3f}")
        for reg in regimes:
            d = per_regime[reg]
            print(
                f"  Δ {reg:5s} = {d['delta']:+.3f}  "
                f"(eq={d['sh_eq']:+.3f} mv={d['sh_mv']:+.3f}, n_obs={d['n_obs']})"
            )
        print()

    df = pd.DataFrame(rows)
    out_csv = Path(__file__).parent / "regime_stratification_cycle90_results.csv"
    df.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}\n")

    print("=== Aggregates: avg ΔSharpe per regime, with-BTC vs no-BTC ===\n")
    print(f"{'N':>3}  {'regime':<6}  {'with_BTC':>9}  {'no_BTC':>8}  {'BTC_effect':>10}")
    for n_val in sorted(df["n"].unique()):
        for reg in ["BULL", "BEAR", "RANGE", "all"]:
            col = "delta_all" if reg == "all" else f"delta_{reg}"
            sub_btc = df[(df["n"] == n_val) & df["has_btc"]][col]
            sub_no = df[(df["n"] == n_val) & ~df["has_btc"]][col]
            if len(sub_btc) == 0 or len(sub_no) == 0:
                continue
            avg_btc = float(sub_btc.mean())
            avg_no = float(sub_no.mean())
            diff = avg_btc - avg_no
            print(
                f"{n_val:>3}  {reg:<6}  {avg_btc:+9.3f}  {avg_no:+8.3f}  {diff:+10.3f}"
            )
        print()

    print("=== Hypothesis verdicts (pre-registered) ===\n")
    # Aggregate across all N for the global verdict
    global_btc = df[df["has_btc"]]
    global_no = df[~df["has_btc"]]
    overall = {}
    for reg in ["BULL", "BEAR", "RANGE"]:
        col = f"delta_{reg}"
        overall[reg] = float(global_btc[col].mean()) - float(global_no[col].mean())

    bull_eff = overall["BULL"]
    bear_eff = overall["BEAR"]
    range_eff = overall["RANGE"]

    print(f"Global BTC effect by regime (mean across all N tested):")
    print(f"  BULL  : {bull_eff:+.3f}")
    print(f"  BEAR  : {bear_eff:+.3f}")
    print(f"  RANGE : {range_eff:+.3f}\n")

    spread = max(bull_eff, bear_eff, range_eff) - min(bull_eff, bear_eff, range_eff)
    print(f"Spread (max - min) across regimes: {spread:+.3f}\n")

    # mechanical verdict
    if bull_eff <= 0:
        verdict = "H_bull_kills"
        interp = "BTC anchor HURTS in bull markets — disable anchor when BTC > EMA200 + slope up"
    elif spread <= 0.10:
        verdict = "H_uniform"
        interp = "Edge similar across regimes — anchor rule survives regime decomposition"
    elif bear_eff - bull_eff >= 0.20:
        verdict = "H_bear_concentrated"
        interp = "Edge concentrated in BEAR — rule actionable only when BTC bearish or ranging"
    else:
        verdict = "H_mixed"
        interp = "Edge varies but pattern doesn't fit clean hypotheses — judgment call"

    print(f"→ Verdict: {verdict}")
    print(f"  {interp}\n")


if __name__ == "__main__":
    main()

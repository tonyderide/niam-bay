"""Cycle 89 — Perturbation N=6 + N=7: closing the frontier of the anchor edge.

Trajectory established by cycles 85b/87/88:
  N=3 (cycle 85b): with-BTC ΔSharpe=+0.320, no-BTC=+0.026, BTC effect=+0.294
  N=4 (cycle 87) : with-BTC ΔSharpe=+0.302, no-BTC=-0.032, BTC effect=+0.334
  N=5 (cycle 88) : with-BTC ΔSharpe=+0.283, no-BTC=+0.050, BTC effect=+0.233

Observed pattern:
  - with-BTC ΔSharpe monotonically decreasing (0.320 → 0.302 → 0.283), ~6% erosion per N
  - BTC effect (diff vs no-BTC) collapses -30% between N=4 and N=5 (no-BTC catches up)
  - BTC weight in min-variance: 82% → 65% → 58% (1/N dilution)

Cycle 89 hypothesis: the trajectory extrapolated forward predicts:
  - N=6 with-BTC ΔSharpe ≈ +0.26 (linear erosion), no-BTC ≈ +0.10
  - N=7 with-BTC ΔSharpe ≈ +0.24, no-BTC ≈ +0.13

If linear extrapolation holds → frontier still distant.
If non-linear collapse (similar to BTC-effect crash N=4→N=5) → frontier ≈ N=6-7.

Test universes N=6 (3 with-BTC, 2 no-BTC):
  LINK+ADA+SOL+ETH+BTC+AVAX  : 4 alts + BTC + AVAX
  LINK+ADA+SOL+ETH+BTC+APT   : 4 alts + BTC + APT
  LINK+ADA+SOL+ETH+BTC+SUI   : 4 alts + BTC + SUI (fresh anchor mix)
  LINK+ADA+SOL+ETH+AVAX+APT  : 6 alts no anchor (control 1)
  LINK+ADA+SOL+ETH+AVAX+OP   : 6 alts no anchor (control 2)

Test universes N=7 (2 with-BTC, 1 no-BTC):
  LINK+ADA+SOL+ETH+BTC+AVAX+APT : 5 alts + BTC + AVAX + APT
  LINK+ADA+SOL+ETH+BTC+AVAX+OP  : 5 alts + BTC + AVAX + OP
  LINK+ADA+SOL+ETH+AVAX+APT+OP  : 7 alts no anchor (control)

Pre-registered hypotheses (rule cycle 86 — verdict applied mechanically):

  N=6 verdict:
    H6_robust : avg ΔSharpe with-BTC ≥ +0.22 → trajectory continues, frontier ≥ N=7
    H6_erode  : avg ΔSharpe with-BTC ∈ [+0.10, +0.22) → erosion accelerating, frontier near
    H6_dies   : avg ΔSharpe with-BTC < +0.10 → frontier at N=6, restrict rule to N ∈ {3,4,5}

  N=7 verdict:
    H7_robust : avg ΔSharpe with-BTC ≥ +0.18 → edge resilient to N=7, frontier still distant
    H7_erode  : avg ΔSharpe with-BTC ∈ [+0.08, +0.18) → marginal, decision boundary
    H7_dies   : avg ΔSharpe with-BTC < +0.08 → frontier at N=7, restrict rule to N ∈ {3,4,5,6}

  Composite verdict (rule for documenting frontier):
    BOTH robust  → trajectory linear, no observable frontier in {3..7}, suggest extrapolation valid further
    N=6 OK, N=7 dies → frontier between N=6 and N=7
    N=6 dies → frontier at N=6, no need to test N=7 result
    Erode tier → judgment call, document erosion trajectory shape

Pre-registered BEFORE the run reads results. Script is the contract.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from rmt.data_loader import load_panel_returns
from rmt.martin_allocation import allocate_capital

TOTAL_CAPITAL = 120.0
TF = "4h"
WINDOW = 360
REBALANCE_STEP = 42
ANNUALIZE = 6 * 365


def realized_sharpe(returns: pd.Series, ann: int = ANNUALIZE) -> float:
    if returns.std() <= 0 or len(returns) == 0:
        return 0.0
    return float(returns.mean() / returns.std() * np.sqrt(ann))


def max_drawdown(returns: pd.Series) -> float:
    cum = returns.cumsum()
    peak = cum.cummax()
    dd = cum - peak
    return float(dd.min())


def walk_forward(rets, strategy_fn, window=WINDOW, step=REBALANCE_STEP):
    n = len(rets)
    out_chunks = []
    t = window
    while t + step <= n:
        train = rets.iloc[t - window : t]
        weights = strategy_fn(train)
        oos = rets.iloc[t : t + step]
        port = (oos * weights.reindex(oos.columns).values).sum(axis=1)
        out_chunks.append(port)
        t += step
    return pd.concat(out_chunks) if out_chunks else pd.Series(dtype=float)


def eq_strategy(train):
    n = train.shape[1]
    return pd.Series([1.0 / n] * n, index=train.columns)


def mv_floor_10_strategy(train):
    alloc = allocate_capital(
        train,
        total_capital=TOTAL_CAPITAL,
        method="raw",
        min_capital_per_pair=10.0,
    )
    return pd.Series(alloc) / TOTAL_CAPITAL


UNIVERSES = [
    # --- N=6 with BTC ---
    ("N6_LINK_ADA_SOL_ETH_BTC_AVAX", ["LINK", "ADA", "SOL", "ETH", "BTC", "AVAX"], "4 alts + BTC + AVAX", 6, True),
    ("N6_LINK_ADA_SOL_ETH_BTC_APT", ["LINK", "ADA", "SOL", "ETH", "BTC", "APT"], "4 alts + BTC + APT", 6, True),
    ("N6_LINK_ADA_SOL_ETH_BTC_SUI", ["LINK", "ADA", "SOL", "ETH", "BTC", "SUI"], "4 alts + BTC + SUI", 6, True),
    # --- N=6 no BTC (control) ---
    ("N6_LINK_ADA_SOL_ETH_AVAX_APT", ["LINK", "ADA", "SOL", "ETH", "AVAX", "APT"], "6 alts no anchor", 6, False),
    ("N6_LINK_ADA_SOL_ETH_AVAX_OP", ["LINK", "ADA", "SOL", "ETH", "AVAX", "OP"], "6 alts no anchor v2", 6, False),
    # --- N=7 with BTC ---
    ("N7_LINK_ADA_SOL_ETH_BTC_AVAX_APT", ["LINK", "ADA", "SOL", "ETH", "BTC", "AVAX", "APT"], "5 alts + BTC + AVAX + APT", 7, True),
    ("N7_LINK_ADA_SOL_ETH_BTC_AVAX_OP", ["LINK", "ADA", "SOL", "ETH", "BTC", "AVAX", "OP"], "5 alts + BTC + AVAX + OP", 7, True),
    # --- N=7 no BTC (control) ---
    ("N7_LINK_ADA_SOL_ETH_AVAX_APT_OP", ["LINK", "ADA", "SOL", "ETH", "AVAX", "APT", "OP"], "7 alts no anchor", 7, False),
]


def main():
    print("=== Cycle 89 — Perturbation N=6 + N=7: closing the frontier ===\n")

    rows = []
    for name, pairs, desc, n, has_btc in UNIVERSES:
        try:
            rets = load_panel_returns(pairs, tf=TF)
        except FileNotFoundError as e:
            print(f"{name:36s}  SKIP  {e}")
            continue

        oos_eq = walk_forward(rets, eq_strategy)
        oos_mv = walk_forward(rets, mv_floor_10_strategy)

        sh_eq, sh_mv = realized_sharpe(oos_eq), realized_sharpe(oos_mv)
        dd_eq, dd_mv = max_drawdown(oos_eq), max_drawdown(oos_mv)

        weights_path = []
        t = WINDOW
        while t + REBALANCE_STEP <= len(rets):
            train = rets.iloc[t - WINDOW : t]
            w = mv_floor_10_strategy(train)
            weights_path.append(w)
            t += REBALANCE_STEP
        avg_w = pd.DataFrame(weights_path).mean()

        anchor = "BTC" if "BTC" in pairs else ("ETH" if "ETH" in pairs else pairs[0])
        anchor_weight = float(avg_w[anchor])

        delta_sharpe = sh_mv - sh_eq
        dd_ratio = dd_mv / dd_eq if dd_eq != 0 else float("nan")

        rows.append({
            "universe": name,
            "desc": desc,
            "n": n,
            "has_btc": has_btc,
            "sh_eq": sh_eq,
            "sh_mv": sh_mv,
            "delta_sharpe": delta_sharpe,
            "dd_eq": dd_eq,
            "dd_mv": dd_mv,
            "dd_ratio": dd_ratio,
            "anchor": anchor,
            "anchor_avg_weight": anchor_weight,
            "n_periods": len(oos_eq),
        })

        print(f"{name:36s}  {desc}")
        print(f"  Sharpe  eq={sh_eq:+.3f}  mv={sh_mv:+.3f}  Δ={delta_sharpe:+.3f}")
        print(f"  maxDD   eq={dd_eq:+.3f}  mv={dd_mv:+.3f}  ratio={dd_ratio:.2f}")
        print(f"  Anchor {anchor} avg weight in mv: {anchor_weight:.1%}")
        print()

    df = pd.DataFrame(rows)
    out_csv = Path(__file__).parent / "perturbation_universe_cycle89_results.csv"
    df.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}\n")

    print("=== Hypothesis verdicts (pre-registered) ===\n")

    for target_n, h_robust_thr, h_erode_thr in [(6, 0.22, 0.10), (7, 0.18, 0.08)]:
        sub_btc = [r for r in rows if r["n"] == target_n and r["has_btc"]]
        sub_no = [r for r in rows if r["n"] == target_n and not r["has_btc"]]
        if not sub_btc:
            print(f"N={target_n}: no with-BTC results")
            continue
        avg_btc = float(np.mean([r["delta_sharpe"] for r in sub_btc]))
        avg_no = float(np.mean([r["delta_sharpe"] for r in sub_no])) if sub_no else float("nan")
        diff = avg_btc - avg_no if sub_no else float("nan")
        weight_btc = float(np.mean([r["anchor_avg_weight"] for r in sub_btc]))
        print(f"N={target_n}:")
        print(f"  avg ΔSharpe with-BTC : {avg_btc:+.3f}  (n={len(sub_btc)} universes)")
        print(f"  avg ΔSharpe no-BTC   : {avg_no:+.3f}  (n={len(sub_no)} universes)")
        print(f"  BTC effect (diff)    : {diff:+.3f}")
        print(f"  BTC avg weight in mv : {weight_btc:.1%}")
        if avg_btc >= h_robust_thr:
            verdict = f"H{target_n}_robust"
            interp = f"edge robust at N={target_n}, frontier still distant"
        elif avg_btc >= h_erode_thr:
            verdict = f"H{target_n}_erode"
            interp = f"partial erosion at N={target_n}, marginal but not killed"
        else:
            verdict = f"H{target_n}_dies"
            interp = f"frontier reached at N={target_n}, restrict rule to N below"
        print(f"  → {verdict}: {interp}\n")

    print("=== Trajectory N=3..7 (avg ΔSharpe with-BTC) ===\n")
    print("  N=3 (cycle 85b): +0.320")
    print("  N=4 (cycle 87) : +0.302")
    print("  N=5 (cycle 88) : +0.283")
    sub6 = [r for r in rows if r["n"] == 6 and r["has_btc"]]
    sub7 = [r for r in rows if r["n"] == 7 and r["has_btc"]]
    if sub6:
        v6 = float(np.mean([r["delta_sharpe"] for r in sub6]))
        print(f"  N=6 (cycle 89) : {v6:+.3f}")
    if sub7:
        v7 = float(np.mean([r["delta_sharpe"] for r in sub7]))
        print(f"  N=7 (cycle 89) : {v7:+.3f}")
    print()


if __name__ == "__main__":
    main()

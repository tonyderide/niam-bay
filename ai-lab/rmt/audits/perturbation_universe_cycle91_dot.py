"""Cycle 91 — DOT inclusion test: does the anchor edge survive with a live-traded pair?

Cycles 85b-90 validated the BTC-anchor effect but never tested DOT, which is
in Martin's live strategy (status 0511). This cycle adds DOT to N=4 and N=5
universes — both with-BTC (does anchor still dominate?) and no-BTC (does DOT
become a quasi-anchor or behave like another alt?).

Pre-registered hypotheses (rule cycle 86):
  H_DOT_compatible : with-BTC avg ΔSharpe ≥ +0.20 at N=4 AND ≥ +0.18 at N=5
                     (i.e. DOT-containing universes behave like cycle 87/88 averages)
  H_DOT_neutral_in_no_BTC : no-BTC with DOT avg ΔSharpe in [-0.05, +0.15]
                     (DOT does not become an unexpected mini-anchor)
  H_DOT_breaks : either with-BTC avg < +0.10 (DOT poisons the anchor)
                 OR no-BTC with DOT avg > +0.20 (DOT becomes anchor — pattern shifts)

Coordonnées de réfutation :
  - if any DOT universe shows |ΔSharpe| outlier > 2× cycle 89 stdev → flag
  - if DOT in mv weights > 35% on average → DOT acts as anchor, semantic shift

Output: append findings to vacation-autonomy.md as cycle 91.
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


# N=4 universes with DOT
# N=5 universes with DOT
UNIVERSES = [
    # N=4 with-BTC + DOT
    ("LINK_ADA_DOT_BTC", ["LINK", "ADA", "DOT", "BTC"], 4, True, "DOT replaces SOL/ETH (alts+BTC)"),
    ("DOT_ADA_ETH_BTC",  ["DOT", "ADA", "ETH", "BTC"], 4, True, "DOT replaces LINK"),
    ("LINK_DOT_SOL_BTC", ["LINK", "DOT", "SOL", "BTC"], 4, True, "DOT replaces ADA"),
    # N=4 no-BTC + DOT
    ("LINK_ADA_DOT_ETH", ["LINK", "ADA", "DOT", "ETH"], 4, False, "DOT in no-anchor control"),
    ("LINK_ADA_SOL_DOT", ["LINK", "ADA", "SOL", "DOT"], 4, False, "DOT replaces ETH (no anchor)"),
    # N=5 with-BTC + DOT
    ("LINK_ADA_SOL_DOT_BTC", ["LINK", "ADA", "SOL", "DOT", "BTC"], 5, True, "5 = canonical +DOT"),
    ("LINK_ADA_ETH_DOT_BTC", ["LINK", "ADA", "ETH", "DOT", "BTC"], 5, True, "5 = ETH variant +DOT"),
    # N=5 no-BTC + DOT
    ("LINK_ADA_SOL_ETH_DOT", ["LINK", "ADA", "SOL", "ETH", "DOT"], 5, False, "5 alts no anchor +DOT"),
]


def main():
    print("=== Cycle 91 — Perturbation: DOT inclusion in N=4 + N=5 universes ===\n")

    rows = []
    for name, pairs, n, has_btc, desc in UNIVERSES:
        try:
            rets = load_panel_returns(pairs, tf=TF)
        except FileNotFoundError as e:
            print(f"{name}  SKIP  {e}")
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

        anchor = "BTC" if has_btc else ("ETH" if "ETH" in pairs else pairs[0])
        anchor_weight = float(avg_w[anchor])
        dot_weight = float(avg_w["DOT"]) if "DOT" in pairs else float("nan")

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
            "dot_avg_weight": dot_weight,
            "n_periods": len(oos_eq),
        })

        print(f"{name:24s}  N={n} BTC={has_btc} — {desc}")
        print(f"  Sharpe  eq={sh_eq:+.3f}  mv={sh_mv:+.3f}  Δ={delta_sharpe:+.3f}")
        print(f"  maxDD   eq={dd_eq:+.3f}  mv={dd_mv:+.3f}  ratio={dd_ratio:.2f}")
        print(f"  Anchor {anchor} weight: {anchor_weight:.1%}   DOT weight: {dot_weight:.1%}")
        print()

    df = pd.DataFrame(rows)
    out_csv = Path(__file__).parent / "perturbation_universe_cycle91_dot_results.csv"
    df.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}\n")

    print("=== Hypothesis verdicts ===")
    n4_btc = [r for r in rows if r["n"] == 4 and r["has_btc"]]
    n4_no = [r for r in rows if r["n"] == 4 and not r["has_btc"]]
    n5_btc = [r for r in rows if r["n"] == 5 and r["has_btc"]]
    n5_no = [r for r in rows if r["n"] == 5 and not r["has_btc"]]

    avg = lambda xs: float(np.mean([r["delta_sharpe"] for r in xs])) if xs else float("nan")
    a4b, a4n, a5b, a5n = avg(n4_btc), avg(n4_no), avg(n5_btc), avg(n5_no)
    print(f"N=4 with-BTC (with DOT) avg ΔSharpe: {a4b:+.3f}  (cycle 87 baseline +0.302)")
    print(f"N=4 no-BTC  (with DOT) avg ΔSharpe: {a4n:+.3f}  (cycle 87 baseline -0.032)")
    print(f"N=5 with-BTC (with DOT) avg ΔSharpe: {a5b:+.3f}  (cycle 88 baseline +0.283)")
    print(f"N=5 no-BTC  (with DOT) avg ΔSharpe: {a5n:+.3f}  (cycle 88 baseline +0.050)")

    print()
    # H_DOT_compatible
    compat = a4b >= 0.20 and a5b >= 0.18
    # H_DOT_neutral_in_no_BTC
    neutral_no_btc = (-0.05 <= a4n <= 0.15) and (-0.05 <= a5n <= 0.15)
    # DOT-as-anchor check
    dot_weights_with_btc = [r["dot_avg_weight"] for r in (n4_btc + n5_btc) if not np.isnan(r["dot_avg_weight"])]
    avg_dot_w_with_btc = float(np.mean(dot_weights_with_btc)) if dot_weights_with_btc else float("nan")
    dot_anchor = avg_dot_w_with_btc > 0.35

    print(f"Avg DOT weight in with-BTC universes: {avg_dot_w_with_btc:.1%}")
    print()
    print(f"H_DOT_compatible (≥+0.20 at N=4 AND ≥+0.18 at N=5): {'PASS' if compat else 'FAIL'}")
    print(f"H_DOT_neutral_in_no_BTC ([-0.05, +0.15]): {'PASS' if neutral_no_btc else 'FAIL'}")
    print(f"DOT-as-anchor risk (avg DOT weight > 35%): {'TRIGGERED' if dot_anchor else 'no'}")

    if compat and neutral_no_btc and not dot_anchor:
        print("\n  → H_DOT_compatible CONFIRMED — DOT is a regular alt, anchor edge holds.")
    elif dot_anchor:
        print("\n  → H_DOT_breaks (anchor shift) — DOT behaves as quasi-anchor.")
    elif not compat and a4b < 0.10:
        print("\n  → H_DOT_breaks (poison) — DOT erodes anchor edge.")
    else:
        print("\n  → H_DOT_mixed — partial signal, write nuance in cycle 91 entry.")


if __name__ == "__main__":
    main()

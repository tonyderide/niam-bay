"""Cycle 93 — Bootstrap CI on regime-stratified anchor edge (R2 closure).

Cycle 90 ran a regime stratification: each OOS chunk (42 candles 4h ≈ 7 days) was
labeled BULL/BEAR/RANGE based on BTC vs EMA200 and EMA200 slope. Per regime, we
computed ΔSharpe (mv - eq) for 10 universes (5 with BTC, 5 without).

Cycle 92 (synthesis `anchor-edge-empirical-map.md`) flagged risk R2: the RANGE
bucket has only 840 OOS observations (20 chunks per universe), which is the
slimmest cell. Conclusion "RANGE no-BTC is negative" might be noise.

Cycle 93 answers that with a moving-block bootstrap at the chunk level (each
chunk = 42 candles = 1 block). For each universe we resample chunks with
replacement and recompute Sharpe per regime. Repeating 1000 times yields IC 95%
on ΔSharpe per regime, then we aggregate across universes (with-BTC vs no-BTC)
keeping the paired bootstrap id so the with-vs-no comparison is itself
bootstrapped.

Pre-registered hypotheses (rule cycle 86):

    H_RANGE_no_BTC_excludes_zero : IC 95% on avg ΔSharpe for no-BTC universes in
                                    RANGE regime excludes 0.
                                    → cycle 90 conclusion is robust.

    H_RANGE_no_BTC_contains_zero : IC 95% on that quantity contains 0.
                                    → cycle 90 conclusion is consistent with noise.
                                    → must downgrade rule "no-BTC hurts in RANGE".

    H_BTC_effect_RANGE_excludes_zero : IC 95% on (with-BTC mean - no-BTC mean)
                                       in RANGE excludes 0.
                                       → BTC anchor edge in RANGE survives bootstrap.

    H_BTC_effect_RANGE_contains_zero : IC 95% on that effect contains 0.
                                       → BTC anchor edge in RANGE is statistically
                                         indistinguishable from chance at slim sample.

For completeness, the same is reported for BULL and BEAR (3192 and 2142 obs
respectively — much larger, so tighter ICs expected).
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
ANNUALIZE = 6 * 365
EMA_FAST = 50
EMA_SLOW = 200
N_BOOTSTRAP = 1000
RNG_SEED = 42


def realized_sharpe(returns_arr: np.ndarray, ann: int = ANNUALIZE) -> float:
    if len(returns_arr) == 0 or returns_arr.std() <= 0:
        return 0.0
    return float(returns_arr.mean() / returns_arr.std() * np.sqrt(ann))


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
    btc_rets = load_pair_returns("BTC", tf=TF)
    log_price = btc_rets["BTC"].cumsum()
    ema_slow = log_price.ewm(span=EMA_SLOW, adjust=False).mean()
    slope = ema_slow.diff(EMA_FAST)
    regime = pd.Series("RANGE", index=log_price.index, dtype=object)
    regime[(log_price > ema_slow) & (slope > 0)] = "BULL"
    regime[(log_price < ema_slow) & (slope < 0)] = "BEAR"
    return regime


def collect_paired_chunks(
    rets: pd.DataFrame,
    regime_labels: pd.Series,
    window: int = WINDOW,
    step: int = REBALANCE_STEP,
) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """Return list of (regime_label, eq_ret_arr, mv_ret_arr) per OOS chunk.

    Paired so that bootstrap preserves time alignment between eq and mv.
    """
    n = len(rets)
    chunks: list[tuple[str, np.ndarray, np.ndarray]] = []
    t = window
    while t + step <= n:
        train = rets.iloc[t - window : t]
        w_eq = eq_strategy(train)
        w_mv = mv_floor_10_strategy(train)
        oos = rets.iloc[t : t + step]
        port_eq = (oos * w_eq.reindex(oos.columns).values).sum(axis=1).values
        port_mv = (oos * w_mv.reindex(oos.columns).values).sum(axis=1).values
        oos_regimes = regime_labels.reindex(oos.index)
        dominant = "RANGE" if oos_regimes.isna().all() else oos_regimes.value_counts().idxmax()
        chunks.append((dominant, port_eq, port_mv))
        t += step
    return chunks


def bootstrap_regime_sharpes(
    chunks: list[tuple[str, np.ndarray, np.ndarray]],
    n_boot: int = N_BOOTSTRAP,
    seed: int = RNG_SEED,
) -> pd.DataFrame:
    """For each bootstrap iteration, resample chunks within each regime and
    compute (sh_eq, sh_mv, delta) per regime.
    """
    rng = np.random.default_rng(seed)
    by_regime: dict[str, list[int]] = {"BULL": [], "BEAR": [], "RANGE": []}
    for i, (reg, _, _) in enumerate(chunks):
        by_regime[reg].append(i)

    rows = []
    for _ in range(n_boot):
        boot_row: dict[str, float] = {}
        for reg, indices in by_regime.items():
            if len(indices) == 0:
                boot_row[f"sh_eq_{reg}"] = float("nan")
                boot_row[f"sh_mv_{reg}"] = float("nan")
                boot_row[f"delta_{reg}"] = float("nan")
                continue
            sampled = rng.choice(indices, size=len(indices), replace=True)
            eq_concat = np.concatenate([chunks[i][1] for i in sampled])
            mv_concat = np.concatenate([chunks[i][2] for i in sampled])
            sh_eq = realized_sharpe(eq_concat)
            sh_mv = realized_sharpe(mv_concat)
            boot_row[f"sh_eq_{reg}"] = sh_eq
            boot_row[f"sh_mv_{reg}"] = sh_mv
            boot_row[f"delta_{reg}"] = sh_mv - sh_eq
        rows.append(boot_row)
    return pd.DataFrame(rows)


UNIVERSES = [
    ("N6_LINK_ADA_SOL_ETH_BTC_AVAX", ["LINK", "ADA", "SOL", "ETH", "BTC", "AVAX"], 6, True),
    ("N6_LINK_ADA_SOL_ETH_BTC_APT", ["LINK", "ADA", "SOL", "ETH", "BTC", "APT"], 6, True),
    ("N6_LINK_ADA_SOL_ETH_AVAX_APT", ["LINK", "ADA", "SOL", "ETH", "AVAX", "APT"], 6, False),
    ("N7_LINK_ADA_SOL_ETH_BTC_AVAX_APT", ["LINK", "ADA", "SOL", "ETH", "BTC", "AVAX", "APT"], 7, True),
    ("N7_LINK_ADA_SOL_ETH_BTC_AVAX_OP", ["LINK", "ADA", "SOL", "ETH", "BTC", "AVAX", "OP"], 7, True),
    ("N7_LINK_ADA_SOL_ETH_AVAX_APT_OP", ["LINK", "ADA", "SOL", "ETH", "AVAX", "APT", "OP"], 7, False),
    ("N4_LINK_ADA_BTC_ETH", ["LINK", "ADA", "BTC", "ETH"], 4, True),
    ("N4_LINK_ADA_SOL_ETH", ["LINK", "ADA", "SOL", "ETH"], 4, False),
    ("N5_LINK_ADA_SOL_ETH_BTC", ["LINK", "ADA", "SOL", "ETH", "BTC"], 5, True),
    ("N5_LINK_ADA_SOL_ETH_AVAX", ["LINK", "ADA", "SOL", "ETH", "AVAX"], 5, False),
]


def main():
    print("=== Cycle 93 — Bootstrap CI per regime (R2 closure) ===\n")
    print(f"N_BOOTSTRAP={N_BOOTSTRAP}  block=chunk(42 candles 4h)\n")

    regime_labels = build_btc_regime()
    print(f"BTC regime label distribution: {regime_labels.value_counts().to_dict()}\n")

    per_univ_rows = []
    universe_boots: list[pd.DataFrame] = []
    for name, pairs, n, has_btc in UNIVERSES:
        try:
            rets = load_panel_returns(pairs, tf=TF)
        except FileNotFoundError as e:
            print(f"  SKIP {name}: {e}")
            continue

        chunks = collect_paired_chunks(rets, regime_labels)
        chunk_counts = {
            reg: sum(1 for c in chunks if c[0] == reg) for reg in ["BULL", "BEAR", "RANGE"]
        }

        boot_df = bootstrap_regime_sharpes(chunks)
        boot_df["universe"] = name
        boot_df["n"] = n
        boot_df["has_btc"] = has_btc
        boot_df["boot_id"] = boot_df.index
        universe_boots.append(boot_df)

        print(
            f"{name} (N={n}, has_BTC={has_btc}, chunks BULL={chunk_counts['BULL']}, "
            f"BEAR={chunk_counts['BEAR']}, RANGE={chunk_counts['RANGE']}):"
        )
        for reg in ["BULL", "BEAR", "RANGE"]:
            col = f"delta_{reg}"
            mean = boot_df[col].mean()
            lo, hi = boot_df[col].quantile([0.025, 0.975])
            verdict = "EXCLUDES 0" if (lo > 0 or hi < 0) else "CONTAINS 0"
            print(f"  {reg:5s}  Δmean={mean:+.3f}  IC95=[{lo:+.3f}, {hi:+.3f}]  {verdict}")
            per_univ_rows.append({
                "universe": name,
                "n": n,
                "has_btc": has_btc,
                "regime": reg,
                "delta_mean": mean,
                "ic_lo": lo,
                "ic_hi": hi,
                "excludes_zero": (lo > 0 or hi < 0),
                "chunk_count": chunk_counts[reg],
            })
        print()

    # save per-universe IC table
    per_univ_df = pd.DataFrame(per_univ_rows)
    per_univ_out = Path(__file__).parent / "bootstrap_regime_cycle93_per_universe.csv"
    per_univ_df.to_csv(per_univ_out, index=False)
    print(f"Wrote {per_univ_out}\n")

    aligned = pd.concat(universe_boots, ignore_index=True)

    print("=== Aggregate IC 95% — avg ΔSharpe per regime, with-BTC vs no-BTC ===\n")
    print(f"{'regime':<6}  {'group':<8}  {'mean':>8}  {'IC_lo':>8}  {'IC_hi':>8}  exclude 0?")
    print("-" * 56)

    summary_rows = []
    for reg in ["BULL", "BEAR", "RANGE"]:
        col = f"delta_{reg}"
        for has_btc_val in [True, False]:
            sub = aligned[aligned["has_btc"] == has_btc_val]
            per_boot = sub.groupby("boot_id")[col].mean()
            mean = float(per_boot.mean())
            lo, hi = per_boot.quantile([0.025, 0.975])
            crosses = lo <= 0 <= hi
            label = "with-BTC" if has_btc_val else "no-BTC"
            print(
                f"{reg:<6}  {label:<8}  {mean:+8.3f}  {lo:+8.3f}  {hi:+8.3f}  "
                f"{'NO' if not crosses else 'YES'}"
            )
            summary_rows.append({
                "regime": reg,
                "group": label,
                "mean": mean,
                "ic_lo": float(lo),
                "ic_hi": float(hi),
                "excludes_zero": not crosses,
            })

        # BTC effect (with - no), paired by boot_id
        sub_with = aligned[aligned["has_btc"]]
        sub_no = aligned[~aligned["has_btc"]]
        per_boot_with = sub_with.groupby("boot_id")[col].mean()
        per_boot_no = sub_no.groupby("boot_id")[col].mean()
        diff = per_boot_with - per_boot_no
        d_mean = float(diff.mean())
        d_lo, d_hi = diff.quantile([0.025, 0.975])
        d_crosses = d_lo <= 0 <= d_hi
        print(
            f"{reg:<6}  effect    {d_mean:+8.3f}  {d_lo:+8.3f}  {d_hi:+8.3f}  "
            f"{'NO' if not d_crosses else 'YES'}"
        )
        summary_rows.append({
            "regime": reg,
            "group": "effect",
            "mean": d_mean,
            "ic_lo": float(d_lo),
            "ic_hi": float(d_hi),
            "excludes_zero": not d_crosses,
        })
        print()

    summary_df = pd.DataFrame(summary_rows)
    out_summary = Path(__file__).parent / "bootstrap_regime_cycle93_summary.csv"
    summary_df.to_csv(out_summary, index=False)
    print(f"Wrote {out_summary}\n")

    # R2 verdict
    print("=== R2 verdicts (pre-registered) ===\n")
    rng_no = next(r for r in summary_rows if r["regime"] == "RANGE" and r["group"] == "no-BTC")
    rng_eff = next(r for r in summary_rows if r["regime"] == "RANGE" and r["group"] == "effect")

    print(f"H_RANGE_no_BTC: IC95 = [{rng_no['ic_lo']:+.3f}, {rng_no['ic_hi']:+.3f}]")
    if rng_no["excludes_zero"]:
        print("  → H_RANGE_no_BTC_excludes_zero  ✓ — cycle 90 verdict robust\n")
    else:
        print("  → H_RANGE_no_BTC_contains_zero  ✓ — cycle 90 verdict NOT robust\n")

    print(f"H_BTC_effect_RANGE: IC95 = [{rng_eff['ic_lo']:+.3f}, {rng_eff['ic_hi']:+.3f}]")
    if rng_eff["excludes_zero"]:
        print("  → BTC anchor edge in RANGE EXCLUDES 0 — survives bootstrap")
    else:
        print("  → BTC anchor edge in RANGE CONTAINS 0 — indistinguishable from noise")


if __name__ == "__main__":
    main()

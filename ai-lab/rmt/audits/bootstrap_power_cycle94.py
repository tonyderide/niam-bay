"""Cycle 94 — Extended power bootstrap (response to cycle 93 finding).

Cycle 93 found that with 5 universes per group (with-BTC vs no-BTC) and
20-76 chunks per regime, IC 95% on the BTC anchor effect contains 0 in ALL
regimes at the aggregate level. Per-universe, only 3 cells (all BULL with-BTC
at N=6-7 with APT/AVAX/OP) excluded 0. Cycle 93 distinguished "absence of
edge" from "absence of statistical power".

Cycle 94 tests the distinction directly: if we expand to ~8 universes per
group by adding new alts (AAVE, INJ, SUI, ATOM — data already cached but
unused in prior cycles), does the aggregate IC tighten enough to exclude 0
on at least one cell?

Pre-registered hypotheses (rule cycle 86):

    H_BULL_with_BTC_8univ_excludes_zero : IC 95% on avg ΔSharpe for with-BTC
                                          universes in BULL regime, N≥8
                                          universes, excludes 0.
                                          → cycle 93 "contains 0" was a power
                                            artifact ; underlying effect real.

    H_BULL_effect_8univ_excludes_zero : IC 95% on (with-BTC - no-BTC) avg
                                        ΔSharpe in BULL, N≥8, excludes 0.
                                        → BTC anchor effect survives stronger
                                          sampling.

    H_BEAR_effect_8univ_excludes_zero : same for BEAR regime.

    H_RANGE_effect_8univ_excludes_zero : same for RANGE — but expected to
                                          remain "contains 0" because RANGE
                                          chunks are ~20/universe, the slimmest
                                          cell.

If ALL aggregate IC remain "contains 0" even with 8 universes per group, the
cycle 93 verdict strengthens: the BTC anchor effect, at the magnitude of
+0.20 to +0.40 ΔSharpe per cycle 92, is genuinely indistinguishable from
sampling noise at the protocol level. The arc 85b-92 then yields a *direction*
without statistical confirmation.
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
    # 6 replays from cycle 93 (with-BTC)
    ("N4_LINK_ADA_BTC_ETH",                 ["LINK", "ADA", "BTC", "ETH"],                       4, True),
    ("N5_LINK_ADA_SOL_ETH_BTC",             ["LINK", "ADA", "SOL", "ETH", "BTC"],                5, True),
    ("N6_LINK_ADA_SOL_ETH_BTC_AVAX",        ["LINK", "ADA", "SOL", "ETH", "BTC", "AVAX"],        6, True),
    ("N6_LINK_ADA_SOL_ETH_BTC_APT",         ["LINK", "ADA", "SOL", "ETH", "BTC", "APT"],         6, True),
    ("N7_LINK_ADA_SOL_ETH_BTC_AVAX_APT",    ["LINK", "ADA", "SOL", "ETH", "BTC", "AVAX", "APT"], 7, True),
    ("N7_LINK_ADA_SOL_ETH_BTC_AVAX_OP",     ["LINK", "ADA", "SOL", "ETH", "BTC", "AVAX", "OP"],  7, True),
    # 4 NEW with-BTC using AAVE/INJ/SUI/ATOM
    ("N5_LINK_AAVE_SOL_ETH_BTC",            ["LINK", "AAVE", "SOL", "ETH", "BTC"],               5, True),
    ("N5_LINK_ATOM_SOL_ETH_BTC",            ["LINK", "ATOM", "SOL", "ETH", "BTC"],               5, True),
    ("N6_LINK_ADA_SOL_ETH_BTC_INJ",         ["LINK", "ADA", "SOL", "ETH", "BTC", "INJ"],         6, True),
    ("N7_LINK_ADA_SOL_ETH_BTC_SUI_AVAX",    ["LINK", "ADA", "SOL", "ETH", "BTC", "SUI", "AVAX"], 7, True),
    # 4 replays from cycle 93 (no-BTC)
    ("N4_LINK_ADA_SOL_ETH",                 ["LINK", "ADA", "SOL", "ETH"],                       4, False),
    ("N5_LINK_ADA_SOL_ETH_AVAX",            ["LINK", "ADA", "SOL", "ETH", "AVAX"],               5, False),
    ("N6_LINK_ADA_SOL_ETH_AVAX_APT",        ["LINK", "ADA", "SOL", "ETH", "AVAX", "APT"],        6, False),
    ("N7_LINK_ADA_SOL_ETH_AVAX_APT_OP",     ["LINK", "ADA", "SOL", "ETH", "AVAX", "APT", "OP"],  7, False),
    # 4 NEW no-BTC using AAVE/INJ/SUI/ATOM
    ("N5_LINK_AAVE_SOL_ETH_AVAX",           ["LINK", "AAVE", "SOL", "ETH", "AVAX"],              5, False),
    ("N5_LINK_ATOM_SOL_ETH_AVAX",           ["LINK", "ATOM", "SOL", "ETH", "AVAX"],              5, False),
    ("N6_LINK_ADA_SOL_ETH_AVAX_INJ",        ["LINK", "ADA", "SOL", "ETH", "AVAX", "INJ"],        6, False),
    ("N7_LINK_ADA_SOL_ETH_AVAX_SUI_OP",     ["LINK", "ADA", "SOL", "ETH", "AVAX", "SUI", "OP"],  7, False),
]


def main():
    print("=== Cycle 94 — Extended power bootstrap (8+ univ/group) ===\n")
    print(f"N_BOOTSTRAP={N_BOOTSTRAP}  block=chunk(42 candles 4h)")
    print(f"Universes: {sum(1 for u in UNIVERSES if u[3])} with-BTC + "
          f"{sum(1 for u in UNIVERSES if not u[3])} no-BTC\n")

    regime_labels = build_btc_regime()
    print(f"BTC regime label distribution: {regime_labels.value_counts().to_dict()}\n")

    per_univ_rows = []
    universe_boots: list[pd.DataFrame] = []
    skipped = []
    for name, pairs, n, has_btc in UNIVERSES:
        try:
            rets = load_panel_returns(pairs, tf=TF)
        except FileNotFoundError as e:
            print(f"  SKIP {name}: {e}")
            skipped.append((name, str(e)))
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
            verdict = "EXCLUDES 0" if (lo > 0 or hi < 0) else "contains 0"
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

    per_univ_df = pd.DataFrame(per_univ_rows)
    per_univ_out = Path(__file__).parent / "bootstrap_power_cycle94_per_universe.csv"
    per_univ_df.to_csv(per_univ_out, index=False)
    print(f"Wrote {per_univ_out}\n")

    aligned = pd.concat(universe_boots, ignore_index=True)
    n_with_btc = aligned[aligned["has_btc"]]["universe"].nunique()
    n_no_btc = aligned[~aligned["has_btc"]]["universe"].nunique()

    print(f"=== Aggregate IC 95% (n_with_BTC={n_with_btc}, n_no_BTC={n_no_btc}) ===\n")
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
    out_summary = Path(__file__).parent / "bootstrap_power_cycle94_summary.csv"
    summary_df.to_csv(out_summary, index=False)
    print(f"Wrote {out_summary}\n")

    # Compare cycle 93 vs cycle 94 IC widths (pre-registered widening test)
    cycle93_summary = Path(__file__).parent / "bootstrap_regime_cycle93_summary.csv"
    if cycle93_summary.exists():
        c93 = pd.read_csv(cycle93_summary)
        print("=== IC half-width: cycle 93 (5 univ) vs cycle 94 (extended) ===\n")
        print(f"{'regime':<6}  {'group':<8}  {'half_93':>8}  {'half_94':>8}  {'ratio':>6}")
        print("-" * 48)
        for _, r94 in summary_df.iterrows():
            match = c93[(c93["regime"] == r94["regime"]) & (c93["group"] == r94["group"])]
            if len(match) == 0:
                continue
            r93 = match.iloc[0]
            hw93 = (r93["ic_hi"] - r93["ic_lo"]) / 2
            hw94 = (r94["ic_hi"] - r94["ic_lo"]) / 2
            ratio = hw94 / hw93 if hw93 > 0 else float("nan")
            print(f"{r94['regime']:<6}  {r94['group']:<8}  {hw93:8.3f}  {hw94:8.3f}  {ratio:6.2f}")
        print()

    print("=== Cycle 94 verdicts (pre-registered) ===\n")
    for reg, group, label in [
        ("BULL", "with-BTC", "H_BULL_with_BTC_8univ"),
        ("BULL", "effect",   "H_BULL_effect_8univ"),
        ("BEAR", "effect",   "H_BEAR_effect_8univ"),
        ("RANGE", "effect",  "H_RANGE_effect_8univ"),
    ]:
        row = next(r for r in summary_rows if r["regime"] == reg and r["group"] == group)
        v = "EXCLUDES 0  ✓" if row["excludes_zero"] else "contains 0  ✓"
        print(f"{label:<28}  IC=[{row['ic_lo']:+.3f}, {row['ic_hi']:+.3f}]  → {v}")

    if skipped:
        print(f"\nSkipped {len(skipped)} universes (missing data):")
        for n, e in skipped:
            print(f"  {n}: {e}")


if __name__ == "__main__":
    main()

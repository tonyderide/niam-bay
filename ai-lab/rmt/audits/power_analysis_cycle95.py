"""Cycle 95 — Formal power analysis for chunk-block bootstrap protocol.

Cycle 94 extended the universe count from 5 to 8-10 per group and found that
IC half-widths shrank only 8-15% (not the theoretical sqrt(N_old/N_new) ≈
20-30% one would expect under iid sampling). All four pre-registered
hypotheses still contained 0. Cycle 94 ended with the question: "given the
observed variance structure, how many universes (or how much data) would
actually be required to detect ΔSharpe of magnitude 0.20-0.30 at α=5% with
power 0.80?"

This script answers that question rigorously by:

1. Decomposing observed variance into σ_between (across universes) and a
   σ_within proxy (mean half-width of per-universe ICs).
2. Computing required N_universes for power 0.80 across a grid of true
   effect sizes Δ ∈ {0.10, 0.20, 0.30, 0.40, 0.50}.
3. Computing achieved power at the current N for the same Δ grid.
4. Estimating sensitivity to data-length extension (σ_within ∝ 1/sqrt(T_per_universe)).

Output: power_analysis_cycle95.csv + console summary table per (régime, group).

Pre-registered conclusion (rule cycle 86):
    If the required N_universes for Δ=0.30 power=0.80 exceeds the realistic
    universe pool (≤ 18 with current Binance 4h cache), then the chunk-block
    bootstrap protocol is structurally underpowered to settle the BTC anchor
    edge question, regardless of how many additional universes we synthesize.
    Cycle 95 thereby provides a *permanent* lower-bound finding rather than
    an inconclusive "let's try yet more universes".
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ALPHA = 0.05
TARGET_POWER = 0.80
Z_ALPHA_2 = norm.ppf(1 - ALPHA / 2)
Z_POWER = norm.ppf(TARGET_POWER)
EFFECT_GRID = [0.10, 0.20, 0.30, 0.40, 0.50]

PER_UNIV_CSV = Path(__file__).parent / "bootstrap_power_cycle94_per_universe.csv"
SUMMARY_CSV = Path(__file__).parent / "bootstrap_power_cycle94_summary.csv"


def required_n(sigma_eff: float, delta: float) -> float:
    if delta <= 0 or sigma_eff <= 0:
        return float("inf")
    return float(((Z_ALPHA_2 + Z_POWER) * sigma_eff / delta) ** 2)


def power_at_n(sigma_eff: float, delta: float, n_current: int) -> float:
    if n_current <= 0 or sigma_eff <= 0:
        return 0.0
    se = sigma_eff / np.sqrt(n_current)
    z = delta / se - Z_ALPHA_2
    return float(norm.cdf(z))


def per_univ_half_width(df: pd.DataFrame) -> pd.Series:
    return (df["ic_hi"] - df["ic_lo"]) / 2.0


def main() -> None:
    print("=== Cycle 95 — Formal power analysis (closes arc 85b-94) ===\n")
    print(f"α (two-sided) = {ALPHA}   target power = {TARGET_POWER}")
    print(f"z_α/2 = {Z_ALPHA_2:.3f}   z_power = {Z_POWER:.3f}\n")

    per_univ = pd.read_csv(PER_UNIV_CSV)
    summary = pd.read_csv(SUMMARY_CSV)

    per_univ["half_width"] = per_univ_half_width(per_univ)

    rows = []
    print(
        f"{'régime':<6}  {'group':<8}  {'mean':>8}  "
        f"{'σ_btw':>6}  {'σ_wn':>6}  {'σ_eff':>6}  "
        f"{'N_now':>5}  {'N_Δ.20':>7}  {'N_Δ.30':>7}  {'N_Δ.50':>7}  "
        f"{'pow.20':>6}  {'pow.30':>6}  {'pow.50':>6}"
    )
    print("-" * 110)

    for regime in ["BULL", "BEAR", "RANGE"]:
        for group in ["with-BTC", "no-BTC", "effect"]:
            # Per-universe slice for σ_between estimation
            if group == "with-BTC":
                slice_df = per_univ[(per_univ["regime"] == regime) & per_univ["has_btc"]]
            elif group == "no-BTC":
                slice_df = per_univ[(per_univ["regime"] == regime) & ~per_univ["has_btc"]]
            else:
                wb = per_univ[(per_univ["regime"] == regime) & per_univ["has_btc"]]["delta_mean"].mean()
                nb = per_univ[(per_univ["regime"] == regime) & ~per_univ["has_btc"]]["delta_mean"].mean()
                wb_arr = per_univ[(per_univ["regime"] == regime) & per_univ["has_btc"]]["delta_mean"].values
                nb_arr = per_univ[(per_univ["regime"] == regime) & ~per_univ["has_btc"]]["delta_mean"].values
                # Effect = with-BTC mean - no-BTC mean. Variance approx pooled.
                n_w = len(wb_arr)
                n_n = len(nb_arr)
                sigma_w = wb_arr.std(ddof=1) if n_w > 1 else 0.0
                sigma_n = nb_arr.std(ddof=1) if n_n > 1 else 0.0
                sigma_between = float(np.sqrt(sigma_w**2 / n_w + sigma_n**2 / n_n) * np.sqrt(min(n_w, n_n)))
                sigma_within = float(per_univ[per_univ["regime"] == regime]["half_width"].mean() / Z_ALPHA_2)
                n_current = min(n_w, n_n)
                mean_eff = float(wb - nb)
                slice_df = None
            if group != "effect":
                arr = slice_df["delta_mean"].values
                n_current = len(arr)
                sigma_between = float(arr.std(ddof=1)) if n_current > 1 else 0.0
                # Within proxy: mean of per-univ half-widths → SE within → σ if scaled by sqrt(K_chunks effective)
                # We treat per-univ half/Z as already a SE; sigma_within ≈ half/Z × sqrt(N_current) for the bootstrap.
                # But since bootstrap is on chunks, the within term is largely absorbed into per-univ mean stability.
                # Use the simpler decomposition: σ_eff² ≈ σ_between² + σ_within²/N_current → solve so that
                # observed agg half-width = Z × σ_eff / sqrt(N_current)
                row_summary = summary[(summary["regime"] == regime) & (summary["group"] == group)]
                agg_half = float((row_summary["ic_hi"].iloc[0] - row_summary["ic_lo"].iloc[0]) / 2.0)
                sigma_eff_obs = agg_half * np.sqrt(n_current) / Z_ALPHA_2
                # decompose: sigma_eff_obs² = sigma_between² + sigma_within²/N_chunks_avg
                # treat any residual after sigma_between as σ_within proxy (collapsed)
                sigma_within = float(max(0.0, sigma_eff_obs**2 - sigma_between**2) ** 0.5)
                mean_eff = float(arr.mean())
            else:
                row_summary = summary[(summary["regime"] == regime) & (summary["group"] == "effect")]
                agg_half = float((row_summary["ic_hi"].iloc[0] - row_summary["ic_lo"].iloc[0]) / 2.0)
                mean_eff = float(row_summary["mean"].iloc[0])

            # Effective sigma for aggregate IC: half = Z × σ_eff / sqrt(N) → σ_eff = half × sqrt(N) / Z
            sigma_eff = agg_half * np.sqrt(n_current) / Z_ALPHA_2

            row = {
                "regime": regime,
                "group": group,
                "mean_observed": mean_eff,
                "n_current": n_current,
                "sigma_between": sigma_between,
                "sigma_within_proxy": sigma_within,
                "sigma_effective": sigma_eff,
                "agg_half_width": agg_half,
            }
            for delta in EFFECT_GRID:
                row[f"N_req_dlt{delta:.2f}"] = required_n(sigma_eff, delta)
                row[f"power_dlt{delta:.2f}"] = power_at_n(sigma_eff, delta, n_current)
            rows.append(row)

            print(
                f"{regime:<6}  {group:<8}  "
                f"{mean_eff:+8.3f}  "
                f"{sigma_between:6.3f}  {sigma_within:6.3f}  {sigma_eff:6.3f}  "
                f"{n_current:>5d}  "
                f"{row['N_req_dlt0.20']:>7.0f}  {row['N_req_dlt0.30']:>7.0f}  {row['N_req_dlt0.50']:>7.0f}  "
                f"{row['power_dlt0.20']*100:>5.1f}%  {row['power_dlt0.30']*100:>5.1f}%  {row['power_dlt0.50']*100:>5.1f}%"
            )
        print()

    out_df = pd.DataFrame(rows)
    out_path = Path(__file__).parent / "power_analysis_cycle95.csv"
    out_df.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")

    # === Bound analysis: realistic universe pool ===
    print("\n=== Universe-pool bound analysis ===\n")
    realistic_pool = 18  # current Binance 4h cache: 9 alts × 2 groups (with-BTC / no-BTC)
    print(f"Realistic universe pool (current Binance 4h cache): {realistic_pool}/group")
    print(f"Below this, the protocol can ever achieve power ≥ {TARGET_POWER}.\n")

    print(f"{'régime':<6}  {'group':<8}  {'effect':>7}  {'N_req':>7}  {'power@N':>9}  {'achievable?':<11}")
    print("-" * 60)
    for r in rows:
        for delta in [0.20, 0.30]:
            n_req = r[f"N_req_dlt{delta:.2f}"]
            pow_18 = power_at_n(r["sigma_effective"], delta, realistic_pool)
            achievable = "YES" if n_req <= realistic_pool else "NO"
            print(
                f"{r['regime']:<6}  {r['group']:<8}  {delta:>+7.2f}  "
                f"{n_req:>7.0f}  {pow_18*100:>8.1f}%  {achievable:<11}"
            )

    # === Data-length extension sensitivity ===
    print("\n=== Data-length extension sensitivity ===\n")
    print("σ_within scales as 1/sqrt(T). If T doubles, σ_within halves √2 →")
    print("σ_effective shrinks by f = sqrt((σ_btw² + σ_within²/2) / σ_effective²).")
    print(f"\n{'régime':<6}  {'group':<8}  {'σ_eff_now':>9}  {'σ_eff_2xT':>9}  {'σ_eff_4xT':>9}  "
          f"{'N_req(Δ=.30,2xT)':>17}  {'N_req(Δ=.30,4xT)':>17}")
    print("-" * 95)
    for r in rows:
        s_btw = r["sigma_between"]
        s_wn = r["sigma_within_proxy"]
        s_now = r["sigma_effective"]
        s_2x = np.sqrt(s_btw**2 + s_wn**2 / 2.0)
        s_4x = np.sqrt(s_btw**2 + s_wn**2 / 4.0)
        n_2x = required_n(s_2x, 0.30)
        n_4x = required_n(s_4x, 0.30)
        print(
            f"{r['regime']:<6}  {r['group']:<8}  {s_now:>9.3f}  {s_2x:>9.3f}  {s_4x:>9.3f}  "
            f"{n_2x:>17.0f}  {n_4x:>17.0f}"
        )

    # === Pre-registered verdict ===
    print("\n=== Pre-registered verdict (cycle 95) ===\n")
    print("Question: 'Does the chunk-block bootstrap protocol have power")
    print("≥ 0.80 to detect ΔSharpe = 0.30 at α=0.05 in any cell, given the")
    print(f"realistic universe pool of N ≤ {realistic_pool}?'\n")

    any_powered = any(
        r["N_req_dlt0.30"] <= realistic_pool
        for r in rows
    )
    print(f"Answer: {'YES — at least one cell is achievable.' if any_powered else 'NO — every cell requires N > realistic pool.'}\n")

    if any_powered:
        for r in rows:
            if r["N_req_dlt0.30"] <= realistic_pool:
                print(
                    f"  Achievable: {r['regime']}/{r['group']}  "
                    f"N_req={r['N_req_dlt0.30']:.0f} ≤ {realistic_pool}  "
                    f"power@18={power_at_n(r['sigma_effective'], 0.30, realistic_pool)*100:.1f}%"
                )
    else:
        print("  → arc 85b-94 result is BOUNDED: protocol underpowered for Δ=0.30")
        print("    irrespective of additional universe synthesis. Closing the arc")
        print("    requires changing the protocol (longer T, different stratification,")
        print("    or accepting the directional answer without significance).")


if __name__ == "__main__":
    main()

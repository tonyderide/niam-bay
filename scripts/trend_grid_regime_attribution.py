#!/usr/bin/env python3
"""Attribution BULL vs transition dans trend_grid — 2026-07-08 (piste cycle 222).

Décompose l'equity de trend_grid en 4 buckets pour isoler le coût des whipsaws :
  STABLE-BULL     : bull=True depuis ≥ WINDOW bars
  TRANSITION-BULL : bull=True mais bull=False il y a < WINDOW bars (juste entré)
  STABLE-BEAR     : bull=False depuis ≥ WINDOW bars
  TRANSITION-BEAR : bull=False mais bull=True il y a < WINDOW bars (juste sorti)

Complément à campaign_walkforward.py — ne modifie pas ce dernier.
Fonctionne avec cache OHLC si présent, sinon série synthétique pour smoke-test.
"""
import json, os, sys, numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from campaign_walkforward import ema, rsi, CACHE, MAKER

WINDOW = 24  # bars post-transition considérées comme instables (~24h en 1h bougies)


def attribution(a, spacing=0.008, rsi_thr=50):
    """Retourne dict {bucket: {n_bars, pnl_pct, share_of_time, share_of_pnl}}."""
    c = a[:, 4]
    e200 = ema(c, 200)
    R = rsi(c)
    bull = np.zeros(len(c), dtype=bool)
    for i in range(200, len(c)):
        bull[i] = c[i] > e200[i] and R[i] > rsi_thr

    # bars since last regime change
    since = np.zeros(len(c), dtype=int)
    for i in range(1, len(c)):
        since[i] = 0 if bull[i] != bull[i - 1] else since[i - 1] + 1

    buckets = {"STABLE-BULL": [], "TRANSITION-BULL": [],
               "STABLE-BEAR": [], "TRANSITION-BEAR": []}
    for i in range(200, len(c) - 1):
        ret = c[i + 1] / c[i] - 1
        # emule trend_grid bar-level : 0.5*ret + harvest si mouvement dépasse spacing
        if bull[i]:
            harvest = (spacing - 2 * MAKER) if abs(ret) >= spacing else 0.0
            bar_pnl = 0.5 * ret + 0.5 * harvest
            key = "STABLE-BULL" if since[i] >= WINDOW else "TRANSITION-BULL"
        else:
            bar_pnl = 0.0
            key = "STABLE-BEAR" if since[i] >= WINDOW else "TRANSITION-BEAR"
        buckets[key].append(bar_pnl)

    total_bars = sum(len(v) for v in buckets.values())
    total_pnl = sum(sum(v) for v in buckets.values())
    out = {}
    for k, v in buckets.items():
        pnl = sum(v)
        out[k] = {"n_bars": len(v),
                  "pnl_pct": round(pnl * 100, 3),
                  "share_of_time_pct": round(100 * len(v) / max(total_bars, 1), 2),
                  "share_of_pnl_pct": round(100 * pnl / total_pnl, 2) if abs(total_pnl) > 1e-9 else None}
    out["_total"] = {"n_bars": total_bars,
                     "pnl_pct": round(total_pnl * 100, 3)}
    return out


def synthetic(n=6000, seed=42):
    rng = np.random.default_rng(seed)
    ret = rng.normal(0.0002, 0.01, n)
    c = 100 * np.exp(np.cumsum(ret))
    o = np.roll(c, 1); o[0] = c[0]
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.003, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.003, n)))
    t = np.arange(n) * 3600.0
    v = np.abs(rng.normal(1000, 200, n))
    return np.column_stack([t, o, h, l, c, v])


def main():
    print(f"# Attribution BULL/transition — trend_grid (WINDOW={WINDOW}h)")
    results = {}
    for name in ("XBT", "ETH", "SOL", "DOT", "LINK", "ADA"):
        f = os.path.join(CACHE, f"{name}_1h.npy")
        if not os.path.exists(f):
            continue
        a = np.load(f)
        results[name] = attribution(a)

    if not results:
        print("(pas de cache OHLC — smoke-test synthétique)")
        results["SYNTH"] = attribution(synthetic())

    for name, r in results.items():
        print(f"\n## {name} (total {r['_total']['pnl_pct']}% sur {r['_total']['n_bars']} bars)")
        for k in ("STABLE-BULL", "TRANSITION-BULL", "STABLE-BEAR", "TRANSITION-BEAR"):
            v = r[k]
            share = f"{v['share_of_pnl_pct']}%" if v['share_of_pnl_pct'] is not None else "n/a"
            print(f"- {k:16s}  bars {v['n_bars']:4d}  ({v['share_of_time_pct']:5.2f}% time)  "
                  f"pnl {v['pnl_pct']:+7.3f}%  share {share}")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trend_grid_attribution.json")
    with open(out, "w") as fh:
        json.dump(results, fh, indent=1)
    print(f"\nÉcrit : {out}")


if __name__ == "__main__":
    main()

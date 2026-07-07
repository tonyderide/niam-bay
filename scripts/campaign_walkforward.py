#!/usr/bin/env python3
"""Campagne backtest sérieuse — 2026-07-07 (Fable, directive Tony).

Discipline :
- Walk-forward : optimise sur fenêtre train, mesure UNIQUEMENT sur test (jamais vu).
- Frais réels Kraken Futures : maker 0.02%, taker 0.05% + slippage 0.03% sur market.
- Verdict par stratégie : POSITIF seulement si PnL OOS > 0 sur la majorité des folds
  ET n_trades total >= 30. Sinon : PAS D'EDGE.
- Règle de dératage live = 30-50% du backtest (recherche 0501) rappelée au rapport.
"""
import json, os, sys, time, urllib.request
import numpy as np

OUT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(OUT, "ohlc_cache")
os.makedirs(CACHE, exist_ok=True)
PAIRS_SPOT = {"XBT": "XBTUSD", "ETH": "ETHUSD", "SOL": "SOLUSD",
              "ADA": "ADAUSD", "DOT": "DOTUSD", "LINK": "LINKUSD"}
MAKER, TAKER, SLIP = 0.0002, 0.0005, 0.0003
DAYS = 430

def fetch_1h(name, spot):
    """Kraken FUTURES charts API publique — pagine vraiment avec from/to (5000 max/call)."""
    f = os.path.join(CACHE, f"{name}_1h.npy")
    if os.path.exists(f):
        a = np.load(f)
        if len(a) > 4000:
            return a
    pf = f"PF_{name}USD"
    rows, start = [], int(time.time()) - DAYS * 86400
    end = int(time.time())
    cur = start
    while cur < end:
        chunk_end = min(cur + 1990 * 3600, end)
        url = f"https://futures.kraken.com/api/charts/v1/trade/{pf}/1h?from={cur}&to={chunk_end}"
        try:
            d = json.load(urllib.request.urlopen(url, timeout=25))
        except Exception:
            time.sleep(2); continue
        for r in d.get("candles", []):
            rows.append([r["time"] / 1000, float(r["open"]), float(r["high"]),
                         float(r["low"]), float(r["close"]), float(r["volume"])])
        cur = chunk_end
        time.sleep(0.8)
    a = np.array(sorted({r[0]: r for r in rows}.values(), key=lambda r: r[0]))
    np.save(f, a)
    return a

def ema(x, n):
    a = np.empty_like(x); k = 2 / (n + 1); a[0] = x[0]
    for i in range(1, len(x)):
        a[i] = x[i] * k + a[i - 1] * (1 - k)
    return a

def atr(o, h, l, c, n=14):
    tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    out = np.empty(len(c)); out[0] = tr[0]
    for i in range(1, len(c)):
        out[i] = (out[i - 1] * (n - 1) + tr[min(i - 1, len(tr) - 1)]) / n
    return out

def rsi(c, n=14):
    d = np.diff(c, prepend=c[0]); up = np.where(d > 0, d, 0.0); dn = np.where(d < 0, -d, 0.0)
    ru, rd = ema(up, n), ema(dn, n)
    return 100 - 100 / (1 + ru / np.maximum(rd, 1e-12))

def metrics(equity, n_trades):
    r = np.diff(equity) / equity[:-1]
    tot = equity[-1] / equity[0] - 1
    sharpe = (r.mean() / (r.std() + 1e-12)) * np.sqrt(24 * 365) if len(r) > 2 else 0
    peak = np.maximum.accumulate(equity); dd = ((equity - peak) / peak).min()
    return {"pnl_pct": round(tot * 100, 2), "sharpe": round(float(sharpe), 2),
            "maxdd_pct": round(float(dd) * 100, 2), "n": int(n_trades)}

# ---------- Stratégies 1h (entrées taker+slip, position unique, equity marked) ----------

def strat_donchian(a, p):
    """Breakout Donchian n haut/bas, sortie trailing ATR*k. Long et short."""
    o, h, l, c = a[:, 1], a[:, 2], a[:, 3], a[:, 4]
    n, k = p["n"], p["k"]; A = atr(o, h, l, c)
    eq, pos, entry, stop, ntr = [1.0], 0, 0.0, 0.0, 0
    for i in range(n + 1, len(c) - 1):
        px = c[i]
        if pos == 0:
            if px >= h[i - n:i].max():
                pos, entry = 1, px * (1 + TAKER + SLIP); stop = px - k * A[i]; ntr += 1
            elif px <= l[i - n:i].min():
                pos, entry = -1, px * (1 - TAKER - SLIP); stop = px + k * A[i]; ntr += 1
        elif pos == 1:
            stop = max(stop, px - k * A[i])
            if px <= stop:
                eq.append(eq[-1] * (1 + (px * (1 - TAKER - SLIP) / entry - 1))); pos = 0; continue
        else:
            stop = min(stop, px + k * A[i])
            if px >= stop:
                eq.append(eq[-1] * (1 + (entry / (px * (1 + TAKER + SLIP)) - 1))); pos = 0; continue
        eq.append(eq[-1] * (1 + pos * (c[i + 1] / c[i] - 1)) if pos else eq[-1])
    return np.array(eq), ntr

def strat_regime_pullback(a, p):
    """Règle 3-régimes Tony, moteur DURCI :
    - signal sur clôture i → entrée à l'OPEN de i+1 (pas de look-ahead)
    - TP/SL exécutés sur high/low intrabar, SL PRIORITAIRE (pire cas)
    - sortie au prix exact du TP/SL (pas au close), frais taker+slip."""
    o, h, l, c = a[:, 1], a[:, 2], a[:, 3], a[:, 4]
    e200, e20 = ema(c, 200), ema(c, 20); R = rsi(c)
    tp, sl = p["tp"], p["sl"]
    eq, pos, entry, ntr = [1.0], 0, 0.0, 0
    pend = 0
    for i in range(200, len(c) - 1):
        if pend and pos == 0:
            px = o[i]
            entry = px * (1 + TAKER + SLIP) if pend == 1 else px * (1 - TAKER - SLIP)
            pos, pend, ntr = pend, 0, ntr + 1
        if pos == 1:
            slp, tpp = entry * (1 - sl), entry * (1 + tp)
            if l[i] <= slp:
                eq.append(eq[-1] * (slp * (1 - TAKER - SLIP) / entry)); pos = 0; continue
            if h[i] >= tpp:
                eq.append(eq[-1] * (tpp * (1 - MAKER) / entry)); pos = 0; continue
        elif pos == -1:
            slp, tpp = entry * (1 + sl), entry * (1 - tp)
            if h[i] >= slp:
                eq.append(eq[-1] * (entry / (slp * (1 + TAKER + SLIP)))); pos = 0; continue
            if l[i] <= tpp:
                eq.append(eq[-1] * (entry / (tpp * (1 + MAKER)))); pos = 0; continue
        if pos == 0 and pend == 0:
            if c[i] > e200[i] and c[i] < e20[i] and R[i] < 45:
                pend = 1
            elif c[i] < e200[i] and c[i] > e20[i] and R[i] > 55:
                pend = -1
        eq.append(eq[-1] * (1 + pos * (c[i + 1] / c[i] - 1)) if pos else eq[-1])
    return np.array(eq), ntr

def strat_trend_grid(a, p):
    """Proxy trend-aware deploy (TrendStateManager) : BULL (c>e200 & RSI>seuil) → grid long
    simulée = exposition 1 avec récolte spacing (approx maker), sinon cash. BEAR → cash."""
    c = a[:, 4]; e200 = ema(c, 200); R = rsi(c)
    sp = p["spacing"]
    eq, ntr, inpos = [1.0], 0, False
    for i in range(200, len(c) - 1):
        bull = c[i] > e200[i] and R[i] > p["rsi"]
        if bull and not inpos: inpos = True; ntr += 1
        if not bull and inpos: inpos = False
        if inpos:
            ret = c[i + 1] / c[i] - 1
            # grid : capte le mouvement + récolte ~half-spread par bar si |ret| >= spacing
            harvest = (sp - 2 * MAKER) if abs(ret) >= sp else 0.0
            eq.append(eq[-1] * (1 + 0.5 * ret + harvest * 0.5))
        else:
            eq.append(eq[-1])
    return np.array(eq), ntr

STRATS = {
    "donchian": (strat_donchian, [{"n": n, "k": k} for n in (20, 55, 96) for k in (2.0, 3.0)]),
    "regime_pullback": (strat_regime_pullback, [{"tp": tp, "sl": sl} for tp in (.02, .04) for sl in (.01, .02)]),
    "trend_grid": (strat_trend_grid, [{"spacing": s, "rsi": r} for s in (.008, .012) for r in (50, 55)]),
}

def walk_forward(a, fn, grid_params, train=2160, test=1080):
    """train 90j / test 45j glissants (bougies 1h).
    Capture aussi IS (train) du best param pour mesurer overfit OOS/IS."""
    folds = []
    i = 0
    while i + train + test <= len(a):
        tr, te = a[i:i + train], a[i + train:i + train + test]
        best, best_m, best_is = None, None, None
        for p in grid_params:
            eq, n = fn(tr, p)
            m = metrics(eq, n)
            score = m["pnl_pct"] if n >= 5 else -999
            if best is None or score > best_m:
                best, best_m, best_is = p, score, m
        eq, n = fn(te, best)
        m = metrics(eq, n); m["params"] = best
        m["is_pnl_pct"] = best_is["pnl_pct"]
        m["is_n"] = best_is["n"]
        folds.append(m)
        i += test
    return folds

def main():
    report = {"generated": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
              "fees": {"maker": MAKER, "taker": TAKER, "slip": SLIP}, "results": {}}
    for name, spot in PAIRS_SPOT.items():
        try:
            a = fetch_1h(name, spot)
        except Exception as e:
            report["results"][name] = {"error": str(e)}; continue
        if len(a) < 4000:
            report["results"][name] = {"error": f"data courte {len(a)}"}; continue
        pr = {}
        for sname, (fn, params) in STRATS.items():
            folds = walk_forward(a, fn, params)
            oos_pnl = [f["pnl_pct"] for f in folds]
            is_pnl = [f["is_pnl_pct"] for f in folds]
            n_tot = sum(f["n"] for f in folds)
            verdict = "POSITIF-OOS" if (len(oos_pnl) >= 2 and n_tot >= 30
                        and sum(1 for x in oos_pnl if x > 0) > len(oos_pnl) / 2
                        and sum(oos_pnl) > 0) else "PAS D'EDGE"
            is_sum, oos_sum = sum(is_pnl), sum(oos_pnl)
            overfit = round(oos_sum / is_sum, 2) if abs(is_sum) > 0.5 else None
            pr[sname] = {"folds_oos_pnl_pct": oos_pnl, "folds_is_pnl_pct": is_pnl,
                         "total_oos_pnl_pct": round(oos_sum, 2), "total_is_pnl_pct": round(is_sum, 2),
                         "overfit_ratio_oos_over_is": overfit,
                         "n_trades": n_tot, "verdict": verdict, "folds": folds}
        report["results"][name] = pr
        print(f"[{name}] fait — bougies {len(a)}", flush=True)
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump(report, f, indent=1)
    # résumé lisible
    lines = ["# Campagne walk-forward OOS — " + report["generated"],
             "Frais maker 0.02% / taker 0.05% + slippage 0.03%. Verdict = OOS only, n>=30.",
             "Rappel : live = 30-50% du backtest.", ""]
    for pair, pr in report["results"].items():
        if "error" in pr:
            lines.append(f"## {pair}: ERREUR {pr['error']}"); continue
        lines.append(f"## {pair}")
        for s, m in pr.items():
            of = m.get('overfit_ratio_oos_over_is')
            of_s = f" | overfit {of}" if of is not None else " | overfit n/a"
            lines.append(f"- {s}: {m['verdict']} | OOS {m['total_oos_pnl_pct']}% vs IS {m['total_is_pnl_pct']}%"
                         f"{of_s} | folds OOS {m['folds_oos_pnl_pct']} | trades {m['n_trades']}")
    open(os.path.join(OUT, "results.md"), "w").write("\n".join(lines))
    print("TERMINE — results.md écrit", flush=True)

if __name__ == "__main__":
    main()

# Applique PREREG-09.
import itertools, json, math, banc
M21 = ["BTC","ETH","SOL","XRP","DOGE","ADA","LINK","AVAX","DOT","LTC","BCH","UNI","ATOM","NEAR","FIL","AAVE","APT","OP","TRX","XLM","ETC"]
SIG = {
 "cassure20": ("close > shift(highest(high, 20), 1)", "close < shift(lowest(low, 20), 1)"),
 "cassure55": ("close > shift(highest(high, 55), 1)", "close < shift(lowest(low, 55), 1)"),
 "ema20_50": ("cross_up(ema(20), ema(50))", "cross_down(ema(20), ema(50))"),
 "supertrend": ("cross_up(supertrend(10, 3), 0)", "cross_down(supertrend(10, 3), 0)"),
 "macd": ("cross_up(macd(), macd_signal())", "cross_down(macd(), macd_signal())"),
 "rsi2": ("rsi(2) < 10", "rsi(2) > 90"),
 "rsi14_retour": ("cross_up(rsi(14), 30)", "cross_down(rsi(14), 70)"),
 "bb_retour": ("close < bb_lower(20, 2)", "close > bb_upper(20, 2)"),
 "bb_momentum": ("close > bb_upper(20, 2)", "close < bb_lower(20, 2)"),
 "fade_3bougies": ("(close < open) & (shift(close) < shift(open)) & (shift(close, 2) < shift(open, 2))", "(close > open) & (shift(close) > shift(open)) & (shift(close, 2) > shift(open, 2))"),
}
FIL = {"aucun": ("", ""), "sens_sma200": ("close > sma(200)", "close < sma(200)"), "adx_fort": ("adx(14) > 25", "adx(14) > 25"),
       "adx_faible": ("adx(14) < 20", "adx(14) < 20"), "vol_monte": ("atr(14) > atr(60)", "atr(14) > atr(60)"),
       "vol_baisse": ("atr(14) < atr(60)", "atr(14) < atr(60)"), "long_seul": ("", None)}
SOR = {"H3": {"max_bougies": 3}, "H5": {"max_bougies": 5}, "H10": {"max_bougies": 10}, "H20": {"max_bougies": 20}, "oppose": {"inverse": True, "max_bougies": 500}, "sl5_tp10": {"sl": 0.05, "tp": 0.10}}
def comb(sig, fil):
    if fil is None: return None
    return f"({sig}) & ({fil})" if fil else f"({sig})"
specs = []
for tf in ("1d", "4h"):
    for (sn, (sl_, ss)), (fn, (fl, fs)), (on, so) in itertools.product(SIG.items(), FIL.items(), SOR.items()):
        specs.append({"nom": f"{tf}|{sn}|{fn}|{on}", "tf": tf, "marches": M21 if tf == "1d" else ["BTC","ETH","SOL"],
                      "long": comb(sl_, fl), "short": comb(ss, fs), "sortie": so})
# cache des expressions par marché
CACHE = {}
def serie(m, tf, expr):
    k = (m, tf, expr)
    if k not in CACHE:
        T, C = banc.candles(banc.SYM[m], tf)
        if (m, tf) not in CACHE: CACHE[(m, tf)] = banc.namespace(T, C)
        CACHE[k] = eval(expr, {"__builtins__": {}}, CACHE[(m, tf)])
    return CACHE[k]
def mesurer(spec, a, b):
    out = []
    for m in spec["marches"]:
        T, C = banc.candles(banc.SYM[m], spec["tf"])
        lo = next(i for i, t in enumerate(T) if t >= a); hi = max(i for i, t in enumerate(T) if t < b) + 1
        L = serie(m, spec["tf"], spec["long"]); Sh = serie(m, spec["tf"], spec["short"]) if spec["short"] else [False] * len(C)
        so = spec["sortie"]; C2 = C[:hi]; tot = 0; n = 0; i = max(lo, 250)
        while i < hi - 1:
            s = 1 if L[i] else -1 if Sh[i] else 0
            if not s: i += 1; continue
            opp = (Sh if s > 0 else L) if so.get("inverse") else None
            r, j = banc.sortir(C2, i + 1, s, so, opp); tot += r; n += 1; i = j + 1
        out.append((tot, n))
    return sum(t for t, _ in out), sum(n for _, n in out), sum(t > 0 for t, _ in out) / len(out)
A, B, C26, E = banc.ts("2024-01-01"), banc.ts("2026-01-01"), banc.ts("2026-01-01"), banc.ts("2026-10-17")
rows = []
for k, s in enumerate(specs):
    s1, n1, p1 = mesurer(s, A, B); s2, n2, p2 = mesurer(s, C26, E); rows.append((s, s1, n1, p1, s2, n2, p2))
    if k % 60 == 0: print(f"  {k}/{len(specs)}", flush=True)
json.dump([(r[0]["nom"],) + r[1:] for r in rows], open("t09-grille.json", "w"))
elig = [r for r in rows if r[2] >= 100 and r[3] >= 0.6]; elig.sort(key=lambda r: -r[1])
print(f"\n{len(rows)} stratégies, {len(elig)} éligibles (≥100 trades, ≥60 % marchés >0 en 2024-25)")
print("TOP 10 de la sélection 2024-2025 :")
for r in elig[:10]: print(f"   {r[0]['nom']:40} 24-25 {r[1]*100:+8.1f} % ({r[2]} tr) | 2026 {r[4]*100:+8.1f} % ({r[5]} tr)")
def rang(v): o = sorted(range(len(v)), key=lambda i: v[i]); R = [0]*len(v); [R.__setitem__(i, k) for k, i in enumerate(o)]; return R
x = rang([r[1] for r in rows]); y = rang([r[4] for r in rows]); n = len(rows)
rho = 1 - 6 * sum((a - b) ** 2 for a, b in zip(x, y)) / (n * (n * n - 1))
srt = sorted(rows, key=lambda r: -r[1]); pos = lambda L: sum(r[4] > 0 for r in L) / len(L)
print(f"\nCONTRÔLE GLOBAL : Spearman(2024-25, 2026) = {rho:+.3f} | part positive en 2026 : top20 {pos(srt[:20]):.0%} · toutes {pos(rows):.0%} · bottom20 {pos(srt[-20:]):.0%}")
best = elig[0][0]; json.dump(best, open("specs/09-meilleure-combinaison.json", "w"), ensure_ascii=False)
banc.PERIODES = (("2026 (JUGEMENT)", C26, E), ("jan-juin 2026", C26, banc.ts("2026-07-01")), ("juil-oct 2026, après cutoff", banc.ts("2026-07-01"), E))
o = banc.banc(best).split("\n")
print(f"\nJUGEMENT de {best['nom']} :"); [print("   ", l.split(" : ")[0], "→", l.split("|| ")[-1]) for l in o[1:-1]]

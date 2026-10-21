"""PREREG-14 : scalp honnête. Voir PREREG-14-scalp-honnete.md."""
import itertools, math, random, statistics
import banc

FEE = 0.0005; MAXB = 24
A, B, C0, C1 = banc.ts("2024-01-01"), banc.ts("2026-01-01"), banc.ts("2026-01-01"), banc.ts("2026-10-17")


def ema(x, k):
    a = 2 / (k + 1); o = [x[0]]
    for v in x[1:]: o.append(o[-1] + a * (v - o[-1]))
    return o


def rsi2(cl):
    o = [50.0] * len(cl); g = l = 0.0; a = 0.5
    for i in range(1, len(cl)):
        d = cl[i] - cl[i - 1]; g = (1 - a) * g + a * max(d, 0); l = (1 - a) * l + a * max(-d, 0)
        o[i] = 100 if l == 0 else 100 - 100 / (1 + g / l)
    return o


def signaux(C):
    cl = [c[3] for c in C]; n = len(cl); s = {k: [0] * n for k in "abcd"}
    r = rsi2(cl); e9, e21 = ema(cl, 9), ema(cl, 21)
    for i in range(25, n):
        s["a"][i] = 1 if r[i] < 10 else -1 if r[i] > 90 else 0
        w = cl[i - 19:i + 1]; m = sum(w) / 20; sd = statistics.pstdev(w)
        s["b"][i] = 1 if cl[i] < m - 2 * sd else -1 if cl[i] > m + 2 * sd else 0
        s["c"][i] = 1 if e9[i] > e21[i] and e9[i - 1] <= e21[i - 1] else -1 if e9[i] < e21[i] and e9[i - 1] >= e21[i - 1] else 0
        hh = max(c[1] for c in C[i - 12:i]); ll = min(c[2] for c in C[i - 12:i])
        s["d"][i] = 1 if cl[i] > hh else -1 if cl[i] < ll else 0
    return s


def trade(C, i, sens, tp, sl):
    """Entrée à l'ouverture de i ; renvoie (rendement net, indice de sortie)."""
    e = C[i][0]; obj = e * (1 + tp * sens); stp = e * (1 - sl * sens)
    for j in range(i, min(i + MAXB, len(C))):
        o, h, l = C[j][0], C[j][1], C[j][2]
        if j > i and ((o <= stp) if sens > 0 else (o >= stp)): return (o / e - 1) * sens - 2 * FEE, j
        if (l <= stp) if sens > 0 else (h >= stp): return -sl - 2 * FEE, j
        if (h >= obj) if sens > 0 else (l <= obj): return tp - 2 * FEE, j
    j = min(i + MAXB, len(C)) - 1
    return (C[j][3] / e - 1) * sens - 2 * FEE, j


def strat(C, T, sig, tp, sl, a, b):
    lo = next(k for k, t in enumerate(T) if t >= a); hi = next((k for k, t in enumerate(T) if t >= b), len(T)) - 1
    i = lo; R = []; nl = ns = 0
    while i < hi - 1:
        if sig[i]:
            r, j = trade(C, i + 1, sig[i], tp, sl); R.append(r); nl += sig[i] > 0; ns += sig[i] < 0; i = j + 1
        else: i += 1
    return R, nl, ns, lo, hi


rows = []; cache = {}
for tf, m in itertools.product(("15m", "1h"), ("BTC", "ETH", "SOL")):
    T, C = banc.candles(banc.SYM[m], tf); S = signaux(C); cache[(tf, m)] = (T, C, S)
    for k, (tp, sl) in itertools.product("abcd", ((0.005, 0.005), (0.01, 0.01), (0.015, 0.01), (0.02, 0.01), (0.03, 0.015))):
        R1 = strat(C, T, S[k], tp, sl, A, B)[0]; R2, nl, ns, lo, hi = strat(C, T, S[k], tp, sl, C0, C1)
        rows.append(((tf, m, k, tp, sl), sum(R1), len(R1), sum(R2), len(R2), nl, ns, lo, hi))
    print(f"  {tf} {m} fait", flush=True)

el = [r for r in rows if r[2] >= 30]
best = max(el, key=lambda r: r[1]); (tf, m, k, tp, sl), s1, n1, s2, n2, nl, ns, lo, hi = best
T, C, S = cache[(tf, m)]; rnd = random.Random(14); J = []
for _ in range(500):
    tot = 0.0
    for sens, cnt in ((1, nl), (-1, ns)):
        for _ in range(cnt): tot += trade(C, rnd.randrange(lo + 1, hi - MAXB), sens, tp, sl)[0]
    J.append(tot)
J.sort(); rang = sum(x < s2 for x in J) / len(J)


def rk(x):
    o = sorted(range(len(x)), key=lambda i: x[i]); r = [0] * len(x)
    for q, i in enumerate(o): r[i] = q
    return r


a, b = rk([r[1] for r in rows]), rk([r[3] for r in rows]); n = len(rows)
sp = 1 - 6 * sum((x - y) ** 2 for x, y in zip(a, b)) / (n * (n * n - 1))
print(f"\n{len(rows)} stratégies ; positives 2024-25 : {sum(r[1] > 0 for r in rows)} ; positives 2026 : {sum(r[3] > 0 for r in rows)} ; Spearman 2024-25 -> 2026 : {sp:+.2f}")
print(f"SÉLECTION (meilleure de 2024-25) : {tf} {m} signal {k} TP {tp:.1%} SL {sl:.1%} | 2024-25 {100*s1:+.1f} % ({n1} trades)")
print(f"JUGEMENT 2026 : {100*s2:+.1f} % ({n2} trades) | jumeaux méd {100*J[250]:+.1f} % max {100*J[-1]:+.1f} % | rang {rang:.1%}")
print("VERDICT :", "GAGNE" if s2 > 0 and n2 >= 30 and s2 > J[-1] else "ÉCHEC")

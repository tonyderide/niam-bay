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
    FEE = globals()['FEE']
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



def sig_ema(C, f, s):
    cl = [c[3] for c in C]; ef, es = ema(cl, f), ema(cl, s); o = [0] * len(cl)
    for i in range(1, len(cl)):
        o[i] = 1 if ef[i] > es[i] and ef[i-1] <= es[i-1] else -1 if ef[i] < es[i] and ef[i-1] >= es[i-1] else 0
    return o

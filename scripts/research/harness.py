#!/usr/bin/env python3
"""Banc d'essai NB (mandat capital, 2026-10-15).

Règles d'honnêteté :
- signal calculé sur la bougie fermée i, entrée à l'open de i+1 (pas de look-ahead) ;
- si SL et TP sont touchés dans la même bougie, on compte le SL ;
- frais 0,05 % taker + 0,02 % de slippage par côté ;
- résultats en R (multiples du risque initial) pour comparer les stratégies entre elles ;
- split IS = 16 premiers mois / OOS = 8 derniers ; on ne juge QUE sur l'OOS, et sur le panier entier.
Usage : harness.py DATADIR
"""
import csv, math, sys, glob, os

COST = 0.0007  # par côté, en fraction du prix


def load(path):
    rows = list(csv.DictReader(open(path)))
    return [(int(r["t"]), float(r["o"]), float(r["h"]), float(r["l"]), float(r["c"])) for r in rows]


def ema(v, n):
    k, e, out = 2 / (n + 1), None, []
    for x in v:
        e = x if e is None else x * k + e * (1 - k)
        out.append(e)
    return out


def rsi(c, n=14):
    out, ag, al = [None] * len(c), 0.0, 0.0
    for i in range(1, len(c)):
        d = c[i] - c[i - 1]; g, l = max(d, 0), max(-d, 0)
        if i <= n: ag += g / n; al += l / n
        else: ag = (ag * (n - 1) + g) / n; al = (al * (n - 1) + l) / n
        if i >= n: out[i] = 100 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def atr(b, n=14):
    tr = [b[0][2] - b[0][3]] + [max(b[i][2] - b[i][3], abs(b[i][2] - b[i - 1][4]), abs(b[i][3] - b[i - 1][4])) for i in range(1, len(b))]
    return ema(tr, n)


class Ctx:
    def __init__(self, b, btc):
        self.b = b; c = [x[4] for x in b]; self.c = c
        self.e50, self.e200, self.r, self.a = ema(c, 50), ema(c, 200), rsi(c), atr(b)
        bc = [x[4] for x in btc]; self.b50, self.b200 = ema(bc, 50), ema(bc, 200)
        self.hh = [max(x[2] for x in b[max(0, i - 47):i + 1]) for i in range(len(b))]
        self.ll = [min(x[3] for x in b[max(0, i - 47):i + 1]) for i in range(len(b))]


# Chaque stratégie : f(ctx, i) -> None ou (side, stop_dist, tp_dist), side = +1 long / -1 short, distances en prix.
def s_pullback(x, i):  # coup n°1 généralisé dans les 2 sens
    if x.b50[i] < x.b200[i] and x.e50[i] < x.e200[i] and x.r[i] > 45 and x.b[i][2] >= x.e50[i] > x.c[i - 1]:
        return (-1, 0.023 * x.c[i], 0.045 * x.c[i])
    if x.b50[i] > x.b200[i] and x.e50[i] > x.e200[i] and x.r[i] < 55 and x.b[i][3] <= x.e50[i] < x.c[i - 1]:
        return (1, 0.023 * x.c[i], 0.045 * x.c[i])


def s_donchian(x, i):  # cassure 48h dans le sens du régime BTC, stop 2 ATR, TP 4 ATR
    if x.c[i] > x.hh[i - 1] and x.b50[i] > x.b200[i]:
        return (1, 2 * x.a[i], 4 * x.a[i])
    if x.c[i] < x.ll[i - 1] and x.b50[i] < x.b200[i]:
        return (-1, 2 * x.a[i], 4 * x.a[i])


def s_meanrev(x, i):  # excès RSI à contre-sens, SEULEMENT dans le sens de la tendance de fond
    if x.r[i] is None: return
    if x.r[i] < 22 and x.c[i] > x.e200[i]:
        return (1, 2 * x.a[i], 2 * x.a[i])
    if x.r[i] > 78 and x.c[i] < x.e200[i]:
        return (-1, 2 * x.a[i], 2 * x.a[i])


def s_squeeze(x, i):  # compression de volatilité puis cassure
    if i < 300: return
    win = x.a[i - 240:i]; rank = sum(1 for v in win if v < x.a[i]) / len(win)
    if rank < 0.15 and x.c[i] > x.hh[i - 1]: return (1, 1.5 * x.a[i], 4.5 * x.a[i])
    if rank < 0.15 and x.c[i] < x.ll[i - 1]: return (-1, 1.5 * x.a[i], 4.5 * x.a[i])


def s_random(x, i):  # contrôle : entrées au hasard (déterministe) même géométrie que pullback
    if (i * 2654435761) % 997 < 4:
        return ((1 if (i // 7) % 2 else -1), 0.023 * x.c[i], 0.045 * x.c[i])


STRATS = {"pullback": s_pullback, "donchian": s_donchian, "meanrev": s_meanrev, "squeeze": s_squeeze, "random": s_random}


def run(x, f, lo, hi):
    out, i = [], max(lo, 201)
    while i < hi - 1:
        sig = f(x, i)
        if not sig: i += 1; continue
        side, sd, td = sig; j = i + 1; e = x.b[j][1]
        sl, tp = e - side * sd, e + side * td; res = None
        while j < hi:
            _, o, h, l, c = x.b[j]
            if (side == 1 and l <= sl) or (side == -1 and h >= sl): res = -sd; break
            if (side == 1 and h >= tp) or (side == -1 and l <= tp): res = td; break
            j += 1
        if res is None: res = side * (x.b[hi - 1][4] - e)
        out.append((res - 2 * COST * e) / sd)  # en R, frais compris
        i = j + 1
    return out


def stats(rs):
    n = len(rs)
    if n < 2: return n, 0, 0, 0
    m = sum(rs) / n; sd = math.sqrt(sum((r - m) ** 2 for r in rs) / (n - 1))
    return n, m, sum(1 for r in rs if r > 0) / n, m / (sd / math.sqrt(n)) if sd else 0


def main(d):
    btc = load(f"{d}/BTCUSDT_1h.csv"); files = sorted(glob.glob(f"{d}/*_1h.csv"))
    print(f"{'strat':10} {'période':4} {'trades':>6} {'E[R]':>7} {'win':>6} {'t':>6}  OOS+ / coins")
    for name, f in STRATS.items():
        pool = {"IS": [], "OOS": []}; pos = 0; ncoin = 0
        for p in files:
            b = load(p); x = Ctx(b, btc); cut = int(len(b) * 2 / 3)
            a, o = run(x, f, 0, cut), run(x, f, cut, len(b))
            pool["IS"] += a; pool["OOS"] += o; ncoin += 1
            if o and sum(o) > 0: pos += 1
        for k in ("IS", "OOS"):
            n, m, w, t = stats(pool[k])
            extra = f"  {pos}/{ncoin}" if k == "OOS" else ""
            print(f"{name:10} {k:4} {n:6d} {m:+7.3f} {w:6.1%} {t:+6.2f}{extra}")


if __name__ == "__main__":
    main(sys.argv[1])

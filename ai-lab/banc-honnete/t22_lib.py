"""PREREG-19 : scalp avec ordres limites (maker). Voir PREREG-19-scalp-limite.md."""
import itertools, random
import banc
import t17_lib as L

MAKER, TAKER, SLIP, TRAV, MAXB = 0.0002, 0.0005, 0.0005, 0.0001, 24
A, B, C0, C1 = banc.ts("2024-01-01"), banc.ts("2026-01-01"), banc.ts("2026-01-01"), banc.ts("2026-10-17")
PAIRES = "XRP DOGE ADA LINK AVAX DOT LTC BCH UNI ATOM NEAR FIL AAVE APT OP TRX XLM ETC".split()


def rempli(C, i, sens, prix):
    """L'ordre limite posé à `prix` est-il traversé par la bougie i ?"""
    return C[i][2] < prix * (1 - TRAV) if sens > 0 else C[i][1] > prix * (1 + TRAV)


def trade_limite(C, i, sens, tp, sl):
    """Entrée limite exécutée dans la bougie i au prix e. Renvoie (rendement net, indice de sortie)."""
    e = C[i - 1][3]; obj = e * (1 + tp * sens); stp = e * (1 - sl * sens)
    for j in range(i, min(i + MAXB, len(C))):
        o, h, l = C[j][0], C[j][1], C[j][2]
        if j > i and ((o <= stp) if sens > 0 else (o >= stp)):
            return (o / e - 1) * sens - MAKER - TAKER - SLIP, j
        if (l <= stp) if sens > 0 else (h >= stp):
            return -sl - MAKER - TAKER - SLIP, j
        if j > i and ((h > obj * (1 + TRAV)) if sens > 0 else (l < obj * (1 - TRAV))):
            return tp - 2 * MAKER, j
    j = min(i + MAXB, len(C)) - 1
    return (C[j][3] / e - 1) * sens - MAKER - TAKER - SLIP, j


def strat(C, T, sig, tp, sl, a, b):
    lo = next(k for k, t in enumerate(T) if t >= a); hi = next((k for k, t in enumerate(T) if t >= b), len(T)) - 1
    i = lo; R = []; nl = ns = 0; ok_l = []; ok_s = []
    for k in range(lo + 1, hi - MAXB):      # instants où un ordre limite posé à la clôture précédente aurait été traversé
        if rempli(C, k, 1, C[k - 1][3]): ok_l.append(k)
        if rempli(C, k, -1, C[k - 1][3]): ok_s.append(k)
    while i < hi - 1:
        if sig[i] and rempli(C, i + 1, sig[i], C[i][3]):
            r, j = trade_limite(C, i + 1, sig[i], tp, sl); R.append(r); nl += sig[i] > 0; ns += sig[i] < 0; i = j + 1
        else: i += 1
    return R, nl, ns, ok_l, ok_s


def jumeaux(C, tp, sl, nl, ns, ok_l, ok_s, rnd):
    return sum(trade_limite(C, rnd.choice(ok_l), 1, tp, sl)[0] for _ in range(nl)) + sum(trade_limite(C, rnd.choice(ok_s), -1, tp, sl)[0] for _ in range(ns))



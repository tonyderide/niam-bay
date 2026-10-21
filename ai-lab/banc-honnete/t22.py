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


rows = []; cache = {}
COUPLES = ((0.005, 0.005), (0.01, 0.01), (0.015, 0.01), (0.02, 0.01), (0.03, 0.015))
for tf, m in itertools.product(("15m", "1h"), ("BTC", "ETH", "SOL")):
    T, C = banc.candles(banc.SYM[m], tf); S = L.signaux(C); cache[(tf, m)] = (T, C, S)
    for k, (tp, sl) in itertools.product("abcd", COUPLES):
        r1 = strat(C, T, S[k], tp, sl, A, B); r2 = strat(C, T, S[k], tp, sl, C0, C1)
        rows.append(((tf, m, k, tp, sl), sum(r1[0]), len(r1[0]), r2))
print(f"120 stratégies avec ordres limites : positives 2024-25 {sum(r[1] > 0 for r in rows)} ; positives 2026 {sum(sum(r[3][0]) > 0 for r in rows)} (avec taker, PREREG-14 : 1 et 8)")
best = max([r for r in rows if r[2] >= 30], key=lambda r: r[1]); (tf, m, k, tp, sl), s1, n1, (R2, nl, ns, okl, oks) = best
T, C, S = cache[(tf, m)]; rnd = random.Random(19); J = sorted(jumeaux(C, tp, sl, nl, ns, okl, oks, rnd) for _ in range(500))
g2 = sum(R2); j1 = g2 > 0 and sum(x < g2 for x in J) / 500 >= 0.99
print(f"SÉLECTION : {tf} {m} signal {k} TP {tp:.1%} SL {sl:.1%} | 2024-25 {100*s1:+.1f} % ({n1} trades)")
print(f"J1 2026 : {100*g2:+.1f} % ({len(R2)} trades) | jumeaux méd {100*J[250]:+.1f} % p99 {100*J[495]:+.1f} % -> {'RÉUSSI' if j1 else 'RATÉ'}")
tot = 0.0; pos = 0; infos = []
for p in PAIRES:
    T2, Cp = banc.candles(banc.SYM[p], tf); Sp = L.signaux(Cp)
    R, nl_, ns_, okl_, oks_ = strat(Cp, T2, Sp[k], tp, sl, A, C1); g = sum(R); tot += g; pos += g > 0; infos.append((Cp, nl_, ns_, okl_, oks_))
rnd = random.Random(191); JJ = sorted(sum(jumeaux(Cp, tp, sl, a, b, c, d, rnd) for Cp, a, b, c, d in infos) for _ in range(300))
j2 = tot > 0 and tot > JJ[int(0.95 * len(JJ))] and pos >= 10
print(f"J2 18 cryptos jamais vues : somme {100*tot:+.1f} % | positives {pos}/18 | jumeaux méd {100*JJ[150]:+.1f} % p95 {100*JJ[int(.95*len(JJ))]:+.1f} % -> {'RÉUSSI' if j2 else 'RATÉ'}")
print("VERDICT :", "GAGNE" if j1 and j2 else "ÉCHEC")

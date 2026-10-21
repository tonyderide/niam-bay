"""Vérifications du résultat t15 : (1) sortie au pire de (stop, ouverture) en cas de gap ; (2) bougies 5 min vs 15 min sur la même période ;
(3) sans martingale (mise fixe) et sens au hasard (mêmes sorties)."""
import calendar, pickle, time, random
ts = lambda d: calendar.timegm(time.strptime(d, "%Y-%m-%d")); FEE = 0.0005
def run(T, C, SL, ACT, DIST, NMAX, a, b, martingale=True, hasard=None):
    i = next(k for k, t in enumerate(T) if t >= a); fin = next((k for k, t in enumerate(T) if t >= b), len(T)) - 1
    eq = 0.0; mise = 1.0; d = 0; sens = 1; n = 0
    while i < fin:
        if hasard: sens = hasard.choice((1, -1))
        e = C[i][0]; stop = e * (1 - SL * sens); actif = False; meilleur = e; j = i
        while j < fin:
            o, h, l = C[j][0], C[j][1], C[j][2]
            if (o <= stop) if sens > 0 else (o >= stop): r = (o / e - 1) * sens; break          # gap : sortie à l'ouverture
            if (l <= stop) if sens > 0 else (h >= stop): r = (stop / e - 1) * sens; break
            meilleur = max(meilleur, h) if sens > 0 else min(meilleur, l)
            if not actif and (meilleur / e - 1) * sens >= ACT: actif = True
            if actif:
                s2 = meilleur * (1 - DIST * sens); stop = max(stop, s2) if sens > 0 else min(stop, s2)
            j += 1
        else: break
        eq += (mise if martingale else 1.0) * (r - 2 * FEE); n += 1
        if r > 0: mise = 1.0; d = 0
        elif d >= NMAX: mise = 1.0; d = 0; sens = -sens
        else: mise *= 2; d += 1; sens = -sens
        i = j + 1
    return eq, n
P = [("ETH", 0.01, 0.003, 4), ("ETH", 0.02, 0.003, 5), ("SOL", 0.02, 0.003, 5)]
a, b = ts("2025-12-01"), ts("2026-10-17")
for sym, SL, DIST, N in P:
    T15, C15 = pickle.load(open(f"/home/tony/.cache/banc-honnete/PF_{sym}USD_15m_2023-11-01.pkl", "rb"))
    T5, C5 = pickle.load(open(f"/home/tony/.cache/banc-honnete/PF_{sym}USD_5m_2025-12-01.pkl", "rb"))
    g15 = run(T15, C15, SL, 0.01, DIST, N, a, b); g5 = run(T5, C5, SL, 0.01, DIST, N, a, b)
    fixe = run(T5, C5, SL, 0.01, DIST, N, a, b, martingale=False)
    H = sorted(run(T5, C5, SL, 0.01, DIST, N, a, b, martingale=False, hasard=random.Random(k))[0] for k in range(40))
    print(f"{sym} SL {SL:.0%} suiveur 0,3 % x{N} | déc-oct : 15 min {g15[0]:+.2f} x ({g15[1]} tr.) | 5 min {g5[0]:+.2f} x ({g5[1]} tr.) | 5 min mise fixe {fixe[0]:+.2f} | 5 min sens au hasard mise fixe : méd {H[20]:+.2f} max {H[-1]:+.2f}")

"""Martingale + trailing (description de Tony, 22/10) : toujours en position. Perte (SL) -> mise x2 et sens inversé.
Dès +ACT de gain, un stop suiveur à DIST du meilleur prix remplace le SL ; sortie par le suiveur = gain -> mise 1, même sens.
BTC/ETH/SOL 15 min ; choix sur 2024-2025, jugement sur 2026. Bougie ambiguë : SL d'abord, et le suiveur ne monte qu'avec la bougie suivante."""
import calendar, pickle, time, itertools
ts = lambda d: calendar.timegm(time.strptime(d, "%Y-%m-%d")); FEE = 0.0005
def run(T, C, SL, ACT, DIST, NMAX, a, b):
    i = next(k for k, t in enumerate(T) if t >= a); fin = next((k for k, t in enumerate(T) if t >= b), len(T)) - 1
    eq = 0.0; mise = 1.0; d = 0; sens = 1; casse = 0; n = 0
    while i < fin:
        e = C[i][0]; stop = e * (1 - SL * sens); actif = False; meilleur = e; j = i
        while j < fin:
            h, l = C[j][1], C[j][2]
            if (l <= stop) if sens > 0 else (h >= stop):                       # stop touché (SL ou suiveur)
                r = (stop / e - 1) * sens; break
            meilleur = max(meilleur, h) if sens > 0 else min(meilleur, l)
            if not actif and (meilleur / e - 1) * sens >= ACT: actif = True
            if actif:
                s2 = meilleur * (1 - DIST * sens); stop = max(stop, s2) if sens > 0 else min(stop, s2)
            j += 1
        else: break
        eq += mise * (r - 2 * FEE); n += 1
        if r > 0: mise = 1.0; d = 0
        elif d >= NMAX: casse += 1; mise = 1.0; d = 0; sens = -sens
        else: mise *= 2; d += 1; sens = -sens
        i = j + 1
    return eq, n, casse
rows = []
for sym in ("XBT", "ETH", "SOL"):
    T, C = pickle.load(open(f"/home/tony/.cache/banc-honnete/PF_{sym}USD_15m_2023-11-01.pkl", "rb"))
    for SL, ACT, DIST, N in itertools.product((0.003, 0.005, 0.01, 0.02), (0.01,), (0.003, 0.005, 0.01), (3, 4, 5)):
        rows.append((sym, SL, ACT, DIST, N, run(T, C, SL, ACT, DIST, N, ts("2024-01-01"), ts("2026-01-01")), run(T, C, SL, ACT, DIST, N, ts("2026-01-01"), ts("2026-10-17"))))
print(f"{len(rows)} réglages ; positifs 2024-25 : {sum(r[5][0] > 0 for r in rows)} ; positifs 2026 : {sum(r[6][0] > 0 for r in rows)}")
top = sorted(rows, key=lambda r: -r[5][0])[:8]
for s, SL, ACT, DIST, N, A, B in top:
    print(f"  {s} SL {SL:.1%} suiveur dès +{ACT:.0%} à {DIST:.1%} x{N} : 2024-25 {A[0]:+6.2f} x ({A[1]} trades, {A[2]} cassées) -> 2026 {B[0]:+6.2f} x ({B[1]} trades)")
print(f"positifs en 2026 parmi ces 8 : {sum(r[6][0] > 0 for r in top)}/8")

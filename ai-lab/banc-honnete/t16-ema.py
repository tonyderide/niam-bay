"""Martingale + stop suiveur dès +1 % + sens donné par l'EMA (description de Tony, 22/10). Toujours en position.
Sens à chaque entrée = signe(clôture précédente − EMA_k). Perte -> mise x2 ; gain -> mise 1. Sorties corrigées des gaps (sortie à l'ouverture si le prix a sauté le stop).
BTC/ETH/SOL 15 min ; choix sur 2024-2025, jugement sur 2026 ; témoin = mêmes règles avec sens tiré au hasard."""
import calendar, pickle, time, itertools, random
ts = lambda d: calendar.timegm(time.strptime(d, "%Y-%m-%d")); FEE = 0.0005
def ema(x, k):
    a = 2 / (k + 1); out = [x[0]]
    for v in x[1:]: out.append(out[-1] + a * (v - out[-1]))
    return out
def run(T, C, E, SL, DIST, NMAX, a, b, hasard=None, ACT=0.01):
    i = next(k for k, t in enumerate(T) if t >= a); fin = next((k for k, t in enumerate(T) if t >= b), len(T)) - 1
    eq = 0.0; mise = 1.0; d = 0; n = 0
    while i < fin:
        sens = hasard.choice((1, -1)) if hasard else (1 if C[i - 1][3] > E[i - 1] else -1)
        e = C[i][0]; stop = e * (1 - SL * sens); actif = False; meilleur = e; j = i
        while j < fin:
            o, h, l = C[j][0], C[j][1], C[j][2]
            if (o <= stop) if sens > 0 else (o >= stop): r = (o / e - 1) * sens; break
            if (l <= stop) if sens > 0 else (h >= stop): r = (stop / e - 1) * sens; break
            meilleur = max(meilleur, h) if sens > 0 else min(meilleur, l)
            if not actif and (meilleur / e - 1) * sens >= ACT: actif = True
            if actif:
                s2 = meilleur * (1 - DIST * sens); stop = max(stop, s2) if sens > 0 else min(stop, s2)
            j += 1
        else: break
        eq += mise * (r - 2 * FEE); n += 1
        if r > 0 or d >= NMAX: mise = 1.0; d = 0
        else: mise *= 2; d += 1
        i = j + 1
    return eq, n
rows = []; data = {}
for sym in ("XBT", "ETH", "SOL"):
    T, C = pickle.load(open(f"/home/tony/.cache/banc-honnete/PF_{sym}USD_15m_2023-11-01.pkl", "rb")); cl = [c[3] for c in C]
    data[sym] = (T, C, {k: ema(cl, k) for k in (20, 50, 200)})
    for K, SL, DIST, N in itertools.product((20, 50, 200), (0.005, 0.01, 0.02), (0.003, 0.005, 0.01), (3, 4, 5)):
        E = data[sym][2][K]
        rows.append((sym, K, SL, DIST, N, run(T, C, E, SL, DIST, N, ts("2024-01-01"), ts("2026-01-01")), run(T, C, E, SL, DIST, N, ts("2026-01-01"), ts("2026-10-17"))))
print(f"{len(rows)} réglages ; positifs 2024-25 : {sum(r[5][0] > 0 for r in rows)} ; positifs 2026 : {sum(r[6][0] > 0 for r in rows)}")
top = sorted(rows, key=lambda r: -r[5][0])[:8]
for sym, K, SL, DIST, N, A, B in top:
    T, C, Es = data[sym]
    H = sorted(run(T, C, Es[K], SL, DIST, N, ts("2026-01-01"), ts("2026-10-17"), hasard=random.Random(s))[0] for s in range(100))
    print(f"  {sym} EMA{K} SL {SL:.1%} suiveur {DIST:.1%} x{N} : 2024-25 {A[0]:+6.2f} x -> 2026 {B[0]:+6.2f} x ({B[1]} tr.) | hasard 2026 méd {H[50]:+.2f} p95 {H[95]:+.2f}")
print(f"positifs en 2026 parmi ces 8 : {sum(r[6][0] > 0 for r in top)}/8")

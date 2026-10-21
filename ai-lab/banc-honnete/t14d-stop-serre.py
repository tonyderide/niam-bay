"""Martingale à stop serré (description de Tony, 22/10) : mise 1, perte -> mise x2 et sens inversé, gain -> mise 1. Bougies 5 min.
Choix sur 2025-12 -> 2026-06, jugement sur 2026-07 -> 2026-10-17. Bougie qui touche TP et SL = SL (prudent). Frais taker 0,05 % par côté."""
import calendar, pickle, time, itertools
ts = lambda d: calendar.timegm(time.strptime(d, "%Y-%m-%d")); FEE = 0.0005
def run(T, C, TP, SL, NMAX, a, b):
    i = next(k for k, t in enumerate(T) if t >= a); fin = next((k for k, t in enumerate(T) if t >= b), len(T)) - 1
    eq = 0.0; mise = 1.0; d = 0; sens = 1; casse = 0; n = 0; pire = 0.0; pic = 0.0
    while i < fin:
        e = C[i][0]; tp = e * (1 + TP * sens); sl = e * (1 - SL * sens); j = i
        while j < fin:
            h, l = C[j][1], C[j][2]
            if (l <= sl) if sens > 0 else (h >= sl): r = -SL; break
            if (h >= tp) if sens > 0 else (l <= tp): r = TP; break
            j += 1
        else: break
        eq += mise * (r - 2 * FEE); n += 1; pic = max(pic, eq); pire = max(pire, pic - eq)
        if r > 0: mise = 1.0; d = 0
        elif d >= NMAX: casse += 1; mise = 1.0; d = 0
        else: mise *= 2; d += 1; sens = -sens
        i = j + 1
    return eq, n, casse, pire
rows = []
for sym in ("XBT", "ETH", "SOL"):
    T, C = pickle.load(open(f"/home/tony/.cache/banc-honnete/PF_{sym}USD_5m_2025-12-01.pkl", "rb"))
    for SL, TP, N in itertools.product((0.001, 0.002, 0.003, 0.005), (0.002, 0.003, 0.005, 0.01, 0.02), (3, 4, 5, 6, 7, 8)):
        A = run(T, C, TP, SL, N, ts("2025-12-01"), ts("2026-07-01")); B = run(T, C, TP, SL, N, ts("2026-07-01"), ts("2026-10-17"))
        rows.append((sym, SL, TP, N, A, B))
print(f"{len(rows)} réglages ; positifs déc-juin : {sum(r[4][0] > 0 for r in rows)} ; positifs juil-oct : {sum(r[5][0] > 0 for r in rows)}")
top = sorted(rows, key=lambda r: -r[4][0])[:10]
print("10 meilleurs de déc-juin, jugés sur juil-oct (gain en x la mise de départ, 1 x = 1 € si la mise est 1 €) :")
for s, SL, TP, N, A, B in top:
    print(f"  {s} SL {SL:.1%} TP {TP:.1%} x{N} : déc-juin {A[0]:+7.2f} ({A[1]} trades, {A[2]} cassées, pire chute {A[3]:.1f}) -> juil-oct {B[0]:+7.2f} ({B[2]} cassées)")
print(f"positifs en juil-oct parmi ces 10 : {sum(r[5][0] > 0 for r in top)}/10")

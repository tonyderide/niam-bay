"""Martingale de Martin (stop parfait, aucun trade manuel, aucun bug) : toutes les combinaisons TP / SL / doublements, BTC ETH SOL 15 min, 2024-01 -> 2026-10."""
import calendar, pickle, time, itertools
ts = lambda d: calendar.timegm(time.strptime(d, "%Y-%m-%d")); FEE = 0.0005
def run(T, C, TP, SL, NMAX):
    i = next(k for k, t in enumerate(T) if t >= ts("2024-01-01")); fin = len(T) - 1
    eq = 0.0; mise = 1.0; d = 0; sens = 1; courbe = []; casse = 0
    while i < fin:
        e = C[i][0]; tp = e * (1 + TP * sens); sl = e * (1 - SL * sens); j = i
        while j < fin:
            h, l = C[j][1], C[j][2]
            if (l <= sl) if sens > 0 else (h >= sl): r = -SL; break
            if (h >= tp) if sens > 0 else (l <= tp): r = TP; break
            j += 1
        else: break
        eq += mise * (r - 2 * FEE); courbe.append((T[j], eq))
        if r > 0: mise = 1.0; d = 0
        elif d >= NMAX: casse += 1; mise = 1.0; d = 0
        else: mise *= 2; d += 1; sens = -sens
        i = j + 1
    W = 91 * 86400; pos = tot = 0; t = courbe[0][0]; k = 0
    vals = courbe
    def at(x):
        nonlocal k
        while k + 1 < len(vals) and vals[k + 1][0] <= x: k += 1
        return vals[k][1] if vals[k][0] <= x else 0.0
    while t + W <= courbe[-1][0]:
        k = 0; a = at(t); k = 0; b = at(t + W); pos += b > a; tot += 1; t += 7 * 86400
    return eq, casse, pos / tot
rows = []
for sym in ("XBT", "ETH", "SOL"):
    T, C = pickle.load(open(f"/home/tony/.cache/banc-honnete/PF_{sym}USD_15m_2023-11-01.pkl", "rb"))
    for TP, SL, N in itertools.product((0.005, 0.01, 0.015, 0.02), (0.005, 0.01, 0.015, 0.02), (3, 4, 5)):
        eq, casse, f3 = run(T, C, TP, SL, N); rows.append((eq, sym, TP, SL, N, casse, f3))
rows.sort(reverse=True)
print(f"{len(rows)} combinaisons ; gagnantes sur 2,8 ans : {sum(r[0] > 0 for r in rows)}")
print("Les 8 meilleures :")
for eq, sym, TP, SL, N, casse, f3 in rows[:8]: print(f"  {sym} TP {TP:.1%} SL {SL:.1%} x{N} : {eq:+6.2f} x | séries cassées {casse} | fenêtres de 3 mois positives {f3:.0%}")
print(f"Médiane des fenêtres de 3 mois positives : {sorted(r[6] for r in rows)[len(rows)//2]:.0%}")

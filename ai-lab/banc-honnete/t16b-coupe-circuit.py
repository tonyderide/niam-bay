"""t16 + coupe-circuit (Tony : « un système de stop quand trop de perte ») : si la perte du jour (UTC) dépasse PLAFOND x la position de départ,
plus aucun trade jusqu'au lendemain, mise remise à 1."""
import calendar, pickle, time, itertools
ts = lambda d: calendar.timegm(time.strptime(d, "%Y-%m-%d")); FEE = 0.0005
def ema(x, k):
    a = 2 / (k + 1); out = [x[0]]
    for v in x[1:]: out.append(out[-1] + a * (v - out[-1]))
    return out
def run(T, C, E, SL, DIST, NMAX, a, b, PLAF, ACT=0.01):
    i = next(k for k, t in enumerate(T) if t >= a); fin = next((k for k, t in enumerate(T) if t >= b), len(T)) - 1
    eq = 0.0; mise = 1.0; d = 0; jour = None; perte_j = 0.0; coupures = 0
    while i < fin:
        jj = T[i] // 86400
        if jj != jour: jour = jj; perte_j = 0.0
        if perte_j <= -PLAF:
            i += 1; mise = 1.0; d = 0; continue
        sens = 1 if C[i - 1][3] > E[i - 1] else -1
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
        g = mise * (r - 2 * FEE); eq += g; perte_j += g
        if perte_j <= -PLAF: coupures += 1
        if r > 0 or d >= NMAX: mise = 1.0; d = 0
        else: mise *= 2; d += 1
        i = j + 1
    return eq, coupures
rows = []
for sym in ("XBT", "ETH", "SOL"):
    T, C = pickle.load(open(f"/home/tony/.cache/banc-honnete/PF_{sym}USD_15m_2023-11-01.pkl", "rb")); cl = [c[3] for c in C]; Es = {k: ema(cl, k) for k in (20, 50, 200)}
    for K, SL, DIST, N, P in itertools.product((20, 50, 200), (0.005, 0.01, 0.02), (0.005, 0.01), (3, 4, 5), (0.05, 0.1, 0.2)):
        rows.append((sym, K, SL, DIST, N, P, run(T, C, Es[K], SL, DIST, N, ts("2024-01-01"), ts("2026-01-01"), P), run(T, C, Es[K], SL, DIST, N, ts("2026-01-01"), ts("2026-10-17"), P)))
print(f"{len(rows)} réglages ; positifs 2024-25 : {sum(r[6][0] > 0 for r in rows)} ; positifs 2026 : {sum(r[7][0] > 0 for r in rows)}")
for r in sorted(rows, key=lambda r: -r[6][0])[:5]:
    print(f"  {r[0]} EMA{r[1]} SL {r[2]:.1%} suiveur {r[3]:.1%} x{r[4]} plafond {r[5]:.2f} x/jour : 2024-25 {r[6][0]:+.2f} x ({r[6][1]} coupures) -> 2026 {r[7][0]:+.2f} x ({r[7][1]} coupures)")

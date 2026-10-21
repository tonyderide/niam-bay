"""PREREG-13 : BTC géré par la volatilité. Voir PREREG-13-vol-geree.md."""
import calendar, math, pickle, random, statistics, time
ts = lambda d: calendar.timegm(time.strptime(d, "%Y-%m-%d"))
T, C = pickle.load(open("/home/tony/.cache/banc-honnete/PF_XBTUSD_1h_2023-11-01.pkl", "rb"))
Cl = [c[3] for c in C]
v = [0.0] * len(Cl); e = 0.005
for i in range(1, len(Cl)):
    v[i] = e; e = 0.94 * e + 0.06 * abs(math.log(Cl[i] / Cl[i - 1]))
jours = [i for i in range(1, len(T)) if T[i] % 86400 == 0]          # indices des bougies de 00h UTC
cible = statistics.median(v[i] for i in jours if ts("2024-01-01") <= T[i] < ts("2026-01-01"))
J = [i for i in jours if ts("2026-01-01") <= T[i] < ts("2026-10-17")]
r = [Cl[J[k + 1]] / Cl[J[k]] - 1 for k in range(len(J) - 1)]       # rendement BTC jour par jour
w = [min(1.0, cible / v[J[k]]) for k in range(len(J) - 1)]          # poids décidé à 00h avec l'info d'avant

def perf(w):
    eq = 1.0; pic = 1.0; dd = 0.0; R = []; prev = 1.0
    for k, x in enumerate(r):
        frais = 0.0005 * abs(w[k] - prev); prev = w[k]
        q = w[k] * x - frais; R.append(q); eq *= 1 + q; pic = max(pic, eq); dd = max(dd, 1 - eq / pic)
    m, s = statistics.mean(R), statistics.pstdev(R)
    return (m / s * math.sqrt(365) if s else 0), eq - 1, dd

sg, rg, dg = perf(w); sb, rb, db = perf([1.0] * len(r))
rnd = random.Random(13); S = []
for _ in range(500):
    ww = w[:]; rnd.shuffle(ww); S.append(perf(ww)[0])
S.sort()
print(f"2026 ({len(r)} jours) | exposition moyenne {statistics.mean(w):.0%}")
print(f"  garder-acheter   : Sharpe {sb:+.2f}  rendement {100*rb:+.1f} %  pire perte {100*db:.1f} %")
print(f"  géré par la vol. : Sharpe {sg:+.2f}  rendement {100*rg:+.1f} %  pire perte {100*dg:.1f} %")
print(f"  témoins mélangés : Sharpe p50 {S[250]:+.2f}  p95 {S[475]:+.2f}  | rang du géré {sum(x < sg for x in S)/5:.0f}e centile")
print("VERDICT :", "GAGNE" if sg > sb and sg > S[475] else "ÉCHEC")

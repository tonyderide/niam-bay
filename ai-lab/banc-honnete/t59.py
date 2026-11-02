"""PREREG-59 : jours 91-180 (règles : PREREG-59-apres-90-jours.md)."""
import json, os, random, statistics as st, time, calendar
ICI = os.path.dirname(os.path.abspath(__file__)); J = 86_400_000; FR = 0.001; N = 90
src = open("t53_vrais_neufs.py").read(); ns = {"__file__": os.path.abspath("t53_vrais_neufs.py")}
exec(src[:src.index("vrai = lambda")], ns)
i_ = ns["ns"]; C, DEB, FINS, P, PB = i_["C"], i_["DEB"], i_["FINS"], ns["P"], ns["PB"]
vrai = lambda s: P.get(s) is not None and P[s] == PB.get(s[:-4])
D0 = min(DEB.values()); ut = lambda a, m, d: calendar.timegm((a, m, d, 0, 0, 0)) * 1000
def mesure(s, e, liq=False):
    if e not in C[s]: return None
    x = min(e + (N - 1) * J, FINS[s])
    while x not in C[s] and x > e: x -= J
    if liq:
        for d in range(e, x + J, J):
            if d in C[s] and C[s][d][1] >= 2 * C[s][e][0]: return -1.0
    return max(-1.0, -(C[s][x][1] / C[s][e][0] - 1) - 2 * FR)
pools = {}
def pool(e):
    if e not in pools: pools[e] = [s for s in C if (DEB[s] <= e - 365 * J or DEB[s] <= D0 + 31 * J) and e in C[s]]
    return pools[e]
T = []
for s in C:
    if DEB[s] <= D0 + 31 * J or not vrai(s): continue
    e1 = DEB[s] + J; e2 = e1 + 90 * J
    if not (ut(2019, 1, 1) <= e2 <= ut(2026, 7, 2)) or e2 not in C[s]: continue
    T.append((e2, s, mesure(s, e2), mesure(s, e1), mesure(s, e2, True)))
T = [x for x in T if x[2] is not None and pool(x[0])]
r = [x[2] for x in T]; m = st.mean(r); rng = random.Random(59); tem = []
for _ in range(1000):
    v = []
    for e, *_ in T:
        t = None
        while t is None: t = mesure(rng.choice(pool(e)), e)
        v.append(t)
    tem.append(st.mean(v))
p = sum(x >= m for x in tem) / len(tem)
res = dict(trades=len(T), moy=m, med=st.median(r), pos=sum(x > 0 for x in r) / len(r), temoin_moy=st.mean(tem), temoin_et=st.pstdev(tem), p=p,
           moy_liquidation=st.mean(x[4] for x in T), moy_fenetre_1_90_memes_jetons=st.mean(x[3] for x in T if x[3] is not None),
           par_an={y: (len(z), st.mean(z)) for y in range(2019, 2027) for z in [[x[2] for x in T if time.gmtime(x[0] / 1000).tm_year == y]] if z})
res["verdict"] = "PERSISTE" if m > 0 and p < 0.05 else "S'ARRÊTE"
json.dump(res, open("t59.json", "w"), indent=1); print(json.dumps(res, indent=1))

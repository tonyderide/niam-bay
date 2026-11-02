"""PREREG-53 : réplication comptant (règles : PREREG-53-cotations-comptant.md, commit a445ee4)."""
import calendar, json, os, random, statistics as st, time
ICI = os.path.dirname(os.path.abspath(__file__)); J = 86_400_000; FR = 0.001; N = 90
K = json.load(open(os.path.join(ICI, "comptant/klines.json")))
C = {s: {x[0]: (x[1], x[2]) for x in v} for s, v in K.items() if v}
DEB = {s: min(v) for s, v in C.items()}; FINS = {s: max(v) for s, v in C.items()}
ut = lambda a, m, d: calendar.timegm((a, m, d, 0, 0, 0)) * 1000
A0, B0, BF = ut(2018, 1, 1), ut(2021, 1, 1), ut(2026, 7, 29)
def mesure(s, e):
    if e not in C[s]: return None
    x = min(e + (N - 1) * J, FINS[s])
    while x not in C[s] and x > e: x -= J
    return max(-1.0, -(C[s][x][1] / C[s][e][0] - 1) - 2 * FR)
nouv = sorted((DEB[s] + J, s) for s in C if DEB[s] > ut(2017, 8, 31))
pools = {}
def pool(e):
    if e not in pools: pools[e] = [s for s in C if DEB[s] <= e - 365 * J and e in C[s]]
    return pools[e]
out = {}
for nom, (a, b) in (("A_2018_2020", (A0, B0)), ("B_2021_2026", (B0, BF + 1))):
    T = [(e, s, mesure(s, e)) for e, s in nouv if a <= e < b]; T = [x for x in T if x[2] is not None and pool(x[0])]
    r = [x[2] for x in T]; m = st.mean(r); rng = random.Random(53); tem = []
    for _ in range(1000):
        v = []
        for e, _, _ in T:
            t = None
            while t is None: t = mesure(rng.choice(pool(e)), e)
            v.append(t)
        tem.append(st.mean(v))
    out[nom] = dict(trades=len(T), moy=m, med=st.median(r), pos=sum(x > 0 for x in r) / len(r), plancher=sum(x <= -1 for x in r),
                    temoin_moy=st.mean(tem), temoin_et=st.pstdev(tem), p=sum(x >= m for x in tem) / len(tem),
                    par_an={y: (len(z), st.mean(z)) for y in range(2018, 2027) for z in [[x[2] for x in T if time.gmtime(x[0] / 1000).tm_year == y]] if z})
    print(nom, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in out[nom].items() if k != "par_an"}, flush=True)
    print("  ", {y: (n, round(v, 3)) for y, (n, v) in out[nom]["par_an"].items()}, flush=True)
ok = [out[k]["moy"] > 0 and out[k]["p"] < 0.05 for k in ("A_2018_2020", "B_2021_2026")]
out["verdict"] = "RÉPLIQUÉ" if all(ok) else "PARTIEL" if any(ok) else "NON RÉPLIQUÉ"
json.dump(out, open(os.path.join(ICI, "t53.json"), "w"), indent=1); print("VERDICT", out["verdict"])

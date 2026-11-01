"""PREREG-46 : short des nouvelles cotations (règles : PREREG-46-short-nouvelles-cotations.md, commit d8f3361)."""
import bisect, calendar, json, os, random, statistics as st, time
ICI = os.path.dirname(os.path.abspath(__file__)); J = 86_400_000; TK = 0.0005; NS = (14, 30, 60, 90)
K = json.load(open(os.path.join(ICI, "../carry-financement/data-univers/klines.json")))
F = json.load(open(os.path.join(ICI, "listings/funding.json")))
C = {s: {k[0]: (k[1], k[2]) for k in v} for s, v in K.items() if v}
FT = {s: [x[0] for x in F.get(s, [])] for s in C}; FR = {s: [x[1] for x in F.get(s, [])] for s in C}
DEB = {s: min(v) for s, v in C.items()}; FINS = {s: max(v) for s, v in C.items()}
T_FIN = 1793059200000 - J                       # dernière bougie 26/10/2026
A21, A26 = calendar.timegm((2021, 1, 1, 0, 0, 0)) * 1000, calendar.timegm((2026, 1, 1, 0, 0, 0)) * 1000
def fin_sum(s, a, b): t = FT[s]; return sum(FR[s][bisect.bisect_left(t, a):bisect.bisect_left(t, b)])
def trade(s, e, N):
    """short à l'ouverture du jour e, sortie à la clôture du jour e+N-1 ou du dernier jour disponible. None si pas de bougie à e."""
    if e not in C[s]: return None
    x = min(e + (N - 1) * J, FINS[s]); 
    while x not in C[s] and x > e: x -= J
    brut = -(C[s][x][1] / C[s][e][0] - 1); f = fin_sum(s, e, x + J)
    return max(-1.0, brut + f - 2 * TK), brut, f
nouvelles = sorted((DEB[s] + J, s) for s in C if DEB[s] > 1599004800000)
anciennes_a = lambda e: [s for s in C if DEB[s] <= e - 365 * J and e in C[s]]
R = {}
for N in NS:
    for nom, ok in (("choix", lambda e: A21 <= e < A26), ("2026", lambda e: A26 <= e <= T_FIN - (N - 1) * J)):
        T = [(e, s, trade(s, e, N)) for e, s in nouvelles if ok(e)]; T = [(e, s, t) for e, s, t in T if t]
        r = [t[0] for _, _, t in T]
        R[(N, nom)] = dict(n=len(r), moy=st.mean(r) if r else 0, med=st.median(r) if r else 0, gagnants=sum(v > 0 for v in r) / max(1, len(r)),
                           fin_moy=st.mean(t[2] for _, _, t in T) if T else 0, pire=min(r) if r else 0, plancher=sum(t[1] + t[2] - 2 * TK <= -1 for _, _, t in T),
                           par_an={y: st.mean([t[0] for e, _, t in T if time.gmtime(e / 1000).tm_year == y]) for y in sorted({time.gmtime(e / 1000).tm_year for e, _, _ in T})},
                           trades=[(e, s) for e, s, _ in T])
        print(N, nom, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in R[(N, nom)].items() if k not in ("trades", "par_an")}, flush=True)
Nc = max(NS, key=lambda N: R[(N, "choix")]["moy"]); J26 = R[(Nc, "2026")]
rng = random.Random(46); tem = []; pool = {}
for _ in range(1000):
    r = []
    for e, s in J26["trades"]:
        if e not in pool: pool[e] = anciennes_a(e)
        t = None
        while t is None: t = trade(rng.choice(pool[e]), e, Nc)
        r.append(t[0])
    tem.append(st.mean(r))
p = sum(t >= J26["moy"] for t in tem) / len(tem)
queue = J26["plancher"] / max(1, J26["n"]) > 0.05
v = "GAGNE" if R[(Nc, "choix")]["moy"] > 0 and J26["moy"] > 0 and p < 0.05 else "NON DÉMONTRÉ" if J26["moy"] > 0 else "PERD"
out = dict(N_choisi=Nc, grille={f"{N}_{nom}": {k: v for k, v in x.items() if k != "trades"} for (N, nom), x in R.items()},
           temoin_2026=dict(moy=st.mean(tem), et=st.pstdev(tem), p=p), risque_de_queue=queue, verdict=v,
           sans_financement=len([s for s in C if not FT[s]]))
json.dump(out, open(os.path.join(ICI, "t46.json"), "w"), indent=1); print("N", Nc, "témoin", out["temoin_2026"], "queue", queue, "VERDICT", v)

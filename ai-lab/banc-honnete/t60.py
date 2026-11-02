"""PREREG-60 : Miller, ouverture du perpétuel (règles : PREREG-60-miller-perpetuel.md, commit d7068ab)."""
import calendar, json, os, random, statistics as st, time
ICI = os.path.dirname(os.path.abspath(__file__)); J = 86_400_000; FR = 0.001; N = 90
S = {s: {x[0]: (x[1], x[2]) for x in v} for s, v in json.load(open("comptant/klines.json")).items() if v}
KP = json.load(open("../carry-financement/data-univers/klines.json"))
EI = {s["symbol"]: s.get("underlyingType") for s in json.load(open("listings/exchangeInfo-20261101.json"))["symbols"]}
DS = {s: min(v) for s, v in S.items()}; FS = {s: max(v) for s, v in S.items()}; D0 = min(DS.values())
ut = lambda a, m, d: calendar.timegm((a, m, d, 0, 0, 0)) * 1000
def mesure(s, e, liq=False):
    if e not in S[s]: return None
    x = min(e + (N - 1) * J, FS[s])
    while x not in S[s] and x > e: x -= J
    if liq and any(d in S[s] and S[s][d][1] >= 2 * S[s][e][0] for d in range(e, x + J, J)): return -1.0
    return max(-1.0, -(S[s][x][1] / S[s][e][0] - 1) - 2 * FR)
EV = []
for p, v in KP.items():
    if not v or EI.get(p, "COIN") != "COIN" or v[0][0] <= 1599004800000: continue
    sp = p[4:] if p.startswith("1000") and p[4:] in S else p
    if sp not in S: continue
    L = v[0][0]; e = L + J
    if DS[sp] <= L - 180 * J and ut(2020, 9, 2) <= L <= ut(2026, 6, 29) and mesure(sp, e) is not None: EV.append((e, sp, p))
pools = {}
def pool(e, sauf):
    if e not in pools: pools[e] = [s for s in S if (DS[s] <= e - 365 * J or DS[s] <= D0 + 31 * J) and e in S[s]]
    return [s for s in pools[e] if s != sauf]
def bilan(X, seed):
    r = [mesure(s, e) for e, s, _ in X]; m = st.mean(r); rng = random.Random(seed); tem = []
    for _ in range(1000):
        v = []
        for e, s, _ in X:
            t = None
            while t is None: t = mesure(rng.choice(pool(e, s)), e)
            v.append(t)
        tem.append(st.mean(v))
    return dict(n=len(r), moy=m, med=st.median(r), pos=sum(x > 0 for x in r) / len(r), liq=st.mean(mesure(s, e, True) for e, s, _ in X),
                temoin_moy=st.mean(tem), p=sum(x >= m for x in tem) / len(tem))
B0 = ut(2024, 1, 1)
res = dict(AB=bilan(EV, 60), A=bilan([x for x in EV if x[0] < B0], 600), B=bilan([x for x in EV if x[0] >= B0], 6000),
           par_an={y: (len(z), st.mean(z)) for y in range(2020, 2027) for z in [[mesure(s, e) for e, s, _ in EV if time.gmtime(e / 1000).tm_year == y]] if z})
ab, a, b = res["AB"], res["A"], res["B"]
res["verdict"] = "DÉMONTRÉ" if ab["moy"] > 0 and ab["p"] < 0.05 and a["moy"] > 0 and b["moy"] > 0 else "NON DÉMONTRÉ" if ab["moy"] > 0 else "PERD"
json.dump(res, open("t60.json", "w"), indent=1); print(json.dumps(res, indent=1))

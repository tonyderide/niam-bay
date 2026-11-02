"""PREREG-57 : profil de risque du portefeuille couvert (règles : PREREG-57-profil-risque-cotations.md, commit 2e6b255)."""
import bisect, calendar, json, math, os, random, statistics as st, time
ICI = os.path.dirname(os.path.abspath(__file__)); J = 86_400_000; TK = 0.0005; N = 90
K = json.load(open(os.path.join(ICI, "../carry-financement/data-univers/klines.json"))); F = json.load(open(os.path.join(ICI, "listings/funding.json")))
EI = {s["symbol"]: s.get("underlyingType") for s in json.load(open(os.path.join(ICI, "listings/exchangeInfo-20261101.json")))["symbols"]}
C = {s: {k[0]: (k[1], k[2]) for k in v} for s, v in K.items() if v and EI.get(s, "COIN") == "COIN"}
FT = {s: [x[0] for x in F.get(s, [])] for s in C}; FR = {s: [x[1] for x in F.get(s, [])] for s in C}
DEB = {s: min(v) for s, v in C.items()}; FINS = {s: max(v) for s, v in C.items()}
ut = lambda a, m, d: calendar.timegm((a, m, d, 0, 0, 0)) * 1000
D0, D1 = ut(2021, 1, 1), ut(2026, 10, 27); JOURS = list(range(D0, D1, J))
def fen(s, e):
    x = min(e + (N - 1) * J, FINS[s]); return (e, x)
SHORTS = [(s,) + fen(s, DEB[s] + J) for s in C if DEB[s] > 1599004800000 and DEB[s] + J in C[s] and DEB[s] + J < D1]
def fin(s, d): t = FT[s]; return sum(FR[s][bisect.bisect_left(t, d):bisect.bisect_left(t, d + J)])
anciens = {d: [s for s in C if DEB[s] <= d - 365 * J and d in C[s]] for d in JOURS}
def simule(shorts):
    prev = {}; serie = []
    ouverts = {d: [] for d in JOURS}
    for s, e, x in shorts:
        for d in range(max(e, D0), min(x, D1 - J) + J, J):
            if d in ouverts and d in C[s]: ouverts[d].append(s)
    for d in JOURS:
        sh = ouverts[d]; w = {}
        if sh:
            for s in sh: w[s] = w.get(s, 0) - 1 / len(sh)
            lo = anciens[d]
            for s in lo: w[s] = w.get(s, 0) + 1 / len(lo)
        r = sum(v * (C[s][d][1] / C[s][d][0] - 1) - v * fin(s, d) for s, v in w.items())
        r -= TK * sum(abs(w.get(s, 0) - prev.get(s, 0)) for s in set(w) | set(prev))
        serie.append(r); prev = w
    return serie, ouverts
def mesures(serie, I):
    v = [serie[i] for i in I]; m, sd = st.mean(v), st.pstdev(v); eq = 1.0; pk = 1.0; dd = 0.0; mois = {}
    for i in I:
        eq *= 1 + serie[i]; pk = max(pk, eq); dd = max(dd, 1 - eq / pk)
        g = time.gmtime(JOURS[i] / 1000); mois[(g.tm_year, g.tm_mon)] = mois.get((g.tm_year, g.tm_mon), 1.0) * (1 + serie[i])
    mm = {k: v - 1 for k, v in mois.items()}; pire = min(mm, key=mm.get)
    return dict(rend_an=(eq ** (365 / len(I)) - 1), sharpe=m / sd * math.sqrt(365) if sd else 0, pire_baisse=dd, pire_mois=f"{pire[0]}-{pire[1]:02d}", pire_mois_val=mm[pire],
                mois_negatifs=sum(v < 0 for v in mm.values()), mois=len(mm))
serie, ouverts = simule(SHORTS); I = list(range(len(JOURS)))
an = lambda y: [i for i in I if time.gmtime(JOURS[i] / 1000).tm_year == y]
res = dict(shorts=len(SHORTS), jours_avec_shorts=sum(1 for d in JOURS if ouverts[d]) / len(JOURS), shorts_ouverts_moy=st.mean(len(ouverts[d]) for d in JOURS),
           tout=mesures(serie, I), par_an={y: mesures(serie, an(y)) for y in range(2021, 2027)})
print(json.dumps({k: res[k] for k in ("shorts", "jours_avec_shorts", "shorts_ouverts_moy", "tout")}, indent=1), flush=True)
rng = random.Random(57); tem = []
for k in range(200):
    fake = []
    for s, e, x in SHORTS:
        pool = [a for a in anciens.get(e, []) if FINS[a] >= e] if e in anciens else []
        if pool: a = rng.choice(pool); fake.append((a, e, min(x, FINS[a])))
    tem.append(mesures(simule(fake)[0], I)["sharpe"])
    if k % 50 == 0: print("témoin", k, flush=True)
p = sum(t >= res["tout"]["sharpe"] for t in tem) / len(tem); res["temoin"] = dict(sharpe_moy=st.mean(tem), sharpe_et=st.pstdev(tem), p=p)
t = res["tout"]; ok = t["sharpe"] > 1.0 and t["pire_baisse"] < 0.30 and t["pire_mois_val"] > -0.15 and res["par_an"][2026]["rend_an"] > 0 and p < 0.05
res["verdict"] = "RISQUE MAÎTRISÉ" if ok else "RISQUE NON MAÎTRISÉ"
json.dump(res, open(os.path.join(ICI, "t57.json"), "w"), indent=1)
print(json.dumps({"temoin": res["temoin"], "verdict": res["verdict"], "par_an": {y: {k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items()} for y, m in res["par_an"].items()}}, indent=1))

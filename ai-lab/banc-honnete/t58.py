"""PREREG-58 : portefeuille de shorts tenus (règles : PREREG-58-shorts-tenus.md, commit 28b4803). Données de t57.py."""
import bisect, json, math, os, random, statistics as st, time
src = open("t57.py").read(); ns = {"__file__": os.path.abspath("t57.py")}; exec(src[:src.index("def simule")], ns)
C, FT, FR, DEB, FINS, SHORTS, JOURS, J, TK, anciens = (ns[k] for k in ("C", "FT", "FR", "DEB", "FINS", "SHORTS", "JOURS", "J", "TK", "anciens"))
A = 1 / 30; IDX = {d: i for i, d in enumerate(JOURS)}; NJ = len(JOURS)
def fin(s, d): t = FT[s]; return sum(FR[s][bisect.bisect_left(t, d):bisect.bisect_left(t, d + J)])
def short_pnl(s, e, x, pnl):
    """ajoute au tableau pnl (par jour) le P&L d'un short tenu de notionnel A ; renvoie le résultat du trade."""
    if e not in C[s]: return None
    p0 = C[s][e][0]; q = A / p0; prev = p0; cum = -A * TK; pnl[IDX[e]] -= A * TK
    for d in range(e, x + J, J):
        if d not in C[s] or d not in IDX: continue
        c = C[s][d][1]; v = -q * (c - prev) + q * c * fin(s, d)
        if cum + v <= -A:                                    # plancher : la mise est perdue
            pnl[IDX[d]] += -A - cum; return -1.0
        pnl[IDX[d]] += v; cum += v; prev = c; last = d
    fr = q * prev * TK; pnl[IDX[last]] -= fr; return (cum - fr) / A
def long_pnl(e, x, pnl):
    L = [s for s in anciens.get(e, []) if e in C[s]]
    if not L: return
    pnl[IDX[e]] -= A * TK
    for s in L:
        p0 = C[s][e][0]; q = A / len(L) / p0; prev = p0; last = None
        for d in range(e, x + J, J):
            if d not in C[s] or d not in IDX: continue
            c = C[s][d][1]; pnl[IDX[d]] += q * (c - prev) - q * c * fin(s, d); prev = c; last = d
        if last: pnl[IDX[last]] -= q * prev * TK
LONG = [0.0] * NJ
for s, e, x in SHORTS:
    if e in IDX: long_pnl(e, min(x, JOURS[-1]), LONG)
def mesures(pnl, I):
    v = [pnl[i] for i in I]; m, sd = st.mean(v), st.pstdev(v); eq = 1.0; pk = 1.0; dd = 0.0; mois = {}; debut = {}
    for i in I:
        g = time.gmtime(JOURS[i] / 1000); k = (g.tm_year, g.tm_mon); debut.setdefault(k, eq)
        eq += pnl[i]; pk = max(pk, eq); dd = max(dd, (pk - eq) / pk); mois[k] = mois.get(k, 0) + pnl[i]
    mm = {k: v / debut[k] for k, v in mois.items()}; pire = min(mm, key=mm.get)
    return dict(pnl_an=sum(v) * 365 / len(I), sharpe=m / sd * math.sqrt(365) if sd else 0, pire_baisse=dd, pire_mois=f"{pire[0]}-{pire[1]:02d}", pire_mois_val=mm[pire],
                mois_negatifs=sum(x < 0 for x in mm.values()), mois=len(mm))
SH = [0.0] * NJ; res_tr = []
for s, e, x in SHORTS:
    if e in IDX: res_tr.append(short_pnl(s, e, min(x, JOURS[-1]), SH))
TOT = [a + b for a, b in zip(SH, LONG)]; I = list(range(NJ)); an = lambda y: [i for i in I if time.gmtime(JOURS[i] / 1000).tm_year == y]
ouverts = [0] * NJ
for s, e, x in SHORTS:
    for d in range(e, min(x, JOURS[-1]) + J, J):
        if d in IDX: ouverts[IDX[d]] += 1
r_tr = [r for r in res_tr if r is not None]
res = dict(trades=len(r_tr), moy_trade=st.mean(r_tr), plancher=sum(r <= -1 for r in r_tr), levier_brut_moy=2 * A * st.mean(ouverts), levier_brut_max=2 * A * max(ouverts),
           couvert=mesures(TOT, I), sans_couverture=mesures(SH, I), par_an={y: mesures(TOT, an(y)) for y in range(2021, 2027)})
print(json.dumps({k: res[k] for k in ("trades", "moy_trade", "plancher", "levier_brut_moy", "levier_brut_max", "couvert", "sans_couverture")}, indent=1), flush=True)
rng = random.Random(58); tem = []
for k in range(200):
    sh = [0.0] * NJ
    for s, e, x in SHORTS:
        if e not in IDX: continue
        pool = [a for a in anciens.get(e, []) if e in C[a]]
        a_ = rng.choice(pool); short_pnl(a_, e, min(x, FINS[a_], JOURS[-1]), sh)
    tem.append(mesures([a + b for a, b in zip(sh, LONG)], I)["sharpe"])
    if k % 50 == 0: print("témoin", k, flush=True)
p = sum(t >= res["couvert"]["sharpe"] for t in tem) / len(tem); res["temoin"] = dict(sharpe_moy=st.mean(tem), sharpe_et=st.pstdev(tem), p=p)
c = res["couvert"]; ok = c["sharpe"] > 1 and c["pire_baisse"] < 0.30 and c["pire_mois_val"] > -0.15 and res["par_an"][2026]["pnl_an"] > 0 and p < 0.05
res["verdict"] = "RISQUE MAÎTRISÉ" if ok else "RISQUE NON MAÎTRISÉ"
json.dump(res, open("t58.json", "w"), indent=1)
print(json.dumps({"temoin": res["temoin"], "verdict": res["verdict"], "par_an": {y: {k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items()} for y, m in res["par_an"].items()}}, indent=1))

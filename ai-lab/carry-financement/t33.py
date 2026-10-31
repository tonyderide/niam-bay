"""PREREG-33 : carry du financement (règle PREREG-27) sur Hyperliquid. Voir PREREG-33-hyperliquid.md. Lancer : nice -n 10 python3 t33.py"""
import bisect, calendar, json, os, random, time
J = 86400000; DOS = "data_hl"; NB = 3; TAKER = 0.00045; MAKER = 0.00015; NT = int(os.environ.get("NT", "2000"))
K = json.load(open(f"{DOS}/klines.json")); UJ = json.load(open(f"{DOS}/univers.json")); F = json.load(open(f"{DOS}/funding.json"))
C = {s: {k[0]: (k[1], k[2]) for k in v if k[4] > 0} for s, v in K.items() if s != "NFTI"}
DATES = sorted(int(t) for t in UJ["univers"]); UNIV = {int(t): u for t, u in UJ["univers"].items()}
FT = {s: [x[0] for x in v] for s, v in F.items()}; FR = {s: [x[1] for x in v] for s, v in F.items()}
def somme(s, a, b, inc=False):
    if s not in FT: return 0.0
    f = bisect.bisect_right if inc else bisect.bisect_left
    return sum(FR[s][f(FT[s], a):f(FT[s], b)])
dernier = max(max(v) for v in C.values()) - J        # la dernière bougie (jour en cours) n'est pas close
jours = list(range(UJ["debut"], dernier + 1, J)); N = len(jours)
ELIG, W, RET = [], [], []                            # éligibles, poids de la règle, rendements (prix, financement) de tout contrat présent ce jour
for d in jours:
    u = UNIV[max(t for t in DATES if t <= d)]
    ok = [s for s in u if d in C[s] and s in FT and FT[s] and FT[s][0] < d - 7 * J]
    sig = sorted(ok, key=lambda s: somme(s, d - 7 * J, d)); w = {}
    if len(ok) >= 2 * NB:
        for s in sig[:NB]: w[s] = 1 / NB
        for s in sig[-NB:]: w[s] = -1 / NB
    ELIG.append(ok); W.append(w)
    RET.append({s: (C[s][d][1] / C[s][d][0] - 1, somme(s, d, d + J, True)) for s in set(ok) | {x for x in C if d in C[x] and x in FT}})
def evalue(Wser, i0, fee=TAKER):
    bp = bf = fr = 0.0; par = {}; serie = []; prev = {}
    for k, w in enumerate(Wser):
        i = i0 + k; jour = 0.0
        for s in set(w) | set(prev):
            c = fee * abs(w.get(s, 0) - prev.get(s, 0)); p = f = 0.0
            if s in w and s in RET[i]: p = w[s] * RET[i][s][0]; f = -w[s] * RET[i][s][1]
            bp += p; bf += f; fr += c; par[s] = par.get(s, 0) + p + f - c; jour += p + f - c
        prev = w; serie.append(jour)
    return bp, bf, fr, par, serie
def temoin(i0, i1, rnd):
    """Pièces au hasard : mêmes jours de changement, même nombre de contrats changés par côté que la règle."""
    out = []; S = L = None; pS = pL = set()
    for i in range(i0, i1):
        rS = {s for s, v in W[i].items() if v < 0}; rL = {s for s, v in W[i].items() if v > 0}
        if not W[i]: out.append({}); S = L = None; pS, pL = rS, rL; continue
        el = ELIG[i]
        if S is None:
            x = rnd.sample(el, 2 * NB); S, L = set(x[:NB]), set(x[NB:])
        else:
            for cote, kchg in ((S, len(rS - pS)), (L, len(rL - pL))):
                morts = [s for s in cote if s not in el]; vivants = sorted(s for s in cote if s in el)
                n = max(kchg, len(morts)); sortir = morts + rnd.sample(vivants, min(len(vivants), n - len(morts)))
                for s in sortir: cote.discard(s)
                libres = sorted(s for s in el if s not in S and s not in L)
                cote.update(rnd.sample(libres, min(len(libres), NB - len(cote))))
        out.append({**{s: -1 / NB for s in S}, **{s: 1 / NB for s in L}}); pS, pL = rS, rL
    return out
def dd(x):
    m = c = pire = 0.0
    for v in x: c += v; m = max(m, c); pire = min(pire, c - m)
    return pire
def pire_mois(i0, serie):
    mo = {}
    for k, v in enumerate(serie): g = time.gmtime(jours[i0 + k] / 1000); mo[(g.tm_year, g.tm_mon)] = mo.get((g.tm_year, g.tm_mon), 0) + v
    (y, m), v = min(mo.items(), key=lambda x: x[1]); return f"{y}-{m:02d} {100*v:+.1f} %", sum(v > 0 for v in mo.values()), len(mo)
def periode(nom, i0, i1, test=True, graine=33):
    bp, bf, fr, par, serie = evalue(W[i0:i1], i0); net = bp + bf - fr; n = i1 - i0
    res = {"net": net, "n": n}
    L = [f"### {nom} : {time.strftime('%F', time.gmtime(jours[i0]/1000))} → {time.strftime('%F', time.gmtime(jours[i1-1]/1000))} ({n} jours)",
         f"- Prix {100*bp:+.1f} % · financement {100*bf:+.1f} % · frais {100*fr:.1f} % · **net {100*net:+.1f} %** (en % de 1 $ par côté)",
         f"- Annualisé {100*net*365/n:+.1f} %/an par côté, soit {50*net*365/n:+.1f} %/an du capital (long + short à levier 1)",
         f"- Pire mois {pire_mois(i0, serie)[0]} ({pire_mois(i0, serie)[1]}/{pire_mois(i0, serie)[2]} mois positifs) · pire baisse {100*dd(serie):.1f} %",
         f"- Contrats gagnants {sum(v > 0 for v in par.values())}/{len(par)} · variante maker 0,015 % : net {100*(lambda a: a[0]+a[1]-a[2])(evalue(W[i0:i1], i0, MAKER)):+.1f} %"]
    if test:
        rnd = random.Random(graine); nets = []
        for _ in range(NT): a, b, c, _, _ = evalue(temoin(i0, i1, rnd), i0); nets.append(a + b - c)
        p = (sum(x >= net for x in nets) + 1) / (NT + 1); nets.sort()
        rnd2 = random.Random(graine); plus = 0
        for _ in range(NT):
            k = rnd2.randint(30, n - 30); Wp = W[i0:i1]; plus += (lambda a: a[0]+a[1]-a[2])(evalue(Wp[k:] + Wp[:k], i0)) >= net
        res["p"] = p
        L.append(f"- Témoin pièces au hasard ({NT} tirages) : médiane {100*nets[NT//2]:+.1f} %, 95e centile {100*nets[int(.95*NT)]:+.1f} % → **p = {p:.4f}** · (info) décalages circulaires : p = {(plus+1)/(NT+1):.4f}")
    res["L"] = L; res["par"] = par; res["fr"] = fr; res["brut"] = bp + bf
    return res
h = N // 2; ij = jours.index(calendar.timegm((2026, 1, 1, 0, 0, 0)) * 1000)
R = periode("Réglage (1re moitié)", 0, h); M = periode("Entre-deux (information)", h, ij, test=False); Jg = periode("JUGEMENT UNIQUE", ij, N)
c1, c2, c3 = R["net"] > 0, Jg["net"] > 0, Jg["p"] < 0.05
verdict = "GAGNE" if c1 and c2 and c3 else ("NON DÉMONTRÉ" if c2 else "PERD")
nj = Jg["n"]; g = lambda cap: f"{cap*Jg['net']/2:+.2f} $ sur {nj} jours (≈ {cap*Jg['net']/2*365/nj:+.2f} $/an)"
T = [f"## Résultat ({time.strftime('%d/%m/%Y %H:%M')}, t33.py)", "",
     f"Historique : {time.strftime('%F', time.gmtime(jours[0]/1000))} → {time.strftime('%F', time.gmtime(jours[-1]/1000))}, {N} jours ; {len({s for u in UNIV.values() for s in u})} contrats dans les univers. Univers : " +
     " | ".join(f"{time.strftime('%F', time.gmtime(t/1000))}: {', '.join(UNIV[t])}" for t in DATES), "", *R["L"], "", *M["L"], "", *Jg["L"], "",
     f"1. net réglage > 0 : {'✅' if c1 else '❌'}", f"2. net jugement > 0 : {'✅' if c2 else '❌'}", f"3. p < 0,05 en jugement : {'✅' if c3 else '❌'}", "",
     f"**VERDICT (pré-enregistré) : {verdict}**", "",
     f"Jugement : bruts (prix + financement) {100*Jg['brut']:+.1f} % contre frais {100*Jg['fr']:.1f} %. Sur 100 $ de capital : {g(100)} ; sur 1 000 $ : {g(1000)} ; sur 6 $ : {g(6)} (mais impossible : ordre minimum 10 $).",
     "Contributions en jugement : " + ", ".join(f"{s} {100*v:+.1f} %" for s, v in sorted(Jg["par"].items(), key=lambda x: -x[1]))]
open("RESULTAT-33.md", "w").write("\n".join(T) + "\n"); print("\n".join(T))

"""PREREG-27 : carry du financement sur un univers choisi chaque 1er janvier (top 30 volume, morts compris)."""
import bisect, calendar, json, os, random, time, urllib.request, sys
J = 86400000; FEE = 0.0005; DOS = "data-univers"; NB = int(os.environ.get("NB", "3"))
INDICES = {"BTCDOMUSDT", "DEFIUSDT", "BLUEBIRDUSDT", "FOOTBALLUSDT"}
K = json.load(open(f"{DOS}/klines.json"))
C = {s: {k[0]: (k[1], k[2], k[3]) for k in v} for s, v in K.items() if v and s not in INDICES}
ANS = [2021, 2022, 2023, 2024, 2025, 2026]
UNIV = {}
for y in ANS:
    t = calendar.timegm((y, 1, 1, 0, 0, 0)) * 1000
    cand = {s: sum(c[2] for d, c in v.items() if t - 30 * J <= d < t) for s, v in C.items() if sum(1 for d in v if d < t) >= 60}
    UNIV[y] = sorted(cand, key=lambda s: -cand[s])[:30]
tous = sorted({s for u in UNIV.values() for s in u})
get = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "nb"}), timeout=60))
FF = f"{DOS}/funding.json"; F = json.load(open(FF)) if os.path.exists(FF) else {}
for s in tous:
    if s in F: continue
    f, t = [], 1609459200000 - 8 * J
    while True:
        r = get(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={s}&startTime={t}&limit=1000")
        if not r: break
        f += [[x["fundingTime"], float(x["fundingRate"])] for x in r]; t = r[-1]["fundingTime"] + 1; time.sleep(0.1)
        if len(r) < 1000: break
    F[s] = f; json.dump(F, open(FF, "w"))
FT = {s: [x[0] for x in F[s]] for s in tous}; FR = {s: [x[1] for x in F[s]] for s in tous}
def somme(s, a, b, inc=False):
    f = bisect.bisect_right if inc else bisect.bisect_left
    return sum(FR[s][f(FT[s], a):f(FT[s], b)])
jours = list(range(1609459200000, 1793059200000, J))
W, RP, RF = [], [], []
for d in jours:
    u = UNIV[time.gmtime(d / 1000).tm_year]
    ok = [s for s in u if d in C[s] and FT[s] and FT[s][0] < d - 7 * J]
    sig = sorted(ok, key=lambda s: somme(s, d - 7 * J, d)); w = {}
    if len(ok) >= 2 * NB:
        for s in sig[:NB]: w[s] = 1 / NB
        for s in sig[-NB:]: w[s] = -1 / NB
    W.append(w)
    RP.append({s: C[s][d][1] / C[s][d][0] - 1 for s in w}); RF.append({s: somme(s, d, d + J, True) for s in w})
N = len(jours)
def evalue(Wser, exclus=()):
    bp = bf = fr = 0.0; par = {}; serie = []; prev = {}
    for i in range(N):
        w = {s: v for s, v in Wser[i].items() if s not in exclus}; jour = 0.0
        for s in set(w) | set(prev):
            c = FEE * abs(w.get(s, 0) - prev.get(s, 0)); p = f = 0.0
            if s in w and s in RP[i]: p = w[s] * RP[i][s]; f = -w[s] * RF[i][s]
            elif s in w:  # poids décalé : rendement du jour pour ce contrat
                d = jours[i]
                if d in C.get(s, {}): p = w[s] * (C[s][d][1] / C[s][d][0] - 1); f = -w[s] * somme(s, d, d + J, True)
            bp += p; bf += f; fr += c; par[s] = par.get(s, 0) + p + f - c; jour += p + f - c
        prev = w; serie.append(jour)
    return bp, bf, fr, par, serie
bp, bf, fr, par, serie = evalue(W); net = bp + bf - fr
rnd = random.Random(27); plus = 0; NT = int(os.environ.get("NT", "2000"))
for _ in range(NT):
    k = rnd.randint(30, N - 30); a, b, c, _, _ = evalue(W[k:] + W[:k]); plus += (a + b - c) >= net
p = (plus + 1) / (NT + 1); g = sum(v > 0 for v in par.values())
morts = [s for s in tous if max(C[s]) < 1792800000000]
c1, c2, c3, c4 = p < 0.05, net > 0, g >= 3, bp + bf > fr
L = [f"# Résultat PREREG-27 ({time.strftime('%d/%m/%Y %H:%M')}) — {NB} contre {NB}\n",
     f"{N} jours ; {len(tous)} contrats différents dans les univers annuels, dont {len(morts)} morts avant la fin : {', '.join(morts)}\n",
     f"- Prix {100*bp:+.1f} % · financement {100*bf:+.1f} % · frais {100*fr:.1f} %", f"- **Net {100*net:+.1f} %** · p = {p:.4f}",
     f"1. p < 0,05 : {'✅' if c1 else '❌'}", f"2. net > 0 : {'✅' if c2 else '❌'}", f"3. ≥ 3 contrats gagnants : {'✅' if c3 else '❌'} ({g}/{len(par)})",
     f"4. bruts > frais : {'✅' if c4 else '❌'}", f"\n**VERDICT : {'DÉMONTRÉ' if all((c1,c2,c3,c4)) else 'NON DÉMONTRÉ'}**\n", "## Pour information"]
an = {}
for i, d in enumerate(jours): an.setdefault(time.gmtime(d / 1000).tm_year, []).append(serie[i])
L.append("Par année : " + " · ".join(f"{y} {100*sum(v):+.1f} %" for y, v in sorted(an.items())))
a, b, c, _, _ = evalue(W, set(morts)); L.append(f"Sans les contrats morts : net {100*(a+b-c):+.1f} %")
L.append("Contributions des morts : " + ", ".join(f"{s} {100*par.get(s,0):+.1f} %" for s in morts if s in par))
L.append("Univers : " + " | ".join(f"{y}: {', '.join(x[:-4] for x in UNIV[y])}" for y in ANS))
out = os.environ.get("SORTIE", "RESULTAT-27.md"); open(out, "w").write("\n".join(L) + "\n"); print("\n".join(L))

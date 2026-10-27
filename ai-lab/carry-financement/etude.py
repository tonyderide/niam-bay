"""PREREG-25 : carry du financement en coupe (short 3 plus hauts, long 3 plus bas sur 7 jours), voir PREREG.md."""
import json, random, bisect, time
H, J = 3600000, 86400000
SYM = ["BTCUSDT","DOTUSDT","SOLUSDT","LINKUSDT","ADAUSDT","ETHUSDT","XRPUSDT","LTCUSDT","BNBUSDT","DOGEUSDT","AVAXUSDT"]
FEE = 0.0005
D = {s: json.load(open(f"../regime-short/data/{s}.json")) for s in SYM}
prix = {s: {t + H: c for t, c in D[s]["k"]} for s in SYM}          # prix à l'instant t+H (clôture de la bougie ouverte à t)
fts = {s: [x[0] for x in D[s]["f"]] for s in SYM}; frs = {s: [x[1] for x in D[s]["f"]] for s in SYM}
def somme_fin(s, a, b, inclut_b):  # paiements dans [a, b) ou (a, b]
    T = fts[s]
    i = bisect.bisect_left(T, a) if not inclut_b else bisect.bisect_right(T, a)
    j = bisect.bisect_left(T, b) if not inclut_b else bisect.bisect_right(T, b)
    return sum(frs[s][i:j])
debut = 1602115200000; fin = 1793059200000  # 2020-10-08 → 2026-10-25 00:00 UTC
jours = list(range(debut, fin - J + 1, J))
W, RP, RF = [], [], []  # poids, rendement prix, financement par crypto et par jour
for d in jours:
    ok = [s for s in SYM if d in prix[s] and d + J in prix[s]]
    sig = sorted(ok, key=lambda s: somme_fin(s, d - 7 * J, d, False))
    w = {s: 0.0 for s in SYM}
    if len(ok) >= 6:
        for s in sig[:3]: w[s] = 1 / 3
        for s in sig[-3:]: w[s] = -1 / 3
    W.append(w)
    RP.append({s: (prix[s][d + J] / prix[s][d] - 1) if s in ok else 0.0 for s in SYM})
    RF.append({s: somme_fin(s, d, d + J, True) for s in SYM})
N = len(jours)

def evalue(Wser):
    brut_p = brut_f = frais = 0.0; par = {s: 0.0 for s in SYM}; serie = []; prev = {s: 0.0 for s in SYM}
    for i in range(N):
        w = Wser[i]; jour = 0.0
        for s in SYM:
            c = FEE * abs(w[s] - prev[s]); p = w[s] * RP[i][s]; f = -w[s] * RF[i][s]
            brut_p += p; brut_f += f; frais += c; par[s] += p + f - c; jour += p + f - c
        prev = w; serie.append(jour)
    c = sum(FEE * abs(prev[s]) for s in SYM); frais += c; serie[-1] -= c
    for s in SYM: par[s] -= FEE * abs(prev[s])
    return brut_p, brut_f, frais, par, serie

def dd(x):
    m = c = pire = 0.0
    for v in x: c += v; m = max(m, c); pire = min(pire, c - m)
    return pire

bp, bf, fr, par, serie = evalue(W); net = bp + bf - fr
rnd = random.Random(25); plus = 0; NT = 2000
for _ in range(NT):
    k = rnd.randint(30, N - 30); a, b, c, _, _ = evalue(W[k:] + W[:k]); plus += (a + b - c) >= net
p = (plus + 1) / (NT + 1)
gagn = sum(v > 0 for v in par.values())
c1, c2, c3, c4 = p < 0.05, net > 0, gagn >= 3, (bp + bf) > fr
L = [f"# Résultat PREREG-25 ({time.strftime('%d/%m/%Y %H:%M')})\n", f"{N} jours, 1 $ long + 1 $ short, sans capitalisation.\n",
     f"- Prix : {100*bp:+.1f} %", f"- Financement : {100*bf:+.1f} %", f"- Frais : {100*fr:.1f} %",
     f"- **Net : {100*net:+.1f} %** · pire repli {100*dd(serie):.1f} %", f"- Test des décalages : p = {p:.4f}\n",
     "| Crypto | contribution nette |", "|---|---|", *[f"| {s[:-4]} | {100*v:+.1f} % |" for s, v in par.items()], "",
     f"1. p < 0,05 : {'✅' if c1 else '❌'}", f"2. net > 0 : {'✅' if c2 else '❌'}", f"3. ≥ 3 cryptos gagnantes : {'✅' if c3 else '❌'} ({gagn}/11)",
     f"4. bruts > frais : {'✅' if c4 else '❌'} ({100*(bp+bf):+.1f} % contre {100*fr:.1f} %)",
     f"\n**VERDICT : {'DÉMONTRÉ' if all((c1,c2,c3,c4)) else 'NON DÉMONTRÉ'}**\n", "## Pour information"]
an = {}
for i, d in enumerate(jours): an.setdefault(time.gmtime(d / 1000).tm_year, []).append(serie[i])
L.append("Par année : " + " · ".join(f"{y} {100*sum(v):+.1f} %" for y, v in sorted(an.items())))
h = N // 2; L.append(f"Moitiés : {100*sum(serie[:h]):+.1f} % · {100*sum(serie[h:]):+.1f} %")
L.append(f"Financement seul (sans risque de prix, mêmes frais) : {100*(bf-fr):+.1f} %")
open("RESULTAT.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))

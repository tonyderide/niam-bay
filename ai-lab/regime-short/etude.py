"""PREREG-24 : short altcoins à poids égal quand BTC (1 h) clôture sous son EMA200 1 h. Voir PREREG.md."""
import json, random
H = 3600000
ALTS = ["DOTUSDT","SOLUSDT","LINKUSDT","ADAUSDT","ETHUSDT","XRPUSDT","LTCUSDT","BNBUSDT","DOGEUSDT","AVAXUSDT"]
FEE = 0.0005
START = 1601510400000
D = {s: json.load(open(f"data/{s}.json")) for s in ["BTCUSDT"] + ALTS}
btc = dict(D["BTCUSDT"]["k"]); T = sorted(btc)
ema, sig = None, {}
for i, t in enumerate(T):  # signal à la clôture de la bougie qui commence à t
    c = btc[t]; ema = c if ema is None else ema + 2 / 201 * (c - ema)
    if i >= 200: sig[t] = 1 if c < ema else 0
# heures de position : l'heure qui commence à t+H, décidée à la clôture de t
heures = [t for t in T if t >= START and t + H in btc and t in sig]
close = {s: dict(D[s]["k"]) for s in ALTS}
fund = {s: {ft - H: r for ft, r in D[s]["f"]} for s in ALTS}  # financement versé à ft -> heure qui finit à ft
# pour chaque heure h (commençant à t+H) : rendement de l'alt sur [t+H, t+2H] = close[t+H]/close[t]-1
R = {s: [] for s in ALTS}; F = {s: [] for s in ALTS}
for t in heures:
    for s in ALTS:
        a, b = close[s].get(t), close[s].get(t + H)
        R[s].append(None if a is None or b is None else b / a - 1)
        F[s].append(fund[s].get(t + H, 0.0))
S0 = [sig[t] for t in heures]
N = len(heures)

def evalue(S, alts=ALTS):
    """par dollar engagé : brut (prix), frais, financement ; portefeuille à poids égal ou un seul alt"""
    brut = frais = fin = 0.0; prev = 0; serie = []
    for i in range(N):
        pos = S[i]
        if pos != prev: frais += FEE; cout = FEE
        else: cout = 0.0
        prev = pos
        rs = [(-R[s][i], F[s][i]) for s in alts if R[s][i] is not None]
        g = f = 0.0
        if pos and rs:
            g = sum(x for x, _ in rs) / len(rs); f = sum(y for _, y in rs) / len(rs)
        brut += g; fin += f; serie.append(g + f - cout)
    return brut, frais, fin, serie

def dd(serie):
    m = c = 0.0; pire = 0.0
    for x in serie: c += x; m = max(m, c); pire = min(pire, c - m)
    return pire

b, fr, fi, serie = evalue(S0); net = b - fr + fi
rnd = random.Random(24); plus = 0; NT = 2000
for _ in range(NT):
    k = rnd.randint(720, N - 720); Sk = S0[k:] + S0[:k]
    bb, ff, ii, _ = evalue(Sk); plus += (bb - ff + ii) >= net
p = (plus + 1) / (NT + 1)
gagnants = []
lignes = []
for s in ALTS:
    bs, fs, ins, _ = evalue(S0, [s]); ns = bs - fs + ins; gagnants += [ns > 0]
    lignes.append(f"| {s[:-4]} | {100*bs:+.1f} % | {100*fs:.1f} % | {100*ins:+.1f} % | **{100*ns:+.1f} %** |")
c1, c2, c3, c4 = p < 0.05, net > 0, sum(gagnants) >= 3, b > fr
out = [f"# Résultat PREREG-24\n",
       f"Heures testées : {N} ({sum(S0)} en position, soit {100*sum(S0)/N:.0f} %), entrées+sorties : {round(fr/FEE)}.\n",
       f"## Portefeuille (10 altcoins, poids égal, pour 1 $ engagé, sans capitalisation)",
       f"- Gains bruts (prix) : {100*b:+.1f} %", f"- Frais payés : {100*fr:.1f} %", f"- Financement : {100*fi:+.1f} %",
       f"- **Net : {100*net:+.1f} %** · pire repli : {100*dd(serie):.1f} %",
       f"- Test des décalages : p = {p:.4f} ({plus} décalages sur {NT} font au moins aussi bien)\n",
       "## Par altcoin", "| Crypto | Brut | Frais | Financement | Net |", "|---|---|---|---|---|", *lignes, "",
       "## Les 4 conditions",
       f"1. p < 0,05 : {'✅' if c1 else '❌'} (p = {p:.4f})", f"2. net > 0 : {'✅' if c2 else '❌'} ({100*net:+.1f} %)",
       f"3. ≥ 3 altcoins gagnants : {'✅' if c3 else '❌'} ({sum(gagnants)}/10)", f"4. gains bruts > frais : {'✅' if c4 else '❌'} ({100*b:+.1f} % contre {100*fr:.1f} %)",
       f"\n**VERDICT : {'DÉMONTRÉ' if all((c1,c2,c3,c4)) else 'NON DÉMONTRÉ'}**\n"]
# pour information
ans = {}
for i, t in enumerate(heures): ans.setdefault(time_y := __import__('time').gmtime(t/1000).tm_year, []).append(serie[i])
out.append("## Pour information (ne change pas le verdict)")
out.append("Par année (net) : " + " · ".join(f"{y} {100*sum(v):+.1f} %" for y, v in sorted(ans.items())))
h = N // 2; out.append(f"Moitiés : 1re {100*sum(serie[:h]):+.1f} % · 2e {100*sum(serie[h:]):+.1f} %")
b1, f1, i1, s1 = evalue([1]*N); out.append(f"Toujours short sans filtre : net {100*(b1-f1+i1):+.1f} % (brut {100*b1:+.1f}, financement {100*i1:+.1f}), pire repli {100*dd(s1):.1f} %")
# variante journalière exploratoire
import collections
jour = collections.OrderedDict()
for t in T: jour[t // 86400000] = btc[t]  # dernière clôture du jour
e = None; sj = {}
for i, (d, c) in enumerate(jour.items()):
    e = c if e is None else e + 2/201*(c - e)
    if i >= 200: sj[d + 1] = 1 if c < e else 0  # appliqué au jour suivant
Sj = [sj.get((t + H) // 86400000, 0) for t in heures]
bj, fj, ij, sjs = evalue(Sj); out.append(f"Variante journalière (EMA200 jours) : net {100*(bj-fj+ij):+.1f} % (brut {100*bj:+.1f}, frais {100*fj:.1f}, financement {100*ij:+.1f}), en position {100*sum(Sj)/N:.0f} % du temps, pire repli {100*dd(sjs):.1f} %")
open("RESULTAT.md", "w").write("\n".join(out) + "\n"); print("\n".join(out))

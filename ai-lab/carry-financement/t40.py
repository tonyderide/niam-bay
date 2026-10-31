"""PREREG-40 : écart de financement Binance / Hyperliquid (règles : PREREG-40-ecart-plateformes.md, commit 243db80)."""
import bisect, calendar, json, random, time
J = 86_400_000; FB, FH, SEUIL = 0.0005, 0.00045, 0.10
F = json.load(open("data-univers/funding.json")); H = json.load(open("data_hl/funding.json"))
KB = json.load(open("data-univers/klines.json")); KH = json.load(open("data_hl/klines.json"))
M = {}
for c in H:
    b = c[1:].upper() if c.startswith("k") else c
    for cand in (b + "USDT", "1000" + b + "USDT"):
        if cand in F and cand in KB: M[c] = cand
CB = {c: {k[0]: (k[1], k[2]) for k in KB[M[c]]} for c in M}
CH = {c: {k[0]: (k[1], k[2]) for k in KH.get(c, []) if k[4] > 0} for c in M}
T = {("B", c): [x[0] for x in F[M[c]]] for c in M} | {("H", c): [x[0] for x in H[c]] for c in M}
R = {("B", c): [x[1] for x in F[M[c]]] for c in M} | {("H", c): [x[1] for x in H[c]] for c in M}
def somme(k, a, b): t = T[k]; return sum(R[k][bisect.bisect_left(t, a):bisect.bisect_left(t, b)])
D0 = calendar.timegm((2023, 10, 1, 0, 0, 0)) * 1000; D1 = calendar.timegm((2026, 10, 27, 0, 0, 0)) * 1000
J26 = calendar.timegm((2026, 1, 1, 0, 0, 0)) * 1000
jours = list(range(D0, D1, J)); POS, GAIN = [], []    # POS[i] = {c: sens}, GAIN[i] = {c: (financement, prix)} pour sens = +1 (short HL, long B)
for d in jours:
    pos, g = {}, {}
    for c in M:
        if d not in CB[c] or d not in CH[c]: continue
        if not T[("B", c)] or not T[("H", c)] or T[("B", c)][0] > d - 7 * J or T[("H", c)][0] > d - 7 * J: continue
        e = (somme(("H", c), d - 7 * J, d) - somme(("B", c), d - 7 * J, d)) * 365 / 7
        fin = somme(("H", c), d, d + J) - somme(("B", c), d, d + J)          # sens +1 : short HL reçoit HL, long B paie B
        prix = (CB[c][d][1] / CB[c][d][0] - 1) - (CH[c][d][1] / CH[c][d][0] - 1)
        g[c] = (fin, prix)
        if abs(e) > SEUIL: pos[c] = 1 if e > 0 else -1
    POS.append(pos); GAIN.append(g)
N = len(jours)
def evalue(P):
    serie, parts, par = [], [0.0, 0.0, 0.0], {}; prev = {}
    for i in range(N):
        p = P[i]; tot = 0.0; n = len(p)
        for c in set(p) | set(prev):
            a, b = prev.get(c, 0), p.get(c, 0); fr = (FB + FH) * abs(b - a)
            f = pr = 0.0
            if b: f, pr = b * GAIN[i][c][0], b * GAIN[i][c][1]
            parts[0] += f / max(n, 1); parts[1] += pr / max(n, 1); parts[2] += fr / max(n, 1)
            par[c] = par.get(c, 0) + (f + pr - fr) / max(n, 1); tot += f + pr - fr
        serie.append(tot / n if n else (tot if prev else 0.0)); prev = p
    return serie, parts, par
serie, parts, par = evalue(POS)
I1 = [i for i in range(N) if jours[i] < J26]; I2 = [i for i in range(N) if jours[i] >= J26]
def an(I, s): return sum(s[i] for i in I) * 365 / len(I)
def mois(I, s):
    m = {}
    for i in I: g = time.gmtime(jours[i] / 1000); m[(g.tm_year, g.tm_mon)] = m.get((g.tm_year, g.tm_mon), 0) + s[i]
    k = min(m, key=m.get); return f"{k[0]}-{k[1]:02d} {100*m[k]:+.2f} %"
rng = random.Random(40); tem = []
for _ in range(1000):
    Pt = []
    for i in range(N): Pt.append({c: rng.choice((1, -1)) for c in POS[i]})
    s, _, _ = evalue(Pt); tem.append(an(I2, s))
a2 = an(I2, serie); p = sum(t >= a2 for t in tem) / len(tem)
_, p1, _ = evalue([POS[i] if i in set(I1) else {} for i in range(N)]); _, p2, _ = evalue([POS[i] if i >= I2[0] else {} for i in range(N)])
res = dict(pieces=len(M), jours=N, hist=dict(net_an=an(I1, serie), jours_pos=sum(1 for i in I1 if POS[i]) / len(I1), pos_moy=sum(len(POS[i]) for i in I1) / len(I1),
           fin=p1[0], prix=p1[1], frais=p1[2], pire_mois=mois(I1, serie)),
           j2026=dict(net_an=a2, jours_pos=sum(1 for i in I2 if POS[i]) / len(I2), pos_moy=sum(len(POS[i]) for i in I2) / len(I2),
           fin=p2[0], prix=p2[1], frais=p2[2], pire_mois=mois(I2, serie)),
           par_an={y: an([i for i in range(N) if time.gmtime(jours[i] / 1000).tm_year == y], serie) for y in (2023, 2024, 2025, 2026)},
           temoin_2026=dict(moy=sum(tem) / len(tem), p=p), meilleures=sorted(par.items(), key=lambda x: -x[1])[:5], pires=sorted(par.items(), key=lambda x: x[1])[:5])
v = "GAGNE" if res["hist"]["net_an"] > 0 and a2 > 0.04 and p < 0.05 else "NON DÉMONTRÉ" if a2 > 0 else "PERD"
res["verdict"] = v; json.dump(res, open("t40.json", "w"), indent=1); print(json.dumps(res, indent=1))

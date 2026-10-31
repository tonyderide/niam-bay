"""PREREG-38 : vol gérée sur le carry PREREG-27 (règles : PREREG-38-vol-geree-carry.md, commit fe5a02a).
Reprend etude_univers.py tel quel jusqu'à la fonction evalue (mêmes données, même règle, mêmes frais)."""
import json, math, random, statistics as st, time
src = open("etude_univers.py").read(); ns = {}
exec(src[:src.index("bp, bf, fr, par, serie = evalue(W)")], ns)
W, evalue, jours, N = ns["W"], ns["evalue"], ns["jours"], ns["N"]
_, _, fr0, _, brut = evalue(W)
m = [1.0] * N; sig = [None] * N
for i in range(30, N):
    sig[i] = st.pstdev(brut[i - 30:i])
for i in range(31, N):
    passe = [s for s in sig[30:i] if s]
    if sig[i] and passe: m[i] = min(2.0, st.median(passe) / sig[i])
def geres(mm): return [{s: v * mm[i] for s, v in W[i].items()} for i in range(N)]
_, _, fr1, _, gere = evalue(geres(m))
an = lambda i: time.gmtime(jours[i] / 1000).tm_year
I_ref = [i for i in range(N) if an(i) <= 2025]; I26 = [i for i in range(N) if an(i) == 2026]
def sh(x, I): v = [x[i] for i in I]; return st.mean(v) / st.pstdev(v) * math.sqrt(365) if st.pstdev(v) else 0
def dd(x, I):
    c = pk = b = 0.0
    for i in I: c += x[i]; pk = max(pk, c); b = max(b, pk - c)
    return b
def mois(x, I):
    d = {}
    for i in I: g = time.gmtime(jours[i] / 1000); d[(g.tm_year, g.tm_mon)] = d.get((g.tm_year, g.tm_mon), 0) + x[i]
    return min(d.values())
R = {}
for nom, I in (("2021-25", I_ref), ("2026", I26)):
    R[nom] = dict(net_brut=sum(brut[i] for i in I), net_gere=sum(gere[i] for i in I), sharpe_brut=sh(brut, I), sharpe_gere=sh(gere, I),
                  dd_brut=dd(brut, I), dd_gere=dd(gere, I), pire_mois_brut=mois(brut, I), pire_mois_gere=mois(gere, I), m_moy=st.mean(m[i] for i in I))
R["par_an"] = {y: dict(brut=sum(brut[i] for i in range(N) if an(i) == y), gere=sum(gere[i] for i in range(N) if an(i) == y),
                       sh_b=sh(brut, [i for i in range(N) if an(i) == y]), sh_g=sh(gere, [i for i in range(N) if an(i) == y])) for y in range(2021, 2027)}
R["frais_total_brut"], R["frais_total_gere"] = fr0, fr1
rng = random.Random(38); tem = []
for k in range(1000):
    mm = m[:]; rng.shuffle(mm); _, _, _, _, x = evalue(geres(mm)); tem.append(sh(x, I26))
    if k % 100 == 0: print("témoin", k, flush=True)
s26 = R["2026"]["sharpe_gere"]; p = sum(t >= s26 for t in tem) / len(tem)
R["temoin_sharpe_2026"] = dict(moy=st.mean(tem), et=st.pstdev(tem), p=p)
a, b = R["2021-25"], R["2026"]
v = ("GAGNE" if a["sharpe_gere"] > a["sharpe_brut"] and b["sharpe_gere"] > b["sharpe_brut"] and b["net_gere"] > 0 and p < 0.05
     else "NON DÉMONTRÉ" if b["sharpe_gere"] > b["sharpe_brut"] and b["net_gere"] > 0 else "PERD")
R["verdict"] = v; json.dump(R, open("t38.json", "w"), indent=1); print(json.dumps(R, indent=1))

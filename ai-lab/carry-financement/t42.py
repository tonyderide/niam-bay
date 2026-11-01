"""PREREG-42 : carry PREREG-27 à rotation lente (règles : PREREG-42-carry-rotation-lente.md, commit 0d92646)."""
import json, math, random, statistics as st, time
src = open("etude_univers.py").read(); ns = {}
exec(src[:src.index("bp, bf, fr, par, serie = evalue(W)")], ns)
W, evalue, jours, N, UNIV, C, FT, somme, J, NB = (ns[k] for k in ("W", "evalue", "jours", "N", "UNIV", "C", "FT", "somme", "J", "NB"))
W2 = []; tenus = {1: [], -1: []}
for d in jours:
    u = UNIV[time.gmtime(d / 1000).tm_year]
    ok = [s for s in u if d in C[s] and FT[s] and FT[s][0] < d - 7 * J]
    for sg in (1, -1): tenus[sg] = [s for s in tenus[sg] if s in ok]        # retrait / sortie d'univers : sort le jour même
    if time.gmtime(d / 1000).tm_wday == 0 and len(ok) >= 2 * NB:
        sig = sorted(ok, key=lambda s: somme(s, d - 7 * J, d))
        bas, haut = sig[:2 * NB], sig[-2 * NB:]
        tenus[1] = [s for s in tenus[1] if s in bas]; tenus[-1] = [s for s in tenus[-1] if s in haut]
        for s in sig:                       # longs : plus bas financement d'abord
            if len(tenus[1]) >= NB: break
            if s not in tenus[1] and s not in tenus[-1]: tenus[1].append(s)
        for s in reversed(sig):
            if len(tenus[-1]) >= NB: break
            if s not in tenus[-1] and s not in tenus[1]: tenus[-1].append(s)
    W2.append({**{s: 1 / NB for s in tenus[1]}, **{s: -1 / NB for s in tenus[-1]}})
an = lambda i: time.gmtime(jours[i] / 1000).tm_year
def bilan(Wx):
    bp, bf, fr, par, serie = evalue(Wx)
    rot = sum(sum(abs(Wx[i].get(s, 0) - (Wx[i - 1].get(s, 0) if i else 0)) for s in set(Wx[i]) | set(Wx[i - 1] if i else {})) for i in range(N))
    I1 = [i for i in range(N) if an(i) <= 2025]; I2 = [i for i in range(N) if an(i) == 2026]
    sh = lambda I: st.mean(serie[i] for i in I) / st.pstdev([serie[i] for i in I]) * math.sqrt(365)
    return dict(prix=bp, fin=bf, frais=fr, net=bp + bf - fr, rotation=rot, net_2125=sum(serie[i] for i in I1), net_2026=sum(serie[i] for i in I2),
                sharpe_2125=sh(I1), sharpe_2026=sh(I2), par_an={y: sum(serie[i] for i in range(N) if an(i) == y) for y in range(2021, 2027)},
                gagnants=sum(v > 0 for v in par.values()), contrats=len(par)), bp + bf - fr
base, _ = bilan(W); var, net = bilan(W2)
print("base", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in base.items() if k != "par_an"}, flush=True)
print("variante", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in var.items() if k != "par_an"}, flush=True)
ns["FEE"] = 0.0002; maker, _ = bilan(W2); ns["FEE"] = 0.0005
rnd = random.Random(42); plus = 0
for k_ in range(1000):
    k = rnd.randint(30, N - 30); a, b, c, _, _ = evalue(W2[k:] + W2[:k]); plus += (a + b - c) >= net
    if k_ % 200 == 0: print("décalage", k_, flush=True)
p = (plus + 1) / 1001
c4 = [p < 0.05, net > 0, var["gagnants"] >= 3, var["prix"] + var["fin"] > var["frais"]]
amel = var["net_2125"] > base["net_2125"] and var["net_2026"] > base["net_2026"]
v = "PERD" if var["net_2026"] <= 0 or not c4[3] else "GAGNE" if all(c4) and amel else "NON DÉMONTRÉ"
res = dict(base=base, variante=var, maker_info=maker, p=p, conditions=c4, amelioration=amel, verdict=v)
json.dump(res, open("t42.json", "w"), indent=1); print(json.dumps(dict(p=p, conditions=c4, amelioration=amel, verdict=v, maker_net=maker["net"], maker_2026=maker["net_2026"],
      par_an_base=base["par_an"], par_an_var=var["par_an"]), indent=1))

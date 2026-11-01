"""PREREG-43 : levier de la foule (règles : PREREG-43-levier-foule.md, commit e475b88)."""
import json, random, time
src = open("etude_univers.py").read(); ns = {}
exec(src[:src.index("W, RP, RF = [], [], []")], ns)
jours, UNIV, C, FT, somme, J, FEE = (ns[k] for k in ("jours", "UNIV", "C", "FT", "somme", "J", "FEE"))
A, POIDS, RB, FB = [], [], [], []
for d in jours:
    u = UNIV[time.gmtime(d / 1000).tm_year]
    ok = [s for s in u if d in C[s] and FT[s] and FT[s][0] < d - 7 * J]
    A.append(sum(somme(s, d - 7 * J, d) for s in ok) / len(ok) if ok else None)
    POIDS.append({s: 1 / len(ok) for s in ok})
    RB.append({s: C[s][d][1] / C[s][d][0] - 1 for s in ok}); FB.append({s: somme(s, d, d + J, True) for s in ok})
N = len(jours); SIG = [False] * N
for i in range(180, N):
    passe = sorted(a for a in A[:i] if a is not None)
    if A[i] is not None and passe: SIG[i] = A[i] > passe[int(0.9 * (len(passe) - 1))]
def evalue(sig, I):
    prev = {}; out = []; parts = [0.0, 0.0, 0.0]
    for i in I:
        w = {s: -v for s, v in POIDS[i].items()} if sig[i] else {}
        fr = FEE * sum(abs(w.get(s, 0) - prev.get(s, 0)) for s in set(w) | set(prev))
        p = sum(v * RB[i][s] for s, v in w.items()); f = sum(-v * FB[i][s] for s, v in w.items())
        parts[0] += p; parts[1] += f; parts[2] += fr; out.append(p + f - fr); prev = w
    return out, parts
an = lambda i: time.gmtime(jours[i] / 1000).tm_year
I1 = [i for i in range(N) if an(i) <= 2025]; I2 = [i for i in range(N) if an(i) == 2026]
res = {}
for nom, I in (("2021-25", I1), ("2026", I2)):
    s, (p, f, fr) = evalue(SIG, I); perm, (pp, pf, pfr) = evalue([True] * N, I)
    mb_sig = [sum(RB[i].values()) / len(RB[i]) for i in I if SIG[i] and RB[i]]; mb_non = [sum(RB[i].values()) / len(RB[i]) for i in I if not SIG[i] and RB[i]]
    res[nom] = dict(jours_signal=sum(SIG[i] for i in I), jours=len(I), net=sum(s), prix=p, fin=f, frais=fr,
                    panier_moy_jours_signal=(sum(mb_sig) / len(mb_sig)) if mb_sig else None, panier_moy_autres=sum(mb_non) / len(mb_non),
                    short_permanent=dict(net=sum(perm), prix=pp, fin=pf, frais=pfr))
res["par_an"] = {y: dict(jours_signal=sum(SIG[i] for i in range(N) if an(i) == y), net=sum(evalue(SIG, [i for i in range(N) if an(i) == y])[0])) for y in range(2021, 2027)}
net26 = res["2026"]["net"]; n2 = len(I2); sig2 = [SIG[i] for i in I2]; rng = random.Random(43); tem = []
for _ in range(1000):
    k = rng.randint(30, n2 - 30); sh = sig2[k:] + sig2[:k]; full = SIG[:]
    for j, i in enumerate(I2): full[i] = sh[j]
    tem.append(sum(evalue(full, I2)[0]))
p = sum(t >= net26 for t in tem) / len(tem); res["temoin_2026"] = dict(moy=sum(tem) / len(tem), p=p)
if res["2026"]["jours_signal"] == 0: v = "NON ÉVALUABLE"
else: v = "GAGNE" if res["2021-25"]["net"] > 0 and net26 > 0 and p < 0.05 else "NON DÉMONTRÉ" if net26 > 0 else "PERD"
res["verdict"] = v; json.dump(res, open("t43.json", "w"), indent=1); print(json.dumps(res, indent=1))

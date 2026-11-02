"""PREREG-55 : achat BTC après un jour de krach (règles : PREREG-55-achat-apres-krach.md)."""
import calendar, json, random, statistics as st, time
J = 86_400_000; FR = 0.001
C = {x[0]: (x[1], x[2]) for x in json.load(open("t51_btc.json"))}; D = sorted(C)
B0 = calendar.timegm((2024, 1, 1, 0, 0, 0)) * 1000
def fen(d): return C[d + 2 * J][1] / C[d][0] - 1 - 2 * FR if d in C and d + 2 * J in C else None
ev = []; occupe = -1
for d in D:
    if d <= occupe: continue
    o, c = C[d]
    if c / o - 1 < -0.07 and fen(d + J) is not None: ev.append((d + J, fen(d + J))); occupe = d + 3 * J
pris = {e + k * J for e, _ in ev for k in range(-2, 3)}
cand = [d for d in D if fen(d) is not None and d not in pris]
def test(X, seed):
    if not X: return None
    m = st.mean(x[1] for x in X); rng = random.Random(seed); lo = min(x[0] for x in X); hi = max(x[0] for x in X)
    pool = [d for d in cand if (X[0][0] < B0) == (d < B0)] if all((x[0] < B0) == (X[0][0] < B0) for x in X) else cand
    t = [st.mean(fen(rng.choice(pool)) for _ in X) for _ in range(1000)]
    return dict(n=len(X), moy=m, med=st.median(x[1] for x in X), pos=sum(x[1] > 0 for x in X) / len(X), pire=min(x[1] for x in X), temoin=st.mean(t), p=sum(v >= m for v in t) / 1000)
A = [x for x in ev if x[0] < B0]; B = [x for x in ev if x[0] >= B0]
res = dict(A=test(A, 55), B=test(B, 550), AB=test(ev, 5500), par_an={y: [round(r, 4) for d, r in ev if time.gmtime(d / 1000).tm_year == y] for y in range(2017, 2027)})
a, b, ab = res["A"], res["B"], res["AB"]
res["verdict"] = "GAGNE" if a and b and a["moy"] > 0 and a["p"] < 0.05 and b["moy"] > 0 and ab["p"] < 0.05 else "NON DÉMONTRÉ" if ab and ab["moy"] > 0 else "PERD"
json.dump(res, open("t55.json", "w"), indent=1); print(json.dumps(res, indent=1))

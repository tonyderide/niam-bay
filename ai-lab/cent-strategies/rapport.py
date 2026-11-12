"""Tableaux pour RESULTAT.md à partir de t75.json (aucun calcul de stratégie ici)."""
import json, numpy as np
O = json.load(open("t75.json")); R = O["R"]; H = O["hasard"]
el = lambda b: b is not None and not b["arretees"] and b["baisse_port"] > -0.30
def neuf(n):
    a = [R[n][k] for k in ("N6_P1", "N6_P2", "N24_P1", "N24_P2") if R[n][k]]
    pp = {}
    for b in a:
        for c, v in b["par_paire"].items(): pp[c] = pp.get(c, 0) + v
    return round(sum(b["total"] for b in a)), sum(v > 0 for v in pp.values()), len(pp)
f = lambda x: f"{x:+,.0f}".replace(",", " ")
mx = np.array([h["max_100"] for h in H]); W5h = np.array([h["W5"] for h in H]); med = np.array([h["mediane"] for h in H])
print("hasard : n =", len(H), "max100 médiane", f(np.median(mx)), "p95", f(np.percentile(mx, 95)), "min", f(mx.min()), "max", f(mx.max()))
print("hasard : médiane des 100 (médiane sur répétitions)", f(np.median(med)), "; W5 sous hasard médiane", f(np.median(W5h)), "p95", f(np.percentile(W5h, 95)))
el_mx = [h["max_eligibles"] for h in H if h["max_eligibles"] is not None]
print("hasard : max éligibles p95", f(np.percentile(el_mx, 95)), "médiane", f(np.median(el_mx)), "(", len(el_mx), "rép. avec au moins une éligible)")
from collections import Counter
print("qui gagne sous hasard :", Counter(h["meilleure"] for h in H).most_common(8))
# percentile de chaque stratégie contre sa propre distribution hasard
print("\n| # | Stratégie | P1 4 paires | éligible | baisse port. | arrêtées | P2 4 paires | 30 neuves P1+P2 (paires +) | P1 moteur 1 h | P1 hasard médiane |")
print("|---|---|---|---|---|---|---|---|---|---|")
noms = [s["nom"] for s in O["strategies"]]
for i, n in enumerate(noms, 1):
    r = R[n]; nv = neuf(n); hz = np.median([h["totaux"][n] for h in H])
    print(f"| {i} | {n} | {f(r['P1']['total'])} | {'oui' if el(r['P1']) else 'non'} | {r['P1']['baisse_port']*100:.0f} % | {len(r['P1']['arretees'])} | {f(r['P2']['total'])} | {f(nv[0])} ({nv[1]}/{nv[2]}) | {f(r['P1_1h']['total'])} | {f(hz)} |")
print("\nTOP 10 P1 (éligibles ou non)")
top = sorted(noms, key=lambda n: -R[n]["P1"]["total"])[:10]
for n in top:
    r = R[n]; nv = neuf(n)
    print(f"| {n} | {f(r['P1']['total'])} | {'oui' if el(r['P1']) else 'non'} | {f(r['P2']['total'])} | {f(r['N6_P1']['total'])} / {f(r['N6_P2']['total'])} | {f(r['N24_P1']['total'])} / {f(r['N24_P2']['total'])} | {f(nv[0])} ({nv[1]}/{nv[2]}) |")
print("\nTOP 10 éligibles")
tope = sorted([n for n in noms if el(R[n]["P1"])], key=lambda n: -R[n]["P1"]["total"])[:10]
for n in tope:
    r = R[n]; nv = neuf(n)
    print(f"| {n} | {f(r['P1']['total'])} | {f(r['P2']['total'])} | {f(r['N6_P1']['total'])} / {f(r['N6_P2']['total'])} | {f(r['N24_P1']['total'])} / {f(r['N24_P2']['total'])} | {f(nv[0])} ({nv[1]}/{nv[2]}) |")
print("\npositives P1:", sum(R[n]["P1"]["total"] > 0 for n in noms), "éligibles:", sum(el(R[n]["P1"]) for n in noms),
      "positives P2:", sum(R[n]["P2"]["total"] > 0 for n in noms), "positives neuves:", sum(neuf(n)[0] > 0 for n in noms))
# corrélation de rang P1 -> hors échantillon
from numpy import argsort
def rk(x): return argsort(argsort(x))
p1 = np.array([R[n]["P1"]["total"] for n in noms]); p2 = np.array([R[n]["P2"]["total"] for n in noms]); nn = np.array([neuf(n)[0] for n in noms])
print("rang P1 vs P2 (Spearman)", round(np.corrcoef(rk(p1), rk(p2))[0, 1], 2), "; P1 vs neuves", round(np.corrcoef(rk(p1), rk(nn))[0, 1], 2))
best_oos = max(noms, key=lambda n: R[n]["P2"]["total"] + neuf(n)[0])
print("meilleure hors échantillon (après coup, à ne pas croire):", best_oos, f(R[best_oos]["P1"]["total"]), f(R[best_oos]["P2"]["total"]), neuf(best_oos))
print("verdict", O.get("verdict"), O.get("criteres"), O.get("hasard_p95_max100"))

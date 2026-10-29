import json, numpy as np, etude as E
fige = eval(json.load(open("resultats-1h.json"))["fige"]); anciens = set(json.load(open("univers.json"))) - {"BTCSTUSDT","CTKUSDT","CVCUSDT","CVXUSDT","LITUSDT","MDTUSDT","SLPUSDT","SXPUSDT"}
R = E.univers(fige, E.REGLAGE)
print("2024-25 figé, 245 anciens :", round(np.mean([r["rend"] for s, r in R.items() if s in anciens]), 4))
print("8 nouveaux :", {s: round(r["rend"], 3) for s, r in R.items() if s not in anciens})
J = E.univers(fige, E.JUGEMENT)
for s, r in J.items():
    if abs(r["rend"]) < 0.001:
        x = E.tranche(E.DON[s], E.JUGEMENT); print(s, len(x), "bougies", r["cycles"], "cycles", round(r["rend"], 5), "fin", np.datetime64(int(x[-1, 0]), "ms"), "var", round(x[-1,4]/x[0,1]-1, 3)); break
print("pièces 2026 avec moins de 2000 bougies :", sum(len(E.tranche(E.DON[s], E.JUGEMENT)) < 2000 for s in J))

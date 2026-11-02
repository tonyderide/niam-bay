"""PREREG-57, diagnostic après verdict : short tenu (quantité fixe, PREREG-46) contre short rééquilibré chaque jour (poids fixe), trade par trade, sans couverture ni financement."""
import json, os, statistics as st
src = open("t57.py").read(); ns = {"__file__": os.path.abspath("t57.py")}; exec(src[:src.index("def simule")], ns)
C, SHORTS, J = ns["C"], ns["SHORTS"], ns["J"]
tenu, reeq = [], []
for s, e, x in SHORTS:
    jours = [d for d in range(e, x + J, J) if d in C[s]]
    if not jours: continue
    tenu.append(max(-1, -(C[s][jours[-1]][1] / C[s][e][0] - 1)))
    v = 1.0
    for d in jours: v *= 1 - (C[s][d][1] / C[s][d][0] - 1)
    reeq.append(v - 1)
print("trades", len(tenu), "short tenu : moyenne", round(st.mean(tenu), 4), "médiane", round(st.median(tenu), 4), "| short rééquilibré chaque jour : moyenne", round(st.mean(reeq), 4), "médiane", round(st.median(reeq), 4))

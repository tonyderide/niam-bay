"""PREREG-55, information : même règle sur le panier égal des 253 perpétuels 2024-2026, seuil −10 %."""
import glob, json, os, numpy as np, statistics as st
src = open("t39.py").read(); ns = {"__file__": os.path.abspath("t39.py")}; exec(src[:src.index("univ = set")], ns)
couper, journalier, D, JMS = ns["couper"], ns["journalier"], ns["D"], ns["JMS"]
univ = set(json.load(open(os.path.join(D, "../univers.json")))); S = {}; N = {}
O = {}
for f in glob.glob(f"{D}/*-1h.npy"):
    s = os.path.basename(f)[:-7]
    if s not in univ: continue
    a = couper(np.load(f))
    if len(a) < 48: continue
    for j, o, c in journalier(a):
        S[int(j)] = S.get(int(j), 0) + c / o - 1; N[int(j)] = N.get(int(j), 0) + 1
R = {j: S[j] / N[j] for j in S}; ev = []; occ = -1
for j in sorted(R):
    if j <= occ: continue
    if R[j] < -0.10 and all(j + k in R for k in (1, 2, 3)):
        v = np.prod([1 + R[j + k] for k in (1, 2, 3)]) - 1 - 0.001; ev.append((j, float(v))); occ = j + 3
print("krachs du panier (< −10 %) :", len(ev), [(int(j), round(v, 4)) for j, v in ev], "moyenne", round(st.mean(v for _, v in ev), 4) if ev else None)

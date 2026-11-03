import glob, numpy as np, re
src = open("t62.py").read().split("D = {}")[0]; exec(src)
g = (0.10, 0.005, 0.01); out = {}
for nom, (d, f) in {"2024-25": (ms(2024,1,1), ms(2026,1,1)), "2026": (ms(2026,1,1), ms(2026,10,1))}.items():
    R = []; n_tr = 0; ruin = 0
    for fn in sorted(glob.glob("../dca-martingale/refait/donnees/*-1h.npy")):
        a = couper(np.load(fn), 48); x = a[(a[:,0] >= d) & (a[:,0] < f)]
        if len(x) < 500: continue
        out_ = np.empty(len(x) + 1); n = chaine(x[:,1], x[:,2], x[:,3], x[:,4], *g, 1, 0, out_); r = out_[:n]
        if n == 0: continue
        R.append(((r > 0).mean(), r.mean(), np.prod(1 + r) - 1, n, np.minimum.accumulate(np.cumprod(1+r)).min() - 1))
    R = np.array(R); print(nom, "pieces", len(R), "gagnants", round(R[:,0].mean(), 3), "esp%", round(R[:,1].mean()*100, 3), "composé médian", round(np.median(R[:,2]), 3), "moyen", round(R[:,2].mean(), 3), "part composé>0", round((R[:,2] > 0).mean(), 3), "trades/pièce", round(R[:,3].mean()), "part -50%+", round((R[:,4] <= -.5).mean(), 3))

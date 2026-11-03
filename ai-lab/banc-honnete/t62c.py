import sys, glob, os, numpy as np
exec(open("t62.py").read().split("D = {}")[0]); g = (0.10, 0.005, 0.01); Dd = sys.argv[1]
for nom, (d, f) in {"2024-25": (ms(2024,1,1), ms(2026,1,1)), "2026": (ms(2026,1,1), ms(2026,10,1))}.items():
    R = []; TM = []
    for fn in sorted(glob.glob(Dd + "/*.npy")):
        a = couper(np.load(fn), 2880); x = a[(a[:,0] >= d) & (a[:,0] < f)]
        o = np.empty(len(x) + 1); n = chaine(x[:,1], x[:,2], x[:,3], x[:,4], *g, 1, 0, o); r = o[:n].copy()
        e = np.cumprod(1 + r); dd = (e / np.maximum.accumulate(e) - 1).min()
        R.append(((r > 0).mean(), r.mean(), e[-1] - 1, n, dd, r.min())); tm = []
        for i in range(200):
            q = np.empty(len(x) + 1); k = chaine(x[:,1], x[:,2], x[:,3], x[:,4], *g, 2, i, q); tm.append(q[:k].mean())
        TM.append(tm); print(" ", nom, os.path.basename(fn)[:-4], f"gagnants {R[-1][0]:.3f} esp% {R[-1][1]*100:+.3f} composé {R[-1][2]*100:+.1f}% n {n} baisse {dd*100:.1f}%", flush=True)
    R = np.array(R); TM = np.array(TM).mean(0); obs = R[:,1].mean()
    print(nom, "MOY gagnants", round(R[:,0].mean(),3), "esp%", round(obs*100,3), "composé médian", round(np.median(R[:,2])*100,1), "part>0", (R[:,2]>0).mean(), "témoin esp%", round(TM.mean()*100,3), "battu", (TM < obs).mean(), "baisse médiane", round(np.median(R[:,4])*100,1))

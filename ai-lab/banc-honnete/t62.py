"""PREREG-62 : 90 % de trades gagnants avec trailing, sans martingale."""
import itertools, json, numpy as np, datetime as dt
from numba import njit
TK = 0.0005
ms = lambda a, m, j: int(dt.datetime(a, m, j, tzinfo=dt.timezone.utc).timestamp() * 1000)
def couper(a, F):
    plat = np.convolve(a[:, 2] == a[:, 3], np.ones(F, int), "valid") == F if len(a) >= F else np.zeros(0, bool)
    return a[:np.argmax(plat)] if plat.any() else a
@njit
def chaine(o, h, l, c, s, t, a, mode, seed, out):
    """mode 0 long seul ; 1 inversion après perte ; 2 sens au hasard à chaque trade (témoin)"""
    np.random.seed(seed)
    T = len(o); i = 0; m = 0; sens = 1.0
    while i < T:
        if mode == 2: sens = 1.0 if np.random.random() < 0.5 else -1.0
        e = o[i]; sl = e * (1 - s * sens); actif = False; pic = 0.0
        while True:
            px = -1.0
            hi = h[i] if sens > 0 else l[i]; lo = l[i] if sens > 0 else h[i]; op = o[i]; stop = sl
            if actif:
                ts = pic * (1 - t * sens); stop = max(sl, ts) if sens > 0 else min(sl, ts)
            if (lo - stop) * sens <= 0: px = min(op, stop) if sens > 0 else max(op, stop)
            elif actif: pic = max(pic, hi) if sens > 0 else min(pic, hi)
            elif (hi - e * (1 + a * sens)) * sens >= 0: actif = True; pic = hi
            if px < 0 and i == T - 1: px = c[i]
            if px >= 0:
                r = sens * (px / e - 1) - TK - TK * px / e
                out[m] = r; m += 1
                if mode == 1 and r <= 0: sens = -sens
                break
            i += 1
        i += 1
    return m
D = {}
for p in ("BTC", "ETH", "SOL"):
    x = couper(np.load(f"../dca-martingale/refait/donnees/{p}USDT-1m.npy"), 2880)
    D[p] = {"choix": x[(x[:, 0] >= ms(2024,1,1)) & (x[:, 0] < ms(2026,1,1))], "juge": x[(x[:, 0] >= ms(2026,1,1)) & (x[:, 0] < ms(2026,10,1))]}
    print(p, {k: len(v) for k, v in D[p].items()})
def tr(x, s, a, t, mode, seed=0):
    out = np.empty(len(x) + 1); n = chaine(x[:,1], x[:,2], x[:,3], x[:,4], s, t, a, mode, seed, out); return out[:n].copy()
def stats(r):
    w = r[r > 0]; l = r[r <= 0]
    return dict(n=len(r), win=float((r > 0).mean()), esp=float(r.mean()), total=float(r.sum()), gain=float(w.mean()) if len(w) else 0, perte=float(l.mean()) if len(l) else 0, pire=float(r.min()), compo=float(np.prod(1 + r) - 1))
G = [(s/100, a/100, t/100) for s, a, t in itertools.product((3,5,8,10,15,20,30), (.3,.5,1,1.5,2), (.1,.25,.5,1)) if t < a]
print("reglages", len(G)); res = {}
for mode, nom in ((0, "long"), (1, "inversion")):
    L = []
    for g in G:
        st = {p: stats(tr(D[p]["choix"], *g, mode)) for p in D}
        L.append((g, st, min(v["win"] for v in st.values()), np.mean([v["esp"] for v in st.values()])))
    el = [x for x in L if x[2] >= .9]; pos = [x for x in el if x[3] > 0]
    print(f"\n=== {nom}: {len(el)}/{len(G)} reglages >=90% partout 2024-25 ; dont esperance>0: {len(pos)}")
    allwin = sorted(L, key=lambda x: -x[2])[:3]
    for x in allwin: print("  top win", x[0], round(x[2], 3), "esp%", round(x[3]*100, 3))
    if not el: res[nom] = None; continue
    g, st, w, e = max(el, key=lambda x: x[3]); print("FIGE", g, "win min", round(w, 3), "esp% moy", round(e*100, 3))
    for p in D: print("  choix", p, {k: round(v, 4) for k, v in st[p].items()})
    ok = True; res[nom] = {"reglage": g}
    for p in D:
        r = tr(D[p]["juge"], *g, mode); sj = stats(r); tm = np.array([tr(D[p]["juge"], *g, 2, seed=i).mean() for i in range(200)]); pv = float((tm >= r.mean()).mean())
        print("  2026", p, {k: round(v, 4) for k, v in sj.items()}, "temoin esp%", round(tm.mean()*100, 3), "p", pv, "| gains pour effacer pire", round(-sj["pire"]/max(sj["gain"], 1e-9), 1))
        res[nom][p] = dict(sj, p=pv)
json.dump(res, open("t62.json", "w"), indent=1)

"""PREREG-63 : filtre de volatilité sur la règle à 90 %."""
import sys, os, numpy as np, datetime as dt
from numba import njit
TK = 0.0005; S, T_, A = 0.10, 0.005, 0.01; DM = 86_400_000
ms = lambda a, m, j: int(dt.datetime(a, m, j, tzinfo=dt.timezone.utc).timestamp() * 1000)
def couper(a, F):
    plat = np.convolve(a[:, 2] == a[:, 3], np.ones(F, int), "valid") == F if len(a) >= F else np.zeros(0, bool)
    return a[:np.argmax(plat)] if plat.any() else a
@njit
def chaine(o, h, l, c, ok, s, t, a, out):
    n = len(o); i = 0; m = 0; sens = 1.0
    while i < n:
        if not ok[i]: i += 1; continue
        e = o[i]; sl = e * (1 - s * sens); actif = False; pic = 0.0
        while True:
            px = -1.0
            hi = h[i] if sens > 0 else l[i]; lo = l[i] if sens > 0 else h[i]; op = o[i]; stop = sl
            if actif:
                ts = pic * (1 - t * sens); stop = max(sl, ts) if sens > 0 else min(sl, ts)
            if (lo - stop) * sens <= 0: px = min(op, stop) if sens > 0 else max(op, stop)
            elif actif: pic = max(pic, hi) if sens > 0 else min(pic, hi)
            elif (hi - e * (1 + a * sens)) * sens >= 0: actif = True; pic = hi
            if px < 0 and i == n - 1: px = c[i]
            if px >= 0:
                r = sens * (px / e - 1) - TK - TK * px / e; out[m] = r; m += 1
                if r <= 0: sens = -sens
                break
            i += 1
        i += 1
    return m
def permis(x):
    j = (x[:, 0] // DM).astype(np.int64); u = np.unique(j); v = {}
    lr = np.diff(np.log(x[:, 4]), prepend=np.log(x[0, 4]))
    for d, seg in zip(u, np.split(lr, np.searchsorted(j, u)[1:])): v[d] = seg.std()
    ok = {}
    for d in u:
        h = [v[k] for k in range(d - 90, d) if k in v]
        ok[d] = len(h) == 90 and v[d - 1] <= np.median(h)
    return np.array([ok[d] for d in j]), np.mean([ok[d] for d in u[90:]])
C = ["BTC","ETH","SOL","XRP","DOGE","ADA","LINK","AVAX","LTC","BNB","DOT","BCH","ATOM"]; Dd = sys.argv[1]
PER = {"P1": (ms(2024,4,1), ms(2026,1,1)), "P2": (ms(2026,1,1), ms(2026,10,1))}; R = {}
for c in C:
    f = f"../dca-martingale/refait/donnees/{c}USDT-1m.npy" if c in ("BTC","ETH","SOL") else f"{Dd}/{c}.npy"
    a = couper(np.load(f), 2880); a = a[a[:, 0] < ms(2026,10,1)]; ok, part = permis(a)
    for p, (d, g) in PER.items():
        w = (a[:, 0] >= d) & (a[:, 0] < g); x = a[w]
        for nom, m in (("sans", np.ones(len(x), bool)), ("filtre", ok[w])):
            o = np.empty(len(x) + 1); n = chaine(x[:,1], x[:,2], x[:,3], x[:,4], m, S, T_, A, o); r = o[:n].copy(); e = np.cumprod(1 + r)
            R[c, p, nom] = ((r > 0).mean(), r.mean(), e[-1] - 1, n, (e / np.maximum.accumulate(np.r_[1, e])[1:] - 1).min())
    print(c, "part jours permis", round(part, 2), flush=True)
for p in PER:
    for nom in ("sans", "filtre"):
        M = np.array([R[c, p, nom] for c in C])
        print(p, nom, f"gagnants {M[:,0].mean()*100:.1f}% esp {M[:,1].mean()*100:+.3f}% composé médian {np.median(M[:,2])*100:+.1f}% positives {(M[:,2]>0).sum()}/13 trades/pièce {M[:,3].mean():.0f} baisse médiane {np.median(M[:,4])*100:.1f}%")
print("--- par pièce composé (filtre) P1 P2 P1xP2")
for c in C:
    a, b = R[c,"P1","filtre"][2], R[c,"P2","filtre"][2]; print(f"  {c:5} {a*100:+7.1f}% {b*100:+7.1f}% {((1+a)*(1+b)-1)*100:+7.1f}%   sans: {((1+R[c,'P1','sans'][2])*(1+R[c,'P2','sans'][2])-1)*100:+7.1f}%")

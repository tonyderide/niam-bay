"""PREREG-67 : martingale avec inversion, sortie SL 5 %, activation 10 %, trailing 1 %."""
import sys, itertools, numpy as np, datetime as dt
from numba import njit
TK = 0.0005; DM = 30 * 86_400_000
ms = lambda a, m, j: int(dt.datetime(a, m, j, tzinfo=dt.timezone.utc).timestamp() * 1000)
def couper(a, F):
    plat = np.convolve(a[:, 2] == a[:, 3], np.ones(F, int), "valid") == F if len(a) >= F else np.zeros(0, bool)
    return a[:np.argmax(plat)] if plat.any() else a
@njit
def chaine(o, h, l, c, mode, seed, s, t, a, R, I):
    np.random.seed(seed); n = len(o); i = 0; m = 0; inv = 1.0
    while i < n:
        sens = inv if mode == 1 else (1.0 if np.random.random() < 0.5 else -1.0)
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
                R[m] = sens * (px / e - 1) - TK - TK * px / e; I[m] = i; m += 1
                if R[m-1] <= 0: inv = -inv
                break
            i += 1
        i += 1
    return m
@njit
def jouer(R, m_, k, s):
    """retourne capital final, capital minimum"""
    cap = 1000.0; mise = 10.0; p = 0; mn = cap
    for r in R:
        if cap < 50: break
        pos = min(mise / s, 10 * cap); cap += pos * r; mn = min(mn, cap)
        if r <= 0:
            p += 1; mise *= m_
            if k > 0 and p >= k: mise = 10.0; p = 0
        else: mise = 10.0; p = 0
    return cap, mn
S_, A_, T_ = .05, .10, .01; Dd = sys.argv[1]; PER = {"P1": (ms(2024,2,1), ms(2026,1,1)), "P2": (ms(2026,1,1), ms(2026,10,1))}
C = "XRP DOGE ADA LINK AVAX LTC BNB DOT BCH ATOM".split(); C3 = ["BTC","ETH","SOL"]; X = {}
for c in C + C3:
    a = couper(np.load(f"../dca-martingale/refait/donnees/{c}USDT-1m.npy" if c in C3 else f"{Dd}/{c}.npy"), 2880)
    for p, (d, f) in PER.items(): X[c, p] = a[(a[:,0] >= d) & (a[:,0] < f)]
def tr(c, p, mode=1, seed=0):
    x = X[c, p]; n = len(x); R = np.empty(n + 1); I = np.empty(n + 1, np.int64); m = chaine(x[:,1], x[:,2], x[:,3], x[:,4], mode, seed, S_, T_, A_, R, I); return R[:m].copy(), x[I[:m], 0]
T = {(c, p): tr(c, p) for c in C + C3 for p in PER}
def bilan(cs, p, m_, k):
    return np.array([jouer(T[c, p][0], m_, k, S_) for c in cs])
for p in PER:
    M = bilan(C, p, 2.0, 4); res = M[:,0] - 1000
    ro = []; mo = []
    d, f = PER[p]
    for c in C:
        R, t = T[c, p]
        for st in range(d, f - 3 * DM, DM):
            w = (t >= st) & (t < st + 3 * DM); a, b = jouer(R[w], 2.0, 4, S_); ro.append(a - 1000); mo.append(b)
    ro = np.array(ro); mo = np.array(mo)
    tm = np.array([np.mean([jouer(tr(c, p, 2, s)[0], 2.0, 4, S_)[0] - 1000 for c in C]) for s in range(200)])
    print(p, f"m2 k4 : résultat moyen {res.mean():+.0f} € médian {np.median(res):+.0f} € positives {(res>0).sum()}/10 capital min le plus bas {M[:,1].min():.0f} € pièces ≤500 € {(M[:,1]<=500).sum()} | gagnants {np.mean([(T[c,p][0]>0).mean() for c in C])*100:.1f}% trades/pièce {np.mean([len(T[c,p][0]) for c in C]):.0f}")
    print("   départs 3 mois :", f"en perte {(ro<=0).mean()*100:.0f}% ruinés(≤500) {(mo<=500).mean()*100:.1f}% médian {np.median(ro):+.0f} € pire {ro.min():+.0f} €", "| témoin", f"{tm.mean():+.0f} € (é.-t. {tm.std():.0f}) battu {(tm<res.mean()).mean():.3f}")
    print("   par pièce", {c: int(res[i]) for i, c in enumerate(C)}); print("   BTC/ETH/SOL", {c: int(v) for c, v in zip(C3, bilan(C3, p, 2.0, 4)[:,0] - 1000)})
    print("   grille moyen € (m,k):", {(m_, k or 'inf'): int(bilan(C, p, m_, k)[:,0].mean() - 1000) for m_, k in itertools.product((1.,1.5,2.,3.), (2,4,6,0)) if m_ > 1 or k == 2})

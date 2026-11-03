"""PREREG-64 : sortie à 90 %, sens donné par l'EMA horaire, 10 cryptos."""
import sys, numpy as np, datetime as dt
from numba import njit
TK = 0.0005; S, T_, A = 0.10, 0.005, 0.01; HM = 3_600_000
ms = lambda a, m, j: int(dt.datetime(a, m, j, tzinfo=dt.timezone.utc).timestamp() * 1000)
def couper(a, F):
    plat = np.convolve(a[:, 2] == a[:, 3], np.ones(F, int), "valid") == F if len(a) >= F else np.zeros(0, bool)
    return a[:np.argmax(plat)] if plat.any() else a
@njit
def chaine(o, h, l, c, sg, mode, seed, s, t, a, out):
    """mode 0 : sens = sg[i] (EMA) ; 1 : inversion après perte ; 2 : hasard à chaque trade"""
    np.random.seed(seed); n = len(o); i = 0; m = 0; inv = 1.0
    while i < n:
        sens = sg[i] if mode == 0 else inv if mode == 1 else (1.0 if np.random.random() < 0.5 else -1.0)
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
                if r <= 0: inv = -inv
                break
            i += 1
        i += 1
    return m
def signe(x, N):
    """sens de chaque minute : clôture de l'heure PRÉCÉDENTE terminée contre son EMA"""
    hh = (x[:, 0] // HM).astype(np.int64); u, idx = np.unique(hh, return_index=True); fin = np.r_[idx[1:] - 1, len(x) - 1]; cl = x[fin, 4]
    k = 2 / (N + 1); e = np.empty(len(cl)); e[0] = cl[0]
    for i in range(1, len(cl)): e[i] = cl[i] * k + e[i-1] * (1 - k)
    sg = np.where(cl > e, 1.0, -1.0); pos = np.searchsorted(u, hh) - 1; pos[pos < 0] = 0
    return sg[pos]
Dd = sys.argv[1]; PER = {"P1": (ms(2024,2,1), ms(2026,1,1)), "P2": (ms(2026,1,1), ms(2026,10,1))}
ch = {}
def charge(c):
    if c not in ch:
        ch[c] = couper(np.load(f"../dca-martingale/refait/donnees/{c}USDT-1m.npy" if c in ("BTC","ETH","SOL") else f"{Dd}/{c}.npy"), 2880)
    return ch[c]
def cut(c, sg, p):
    a = charge(c); d, g = PER[p]; w = (a[:, 0] >= d) & (a[:, 0] < g); return a[w], sg[w]
def run(c, N, p, mode, seed=0):
    x, sg = cut(c, signe(charge(c), N or 50), p); o = np.empty(len(x) + 1); n = chaine(x[:,1], x[:,2], x[:,3], x[:,4], sg, mode, seed, S, T_, A, o); return o[:n].copy()
def st(r):
    e = np.cumprod(1 + r); return ((r > 0).mean(), r.mean(), e[-1] - 1, len(r), (e / np.maximum.accumulate(np.r_[1, e])[1:] - 1).min())
sc = {N: np.mean([st(run(c, N, "P1", 0))[1] for c in ("BTC","ETH","SOL")]) for N in (20, 50, 200)}
print("choix", {k: round(v*100, 3) for k, v in sc.items()}); N = max(sc, key=sc.get); print("N figé", N)
C = "XRP DOGE ADA LINK AVAX LTC BNB DOT BCH ATOM".split(); RR = {}
for p in PER:
    M = np.array([st(run(c, N, p, 0)) for c in C]); I = np.array([st(run(c, N, p, 1)) for c in C]); RR[p] = M
    tm = np.array([np.mean([run(c, N, p, 2, s).mean() for c in C]) for s in range(200)])
    print(p, f"EMA gagnants {M[:,0].mean()*100:.1f}% esp {M[:,1].mean()*100:+.3f}% portefeuille {M[:,2].mean()*100:+.1f}% médian {np.median(M[:,2])*100:+.1f}% positives {(M[:,2]>0).sum()}/10 trades/pièce {M[:,3].mean():.0f} baisse médiane {np.median(M[:,4])*100:.1f}%")
    print(p, f"Inversion gagnants {I[:,0].mean()*100:.1f}% esp {I[:,1].mean()*100:+.3f}% portefeuille {I[:,2].mean()*100:+.1f}% positives {(I[:,2]>0).sum()}/10")
    print(p, f"témoin esp {tm.mean()*100:+.3f}% battu {(tm < M[:,1].mean()).mean():.3f}")
print("--- pièce P1 P2 P1xP2")
for i, c in enumerate(C):
    a, b = RR["P1"][i,2], RR["P2"][i,2]; print(f"  {c:5} {a*100:+8.1f}% {b*100:+8.1f}% {((1+a)*(1+b)-1)*100:+8.1f}% gagnants {RR['P1'][i,0]*100:.1f}/{RR['P2'][i,0]*100:.1f}")
pf = np.mean([(1+RR["P1"][i,2])*(1+RR["P2"][i,2]) for i in range(10)]) - 1; print("portefeuille P1xP2", round(pf*100, 1))
for c in ("BTC","ETH","SOL"): print(" ", c, "2026", [round(v, 4) for v in st(run(c, N, "P2", 0))])

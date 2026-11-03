"""PREREG-66 : stopper plus tôt, prendre plus tard."""
import sys, itertools, json, numpy as np
src = open("t64.py").read().split("def signe")[0]; exec(src)
Dd = sys.argv[1]; PER = {"P1": (ms(2024,2,1), ms(2026,1,1)), "P2": (ms(2026,1,1), ms(2026,10,1))}
G = [(s/100, a/100, t/100) for s, a, t in itertools.product((1,2,3,5), (2,3,5,10), (1,2,3)) if t < a]
X = {}
for c in "BTC ETH SOL XRP DOGE ADA LINK AVAX LTC BNB DOT BCH ATOM".split():
    a = couper(np.load(f"../dca-martingale/refait/donnees/{c}USDT-1m.npy" if c in ("BTC","ETH","SOL") else f"{Dd}/{c}.npy"), 2880)
    for p, (d, f) in PER.items(): X[c, p] = a[(a[:,0] >= d) & (a[:,0] < f)]
Z = {k: np.ones(len(v)) for k, v in X.items()}
def run(c, p, g, mode=1, seed=0):
    x = X[c, p]; s, a, t = g; o = np.empty(len(x) + 1); n = chaine(x[:,1], x[:,2], x[:,3], x[:,4], Z[c, p], mode, seed, s, t, a, o); return o[:n].copy()
def st(r):
    e = np.cumprod(1 + r); return ((r > 0).mean(), r.mean(), e[-1] - 1, len(r), (e / np.maximum.accumulate(np.r_[1, e])[1:] - 1).min())
C3 = ("BTC","ETH","SOL"); C = "XRP DOGE ADA LINK AVAX LTC BNB DOT BCH ATOM".split()
sc = {g: np.mean([st(run(c, "P1", g))[1] for c in C3]) for g in G}; N = max(sc, key=sc.get)
print("choix: reglages positifs sur BTC/ETH/SOL P1", sum(v > 0 for v in sc.values()), "/", len(G), "| figé (s,a,t)", N, "esp%", round(sc[N]*100, 3))
for g, v in sorted(sc.items(), key=lambda x: -x[1])[:4]: print("   ", g, round(v*100, 3))
for p in PER:
    M = np.array([st(run(c, p, N)) for c in C]); tm = np.array([np.mean([run(c, p, N, 2, s).mean() for c in C]) for s in range(200)])
    print(p, f"gagnants {M[:,0].mean()*100:.1f}% esp {M[:,1].mean()*100:+.3f}% portefeuille {M[:,2].mean()*100:+.1f}% médian {np.median(M[:,2])*100:+.1f}% positives {(M[:,2]>0).sum()}/10 trades/pièce {M[:,3].mean():.0f} baisse médiane {np.median(M[:,4])*100:.1f}% témoin {tm.mean()*100:+.3f}% battu {(tm < M[:,1].mean()).mean():.3f}")
    print("   par pièce", {c: round(float(M[i,2])*100) for i, c in enumerate(C)})
    # toute la grille, sur les 10 pièces, pour information
    A = np.array([[st(run(c, p, g))[:2] for c in C] for g in G])
    print("   grille 10 pièces: réglages à esp>0", int((A[:,:,1].mean(1) > 0).sum()), "/", len(G), "| gagnants de", round(A[:,:,0].mean(1).min()*100, 1), "à", round(A[:,:,0].mean(1).max()*100, 1), "% | meilleure esp%", round(A[:,:,1].mean(1).max()*100, 3))
    json.dump({str(g): [float(A[i,:,0].mean()), float(A[i,:,1].mean())] for i, g in enumerate(G)}, open(f"t66_{p}.json", "w"))

"""PREREG-49 : effet MAX (règles : PREREG-49-effet-max.md). Prix : construction de t39.py ; squelette de t48.py."""
import glob, json, os, numpy as np
src = open("t39.py").read(); ns = {"__file__": os.path.abspath("t39.py")}
exec(src[:src.index("TAILLE =")], ns)
R, LUN, JMS, TK, sym, D, couper, journalier = (ns[k] for k in ("R", "LUN", "JMS", "TK", "sym", "D", "couper", "journalier"))
NW, NP = R.shape; J0 = int(LUN[0]) - 70; ND = int(LUN[-1]) + 7 - J0
CL = np.full((ND, NP), np.nan)
for j, s in enumerate(sym):
    d = journalier(couper(np.load(f"{D}/{s}-1h.npy")))
    for x in d:
        k = int(x[0]) - J0
        if 0 <= k < ND: CL[k, j] = x[2]
RJ = np.vstack([np.full((1, NP), np.nan), CL[1:] / CL[:-1] - 1]); ib = sym.index("BTCUSDT")
MAXR = np.full((NW, NP), np.nan)
for w, lu in enumerate(LUN):
    k = int(lu) - J0; X = RJ[k - 30:k]
    n = (~np.isnan(X)).sum(0); m = np.nanmax(np.where(np.isnan(X), -np.inf, X), 0)
    MAXR[w] = np.where(n >= 25, m, np.nan)
I1 = np.flatnonzero((LUN * JMS >= 1707091200000) & (LUN * JMS < 1767225600000)); I2 = np.flatnonzero((LUN * JMS >= 1767571200000) & (LUN * JMS <= 1789948800000))
def elig(w): return np.flatnonzero(~np.isnan(R[w]) & ~np.isnan(MAXR[w]))
def pond(w, lo, hi):
    P = np.zeros(NP)
    if len(lo) and len(hi): P[list(lo)] = 0.5 / len(lo); P[list(hi)] = -0.5 / len(hi)
    return P
P = np.zeros((NW, NP))
for w in range(NW):
    e = elig(w)
    if len(e) < 10: continue
    q = len(e) // 5; o = e[np.argsort(MAXR[w][e])]; P[w] = pond(w, list(o[:q]), o[-q:])   # long MAX faible, short MAX fort
def perf(P, I):
    rr = np.nan_to_num(R); prev = np.vstack([np.zeros((1, NP)), P[:-1]])
    g = (P * rr).sum(1); fr = TK * np.abs(P - prev).sum(1)
    return (g - fr)[I], g[I], fr[I], (np.where(P > 0, P, 0) * rr).sum(1)[I], (np.where(P < 0, P, 0) * rr).sum(1)[I]
def resume(P, I):
    s, g, f, lo, sh = perf(P, I); cum = np.cumsum(s); rb = np.nan_to_num(R[I, ib])
    return dict(net=float(s.sum()), brut=float(g.sum()), frais=float(f.sum()), jambe_longue=float(lo.sum()), jambe_courte=float(sh.sum()),
                beta_realise=float(np.cov(s, rb)[0, 1] / np.var(rb, ddof=1)),
                sem_pos=float((s > 0).mean()), pire_baisse=float(np.max(np.maximum.accumulate(np.r_[0, cum])[1:] - cum)))
def conservation(I):
    k = []
    for w in I:
        for sg in (1, -1):
            a = set(np.flatnonzero(np.sign(P[w - 1]) == sg)); b = set(np.flatnonzero(np.sign(P[w]) == sg))
            if a and b: k.append(len(a & b) / len(b))
    return float(np.mean(k))
rng = np.random.default_rng(49); out = {}
for nom, I in (("hist", I1), ("2026", I2)):
    r = resume(P, I); kp = conservation(I); tem = []
    for _ in range(1000):
        T = np.zeros((NW, NP)); prev = {1: set(), -1: set()}
        for w in I:
            e = set(elig(w)); nl = int((P[w] > 0).sum()); nsh = int((P[w] < 0).sum()); cote = {}
            if not nl: continue
            for sg, n in ((1, nl), (-1, nsh)):
                pool = e
                g = [x for x in prev[sg] if x in pool and rng.random() < kp][:n]
                pris = set(g) | (cote.get(1, set()) if sg == -1 else set())
                reste = np.array(sorted(pool - pris)); aj = rng.choice(reste, n - len(g), replace=False) if n > len(g) else []
                cote[sg] = set(g) | set(int(x) for x in aj)
            T[w] = pond(w, sorted(cote[1]), np.array(sorted(cote[-1]))); prev = cote
        tem.append(perf(T, I)[0].sum())
    tem = np.array(tem); out[nom] = dict(r, conservation=kp, temoin_moy=float(tem.mean()), temoin_et=float(tem.std()), p=float((tem >= r["net"]).mean()))
    print(nom, {k: round(v, 4) for k, v in out[nom].items()}, flush=True)
a, b = out["hist"], out["2026"]
v = "GAGNE" if a["net"] > 0 and b["net"] > 0 and b["p"] < 0.05 else "NON DÉMONTRÉ" if b["net"] > 0 else "PERD"
out["verdict"] = v; json.dump(out, open("t49.json", "w"), indent=1); print("VERDICT", v)

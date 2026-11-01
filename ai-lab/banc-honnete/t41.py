"""PREREG-41 : momentum transversal hebdo, quintiles (règles : PREREG-41-momentum-transversal-large.md, commit df88b26).
Données construites par t39.py (exécuté jusqu'à la taille, sans son calcul)."""
import json, os, numpy as np
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "t39.py")).read()
src = src.replace("LS = (2, 4, 8, 12)", "LS = (1, 2, 3, 4)"); ns = {"__file__": os.path.abspath("t39.py")}
exec(src[:src.index("TAILLE =")], ns)
R, MOM, LUN, JMS, TK, sym = ns["R"], ns["MOM"], ns["LUN"], ns["JMS"], ns["TK"], ns["sym"]
NW, NP = R.shape
I1 = np.flatnonzero(LUN * JMS < 1767225600000); I2 = np.flatnonzero((LUN * JMS >= 1767571200000) & (LUN * JMS <= 1789948800000))
def eligibles(L, w): return np.flatnonzero(~np.isnan(R[w]) & ~np.isnan(MOM[L][w]))
def regle(L):
    P = np.zeros((NW, NP))
    for w in range(NW):
        e = eligibles(L, w)
        if len(e) < 10: continue
        q = len(e) // 5; o = e[np.argsort(MOM[L][w][e])]
        P[w, o[-q:]] = 0.5 / q; P[w, o[:q]] = -0.5 / q
    return P
def perf(P, I):
    rr = np.nan_to_num(R); prev = np.vstack([np.zeros((1, NP)), P[:-1]])
    g = (P * rr).sum(1); fr = TK * np.abs(P - prev).sum(1)
    lo = (np.where(P > 0, P, 0) * rr).sum(1); sh = (np.where(P < 0, P, 0) * rr).sum(1)
    return (g - fr)[I], g[I], fr[I], lo[I], sh[I]
def resume(P, I):
    s, g, f, lo, sh = perf(P, I); cum = np.cumsum(s); dd = float(np.max(np.maximum.accumulate(np.r_[0, cum])[1:] - cum))
    return dict(net=float(s.sum()), brut=float(g.sum()), frais=float(f.sum()), jambe_longue=float(lo.sum()), jambe_courte=float(sh.sum()),
                sem_pos=float((s > 0).mean()), pire_sem=float(s.min()), pire_baisse=dd)
def conservation(P, I):
    k = []
    for w in I:
        if w == 0: continue
        for sgn in (1, -1):
            a = set(np.flatnonzero(np.sign(P[w - 1]) == sgn)); b = set(np.flatnonzero(np.sign(P[w]) == sgn))
            if a and b: k.append(len(a & b) / len(b))
    return float(np.mean(k))
G = {}; PL = {}
for L in (1, 2, 3, 4):
    PL[L] = regle(L); G[L] = {"2024-25": resume(PL[L], I1), "2026": resume(PL[L], I2)}
    print("L", L, {k: round(v["net"], 4) for k, v in G[L].items()}, flush=True)
Lc = max(G, key=lambda L: G[L]["2024-25"]["net"]); P = PL[Lc]
rng = np.random.default_rng(41); out = {}
for nom, I in (("2024-25", I1), ("2026", I2)):
    kp = conservation(P, I); tem = []
    for _ in range(1000):
        T = np.zeros((NW, NP)); prev = {1: set(), -1: set()}
        for w in I:
            e = set(eligibles(Lc, w)); nl = int((P[w] > 0).sum()); ns_ = int((P[w] < 0).sum())
            if not nl: prev = {1: set(), -1: set()}; continue
            cote = {}
            for sgn, n in ((1, nl), (-1, ns_)):
                garde = [x for x in prev[sgn] if x in e and rng.random() < kp][:n]
                pris = set(garde) | (cote.get(1, set()) if sgn == -1 else set())
                reste = np.array(sorted(e - pris)); ajout = rng.choice(reste, n - len(garde), replace=False) if n > len(garde) else []
                cote[sgn] = set(garde) | set(int(x) for x in ajout)
            for x in cote[1]: T[w, x] = 0.5 / nl
            for x in cote[-1]: T[w, x] = -0.5 / ns_
            prev = cote
        tem.append(perf(T, I)[0].sum())
    tem = np.array(tem); out[nom] = dict(G[Lc][nom], conservation=kp, temoin_moy=float(tem.mean()), temoin_et=float(tem.std()), p=float((tem >= G[Lc][nom]["net"]).mean()))
    print(nom, out[nom], flush=True)
a, b = out["2024-25"], out["2026"]
v = "GAGNE" if a["net"] > 0 and b["net"] > 0 and b["p"] < 0.05 else "NON DÉMONTRÉ" if b["net"] > 0 else "PERD"
res = dict(L_choisi=Lc, grille=G, regle=out, verdict=v, pieces=NP)
json.dump(res, open("t41.json", "w"), indent=1); print("VERDICT", v)

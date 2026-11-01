"""PREREG-44 : facteur taille (règles : PREREG-44-facteur-taille.md, commit c0b6e9a). Prix : construction de t39.py ; volumes : taille/volumes.json."""
import json, os, numpy as np
src = open("t39.py").read(); ns = {"__file__": os.path.abspath("t39.py")}
exec(src[:src.index("TAILLE =")], ns)
R, LUN, JMS, TK, sym = ns["R"], ns["LUN"], ns["JMS"], ns["TK"], ns["sym"]; NW, NP = R.shape; GL = 0.0010
V = json.load(open("taille/volumes.json")); VOL = np.full((NW, NP), np.nan)
for j, s in enumerate(sym):
    d = {int(t) // JMS: v for t, v in V.get(s, [])}
    for w, lu in enumerate(LUN):
        x = [d.get(int(lu) - k) for k in range(1, 31)]
        if all(v is not None for v in x): VOL[w, j] = sum(x)
I1 = np.flatnonzero((LUN * JMS >= 1707091200000) & (LUN * JMS < 1767225600000)); I2 = np.flatnonzero((LUN * JMS >= 1767571200000) & (LUN * JMS <= 1789948800000))
def elig(w): return np.flatnonzero(~np.isnan(R[w]) & ~np.isnan(VOL[w]) & (VOL[w] > 0))
P = np.zeros((NW, NP))
for w in range(NW):
    e = elig(w)
    if len(e) < 10: continue
    q = len(e) // 5; o = e[np.argsort(VOL[w][e])]
    P[w, o[:q]] = 0.5 / q; P[w, o[-q:]] = -0.5 / q          # long les petites, short les grandes
def perf(P, I, gl=GL):
    rr = np.nan_to_num(R); prev = np.vstack([np.zeros((1, NP)), P[:-1]]); dP = np.abs(P - prev)
    longp = (P > 0) | (prev > 0)
    g = (P * rr).sum(1); fr = TK * dP.sum(1) + gl * (dP * longp).sum(1)
    lo = (np.where(P > 0, P, 0) * rr).sum(1); sh = (np.where(P < 0, P, 0) * rr).sum(1)
    return (g - fr)[I], g[I], fr[I], lo[I], sh[I]
def resume(P, I, gl=GL):
    s, g, f, lo, sh = perf(P, I, gl); cum = np.cumsum(s)
    return dict(net=float(s.sum()), brut=float(g.sum()), couts=float(f.sum()), jambe_petites=float(lo.sum()), jambe_grandes=float(sh.sum()),
                sem_pos=float((s > 0).mean()), pire_sem=float(s.min()), pire_baisse=float(np.max(np.maximum.accumulate(np.r_[0, cum])[1:] - cum)))
def conservation(P, I):
    k = []
    for w in I:
        for sg in (1, -1):
            a = set(np.flatnonzero(np.sign(P[w - 1]) == sg)); b = set(np.flatnonzero(np.sign(P[w]) == sg))
            if a and b: k.append(len(a & b) / len(b))
    return float(np.mean(k))
rng = np.random.default_rng(44); out = {}
for nom, I in (("hist", I1), ("2026", I2)):
    r = resume(P, I); kp = conservation(P, I); tem = []
    for _ in range(1000):
        T = np.zeros((NW, NP)); prev = {1: set(), -1: set()}
        for w in I:
            e = set(elig(w)); nl = int((P[w] > 0).sum()); nsh = int((P[w] < 0).sum()); cote = {}
            for sg, n in ((1, nl), (-1, nsh)):
                garde = [x for x in prev[sg] if x in e and rng.random() < kp][:n]
                pris = set(garde) | (cote.get(1, set()) if sg == -1 else set())
                reste = np.array(sorted(e - pris)); aj = rng.choice(reste, n - len(garde), replace=False) if n > len(garde) else []
                cote[sg] = set(garde) | set(int(x) for x in aj)
            for x in cote[1]: T[w, x] = 0.5 / nl
            for x in cote[-1]: T[w, x] = -0.5 / nsh
            prev = cote
        tem.append(perf(T, I)[0].sum())
    tem = np.array(tem); out[nom] = dict(r, sans_glissement=resume(P, I, 0.0)["net"], conservation=kp, temoin_moy=float(tem.mean()), temoin_et=float(tem.std()),
                                       p=float((tem >= r["net"]).mean()), quintile_moy=float((P[I] > 0).sum(1).mean()))
    print(nom, out[nom], flush=True)
a, b = out["hist"], out["2026"]
v = "GAGNE" if a["net"] > 0 and b["net"] > 0 and b["p"] < 0.05 else "NON DÉMONTRÉ" if b["net"] > 0 else "PERD"
out["verdict"] = v; json.dump(out, open("t44.json", "w"), indent=1); print("VERDICT", v)

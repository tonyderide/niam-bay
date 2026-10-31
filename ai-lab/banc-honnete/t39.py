"""PREREG-39 : momentum de séries temporelles hebdomadaire (règles : PREREG-39-momentum-series-hebdo.md, commit 9e5466c).
Données et coupure identiques à t32.py ; jours UTC puis semaines du lundi."""
import glob, json, os, numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(ICI, "../dca-martingale/refait/donnees")
JMS = 86_400_000; TK = 0.0005; LS = (2, 4, 8, 12)
def couper(a, F=48):
    plat = np.convolve(a[:, 2] == a[:, 3], np.ones(F, int), "valid") == F if len(a) >= F else np.zeros(0, bool)
    return a[:np.argmax(plat)] if plat.any() else a
def journalier(a):
    j = (a[:, 0] // JMS).astype(np.int64); k = np.r_[0, np.flatnonzero(np.diff(j)) + 1]; fin = np.r_[k[1:] - 1, len(a) - 1]
    return np.column_stack([j[k], a[k, 1], a[fin, 4]])     # jour (index), ouverture, clôture
univ = set(json.load(open(os.path.join(D, "../univers.json"))))
J0 = 1704067200000 // JMS                                    # 01/01/2024 (lundi)
LUN = np.arange(J0, J0 + 7 * 144, 7); LUN = LUN[LUN * JMS < 1790553600000]   # lundis jusqu'au 28/09/2026 inclus
NW = len(LUN); sym = []
R = []; MOM = {L: [] for L in LS}; SIG = []
for f in sorted(glob.glob(f"{D}/*-1h.npy")):
    s = os.path.basename(f)[:-7]
    if s not in univ: continue
    a = couper(np.load(f))
    if len(a) < 24 * 40: continue
    d = journalier(a); idx = {int(x): i for i, x in enumerate(d[:, 0])}
    o, c = d[:, 1], d[:, 2]; r = np.full(NW, np.nan); sg = np.full(NW, np.nan); mm = {L: np.full(NW, np.nan) for L in LS}
    for w, lu in enumerate(LUN):
        i = idx.get(int(lu))
        if i is None: continue
        i2 = idx.get(int(lu) + 7)
        r[w] = (o[i2] if i2 is not None else c[min(i + 6, len(c) - 1)]) / o[i] - 1
        if i >= 31:
            rj = c[i - 30:i] / c[i - 31:i - 1] - 1; sg[w] = rj.std()
        for L in LS:
            iL = idx.get(int(lu) - 7 * L)
            if iL is not None: mm[L][w] = o[i] / o[iL] - 1
    sym.append(s); R.append(r); SIG.append(sg)
    for L in LS: MOM[L].append(mm[L])
R = np.array(R).T; SIG = np.array(SIG).T; MOM = {L: np.array(v).T for L, v in MOM.items()}
print(len(sym), "pièces,", NW, "semaines", flush=True)
TAILLE = np.minimum(2, 0.04 / np.where(SIG > 0, SIG, np.nan))
def perf(pos, I):
    """pos : semaines × pièces (0 hors jeu). Rendement hebdo du panier = somme(pos×r − frais) / nb en jeu."""
    rr = np.nan_to_num(R); prev = np.vstack([np.zeros((1, pos.shape[1])), pos[:-1]])
    fr = TK * np.abs(pos - prev); g = pos * rr; n = (pos != 0).sum(1)
    sem = np.where(n > 0, (g - fr).sum(1) / np.maximum(n, 1), 0.0)
    bru = np.where(n > 0, g.sum(1) / np.maximum(n, 1), 0.0); fra = np.where(n > 0, fr.sum(1) / np.maximum(n, 1), 0.0)
    return sem[I], bru[I], fra[I], n[I]
def positions(L, sens=None):
    ok = ~np.isnan(R) & ~np.isnan(MOM[L]) & ~np.isnan(TAILLE)
    s = np.sign(np.nan_to_num(MOM[L])) if sens is None else sens
    return np.where(ok, s * np.nan_to_num(TAILLE), 0.0), ok
I1 = np.flatnonzero(LUN * JMS < 1767225600000); I2 = np.flatnonzero((LUN * JMS >= 1767571200000) & (LUN * JMS <= 1789948800000))
def resume(sem, bru, fra, n):
    cum = np.cumsum(sem); dd = np.max(np.maximum.accumulate(np.r_[0, cum])[1:] - cum) if len(cum) else 0
    return dict(net=float(sem.sum()), brut=float(bru.sum()), frais=float(fra.sum()), sem_pos=float((sem > 0).mean()), pire_sem=float(sem.min()), pire_baisse=float(dd), pieces_moy=float(n.mean()))
T = {}
for L in LS:
    p, _ = positions(L); T[L] = {"2024-25": resume(*perf(p, I1)), "2026": resume(*perf(p, I2))}
    print("L", L, {k: round(v["net"], 4) for k, v in T[L].items()}, flush=True)
Lc = max(LS, key=lambda L: T[L]["2024-25"]["net"])
p, ok = positions(Lc)
rng = np.random.default_rng(39); res = {}
for nom, I in (("2024-25", I1), ("2026", I2)):
    net = T[Lc][nom]["net"]; okI = ok[I]; pl = (p[I] > 0).sum() / max(1, (p[I] != 0).sum())
    tem = []
    for _ in range(1000):
        s = np.where(rng.random(p.shape) < pl, 1.0, -1.0); pt = np.where(ok & (p != 0), s * np.nan_to_num(TAILLE), 0.0)
        tem.append(perf(pt, I)[0].sum())
    tem = np.array(tem); res[nom] = dict(T[Lc][nom], part_longs=float(pl), temoin_moy=float(tem.mean()), temoin_et=float(tem.std()), p=float((tem >= net).mean()))
# repères
bh = {}
for nom, I in (("2024-25", I1), ("2026", I2)):
    w0 = I[0]; w1 = I[-1]; alive = ~np.isnan(R[w0])
    cumr = np.nanprod(1 + np.where(np.isnan(R[w0:w1 + 1]), 0, R[w0:w1 + 1]), axis=0) - 1
    bh[nom] = dict(panier=float(cumr[alive].mean()), BTC=float(cumr[sym.index("BTCUSDT")]))
lo = {}
for nom, I in (("2024-25", I1), ("2026", I2)):
    pp, okk = positions(Lc); pp = np.where(pp > 0, pp, 0.0); lo[nom] = resume(*perf(pp, I))
a, b = res["2024-25"], res["2026"]
v = "GAGNE" if a["net"] > 0 and b["net"] > 0 and b["p"] < 0.05 else "NON DÉMONTRÉ" if b["net"] > 0 else "PERD"
out = dict(L_choisi=Lc, grille=T, regle=res, acheter_garder=bh, long_ou_rien=lo, verdict=v, pieces=len(sym))
json.dump(out, open(os.path.join(ICI, "t39.json"), "w"), indent=1); print(json.dumps({k: out[k] for k in ("L_choisi", "regle", "acheter_garder", "long_ou_rien", "verdict")}, indent=1))

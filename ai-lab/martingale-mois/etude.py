"""PREREG-29, étape 1 : tous les réglages sur BTC/ETH/SOL 1 min, mois par mois (capital remis à 1 000 € chaque mois).
Sortie : grille.npz (résultat de chaque réglage sur chaque mois-pièce) + choix.json (réglage figé par famille, choisi sur 2024-2025)."""
import itertools, json, sys, time
import numpy as np
from moteur import *
sys.path.insert(0, "../dca-martingale/refait")
from simu import simu_nb

D = "../dca-martingale/refait/donnees/"
PIECES = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
XS, RS, MODES, BASES = (0.005, 0.01, 0.02, 0.03, 0.05, 0.08), (1.0, 0.5), (0, 1, 2, 3), (1.0, 2.0, 5.0, 10.0, 20.0)
NOM_MODE = {0: "long", 1: "short", 2: "inversé après perte", 3: "inversé à chaque trade"}
INF = 1e9


def reglages():
    R = []
    for x, r, md, b in itertools.product(XS, RS, MODES, BASES):
        for m in (2.0, 0.0):
            for k in (3, 5, 8, INF): R.append((1, x, r, md, m, k, b))
        for um in (10, INF): R.append((2, x, r, md, um, 0, b))
        for jm in (6, 10, INF): R.append((3, x, r, md, jm, 0, b))
        for li in (0, 1):
            for L in (10, 20, INF): R.append((4, x, r, md, li, L, b))
        for k in (2, 3, 4): R.append((5, x, r, md, k, 0, b))
    for d, tp, t, n, s in itertools.product((0.01, 0.02, 0.03), (0.01, 0.015, 0.025), (0.005, 0.01), (3, 5), (0.03, 0.08)): R.append((6, d, tp, t, n, s, 0))
    TR = [(s, a, t) for s in (0.01, 0.02, 0.03, 0.05) for a in (0.005, 0.01, 0.02) for t in (0.005, 0.01) if t <= a]
    for (s, a, t), b in itertools.product(TR, (2.0, 5.0, 10.0)):
        R.append((7, s, a, t, 1.0, INF, b))
        for m, k in itertools.product((1.5, 2.0, 3.0), (2, 4, 6, INF)): R.append((7, s, a, t, m, k, b))
    return R


def tranches(a):
    """liste de 33 tranches mensuelles (None si moins de 168 h de données)"""
    if len(a) < 200: return [None] * 33
    idx = np.searchsorted(a[:, 0], MOIS); bar_h = float(np.median(np.diff(a[:200, 0]))) / 3.6e6
    return [a[idx[k]:idx[k + 1]] if (idx[k + 1] - idx[k]) * bar_h >= 168 else None for k in range(33)]


def chaines(x_, opt=0):
    """toutes les chaînes de trades d'une tranche"""
    o, h, l, c = (np.ascontiguousarray(x_[:, j]) for j in (1, 2, 3, 4)); out = np.empty((len(o) + 1, 4)); C = {}
    for x, r, md in itertools.product(XS, RS, MODES):
        m = chaine_tpsl(o, h, l, c, x, r, md, opt, out); C[("tpsl", x, r, md)] = out[:m, 0].copy()
    for s, a, t in {(g[1], g[2], g[3]) for g in REG if g[0] == 7}:
        m = chaine_trail(o, h, l, c, s, t, a, out); C[("trail", s, a, t)] = out[:m, 0].copy()
    return C


def resultat_mois(g, C, x_):
    """(résultat € du mois, ruine, nb trades) pour un réglage g sur une tranche (chaînes C déjà calculées)"""
    f = g[0]
    if f == 6:
        cy, tot = simu_nb(*(np.ascontiguousarray(x_[:, j]) for j in (1, 2, 3, 4)), g[1], g[2], g[3], g[4], g[5], 2.0)
        return float(cy[:, 0].sum() / tot * 1000), 0, len(cy)
    if f == 7:
        ret = C[("trail", g[1], g[2], g[3])]; cap, ru, n = miser(ret, g[1], 7, g[4], g[5], 0, g[6], 1.0, 1000.0)
    else:
        x, r = g[1], g[2]; ret = C[("tpsl", x, r, g[3])]; wu = (r * x - TK - MK * (1 + r * x)) / x
        cap, ru, n = miser(ret, x, f, g[4], g[5], 0, g[6], wu, 1000.0)
    return cap - 1000.0, ru, n


def decrire(g):
    f = g[0]; k = lambda v: "∞" if v >= INF else int(v)
    if f == 6: return f"grille DCA : 1er OS à −{g[1]:.0%}, TP +{g[2]:.1%}, trailing {g[3]:.1%}, {g[4]} OS, SL {g[5]:.0%} sous le dernier OS"
    if f == 7: return f"Tony : SL {g[1]:.1%}, trailing {g[3]:.1%} dès +{g[2]:.1%}, inversion après perte, ×{g[4]} après perte, plafond {k(g[5])}, base {g[6]:.0f} €"
    t = f"SL {g[1]:.1%} TP {g[1] * g[2]:.2%}, {NOM_MODE[g[3]]}, base {g[6]:.0f} €, "
    if f == 1: return "doublement : " + t + ("récupération exacte" if g[4] == 0 else f"×{g[4]:.0f}") + f", plafond {k(g[5])} pertes"
    if f == 2: return "d'Alembert : " + t + f"u max {k(g[4])}"
    if f == 3: return "Fibonacci : " + t + f"j max {k(g[4])}"
    if f == 4: return "Labouchère : " + t + ("liste 1-2-3" if g[4] == 0 else "liste 1-1-1-1") + f", longueur max {k(g[5])}"
    return "Paroli : " + t + f"retour à la base après {g[4]} gains"


REG = reglages()
FAM = {1: "doublement classique", 2: "d'Alembert", 3: "Fibonacci", 4: "Labouchère", 5: "anti-martingale (Paroli)", 6: "grille DCA", 7: "règle de Tony"}
if __name__ == "__main__":
    print(len(REG), "réglages", {FAM[f]: sum(g[0] == f for g in REG) for f in FAM}, flush=True)
    RES = np.full((len(REG), 3, 33), np.nan); RU = np.zeros((len(REG), 3, 33), np.int8); NT = np.zeros((len(REG), 3, 33), np.int32)
    t0 = time.time()
    for p, s in enumerate(PIECES):
        a = couper(np.load(D + f"{s}-1m.npy"), 2880); T = tranches(a)
        for k, x_ in enumerate(T):
            if x_ is None: continue
            C = chaines(x_)
            for q, g in enumerate(REG): RES[q, p, k], RU[q, p, k], NT[q, p, k] = resultat_mois(g, C, x_)
        print(s, f"{time.time() - t0:.0f} s", flush=True)
    np.savez_compressed("grille.npz", RES=RES, RU=RU, NT=NT, REG=np.array(REG, dtype=float))
    choix = {}
    for f in FAM:
        q_ = [q for q, g in enumerate(REG) if g[0] == f]
        sc = {q: (float((RES[q, :, :24] > 0).mean()), float(np.nanmean(RES[q, :, :24]))) for q in q_}
        cand = [q for q in q_ if sc[q][1] > 0]; signale = not cand
        best = sorted(cand or q_, key=lambda q: (-sc[q][0], -sc[q][1]))
        choix[FAM[f]] = {"fige": REG[best[0]], "texte": decrire(REG[best[0]]), "aucun_candidat_moyenne_positive": signale, "candidats": len(cand), "reglages": len(q_),
                         "part_mois_pos_24_25": sc[best[0]][0], "moyenne_24_25": sc[best[0]][1],
                         "top5": [[decrire(REG[q]), sc[q][0], round(sc[q][1], 2), float((RES[q, :, 24:] > 0).mean()), round(float(np.nanmean(RES[q, :, 24:])), 2)] for q in best[:5]],
                         "meilleure_part_24_25_tous_reglages": max(sc[q][0] for q in q_)}
        print(FAM[f], json.dumps(choix[FAM[f]], ensure_ascii=False), flush=True)
    json.dump(choix, open("choix.json", "w"), indent=1, ensure_ascii=False, default=float)

"""PREREG-28 : SL fixe au départ, trailing dès qu'on gagne. Règles : ../banc-honnete/PREREG-28-sl-fixe-puis-trailing.md
Données : ../dca-martingale/refait/donnees (coupées au retrait). python etude.py [1h|5m]"""
import glob, itertools, json, os, sys, datetime as dt
import numpy as np
from numba import njit
sys.path.insert(0, "../dca-martingale/refait")
TK = 0.0005; IV = sys.argv[1] if len(sys.argv) > 1 else "1h"
ms = lambda a, m, j: int(dt.datetime(a, m, j, tzinfo=dt.timezone.utc).timestamp() * 1000)
REGLAGE, JUGEMENT = (ms(2024, 1, 1), ms(2026, 1, 1)), (ms(2026, 1, 1), ms(2026, 10, 1))
GRILLE = list(itertools.product((0.01, 0.02, 0.03, 0.05, 0.08), (0.005, 0.01, 0.02, 0.03, 0.05), (0.001, 0.01)))


def couper(a, F=48):
    plat = np.convolve(a[:, 2] == a[:, 3], np.ones(F, int), "valid") == F if len(a) >= F else np.zeros(0, bool)
    return a[:np.argmax(plat)] if plat.any() else a


@njit(cache=True)
def simuler(o, h, l, c, s, t, a, sens, out):
    """sens +1 long, -1 short. Pour le short on travaille sur le prix inversé : même code, même pessimisme. out[m] = (rendement net, i entrée, i sortie, px entrée, px sortie)"""
    T = len(o); i = 0; m = 0
    while i < T:
        e = o[i]; i0 = i; sl = e * (1 - s * sens); actif = False; pic = 0.0
        while True:
            px = -1.0
            hi = h[i] if sens > 0 else l[i]; lo = l[i] if sens > 0 else h[i]; op = o[i]
            stop = sl
            if actif:
                ts = pic * (1 - t * sens)
                stop = max(sl, ts) if sens > 0 else min(sl, ts)
            if (lo - stop) * sens <= 0:                                   # stop touché (pessimiste : avant tout)
                px = min(op, stop) if sens > 0 else max(op, stop)
            elif actif:
                pic = max(pic, hi) if sens > 0 else min(pic, hi)
            elif (hi - e * (1 + a * sens)) * sens >= 0:
                actif = True; pic = hi
            if px < 0 and i == T - 1: px = c[i]
            if px >= 0:
                r = sens * (px / e - 1) - TK - TK * px / e
                out[m, 0] = r; out[m, 1] = i0; out[m, 2] = i; out[m, 3] = e; out[m, 4] = px; m += 1; break
            i += 1
        i += 1
    return m


def lancer(x, cfg, sens):
    out = np.empty((len(x) + 1, 5)); m = simuler(x[:, 1], x[:, 2], x[:, 3], x[:, 4], *cfg, sens, out); return out[:m]


def tranche(a, per):
    a = a[(a[:, 0] >= per[0]) & (a[:, 0] < per[1])]; return a if len(a) > 24 else None


def melanger(x, rng):
    """bougies tirées dans un ordre aléatoire, forme relative à l'ouverture gardée, prix recollés bout à bout"""
    k = rng.permutation(len(x)); o, h, l, c = x[k, 1], x[k, 2], x[k, 3], x[k, 4]
    rc = c / o; ro = np.r_[1.0, x[1:, 1] / x[:-1, 4]][rng.permutation(len(x))]
    no = np.empty(len(x)); no[0] = x[0, 1]
    for i in range(1, len(x)): no[i] = no[i - 1] * rc[i - 1] * ro[i]
    y = np.empty_like(x); y[:, 0] = x[:, 0]; y[:, 1] = no; y[:, 2] = h / o * no; y[:, 3] = l / o * no; y[:, 4] = rc * no; return y


DON = {os.path.basename(f)[:-len(IV) - 5]: couper(np.load(f)) for f in sorted(glob.glob(f"../dca-martingale/refait/donnees/*-{IV}.npy"))}
if IV == "1h":
    out = {}
    for sens, nom in ((1, "long"), (-1, "short")):
        P1 = {s: tranche(a, REGLAGE) for s, a in DON.items()}; P1 = {s: x for s, x in P1.items() if x is not None}
        regl = {str(g): float(np.mean([lancer(x, g, sens)[:, 0].sum() for x in P1.values()])) for g in GRILLE}
        fige = max(GRILLE, key=lambda g: regl[str(g)])
        P2 = {s: tranche(a, JUGEMENT) for s, a in DON.items()}; P2 = {s: x for s, x in P2.items() if x is not None}
        R = {s: lancer(x, fige, sens) for s, x in P2.items()}; v = np.array([r[:, 0].sum() for r in R.values()])
        tr = np.concatenate([r[:, 0] for r in R.values()]); n_tr = len(tr)
        bh = float(np.mean([x[-1, 4] / x[0, 1] * (1 - TK) ** 2 - 1 for x in P2.values()])) if sens > 0 else 0.0
        rng = np.random.default_rng(28); hasard = []
        for _ in range(200): hasard.append(np.mean([lancer(melanger(x, rng), fige, sens)[:, 0].sum() for x in P2.values()]))
        hasard = np.array(hasard); p = float((hasard >= v.mean()).mean())
        frais = n_tr * 2 * TK; brut = v.sum() + frais
        b = {"fige": str(fige), "reglage_2024_2025_meilleur": round(regl[str(fige)], 4), "reglages_positifs_2024_2025": sum(x > 0 for x in regl.values()),
             "pieces": len(v), "rend_moyen_2026": round(v.mean(), 4), "pieces_positives": int((v > 0).sum()), "trades": n_tr,
             "trades_gagnants": round(float((tr > 0).mean()), 4), "gain_moyen": round(float(tr[tr > 0].mean()), 4), "perte_moyenne": round(float(tr[tr <= 0].mean()), 4),
             "temoin_a": round(bh, 4), "hasard_moyen": round(float(hasard.mean()), 4), "hasard_ecart_type": round(float(hasard.std()), 4), "p": p,
             "gains_bruts_totaux": round(brut, 2), "frais_totaux": round(frais, 2)}
        crit = [b["rend_moyen_2026"] > 0, b["rend_moyen_2026"] > bh, p < 0.05, brut > frais and b["pieces_positives"] >= 3]
        b["criteres"] = crit; b["verdict"] = "GAGNE" if all(crit) else ("NON DÉMONTRÉ" if crit[0] else "PERD")
        b["tous_2026"] = {str(g): round(float(np.mean([lancer(x, g, sens)[:, 0].sum() for x in P2.values()])), 4) for g in GRILLE}
        b["reglages_positifs_2026"] = sum(x > 0 for x in b["tous_2026"].values())
        # journal vérifiable : les trades BTC 2026
        x = P2["BTCUSDT"]; jt = lancer(x, fige, sens)
        b["btc_trades"] = [[str(np.datetime64(int(x[int(r[1]), 0]), "ms").astype("datetime64[m]")), round(r[3], 1), str(np.datetime64(int(x[int(r[2]), 0]), "ms").astype("datetime64[m]")), round(r[4], 1), round(r[0] * 100, 2)] for r in jt]
        out[nom] = b; print(nom, {k: w for k, w in b.items() if k not in ("tous_2026", "btc_trades")}, flush=True)
    json.dump(out, open("resultats-1h.json", "w"), indent=1, default=lambda z: z.item())
else:
    r1 = json.load(open("resultats-1h.json")); D1 = {s: couper(np.load(f"../dca-martingale/refait/donnees/{s}-1h.npy")) for s in DON}
    for nom, sens in (("long", 1), ("short", -1)):
        g = eval(r1[nom]["fige"])
        for s in DON: print(nom, s, f"1h {lancer(tranche(D1[s], JUGEMENT), g, sens)[:, 0].sum():+.2%}  5m {lancer(tranche(DON[s], JUGEMENT), g, sens)[:, 0].sum():+.2%}")

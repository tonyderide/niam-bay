"""PREREG-24 : martingale DCA (ordres de sécurité ×2) + trailing stop + SL. Règles : ../banc-honnete/PREREG-24-dca-martingale.md
python etude.py [1h|5m]"""
import glob, itertools, json, os, sys
import numpy as np
from numba import njit

ICI = os.path.dirname(os.path.abspath(__file__)); IV = sys.argv[1] if len(sys.argv) > 1 else "1h"
TK, MK = 0.0005, 0.0002
P1 = (1704067200000, 1767225600000)  # 2024-01-01 → 2026-01-01 (réglage)
P2 = (1767225600000, 1790812800000)  # 2026-01-01 → 2026-10-01 (jugement)


@njit(cache=True)
def simuler(o, h, l, c, d, tp, tr, n, s, mult):
    """renvoie pnl total (en unités de mise de base), frais totaux, nb cycles, nb gagnants, pire cycle"""
    tailles = np.empty(n + 1); cum = np.empty(n)
    for j in range(n + 1): tailles[j] = mult ** j
    e = d
    for j in range(n):
        cum[j] = e if j == 0 else cum[j - 1] + e
        e *= 1.5
    pnl = 0.0; frais = 0.0; ncy = 0; ngain = 0; pire = 0.0
    en = False; i = 0; T = len(o)
    qte = 0.0; depense = 0.0; fcy = 0.0; k = 0; arme = False; pic = 0.0; p0 = 0.0
    while i < T:
        if not en:
            p0 = o[i]; qte = tailles[0] / p0; depense = tailles[0]; fcy = tailles[0] * TK; k = 0; arme = False; pic = 0.0; en = True
        sortie = -1.0
        moy = depense / qte
        # 1. SL (tous les OS exécutés)
        if k == n:
            slp = p0 * (1 - cum[n - 1]) * (1 - s)
            if l[i] <= slp: sortie = min(o[i], slp)
        rempli = False
        if sortie < 0:
            # 2. ordres de sécurité
            while k < n and l[i] <= p0 * (1 - cum[k]):
                px = min(o[i], p0 * (1 - cum[k])); q = tailles[k + 1] / px
                qte += q; depense += tailles[k + 1]; fcy += tailles[k + 1] * MK; k += 1; rempli = True; arme = False  # nouveau prix moyen : le trailing se réarme
            if rempli and k == n:  # SL dans la même bougie (pessimiste)
                slp = p0 * (1 - cum[n - 1]) * (1 - s)
                if l[i] <= slp: sortie = slp
            moy = depense / qte
        if sortie < 0 and not rempli:
            # 3. trailing
            if arme:
                st = pic * (1 - tr)
                if l[i] <= st: sortie = min(o[i], st)
                else: pic = max(pic, h[i])
            elif h[i] >= moy * (1 + tp):
                arme = True; pic = h[i]
        if sortie < 0 and i == T - 1: sortie = c[i]  # fin des données / retrait : au dernier prix
        if sortie >= 0:
            prod = qte * sortie; fcy += prod * TK; g = prod - depense - fcy
            pnl += g; frais += fcy; ncy += 1
            if g > 0: ngain += 1
            if g < pire: pire = g
            en = False
        i += 1
    return pnl, frais, ncy, ngain, pire


def charger(s, a, b):
    x = np.load(os.path.join(ICI, "data", f"{s}-{IV}.npy"))
    if len(x) == 0: return None
    if x[0, 0] > 1e14: x[:, 0] /= 1000  # microsecondes éventuelles
    x = x[(x[:, 0] >= a) & (x[:, 0] < b)]
    return x if len(x) > 24 else None


GRILLE = list(itertools.product((0.01, 0.02, 0.03), (0.01, 0.015, 0.025), (0.005, 0.01), (3, 5), (0.03, 0.08)))
CLASSIQUE = (0.02, 0.015, 0.005, 5, 0.08)


def lancer(cfg, per, syms, mult=2.0):
    d, tp, tr, n, s = cfg; cap = sum(mult ** j for j in range(n + 1)); R = {}
    for sy in syms:
        x = charger(sy, *per)
        if x is None: continue
        p, f, ncy, ng, pire = simuler(x[:, 1], x[:, 2], x[:, 3], x[:, 4], d, tp, tr, n, s, mult)
        R[sy] = {"rend": p / cap, "frais": f / cap, "cycles": ncy, "gagnants": ng, "pire": pire / cap,
                 "bh": x[-1, 4] / x[0, 1] * (1 - TK) ** 2 - 1}
    return R


def resume(R):
    v = [r["rend"] for r in R.values()]; ncy = sum(r["cycles"] for r in R.values()); ng = sum(r["gagnants"] for r in R.values())
    gains = sum(max(0, r["rend"]) for r in R.values())
    return {"pieces": len(v), "rend_moyen": round(float(np.mean(v)), 4), "rend_median": round(float(np.median(v)), 4), "pieces_positives": sum(x > 0 for x in v),
            "cycles": ncy, "taux_cycles_gagnants": round(ng / max(1, ncy), 4), "pire_cycle": round(min(r["pire"] for r in R.values()), 4),
            "frais_moyens": round(float(np.mean([r["frais"] for r in R.values()])), 4), "gains_nets_totaux": round(float(sum(v)), 3),
            "frais_totaux": round(float(sum(r["frais"] for r in R.values())), 3), "bh_moyen": round(float(np.mean([r["bh"] for r in R.values()])), 4)}


if __name__ == "__main__":
    syms = sorted(os.path.basename(f)[:-len(f"-{IV}.npy")] for f in glob.glob(os.path.join(ICI, "data", f"*-{IV}.npy")))
    if IV == "1h":
        out = {"reglage_2024_2025": {}}
        for cfg in GRILLE: out["reglage_2024_2025"][str(cfg)] = resume(lancer(cfg, P1, syms))
        best = max(GRILLE, key=lambda g: out["reglage_2024_2025"][str(g)]["rend_moyen"]); out["fige"] = str(best)
        for nom, cfg in (("jugement_2026", best), ("classique_2026", CLASSIQUE)):
            R = lancer(cfg, P2, syms); Rb = lancer(cfg, P2, syms, mult=1.0); out[nom] = resume(R)
            n = cfg[3]; out[nom]["temoin_b_sans_martingale"] = round(float(np.mean([r["rend"] for r in Rb.values()])), 4)  # rendement du capital réservé : indépendant de l'échelle
            out[nom + "_par_piece"] = {k: round(v["rend"], 4) for k, v in sorted(R.items(), key=lambda kv: kv[1]["rend"])}
        out["classique_2024_2025"] = out["reglage_2024_2025"][str(CLASSIQUE)]
        json.dump(out, open(os.path.join(ICI, "resultats-1h.json"), "w"), indent=1)
        for k in ("fige", "classique_2024_2025", "jugement_2026", "classique_2026"): print(k, out[k])
        pos = sum(v["rend_moyen"] > 0 for v in out["reglage_2024_2025"].values()); print("réglages positifs 2024-2025 :", pos, "/", len(GRILLE))
    else:
        cfg = eval(json.load(open(os.path.join(ICI, "resultats-1h.json")))["fige"])
        print({sy: round(r["rend"], 4) for sy, r in lancer(cfg, P2, syms).items()})

"""Refait à neuf : grille 72 réglages sur 2024-2025, réglage figé jugé une fois sur 2026, témoins, critères de PREREG-24.
python etude.py        (1 h)       python etude.py 5m   (contrôle d'artefact BTC/ETH/SOL)"""
import glob, itertools, json, os, sys, datetime as dt
import numpy as np
from simu import simu_nb, TAKER
IV = sys.argv[1] if len(sys.argv) > 1 else "1h"
ms = lambda a, m, j: int(dt.datetime(a, m, j, tzinfo=dt.timezone.utc).timestamp() * 1000)
REGLAGE, JUGEMENT = (ms(2024, 1, 1), ms(2026, 1, 1)), (ms(2026, 1, 1), ms(2026, 10, 1))
GRILLE = list(itertools.product((0.01, 0.02, 0.03), (0.01, 0.015, 0.025), (0.005, 0.01), (3, 5), (0.03, 0.08)))
CLASSIQUE = (0.02, 0.015, 0.005, 5, 0.08)
FIGE = 48  # bougies d'affilée avec haut == bas : la pièce est retirée (Binance continue d'archiver un prix figé, et réutilise parfois le nom : LIT)


def couper(a):
    """Coupe la série à la première période figée = retrait de la cote (règle PREREG-24 : sortie au dernier prix connu)."""
    if len(a) < FIGE: return a
    plat = np.convolve(a[:, 2] == a[:, 3], np.ones(FIGE, int), "valid") == FIGE
    return a[:np.argmax(plat)] if plat.any() else a


DON = {os.path.basename(f)[:-len(IV) - 5]: couper(np.load(f)) for f in sorted(glob.glob(f"donnees/*-{IV}.npy"))}


def tranche(a, per):
    a = a[(a[:, 0] >= per[0]) & (a[:, 0] < per[1])]
    return a if len(a) > 24 else None


def piece(a, cfg, mult=2.0):
    cy, cap = simu_nb(a[:, 1], a[:, 2], a[:, 3], a[:, 4], *cfg, mult)
    g = cy[:, 0]
    return {"rend": g.sum() / cap, "frais": cy[:, 1].sum() / cap, "cycles": len(g), "gagnants": int((g > 0).sum()),
            "pire": g.min() / cap, "pertes_sl": int((g / cap < -0.05).sum()), "bh": a[-1, 4] / a[0, 1] * (1 - TAKER) ** 2 - 1}


def univers(cfg, per, mult=2.0):
    R = {}
    for s, a in DON.items():
        x = tranche(a, per)
        if x is not None: R[s] = piece(x, cfg, mult)
    return R


def bilan(R):
    v = np.array([r["rend"] for r in R.values()]); cy = sum(r["cycles"] for r in R.values())
    return {"pieces": len(v), "rend_moyen": round(v.mean(), 4), "rend_median": round(float(np.median(v)), 4), "pieces_positives": int((v > 0).sum()),
            "cycles": cy, "cycles_gagnants": round(sum(r["gagnants"] for r in R.values()) / cy, 4), "cycles_perte_plus_5pc": sum(r["pertes_sl"] for r in R.values()),
            "pire_cycle": round(min(r["pire"] for r in R.values()), 4), "gains_nets_totaux": round(v.sum(), 3),
            "gains_bruts_totaux": round(v.sum() + sum(r["frais"] for r in R.values()), 3), "frais_totaux": round(sum(r["frais"] for r in R.values()), 3),
            "acheter_garder_moyen": round(float(np.mean([r["bh"] for r in R.values()])), 4)}


if IV == "1h":
    regl = {str(g): bilan(univers(g, REGLAGE)) for g in GRILLE}
    fige = max(GRILLE, key=lambda g: regl[str(g)]["rend_moyen"])
    out = {"reglage_2024_2025": regl, "fige": str(fige), "positifs_2024_2025": sum(b["rend_moyen"] > 0 for b in regl.values())}
    for nom, g in (("jugement_2026", fige), ("classique_2026", CLASSIQUE)):
        R = univers(g, JUGEMENT); b = bilan(R)
        b["temoin_b_sans_martingale"] = round(float(np.mean([r["rend"] for r in univers(g, JUGEMENT, 1.0).values()])), 4)
        out[nom] = b; out[nom + "_par_piece"] = {s: round(r["rend"], 4) for s, r in sorted(R.items(), key=lambda kv: kv[1]["rend"])}
    tous = {str(g): bilan(univers(g, JUGEMENT))["rend_moyen"] for g in GRILLE}
    out["tous_2026"] = tous; out["positifs_2026"] = sum(v > 0 for v in tous.values()); out["mediane_2026"] = float(np.median(list(tous.values())))
    j = out["jugement_2026"]
    crit = {"rend>0": j["rend_moyen"] > 0, ">acheter_garder": j["rend_moyen"] > j["acheter_garder_moyen"], ">sans_martingale": j["rend_moyen"] > j["temoin_b_sans_martingale"],
            ">=3 pieces gagnantes et gains>frais": j["pieces_positives"] >= 3 and j["gains_nets_totaux"] > 0}
    out["criteres"] = crit
    out["verdict"] = "GAGNE" if all(crit.values()) else ("NON DÉMONTRÉ" if crit["rend>0"] else "PERD")
    json.dump(out, open("resultats-1h.json", "w"), indent=1, default=lambda x: x.item())
    for k in ("fige", "positifs_2024_2025", "verdict", "criteres", "jugement_2026", "classique_2026", "positifs_2026", "mediane_2026"): print(k, out[k])
    print("figé 2024-2025", regl[str(fige)]); print("classique 2024-2025", regl[str(CLASSIQUE)])
else:
    r1 = json.load(open("resultats-1h.json")); D1 = {s: couper(np.load(f"donnees/{s}-1h.npy")) for s in DON}
    for nom, g in (("fige", eval(r1["fige"])), ("classique", CLASSIQUE)):
        for s in DON:
            a = piece(tranche(D1[s], JUGEMENT), g)["rend"]; b = piece(tranche(DON[s], JUGEMENT), g)["rend"]
            ecart = abs(b - a) / max(abs(a), 1e-9)
            print(nom, s, f"1h {a:+.2%}  5m {b:+.2%}", "SUSPECT" if (a > 0) != (b > 0) or ecart > 0.3 else "ok")

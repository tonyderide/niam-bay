"""PREREG-29, étape 2 : jugement unique des réglages figés (choix.json).
J1 = BTC/ETH/SOL 2026 en 1 min (déjà dans grille.npz) ; J2 = les 250 autres pièces en 1 h (pessimiste et optimiste) ;
témoin hasard (minutes mélangées dans chaque mois, 30 mélanges) ; rejeu 1 h de BTC/ETH/SOL ; parcours continu ; tableau mois par mois."""
import glob, json, os, time
import numpy as np
from moteur import *
from etude import REG, FAM, PIECES, D, tranches, decrire, INF
from simu import simu_nb

choix = json.load(open("choix.json")); G = np.load("grille.npz"); RES, RU = G["RES"], G["RU"]
FIG = {f: tuple(choix[n]["fige"]) for f, n in FAM.items()}
QF = {f: REG.index(tuple(g)) for f, g in FIG.items()}


def un_mois(g, x_, opt=0, chemin=None):
    """(résultat €, ruine) d'un réglage sur une tranche, en ne calculant que sa propre chaîne. chemin : liste où ranger le capital après chaque trade"""
    o, h, l, c = (np.ascontiguousarray(x_[:, j]) for j in (1, 2, 3, 4)); f = g[0]
    if f == 6:
        cy, tot = simu_nb(o, h, l, c, g[1], g[2], g[3], int(g[4]), g[5], 2.0); v = cy[:, 0] / tot * 1000
        if chemin is not None: chemin.extend((1000 + np.cumsum(v)).tolist())
        return float(v.sum()), 0
    out = np.empty((len(o) + 1, 4))
    if f == 7: m = chaine_trail(o, h, l, c, g[1], g[3], g[2], out); x, wu = g[1], 1.0
    else:
        m = chaine_tpsl(o, h, l, c, g[1], g[2], int(g[3]), opt, out); x, r = g[1], g[2]; wu = (r * x - TK - MK * (1 + r * x)) / x
    ret = out[:m, 0].copy(); ch = np.zeros(m) if chemin is not None else np.zeros(0)
    cap, ru, n = miser(ret, x, 7 if f == 7 else f, g[4], g[5], 0, g[6], wu, 1000.0, ch)
    if chemin is not None: chemin.extend(ch[:n].tolist())
    return cap - 1000, ru


def resume(v, ru=None):
    v = np.asarray(v, float); v = v[~np.isnan(v)]
    d = {"mois_pieces": int(len(v)), "part_positifs": round(float((v > 0).mean()), 4), "moyenne_e": round(float(v.mean()), 2), "mediane_e": round(float(np.median(v)), 2),
         "pire_mois_e": round(float(v.min()), 1), "meilleur_mois_e": round(float(v.max()), 1), "cumul_e": round(float(v.sum()), 1)}
    if ru is not None: d["ruines"] = int(np.nansum(ru))
    return d


def pire_baisse(ch):
    ch = np.r_[1000.0, np.asarray(ch)]; return float((ch / np.maximum.accumulate(ch) - 1).min())


if __name__ == "__main__":
    t0 = time.time(); O = {}
    AUTRES = sorted(os.path.basename(f)[:-7] for f in glob.glob(D + "*-1h.npy") if os.path.basename(f)[:-7] not in PIECES)
    D1h = {s: tranches(couper(np.load(D + f"{s}-1h.npy"), 48)) for s in AUTRES + PIECES}
    D1m = {s: couper(np.load(D + f"{s}-1m.npy"), 2880) for s in PIECES}; T1m = {s: tranches(D1m[s]) for s in PIECES}
    print(len(AUTRES), "autres pièces", flush=True)
    for f, g in FIG.items():
        q = QF[f]; nom = FAM[f]; b = {"fige": decrire(g)}
        b["choix_2024_2025_3pieces"] = resume(RES[q, :, :24], RU[q, :, :24])
        b["J1_2026_3pieces"] = resume(RES[q, :, 24:], RU[q, :, 24:])
        b["J1_par_piece_2026"] = {s: resume(RES[q, p, 24:]) for p, s in enumerate(PIECES)}
        # J2 : autres pièces, 1 h
        for opt, lab in ((0, "J2_autres_1h_pessimiste"), (1, "J2_autres_1h_optimiste")):
            if f in (6, 7) and opt == 1: continue          # DCA et trailing : ordre de bougie déjà fixé par leur règle (pas de TP limite)
            M = np.full((len(AUTRES), 33), np.nan); R_ = np.zeros((len(AUTRES), 33))
            for i, s in enumerate(AUTRES):
                for k, x_ in enumerate(D1h[s]):
                    if x_ is not None: M[i, k], R_[i, k] = un_mois(g, x_, opt)
            b[lab] = resume(M, R_); b[lab]["pieces_tous_mois_positifs"] = int(sum(np.all(M[i][~np.isnan(M[i])] > 0) and (~np.isnan(M[i])).sum() > 0 for i in range(len(AUTRES))))
            b[lab]["part_positifs_par_mois"] = [round(float((M[:, k][~np.isnan(M[:, k])] > 0).mean()), 3) for k in range(33)]
            b[lab]["moyenne_par_mois"] = [round(float(np.nanmean(M[:, k])), 2) for k in range(33)]
            if opt == 0: b[lab]["2026_seul"] = resume(M[:, 24:], R_[:, 24:])
        # rejeu 1 h de BTC/ETH/SOL (effet de la résolution)
        b["rejeu_1h_3pieces_2026"] = resume([un_mois(g, D1h[s][k])[0] for s in PIECES for k in range(24, 33)])
        # témoin hasard sur J1
        rng = np.random.default_rng(29); H = np.zeros((30, 27))
        for z in range(30):
            j = 0
            for s in PIECES:
                for k in range(24, 33): H[z, j] = un_mois(g, shuffle_mois(T1m[s][k], rng))[0]; j += 1
        vrai = float(np.nanmean(RES[q, :, 24:]))
        b["hasard_J1"] = {"part_positifs": round(float((H > 0).mean()), 4), "moyenne_e": round(float(H.mean()), 2), "pire_mois_e": round(float(H.min()), 1),
                          "p_moyenne": round(float((H.mean(1) >= vrai).mean()), 3), "part_positifs_par_melange_min_max": [round(float((H > 0).mean(1).min()), 3), round(float((H > 0).mean(1).max()), 3)]}
        # parcours continu (1 000 € au 01/2024, sans remise)
        cont = {}
        for s in PIECES:
            x_ = D1m[s][(D1m[s][:, 0] >= MOIS[0]) & (D1m[s][:, 0] < MOIS[-1])]; ch = []
            r, ru = un_mois(g, x_, 0, ch); cont[s] = {"final_e": round(1000 + r, 1), "ruine": int(ru), "pire_baisse": round(pire_baisse(ch), 3)}
        fin = []; rus = 0
        for s in AUTRES:
            seg = [x_ for x_ in D1h[s] if x_ is not None]
            if not seg: continue
            r, ru = un_mois(g, np.concatenate(seg)); fin.append(1000 + r); rus += ru
        cont["autres_1h"] = {"pieces": len(fin), "part_finissant_au_dessus_de_1000": round(float(np.mean(np.array(fin) > 1000)), 3), "final_median_e": round(float(np.median(fin)), 1), "ruines": int(rus)}
        b["continu"] = cont
        # verdicts pré-écrits
        j1, j2 = b["J1_2026_3pieces"], b["J2_autres_1h_pessimiste"]
        b["verdict_tous_les_coups"] = "VRAI" if (j1["part_positifs"] == 1 and j2["part_positifs"] >= 0.95 and j1["ruines"] == 0 and j2["ruines"] == 0) else "FAUX"
        crit = [j1["moyenne_e"] > 0, j2["moyenne_e"] > 0, b["hasard_J1"]["p_moyenne"] < 0.05]
        b["verdict_avantage"] = "GAGNE" if all(crit) else ("NON DÉMONTRÉ" if crit[0] else "PERD")
        b["mois_par_mois_3pieces"] = {s: [None if np.isnan(v) else round(float(v), 1) for v in RES[q, p]] for p, s in enumerate(PIECES)}
        O[nom] = b
        print(nom, f"{time.time() - t0:.0f} s", json.dumps({k: v for k, v in b.items() if k not in ("mois_par_mois_3pieces",) and not k.startswith("J2")}, ensure_ascii=False), flush=True)
        print("   J2 pess", {k: v for k, v in j2.items() if "par_mois" not in k}, "| opt", {k: v for k, v in b.get("J2_autres_1h_optimiste", {}).items() if "par_mois" not in k}, flush=True)
    json.dump(O, open("jugement.json", "w"), indent=1, ensure_ascii=False)

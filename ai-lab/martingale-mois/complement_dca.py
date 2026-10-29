"""COMPLÉMENT hors pré-enregistrement (écrit après avoir vu J2) : la grille DCA figée est la seule famille au résultat moyen > 0 sur les autres pièces.
Est-ce de la structure des prix (rebonds) ou le simple effet de forme ? Même témoin hasard que J1, appliqué à J2 (1 h, 10 mélanges par mois-pièce)."""
import glob, os, json, numpy as np
from moteur import *
from etude import D, PIECES, tranches
from simu import simu_nb
g = (0.03, 0.025, 0.005, 5, 0.08)
P = sorted(os.path.basename(f)[:-7] for f in glob.glob(D + "*-1h.npy") if os.path.basename(f)[:-7] not in PIECES)
f = lambda x_: (lambda cy, tot: cy[:, 0].sum() / tot * 1000)(*simu_nb(*(np.ascontiguousarray(x_[:, j]) for j in (1, 2, 3, 4)), *g, 2.0))
rng = np.random.default_rng(291); V, H = [], []
for s in P:
    for x_ in tranches(couper(np.load(D + f"{s}-1h.npy"), 48)):
        if x_ is None: continue
        V.append(f(x_)); H.append([f(shuffle_mois(x_, rng)) for _ in range(10)])
V, H = np.array(V), np.array(H)
O = {"mois_pieces": len(V), "vrai_moyenne_e": round(float(V.mean()), 2), "vrai_part_positifs": round(float((V > 0).mean()), 4),
     "hasard_moyenne_e": round(float(H.mean()), 2), "hasard_part_positifs": round(float((H > 0).mean()), 4),
     "hasard_moyennes_par_melange": [round(float(m), 2) for m in H.mean(0)], "p": float((H.mean(0) >= V.mean()).mean())}
print(O); json.dump(O, open("complement-dca.json", "w"), indent=1)

"""APRÈS COUP (non pré-enregistré) : les réglages à 27/27 mois positifs en 2026 (choisis en regardant 2026) tiennent-ils sur les autres pièces ?"""
import glob, os, json, numpy as np
from juge import un_mois, resume, D, PIECES
from moteur import couper
from etude import tranches, decrire
P = sorted(os.path.basename(f)[:-7] for f in glob.glob(D + "*-1h.npy") if os.path.basename(f)[:-7] not in PIECES)
T = {s: tranches(couper(np.load(D + f"{s}-1h.npy"), 48)) for s in P}; O = {}
for g in [(1, 0.08, 0.5, 2, 0.0, 1e9, 1.0), (1, 0.08, 0.5, 2, 0.0, 1e9, 5.0)]:
    v, ru = [], []
    for s in P:
        for x_ in T[s]:
            if x_ is not None: r, z = un_mois(g, x_); v.append(r); ru.append(z)
    O[decrire(g)] = resume(v, ru); print(decrire(g), O[decrire(g)])
json.dump(O, open("verif-apres-coup.json", "w"), indent=1, ensure_ascii=False)

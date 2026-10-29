"""contrôle : la grille DCA figée, positive en moyenne sur J2, contre PREREG-24 refait (−0,57 % en 2026, 188 pièces, sans remise mensuelle)"""
import glob, os, numpy as np
from moteur import *
from etude import D, tranches
from simu import simu_nb
g = (0.03, 0.025, 0.005, 5, 0.08)
P = sorted(os.path.basename(f)[:-7] for f in glob.glob(D + "*-1h.npy"))
cont, mens, n = [], [], 0
for s in P:
    a = couper(np.load(D + f"{s}-1h.npy"), 48); a26 = a[(a[:, 0] >= MOIS[24]) & (a[:, 0] < MOIS[33])]
    if len(a26) <= 24: continue
    cy, tot = simu_nb(*(np.ascontiguousarray(a26[:, j]) for j in (1, 2, 3, 4)), *g, 2.0); cont.append(cy[:, 0].sum() / tot)
    m = 0.0
    for k in range(24, 33):
        x_ = a26[(a26[:, 0] >= MOIS[k]) & (a26[:, 0] < MOIS[k + 1])]
        if len(x_) > 1: cy, tot = simu_nb(*(np.ascontiguousarray(x_[:, j]) for j in (1, 2, 3, 4)), *g, 2.0); m += cy[:, 0].sum() / tot
    mens.append(m)
print(len(cont), "pièces 2026 ; sans remise (PREREG-24) :", f"{np.mean(cont):+.2%}", "; avec fermeture forcée chaque fin de mois :", f"{np.mean(mens):+.2%}")
print("pièces positives sans remise", sum(np.array(cont) > 0), "avec", sum(np.array(mens) > 0))

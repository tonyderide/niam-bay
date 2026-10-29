"""Un cycle calculé à la main, pour vérifier que la règle codée est bien celle du texte."""
import numpy as np
from simu import simu_py, simu_nb
#            ouv    haut   bas    clôt
B = np.array([[100,  100,   99,    99.5],   # entrée à 100 (1 unité)
              [99.5, 99.5,  97.9,  98],     # OS1 à 98 (2 unités) ; trailing désarmé
              [98,   99.7,  98,    99.5],   # prix moyen 98,658 -> armement à 99,645 : armé, pic 99,7
              [99.6, 100.5, 99.3,  100],    # stop 99,20 non touché ; pic -> 100,5
              [100.2, 100.3, 99.0, 99.2]])  # stop 100,5 × 0,995 = 99,9975 touché -> sortie
o, h, l, c = B.T
qte = 1 / 100 + 2 / 98; recette = qte * 100.5 * 0.995; frais = 0.0005 + 2 * 0.0002 + recette * 0.0005
attendu = recette - 3 - frais
for f in (simu_py, simu_nb):
    cy, cap = f(o, h, l, c, 0.02, 0.01, 0.005, 3, 0.03, 2.0)
    print(f.__name__, "cycles", len(cy), "gain", round(float(cy[0][0]), 6), "attendu", round(attendu, 6), "capital", cap)
# SL : chute directe de 100 à 85 -> 3 OS (98, 95, 90,5) puis SL à 90,5 × 0,97 = 87,785 dans la même bougie
o, h, l, c = np.array([[100, 100, 85, 86]], float).T
q = 1/100 + 2/98 + 4/95 + 8/90.5; rec = q * 87.785; fr = 0.0005 + 14 * 0.0002 + rec * 0.0005
print("SL : simu", round(float(simu_py(o, h, l, c, 0.02, 0.01, 0.005, 3, 0.03, 2.0)[0][0][0]), 6), "attendu", round(rec - 15 - fr, 6), "soit", round((rec - 15 - fr) / 15 * 100, 1), "% du capital")

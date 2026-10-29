"""contrôles à la main des moteurs"""
import numpy as np
from moteur import *
# bougies : entrée 100 ; TP 1 % ; SL 1 %
o = np.array([100, 100.5, 101.2, 100, 99.5]); h = np.array([100.6, 101.1, 101.3, 100.2, 99.8]); l = np.array([99.9, 100.4, 100.9, 98.8, 99.4]); c = o.copy()
out = np.empty((10, 4))
m = chaine_tpsl(o, h, l, c, 0.01, 1.0, 0, 0, out); print("long :", out[:m].round(5).tolist())
# trade 1 : entrée 100 bougie 0, TP 101 touché bougie 1 -> +1 % - 0,05 % - 0,02 %*1,01 = 0.0092798
# trade 2 : entrée bougie 2 à 101.2 ; TP 102.212 / SL 100.188 ; bougie 3 ouvre 100 < SL -> sortie 100 : -1.1858 % - frais
print(" attendu", 0.01 - 0.0005 - 0.0002 * 1.01, 100 / 101.2 - 1 - 0.0005 - 0.0005 * 100 / 101.2)
m = chaine_tpsl(o, h, l, c, 0.01, 1.0, 2, 0, out); print("inv après perte :", out[:m].round(5).tolist())
# bougie ambiguë
o2 = np.array([100., 100]); h2 = np.array([101.5, 100]); l2 = np.array([98.5, 100]); out2 = np.empty((5, 4))
print("ambigue pess", out2[:chaine_tpsl(o2, h2, l2, o2, .01, 1., 0, 0, out2)][:, 0].copy(), "opt", out2[:chaine_tpsl(o2, h2, l2, o2, .01, 1., 0, 1, out2)][:, 0].copy(), "attendu pess", -0.01 - 0.0005 - 0.0005 * 0.99)
# mises : doublement, 3 pertes puis 1 gain, base 10, x 1 %
ret = np.array([-0.011, -0.011, -0.011, 0.0093])
print("doublement m2:", miser(ret, 0.01, 1, 2.0, 1e6, 0, 10.0, 1, 1000.0), "attendu", 1000 - 1.1 * (10 + 20 + 40) + 0.93 * 80)
wu = (0.01 - 0.0005 - 0.0002 * 1.01) / 0.01
cap = miser(ret, 0.01, 1, 0.0, 1e6, 0, 10.0, wu, 1000.0)[0]; print("récup:", cap, "attendu ~", 1000 + 10 + (-0.011 + 0.0093028) / 0.01 * 0 )
print("dalembert:", miser(ret, 0.01, 2, 1e6, 0, 0, 10.0, 1, 1000.0)[0], "attendu", 1000 - 1.1 * (10 + 20 + 30) + 0.93 * 40)
print("fibo:", miser(ret, 0.01, 3, 1e6, 0, 0, 10.0, 1, 1000.0)[0], "attendu", 1000 - 1.1 * (10 + 10 + 20) + 0.93 * 30)
print("labouchere 123:", miser(ret, 0.01, 4, 0, 1e6, 0, 10.0, 1, 1000.0)[0], "attendu", 1000 - 1.1 * (40 + 50 + 60) + 0.93 * 70)
print("paroli k3:", miser(np.array([0.0093, 0.0093, 0.0093, 0.0093, -0.011]), 0.01, 5, 3, 0, 0, 10.0, 1, 1000.0)[0], "attendu", 1000 + 0.93 * (10 + 20 + 40 + 10) - 1.1 * 20)
print("levier:", miser(np.array([-0.011] * 8), 0.01, 1, 2.0, 1e6, 0, 10.0, 1, 1000.0))

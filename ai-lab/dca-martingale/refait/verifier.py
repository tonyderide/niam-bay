"""Les deux simulateurs doivent coïncider. Données synthétiques (marche aléatoire à grosses mèches) : pas besoin d'attendre le téléchargement."""
import itertools, random, numpy as np
from simu import simu_py, simu_nb
r = np.random.default_rng(7); pires = 0.0; nc = 0
for essai in range(40):
    T = 3000; ret = r.standard_t(3, T) * 0.01 * r.uniform(0.3, 3)
    c = 100 * np.exp(np.cumsum(ret)); o = np.r_[100, c[:-1]] * np.exp(r.normal(0, 0.002, T))
    h = np.maximum(o, c) * np.exp(np.abs(r.normal(0, 0.008, T))); l = np.minimum(o, c) * np.exp(-np.abs(r.normal(0, 0.008, T)))
    for cfg in random.Random(essai).sample(list(itertools.product((0.01, 0.02, 0.03), (0.01, 0.015, 0.025), (0.005, 0.01), (3, 5), (0.03, 0.08))), 6):
        for mult in (2.0, 1.0):
            a, ca = simu_py(o, h, l, c, *cfg, mult); b, cb = simu_nb(o, h, l, c, *cfg, mult)
            assert len(a) == len(b) and ca == cb, (cfg, len(a), len(b))
            pires = max(pires, float(np.abs(np.array(a) - b).max())); nc += len(a)
print("identiques :", nc, "cycles comparés, écart max", pires)

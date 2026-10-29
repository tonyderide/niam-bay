"""Refait à neuf : simulateur réécrit depuis le texte de PREREG-24 (pas depuis etude.py), en deux versions indépendantes :
- simu_py : Python pur, lisible, sert de référence ;
- simu_nb : même règle compilée (numba), pour la grille. Les deux doivent donner exactement les mêmes chiffres (verifier.py).
Choix plus strict que la 1re version : un OS limite se remplit à SON prix, même si la bougie ouvre dessous (l'ancienne version prenait l'ouverture, plus favorable)."""
import numpy as np
from numba import njit
TAKER, MAKER = 0.0005, 0.0002


def paliers(d, n, mult):
    ecart, cumul, niv = d, 0.0, []
    for j in range(n):
        cumul += ecart; niv.append(cumul); ecart *= 1.5
    return np.array(niv), np.array([mult ** j for j in range(n + 1)])


def simu_py(o, h, l, c, d, tp, t, n, s, mult):
    niv, taille = paliers(d, n, mult)
    cycles = []                       # (gain net, frais) de chaque cycle
    i, T = 0, len(o)
    while i < T:
        p0 = o[i]; qte = taille[0] / p0; mise = taille[0]; frais = taille[0] * TAKER
        k = 0; arme = False; pic = 0.0; sl = p0 * (1 - niv[-1]) * (1 - s)
        while True:
            px_sortie = None
            if k == n and l[i] <= sl:                    # 1. SL (tous les OS faits)
                px_sortie = min(o[i], sl)
            else:
                avant = k
                while k < n and l[i] <= p0 * (1 - niv[k]):  # 2. OS limites, à leur prix
                    px = p0 * (1 - niv[k]); qte += taille[k + 1] / px; mise += taille[k + 1]; frais += taille[k + 1] * MAKER; k += 1
                if k > avant:
                    arme = False
                    if k == n and l[i] <= sl: px_sortie = sl     # SL dans la même bougie : pessimiste
                else:                                            # 3. trailing
                    if arme:
                        if l[i] <= pic * (1 - t): px_sortie = min(o[i], pic * (1 - t))
                        else: pic = max(pic, h[i])
                    elif h[i] >= (mise / qte) * (1 + tp):
                        arme = True; pic = h[i]
            if px_sortie is None and i == T - 1: px_sortie = c[i]     # fin de période ou retrait : dernier prix
            if px_sortie is not None:
                recette = qte * px_sortie; frais += recette * TAKER
                cycles.append((recette - mise - frais, frais)); break
            i += 1
        i += 1
    return cycles, taille.sum()


@njit(cache=True)
def _nb(o, h, l, c, niv, taille, tp, t, s, out):
    n = len(niv); i = 0; T = len(o); m = 0
    while i < T:
        p0 = o[i]; qte = taille[0] / p0; mise = taille[0]; frais = taille[0] * TAKER
        k = 0; arme = False; pic = 0.0; sl = p0 * (1 - niv[n - 1]) * (1 - s)
        while True:
            px = -1.0
            if k == n and l[i] <= sl:
                px = min(o[i], sl)
            else:
                avant = k
                while k < n and l[i] <= p0 * (1 - niv[k]):
                    q = p0 * (1 - niv[k]); qte += taille[k + 1] / q; mise += taille[k + 1]; frais += taille[k + 1] * MAKER; k += 1
                if k > avant:
                    arme = False
                    if k == n and l[i] <= sl: px = sl
                else:
                    if arme:
                        if l[i] <= pic * (1 - t): px = min(o[i], pic * (1 - t))
                        else: pic = max(pic, h[i])
                    elif h[i] >= (mise / qte) * (1 + tp):
                        arme = True; pic = h[i]
            if px < 0 and i == T - 1: px = c[i]
            if px >= 0:
                r = qte * px; frais += r * TAKER
                out[m, 0] = r - mise - frais; out[m, 1] = frais; m += 1; break
            i += 1
        i += 1
    return m


def simu_nb(o, h, l, c, d, tp, t, n, s, mult):
    niv, taille = paliers(d, n, mult); out = np.empty((len(o) + 1, 2))
    m = _nb(o, h, l, c, niv, taille.astype(np.float64), tp, t, s, out)
    return out[:m], taille.sum()

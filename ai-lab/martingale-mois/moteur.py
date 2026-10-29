"""PREREG-29 : moteurs. Règles : ../banc-honnete/PREREG-29-martingale-mois-par-mois.md
1) chaînes de trades (prix seulement, indépendantes de la mise) ; 2) systèmes de mise appliqués à la chaîne."""
import datetime as dt
import numpy as np
from numba import njit

TK, MK = 0.0005, 0.0002


def couper(a, F=48):
    plat = np.convolve(a[:, 2] == a[:, 3], np.ones(F, int), "valid") == F if len(a) >= F else np.zeros(0, bool)
    return a[:np.argmax(plat)] if plat.any() else a


def bornes_mois():
    """début (ms UTC) de 01/2024 ... 10/2026 : 34 bornes = 33 mois"""
    b = []
    for y in (2024, 2025, 2026):
        for m in range(1, 13):
            if (y, m) <= (2026, 10): b.append(int(dt.datetime(y, m, 1, tzinfo=dt.timezone.utc).timestamp() * 1000))
    return np.array(b, dtype=np.int64)


MOIS = bornes_mois()
NOMS_MOIS = [f"{2024 + k // 12}-{k % 12 + 1:02d}" for k in range(33)]


@njit(cache=True)
def chaine_tpsl(o, h, l, c, x, r, mode, opt, out):
    """TP = r*x (limite, maker, rempli au toucher), SL = x (stop, taker). mode 0 long, 1 short, 2 inversé après perte, 3 inversé à chaque trade.
    opt = 1 : bougie ambiguë comptée en TP (version optimiste). out[m] = (rendement net / position, sens, i entrée, i sortie)"""
    T = len(o); i = 0; m = 0; sens = 1.0 if mode != 1 else -1.0
    while i < T:
        e = o[i]; i0 = i; tp = e * (1 + sens * r * x); sl = e * (1 - sens * x)
        while True:
            px = -1.0; fe = TK; op = o[i]
            hi = h[i] if sens > 0 else l[i]; lo = l[i] if sens > 0 else h[i]
            if (op - sl) * sens <= 0: px = op
            elif (op - tp) * sens >= 0: px = op; fe = MK
            else:
                hs = (lo - sl) * sens <= 0; ht = (hi - tp) * sens >= 0
                if hs and ht:
                    if opt == 1: px = tp; fe = MK
                    else: px = sl
                elif hs: px = sl
                elif ht: px = tp; fe = MK
            if px < 0 and i == T - 1: px = c[i]
            if px >= 0:
                ret = sens * (px / e - 1) - TK - fe * px / e
                out[m, 0] = ret; out[m, 1] = sens; out[m, 2] = i0; out[m, 3] = i; m += 1
                if mode == 3 or (mode == 2 and ret <= 0): sens = -sens
                break
            i += 1
        i += 1
    return m


@njit(cache=True)
def chaine_trail(o, h, l, c, s, t, a, out):
    """règle de Tony (même logique que sl-trailing/regle_tony.py chaine(), inversion après perte) : SL fixe s, trailing t activé à +a."""
    T = len(o); i = 0; m = 0; sens = 1.0
    while i < T:
        e = o[i]; i0 = i; sl = e * (1 - s * sens); actif = False; pic = 0.0
        while True:
            px = -1.0
            hi = h[i] if sens > 0 else l[i]; lo = l[i] if sens > 0 else h[i]; op = o[i]; stop = sl
            if actif:
                ts = pic * (1 - t * sens); stop = max(sl, ts) if sens > 0 else min(sl, ts)
            if (lo - stop) * sens <= 0: px = min(op, stop) if sens > 0 else max(op, stop)
            elif actif: pic = max(pic, hi) if sens > 0 else min(pic, hi)
            elif (hi - e * (1 + a * sens)) * sens >= 0: actif = True; pic = hi
            if px < 0 and i == T - 1: px = c[i]
            if px >= 0:
                ret = sens * (px / e - 1) - TK - TK * px / e
                out[m, 0] = ret; out[m, 1] = sens; out[m, 2] = i0; out[m, 3] = i; m += 1
                if ret <= 0: sens = -sens
                break
            i += 1
        i += 1
    return m


FIB = np.array([1.0, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765, 10946, 17711, 28657, 46368,
                75025, 121393, 196418, 317811, 514229, 832040, 1346269, 2178309, 3524578, 5702887, 9227465, 14930352, 24157817, 39088169, 63245986, 102334155])


@njit(cache=True)
def miser(ret, x, fam, p1, p2, p3, base, winu, cap0, chemin=np.zeros(0)):
    """applique un système de mise à une chaîne. Mise = risque au SL ; position = mise / x, plafonnée à 10 x capital.
    fam 1 doublement (p1 = m, ou 0 = récupération exacte ; p2 = plafond de pertes) ; 2 d'Alembert (p1 = u max) ; 3 Fibonacci (p1 = j max) ;
    4 Labouchère (p1 = 0 liste [1,2,3] / 1 liste [1,1,1,1] ; p2 = longueur max) ; 5 Paroli (p1 = k gains) ; 7 = 1 (règle de Tony).
    renvoie (capital final, ruine 0/1, nb trades joués)"""
    cap = cap0; st = base; pertes = 0; cumul = 0.0; u = 1.0; j = 0; gains = 0
    lst = np.zeros(4096); n0 = 0; n1 = 0
    if fam == 4:
        if p1 == 0: lst[0] = 1; lst[1] = 2; lst[2] = 3; n1 = 3
        else: lst[0] = 1; lst[1] = 1; lst[2] = 1; lst[3] = 1; n1 = 4
    for q in range(len(ret)):
        if fam == 1 or fam == 7: mise = st
        elif fam == 2: mise = u * base
        elif fam == 3: mise = FIB[j] * base
        elif fam == 4: mise = (lst[n0] + lst[n1 - 1]) * base if n1 - n0 > 1 else lst[n0] * base
        else: mise = st
        mise = min(mise, 10 * cap * x)
        pnl = mise / x * ret[q]; cap += pnl
        if len(chemin) > 0: chemin[q] = cap
        if cap < 50: return cap, 1, q + 1
        g = pnl > 0
        if fam == 1 or fam == 7:
            if g: st = base; pertes = 0; cumul = 0.0
            else:
                pertes += 1; cumul -= pnl
                if pertes >= p2: st = base; pertes = 0; cumul = 0.0
                elif p1 == 0: st = (cumul + base) / winu
                else: st = st * p1
        elif fam == 2:
            if g: u = max(1.0, u - 1)
            else:
                u += 1
                if u > p1: u = 1.0
        elif fam == 3:
            if g: j = max(0, j - 2)
            else:
                j += 1
                if j > p1 or j >= len(FIB): j = 0
        elif fam == 4:
            if g:
                if n1 - n0 > 1: n0 += 1; n1 -= 1
                else: n0 += 1
            else:
                lst[n1] = mise / base; n1 += 1
                if n1 - n0 > p2 or n1 - n0 > 4000: n0 = n1          # liste trop longue : abandon
            if n1 - n0 <= 0:                                          # liste rayée ou abandonnée : nouvelle liste
                n0 = 0
                if p1 == 0: lst[0] = 1; lst[1] = 2; lst[2] = 3; n1 = 3
                else: lst[0] = 1; lst[1] = 1; lst[2] = 1; lst[3] = 1; n1 = 4
            elif n1 >= 4090:                                          # recopie au début
                k = n1 - n0
                for z in range(k): lst[z] = lst[n0 + z]
                n0 = 0; n1 = k
        else:  # Paroli
            if g:
                gains += 1
                if gains >= p1: st = base; gains = 0
                else: st = st * 2
            else: st = base; gains = 0
    return cap, 0, len(ret)


def shuffle_mois(x, rng):
    """bougies d'un mois tirées dans un ordre aléatoire, forme relative à l'ouverture gardée, prix recollés (vectorisé)"""
    n = len(x); k = rng.permutation(n); o, h, l, c = x[k, 1], x[k, 2], x[k, 3], x[k, 4]
    rc = c / o; ro = np.r_[1.0, x[1:, 1] / x[:-1, 4]][rng.permutation(n)]
    f = np.r_[1.0, rc[:-1] * ro[1:]]; no = x[0, 1] * np.cumprod(f)
    y = np.empty_like(x); y[:, 0] = x[:, 0]; y[:, 1] = no; y[:, 2] = h / o * no; y[:, 3] = l / o * no; y[:, 4] = rc * no
    return y

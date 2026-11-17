"""PREREG-77 : les trois règles, minute par minute. Aucune ne regarde le futur : la décision à la minute i n'utilise que
des données closes avant i, l'entrée se fait à l'OUVERTURE d'une bougie postérieure. Coût identique partout (cout = aller-retour)."""
import numpy as np
from numba import njit


@njit(cache=True)
def piste2(sig, o, off, hold, lat, i0, i1, cout, R, E):
    """sig[i] = sens du mouvement du BTC connu à la CLÔTURE de la minute i (0 = rien). Entrée à l'ouverture de i+1+lat,
    sortie à l'ouverture hold minutes plus tard. Une position à la fois. off = décalage du témoin (en minutes)."""
    n = 0; libre = i0; N = len(sig)
    for i in range(i0, i1 - 1 - lat - hold):
        s = sig[(i - off) % N]
        if s != 0 and i + 1 + lat >= libre:
            e = i + 1 + lat; x = e + hold
            R[n] = s * (o[x] / o[e] - 1.0) - cout; E[n] = e; n += 1; libre = x
    return n


@njit(cache=True)
def piste1(flag, stag, o, h, l, c, off, hold, j0, j1, cout, R, E, V):
    """Grille de décision à 5 min (créneau j <-> minute m = 5j). Signal = flag (dette en forte hausse) ET stag (prix calme).
    Puis jusqu'à 24 h d'attente d'une CLÔTURE 1 min hors de la fourchette [bas, haut] des 24 h d'avant le signal ; entrée à
    l'ouverture suivante dans le sens de la sortie ; stop à l'autre bord (testé d'abord, exécuté au stop ou à l'ouverture si
    sauté) ; sinon sortie à l'ouverture hold minutes après l'entrée. V = |mouvement| des 24 h suivant chaque signal.
    Renvoie (nombre de trades, nombre de signaux)."""
    n = 0; ns = 0; libre = 5 * j0; NJ = len(flag)
    for j in range(j0, j1):
        m = 5 * j
        if m < libre or m < 1441: continue
        if not (flag[(j - off) % NJ] and stag[j]): continue
        hi = -1e300; lo = 1e300
        for q in range(m - 1440, m):
            if h[q] > hi: hi = h[q]
            if l[q] < lo: lo = l[q]
        V[ns] = abs(c[m + 1439] / c[m - 1] - 1.0); ns += 1
        libre = m + 1440
        side = 0; e = -1
        for q in range(m, m + 1440):
            if c[q] > hi: side = 1; e = q + 1; break
            if c[q] < lo: side = -1; e = q + 1; break
        if side == 0: continue
        ent = o[e]; stop = lo if side == 1 else hi
        x = e + hold; px = o[x]
        for q in range(e, e + hold):
            if side == 1 and l[q] <= stop:
                px = min(stop, o[q]); x = q; break
            if side == -1 and h[q] >= stop:
                px = max(stop, o[q]); x = q; break
        R[n] = side * (px / ent - 1.0) - cout; E[n] = e; n += 1
        if x + 1 > libre: libre = x + 1
    return n, ns


@njit(cache=True)
def piste3(sig, o, off, hmin, d0, d1, cout, R, E):
    """sig[d] = sens voulu au contrôle de 00:00 UTC du jour d (+1 long, −1 short, 0 rien), connu avec des données <= 23:55.
    Prix d'action = ouverture de la bougie 00:05. Sortie au premier contrôle, hmin jours au moins après l'entrée, où le signal
    n'est plus dans le sens de la position ; sortie forcée au jour d1."""
    n = 0; side = 0; de = 0; ent = 0.0; ND = len(sig)
    for d in range(d0, d1):
        s = sig[(d - off) % ND]; px = o[1440 * d + 5]
        if side != 0 and d - de >= hmin and s != side:
            R[n] = side * (px / ent - 1.0) - cout; E[n] = 1440 * de + 5; n += 1; side = 0
        if side == 0 and s != 0:
            side = s; ent = px; de = d
    if side != 0:
        R[n] = side * (o[1440 * d1 + 5] / ent - 1.0) - cout; E[n] = 1440 * de + 5; n += 1
    return n


@njit(cache=True)
def marche(n, sd, graine, derive):
    """marche au hasard fabriquée : 10 pas par minute, bougies o/h/l/c ; derive[i] = rendement ajouté à la minute i."""
    np.random.seed(graine)
    o = np.empty(n); h = np.empty(n); l = np.empty(n); c = np.empty(n); p = 100.0; s = sd / np.sqrt(10.0)
    for i in range(n):
        o[i] = p; hi = p; lo = p
        for k in range(10):
            p *= np.exp(np.random.normal(0.0, s) + derive[i] / 10.0)
            if p > hi: hi = p
            if p < lo: lo = p
        h[i] = hi; l[i] = lo; c[i] = p
    return o, h, l, c

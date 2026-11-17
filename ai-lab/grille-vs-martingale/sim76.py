"""PREREG-76 : simulateurs minute par minute.
- grille : la grille W5 telle que Martin la joue (code déployé d7ff867, branche retour-avril) — bras A (protection à deux
  branches) et bras B (une seule branche : stop serré, objectif large, depuis le prix courant).
- martingale : la martingale avec inversion de ~/martin/scripts/martingale.py (bras C).
Résultats en dollars (gain cumulé depuis 0), mises fixes (pas de réinvestissement), aucun arrêt « compte vide » dans le moteur :
la ruine se mesure après coup sur la courbe.
Dans une bougie, le chemin est pessimiste pour la position tenue : long -> le bas d'abord, short -> le haut d'abord
(le stop est donc toujours testé avant l'objectif). À plat : ordre habituel selon la couleur de la bougie."""
import numpy as np
from numba import njit

FM, FT = 0.0002, 0.0005                       # frais Kraken : maker 0,02 %, taker 0,05 %
ESP, NL, LEV, MAXLOSS = 0.05, 5, 10.0, 0.15   # W5 : écart 5 %, 5 niveaux, levier 10, vrai stop à -15 % du capital de la paire
WSL, WTP, LSL, LTP = 0.006, 0.025, 0.030, 0.002   # constantes de AutoGridScheduler (d7ff867)
M_SL, M_ACT, M_TRAIL, M_KMAX = 0.05, 0.10, 0.01, 4   # martingale.py


@njit
def grille(t, o, h, l, c, R, DG, cap, bras, dec, prec, force0):
    """cap = capital de la paire (notionnel par niveau = cap*LEV/NL, plafond cap*LEV). bras 0 = A, 1 = B.
    dec = minute du quart d'heure où passe checkSignals. prec >= 0 : taille arrondie à 10^-prec (lots Kraken) ; -1 : pas d'arrondi.
    force0 : grille démarrée à la première minute quel que soit le régime (déploiement manuel).
    Retour : eq (gain cumulé $ à chaque minute, position valorisée à la clôture), cycles (minute, gain, sortie, branche), stats."""
    n = len(o); eq = np.zeros(n)
    N = cap * LEV / NL; CAPX = cap * LEV; f10 = 10.0 ** prec if prec >= 0 else 0.0
    pr = np.zeros(NL); sd = np.zeros(NL); fr = np.zeros(NL, np.int64); al = np.zeros(NL, np.bool_); ro = np.zeros(NL, np.bool_)
    q = 0.0; cash = 0.0; avg = 0.0; on = False; co = False; P = 0.0; s = 0.0; pause = 0
    pact = False; pq = 0.0; psz = 0.0; sl = 0.0; tp = 0.0; pbr = 0
    frais = 0.0; vol = 0.0; nf = 0; nprot = 0; nstop = 0; ndj = 0; ngr = 0
    c0 = 0.0; lastk = 0; lastb = 0
    ci = []; cg = []; ck = []; cb = []
    for i in range(n):
        m15 = (t[i] // 60000) % 15
        if (m15 == dec and i > 0) or (force0 and i == 0):
            act = on
            if act:                                               # 3. protection : reposée si le côté OU la taille a changé
                if q != 0.0 and (not pact or q != pq):
                    C0 = c[i - 1] if i > 0 else o[i]; pact = True; pq = q; psz = abs(q); nprot += 1
                    if q > 0:
                        if bras == 1 or C0 > avg: sl = C0 * (1 - WSL); tp = C0 * (1 + WTP); pbr = 1
                        else: sl = avg * (1 - LSL); tp = avg * (1 + LTP); pbr = 2
                    else:
                        if bras == 1 or C0 < avg: sl = C0 * (1 + WSL); tp = C0 * (1 - WTP); pbr = 1
                        else: sl = avg * (1 + LSL); tp = avg * (1 - LTP); pbr = 2
                elif q == 0.0: pact = False
            if act and DG[i]:                                     # 4. disjoncteur RSI < 25 : grille arrêtée, position et protection laissées
                on = False; co = False; ndj += 1
                for k in range(NL): al[k] = False
            elif not act:
                if (R[i] or (force0 and i == 0)) and (not DG[i]) and i >= pause:   # 6. régime calme : nouvelle grille
                    on = True; co = False; P = o[i]; s = P * ESP; ngr += 1
                    for k in range(NL):
                        pr[k] = P + (k - 1.5) * s; sd[k] = 1.0 if pr[k] < P else -1.0; fr[k] = i; al[k] = True; ro[k] = False
            else:                                                 # 7. régime agité
                if not R[i]:
                    if q != 0.0: co = True
                    else:
                        on = False; co = False
                        for k in range(NL): al[k] = False
                if on and co and q == 0.0:
                    on = False; co = False
                    for k in range(NL): al[k] = False
        pf = o[i]
        if q > 0: basd = True                                     # chemin fixé à l'ouverture de la bougie, selon la position tenue
        elif q < 0: basd = False
        else: basd = c[i] >= o[i]
        for leg in range(3):
            if leg == 0: x = l[i] if basd else h[i]
            elif leg == 1: x = h[i] if basd else l[i]
            else: x = c[i]
            bas = x < pf
            while True:
                best = -1; bp = 0.0; kind = 0
                if on:
                    for k in range(NL):
                        if not al[k] or fr[k] > i: continue
                        if bas and sd[k] > 0 and x < pr[k] and (best < 0 or pr[k] > bp): best = k; bp = pr[k]; kind = 1
                        if (not bas) and sd[k] < 0 and x > pr[k] and (best < 0 or pr[k] < bp): best = k; bp = pr[k]; kind = 1
                if pact and q != 0.0 and q * pq > 0:
                    if bas:
                        if q > 0 and x <= sl and (best < 0 or sl > bp): best = 99; bp = sl; kind = 2
                        if q < 0 and x < tp and (best < 0 or tp > bp): best = 99; bp = tp; kind = 3
                    else:
                        if q > 0 and x > tp and (best < 0 or tp < bp): best = 99; bp = tp; kind = 3
                        if q < 0 and x >= sl and (best < 0 or sl < bp): best = 99; bp = sl; kind = 2
                if best < 0: break
                if kind == 1:
                    k = best; al[k] = False                      # niveau à un coup (reprise sautée : « level exists, one-shot »)
                    sz = N / pr[k]
                    if f10 > 0.0: sz = np.round(sz * f10) / f10
                    if sz <= 0.0: continue
                    dq = sd[k] * sz
                    if ro[k]:
                        if q * dq >= 0: continue
                        dq = np.sign(dq) * min(abs(dq), abs(q))
                    if abs(q + dq) > abs(q) and abs(q + dq) * pr[k] > CAPX * 1.0001: continue
                    neuf = fr[k] == i and ((sd[k] > 0 and pf < pr[k]) or (sd[k] < 0 and pf > pr[k]))
                    fp = pf if neuf else pr[k]; fe = FT if neuf else FM
                else:
                    dq = -np.sign(q) * min(psz, abs(q))
                    if kind == 2: fp = min(sl, pf) if bas else max(sl, pf); fe = FT
                    else: fp = tp; fe = FM
                    pact = False
                if q == 0.0:
                    c0 = cash; lastb = 0
                if q == 0.0 or q * dq > 0: avg = (avg * abs(q) + fp * abs(dq)) / abs(q + dq)
                elif abs(dq) > abs(q): avg = fp
                qa = q
                q += dq; cash -= dq * fp; f = abs(dq) * fp * fe; cash -= f; frais += f; vol += abs(dq) * fp; nf += 1
                if abs(q) < 1e-12: q = 0.0
                if kind != 1: lastb = pbr
                if qa != 0.0 and (q == 0.0 or q * qa < 0):       # position fermée (ou retournée) : un cycle se termine
                    if q == 0.0:
                        ci.append(i); cg.append(cash - c0); ck.append(kind); cb.append(lastb); pact = False
                    else:
                        g = cash + q * fp - c0
                        ci.append(i); cg.append(g); ck.append(kind); cb.append(lastb); c0 = cash + q * fp; lastb = 0
            if on and q != 0.0 and q * (x - avg) < -MAXLOSS * cap:      # vrai stop de GridTradingService : -15 % du capital sur la position
                ps = avg - MAXLOSS * cap / q
                if q * (pf - avg) < -MAXLOSS * cap: ps = pf
                cash += q * ps; f = abs(q) * ps * FT; cash -= f; frais += f; vol += abs(q) * ps; q = 0.0; nstop += 1; nf += 1
                ci.append(i); cg.append(cash - c0); ck.append(4); cb.append(pbr if pact else 0)
                on = False; co = False; pact = False; pause = i + 1440
                for k in range(NL): al[k] = False
                x = ps
            pf = x
        if on and (c[i] > P + 2 * s or c[i] < P - 2 * s):         # recentrage, position gardée, mêmes écarts
            P = c[i]
            for k in range(NL):
                pr[k] = P + (k - 1.5) * s; sd[k] = 1.0 if pr[k] < P else -1.0; fr[k] = i + 1; ro[k] = co
                al[k] = not (co and sd[k] > 0)
        eq[i] = cash + q * c[i]
    if q != 0.0:
        f = abs(q) * c[n - 1] * FT; cash += q * c[n - 1] - f; frais += f; vol += abs(q) * c[n - 1]
        ci.append(n - 1); cg.append(cash - c0); ck.append(5); cb.append(pbr if pact else 0); q = 0.0
        eq[n - 1] = cash
    st = np.array([frais, vol, float(nf), float(nprot), float(nstop), float(ndj), float(ngr)])
    return eq, np.array(ci, np.int64), np.array(cg, np.float64), np.array(ck, np.int64), np.array(cb, np.int64), st


@njit
def martingale(o, h, l, c, sens0, base, lot):
    """martingale.py : position de base `base` $, stop à -5 % de l'entrée, à +10 % stop suiveur à 1 % du meilleur prix (vu une
    fois par minute, à l'ouverture), après une perte : x2 et sens inversé, après un gain ou 4 pertes d'affilée : retour à la base.
    Entrée au marché à l'ouverture de la minute, 2 minutes après la sortie (une minute pour constater, une pour rouvrir).
    lot = True : taille arrondie à l'unité (comme le script sur DOGE)."""
    n = len(o); eq = np.zeros(n)
    cash = 0.0; q = 0.0; ent = 0.0; stop = 0.0; best = 0.0; sens = sens0; niv = 0; pertes = 0; nxt = 0; ce = 0.0
    frais = 0.0; vol = 0.0
    ti = []; tg = []; tn = []; ts = []
    for i in range(n):
        if q == 0.0:
            if i >= nxt:
                px = o[i]; sz = base * 2.0 ** niv / px
                if lot: sz = max(1.0, np.round(sz))
                q = sens * sz; ent = px; best = px; stop = px * (1 - sens * M_SL); ce = cash
                f = sz * px * FT; cash -= f; frais += f; vol += sz * px; cash -= q * px
        else:
            px = o[i]
            best = max(best, px) if sens > 0 else min(best, px)
            if sens * (px / ent - 1) >= M_ACT:
                cible = best * (1 - sens * M_TRAIL)
                if (sens > 0 and cible > stop * 1.0005) or (sens < 0 and cible < stop * 0.9995): stop = cible
        if q != 0.0:
            hit = (sens > 0 and l[i] <= stop) or (sens < 0 and h[i] >= stop)
            if hit:
                fp = min(stop, o[i]) if sens > 0 else max(stop, o[i])
                sz = abs(q); f = sz * fp * FT; cash += q * fp - f; frais += f; vol += sz * fp; q = 0.0
                res = cash - ce
                ti.append(i); tg.append(res); tn.append(niv); ts.append(sens)
                if res > 0: niv = 0; pertes = 0
                else:
                    pertes += 1; sens = -sens
                    if pertes >= M_KMAX: niv = 0; pertes = 0
                    else: niv += 1
                nxt = i + 2
        eq[i] = cash + q * c[i]
    if q != 0.0:
        sz = abs(q); f = sz * c[n - 1] * FT; cash += q * c[n - 1] - f; frais += f; vol += sz * c[n - 1]
        ti.append(n - 1); tg.append(cash - ce); tn.append(niv); ts.append(sens); eq[n - 1] = cash
    st = np.array([frais, vol])
    return eq, np.array(ti, np.int64), np.array(tg, np.float64), np.array(tn, np.int64), np.array(ts, np.float64), st


@njit
def achat(o, c, base):
    """achat simple : `base` $ achetés à la première ouverture, gardés ; frais taker à l'achat et à la vente finale."""
    n = len(o); q = base / o[0]; eq = np.empty(n); f0 = base * FT
    for i in range(n): eq[i] = q * (c[i] - o[0]) - f0
    eq[n - 1] -= q * c[n - 1] * FT
    return eq

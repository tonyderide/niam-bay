"""PREREG-75 : moteurs et définitions des 100 stratégies.
- simg : copie de t73.sim (grille W5 en service), avec paramètres en plus (écart, niveaux, plafond, sens, filtre,
  écart ATR, disjoncteur, protection, garde-fou). Réglages par défaut = t73.sim exactement (témoin W5).
- simd : moteur directionnel sur bougies 1 h (signal sur la bougie close, exécution à l'ouverture suivante, frais taker,
  stops dans la bougie dans l'ordre pessimiste O-B-H-C / O-H-B-C, mêmes garde-fous R+ : 85 % du capital d'entrée, pause 24 h,
  arrêt si cash < 60 %).
Aucune donnée future : tous les indicateurs viennent de bougies 1 h (ou jours) CLOSES avant la bougie de décision."""
import sys, os, numpy as np
from numba import njit
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "banc-honnete"))
from t73 import danger, tendance  # noqa: E402  (mêmes fonctions que le témoin)

FM, FT, CAP0 = 0.0002, 0.0005, 1000.0
WSL, WTP, LSL, LTP = 0.006, 0.025, 0.030, 0.002


# ----------------------------------------------------------------------------------------------- grille
@njit
def simg(t, o, h, l, c, DG, FL, ESP, N, capref, esp, nl, capx, side, off, prot, stopf, bpd, chk):
    n = len(o); ND = (n - 1) // bpd + 1; eqd = np.zeros(ND)
    cap0 = capref; pr = np.zeros(nl); sd = np.zeros(nl); fr = np.zeros(nl, np.int64); al = np.zeros(nl, np.bool_); ro = np.zeros(nl, np.bool_)
    q = 0.0; cash = cap0; avg = 0.0; on = False; co = False; P = 0.0; s = 0.0
    pside = 0.0; tp = 0.0; sl = 0.0; psz = 0.0; capg = cap0; pause = 0
    dead = False; liq = False; tue = False; nf = 0; nst = 0; frais = 0.0; pic = cap0; dd = 0.0
    rec = nl // 2
    for i in range(n):
        if dead:
            eqd[i // bpd] = cash; continue
        if t[i] % chk == 0 and i > 0:
            act = on
            if prot and act and q != 0.0 and pside != np.sign(q):
                C0 = c[i - 1]; pside = np.sign(q); psz = abs(q)
                if q > 0:
                    if C0 > avg: sl = C0 * (1 - WSL); tp = C0 * (1 + WTP)
                    else: sl = avg * (1 - LSL); tp = avg * (1 + LTP)
                else:
                    if C0 < avg: sl = C0 * (1 + WSL); tp = C0 * (1 - WTP)
                    else: sl = avg * (1 + LSL); tp = avg * (1 - LTP)
            if act and DG[i]:
                on = False; co = False
                for k in range(nl): al[k] = False
                act = False
            if (not on) and (not DG[i]) and i >= pause:
                on = True; co = False; P = o[i]
                e_ = esp
                if esp < 0:
                    e_ = ESP[i] if ESP[i] > 0.005 else 0.005
                s = P * e_; capg = cash + q * o[i]
                for k in range(nl):
                    pr[k] = P + (k - off) * s; sd[k] = 1.0 if pr[k] < P else -1.0; fr[k] = i; al[k] = True; ro[k] = False
        pf = o[i]
        for leg in range(3):
            x = ((l[i], h[i], c[i]) if c[i] >= o[i] else (h[i], l[i], c[i]))[leg]
            bas = x < pf
            while True:
                best = -1; bp = 0.0; kind = 0
                if on:
                    for k in range(nl):
                        if not al[k] or fr[k] > i: continue
                        if bas and sd[k] > 0 and x < pr[k] and (best < 0 or pr[k] > bp): best = k; bp = pr[k]; kind = 1
                        if (not bas) and sd[k] < 0 and x > pr[k] and (best < 0 or pr[k] < bp): best = k; bp = pr[k]; kind = 1
                if pside != 0.0 and q != 0.0:
                    if bas:
                        if pside > 0 and x <= sl and (best < 0 or sl > bp): best = 99; bp = sl; kind = 2
                        if pside < 0 and x < tp and (best < 0 or tp > bp): best = 99; bp = tp; kind = 3
                    else:
                        if pside > 0 and x > tp and (best < 0 or tp < bp): best = 99; bp = tp; kind = 3
                        if pside < 0 and x >= sl and (best < 0 or sl < bp): best = 99; bp = sl; kind = 2
                if best < 0: break
                if kind == 1:
                    k = best; al[k] = False
                    dq = sd[k] * N / pr[k]
                    if ro[k]:
                        if q * dq >= 0: continue
                        dq = np.sign(dq) * min(abs(dq), abs(q))
                    if side == 1 and dq < 0:                      # long seul : une vente ne fait que réduire
                        if q <= 0.0: continue
                        dq = -min(abs(dq), q)
                    if side == -1 and dq > 0:                     # short seul : un achat ne fait que réduire
                        if q >= 0.0: continue
                        dq = min(dq, -q)
                    if abs(q + dq) > abs(q) and abs(q + dq) * pr[k] > capx * cap0 * 1.0001: continue
                    if (q == 0.0 or q * dq > 0) and ((dq > 0 and (FL[i] & 1) == 0) or (dq < 0 and (FL[i] & 2) == 0)): continue
                    neuf = fr[k] == i and ((sd[k] > 0 and pf < pr[k]) or (sd[k] < 0 and pf > pr[k]))
                    fp = pf if neuf else pr[k]; fe = FT if neuf else FM
                else:
                    dq = -np.sign(q) * min(psz, abs(q))
                    if kind == 2: fp = min(sl, pf) if bas else max(sl, pf); fe = FT
                    else: fp = tp; fe = FM
                    pside = 0.0 if abs(q + dq) < 1e-12 else pside
                    if kind == 2 or kind == 3: psz = 0.0; pside = 0.0
                if q == 0.0 or q * dq > 0: avg = (avg * abs(q) + fp * abs(dq)) / abs(q + dq)
                elif abs(dq) > abs(q): avg = fp
                q += dq; cash -= dq * fp; f = abs(dq) * fp * fe; cash -= f; frais += f; nf += 1
                if abs(q) < 1e-12: q = 0.0; pside = 0.0
            eq = cash + q * x
            if eq <= 0:
                dead = True; liq = True; cash = 0.0; q = 0.0; break
            if q != 0.0 and eq <= capg * stopf:
                th = capg * stopf; ps = (th - cash) / q
                if cash + q * pf <= th: ps = pf
                cash += q * ps; f = abs(q) * ps * FT; cash -= f; frais += f; q = 0.0; nst += 1
                on = False; co = False; pside = 0.0; pause = i + bpd
                for k in range(nl): al[k] = False
                if cash < 0.6 * cap0: dead = True; tue = True
                break
            pf = x
        if dead:
            eqd[i // bpd] = cash; continue
        if on and (c[i] > P + rec * s or c[i] < P - rec * s):
            P = c[i]
            if esp < 0:
                s = P * (ESP[i] if ESP[i] > 0.005 else 0.005)
            for k in range(nl):
                pr[k] = P + (k - off) * s; sd[k] = 1.0 if pr[k] < P else -1.0; fr[k] = i + 1; ro[k] = co
                al[k] = not (co and sd[k] > 0)
        if q == 0.0 and cash < 0.6 * cap0: dead = True; tue = True       # arrêt aussi par érosion (règle R+ écrite)
        eq = cash + q * c[i]; eqd[i // bpd] = eq; pic = max(pic, eq); dd = min(dd, eq / pic - 1)
    if q != 0.0:
        f = abs(q) * c[n - 1] * FT; cash += q * c[n - 1] - f; frais += f; q = 0.0
    eqd[(n - 1) // bpd] = cash
    return cash, dd, frais, nf, nst, liq, tue, eqd


# ----------------------------------------------------------------------------------------------- directionnel
@njit
def simd(o, h, l, c, TGT, ATR, L, slp, ta, tt, atrk, tpp, reentry, hold, mart, capref, stopf, bpd):
    """TGT[i] = position voulue CONNUE à l'ouverture de la bougie de base i (signal de la dernière heure close).
    Amendement 1 : le sommet du trailing ne monte qu'avec les CLÔTURES des bougies de base (pas avec les mèches dans la bougie).
    slp : stop fixe (fraction) ; ta/tt : trailing activé à +ta, distance tt ; atrk : trailing à atrk*ATR (ATR[k] connu à l'ouverture de k) ;
    tpp : objectif (limite, maker) ; reentry=0 : après un stop, attendre que TGT change ; hold=1 : TGT lu seulement à plat ;
    mart=1 : mise x2 après une perte, au plus 3 doublements puis retour à la base."""
    n = len(o); ND = (n - 1) // bpd + 1; eqd = np.zeros(ND)
    cash = capref; q = 0.0; pos = 0; ent = 0.0; peak = 0.0; eqe = capref; pause = 0
    dead = False; liq = False; tue = False; nf = 0; nst = 0; frais = 0.0; pic = capref; dd = 0.0
    blk = False; bval = 0; mstep = 0; cash_ent = capref
    eqd[0] = cash
    for i in range(1, n):
        if dead:
            eqd[i // bpd] = cash; continue
        want = TGT[i]
        if blk:
            if want != bval: blk = False
            else: want = 0 if pos == 0 else pos
        if hold and pos != 0: want = pos
        if i < pause: want = 0
        if want != pos:
            if pos != 0:                                         # sortie au marché à l'ouverture
                fp = o[i]; cash += q * fp; f = abs(q) * fp * FT; cash -= f; frais += f; nf += 1
                if mart:
                    if cash < cash_ent: mstep = mstep + 1 if mstep < 3 else 0
                    else: mstep = 0
                q = 0.0; pos = 0
            if want != 0:
                Le = L * (2.0 ** mstep if mart else 1.0)
                if Le > 10.0: Le = 10.0
                fp = o[i]; eqe = cash; cash_ent = cash
                q = want * Le * cash / fp; f = abs(q) * fp * FT; cash -= f; frais += f; nf += 1
                cash -= q * fp; pos = want; ent = fp; peak = fp
        if pos != 0:
            pf = o[i]
            for leg in range(3):
                x = ((l[i], h[i], c[i]) if c[i] >= o[i] else (h[i], l[i], c[i]))[leg]
                adverse = (pos > 0 and x < pf) or (pos < 0 and x > pf)
                ex = 0.0; kind = 0
                if adverse:
                    # niveau de sortie le plus proche dans le sens défavorable : stop fixe, trailing, ATR, garde-fou
                    G = (eqe * stopf - cash) / q                    # prix où l'équité touche le garde-fou
                    if pos > 0:
                        S = G; kind = 2
                        if slp > 0 and ent * (1 - slp) > S: S = ent * (1 - slp); kind = 1
                        if ta > 0 and peak >= ent * (1 + ta) and peak * (1 - tt) > S: S = peak * (1 - tt); kind = 1
                        if atrk > 0 and ATR[i] > 0 and peak - atrk * ATR[i] > S: S = peak - atrk * ATR[i]; kind = 1
                        if x <= S: ex = min(S, pf)
                    else:
                        S = G; kind = 2
                        if slp > 0 and ent * (1 + slp) < S: S = ent * (1 + slp); kind = 1
                        if ta > 0 and peak <= ent * (1 - ta) and peak * (1 + tt) < S: S = peak * (1 + tt); kind = 1
                        if atrk > 0 and ATR[i] > 0 and peak + atrk * ATR[i] < S: S = peak + atrk * ATR[i]; kind = 1
                        if x >= S: ex = max(S, pf)
                    fe = FT
                else:
                    if tpp > 0:
                        if pos > 0 and x >= ent * (1 + tpp): ex = max(ent * (1 + tpp), pf); kind = 3
                        if pos < 0 and x <= ent * (1 - tpp): ex = min(ent * (1 - tpp), pf); kind = 3
                    fe = FM
                if ex > 0.0:
                    cash += q * ex; f = abs(q) * ex * fe; cash -= f; frais += f; nf += 1
                    if mart:
                        if cash < cash_ent: mstep = mstep + 1 if mstep < 3 else 0
                        else: mstep = 0
                    q = 0.0; pos = 0
                    if kind == 2:
                        nst += 1; pause = i + bpd
                        if cash < 0.6 * capref: dead = True; tue = True
                    if not reentry:
                        blk = True; bval = TGT[i]
                    break
                if cash + q * x <= 0:
                    dead = True; liq = True; cash = 0.0; q = 0.0; pos = 0; break
                pf = x
        if pos > 0: peak = max(peak, c[i])
        elif pos < 0: peak = min(peak, c[i])
        if pos == 0 and cash < 0.6 * capref: dead = True; tue = True
        eq = cash + q * c[i]; eqd[i // bpd] = eq; pic = max(pic, eq); dd = min(dd, eq / pic - 1)
    if q != 0.0:
        f = abs(q) * c[n - 1] * FT; cash += q * c[n - 1] - f; frais += f; q = 0.0
    eqd[(n - 1) // bpd] = cash
    return cash, dd, frais, nf, nst, liq, tue, eqd


# ----------------------------------------------------------------------------------------------- bougies 1 h, indicateurs
@njit
def horaire(t, o, h, l, c):
    n = len(t); g = t // 3_600_000; hid = np.zeros(n, np.int64)
    T = []; O = []; H = []; Lo = []; C = []
    i = 0; m = 0
    while i < n:
        j = i; hh = h[i]; ll = l[i]
        while j + 1 < n and g[j + 1] == g[i]:
            j += 1; hh = max(hh, h[j]); ll = min(ll, l[j])
        for k in range(i, j + 1): hid[k] = m
        T.append(g[i] * 3_600_000); O.append(o[i]); H.append(hh); Lo.append(ll); C.append(c[j]); m += 1; i = j + 1
    return np.array(T), np.array(O), np.array(H), np.array(Lo), np.array(C), hid


@njit
def ema(x, n):
    e = np.empty(len(x)); e[0] = x[0]; a = 2.0 / (n + 1)
    for k in range(1, len(x)): e[k] = e[k - 1] + a * (x[k] - e[k - 1])
    for k in range(min(n, len(x))): e[k] = np.nan                       # chauffe
    return e


@njit
def rsi(C, n):
    m = len(C); r = np.full(m, np.nan); ag = 0.0; al = 0.0
    for k in range(1, m):
        d = C[k] - C[k - 1]; up = d if d > 0 else 0.0; dn = -d if d < 0 else 0.0
        if k <= n: ag += up / n; al += dn / n
        else: ag = (ag * (n - 1) + up) / n; al = (al * (n - 1) + dn) / n
        if k >= n: r[k] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return r


@njit
def atr(H, L, C, n):
    m = len(C); a = np.full(m, np.nan); s = 0.0
    for k in range(1, m):
        tr = max(H[k] - L[k], abs(H[k] - C[k - 1]), abs(L[k] - C[k - 1]))
        if k <= n: s += tr / n
        else: s = (s * (n - 1) + tr) / n
        if k >= n: a[k] = s
    return a


@njit
def adx(H, L, C, n):
    m = len(C); out = np.full(m, np.nan); tr_s = 0.0; pd_s = 0.0; md_s = 0.0; ax = 0.0; dxs = 0.0
    for k in range(1, m):
        up = H[k] - H[k - 1]; dn = L[k - 1] - L[k]
        pdm = up if (up > dn and up > 0) else 0.0; mdm = dn if (dn > up and dn > 0) else 0.0
        tr = max(H[k] - L[k], abs(H[k] - C[k - 1]), abs(L[k] - C[k - 1]))
        if k <= n: tr_s += tr; pd_s += pdm; md_s += mdm
        else: tr_s = tr_s - tr_s / n + tr; pd_s = pd_s - pd_s / n + pdm; md_s = md_s - md_s / n + mdm
        if k >= n:
            pdi = 100 * pd_s / tr_s if tr_s > 0 else 0.0; mdi = 100 * md_s / tr_s if tr_s > 0 else 0.0
            dx = 100 * abs(pdi - mdi) / (pdi + mdi) if pdi + mdi > 0 else 0.0
            if k < 2 * n: dxs += dx; ax = dxs / (k - n + 1)
            else: ax = (ax * (n - 1) + dx) / n
            if k >= 2 * n - 1: out[k] = ax
    return out


@njit
def boll(C, n, kk):
    m = len(C); mu = np.full(m, np.nan); up = np.full(m, np.nan); lo = np.full(m, np.nan)
    for k in range(n - 1, m):
        s = 0.0; s2 = 0.0
        for j in range(k - n + 1, k + 1): s += C[j]; s2 += C[j] * C[j]
        a = s / n; sd = np.sqrt(max(s2 / n - a * a, 0.0)); mu[k] = a; up[k] = a + kk * sd; lo[k] = a - kk * sd
    return mu, up, lo


@njit
def vol24_calme(C):
    """+1 si la vol. réalisée des 24 dernières heures < sa médiane des 720 dernières heures, -1 sinon, 0 en chauffe."""
    m = len(C); v = np.full(m, np.nan); out = np.zeros(m, np.int8)
    for k in range(25, m):
        s = 0.0; s2 = 0.0
        for j in range(k - 23, k + 1):
            r = np.log(C[j] / C[j - 1]); s += r; s2 += r * r
        v[k] = np.sqrt(max(s2 / 24 - (s / 24) ** 2, 0.0))
    for k in range(25 + 720, m):
        med = np.median(v[k - 719:k + 1])
        out[k] = 1 if v[k] < med else -1
    return out


@njit
def atr_jour(T, H, L, C):
    """ATR14 journalier (en prix) de la DERNIÈRE journée close, reporté sur chaque heure."""
    m = len(C); d = T // 86_400_000; out = np.full(m, np.nan)
    DH = []; DL = []; DC = []; fin = []
    i = 0
    while i < m:
        j = i; hh = H[i]; ll = L[i]
        while j + 1 < m and d[j + 1] == d[i]: j += 1; hh = max(hh, H[j]); ll = min(ll, L[j])
        DH.append(hh); DL.append(ll); DC.append(C[j]); fin.append(j); i = j + 1
    a = atr(np.array(DH), np.array(DL), np.array(DC), 14)
    for k in range(len(fin) - 1):
        for i in range(fin[k] + 1, fin[k + 1] + 1): out[i] = a[k]
    return out


def prev(x, hid):
    """valeur de la dernière heure CLOSE avant la bougie de base (hid = indice de l'heure en cours)."""
    out = np.full(len(hid), np.nan)
    ok = hid >= 1
    out[ok] = x[hid[ok] - 1]
    return out


# ----------------------------------------------------------------------------------------------- signaux directionnels (sur 1 h)
@njit
def donchian(H, L, C, N, M, longonly):
    m = len(C); tg = np.zeros(m, np.int8); p = 0
    for k in range(N, m):
        hi = H[k - N:k].max(); lo = L[k - N:k].min(); hm = H[k - M:k].max(); lm = L[k - M:k].min()
        if p == 1 and C[k] < lm: p = 0
        if p == -1 and C[k] > hm: p = 0
        if C[k] > hi: p = 1
        elif C[k] < lo and not longonly: p = -1
        tg[k] = p
    return tg


@njit
def supertrend(C, A, kk):
    m = len(C); tg = np.zeros(m, np.int8); p = 0; tr = 0.0
    for k in range(m):
        if np.isnan(A[k]): continue
        if p == 0:
            p = 1; tr = C[k] - kk * A[k]
        elif p == 1:
            tr = max(tr, C[k] - kk * A[k])
            if C[k] < tr: p = -1; tr = C[k] + kk * A[k]
        else:
            tr = min(tr, C[k] + kk * A[k])
            if C[k] > tr: p = 1; tr = C[k] - kk * A[k]
        tg[k] = p
    return tg


@njit
def tsmom(T, C, nd, longonly):
    m = len(C); tg = np.zeros(m, np.int8); p = 0; n = nd * 24
    for k in range(n, m):
        if (T[k] // 3_600_000) % 24 == 23:                 # décision une fois par jour, à la clôture de 23 h UTC
            r = C[k] / C[k - n] - 1
            p = 1 if r > 0 else (0 if longonly else -1)
        tg[k] = p
    return tg


@njit
def etat_rev(X, lo, hi, mid_up, mid_dn, longonly, flt):
    """retour à la moyenne générique : X < lo -> long, X > hi -> short ; long sort quand X >= mid_up ; short quand X <= mid_dn.
    flt[k] : +1 longs seulement, -1 shorts seulement, 0 les deux."""
    m = len(X); tg = np.zeros(m, np.int8); p = 0
    for k in range(m):
        if np.isnan(X[k]) or np.isnan(lo[k]) or np.isnan(hi[k]): continue
        if p == 1 and X[k] >= mid_up[k]: p = 0
        if p == -1 and X[k] <= mid_dn[k]: p = 0
        if p == 0:
            if X[k] < lo[k] and flt[k] >= 0: p = 1
            elif X[k] > hi[k] and not longonly and flt[k] <= 0: p = -1
        tg[k] = p
    return tg


@njit
def cassure_bb(C, mu, up, lo):
    m = len(C); tg = np.zeros(m, np.int8); p = 0
    for k in range(m):
        if np.isnan(mu[k]): continue
        if p == 1 and C[k] < mu[k]: p = 0
        if p == -1 and C[k] > mu[k]: p = 0
        if p == 0:
            if C[k] > up[k]: p = 1
            elif C[k] < lo[k]: p = -1
        tg[k] = p
    return tg


@njit
def volbreak(C, Ah, kk, hold):
    m = len(C); tg = np.zeros(m, np.int8); p = 0; cnt = 0
    for k in range(1, m):
        if cnt > 0: cnt -= 1
        if cnt == 0: p = 0
        if not np.isnan(Ah[k - 1]) and abs(C[k] - C[k - 1]) > kk * Ah[k - 1]:
            p = 1 if C[k] > C[k - 1] else -1; cnt = hold
        tg[k] = p
    return tg


def sgn(x, longonly=False):
    s = np.where(np.isnan(x), 0, np.sign(x)).astype(np.int8)
    if longonly: s[s < 0] = 0
    return s

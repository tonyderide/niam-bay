"""PREREG-73 : écarts 1,2 / 2 / 3 / 5 % et grille inversée (ordres stop qui suivent le prix)."""
import sys, json, numpy as np
from numba import njit
from t69 import regime, couper, ms
E, NL, LEV, FM, FT, CAP0 = 0.012, 5, 5.0, 0.0002, 0.0005, 1000.0
WSL, WTP, LSL, LTP = 0.006, 0.025, 0.030, 0.002


@njit
def danger(t, c):
    """DG[i] = RSI14 (Wilder) de la dernière bougie 1 h close avant la minute i < 25."""
    n = len(c); g = t // 3_600_000; D = np.zeros(n, np.bool_)
    fin = []; C = []
    i = 0
    while i < n:
        j = i
        while j + 1 < n and g[j + 1] == g[i]: j += 1
        fin.append(j); C.append(c[j]); i = j + 1
    m = len(C); bad = np.zeros(m, np.bool_); ag = 0.0; al = 0.0
    for k in range(1, m):
        d = C[k] - C[k - 1]; up = d if d > 0 else 0.0; dn = -d if d < 0 else 0.0
        if k <= 14: ag += up / 14; al += dn / 14
        else: ag = (ag * 13 + up) / 14; al = (al * 13 + dn) / 14
        if k >= 14:
            rsi = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
            bad[k] = rsi < 25
    for k in range(m - 1):
        for i in range(fin[k] + 1, fin[k + 1] + 1): D[i] = bad[k]
    return D


@njit
def tendance(t, c):
    """UP[i] = +1 si EMA50 >= EMA200 des clôtures 1 h (dernière bougie 1 h close avant la minute i), -1 sinon, 0 pendant la chauffe (200 h)."""
    n = len(c); g = t // 3_600_000; U = np.zeros(n, np.int8)
    fin = []; C = []
    i = 0
    while i < n:
        j = i
        while j + 1 < n and g[j + 1] == g[i]: j += 1
        fin.append(j); C.append(c[j]); i = j + 1
    m = len(C); v = np.zeros(m, np.int8); e50 = C[0]; e200 = C[0]
    for k in range(1, m):
        e50 += (C[k] - e50) * 2 / 51; e200 += (C[k] - e200) * 2 / 201
        if k >= 200: v[k] = 1 if e50 >= e200 else -1
    for k in range(m - 1):
        for i in range(fin[k] + 1, fin[k + 1] + 1): U[i] = v[k]
    return U


@njit
def sim(t, o, h, l, c, R, DG, N, plus, UP, flt, rearm=0, esp=0.012, inv=0):
    """N = notionnel par niveau (= capital de la paire). plus = 1 pour R+."""
    n = len(o); ND = (n - 1) // 1440 + 1; eqd = np.zeros(ND)
    cap0 = N; pr = np.zeros(NL); sd = np.zeros(NL); fr = np.zeros(NL, np.int64); al = np.zeros(NL, np.bool_); ro = np.zeros(NL, np.bool_)
    q = 0.0; cash = cap0; avg = 0.0; on = False; co = False; P = 0.0; s = 0.0
    pside = 0.0; tp = 0.0; sl = 0.0; psz = 0.0; capg = cap0; pause = 0
    dead = False; liq = False; tue = False; nf = 0; nst = 0; frais = 0.0; pic = cap0; dd = 0.0
    for i in range(n):
        if dead:
            eqd[i // 1440] = cash; continue
        if t[i] % 900_000 == 0 and i > 0:
            act = on
            if act and q != 0.0 and pside != np.sign(q):          # 3. protection, posée une fois par côté
                C0 = c[i - 1]; pside = np.sign(q); psz = abs(q)
                if q > 0:
                    if C0 > avg: sl = C0 * (1 - WSL); tp = C0 * (1 + WTP)
                    else: sl = avg * (1 - LSL); tp = avg * (1 + LTP)
                else:
                    if C0 < avg: sl = C0 * (1 + WSL); tp = C0 * (1 - WTP)
                    else: sl = avg * (1 + LSL); tp = avg * (1 - LTP)
            if act and DG[i]:                                     # 4. disjoncteur
                on = False; co = False
                for k in range(NL): al[k] = False
                act = False
            if (not on) and R[i] and (not DG[i]) and i >= pause:  # 6. fourchette : démarrage
                on = True; co = False; P = o[i]; s = P * esp; capg = cash + q * o[i]
                for k in range(NL):
                    pr[k] = P + (k - 1.5) * s; sd[k] = 1.0 if pr[k] < P else -1.0; fr[k] = i; al[k] = True; ro[k] = False
            elif act and not R[i]:                                # 7. tendance
                if q == 0.0:
                    on = False
                    for k in range(NL): al[k] = False
                else: co = True
            if on and co and q == 0.0:
                on = False; co = False
                for k in range(NL): al[k] = False
        pf = o[i]
        for leg in range(3):
            x = ((l[i], h[i], c[i]) if c[i] >= o[i] else (h[i], l[i], c[i]))[leg]
            bas = x < pf
            while True:
                # prochain événement dans le sens du mouvement : niveau de grille, objectif ou stop
                best = -1; bp = 0.0; kind = 0
                if on:
                    for k in range(NL):
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
                    k = best; al[k] = False                      # niveau à un coup : la reprise est sautée
                    dq = (-sd[k] if inv else sd[k]) * N / pr[k]          # inversée : vente sous le centre, achat au-dessus
                    if ro[k]:
                        if q * dq >= 0: continue
                        dq = np.sign(dq) * min(abs(dq), abs(q))
                    if plus and abs(q + dq) > abs(q) and abs(q + dq) * pr[k] > LEV * cap0 * 1.0001: continue
                    if flt and (q == 0.0 or q * dq > 0) and ((dq > 0 and UP[i] < 0) or (dq < 0 and UP[i] > 0)): continue   # B : pas d'entrée contre la tendance
                    if inv:                                          # ordre stop : au niveau, ou au premier prix si sauté ; frais taker
                        saute = (bas and pf < pr[k]) or ((not bas) and pf > pr[k])
                        fp = pf if saute else pr[k]; fe = FT
                    else:
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
                if rearm and q == 0.0 and on:                        # C : retour à zéro, quelle qu'en soit la cause -> tous les niveaux reposés, même centre
                    for kk in range(NL):
                        al[kk] = not (co and sd[kk] > 0); fr[kk] = i + 1; ro[kk] = co
            eq = cash + q * x
            if eq <= 0:
                dead = True; liq = True; cash = 0.0; q = 0.0; break
            if plus and q != 0.0 and eq <= capg * 0.85:
                th = capg * 0.85; ps = (th - cash) / q
                if cash + q * pf <= th: ps = pf
                cash += q * ps; f = abs(q) * ps * FT; cash -= f; frais += f; q = 0.0; nst += 1
                on = False; co = False; pside = 0.0; pause = i + 1440
                for k in range(NL): al[k] = False
                if cash < 0.6 * cap0: dead = True; tue = True
                break
            pf = x
        if dead:
            eqd[i // 1440] = cash; continue
        if on and (c[i] > P + 2 * s or c[i] < P - 2 * s):        # recentrage, position gardée
            P = c[i]
            for k in range(NL):
                pr[k] = P + (k - 1.5) * s; sd[k] = 1.0 if pr[k] < P else -1.0; fr[k] = i + 1; ro[k] = co
                al[k] = not (co and sd[k] > 0)                    # fermeture seule : pas d'achats d'entrée
        eq = cash + q * c[i]; eqd[i // 1440] = eq; pic = max(pic, eq); dd = min(dd, eq / pic - 1)
    if q != 0.0:
        f = abs(q) * c[n - 1] * FT; cash += q * c[n - 1] - f; frais += f; q = 0.0
    eqd[(n - 1) // 1440] = cash
    return cash, dd, frais, nf, nst, liq, tue, eqd


if __name__ == "__main__":
    Dd = sys.argv[1]; C4 = ["SOL", "LINK", "ADA", "DOT"]
    X = {}
    for c in C4:
        a = couper(np.load("../dca-martingale/refait/donnees/SOLUSDT-1m.npy" if c == "SOL" else f"{Dd}/{c}.npy"), 2880)
        tt = a[:, 0].astype(np.int64)
        X[c] = (a, tt, danger(tt, a[:, 4]), tendance(tt, a[:, 4]))
    def run(c, d, f, esp, inv):
        a, tt, DG, UP = X[c]; w = (tt >= d) & (tt < f); x = a[w]
        R = np.ones(int(w.sum()), np.bool_)
        return sim(tt[w].copy(), x[:, 1].copy(), x[:, 2].copy(), x[:, 3].copy(), x[:, 4].copy(), R, DG[w].copy(), CAP0, 1, UP[w].copy(), 0, 0, esp, inv)
    OUT = {}
    PER = {"P1": (ms(2024, 2, 1), ms(2026, 1, 1)), "P2": (ms(2026, 1, 1), ms(2026, 10, 1))}
    VAR = [("A", 0.012, 0), ("W2", 0.02, 0), ("W3", 0.03, 0), ("W5", 0.05, 0), ("I1.2", 0.012, 1), ("I3", 0.03, 1)]
    for nom, esp, inv in VAR:
        for pn, (d, f) in PER.items():
            r4 = {c: run(c, d, f, esp, inv) for c in C4}; Lm = min(len(r[7]) for r in r4.values())
            port = sum(r[7][:Lm] for r in r4.values()); pk = np.maximum.accumulate(port); ddp = float((port / pk - 1).min())
            res = {c: round(r[0] - CAP0, 1) for c, r in r4.items()}; tt_ = sum(res.values())
            mort = [c for c, r in r4.items() if r[5] or r[6]]
            ok = tt_ > 0 and sum(v > 0 for v in res.values()) >= 3 and not mort and ddp > -0.30
            OUT[f"{nom}_{pn}"] = dict(total=round(tt_, 1), par_paire=res, positives=sum(v > 0 for v in res.values()), baisse_port=round(ddp, 3),
                                      liquidees_ou_arretees=mort, brut=round(sum(r[0] - CAP0 + r[2] for r in r4.values()), 1),
                                      frais=round(sum(r[2] for r in r4.values()), 1), exec=sum(int(r[3]) for r in r4.values()),
                                      stops=sum(int(r[4]) for r in r4.values()), critere_ok=ok)
            print(f"{nom} {pn}:", json.dumps(OUT[f'{nom}_{pn}'], ensure_ascii=False), flush=True)
    temoin = OUT["A_P1"]["total"] == -1713.2 and OUT["A_P2"]["total"] == -1606.0
    OUT["temoin_ok"] = temoin; OUT["verdicts"] = {}
    for nom, _, _ in VAR[1:]:
        mieux = OUT[f"{nom}_P1"]["total"] > OUT["A_P1"]["total"] and OUT[f"{nom}_P2"]["total"] > OUT["A_P2"]["total"]
        tient = OUT[f"{nom}_P1"]["critere_ok"] and OUT[f"{nom}_P2"]["critere_ok"]
        OUT["verdicts"][nom] = "NON CONCLUANT (témoin)" if not temoin else ("TIENT" if tient else ("MIEUX SANS SUFFIRE" if mieux else "NON"))
    print("VERDICTS :", json.dumps(OUT["verdicts"], ensure_ascii=False))
    json.dump(OUT, open("t73.json", "w"), ensure_ascii=False, indent=1)

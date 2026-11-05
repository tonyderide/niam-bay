"""PREREG-69 : grille d'avril (neutre, 1,2 %, 5 niveaux, levier 5). A voulue, B corrigée, C corrigée + régime ADX/BBW 15 min."""
import sys, json, numpy as np, datetime as dt
from numba import njit
E, NL, LEV, FM, FT, CAP0 = 0.012, 5, 5.0, 0.0002, 0.0005, 1000.0
ms = lambda a, m, j: int(dt.datetime(a, m, j, tzinfo=dt.timezone.utc).timestamp() * 1000)
def couper(a, F):
    plat = np.convolve(a[:, 2] == a[:, 3], np.ones(F, int), "valid") == F if len(a) >= F else np.zeros(0, bool)
    return a[:np.argmax(plat)] if plat.any() else a
@njit
def regime(t, h, l, c):
    """ranging[i] = ADX(14) < 40 et BBW(20,2) < 4 % sur la dernière bougie 15 min CLOSE avant la minute i."""
    n = len(c); g = t // 900_000; R = np.zeros(n, np.bool_)
    H = []; L = []; C = []; fin = []
    i = 0
    while i < n:
        j = i; hh = h[i]; ll = l[i]
        while j + 1 < n and g[j + 1] == g[i]: j += 1; hh = max(hh, h[j]); ll = min(ll, l[j])
        H.append(hh); L.append(ll); C.append(c[j]); fin.append(j); i = j + 1
    m = len(C); ok = np.zeros(m, np.bool_); tr_s = 0.0; pd_s = 0.0; md_s = 0.0; adx = 0.0; dxs = 0.0
    for k in range(1, m):
        up = H[k] - H[k-1]; dn = L[k-1] - L[k]
        pdm = up if (up > dn and up > 0) else 0.0; mdm = dn if (dn > up and dn > 0) else 0.0
        tr = max(H[k] - L[k], abs(H[k] - C[k-1]), abs(L[k] - C[k-1]))
        if k <= 14: tr_s += tr; pd_s += pdm; md_s += mdm
        else: tr_s = tr_s - tr_s / 14 + tr; pd_s = pd_s - pd_s / 14 + pdm; md_s = md_s - md_s / 14 + mdm
        if k >= 14:
            pdi = 100 * pd_s / tr_s if tr_s > 0 else 0.0; mdi = 100 * md_s / tr_s if tr_s > 0 else 0.0
            dx = 100 * abs(pdi - mdi) / (pdi + mdi) if pdi + mdi > 0 else 0.0
            if k < 28: dxs += dx; adx = dxs / (k - 13)
            else: adx = (adx * 13 + dx) / 14
            if k >= 27 and k >= 19:
                s = 0.0; s2 = 0.0
                for q in range(k - 19, k + 1): s += C[q]; s2 += C[q] * C[q]
                mu = s / 20; sd = np.sqrt(max(s2 / 20 - mu * mu, 0.0)); bbw = 400 * sd / mu
                ok[k] = adx < 40 and bbw < 4
    for k in range(m - 1):
        a = fin[k] + 1; b = fin[k + 1] + 1
        for i in range(a, b): R[i] = ok[k]
    return R
@njit
def sim(o, h, l, c, R, ver):
    n = len(o); ND = (n - 1) // 1440 + 1; eqd = np.zeros(ND)
    pr = np.zeros(NL); sd = np.zeros(NL); sz = np.zeros(NL); fr = np.zeros(NL, np.int64); al = np.zeros(NL, np.bool_)
    q = 0.0; cash = CAP0; on = False; co = False; dead = False; pause = 0; P = 0.0; s = 0.0; N = 0.0; capg = CAP0
    pic = CAP0; dd = 0.0; frais = 0.0; nf = 0; nstop = 0; liq = False; tue = False
    for i in range(n):
        if dead:
            eqd[i // 1440] = cash; continue
        if not on and i >= pause and (ver < 2 or R[i]):
            on = True; co = False; P = o[i]; s = P * E; capg = cash + q * o[i]; N = capg * LEV / NL
            for k in range(NL):
                pr[k] = P + (k - 1.5) * s; sd[k] = 1.0 if pr[k] < P else -1.0; sz[k] = N / pr[k]; fr[k] = i; al[k] = True
        if on and co:
            for k in range(NL):
                if al[k] and sd[k] * q >= 0: al[k] = False
            if q == 0.0: on = False
        pf = o[i]
        for leg in range(2):
            x = (l[i] if leg == 0 else h[i]) if c[i] >= o[i] else (h[i] if leg == 0 else l[i])
            if on:
                bas = x < pf
                while True:
                    best = -1
                    for k in range(NL):
                        if not al[k] or fr[k] > i: continue
                        if bas and sd[k] > 0 and x < pr[k] and (best < 0 or pr[k] > pr[best]): best = k
                        if (not bas) and sd[k] < 0 and x > pr[k] and (best < 0 or pr[k] < pr[best]): best = k
                    if best < 0: break
                    k = best; fp = min(pr[k], pf) if bas else max(pr[k], pf); dq = sd[k] * sz[k]
                    if ver >= 1 and abs(q + dq) > abs(q) and abs(q + dq) * fp > LEV * capg * 1.0001:
                        al[k] = False; continue
                    q += dq; cash -= dq * fp; f = abs(dq) * fp * FM; cash -= f; frais += f; nf += 1
                    pr[k] = pr[k] + s if sd[k] > 0 else pr[k] - s; sd[k] = -sd[k]; fr[k] = i + 1
                    if co and sd[k] * q >= 0: al[k] = False
            eq = cash + q * x
            if ver == 0 and eq <= 0:
                dead = True; liq = True; cash = 0.0; q = 0.0; break
            if ver >= 1 and q != 0.0 and eq <= capg * 0.85:
                th = capg * 0.85; ps = (th - cash) / q
                if (cash + q * pf) <= th: ps = pf
                cash += q * ps; f = abs(q) * ps * FT; cash -= f; frais += f; q = 0.0; on = False; nstop += 1; pause = i + 1440
                for k in range(NL): al[k] = False
                if cash < 0.6 * CAP0: dead = True; tue = True
                break
            pf = x
        if dead:
            eqd[i // 1440] = cash; continue
        if on and not co and (c[i] > P + 2 * s or c[i] < P - 2 * s):
            P = c[i]
            for k in range(NL):
                pr[k] = P + (k - 1.5) * s; sd[k] = 1.0 if pr[k] < P else -1.0; sz[k] = N / pr[k]; fr[k] = i + 1; al[k] = True
        if on and ver == 2 and not co and not R[i]: co = True
        eq = cash + q * c[i]; eqd[i // 1440] = eq; pic = max(pic, eq); dd = min(dd, eq / pic - 1)
    if q != 0.0:
        f = abs(q) * c[n - 1] * FT; cash += q * c[n - 1] - f; frais += f; q = 0.0
    eqd[(n - 1) // 1440] = cash
    return cash, dd, frais, nf, nstop, liq, tue, eqd
if __name__ == "__main__" and sys.argv[1] == "test":
    # dents de scie : le prix fait 100 allers-retours entre 99,0 et 100,9 ; centre 100, e = 1,2 -> achat 99,4 / vente 100,6 répétés
    pts = [100.0] + [99.0, 100.9] * 100 + [100.0]
    o = np.array(pts[:-1]); c = np.array(pts[1:]); h = np.maximum(o, c); l = np.minimum(o, c); R = np.ones(len(o), np.bool_)
    for v in range(3):
        f, dd, fr, nf, ns, lq, tu, _ = sim(o, h, l, c, R, v); print("test ver", v, "final", round(f, 2), "fills", nf, "frais", round(fr, 2), "dd", round(dd, 4))
    sys.exit()
if __name__ == "__main__":
    Dd = sys.argv[1]; C4 = ["SOL", "LINK", "ADA", "DOT"]; C7 = "XRP DOGE AVAX LTC BNB BCH ATOM".split()
    PER = {"P1": (ms(2024, 2, 1), ms(2026, 1, 1)), "P2": (ms(2026, 1, 1), ms(2026, 10, 1)), "avril26": (ms(2026, 4, 1), ms(2026, 5, 1))}
    X = {}
    for c in C4 + C7:
        a = couper(np.load(f"../dca-martingale/refait/donnees/SOLUSDT-1m.npy" if c == "SOL" else f"{Dd}/{c}.npy"), 2880)
        R = regime(a[:, 0].astype(np.int64), a[:, 2], a[:, 3], a[:, 4]); X[c] = (a, R)
    def run(c, d, f, v):
        a, R = X[c]; w = (a[:, 0] >= d) & (a[:, 0] < f); x = a[w]
        return sim(x[:, 1].copy(), x[:, 2].copy(), x[:, 3].copy(), x[:, 4].copy(), R[w].copy(), v)
    OUT = {}; NOM = "ABC"
    for v in range(3):
        for p, (d, f) in PER.items():
            r4 = {c: run(c, d, f, v) for c in C4}; L = min(len(r[7]) for r in r4.values())
            port = sum(r[7][:L] for r in r4.values()); pk = np.maximum.accumulate(port); ddp = float((port / pk - 1).min())
            res = {c: round(r[0] - CAP0, 1) for c, r in r4.items()}; tot = sum(res.values())
            brut = sum(r[0] - CAP0 + r[2] for r in r4.values()); fr = sum(r[2] for r in r4.values())
            mort = [c for c, r in r4.items() if r[5] or r[6]]
            ok = tot > 0 and sum(x > 0 for x in res.values()) >= 3 and not mort and ddp > -0.30
            r7 = {c: round(run(c, d, f, v)[0] - CAP0, 1) for c in C7} if p != "avril26" else {}
            # départs de 3 mois
            dep = []
            if p != "avril26":
                M = 30 * 86_400_000
                for st in range(d, f - 3 * M, M): dep.append(sum(run(c, st, st + 3 * M, v)[0] - CAP0 for c in C4))
            OUT[f"{NOM[v]}_{p}"] = dict(total=round(tot, 1), par_paire=res, positives=sum(x > 0 for x in res.values()), baisse_port=round(ddp, 3), liquidees_ou_arretees=mort,
                brut=round(brut, 1), frais=round(fr, 1), exec=sum(int(r[3]) for r in r4.values()), stops=sum(int(r[4]) for r in r4.values()), critere_ok=ok,
                autres7=r7, autres7_total=round(sum(r7.values()), 1), departs3m_en_perte=round(float(np.mean(np.array(dep) <= 0)), 2) if dep else None, departs3m_median=round(float(np.median(dep)), 1) if dep else None)
            print(f"{NOM[v]} {p}:", json.dumps(OUT[f'{NOM[v]}_{p}'], ensure_ascii=False))
        print(f"VERSION {NOM[v]} :", "TIENT" if OUT[f"{NOM[v]}_P1"]["critere_ok"] and OUT[f"{NOM[v]}_P2"]["critere_ok"] else "NON")
    json.dump(OUT, open("t69.json", "w"), ensure_ascii=False, indent=1)

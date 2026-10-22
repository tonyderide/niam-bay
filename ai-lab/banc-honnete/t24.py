"""PREREG-21 : alignement de plusieurs unités de temps. Voir PREREG-21-multi-unites.md.
Signal en 3 ou 5 min, filtre de tendance 1 h (et 15 min), trades déroulés minute par minute."""
import bisect, itertools, os, pickle, random
CACHE = os.path.expanduser("~/.cache/banc-honnete")
ts = lambda y, m, d: int(__import__("calendar").timegm((y, m, d, 0, 0, 0)))
A, B, C0, C1 = ts(2024, 1, 1), ts(2026, 1, 1), ts(2026, 1, 1), ts(2026, 10, 17)
FEE = 0.0005; STOP_EXTRA = 0.0003; MAXB = 48
SORTIES = ((0.005, 0.0025), (0.01, 0.005), (0.015, 0.0075), (0.005, 0.005), (0.005, 0.01))
MINCE = {"ARB", "INJ", "FET", "GRT", "ALGO"}


def charge(m):
    return pickle.load(open(f"{CACHE}/PF_{m}USD_1m_2024-01-01.pkl", "rb"))


def agrege(T, C, k):
    """Bougies de k minutes alignées sur l'heure UTC ; seulement les bougies complètes."""
    s = k * 60; out = []; cur = None
    for t, c in zip(T, C):
        b = t - t % s
        if cur is None or b != cur[0]:
            if cur and cur[5] == k: out.append(cur)
            cur = [b, c[0], c[1], c[2], c[3], 1]
        else:
            cur[2] = max(cur[2], c[1]); cur[3] = min(cur[3], c[2]); cur[4] = c[3]; cur[5] += 1
    if cur and cur[5] == k: out.append(cur)
    return [x[0] for x in out], [(x[1], x[2], x[3], x[4]) for x in out]


def ema(x, k):
    a = 2 / (k + 1); o = [x[0]]
    for v in x[1:]: o.append(o[-1] + a * (v - o[-1]))
    return o


def tendance(Th, Ch):
    cl = [c[3] for c in Ch]; e20, e50 = ema(cl, 20), ema(cl, 50)
    return [1 if a > b else -1 for a, b in zip(e20, e50)]


def rsi2(cl):
    o = [50.0] * len(cl); g = l = 0.0
    for i in range(1, len(cl)):
        d = cl[i] - cl[i - 1]; g = 0.5 * g + 0.5 * max(d, 0); l = 0.5 * l + 0.5 * max(-d, 0)
        o[i] = 100 if l == 0 else 100 - 100 / (1 + g / l)
    return o


class Marche:
    def __init__(self, m):
        self.m = m; self.slip = 0.0005 if m in MINCE else 0.0002
        self.T1, self.C1 = charge(m); self.idx1 = {t: i for i, t in enumerate(self.T1)}
        Th, Ch = agrege(self.T1, self.C1, 60); Tq, Cq = agrege(self.T1, self.C1, 15)
        self.Th, self.trh = Th, tendance(Th, Ch); self.Tq, self.trq = Tq, tendance(Tq, Cq)
        self.petit = {}
        for k in (3, 5):
            Ts, Cs = agrege(self.T1, self.C1, k); cl = [c[3] for c in Cs]
            e9, e21 = ema(cl, 9), ema(cl, 21); r = rsi2(cl); n = len(cl)
            s1 = [0] * n; s2 = [0] * n; f1 = [0] * n; f2 = [0] * n
            for i in range(1, n):
                s1[i] = 1 if e9[i] > e21[i] and e9[i - 1] <= e21[i - 1] else -1 if e9[i] < e21[i] and e9[i - 1] >= e21[i - 1] else 0
                s2[i] = 1 if r[i] < 10 else -1 if r[i] > 90 else 0
                td = Ts[i] + k * 60                                  # instant de décision : clôture de la petite bougie i
                jh = bisect.bisect_right(Th, td - 3600) - 1           # dernière bougie 1 h CLOSE à td
                jq = bisect.bisect_right(Tq, td - 900) - 1            # dernière bougie 15 min CLOSE à td
                th = self.trh[jh] if jh >= 0 else 0; tq = self.trq[jq] if jq >= 0 else 0
                f1[i] = th; f2[i] = th if th == tq else 0
            self.petit[k] = (Ts, s1, s2, f1, f2)

    def trade(self, k, i, sens, tp, sl):
        """Entrée à l'ouverture de la petite bougie i+1, déroulée en 1 min. Renvoie (rendement net, temps de sortie, ambigu)."""
        Ts = self.petit[k][0]
        if i + 1 >= len(Ts) or Ts[i + 1] not in self.idx1: return None
        e1 = self.idx1[Ts[i + 1]]; e = self.C1[e1][0]; obj = e * (1 + tp * sens); stp = e * (1 - sl * sens)
        fin = Ts[i + 1] + MAXB * k * 60; cout_e = FEE + self.slip; j = e1; amb = False
        while j < len(self.T1) and self.T1[j] < fin:
            o, h, l, c = self.C1[j][:4]
            if j > e1 and ((o <= stp) if sens > 0 else (o >= stp)):
                return (o / e - 1) * sens - cout_e - FEE - self.slip - STOP_EXTRA, self.T1[j], amb
            ts_ = (l <= stp) if sens > 0 else (h >= stp); to_ = (h >= obj) if sens > 0 else (l <= obj)
            if ts_ and to_: amb = True
            if ts_: return -sl - cout_e - FEE - self.slip - STOP_EXTRA, self.T1[j], amb
            if to_: return tp - cout_e - FEE - self.slip, self.T1[j], amb
            j += 1
        j = min(j, len(self.T1) - 1)
        return (self.C1[j][3] / e - 1) * sens - cout_e - FEE - self.slip, self.T1[j], amb

    def strat(self, k, sig, filt, tp, sl, a, b):
        Ts, s1, s2, f1, f2 = self.petit[k]; S = s1 if sig == 1 else s2; F = {0: None, 1: f1, 2: f2}[filt]
        lo = bisect.bisect_left(Ts, a); hi = bisect.bisect_left(Ts, b) - 1; i = lo; R = []; nl = ns = namb = 0
        while i < hi:
            d = S[i]
            if d and (F is None or F[i] == d):
                r = self.trade(k, i, d, tp, sl)
                if r:
                    R.append(r[0]); nl += d > 0; ns += d < 0; namb += r[2]
                    i = bisect.bisect_right(Ts, r[1]); continue
            i += 1
        return R, nl, ns, namb, lo, hi

    def jumeaux(self, k, tp, sl, nl, ns, lo, hi, rnd):
        tot = 0.0
        for sens, cnt in ((1, nl), (-1, ns)):
            for _ in range(cnt):
                r = None
                while r is None: r = self.trade(k, rnd.randrange(lo, hi - MAXB), sens, tp, sl)
                tot += r[0]

        return tot


if __name__ == "__main__":
    M = {m: Marche(m) for m in ("XBT", "ETH", "SOL")}; print("données prêtes", flush=True)
    rows = []
    for m, k, filt, sig, (tp, sl) in itertools.product(("XBT", "ETH", "SOL"), (3, 5), (0, 1, 2), (1, 2), SORTIES):
        R1, *_ = M[m].strat(k, sig, filt, tp, sl, A, B); R2, nl, ns, namb, lo, hi = M[m].strat(k, sig, filt, tp, sl, C0, C1)
        rows.append(((m, k, filt, sig, tp, sl), sum(R1), len(R1), sum(R2), len(R2), nl, ns, namb, lo, hi))
    print(f"180 stratégies ; positives 2024-25 : {sum(r[1] > 0 for r in rows)} ; positives 2026 : {sum(r[3] > 0 for r in rows)}")
    amb = {}
    for r in rows: amb.setdefault((r[0][4], r[0][5]), [0, 0]); amb[(r[0][4], r[0][5])][0] += r[7]; amb[(r[0][4], r[0][5])][1] += r[4]
    for kx, (a_, n_) in amb.items(): print(f"  sortie TP {kx[0]:.2%} / SL {kx[1]:.2%} : bougies 1 min ambiguës {a_/max(1,n_):.1%} des trades 2026" + ("  <-- > 5 % (signalé)" if a_ / max(1, n_) > 0.05 else ""))
    gain = {}
    for (m, k, filt, sig, tp, sl), s1, n1, s2, *_ in rows: gain[(m, k, filt, sig, tp, sl)] = s2
    mieux = sum(gain[(m, k, f, sg, tp, sl)] > gain[(m, k, 0, sg, tp, sl)] for (m, k, f, sg, tp, sl) in gain if f > 0)
    print(f"[info] version filtrée > même signal sans filtre en 2026 : {mieux}/120")
    el = [r for r in rows if r[0][2] > 0 and r[2] >= 30]
    best = max(el, key=lambda r: r[1]); (m, k, filt, sig, tp, sl), s1, n1, s2, n2, nl, ns, namb, lo, hi = best
    rnd = random.Random(21); J = sorted(M[m].jumeaux(k, tp, sl, nl, ns, lo, hi, rnd) for _ in range(500))
    f0 = gain[(m, k, 0, sig, tp, sl)]
    j1 = s2 > 0 and sum(x < s2 for x in J) / 500 >= 0.99 and s2 > f0
    nom = f"{m} {k} min, filtre F{filt}, signal S{sig}, TP {tp:.2%} SL {sl:.2%}"
    print(f"SÉLECTION : {nom} | 2024-25 {100*s1:+.1f} % ({n1} trades)")
    print(f"J1 2026 : {100*s2:+.1f} % ({n2} trades) | jumeaux méd {100*J[250]:+.1f} % p99 {100*J[495]:+.1f} % | sans filtre {100*f0:+.1f} % -> {'RÉUSSI' if j1 else 'RATÉ'}", flush=True)
    tot = 0.0; pos = 0; infos = []
    for m2 in ("ARB", "BNB", "INJ", "FET", "GRT", "ALGO"):
        X = Marche(m2); R, nl2, ns2, _, lo2, hi2 = X.strat(k, sig, filt, tp, sl, A, C1); g = sum(R); tot += g; pos += g > 0; infos.append((X, nl2, ns2, lo2, hi2))
        print(f"  J2 {m2:5} {100*g:+.1f} % ({len(R)} trades)", flush=True)
    rnd = random.Random(212); JJ = sorted(sum(X.jumeaux(k, tp, sl, a_, b_, c_, d_, rnd) for X, a_, b_, c_, d_ in infos) for _ in range(200))
    j2 = tot > 0 and tot > JJ[190] and pos >= 4
    print(f"J2 6 marchés jamais vus : somme {100*tot:+.1f} % | positifs {pos}/6 | jumeaux méd {100*JJ[100]:+.1f} % p95 {100*JJ[190]:+.1f} % -> {'RÉUSSI' if j2 else 'RATÉ'}")
    print("VERDICT :", "GAGNE" if j1 and j2 else "NON DÉMONTRÉ")

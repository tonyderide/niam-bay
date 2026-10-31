"""PREREG-32 : règle de Tony en bougies JOURNALIÈRES (1 h agrégées en jours UTC), panier 253 perpétuels Binance, morts compris.
Règles : PREREG-32-journalier.md (commit f09036c). Sortie identique à t31.py / sl-trailing/etude.py (jour ambigu = SL d'abord).
(i) inversion après perte ; (ii) sens EMA50 jours ; (iii) acheter-garder BTC et panier. Grille 36 réglages choisie sur 2024-25, jugement 2026.
Témoin : sens au hasard, 1 000 tirages. Funding : sous-panier couvert par carry-financement/data-univers/funding.json."""
import glob, json, os, datetime as dt
import numpy as np
try:
    from numba import njit
except ImportError:            # repli sans numba (plus lent, même résultat)
    def njit(*a, **k):
        return (lambda f: f) if not (a and callable(a[0])) else a[0]
TK = 0.0005
ICI = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(ICI, "../dca-martingale/refait/donnees")
FUND = os.path.join(ICI, "../carry-financement/data-univers/funding.json")
JMS = 86_400_000
ms = lambda *x: int(dt.datetime(*x, tzinfo=dt.timezone.utc).timestamp() * 1000)
PER = {"2024_2025": (ms(2024, 1, 1), ms(2026, 1, 1), 2.0), "2026": (ms(2026, 1, 1), ms(2026, 10, 1), 273 / 365)}
GRILLE = [(s, a, t) for s in (0.05, 0.10, 0.15, 0.20) for a in (0.05, 0.10, 0.20) for t in (0.03, 0.05, 0.10)]
VARS = {"i_inversion_apres_perte": 0, "ii_sens_ema50j": 1}
NTIR = 1000


def couper(a, F=48):   # identique à sl-trailing/etude.py et t31.py
    plat = np.convolve(a[:, 2] == a[:, 3], np.ones(F, int), "valid") == F if len(a) >= F else np.zeros(0, bool)
    return a[:np.argmax(plat)] if plat.any() else a


def journalier(a):
    j = (a[:, 0] // JMS).astype(np.int64); k = np.r_[0, np.flatnonzero(np.diff(j)) + 1]
    fin = np.r_[k[1:] - 1, len(a) - 1]
    return np.column_stack([j[k] * JMS, a[k, 1], np.maximum.reduceat(a[:, 2], k), np.minimum.reduceat(a[:, 3], k), a[fin, 4]])


def sens_ema(c, N=50):
    """sens[i] = signe(clôture[i-1] - EMA_N[i-1]) : jours terminés seulement ; 0 pendant la chauffe (N jours)."""
    e = np.empty(len(c)); k = 2 / (N + 1); e[0] = c[0]
    for j in range(1, len(c)): e[j] = c[j] * k + e[j - 1] * (1 - k)
    sh = np.where(c > e, 1, -1); sh[:N] = 0
    d = np.zeros(len(c), np.int64); d[1:] = sh[:-1]; return d


@njit(cache=True)
def graine(x):
    np.random.seed(x)


@njit(cache=True)
def chaine(o, h, l, c, ok, s, t, a, mode, dirs, pl, out):
    """mode 0 : inversion après perte (départ long) ; 1 : sens = dirs[i] ; 2 : hasard P(long)=pl (attend si dirs[i]==0).
    Entrée seulement aux barres ok[i] (journalier : toutes ; contrôle 1 h : première heure du jour). out[m] = (net, sens, i entrée, i sortie)."""
    T = len(o); i = 0; m = 0; sv = 1.0
    while i < T:
        if not ok[i]: i += 1; continue
        if mode == 0: sens = sv
        elif mode == 1:
            sens = float(dirs[i])
            if sens == 0: i += 1; continue
        else:
            if dirs[i] == 0: i += 1; continue
            sens = 1.0 if np.random.random() < pl else -1.0
        e = o[i]; i0 = i; sl = e * (1 - s * sens); actif = False; pic = 0.0
        while True:
            px = -1.0
            hi = h[i] if sens > 0 else l[i]; lo = l[i] if sens > 0 else h[i]; stop = sl
            if actif:
                ts = pic * (1 - t * sens); stop = max(sl, ts) if sens > 0 else min(sl, ts)
            if (lo - stop) * sens <= 0: px = min(o[i], stop) if sens > 0 else max(o[i], stop)
            elif actif: pic = max(pic, hi) if sens > 0 else min(pic, hi)
            elif (hi - e * (1 + a * sens)) * sens >= 0: actif = True; pic = hi
            if px < 0 and i == T - 1: px = c[i]
            if px >= 0:
                r = sens * (px / e - 1) - TK - TK * px / e
                out[m, 0] = r; out[m, 1] = sens; out[m, 2] = i0; out[m, 3] = i; m += 1
                if mode == 0 and r <= 0: sv = -sv
                break
            i += 1
        i += 1
    return m


def trades(x, g, mode, dirs, pl=0.5, ok=None):
    s, a, t = g
    if ok is None: ok = np.ones(len(x), np.bool_)
    out = np.empty((len(x) + 1, 4)); n = chaine(x[:, 1], x[:, 2], x[:, 3], x[:, 4], ok, s, t, a, mode, dirs, pl, out); return out[:n]


def dirs_de(d, mode):
    return d if mode == 1 else np.ones(len(d), np.int64)


# --- données
univ = set(json.load(open(os.path.join(D, "../univers.json"))))
H1, DJ = {}, {}
for f in sorted(glob.glob(f"{D}/*-1h.npy")):
    s = os.path.basename(f)[:-7]
    if s not in univ: continue
    a = couper(np.load(f))
    if len(a) > 24:
        H1[s] = a; dj = journalier(a); DJ[s] = (dj, sens_ema(dj[:, 4]))
FU = {s: np.array(v, float) for s, v in json.load(open(FUND)).items() if s in DJ}
print(len(DJ), "pièces exploitables ;", len(FU), "avec funding", flush=True)


def tranche(t0, t1):
    P = {}
    for s, (x, d) in DJ.items():
        k0, k1 = np.searchsorted(x[:, 0], [t0, t1])
        if k1 - k0 >= 20 and x[k0, 0] == t0: P[s] = (x[k0:k1], d[k0:k1])
    return P


def stats(P, R, ans):
    par = np.array([r[:, 0].sum() for r in R.values()]); N = len(par)
    tous = np.concatenate([r[:, 0] for r in R.values()]); nt = len(tous)
    ts = np.concatenate([x[r[:, 3].astype(int), 0] for (x, _), r in zip(P.values(), R.values())])
    k = np.argsort(ts, kind="stable"); cum = np.cumsum(tous[k]) / N
    dd = float((np.maximum.accumulate(np.r_[0.0, cum]) - np.r_[0.0, cum]).max())
    mo = ts[k].astype("datetime64[ms]").astype("datetime64[M]")
    mois = {str(u): float(tous[k][mo == u].sum() / N) for u in np.unique(mo)}
    brut = float((tous + 2 * TK).sum() / N); frais = nt * 2 * TK / N
    return {"net_panier_pct": round(100 * float(par.mean()), 3), "pieces": N, "pieces_positives": round(float((par > 0).mean()), 3),
            "trades": nt, "trades_par_piece": round(nt / N, 2), "trades_par_piece_par_an": round(nt / N / ans, 2),
            "gagnants": round(float((tous > 0).mean()), 3), "longs": round(float((R and np.mean([(r[:, 1] > 0).mean() for r in R.values() if len(r)])) or 0), 3),
            "brut_pct": round(100 * brut, 2), "frais_pct": round(100 * frais, 2), "frais_sur_brut": round(frais / brut, 3) if brut > 0 else "brut <= 0",
            "pire_mois_pct": round(100 * min(mois.values()), 2), "pire_mois": min(mois, key=mois.get),
            "mois_positifs": f"{sum(z > 0 for z in mois.values())}/{len(mois)}", "pire_baisse_pts": round(100 * dd, 2),
            "mois_pct": {m_: round(100 * z, 2) for m_, z in mois.items()}}, float(par.mean())


def net_panier(P, g, mode):
    return float(np.mean([trades(x, g, mode, dirs_de(d, mode))[:, 0].sum() for x, d in P.values()]))


def funding_trade(s, x, r):
    """somme des funding payés (négatif = coût) par les trades r de la pièce s, position de taille constante."""
    f = FU[s]; cs = np.r_[0.0, np.cumsum(f[:, 1])]; tot = 0.0
    for net, sens, i0, i1 in r:
        a_, b_ = np.searchsorted(f[:, 0], [x[int(i0), 0], x[int(i1), 0] + JMS // 2])
        tot += -sens * (cs[b_] - cs[a_])
    return tot


O = {"pre_enregistrement": "PREREG-32-journalier.md (commit f09036c)", "grille": GRILLE, "tirages_temoin": NTIR}
PP = {p: tranche(t0, t1) for p, (t0, t1, _) in PER.items()}
for p, P in PP.items(): print(p, len(P), "pièces vivantes au début", flush=True)

# --- 1. choix du réglage sur 2024-25 (et 2026 pour info seulement, calculé APRÈS le figement)
FIG = {}
for vnom, mode in VARS.items():
    tab = [(g, net_panier(PP["2024_2025"], g, mode)) for g in GRILLE]
    FIG[vnom] = max(tab, key=lambda z: z[1])[0]
    O.setdefault("grille_2024_2025_pct", {})[vnom] = {f"s{g[0]:.2f}_a{g[1]:.2f}_t{g[2]:.2f}": round(100 * v, 2) for g, v in tab}
    print(vnom, "réglage figé sur 2024-25 :", FIG[vnom], flush=True)
O["reglage_fige"] = FIG

# --- 2. variantes figées, témoin, funding
graine(32)
for pnom, P in PP.items():
    ans = PER[pnom][2]; O[pnom] = {"pieces": len(P)}
    for vnom, mode in VARS.items():
        g = FIG[vnom]
        R = {s: trades(x, g, mode, dirs_de(d, mode)) for s, (x, d) in P.items()}
        b, net = stats(P, R, ans)
        pls = {s: float((r[:, 1] > 0).mean()) if len(r) else 0.5 for s, r in R.items()}
        Hn = np.empty(NTIR); HN = np.empty(NTIR)
        for j in range(NTIR):
            tot = 0.0; n = 0
            for s, (x, d) in P.items():
                rr = trades(x, g, 2, dirs_de(d, mode), pls[s]); tot += rr[:, 0].sum(); n += len(rr)
            Hn[j] = tot / len(P); HN[j] = n
        b.update({"temoin_moyen_pct": round(100 * float(Hn.mean()), 3), "temoin_ecart_type_pct": round(100 * float(Hn.std()), 3),
                  "temoin_trades_moyen": round(float(HN.mean()), 0), "p": float((Hn >= net).mean())})
        cov = [s for s in R if s in FU and FU[s][0, 0] <= PER[pnom][0] + JMS]
        if cov:
            sans = np.mean([R[s][:, 0].sum() for s in cov]); avec = np.mean([R[s][:, 0].sum() + funding_trade(s, P[s][0], R[s]) for s in cov])
            b["funding_sous_panier"] = {"pieces": len(cov), "net_sans_funding_pct": round(100 * float(sans), 2), "net_avec_funding_pct": round(100 * float(avec), 2)}
        b["meilleures_pieces"] = sorted(((s, round(100 * float(r[:, 0].sum()), 1)) for s, r in R.items()), key=lambda z: -z[1])[:5]
        b["pires_pieces"] = sorted(((s, round(100 * float(r[:, 0].sum()), 1)) for s, r in R.items()), key=lambda z: z[1])[:5]
        O[pnom][vnom] = b
        print(pnom, vnom, g, {k_: w for k_, w in b.items() if k_ != "mois_pct"}, flush=True)
    # (iii) acheter-garder
    bh = {s: float(x[-1, 4] / x[0, 1] - 1 - 2 * TK) for s, (x, _) in P.items()}
    cov = [s for s in bh if s in FU and FU[s][0, 0] <= PER[pnom][0] + JMS]
    fbh = {s: -float(FU[s][(FU[s][:, 0] >= P[s][0][0, 0]) & (FU[s][:, 0] < P[s][0][-1, 0] + JMS), 1].sum()) for s in cov}
    O[pnom]["iii_acheter_garder"] = {"panier_pct": round(100 * float(np.mean(list(bh.values()))), 2), "pieces_positives": round(float(np.mean([v > 0 for v in bh.values()])), 3),
                                     "BTC_pct": round(100 * bh["BTCUSDT"], 2),
                                     "funding_sous_panier": {"pieces": len(cov), "sans_pct": round(100 * float(np.mean([bh[s] for s in cov])), 2),
                                                             "avec_pct": round(100 * float(np.mean([bh[s] + fbh[s] for s in cov])), 2)}}
    print(pnom, "acheter-garder", O[pnom]["iii_acheter_garder"], flush=True)

# --- 3. informations après figement : grille en 2026, contrôle 1 h du jour ambigu
for vnom, mode in VARS.items():
    tab = {f"s{g[0]:.2f}_a{g[1]:.2f}_t{g[2]:.2f}": round(100 * net_panier(PP["2026"], g, mode), 2) for g in GRILLE}
    O.setdefault("grille_2026_info_pct", {})[vnom] = tab
    O.setdefault("grille_2026_positifs", {})[vnom] = f"{sum(v > 0 for v in tab.values())}/36"
    t0, t1, _ = PER["2026"]; nets = []
    for s, (x, d) in PP["2026"].items():
        a = H1[s]; k0, k1 = np.searchsorted(a[:, 0], [t0, t1]); h = a[k0:k1]
        jour = (h[:, 0] // JMS).astype(np.int64); ok = np.r_[True, np.diff(jour) != 0]
        dj = dict(zip((x[:, 0] // JMS).astype(np.int64), dirs_de(d, mode)))
        dh = np.array([dj.get(j_, 0) for j_ in jour], np.int64)
        nets.append(trades(h, FIG[vnom], mode, dh, ok=ok)[:, 0].sum())
    O.setdefault("controle_1h_2026_pct", {})[vnom] = round(100 * float(np.mean(nets)), 3)
print("grille 2026 (info)", O["grille_2026_positifs"], "contrôle 1 h 2026", O["controle_1h_2026_pct"], flush=True)

for vnom in VARS:
    a, b = O["2024_2025"][vnom], O["2026"][vnom]
    ok = a["net_panier_pct"] > 0 and b["net_panier_pct"] > 0 and b["p"] < 0.05
    O.setdefault("verdicts", {})[vnom] = "GAGNE" if ok else ("NON DÉMONTRÉ" if b["net_panier_pct"] > 0 else "PERD")
print("VERDICTS", O["verdicts"])
json.dump(O, open(os.path.join(ICI, "t32.json"), "w"), indent=1, ensure_ascii=False, default=lambda z: z.item() if hasattr(z, "item") else str(z))

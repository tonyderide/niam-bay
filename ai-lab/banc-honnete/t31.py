"""PREREG-31 : règle de Tony en PANIER (253 perpétuels Binance 1 h, morts compris). Règles : PREREG-31-panier-inversion.md
(i) inversion après perte, SL 3 % / +5 % / trailing 1 % (PREREG-28 B figé) ; (ii) sens EMA50 h, SL 5 % / +3 % / trailing 1 % (PREREG-30 figé).
Sortie : même logique que ../sl-trailing/etude.py (bougie ambiguë = SL d'abord). Témoin : sens au hasard, 1 000 tirages."""
import glob, json, os, datetime as dt
import numpy as np
from numba import njit
TK = 0.0005
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../dca-martingale/refait/donnees")
ms = lambda *x: int(dt.datetime(*x, tzinfo=dt.timezone.utc).timestamp() * 1000)
PER = {"2024_2025": (ms(2024, 1, 1), ms(2026, 1, 1)), "2026": (ms(2026, 1, 1), ms(2026, 10, 1))}
VAR = {"i_inversion_apres_perte": dict(mode=0, s=0.03, a=0.05, t=0.01), "ii_sens_ema50": dict(mode=1, s=0.05, a=0.03, t=0.01)}
NTIR = 1000


def couper(a, F=48):   # identique à sl-trailing/etude.py
    plat = np.convolve(a[:, 2] == a[:, 3], np.ones(F, int), "valid") == F if len(a) >= F else np.zeros(0, bool)
    return a[:np.argmax(plat)] if plat.any() else a


def sens_ema(c, N=50):
    """sens[i] = signe(clôture[i-1] - EMA_N[i-1]) : seulement des heures terminées ; 0 pendant la chauffe (3N)."""
    e = np.empty(len(c)); k = 2 / (N + 1); e[0] = c[0]
    for j in range(1, len(c)): e[j] = c[j] * k + e[j - 1] * (1 - k)
    sh = np.where(c > e, 1, -1); sh[:3 * N] = 0
    d = np.zeros(len(c), np.int64); d[1:] = sh[:-1]; return d


@njit(cache=True)
def graine(x):
    np.random.seed(x)


@njit(cache=True)
def chaine(o, h, l, c, s, t, a, mode, dirs, pl, out):
    """mode 0 : inversion après perte (départ long) ; 1 : sens = dirs[i] à l'entrée (0 = attendre) ; 2 : sens au hasard, P(long) = pl.
    Logique de sortie copiée de simuler() (etude.py). out[m] = (rendement net, sens, i entrée, i sortie)."""
    T = len(o); i = 0; m = 0; sv = 1.0
    while i < T:
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


def trades(x, v, mode, dirs, pl=0.5):
    out = np.empty((len(x) + 1, 4)); n = chaine(x[:, 1], x[:, 2], x[:, 3], x[:, 4], v["s"], v["t"], v["a"], mode, dirs, pl, out); return out[:n]


# --- données
DON = {}
for f in sorted(glob.glob(f"{D}/*-1h.npy")):
    s = os.path.basename(f)[:-7]; a = couper(np.load(f))
    if len(a) > 24: DON[s] = (a, sens_ema(a[:, 4]))
univ = json.load(open(os.path.join(D, "../univers.json")))
print(len(DON), "fichiers 1 h ;", len(set(DON) & set(univ)), "dans univers.json", flush=True)
DON = {s: v for s, v in DON.items() if s in univ}

O = {"pre_enregistrement": "PREREG-31-panier-inversion.md (commit b9bebc2)", "variantes": VAR, "tirages_temoin": NTIR}
graine(31)
for pnom, (t0, t1) in PER.items():
    P = {}
    for s, (a, d) in DON.items():
        k0, k1 = np.searchsorted(a[:, 0], [t0, t1])
        if k1 - k0 > 24 and a[k0, 0] - t0 <= 2 * 3600 * 1000: P[s] = (a[k0:k1], d[k0:k1])
    P_ema = P
    P_un = {s: (x, np.ones(len(x), np.int64)) for s, (x, _) in P.items()}   # variante (i) : pas d'attente
    O[pnom] = {"pieces": len(P)}
    for vnom, v in VAR.items():
        P = P_ema if v["mode"] == 1 else P_un
        R = {s: trades(x, v, v["mode"], d) for s, (x, d) in P.items()}
        par_piece = np.array([r[:, 0].sum() for r in R.values()]); N = len(par_piece)
        tous = np.concatenate([r[:, 0] for r in R.values()]); nt = len(tous)
        # courbe et mois du panier (trades rangés par heure de sortie)
        ts = np.concatenate([x[r[:, 3].astype(int), 0] for (x, _), r in zip(P.values(), R.values())])
        k = np.argsort(ts, kind="stable"); cum = np.cumsum(tous[k]) / N
        dd = float((np.maximum.accumulate(np.r_[0.0, cum]) - np.r_[0.0, cum]).max())
        mo = ts[k].astype("datetime64[ms]").astype("datetime64[M]")
        mois = {str(u): float(tous[k][mo == u].sum() / N) for u in np.unique(mo)}
        # témoin : sens au hasard, même part de longs par pièce
        pls = {s: float((r[:, 1] > 0).mean()) if len(r) else 0.5 for s, r in R.items()}
        H = np.empty(NTIR); HN = np.empty(NTIR)
        for j in range(NTIR):
            tot = 0.0; n = 0
            for s, (x, d) in P.items():
                rr = trades(x, v, 2, d, pls[s]); tot += rr[:, 0].sum(); n += len(rr)
            H[j] = tot / N; HN[j] = n
        net = float(par_piece.mean()); p = float((H >= net).mean())
        b = {"net_panier_pct": round(100 * net, 3), "pieces_positives": round(float((par_piece > 0).mean()), 3), "trades": nt, "trades_par_piece": round(nt / N, 1),
             "gagnants": round(float((tous > 0).mean()), 3), "longs": round(float(np.mean([(r[:, 1] > 0).mean() for r in R.values() if len(r)])), 3),
             "brut_pct": round(100 * float((tous + 2 * TK).sum() / N), 2), "frais_pct": round(100 * nt * 2 * TK / N, 2),
             "pire_mois_pct": round(100 * min(mois.values()), 2), "pire_mois": min(mois, key=mois.get), "mois_positifs": f"{sum(z > 0 for z in mois.values())}/{len(mois)}",
             "pire_baisse_pts": round(100 * dd, 2), "temoin_moyen_pct": round(100 * float(H.mean()), 3), "temoin_ecart_type_pct": round(100 * float(H.std()), 3),
             "temoin_trades_moyen": round(float(HN.mean()), 0), "p": p,
             "meilleures_pieces": sorted(((s, round(100 * float(r[:, 0].sum()), 1)) for s, r in R.items()), key=lambda z: -z[1])[:5],
             "pires_pieces": sorted(((s, round(100 * float(r[:, 0].sum()), 1)) for s, r in R.items()), key=lambda z: z[1])[:5],
             "mois_pct": {m_: round(100 * z, 2) for m_, z in mois.items()}}
        O[pnom][vnom] = b
        print(pnom, vnom, {k_: w for k_, w in b.items() if k_ != "mois_pct"}, flush=True)

for vnom in VAR:
    a, b = O["2024_2025"][vnom], O["2026"][vnom]
    ok = a["net_panier_pct"] > 0 and b["net_panier_pct"] > 0 and b["p"] < 0.05
    O.setdefault("verdicts", {})[vnom] = "GAGNE" if ok else ("NON DÉMONTRÉ" if b["net_panier_pct"] > 0 else "PERD")
print("VERDICTS", O["verdicts"])
json.dump(O, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "t31.json"), "w"), indent=1, ensure_ascii=False, default=lambda z: z.item() if hasattr(z, "item") else str(z))

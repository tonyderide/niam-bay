"""PREREG-34 : martingale avec inversion après perte, réglage qui minimise la QUEUE (CVaR 5 % à 3 mois). Règles : PREREG-34-martingale-moindre-risque.md
Règle de sortie et sens : chaine() copiée de ../sl-trailing/regle_tony.py / t31.py ; martingale : jouer() de ../sl-trailing/moins_de_perte.py (mise de base 10 €, 1 000 €).
Lancer : nice -n 10 python t34.py  -> t34.log, t34.json"""
import glob, json, math, os, itertools, datetime as dt
import numpy as np
from numba import njit
TK = 0.0005; ICI = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(ICI, "../dca-martingale/refait/donnees")
ms = lambda *x: int(dt.datetime(*x, tzinfo=dt.timezone.utc).timestamp() * 1000)
P1, P2 = (ms(2024, 1, 1), ms(2026, 1, 1)), (ms(2026, 1, 1), ms(2026, 10, 1))
JOUR = 86400000; FEN = 90 * JOUR; H2 = 2 * 3600000
G = [(s, ac, t) for s in (0.005, 0.01, 0.015, 0.02, 0.03, 0.05) for ac in (0.005, 0.01, 0.015, 0.02, 0.03, 0.05) for t in (0.0025, 0.005, 0.01, 0.015, 0.02, 0.03) if t <= ac]
ARG = [(1.0, 10 ** 6)] + [(m, k) for m in (1.5, 2.0, 3.0) for k in (2, 4, 6, 10 ** 6)]
BASE = 10.0; NTIR = 1000
assert len(G) == 156 and len(G) * len(ARG) == 2028


def couper(a, F=48):   # identique à sl-trailing/etude.py
    plat = np.convolve(a[:, 2] == a[:, 3], np.ones(F, int), "valid") == F if len(a) >= F else np.zeros(0, bool)
    return a[:np.argmax(plat)] if plat.any() else a


@njit(cache=True)
def graine(x):
    np.random.seed(x)


@njit(cache=True)
def chaine(o, h, l, c, s, t, a, mode, pl, out):
    """mode 0 : inversion après perte (départ long) ; mode 2 : sens au hasard, P(long) = pl. Sortie identique à simuler() (etude.py)."""
    T = len(o); i = 0; m = 0; sv = 1.0
    while i < T:
        if mode == 0: sens = sv
        else: sens = 1.0 if np.random.random() < pl else -1.0
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


@njit(cache=True)
def jouer(mise, tfin, k0s, fins, s, m, k, base, out):
    """out[z] = (capital final - 1000, 1 si le capital a touché <= 500 €). Mise après perte x m, base après gain, base après k pertes d'affilée."""
    for z in range(len(k0s)):
        cap = 1000.0; st = base; perdues = 0; mini = cap; j = k0s[z]
        while j < len(mise) and tfin[j] < fins[z]:
            st = min(st, 10 * cap * s)
            cap += st * mise[j]; mini = min(mini, cap)
            if cap < 50: break
            if mise[j] > 0: st = base; perdues = 0
            else:
                perdues += 1
                if perdues >= k: st = base; perdues = 0
                else: st = st * m
            j += 1
        out[z, 0] = cap - 1000; out[z, 1] = 1.0 if mini <= 500 else 0.0


@njit(cache=True)
def parcours(mise, s, m, k, base):
    """parcours continu de toute la tranche : pire baisse depuis un sommet (€)"""
    cap = 1000.0; st = base; perdues = 0; pic = cap; dd = 0.0
    for j in range(len(mise)):
        st = min(st, 10 * cap * s); cap += st * mise[j]; pic = max(pic, cap); dd = max(dd, pic - cap)
        if cap < 50: break
        if mise[j] > 0: st = base; perdues = 0
        else:
            perdues += 1
            if perdues >= k: st = base; perdues = 0
            else: st *= m
    return dd


def tranche(a, per):
    k0, k1 = np.searchsorted(a[:, 0], per); return a[k0:k1]


def trades(x, g, mode=0, pl=0.5):
    out = np.empty((len(x) + 1, 4)); n = chaine(x[:, 1], x[:, 2], x[:, 3], x[:, 4], g[0], g[2], g[1], mode, pl, out); return out[:n]


def preparer(x, R, s):
    return R[:, 0] / s, x[R[:, 2].astype(np.int64), 0].astype(np.int64), x[R[:, 3].astype(np.int64), 0].astype(np.int64)


def departs(x, tdeb, per, pas):
    ds = np.arange(per[0], per[1] - FEN + 1, pas * JOUR, dtype=np.int64)
    ix = np.searchsorted(x[:, 0], ds); ok = ix < len(x)
    ok[ok] &= (x[ix[ok], 0] - ds[ok]) <= H2                        # pièce vivante au départ
    ds = ds[ok]; k0 = np.searchsorted(tdeb, ds); ok = k0 < len(tdeb)
    return k0[ok].astype(np.int64), (ds[ok] + FEN).astype(np.int64)


def fenetres(mise, tfin, k0, fins, s, m, k):
    out = np.empty((len(k0), 2)); jouer(mise, tfin, k0, fins, s, m, k, BASE, out); return out


def mesures(res):
    R, ru = res[:, 0], res[:, 1]; q = max(1, math.ceil(0.05 * len(R)))
    return {"fenetres": len(R), "esperance_e": round(float(R.mean()), 2), "cvar5_e": round(float(np.sort(R)[:q].mean()), 1),
            "p_perte": round(float((R < 0).mean()), 4), "ruine": round(float(ru.mean()), 4), "pire_3_mois_e": round(float(R.min()), 1)}


def melanger(x, rng):   # comme sl-trailing/etude.py et verif_choisie.py (vectorisé)
    k = rng.permutation(len(x)); o, h, l, c = x[k, 1], x[k, 2], x[k, 3], x[k, 4]
    gap = np.r_[1.0, x[1:, 1] / x[:-1, 4]][rng.permutation(len(x))]; no = x[0, 1] * np.cumprod(np.r_[1.0, (c / o)[:-1]] * gap)
    return np.column_stack([x[:, 0], no, h / o * no, l / o * no, c / o * no])


nom = lambda g, mk: {"s": g[0], "a": g[1], "t": g[2], "mult": mk[0], "plafond": "∞" if mk[1] > 100 else mk[1], "mise_base": BASE}

# ---------- données
UN = {s: couper(np.load(f"{D}/{s}USDT-1m.npy"), 2880) for s in ("BTC", "ETH", "SOL")}
univ = set(json.load(open(os.path.join(D, "../univers.json"))))
PAN = {}
for f in sorted(glob.glob(f"{D}/*-1h.npy")):
    s = os.path.basename(f)[:-7]; a = couper(np.load(f))
    if s in univ and len(a) > 24: PAN[s] = a
print("panier :", len(PAN), "pièces 1 h", flush=True)
graine(34)


def terrain_1m(x, per, pas=1):
    """toutes les combinaisons sur une pièce 1 min, une période : dict (g, mk) -> mesures + pire baisse"""
    x = tranche(x, per); T = {}
    for g in G:
        R = trades(x, g); mise, tdeb, tfin = preparer(x, R, g[0]); k0, fins = departs(x, tdeb, per, pas)
        for mk in ARG:
            T[(g, mk)] = {**mesures(fenetres(mise, tfin, k0, fins, g[0], *mk)), "pire_baisse_e": round(float(parcours(mise, g[0], *mk, BASE)), 1), "trades": len(R)}
    return T


def terrain_panier(per, combos, pas=7):
    """combos : liste de (g, mk). Fenêtres mises en commun sur (pièce, départ) ; pire baisse = 95e centile sur les pièces vivantes au début."""
    P = {s: tranche(a, per) for s, a in PAN.items()}; P = {s: x for s, x in P.items() if len(x) > 24}
    vivantes_debut = {s for s, x in P.items() if x[0, 0] - per[0] <= H2}
    gs = sorted({g for g, _ in combos}); acc = {c: ([], [], 0) for c in combos}
    for g in gs:
        mks = [mk for gg, mk in combos if gg == g]
        for s, x in P.items():
            R = trades(x, g); mise, tdeb, tfin = preparer(x, R, g[0]); k0, fins = departs(x, tdeb, per, pas)
            for mk in mks:
                f, d, n = acc[(g, mk)]
                if len(k0): f.append(fenetres(mise, tfin, k0, fins, g[0], *mk))
                if s in vivantes_debut: d.append((s, parcours(mise, g[0], *mk, BASE)))
                acc[(g, mk)] = (f, d, n + len(R))
    T = {}
    for c, (f, d, n) in acc.items():
        dd = np.array([z for _, z in d]); w = max(d, key=lambda z: z[1])
        T[c] = {**mesures(np.concatenate(f)), "pire_baisse_e": round(float(np.quantile(dd, 0.95)), 1), "pire_baisse_pire_piece": [w[0], round(float(w[1]), 1)],
                "pire_baisse_mediane_e": round(float(np.median(dd)), 1), "pieces": len(dd), "trades": n}
    return T


def choisir(T):
    cand = [c for c, v in T.items() if v["esperance_e"] > 0]; signal = "" if cand else "AUCUN candidat à espérance > 0 : meilleure CVaR prise quand même"
    pool = cand or list(T)
    best = max(pool, key=lambda c: (T[c]["cvar5_e"], -T[c]["pire_baisse_e"]))
    dd = min(pool, key=lambda c: (T[c]["pire_baisse_e"], -T[c]["cvar5_e"]))
    return best, dd, len(cand), signal


O = {"pre_enregistrement": "PREREG-34-martingale-moindre-risque.md (commit 9b53175)", "reglages": len(G) * len(ARG)}
C28 = ((0.05, 0.01, 0.01), (3.0, 4))
# ---------- choix A : BTC 1 min 2024-25
TB = terrain_1m(UN["BTC"], P1)
A, Add, nA, sA = choisir(TB)
O["A_choix_btc_2024_2025"] = {"reglage": nom(*A), "mesures_2024_2025": TB[A], "candidats_esperance_pos": nA, "signal": sA,
                             "min_pire_baisse_seule": {"reglage": nom(*Add), "mesures_2024_2025": TB[Add]},
                             "pour_memoire_choix_C_prereg28": TB[C28],
                             "meilleur_par_multiplicateur": {str(m): (lambda c: {"reglage": nom(*c), **TB[c]})(max([c for c in TB if c[1][0] == m and TB[c]["esperance_e"] > 0] or [c for c in TB if c[1][0] == m], key=lambda c: (TB[c]["cvar5_e"], -TB[c]["pire_baisse_e"]))) for m in (1.0, 1.5, 2.0, 3.0)}}
print("A", O["A_choix_btc_2024_2025"], flush=True)
# ---------- choix B : panier 1 h 2024-25
TP = terrain_panier(P1, [(g, mk) for g in G for mk in ARG])
B, Bdd, nB, sB = choisir(TP)
O["B_choix_panier_2024_2025"] = {"reglage": nom(*B), "mesures_2024_2025": TP[B], "candidats_esperance_pos": nB, "signal": sB,
                                "min_pire_baisse_seule": {"reglage": nom(*Bdd), "mesures_2024_2025": TP[Bdd]}, "A_sur_panier_2024_2025": TP[A],
                                "pour_memoire_choix_C_prereg28": TP[C28]}
O["A_choix_btc_2024_2025"]["A_sur_panier_2024_2025"] = TP[A]
print("B", O["B_choix_panier_2024_2025"], flush=True)


# ---------- jugement 2026
def juger_1m(x, c, rng, nmel=100):
    g, mk = c; x = tranche(x, P2); R = trades(x, g); mise, tdeb, tfin = preparer(x, R, g[0]); k0, fins = departs(x, tdeb, P2, 1)
    v = {**mesures(fenetres(mise, tfin, k0, fins, g[0], *mk)), "pire_baisse_e": round(float(parcours(mise, g[0], *mk, BASE)), 1), "trades": len(R)}
    pl = float((R[:, 1] > 0).mean()); H = []
    for _ in range(NTIR):
        Rh = trades(x, g, 2, pl); mh, dh, fh = preparer(x, Rh, g[0]); kh, fnh = departs(x, dh, P2, 1)
        H.append(mesures(fenetres(mh, fh, kh, fnh, g[0], *mk)))
    M = []
    for _ in range(nmel):
        y = melanger(x, rng); Ry = trades(y, g); my, dy, fy = preparer(y, Ry, g[0]); ky, fny = departs(y, dy, P2, 1)
        M.append(mesures(fenetres(my, fy, ky, fny, g[0], *mk)))
    return v, H, M


def juger_panier(c, rng, nmel=20):
    g, mk = c; v = terrain_panier(P2, [c])[c]
    P = {s: tranche(a, P2) for s, a in PAN.items()}; P = {s: x for s, x in P.items() if len(x) > 24}
    PL = {}
    for s, x in P.items():
        R = trades(x, g); PL[s] = float((R[:, 1] > 0).mean()) if len(R) else 0.5
    def pool(gen):
        f = []
        for s, x in P.items():
            y, mode = gen(s, x); R = trades(y, g, mode, PL[s]); mi, de, fi = preparer(y, R, g[0]); k0, fins = departs(y, de, P2, 7)
            if len(k0): f.append(fenetres(mi, fi, k0, fins, g[0], *mk))
        return mesures(np.concatenate(f))
    H = [pool(lambda s, x: (x, 2)) for _ in range(NTIR)]
    M = [pool(lambda s, x: (melanger(x, rng), 0)) for _ in range(nmel)]
    return v, H, M


def resume(v, H, M):
    moy = lambda L, key: round(float(np.mean([h[key] for h in L])), 4 if key in ("p_perte", "ruine") else 2)
    return {**v, "temoin_sens_hasard": {k: moy(H, k) for k in ("esperance_e", "cvar5_e", "p_perte", "ruine")} | {"esperance_ecart_type": round(float(np.std([h["esperance_e"] for h in H])), 2), "tirages": len(H)},
            "p_vs_temoin": float(np.mean([h["esperance_e"] >= v["esperance_e"] for h in H])),
            "prix_melanges": {k: moy(M, k) for k in ("esperance_e", "cvar5_e", "p_perte", "ruine")} | {"melanges": len(M)},
            "part_melanges_aussi_bien": float(np.mean([h["esperance_e"] >= v["esperance_e"] for h in M]))}


def verdict(J):
    risque_bas = all(J[t]["pire_baisse_e"] < 200 and J[t]["ruine"] == 0 for t in J)
    gagnant = all(J[t]["esperance_e"] > 0 and J[t]["p_vs_temoin"] < 0.05 for t in J)
    return "moindre risque ET gagnant" if risque_bas and gagnant else ("moindre risque mais pas d'avantage" if risque_bas else "risque non maîtrisé")


rng = np.random.default_rng(34)
for lab, c in (("A", A), ("B", B)):
    J = {}
    for s in ("BTC", "ETH", "SOL"):
        J[s] = resume(*juger_1m(UN[s], c, rng)); print(lab, s, J[s], flush=True)
    J["panier"] = resume(*juger_panier(c, rng)); print(lab, "panier", J["panier"], flush=True)
    O[f"{lab}_jugement_2026"] = J; O[f"{lab}_verdict"] = verdict(J); print(lab, "VERDICT", O[f"{lab}_verdict"], flush=True)
# pour information : A sur ETH / SOL en 2024-25 (non utilisé pour le choix), et le réglage « pire baisse seule » en 2026
for s in ("ETH", "SOL"):
    x = tranche(UN[s], P1); g, mk = A; R = trades(x, g); mise, tdeb, tfin = preparer(x, R, g[0]); k0, fins = departs(x, tdeb, P1, 1)
    O["A_choix_btc_2024_2025"][f"A_sur_{s}_2024_2025"] = {**mesures(fenetres(mise, tfin, k0, fins, g[0], *mk)), "pire_baisse_e": round(float(parcours(mise, g[0], *mk, BASE)), 1)}
info = {}
for s in ("BTC", "ETH", "SOL"):
    x = tranche(UN[s], P2); g, mk = Add; R = trades(x, g); mise, tdeb, tfin = preparer(x, R, g[0]); k0, fins = departs(x, tdeb, P2, 1)
    info[s] = {**mesures(fenetres(mise, tfin, k0, fins, g[0], *mk)), "pire_baisse_e": round(float(parcours(mise, g[0], *mk, BASE)), 1)}
info["panier"] = terrain_panier(P2, [Add])[Add]
O["A_choix_btc_2024_2025"]["min_pire_baisse_seule"]["info_2026"] = info
print("info pire baisse seule 2026", info, flush=True)
O["tableau_btc_2024_2025"] = [{**nom(*c), **v} for c, v in TB.items()]
O["tableau_panier_2024_2025"] = [{**nom(*c), **v} for c, v in TP.items()]
json.dump(O, open(os.path.join(ICI, "t34.json"), "w"), indent=1, ensure_ascii=False, default=lambda z: z.item() if hasattr(z, "item") else str(z))
print("VERDICTS", O["A_verdict"], "|", O["B_verdict"])

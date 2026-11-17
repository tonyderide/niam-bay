"""PREREG-77 : trois pistes neuves (dette qui gonfle, retard des altcoins sur le BTC à la minute, foule d'un seul côté).
Usage : python t77.py controle   (contrôles de bon sens, prix fabriqués)
        python t77.py officiel   (une seule fois, refuse de tourner si les contrôles n'ont pas passé)"""
import sys, os, json, time, numpy as np
from sim77 import piste1, piste2, piste3, marche

ICI = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.expanduser("~/.cache/banc-honnete")
C4 = ["SOL", "LINK", "ADA", "DOT"]; N2 = ["ATOM", "AVAX", "BCH", "BNB", "XRP", "LTC", "DOGE"]; N13 = N2 + ["BTC"]
FRAIS, GLISSE = 0.0005, 0.0002; COUT = 2 * (FRAIS + GLISSE)            # 0,14 % l'aller-retour, partout
N = 1004 * 1440; NJ = N // 5; ND = 1004; OFFS = 61 * 288                 # prix depuis le 01/01/2024, metrics depuis le 01/11/2023
I_REG, I_JUG = 31 * 1440, 731 * 1440                                     # 01/02/2024 et 01/01/2026
PER2 = {"reg": (I_REG, I_JUG), "jug": (I_JUG, N), "tout": (I_REG, N)}
PER1 = {k: (a // 5, (b - 2882) // 5) for k, (a, b) in PER2.items()}
PER3 = {"reg": (31, 731), "jug": (731, 1003), "tout": (31, 1003)}
G2 = [(k, tau, h) for k in (1, 5) for tau in (0.003, 0.006) for h in (1, 5, 15)]
G1 = [(q, h) for q in (0.90, 0.975) for h in (240, 1440)]
G3 = [(a, h) for a in (0.10, 0.025) for h in (1, 3)]
MIN_REG = {1: 40, 2: 200, 3: 40}; MIN_JUG = 30; ALPHA = 0.05 / 3; TIRAGES = 2000; GRAINE = 7700
R_, E_, V_ = np.empty(N), np.empty(N, np.int64), np.empty(N)


# ---------- signaux (rien du futur) ----------
def sig2(cb, k, tau):
    r = np.zeros(len(cb)); r[k:] = cb[k:] / cb[:-k] - 1
    return np.where(r >= tau, 1, np.where(r <= -tau, -1, 0)).astype(np.int8)


def seuil_jour(x, q, jours=90, mini=0.5):
    """seuil[D] = quantile q des valeurs à 5 min des `jours` jours AVANT le jour D (NaN si trop de trous)"""
    nd = len(x) // 288; s = np.full(nd, np.nan)
    for D in range(1, nd):
        w = x[288 * max(0, D - jours):288 * D]; ok = ~np.isnan(w)
        if ok.sum() >= mini * 288 * jours: s[D] = np.quantile(w[ok], q)
    return s


def flag1(oi, q):
    X = np.full(len(oi), np.nan); X[288:] = oi[288:] / oi[:-288] - 1          # hausse de la dette sur 24 h, par créneau
    thr = np.repeat(seuil_jour(X, q), 288); prec = np.concatenate([[np.nan], X[:-1]])   # valeur du créneau d'avant (publiée)
    with np.errstate(invalid="ignore"): f = prec >= thr
    return f[OFFS:OFFS + NJ]


def stag1(c):
    Y = np.full(NJ, np.nan); j = np.arange(289, NJ); Y[289:] = np.abs(c[5 * j - 1] / c[5 * j - 1 - 1440] - 1)
    med = np.repeat(seuil_jour(Y, 0.5, mini=8000 / (288 * 90)), 288)
    with np.errstate(invalid="ignore"): return Y <= med


def sig3(ls, a):
    s = np.zeros(ND, np.int8)
    for d in range(29, ND):
        g = 288 * (d + 61); der = ls[g - 12:g]; der = der[~np.isnan(der)]; w = ls[g - 288 * 90:g]; w = w[~np.isnan(w)]
        if len(der) == 0 or len(w) < 0.5 * 288 * 90: continue
        if der[-1] >= np.quantile(w, 1 - a): s[d] = -1          # foule très longue -> short
        elif der[-1] <= np.quantile(w, a): s[d] = 1             # foule très courte -> long
    return s


# ---------- jeu d'une pièce ----------
def joue(piste, P, cfg, per, off=0, lat=0):
    if piste == 2:
        a, b = PER2[per]; n = piste2(P["sig"][cfg[:2]], P["o"], off, cfg[2], lat, a, b, COUT, R_, E_); return R_[:n].copy(), None
    if piste == 1:
        a, b = PER1[per]; n, ns = piste1(P["flag"][cfg[0]], P["stag"], P["o"], P["h"], P["l"], P["c"], off, cfg[1], a, b, COUT, R_, E_, V_)
        return R_[:n].copy(), V_[:ns].copy()
    a, b = PER3[per]; n = piste3(P["sig"][cfg[0]], P["o"], off, cfg[1], a, b, COUT, R_, E_); return R_[:n].copy(), None


def ensemble(piste, T, cfg, per, off=0, lat=0):
    rs = [joue(piste, P, cfg, per, off, lat) for P in T.values()]
    return np.concatenate([r for r, _ in rs]), (np.concatenate([v for _, v in rs]) if piste == 1 else None)


def decalage(piste, rng):
    if piste == 2: return 1440 * int(rng.integers(7, ND - 7))
    if piste == 1: return 288 * int(rng.integers(30, ND - 30))
    return int(rng.integers(30, ND - 30))


def temoin(piste, T, cfg, per, reel, tirages, graine, vol=None):
    """mêmes règles, signaux décalés d'un nombre entier de jours tiré au hasard (le même pour toutes les pièces d'un tirage)"""
    rng = np.random.default_rng(graine); m = np.full(tirages, np.nan); mv = np.full(tirages, np.nan); nn = np.zeros(tirages)
    for k in range(tirages):
        r, v = ensemble(piste, T, cfg, per, decalage(piste, rng)); nn[k] = len(r)
        if len(r): m[k] = r.mean()
        if v is not None and len(v): mv[k] = v.mean()
    out = {"moy": float(np.nanmean(m)), "sd": float(np.nanstd(m)), "trades_moy": float(nn.mean()),
           "p": float((1 + np.sum(~(m < reel))) / (tirages + 1))}
    if vol is not None: out["vol_moy"] = float(np.nanmean(mv)); out["vol_p"] = float((1 + np.sum(~(mv < vol))) / (tirages + 1))
    return out


def stat(r):
    if len(r) == 0: return {"n": 0, "moy": None, "se": None, "somme": 0.0, "gagnants": None}
    return {"n": int(len(r)), "moy": float(r.mean()), "se": float(r.std(ddof=1) / np.sqrt(len(r))) if len(r) > 1 else None,
            "somme": float(r.sum()), "gagnants": float(np.mean(r > 0))}


# ---------- chargement ----------
def prix(c):
    a = np.load(f"{CACHE}/m1-binance/{c}.npy"); assert a.shape == (N, 5) and a[0, 0] == 1704067200000, c
    return {k: np.ascontiguousarray(a[:, i]) for i, k in enumerate("ohlc", 1)}


def terrain(piste, pieces, cb=None, faux=None):
    """faux = {pièce: (o,h,l,c)} pour remplacer les vrais prix par des prix fabriqués (contrôles)"""
    T = {}
    for c in pieces:
        nom = c.split("#")[0]; P = dict(zip("ohlc", faux[c])) if faux else prix(nom)
        if piste == 2: P["sig"] = {(k, tau): sig2(cb, k, tau) for k in (1, 5) for tau in (0.003, 0.006)}
        else:
            M = np.load(f"{CACHE}/metrics-77/{nom}.npy"); assert len(M) == OFFS + NJ
            if piste == 1: P["flag"] = {q: flag1(M[:, 0], q) for q in (0.90, 0.975)}; P["stag"] = stag1(P["c"])
            else: P["sig"] = {a: sig3(M[:, 4], a) for a in (0.10, 0.025)}
        T[c] = P
    return T


# ---------- contrôles de bon sens ----------
def controle():
    res = {}; ok = True; Z = np.zeros(N); cb = prix("BTC")["c"]
    def note(nom, cond, **k):
        nonlocal ok; ok &= bool(cond); res[nom] = dict(k, passe=bool(cond)); print(("OK   " if cond else "RATÉ ") + nom, json.dumps(k, default=float), flush=True)
    plat = (np.full(N, 100.0),) * 4
    # piste 2
    T = terrain(2, ["A", "B", "C", "D"], cb, {c: marche(N, 0.0008, 100 + i, Z) for i, c in enumerate("ABCD")})
    pire = 0.0
    for cfg in G2:
        r, _ = ensemble(2, T, cfg, "tout"); s = stat(r); pire = max(pire, abs(s["moy"] + COUT) / s["se"])
    note("P2 marche au hasard : net = -cout sur les 12 réglages (écart max en erreurs types, seuil 3,5)", pire <= 3.5, ecart_max=pire)
    r, _ = ensemble(2, T, G2[0], "tout"); t = temoin(2, T, G2[0], "tout", r.mean(), 300, 1)
    note("P2 marche au hasard : p du témoin ni extrême ni collé", 0.01 <= t["p"] <= 0.99, p=t["p"], n=len(r), moy=r.mean(), temoin=t["moy"])
    r, _ = ensemble(2, terrain(2, ["A"], cb, {"A": plat}), G2[0], "tout")
    note("P2 prix plats : chaque trade = -cout exactement", len(r) > 0 and np.allclose(r, -COUT, atol=1e-12), n=len(r))
    d = np.zeros(N); d[2:] = np.log(cb[1:-1] / cb[:-2])
    T = terrain(2, ["A"], cb, {"A": marche(N, 0.0008, 200, d)}); r, _ = ensemble(2, T, G2[0], "tout"); t = temoin(2, T, G2[0], "tout", r.mean(), 300, 2)
    note("P2 retard d'une minute planté : la règle le trouve (net > +0,10 % et p < 0,01)", r.mean() > 0.001 and t["p"] < 0.01, moy=r.mean(), p=t["p"], n=len(r))
    # piste 1
    noms = [f"{c}#{g}" for c in C4 for g in range(5)]
    F = {x: marche(N, 0.0008, 300 + i, Z) for i, x in enumerate(noms)}
    T = terrain(1, noms, faux=F); r, _ = ensemble(1, T, G1[1], "tout"); s = stat(r); t = temoin(1, T, G1[1], "tout", r.mean(), 300, 3)
    note("P1 marche au hasard (vraie dette, faux prix) : net = -cout à 3 erreurs types + 0,02 %", abs(s["moy"] + COUT) <= 3 * s["se"] + 0.0002, **s)
    note("P1 marche au hasard : p du témoin ni extrême ni collé", 0.01 <= t["p"] <= 0.99, p=t["p"], temoin=t["moy"])
    # piste 3
    T = terrain(3, noms, faux=F); r, _ = ensemble(3, T, G3[0], "tout"); s = stat(r); t = temoin(3, T, G3[0], "tout", r.mean(), 300, 4)
    note("P3 marche au hasard (vrais ratios, faux prix) : net = -cout à 3 erreurs types", abs(s["moy"] + COUT) <= 3 * s["se"], **s)
    note("P3 marche au hasard : p du témoin ni extrême ni collé", 0.01 <= t["p"] <= 0.99, p=t["p"], temoin=t["moy"])
    r, _ = ensemble(3, terrain(3, ["SOL"], faux={"SOL": plat}), G3[0], "tout")
    note("P3 prix plats : chaque trade = -cout exactement", len(r) > 0 and np.allclose(r, -COUT, atol=1e-12), n=len(r))
    sg = sig3(np.load(f"{CACHE}/metrics-77/SOL.npy")[:, 4], 0.10); d = np.zeros(N)
    for j in range(ND - 1): d[1440 * j + 5:1440 * (j + 1) + 5] = sg[j] * 0.005 / 1440
    T = terrain(3, ["SOL"], faux={"SOL": marche(N, 0.0008, 400, d)}); r, _ = ensemble(3, T, G3[0], "tout"); t = temoin(3, T, G3[0], "tout", r.mean(), 300, 5)
    note("P3 dérive plantée dans le sens du signal : la règle la trouve (net > 0 et p < 0,01)", r.mean() > 0 and t["p"] < 0.01, moy=r.mean(), p=t["p"], n=len(r))
    res["tout_passe"] = ok; json.dump(res, open(f"{ICI}/controle.json", "w"), indent=1, ensure_ascii=False, default=float)
    print("CONTRÔLES :", "TOUS PASSÉS" if ok else "AU MOINS UN RATÉ", flush=True)


# ---------- officiel ----------
def verdict(reg, j4, jn):
    if j4["n"] < MIN_JUG or jn["n"] < MIN_JUG: return "NON ÉVALUABLE"
    if reg["moy"] > 0 and j4["moy"] > 0 and j4["temoin"]["p"] < ALPHA and jn["moy"] > 0 and jn["temoin"]["p"] < 0.05: return "DÉMONTRÉ"
    if j4["moy"] <= 0 and jn["moy"] <= 0: return "PERD"
    return "NON DÉMONTRÉ"


def officiel():
    assert json.load(open(f"{ICI}/controle.json"))["tout_passe"], "contrôles de bon sens non passés"
    assert not os.path.exists(f"{ICI}/t77.json"), "déjà lancé : le jugement est unique"
    cb = prix("BTC")["c"]; out = {"cout_aller_retour": COUT, "alpha": ALPHA, "tirages": TIRAGES}
    for piste, grille, neuves, nom in ((1, G1, N13, "dette qui gonfle, prix calme"), (2, G2, N2, "retard des altcoins sur le BTC"), (3, G3, N13, "foule d'un seul côté")):
        t0 = time.time(); T4 = terrain(piste, C4, cb); TN = terrain(piste, neuves, cb); o = {"nom": nom, "reglage": []}
        for cfg in grille:
            s = stat(ensemble(piste, T4, cfg, "reg")[0]); s["cfg"] = list(cfg); o["reglage"].append(s)
        cand = [s for s in o["reglage"] if s["n"] >= MIN_REG[piste]]
        print(f"\n=== PISTE {piste} : {nom} ===\nRéglage (4 paires, 02/2024-12/2025) :", flush=True)
        for s in o["reglage"]: print("  ", s["cfg"], "trades", s["n"], "net moyen %.4f %%" % (100 * s["moy"]) if s["n"] else "", "somme %.1f %%" % (100 * s["somme"]), flush=True)
        if not cand:
            o["verdict"] = "NON ÉVALUABLE"; out[f"piste{piste}"] = o; print("aucun réglage n'atteint le minimum de trades -> NON ÉVALUABLE"); continue
        ch = max(cand, key=lambda s: s["moy"]); cfg = tuple(ch["cfg"]); o["choisi"] = ch; print("choisi :", cfg, flush=True)
        for cle, T in (("jug4", T4), ("jugN", TN)):
            r, v = ensemble(piste, T, cfg, "jug"); s = stat(r)
            s["par_piece"] = {c: stat(joue(piste, P, cfg, "jug")[0]) for c, P in T.items()}
            if s["n"]:
                s["temoin"] = temoin(piste, T, cfg, "jug", r.mean(), TIRAGES, GRAINE + 10 * piste + (cle == "jugN"), vol=(v.mean() if piste == 1 and len(v) else None))
                if piste == 1: s["signaux"] = int(len(v)); s["vol_apres_signal"] = float(v.mean()) if len(v) else None
            else: s["temoin"] = {"p": 1.0}
            o[cle] = s
            print(f"JUGEMENT 2026, {'4 paires' if cle == 'jug4' else 'paires neuves'} : trades {s['n']}, net moyen {100 * s['moy'] if s['n'] else float('nan'):.4f} %, somme {100 * s['somme']:.1f} %, gagnants {s['gagnants']}, témoin {s['temoin']}", flush=True)
        o["info_neuves_reglage"] = stat(ensemble(piste, TN, cfg, "reg")[0])
        if piste == 2: o["info_retard_1min"] = {"jug4": stat(ensemble(2, T4, cfg, "jug", lat=1)[0]), "jugN": stat(ensemble(2, TN, cfg, "jug", lat=1)[0]), "reg4": stat(ensemble(2, T4, cfg, "reg", lat=1)[0])}
        o["verdict"] = verdict(ch, o["jug4"], o["jugN"]); o["secondes"] = time.time() - t0
        print("info :", {k: v for k, v in o.items() if k.startswith("info")}, "\nVERDICT PISTE", piste, ":", o["verdict"], flush=True)
        out[f"piste{piste}"] = o
    json.dump(out, open(f"{ICI}/t77.json", "w"), indent=1, ensure_ascii=False, default=float)


if __name__ == "__main__":
    {"controle": controle, "officiel": officiel}[sys.argv[1]]()

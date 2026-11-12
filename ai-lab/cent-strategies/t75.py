"""PREREG-75 : 100 stratégies, choix sur P1 (4 paires), contrôles P2 + 30 paires neuves, témoin hasard (prix mélangés).
Usage : python t75.py liste | prevol | tout"""
import sys, os, json, time, hashlib, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from moteur import (simg, simd, horaire, ema, rsi, atr, adx, boll, vol24_calme, atr_jour, prev, donchian, supertrend,
                    tsmom, etat_rev, cassure_bb, volbreak, sgn, danger, tendance, CAP0)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "banc-honnete"))
from t69 import couper, ms  # noqa: E402

ICI = os.path.dirname(os.path.abspath(__file__))
D1H = os.path.join(ICI, "..", "dca-martingale", "refait", "donnees")
M1 = "/tmp/claude-1000/-home-tony-projets-tonyderide-martin/4e81611e-b9db-4354-98b5-7975f809d2e0/scratchpad/m1"
C4 = ["SOL", "LINK", "ADA", "DOT"]
C6 = ["ATOM", "AVAX", "BCH", "BNB", "XRP", "LTC"]
EXCLU = set(C4 + C6 + ["DOGE", "BTC", "ETH", "USDC", "BTCDOM", "DEFI", "FOOTBALL", "BLUEBIRD"])
PER = {"P1": (ms(2024, 2, 1), ms(2026, 1, 1)), "P2": (ms(2026, 1, 1), ms(2026, 10, 1))}
GRAINE_PAIRES, N_NEUVES, N_HASARD, GRAINE_HASARD = 75, 24, 50, 7500

# ------------------------------------------------------------------------------------------- les 100 stratégies
G0 = dict(esp=0.05, nl=5, capx=5.0, npl=1.0, side=0, off=None, flt=0, dg=1, prot=1, stopf=0.85, ka=0.0)
def G(nom, txt, **kw):
    d = dict(G0); d.update(kw); return ("G", nom, txt, d)
D0 = dict(L=2.0, slp=0.0, ta=0.0, tt=0.0, atrk=0.0, tpp=0.0, reentry=1, hold=0, mart=0)
def D(nom, txt, sig, **kw):
    d = dict(D0); d.update(kw); return ("D", nom, txt, sig, d)

S = [
    G("W5", "grille en service (témoin) : écart 5 %, 5 niveaux, plafond 5×"),
    G("W3", "écart 3 %", esp=0.03), G("W4", "écart 4 %", esp=0.04), G("W6", "écart 6 %", esp=0.06),
    G("W8", "écart 8 %", esp=0.08), G("W12", "écart 12 %", esp=0.12), G("W15", "écart 15 %", esp=0.15),
    G("W5-N3", "5 %, 3 niveaux, plafond 3×", nl=3, capx=3.0), G("W5-N7", "5 %, 7 niveaux, plafond 7×", nl=7, capx=7.0),
    G("W5-N9", "5 %, 9 niveaux, plafond 9×", nl=9, capx=9.0), G("W3-N7", "3 %, 7 niveaux, plafond 7×", esp=0.03, nl=7, capx=7.0),
    G("W5-x0.5", "5 %, demi-taille par niveau (plafond 2,5×)", npl=0.5, capx=2.5),
    G("W5-x2", "5 %, double taille par niveau (plafond 10×)", npl=2.0, capx=10.0),
    G("W5-cap2", "5 %, plafond d'exposition 2×", capx=2.0), G("W5-cap3", "5 %, plafond 3×", capx=3.0),
    G("W3-x2", "3 %, double taille (plafond 10×)", esp=0.03, npl=2.0, capx=10.0),
    G("W5-L", "5 %, long seul", side=1), G("W5-S", "5 %, short seul", side=-1),
    G("W3-L", "3 %, long seul", esp=0.03, side=1), G("W3-S", "3 %, short seul", esp=0.03, side=-1),
    G("W8-L", "8 %, long seul", esp=0.08, side=1), G("W8-S", "8 %, short seul", esp=0.08, side=-1),
    G("W3-F", "3 %, filtre de sens EMA50/200 1 h", esp=0.03, flt=1), G("W8-F", "8 %, filtre EMA50/200", esp=0.08, flt=1),
    G("W5-F20", "5 %, filtre de sens EMA20/100 1 h", flt=2), G("W5-F200", "5 %, sens = clôture 1 h vs EMA200", flt=3),
    G("W5-A20", "5 %, entrées seulement si ADX14 1 h < 20", flt=4), G("W5-A25", "5 %, ADX < 25", flt=5),
    G("W5-A30", "5 %, ADX < 30", flt=6), G("W3-A25", "3 %, ADX < 25", esp=0.03, flt=5),
    G("W5-calme", "5 %, entrées seulement si vol. 24 h < médiane 30 j", flt=7),
    G("W5-agité", "5 %, entrées seulement si vol. 24 h > médiane 30 j", flt=8),
    G("W3-calme", "3 %, vol. calme", esp=0.03, flt=7),
    G("W5-L-hausse", "5 %, long seul, entrées seulement si EMA50 > EMA200", side=1, flt=9),
    G("W3-L-hausse", "3 %, long seul, EMA50 > EMA200", esp=0.03, side=1, flt=9),
    G("W-ATR1", "écart = 1 × ATR14 journalier", ka=1.0), G("W-ATR2", "écart = 2 × ATR journalier", ka=2.0),
    G("W-ATR3", "écart = 3 × ATR journalier", ka=3.0),
    G("W5-sansDJ", "5 %, sans disjoncteur RSI<25", dg=0), G("W5-sansProt", "5 %, sans protection SL/TP 15 min", prot=0),
    G("W5-gf80", "5 %, garde-fou à −20 %", stopf=0.80), G("W5-gf90", "5 %, garde-fou à −10 %", stopf=0.90),
    G("W5-miroir", "5 %, 3 achats / 2 ventes", off=2.5), G("W3-miroir", "3 %, 3 achats / 2 ventes", esp=0.03, off=2.5),
    G("W5-A25-F", "5 %, ADX < 25 + filtre EMA50/200", flt=10), G("W8-N7", "8 %, 7 niveaux, plafond 7×", esp=0.08, nl=7, capx=7.0),
    G("W5-S-baisse", "5 %, short seul, entrées seulement si EMA50 < EMA200", side=-1, flt=11),
    G("W12-x2", "12 %, double taille (plafond 10×)", esp=0.12, npl=2.0, capx=10.0),
    G("W4-L", "4 %, long seul", esp=0.04, side=1), G("W6-A25", "6 %, ADX < 25", esp=0.06, flt=5),
    # ---- suivi de tendance
    D("X12/26", "croisement EMA 12/26 h, toujours en position", ("emax", 12, 26, 0)),
    D("X20/50", "croisement EMA 20/50 h", ("emax", 20, 50, 0)), D("X50/200", "croisement EMA 50/200 h", ("emax", 50, 200, 0)),
    D("X10/30", "croisement EMA 10/30 h", ("emax", 10, 30, 0)),
    D("X20/50-L", "EMA 20/50, long seul", ("emax", 20, 50, 1)), D("X50/200-L", "EMA 50/200, long seul", ("emax", 50, 200, 1)),
    D("X20/50-ATR", "EMA 20/50 + stop suiveur 3 ATR jour", ("emax", 20, 50, 0), atrk=3.0, reentry=0),
    D("X50/200-ATR", "EMA 50/200 + stop suiveur 3 ATR jour", ("emax", 50, 200, 0), atrk=3.0, reentry=0),
    D("X20/50-L5", "EMA 20/50, levier 5", ("emax", 20, 50, 0), L=5.0), D("X50/200-L1", "EMA 50/200, levier 1", ("emax", 50, 200, 0), L=1.0),
    D("DC24", "cassure Donchian 24 h, sortie canal 12 h", ("donch", 24, 12, 0)),
    D("DC72", "Donchian 72 h / 36 h", ("donch", 72, 36, 0)), D("DC168", "Donchian 168 h / 84 h", ("donch", 168, 84, 0)),
    D("DC480", "Donchian 480 h / 240 h", ("donch", 480, 240, 0)),
    D("DC168-ATR3", "Donchian 168 h + stop suiveur 3 ATR jour", ("donch", 168, 84, 0), atrk=3.0, reentry=0),
    D("DC72-ATR2", "Donchian 72 h + stop suiveur 2 ATR jour", ("donch", 72, 36, 0), atrk=2.0, reentry=0),
    D("DC168-L", "Donchian 168 h, long seul", ("donch", 168, 84, 1)),
    D("DC480-L1", "Donchian 480 h, levier 1", ("donch", 480, 240, 0), L=1.0),
    D("DC480-L5", "Donchian 480 h, levier 5", ("donch", 480, 240, 0), L=5.0),
    D("DC168-SL5TP10", "Donchian 168 h, SL 5 %, TP 10 %", ("donch", 168, 84, 0), slp=0.05, tpp=0.10, reentry=0),
    D("ST2", "stop-and-reverse 2 ATR jour (supertrend)", ("st", 2.0)), D("ST3", "supertrend 3 ATR jour", ("st", 3.0)),
    D("TSM7", "momentum 7 jours (signe), revu chaque jour", ("tsm", 7, 0)), D("TSM30", "momentum 30 jours", ("tsm", 30, 0)),
    D("TSM7-L", "momentum 7 jours, long seul", ("tsm", 7, 1)),
    D("MACD", "MACD 48/104/36 h, toujours en position", ("macd", 0)),
    D("MACD-L200", "MACD, long seul au-dessus de l'EMA200 h", ("macd", 1)),
    D("VB3", "mouvement horaire > 3 ATR h : suivre 24 h, SL 3 %", ("vb", 3.0, 24), slp=0.03, reentry=0),
    # ---- retour à la moyenne
    D("RSI30/70", "RSI14 h < 30 achat, > 70 vente, sortie à 50, SL 5 %", ("rsi", 30, 70, 0, 0), slp=0.05, reentry=0),
    D("RSI30-L", "RSI14 h < 30 achat seul, SL 5 %", ("rsi", 30, 70, 1, 0), slp=0.05, reentry=0),
    D("RSI20/80", "RSI 20/80, SL 5 %", ("rsi", 20, 80, 0, 0), slp=0.05, reentry=0),
    D("RSI30/70-E200", "RSI 30/70 dans le sens de l'EMA200 h, SL 5 %", ("rsi", 30, 70, 0, 1), slp=0.05, reentry=0),
    D("RSI30/70-L5", "RSI 30/70, levier 5, SL 5 %", ("rsi", 30, 70, 0, 0), L=5.0, slp=0.05, reentry=0),
    D("BB20/2", "Bollinger 20 h 2σ : contre la sortie de bande, sortie à la moyenne, SL 5 %", ("bb", 20, 2.0, 0, 0), slp=0.05, reentry=0),
    D("BB20/3", "Bollinger 20 h 3σ, SL 5 %", ("bb", 20, 3.0, 0, 0), slp=0.05, reentry=0),
    D("BB20/2-L", "Bollinger 20/2, long seul, SL 5 %", ("bb", 20, 2.0, 1, 0), slp=0.05, reentry=0),
    D("BB20/2.5-E200", "Bollinger 20/2,5 dans le sens de l'EMA200 h, SL 5 %", ("bb", 20, 2.5, 0, 1), slp=0.05, reentry=0),
    D("BB20/2-L5", "Bollinger 20/2, levier 5, SL 5 %", ("bb", 20, 2.0, 0, 0), L=5.0, slp=0.05, reentry=0),
    D("BBX20/2", "Bollinger 20/2 en cassure (dans le sens), sortie à la moyenne", ("bbx", 20, 2.0)),
    D("BB480/2", "Bollinger lent 480 h 2σ, SL 8 %", ("bb", 480, 2.0, 0, 0), slp=0.08, reentry=0),
    # ---- sens EMA de PREREG-30 (sortie de Tony : SL fixe, trailing activé à +a, distance t ; sens lu à plat seulement)
    D("E30-L1", "PREREG-30 figé : EMA50 h, SL 5 %, trailing +3 %/1 %, levier 1", ("pxema", 50), L=1.0, slp=0.05, ta=0.03, tt=0.01, hold=1),
    D("E30-L2", "PREREG-30 figé, levier 2", ("pxema", 50), slp=0.05, ta=0.03, tt=0.01, hold=1),
    D("E30-L5", "PREREG-30 figé, levier 5", ("pxema", 50), L=5.0, slp=0.05, ta=0.03, tt=0.01, hold=1),
    D("E30-EMA20", "PREREG-30, EMA20", ("pxema", 20), slp=0.05, ta=0.03, tt=0.01, hold=1),
    D("E30-EMA200", "PREREG-30, EMA200", ("pxema", 200), slp=0.05, ta=0.03, tt=0.01, hold=1),
    D("E30-3/2/1", "PREREG-30, SL 3 %, trailing +2 %/1 %", ("pxema", 50), slp=0.03, ta=0.02, tt=0.01, hold=1),
    D("E30-8/5/2", "PREREG-30, SL 8 %, trailing +5 %/2 %", ("pxema", 50), slp=0.08, ta=0.05, tt=0.02, hold=1),
    D("E30-mart", "PREREG-30 + martingale ×2 plafonnée à 3 doublements (base levier 1)", ("pxema", 50), L=1.0, slp=0.05, ta=0.03, tt=0.01, hold=1, mart=1),
    D("E30-ADX25", "PREREG-30, seulement si ADX14 h > 25", ("pxema_adx", 50, 25), slp=0.05, ta=0.03, tt=0.01, hold=1),
    # ---- référence
    D("BH", "achat-conservation, levier 1 (mêmes garde-fous)", ("bh",), L=1.0),
]
assert len(S) == 100 and len({s[1] for s in S}) == 100


# ------------------------------------------------------------------------------------------- préparation d'un terrain
class Terrain:
    def __init__(self, a, base_1m):
        self.t = a[:, 0].astype(np.int64); self.o, self.h, self.l, self.c = (a[:, k].copy() for k in (1, 2, 3, 4))
        self.m1 = base_1m; self.bpd = 1440 if base_1m else 24; self.chk = 900_000 if base_1m else 3_600_000
        self.DG = danger(self.t, self.c); self.UP = tendance(self.t, self.c)
        self.T, self.O, self.H, self.L, self.C, self.hid = horaire(self.t, self.o, self.h, self.l, self.c)
        self.ATRd = atr_jour(self.T, self.H, self.L, self.C); self._fl = {}; self._tg = {}

    def FL(self, code):
        if code in self._fl: return self._fl[code]
        n = len(self.t); up = self.UP
        if code == 0: F = np.full(n, 3, np.int8)
        elif code in (1, 9, 10, 11):
            F = np.where(up > 0, 1, np.where(up < 0, 2, 3)).astype(np.int8)
            if code == 9: F = np.where(up > 0, 1, 0).astype(np.int8)
            if code == 11: F = np.where(up < 0, 2, 0).astype(np.int8)
            if code == 10:
                A = prev(adx(self.H, self.L, self.C, 14), self.hid); F = np.where(A < 25, F, 0).astype(np.int8)
        elif code == 2:
            x = prev(ema(self.C, 20) - ema(self.C, 100), self.hid); F = np.where(np.isnan(x), 3, np.where(x >= 0, 1, 2)).astype(np.int8)
        elif code == 3:
            x = prev(self.C - ema(self.C, 200), self.hid); F = np.where(np.isnan(x), 3, np.where(x >= 0, 1, 2)).astype(np.int8)
        elif code in (4, 5, 6):
            A = prev(adx(self.H, self.L, self.C, 14), self.hid); F = np.where(A < {4: 20, 5: 25, 6: 30}[code], 3, 0).astype(np.int8)
        elif code in (7, 8):
            v = prev(vol24_calme(self.C).astype(float), self.hid); F = np.where(v == (1 if code == 7 else -1), 3, 0).astype(np.int8)
        self._fl[code] = F; return F

    def ESP(self, ka):
        return np.nan_to_num(ka * prev(self.ATRd / self.C, self.hid), nan=0.05)

    def TGT(self, sig):
        if sig in self._tg: return self._tg[sig]
        T, H, L, C = self.T, self.H, self.L, self.C; k = sig[0]
        if k == "emax": g = sgn(ema(C, sig[1]) - ema(C, sig[2]), sig[3])
        elif k == "pxema": g = sgn(C - ema(C, sig[1]))
        elif k == "pxema_adx":
            g = sgn(C - ema(C, sig[1])); A = adx(H, L, C, 14); g = np.where(A > sig[2], g, 0).astype(np.int8)
        elif k == "donch": g = donchian(H, L, C, sig[1], sig[2], sig[3])
        elif k == "st": g = supertrend(C, self.ATRd, sig[1])
        elif k == "tsm": g = tsmom(T, C, sig[1], sig[2])
        elif k == "macd":
            e1 = C.copy(); e2 = C.copy(); a1, a2 = 2 / 49, 2 / 105
            for i in range(1, len(C)): e1[i] = e1[i - 1] + a1 * (C[i] - e1[i - 1]); e2[i] = e2[i - 1] + a2 * (C[i] - e2[i - 1])
            m = e1 - e2; sg = m.copy(); a3 = 2 / 37
            for i in range(1, len(C)): sg[i] = sg[i - 1] + a3 * (m[i] - sg[i - 1])
            d = m - sg; d[:140] = np.nan
            if sig[1]:
                e200 = ema(C, 200); g = np.where((d > 0) & (C > e200), 1, 0).astype(np.int8)
            else: g = sgn(d)
        elif k == "vb": g = volbreak(C, atr(H, L, C, 14), sig[1], sig[2])
        elif k in ("rsi", "bb"):
            fl = np.zeros(len(C), np.int8)
            if sig[4]:
                e = ema(C, 200); fl = np.where(np.isnan(e), 0, np.where(C > e, 1, -1)).astype(np.int8)
            if k == "rsi":
                X = rsi(C, 14); n = len(C)
                g = etat_rev(X, np.full(n, float(sig[1])), np.full(n, float(sig[2])), np.full(n, 50.0), np.full(n, 50.0), sig[3], fl)
            else:
                mu, up, lo = boll(C, sig[1], sig[2]); g = etat_rev(C, lo, up, mu, mu, sig[3], fl)
        elif k == "bbx":
            mu, up, lo = boll(C, sig[1], sig[2]); g = cassure_bb(C, mu, up, lo)
        elif k == "bh": g = np.ones(len(C), np.int8)
        self._tg[sig] = g; return g

    def run(self, s, d, f):
        if s[0] == "G":
            p = s[3]; w = (self.t >= d) & (self.t < f)
            if w.sum() < 2 * self.bpd: return None
            nl = p["nl"]; off = p["off"] if p["off"] is not None else (nl - 1) / 2 - 0.5
            esp = -1.0 if p["ka"] > 0 else p["esp"]
            ESP = self.ESP(p["ka"])[w] if p["ka"] > 0 else np.zeros(int(w.sum()))
            DG = self.DG[w].copy() if p["dg"] else np.zeros(int(w.sum()), np.bool_)
            return simg(self.t[w].copy(), self.o[w].copy(), self.h[w].copy(), self.l[w].copy(), self.c[w].copy(), DG,
                        self.FL(p["flt"])[w].copy(), ESP.copy(), CAP0 * p["npl"], CAP0, esp, nl, p["capx"], p["side"], off,
                        p["prot"], p["stopf"], self.bpd, self.chk)
        p = s[4]; w = (self.T >= d) & (self.T < f)
        if w.sum() < 48: return None
        return simd(self.O[w].copy(), self.H[w].copy(), self.L[w].copy(), self.C[w].copy(), self.TGT(s[3])[w].copy(),
                    np.nan_to_num(self.ATRd[w], nan=0.0), p["L"], p["slp"], p["ta"], p["tt"], p["atrk"], p["tpp"],
                    p["reentry"], p["hold"], p["mart"], CAP0, 0.85, 24)


def charge(c, quelle):
    if quelle == "1m":
        a = np.load(os.path.join(D1H, "SOLUSDT-1m.npy") if c == "SOL" else f"{M1}/{c}.npy"); return couper(a, 2880)
    return couper(np.load(os.path.join(D1H, f"{c}USDT-1h.npy")), 48)


def melange(a, rng):
    """prix mélangés : bougies 1 min permutées (forme gardée), dérive moyenne retirée ; la volatilité reste, la tendance part."""
    o, h, l, c = a[:, 1], a[:, 2], a[:, 3], a[:, 4]
    rc = np.log(c / o); rh = np.log(h / o); rl = np.log(l / o); mu = rc.mean()
    rc, rh, rl = rc - mu, rh - mu, rl - mu
    rh = np.maximum(np.maximum(rh, 0), rc); rl = np.minimum(np.minimum(rl, 0), rc)
    p = rng.permutation(len(a)); rc, rh, rl = rc[p], rh[p], rl[p]
    C = o[0] * np.exp(np.cumsum(rc)); O = np.concatenate([[o[0]], C[:-1]])
    b = a.copy(); b[:, 1] = O; b[:, 2] = O * np.exp(rh); b[:, 3] = O * np.exp(rl); b[:, 4] = C
    return b


def paires_neuves():
    noms = sorted(f[:-len("USDT-1h.npy")] for f in os.listdir(D1H) if f.endswith("USDT-1h.npy"))
    cand = [x for x in noms if x not in EXCLU]
    rng = np.random.default_rng(GRAINE_PAIRES); out = []
    for x in rng.permutation(cand):
        a = charge(str(x), "1h")
        if a[-1, 0] >= ms(2024, 5, 1): out.append(str(x))
        if len(out) == N_NEUVES: break
    return out, len(cand)


def bloc(terr, s, pn):
    d, f = PER[pn]; r = {c: T.run(s, d, f) for c, T in terr.items()}; r = {c: v for c, v in r.items() if v is not None}
    if not r: return None
    Lm = min(len(v[7]) for v in r.values()); port = sum(v[7][:Lm] for v in r.values()); pk = np.maximum.accumulate(port)
    res = {c: round(float(v[0]) - CAP0, 1) for c, v in r.items()}
    return dict(total=round(sum(res.values()), 1), par_paire=res, positives=sum(v > 0 for v in res.values()), n=len(res),
                arretees=[c for c, v in r.items() if v[5] or v[6]], baisse_port=round(float((port / pk - 1).min()), 3),
                frais=round(sum(float(v[2]) for v in r.values()), 1), exec=sum(int(v[3]) for v in r.values()))


def eligible(o): return o is not None and not o["arretees"] and o["baisse_port"] > -0.30


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "liste":
        for i, s in enumerate(S, 1): print(f"| {i} | {s[1]} | {s[2]} |")
        nv, nc = paires_neuves(); print("paires neuves tirées :", nv, "sur", nc, "candidates"); sys.exit()
    if mode == "prevol":
        t0 = time.time(); terr = {c: Terrain(charge(c, "1m"), True) for c in C4}; print("chargement", round(time.time() - t0, 1), "s")
        for nom in ("W5",):
            s = [x for x in S if x[1] == nom][0]
            t0 = time.time(); b1 = bloc(terr, s, "P1"); b2 = bloc(terr, s, "P2")
            print(nom, b1["total"], b2["total"], "temps", round(time.time() - t0, 1), "s")
        sys.exit()
    # ------------------------------------------------------------------------------------------- tout
    OUT = {"strategies": [dict(n=i + 1, nom=s[1], famille=s[0], txt=s[2]) for i, s in enumerate(S)]}
    t00 = time.time()
    def log(*x): print(f"[{time.time() - t00:7.0f}s]", *x, flush=True)
    T4 = {c: Terrain(charge(c, "1m"), True) for c in C4}
    R = {}
    for s in S:
        R[s[1]] = {"P1": bloc(T4, s, "P1"), "P2": bloc(T4, s, "P2")}
    log("4 paires P1/P2 faits")
    OUT["temoin_ok"] = R["W5"]["P1"]["total"] == 881.4 and R["W5"]["P2"]["total"] == -245.0
    ok = {n: v["P1"] for n, v in R.items() if eligible(v["P1"])}
    X = max(ok, key=lambda n: ok[n]["total"]); OUT["X"] = X
    log("témoin", OUT["temoin_ok"], "W5", R["W5"]["P1"]["total"], R["W5"]["P2"]["total"], "CHOIX X* =", X, ok[X]["total"])
    # diagnostic : mêmes 4 paires P1 sur bougies 1 h (fidélité du moteur 1 h utilisé pour les 24 paires tirées)
    T4h = {c: Terrain(charge(c, "1h"), False) for c in C4}
    for s in S: R[s[1]]["P1_1h"] = bloc(T4h, s, "P1")
    del T4h; log("diagnostic 1 h fait")
    T6 = {c: Terrain(charge(c, "1m"), True) for c in C6}
    for s in S:
        R[s[1]]["N6_P1"] = bloc(T6, s, "P1"); R[s[1]]["N6_P2"] = bloc(T6, s, "P2")
    del T6; log("6 paires faites")
    NV, nc = paires_neuves(); OUT["paires_neuves_24"] = NV
    T24 = {c: Terrain(charge(c, "1h"), False) for c in NV}
    for s in S:
        R[s[1]]["N24_P1"] = bloc(T24, s, "P1"); R[s[1]]["N24_P2"] = bloc(T24, s, "P2")
    del T24; log("24 paires faites")
    OUT["R"] = R
    json.dump(OUT, open(os.path.join(ICI, "t75.json"), "w"), ensure_ascii=False, indent=0)
    # ------------------------------------------------------------------------------------------- témoin hasard
    BR = {c: T4[c] for c in C4}; del T4
    brut = {c: charge(c, "1m") for c in C4}
    rng = np.random.default_rng(GRAINE_HASARD); HZ = []
    for r in range(N_HASARD):
        Th = {}
        for c in C4:
            a = brut[c]; a = a[(a[:, 0] >= ms(2024, 1, 1)) & (a[:, 0] < ms(2026, 1, 1))]
            Th[c] = Terrain(melange(a, rng), True)
        tot = {}
        for s in S:
            b = bloc(Th, s, "P1"); tot[s[1]] = (b["total"], eligible(b))
        best_all = max(v[0] for v in tot.values()); el = [v[0] for v in tot.values() if v[1]]
        best_el = max(el) if el else None; arg = max(tot, key=lambda n: tot[n][0])
        HZ.append(dict(rep=r, max_100=best_all, max_eligibles=best_el, meilleure=arg, W5=tot["W5"][0],
                       mediane=float(np.median([v[0] for v in tot.values()])), totaux={k: v[0] for k, v in tot.items()}))
        log("hasard", r, "max", best_all, "par", arg, "max éligibles", best_el, "W5", tot["W5"][0])
        OUT["hasard"] = HZ; json.dump(OUT, open(os.path.join(ICI, "t75.json"), "w"), ensure_ascii=False, indent=0)
    p95 = float(np.percentile([h["max_100"] for h in HZ], 95)); OUT["hasard_p95_max100"] = round(p95, 1)
    # ------------------------------------------------------------------------------------------- verdict
    def neuf(n):
        a = [R[n][k] for k in ("N6_P1", "N6_P2", "N24_P1", "N24_P2") if R[n][k]]
        tot = sum(b["total"] for b in a); pp = {}
        for b in a:
            for c, v in b["par_paire"].items(): pp[c] = pp.get(c, 0) + v
        return round(tot, 1), sum(v > 0 for v in pp.values()), len(pp)
    nX, nW = neuf(X), neuf("W5")
    c1 = X != "W5"; c2 = R[X]["P1"]["total"] > p95
    c3 = R[X]["P2"]["total"] > 0 and R[X]["P2"]["total"] > R["W5"]["P2"]["total"]
    c4 = nX[0] > 0 and nX[0] > nW[0] and nX[1] >= nX[2] / 2
    OUT["criteres"] = dict(C1_pas_W5=c1, C2_au_dessus_hasard=c2, C3_P2=c3, C4_neuves=c4, neuves_X=nX, neuves_W5=nW)
    if not OUT["temoin_ok"]: v = "NON CONCLUANT (témoin)"
    elif not c1: v = "NON (W5 reste la meilleure sur P1)"
    elif c2 and c3 and c4: v = "TIENT"
    elif R[X]["P2"]["total"] > R["W5"]["P2"]["total"] and nX[0] > nW[0]: v = "MIEUX QUE W5 SANS PREUVE"
    else: v = "NON"
    OUT["verdict"] = v; log("VERDICT", v, json.dumps(OUT["criteres"], ensure_ascii=False), "p95", p95)
    json.dump(OUT, open(os.path.join(ICI, "t75.json"), "w"), ensure_ascii=False, indent=0)

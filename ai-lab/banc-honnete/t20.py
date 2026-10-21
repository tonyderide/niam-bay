"""PREREG-17 : chef d'orchestre, score par date de SORTIE (pas de regard vers le futur). Univers A (120 rapides, re-vérif du 16) et B (180 lents)."""
import itertools, random, statistics, sys
import banc
import t17_lib as L

A, B, C0, C1 = banc.ts("2024-01-01"), banc.ts("2026-01-01"), banc.ts("2026-01-01"), banc.ts("2026-10-17")
LUNDI0 = banc.ts("2023-12-25"); W = 7 * 86400
wk = lambda t: int((t - LUNDI0) // W)


def macd_sig(cl):
    e12, e26 = L.ema(cl, 12), L.ema(cl, 26); m = [a - b for a, b in zip(e12, e26)]; s = L.ema(m, 9); o = [0] * len(cl)
    for i in range(1, len(cl)):
        o[i] = 1 if m[i] > s[i] and m[i - 1] <= s[i - 1] else -1 if m[i] < s[i] and m[i - 1] >= s[i - 1] else 0
    return o


def rsi14(cl):
    o = [50.0] * len(cl); g = l = 0.0; a = 1 / 14
    for i in range(1, len(cl)):
        d = cl[i] - cl[i - 1]; g = (1 - a) * g + a * max(d, 0); l = (1 - a) * l + a * max(-d, 0)
        o[i] = 100 if l == 0 else 100 - 100 / (1 + g / l)
    return o


def signaux_lents(C):
    cl = [c[3] for c in C]; n = len(cl); s = {k: [0] * n for k in "vwxyz"}
    s["v"] = L.sig_ema(C, 20, 50); s["z"] = macd_sig(cl); r = rsi14(cl)
    for i in range(25, n):
        hh = max(c[1] for c in C[i - 20:i]); ll = min(c[2] for c in C[i - 20:i])
        s["w"][i] = 1 if cl[i] > hh else -1 if cl[i] < ll else 0
        s["x"][i] = 1 if r[i] < 30 else -1 if r[i] > 70 else 0
        w = cl[i - 19:i + 1]; m = sum(w) / 20; sd = statistics.pstdev(w)
        s["y"][i] = 1 if cl[i] < m - 2 * sd else -1 if cl[i] > m + 2 * sd else 0
    return s


def trades(C, T, sig, tp, sl, a, b, maxb):
    L.MAXB = maxb
    lo = next(k for k, t in enumerate(T) if t >= a); hi = next((k for k, t in enumerate(T) if t >= b), len(T)) - 1
    i = lo; out = []
    while i < hi - 1:
        if sig[i]:
            r, j = L.trade(C, i + 1, sig[i], tp, sl); out.append((T[i + 1], T[j], r)); i = j + 1
        else: i += 1
    return out


def univers(nom):
    U = []
    if nom == "A":
        for tf, m in itertools.product(("15m", "1h"), ("BTC", "ETH", "SOL")):
            T, C = banc.candles(banc.SYM[m], tf); S = L.signaux(C)
            for k, (tp, sl) in itertools.product("abcd", ((0.005, 0.005), (0.01, 0.01), (0.015, 0.01), (0.02, 0.01), (0.03, 0.015))):
                U.append(trades(C, T, S[k], tp, sl, A - 10 * W, C1, 24))
    else:
        for tf, m in itertools.product(("4h", "1d"), ("BTC", "ETH", "SOL", "XRP", "ADA", "LINK")):
            T, C = banc.candles(banc.SYM[m], tf); S = signaux_lents(C)
            for k, (tp, sl) in itertools.product("vwxyz", ((0.05, 0.025), (0.08, 0.04), (0.12, 0.06))):
                U.append(trades(C, T, S[k], tp, sl, A - 10 * W, C1, 30))
    return U


def tables(U):
    NW = wk(C1) + 2
    sortie = [[0.0] * NW for _ in U]; entree = [[0.0] * NW for _ in U]
    for s, tr in enumerate(U):
        for te, ts_, r in tr:
            if 0 <= wk(ts_) < NW: sortie[s][wk(ts_)] += r
            if 0 <= wk(te) < NW: entree[s][wk(te)] += r
    return sortie, entree


def chef(S_, E_, Lw, K, seuil, w0, w1, rnd=None, nombres=None):
    NS = len(S_); tot = 0.0; joues = []
    for w in range(w0, w1):
        if rnd is None:
            sc = sorted(((sum(S_[s][max(0, w - Lw):w]), s) for s in range(NS)), reverse=True)  # trades SORTIS avant le lundi w
            choix = [s for v, s in sc[:K] if v > seuil]
        else:
            choix = rnd.sample(range(NS), nombres[w - w0])
        joues.append(len(choix))
        if choix: tot += sum(E_[s][w] for s in choix) / len(choix)
    return tot, joues


def persistance(S_, w0, w1):
    NS = len(S_); v = []
    for w in range(w0 + 1, w1):
        a = [S_[s][w - 1] for s in range(NS)]; b = [S_[s][w] for s in range(NS)]
        ra = {s: i for i, s in enumerate(sorted(range(NS), key=lambda s: a[s]))}; rb = {s: i for i, s in enumerate(sorted(range(NS), key=lambda s: b[s]))}
        v.append(1 - 6 * sum((ra[s] - rb[s]) ** 2 for s in range(NS)) / (NS * (NS * NS - 1)))
    return statistics.mean(v)


for nom, seuils in (("A", (0.0,)), ("B", (0.0, 0.02))):
    U = univers(nom); S_, E_ = tables(U); NS = len(U)
    g = {}
    for Lw, K, s in itertools.product((1, 2, 4, 8), (1, 5, 10), seuils): g[(Lw, K, s)] = chef(S_, E_, Lw, K, s, wk(A), wk(B))[0]
    Lw, K, s = max(g, key=g.get)
    v, nb = chef(S_, E_, Lw, K, s, wk(C0), wk(C1))
    tous = sum(sum(E_[x][w] for x in range(NS)) / NS for w in range(wk(C0), wk(C1)))
    rnd = random.Random(17); H = sorted(chef(S_, E_, Lw, K, s, wk(C0), wk(C1), rnd, nb)[0] for _ in range(1000))
    rang = sum(x < v for x in H) / len(H)
    print(f"Univers {nom} ({NS} stratégies) | choisi sur 2024-25 : mémoire {Lw} sem., {K} strat., seuil {s:.0%} ({100*g[(Lw, K, s)]:+.1f} %)")
    print(f"  2026 : chef {100*v:+.1f} % | toutes à poids égal {100*tous:+.1f} % | hasard méd {100*H[500]:+.1f} % p99 {100*H[990]:+.1f} % | rang {rang:.1%} | semaines jouées {sum(x > 0 for x in nb)}/{len(nb)}")
    print(f"  persistance (sorties) : 2024-25 {persistance(S_, wk(A), wk(B)):+.3f} | 2026 {persistance(S_, wk(C0), wk(C1)):+.3f}")
    print("  VERDICT :", "GAGNE" if v > 0 and v > tous and rang >= 0.99 else "ÉCHEC", flush=True)

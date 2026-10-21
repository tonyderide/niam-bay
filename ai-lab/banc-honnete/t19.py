"""PREREG-16 : le chef d'orchestre. Voir PREREG-16-chef-orchestre.md."""
import itertools, random, statistics
import banc
import t17_lib as L

A, B, C0, C1 = banc.ts("2024-01-01"), banc.ts("2026-01-01"), banc.ts("2026-01-01"), banc.ts("2026-10-17")
LUNDI0 = banc.ts("2023-12-25")  # un lundi
W = 7 * 86400


def trades_dates(C, T, sig, tp, sl, a, b):
    lo = next(k for k, t in enumerate(T) if t >= a); hi = next((k for k, t in enumerate(T) if t >= b), len(T)) - 1
    i = lo; out = []
    while i < hi - 1:
        if sig[i]:
            r, j = L.trade(C, i + 1, sig[i], tp, sl); out.append((T[i + 1], r)); i = j + 1
        else: i += 1
    return out


strats = []
for tf, m in itertools.product(("15m", "1h"), ("BTC", "ETH", "SOL")):
    T, C = banc.candles(banc.SYM[m], tf); S = L.signaux(C)
    for k, (tp, sl) in itertools.product("abcd", ((0.005, 0.005), (0.01, 0.01), (0.015, 0.01), (0.02, 0.01), (0.03, 0.015))):
        strats.append(((tf, m, k, tp, sl), trades_dates(C, T, S[k], tp, sl, A - 10 * W, C1)))
NS = len(strats); NW = int((C1 - LUNDI0) // W) + 1
# rendement hebdomadaire de chaque stratégie (semaine = [lundi, lundi suivant), selon la date d'entrée)
R = [[0.0] * NW for _ in range(NS)]
for s, (_, tr) in enumerate(strats):
    for t, r in tr:
        w = int((t - LUNDI0) // W)
        if 0 <= w < NW: R[s][w] += r
wk = lambda t: int((t - LUNDI0) // W)


def chef(Lw, K, w0, w1, rnd=None, nombres=None):
    tot = 0.0; joues = []
    for w in range(w0, w1):
        sc = [(sum(R[s][max(0, w - Lw):w]), s) for s in range(NS)]
        if rnd is None:
            choix = [s for v, s in sorted(sc, reverse=True)[:K] if v > 0]
        else:
            choix = rnd.sample(range(NS), nombres[w - w0])
        joues.append(len(choix))
        if choix: tot += sum(R[s][w] for s in choix) / len(choix)
    return tot, joues


grille = {}
for Lw, K in itertools.product((1, 2, 4, 8), (1, 5, 10)):
    grille[(Lw, K)] = chef(Lw, K, wk(A), wk(B))[0]
    print(f"  2024-25 : mémoire {Lw} sem., {K} stratégie(s) -> {100*grille[(Lw, K)]:+.1f} %")
Lw, K = max(grille, key=grille.get); print(f"CHOISI : mémoire {Lw} semaine(s), {K} stratégie(s) à la fois")
g, nb = chef(Lw, K, wk(C0), wk(C1))
tous = sum(sum(R[s][w] for s in range(NS)) / NS for w in range(wk(C0), wk(C1)))
rnd = random.Random(16); H = sorted(chef(Lw, K, wk(C0), wk(C1), rnd, nb)[0] for _ in range(1000))
rang = sum(x < g for x in H) / len(H)


def persistance(w0, w1):
    v = []
    for w in range(w0 + 1, w1):
        a = [R[s][w - 1] for s in range(NS)]; b = [R[s][w] for s in range(NS)]
        ra = {s: i for i, s in enumerate(sorted(range(NS), key=lambda s: a[s]))}; rb = {s: i for i, s in enumerate(sorted(range(NS), key=lambda s: b[s]))}
        v.append(1 - 6 * sum((ra[s] - rb[s]) ** 2 for s in range(NS)) / (NS * (NS * NS - 1)))
    return statistics.mean(v)


print(f"JUGEMENT 2026 : chef {100*g:+.1f} % | les 120 à poids égal {100*tous:+.1f} % | chefs au hasard méd {100*H[500]:+.1f} % p99 {100*H[990]:+.1f} % | rang {rang:.1%} | semaines jouées {sum(x > 0 for x in nb)}/{len(nb)}")
print("VERDICT :", "GAGNE" if g > 0 and g > tous and rang >= 0.99 else "ÉCHEC")
print(f"[info] persistance de la forme (Spearman semaine -> semaine suivante, moyenne) : 2024-25 {persistance(wk(A), wk(B)):+.3f} | 2026 {persistance(wk(C0), wk(C1)):+.3f}")

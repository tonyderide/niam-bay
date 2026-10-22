# [info, contrôle] t23 sur la période AVANT (mars 2024 -> mars 2025) ; T2 sans objet (d=0 = chef lui-même)
"""PREREG-20 : le chef a-t-il un vrai timing ? Jumeaux stratifiés (T1) et chef décalé (T2), 18 marchés neufs."""
import itertools, random
import banc
import t17_lib as L
src = open("t20.py").read().split("for nom, seuils in")[0]; ns = {}; exec(compile(src, "t20_lib", "exec"), ns)
trades, wk = ns["trades"], ns["wk"]
A, C1 = banc.ts("2024-01-01"), banc.ts("2026-10-17"); W = 7 * 86400
G = [("ARB", "BNB", "INJ"), ("FET", "GRT", "ALGO"), ("CRV", "LDO", "IMX"), ("RUNE", "EGLD", "SAND"), ("MANA", "AXS", "APE"), ("DYDX", "GALA", "COMP")]
COUPLES = ((0.005, 0.005), (0.01, 0.01), (0.015, 0.01), (0.02, 0.01), (0.03, 0.015))
NT = 1000; W0, W1 = wk(A) + 8, wk(A) + 60; NW = W1 + 2


def prefix(row):
    p = [0.0]
    for x in row: p.append(p[-1] + x)
    return p


def groupe(grp, graine):
    U = []; meta = []
    for tf, m in itertools.product(("15m", "1h"), grp):
        T, C = banc.candles(f"PF_{m}USD", tf); S = L.signaux(C)
        for k, (ci, (tp, sl)) in itertools.product("abcd", enumerate(COUPLES)):
            U.append(trades(C, T, S[k], tp, sl, A - 10 * W, C1, 24)); meta.append((tf, ci))
    NS = len(U)
    Sx = [[0.0] * NW for _ in U]; Ex = [[0.0] * NW for _ in U]; Nx = [[0] * NW for _ in U]; Ne = [[0] * NW for _ in U]
    for s, tr in enumerate(U):
        for te, tsx, r in tr:
            if 0 <= wk(tsx) < NW: Sx[s][wk(tsx)] += r; Nx[s][wk(tsx)] += 1
            if 0 <= wk(te) < NW: Ex[s][wk(te)] += r; Ne[s][wk(te)] += 1
    PS = [prefix(r) for r in Sx]; PN = [prefix(r) for r in Nx]
    win = lambda P, s, a, b: P[s][max(0, b)] - P[s][max(0, a)]
    cases = {}
    for s, mt in enumerate(meta): cases.setdefault(mt, []).append(s)

    def choix_chef(w, d=0):
        sc = sorted(((win(PS, s, w - 8 - d, w - d), s) for s in range(NS)), reverse=True)
        return [s for v, s in sc[:10] if v > 0]

    def gain(w, ch): return (sum(Ex[s][w] for s in ch) / len(ch)) if ch else 0.0
    def ntr(w, ch): return sum(Ne[s][w] for s in ch)

    chef = [choix_chef(w) for w in range(W0, W1)]
    g_chef = [gain(w, c) for w, c in zip(range(W0, W1), chef)]; n_chef = sum(ntr(w, c) for w, c in zip(range(W0, W1), chef))
    rnd = random.Random(graine); T1 = []; T2 = []; T1w = [0.0] * (W1 - W0); n_t1 = 0; elargi = 0; remplacements = 0
    for _ in range(NT):
        tot1 = 0.0; tot2 = 0.0
        for iw, w in enumerate(range(W0, W1)):
            ch = chef[iw]
            if ch:
                pris = set(); new = []
                moities = {}
                for mt, membres in cases.items():
                    m2 = sorted(membres, key=lambda s: (win(PN, s, w - 8, w), rnd.random())); h = len(m2) // 2
                    moities[mt] = (m2[:h], m2[h:])
                for s in ch:
                    mt = meta[s]; bas, haut = moities[mt]; part = bas if s in bas else haut
                    dispo = [x for x in part if x not in pris]
                    if not dispo: dispo = [x for x in cases[mt] if x not in pris]; elargi += 1
                    remplacements += 1; x = rnd.choice(dispo); pris.add(x); new.append(x)
                g = gain(w, new); tot1 += g; T1w[iw] += g / NT; n_t1 += ntr(w, new)
            d = 0; tot2 += gain(w, choix_chef(w, d))
        T1.append(tot1); T2.append(tot2)
    return sum(g_chef), T1, T2, g_chef, T1w, n_chef, n_t1 / NT, elargi / max(1, remplacements)


tot_c = 0.0; S1 = [0.0] * NT; S2 = [0.0] * NT; au_dessus = 0; diag_ok = True; elarg_ok = True; diff_w = None
for gi, grp in enumerate(G):
    c, T1, T2, gw, t1w, nc, nt1, el = groupe(grp, 200 + gi)
    tot_c += c; S1 = [a + b for a, b in zip(S1, T1)]; S2 = [a + b for a, b in zip(S2, T2)]
    med1 = sorted(T1)[NT // 2]; au_dessus += c > med1
    ok_d = abs(nt1 - nc) <= 0.10 * max(1, nc); diag_ok &= ok_d; elarg_ok &= el <= 0.20
    dw = [a - b for a, b in zip(gw, t1w)]; diff_w = dw if diff_w is None else [a + b for a, b in zip(diff_w, dw)]
    print(f"G{gi+1} {'/'.join(grp):15} chef {100*c:+7.1f} % | T1 méd {100*med1:+7.1f} % | T2 méd {100*sorted(T2)[NT//2]:+7.1f} % | trades chef {nc} / T1 {nt1:.0f} ({'OK' if ok_d else 'HORS ±10 %'}) | élargis {el:.0%}", flush=True)
S1.sort(); S2.sort()
rb = random.Random(20); eff = sum(diff_w); B = []; nb = len(diff_w) // 4   # rééchantillonnage en blocs de 4 semaines
for _ in range(2000):
    tot = 0.0
    for _ in range(nb):
        k = rb.randrange(0, len(diff_w) - 3); tot += sum(diff_w[k:k + 4])
    B.append(tot * len(diff_w) / (4 * nb))
B.sort()
print(f"\nSOMME : chef {100*tot_c:+.1f} % | T1 méd {100*S1[NT//2]:+.1f} % p95 {100*S1[int(.95*NT)]:+.1f} % | T2 méd {100*S2[NT//2]:+.1f} % p95 {100*S2[int(.95*NT)]:+.1f} % | groupes > méd T1 : {au_dessus}/6")
print(f"Effet chef − T1 : {100*eff:+.1f} points, IC 95 % (blocs de 4 sem.) [{100*B[50]:+.1f} ; {100*B[1950]:+.1f}]")
if not diag_ok or not elarg_ok: print("TEST INVALIDE :", "diagnostic de trades hors ±10 %" if not diag_ok else "", "élargissement > 20 %" if not elarg_ok else "")
else:
    ok = tot_c > S1[int(.95 * NT)] and tot_c > S2[int(.95 * NT)] and au_dessus >= 4
    print("VERDICT TIMING :", "CONFIRMÉ" if ok else "NON DÉMONTRÉ")
print("Rentabilité (info) :", "positive" if tot_c > 0 else "négative")

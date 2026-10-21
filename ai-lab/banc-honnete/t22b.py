"""[contre-vérification de PREREG-19, revue du scalpeur] Limite vs marché À ARMES ÉGALES sur les 120 stratégies :
même glissement des deux côtés (0 pb, puis 5 pb), objectif autorisé dès la bougie d'entrée pour les deux ; + taux de remplissage des limites."""
import itertools
import banc
import t17_lib as L
import t22_lib as M
A, B, C0, C1 = banc.ts("2024-01-01"), banc.ts("2026-01-01"), banc.ts("2026-01-01"), banc.ts("2026-10-17")
COUPLES = ((0.005, 0.005), (0.01, 0.01), (0.015, 0.01), (0.02, 0.01), (0.03, 0.015))

def trade_lim(C, i, sens, tp, sl, slip):
    e = C[i - 1][3]; obj = e * (1 + tp * sens); stp = e * (1 - sl * sens)
    for j in range(i, min(i + 24, len(C))):
        o, h, l = C[j][0], C[j][1], C[j][2]
        if j > i and ((o <= stp) if sens > 0 else (o >= stp)): return (o / e - 1) * sens - M.MAKER - M.TAKER - slip, j
        if (l <= stp) if sens > 0 else (h >= stp): return -sl - M.MAKER - M.TAKER - slip, j
        if (h > obj * (1 + M.TRAV)) if sens > 0 else (l < obj * (1 - M.TRAV)): return tp - 2 * M.MAKER, j
    j = min(i + 24, len(C)) - 1
    return (C[j][3] / e - 1) * sens - M.MAKER - M.TAKER - slip, j

def run_lim(C, T, sig, tp, sl, a, b, slip):
    lo = next(k for k, t in enumerate(T) if t >= a); hi = next((k for k, t in enumerate(T) if t >= b), len(T)) - 1
    i = lo; R = []; sigs = 0; remplis = 0
    while i < hi - 1:
        if sig[i]:
            sigs += 1
            if M.rempli(C, i + 1, sig[i], C[i][3]):
                remplis += 1; r, j = trade_lim(C, i + 1, sig[i], tp, sl, slip); R.append(r); i = j + 1; continue
        i += 1
    return sum(R), sigs, remplis

def run_mkt(C, T, sig, tp, sl, a, b, slip):
    L.FEE = 0.0005 + slip / 2   # taker + glissement réparti sur les 2 côtés (même total que le limite côté stop)
    R = L.strat(C, T, sig, tp, sl, a, b)[0]; L.FEE = 0.0005
    return sum(R)

for slip in (0.0, 0.0005):
    res = {"lim": [0, 0, 0.0, 0.0], "mkt": [0, 0, 0.0, 0.0]}; S_ = R_ = 0
    for tf, m in itertools.product(("15m", "1h"), ("BTC", "ETH", "SOL")):
        T, C = banc.candles(banc.SYM[m], tf); S = L.signaux(C)
        for k, (tp, sl) in itertools.product("abcd", COUPLES):
            l1, s1, r1 = run_lim(C, T, S[k], tp, sl, A, B, slip); l2, s2, r2 = run_lim(C, T, S[k], tp, sl, C0, C1, slip)
            m1 = run_mkt(C, T, S[k], tp, sl, A, B, slip); m2 = run_mkt(C, T, S[k], tp, sl, C0, C1, slip)
            res["lim"][0] += l1 > 0; res["lim"][1] += l2 > 0; res["lim"][2] += l1; res["lim"][3] += l2
            res["mkt"][0] += m1 > 0; res["mkt"][1] += m2 > 0; res["mkt"][2] += m1; res["mkt"][3] += m2
            S_ += s1 + s2; R_ += r1 + r2
    print(f"Glissement {slip*1e4:.0f} pb des DEUX côtés (objectif permis dès la bougie d'entrée) :")
    for key, nom in (("mkt", "au marché"), ("lim", "limite")):
        a, b, c, d = res[key]; print(f"  {nom:10} positives 2024-25 {a}/120, 2026 {b}/120 | somme 2024-25 {100*c:+.0f} %, 2026 {100*d:+.0f} %")
    print(f"  taux de remplissage des limites : {R_/S_:.1%}")

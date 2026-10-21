"""PREREG-18 : chef figé (8 semaines, top 10, score sur trades sortis) sur 18 cryptos jamais vues, 6 groupes de 3."""
import itertools, random
import banc
import t17_lib as L
src = open("t20.py").read().split("for nom, seuils in")[0]; ns = {}; exec(compile(src, "t20_lib", "exec"), ns)
trades, tables, chef, wk = ns["trades"], ns["tables"], ns["chef"], ns["wk"]
A, C1 = banc.ts("2024-01-01"), banc.ts("2026-10-17"); W = 7 * 86400
G = [("XRP", "DOGE", "ADA"), ("LINK", "AVAX", "DOT"), ("LTC", "BCH", "UNI"), ("ATOM", "NEAR", "FIL"), ("AAVE", "APT", "OP"), ("TRX", "XLM", "ETC")]
NT = 1000; tot_v = 0.0; tot_H = [0.0] * NT; au_dessus = 0
for gi, grp in enumerate(G):
    U = []
    for tf, m in itertools.product(("15m", "1h"), grp):
        T, C = banc.candles(banc.SYM[m], tf); S = L.signaux(C)
        for k, (tp, sl) in itertools.product("abcd", ((0.005, 0.005), (0.01, 0.01), (0.015, 0.01), (0.02, 0.01), (0.03, 0.015))):
            U.append(trades(C, T, S[k], tp, sl, A - 10 * W, C1, 24))
    S_, E_ = tables(U); w0, w1 = wk(A) + 8, wk(C1)
    v, nb = chef(S_, E_, 8, 10, 0.0, w0, w1)
    rnd = random.Random(18 + gi); H = [chef(S_, E_, 8, 10, 0.0, w0, w1, rnd, nb)[0] for _ in range(NT)]
    tous = sum(sum(E_[x][w] for x in range(len(U))) / len(U) for w in range(w0, w1))
    med = sorted(H)[NT // 2]; au_dessus += v > med; tot_v += v; tot_H = [a + b for a, b in zip(tot_H, H)]
    print(f"G{gi+1} {'/'.join(grp):15} chef {100*v:+8.1f} % | toutes {100*tous:+8.1f} % | hasard méd {100*med:+8.1f} % | rang {sum(x < v for x in H)/NT:.1%}", flush=True)
tot_H.sort(); r = sum(x < tot_v for x in tot_H) / NT
v1 = tot_v > tot_H[int(0.95 * NT)] and au_dessus >= 4
print(f"\nSOMME 6 groupes : chef {100*tot_v:+.1f} % | hasard méd {100*tot_H[NT//2]:+.1f} % p95 {100*tot_H[int(.95*NT)]:+.1f} % | rang {r:.1%} | groupes au-dessus de la médiane : {au_dessus}/6")
print("VERDICT 1 (le chef sait choisir) :", "RÉUSSI" if v1 else "RATÉ")
print("VERDICT 2 (rentable) :", "RÉUSSI" if v1 and tot_v > 0 else "RATÉ")

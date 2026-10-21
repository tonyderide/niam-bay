"""[info, contrôle de PREREG-18] Le chef gagne-t-il par le TIMING (forme récente) ou juste parce qu'il choisit des stratégies qui tradent peu ?
Contrôles sans timing : (S1) toujours les 10 stratégies qui ont le moins tradé dans le passé ; (S2) les 10 meilleures depuis le début (score cumulé) ; (S3) forme sur 8 semaines mais en score PAR TRADE (neutralise le nombre de trades)."""
import itertools
import banc
import t17_lib as L
src = open("t20.py").read().split("for nom, seuils in")[0]; ns = {}; exec(compile(src, "t20_lib", "exec"), ns)
trades, tables, chef, wk = ns["trades"], ns["tables"], ns["chef"], ns["wk"]
A, C1 = banc.ts("2024-01-01"), banc.ts("2026-10-17"); W = 7 * 86400
G = [("XRP", "DOGE", "ADA"), ("LINK", "AVAX", "DOT"), ("LTC", "BCH", "UNI"), ("ATOM", "NEAR", "FIL"), ("AAVE", "APT", "OP"), ("TRX", "XLM", "ETC")]
T_ = {k: 0.0 for k in ("chef", "S1", "S2", "S3")}
for gi, grp in enumerate(G):
    U = []
    for tf, m in itertools.product(("15m", "1h"), grp):
        T, C = banc.candles(banc.SYM[m], tf); S = L.signaux(C)
        for k, (tp, sl) in itertools.product("abcd", ((0.005, 0.005), (0.01, 0.01), (0.015, 0.01), (0.02, 0.01), (0.03, 0.015))):
            U.append(trades(C, T, S[k], tp, sl, A - 10 * W, C1, 24))
    S_, E_ = tables(U); NS = len(U); w0, w1 = wk(A) + 8, wk(C1)
    NW = len(S_[0]); nsort = [[0] * NW for _ in U]
    for s, tr in enumerate(U):
        for te, tsx, r in tr:
            if 0 <= wk(tsx) < NW: nsort[s][wk(tsx)] += 1
    res = {"chef": chef(S_, E_, 8, 10, 0.0, w0, w1)[0], "S1": 0.0, "S2": 0.0, "S3": 0.0}
    for w in range(w0, w1):
        n_pass = [sum(nsort[s][:w]) for s in range(NS)]; cum = [sum(S_[s][:w]) for s in range(NS)]
        s1 = sorted(range(NS), key=lambda s: n_pass[s])[:10]
        s2 = [s for s in sorted(range(NS), key=lambda s: -cum[s])[:10] if cum[s] > 0]
        par = [(sum(S_[s][w - 8:w]) / max(1, sum(nsort[s][w - 8:w])), s) for s in range(NS) if sum(nsort[s][w - 8:w]) > 0]
        s3 = [s for v, s in sorted(par, reverse=True)[:10] if v > 0]
        for key, ch in (("S1", s1), ("S2", s2), ("S3", s3)):
            if ch: res[key] += sum(E_[s][w] for s in ch) / len(ch)
    for k in T_: T_[k] += res[k]
    print(f"G{gi+1} {'/'.join(grp):15} chef {100*res['chef']:+7.1f} % | S1 moins de trades {100*res['S1']:+7.1f} % | S2 meilleures depuis le début {100*res['S2']:+7.1f} % | S3 forme par trade {100*res['S3']:+7.1f} %", flush=True)
print(f"\nSOMME : chef {100*T_['chef']:+.1f} % | S1 {100*T_['S1']:+.1f} % | S2 {100*T_['S2']:+.1f} % | S3 {100*T_['S3']:+.1f} %")

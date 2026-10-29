"""PREREG-28 addendum D + parcours continus de la combinaison choisie en C."""
import json, numpy as np
exec(open("moins_de_perte.py").read().split("res = []")[0])
g = (0.05, 0.01, 0.01); M, K, B = 3.0, 4, 10.0
@njit
def parcours(mise, s, m, k, base):
    cap = 1000.0; st = base; perdues = 0; pic = cap; pire_baisse = 0.0; serie = 0; pire_serie = 0; pire_trade = 0.0
    for j in range(len(mise)):
        st = min(st, 10 * cap * s); gain = st * mise[j]; cap += gain; pire_trade = min(pire_trade, gain)
        pic = max(pic, cap); pire_baisse = min(pire_baisse, cap / pic - 1)
        if cap < 50: break
        if mise[j] > 0: st = base; perdues = 0; serie = 0
        else:
            perdues += 1; serie += 1; pire_serie = max(pire_serie, serie)
            if perdues >= k: st = base; perdues = 0
            else: st *= m
    return cap, pire_baisse, pire_serie, pire_trade
O = {}
for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
    x = couper(np.load(f"../dca-martingale/refait/donnees/{sym}-1m.npy"), 2880)
    out = np.empty((len(x) + 1, 4)); n = chaine(x[:, 1], x[:, 2], x[:, 3], x[:, 4], g[0], g[2], g[1], False, out); R = out[:n]
    mise = R[:, 0] / g[0]; deb = R[:, 2].astype(np.int64); fin = R[:, 3].astype(np.int64)
    ks = np.searchsorted(deb, np.arange(0, len(x) - D + 1, 1440)); ks = ks[ks < len(R)]
    r = jouer(mise, deb, fin, ks, g[0], M, K, B)
    cap, baisse, serie, pt = parcours(mise, g[0], M, K, B)
    O[sym] = {"minutes": len(x), "trades": n, "esperance_par_trade_pct": round(float(R[:, 0].mean() * 100), 3), "p_perte_3_mois": round(float((r < 0).mean()), 3),
              "median_3_mois_e": round(float(np.median(r)), 1), "pire_3_mois_e": round(float(r.min()), 1), "ruines": round(float((r <= -950).mean()), 3),
              "parcours_33_mois_capital_final": round(cap, 1), "pire_baisse_depuis_sommet": round(baisse, 3), "pire_serie_pertes": int(serie), "pire_trade_e": round(pt, 1)}
    print(sym, O[sym], flush=True)
O["verdict_D"] = "tient" if O["ETHUSDT"]["p_perte_3_mois"] <= 0.10 and O["SOLUSDT"]["p_perte_3_mois"] <= 0.10 else "ne tient pas"
print(O["verdict_D"]); json.dump(O, open("hors-echantillon.json", "w"), indent=1)

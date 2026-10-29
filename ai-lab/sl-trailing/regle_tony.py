"""PREREG-28 addendum A : règle exacte de Tony sur BTC 1 min. SL 1 %, trailing 0,5 % activé à +1 %, toujours en position, sens inversé ; martingale 10 € / 1 000 €."""
import json, numpy as np, sys
sys.argv = ["x", "aucun"]
exec(open("etude.py").read().split("DON =")[0].replace("cache=True", "cache=False"))   # couper(), même règle que simuler()


@njit
def chaine(o, h, l, c, s, t, a, inv_toujours, out):
    """même logique de sortie que simuler() (etude.py), mais le sens change entre les trades"""
    T = len(o); i = 0; m = 0; sens = 1.0
    while i < T:
        e = o[i]; i0 = i; sl = e * (1 - s * sens); actif = False; pic = 0.0
        while True:
            px = -1.0
            hi = h[i] if sens > 0 else l[i]; lo = l[i] if sens > 0 else h[i]; op = o[i]; stop = sl
            if actif:
                ts = pic * (1 - t * sens); stop = max(sl, ts) if sens > 0 else min(sl, ts)
            if (lo - stop) * sens <= 0: px = min(op, stop) if sens > 0 else max(op, stop)
            elif actif: pic = max(pic, hi) if sens > 0 else min(pic, hi)
            elif (hi - e * (1 + a * sens)) * sens >= 0: actif = True; pic = hi
            if px < 0 and i == T - 1: px = c[i]
            if px >= 0:
                r = sens * (px / e - 1) - TK - TK * px / e
                out[m, 0] = r; out[m, 1] = sens; out[m, 2] = i0; out[m, 3] = i; m += 1
                if inv_toujours or r <= 0: sens = -sens
                break
            i += 1
        i += 1
    return m
a = couper(np.load("../dca-martingale/refait/donnees/BTCUSDT-1m.npy")); T = len(a)
S, A, TR = 0.01, 0.01, 0.005


def trades(inverser_toujours):
    """enchaîne les trades : chaque trade démarre à l'ouverture de la minute qui suit la sortie, le sens change selon la variante"""
    out = np.empty((T + 1, 4)); m = chaine(a[:, 1], a[:, 2], a[:, 3], a[:, 4], S, TR, A, inverser_toujours, out)
    return [(x[0], x[1], int(x[2]), int(x[3])) for x in out[:m]]


O = {}
for var, inv in (("inverse_a_chaque_sortie", True), ("inverse_apres_perte", False)):
    R = trades(inv); r = np.array([x[0] for x in R]); mise = r / S   # en « mises » : -1 mise = SL touché (hors frais)
    # martingale sur des départs quotidiens
    debut = [x[2] for x in R]; jours = np.searchsorted(debut, np.arange(0, T, 1440))
    def jouer(k0, duree_min):
        cap, m10 = 1000.0, 10.0; k = k0; fin_t = R[k0][2] + duree_min
        while k < len(R) and R[k][3] < fin_t:
            g = m10 * mise[k]; cap += g
            m10 = 10.0 if g > 0 else m10 * 2
            if m10 > cap: return cap - 1000, True
            k += 1
        return cap - 1000, False
    def jouer_fixe(k0, duree_min):
        k = k0; fin_t = R[k0][2] + duree_min; tot = 0.0
        while k < len(R) and R[k][3] < fin_t: tot += 10 * mise[k]; k += 1
        return tot
    bil = {"trades": len(r), "trades_gagnants": round(float((r > 0).mean()), 4), "gain_moyen_mises": round(float(mise[r > 0].mean()), 3),
           "perte_moyenne_mises": round(float(mise[r <= 0].mean()), 3), "esperance_par_trade_mises": round(float(mise.mean()), 4),
           "pire_serie_de_pertes": int(max(len(s) for s in "".join("P" if x <= 0 else "G" for x in r).split("G"))),
           "total_sans_martingale_10e": round(float(10 * mise.sum()), 1)}
    for nom, dm in (("1_mois", 30 * 1440), ("3_mois", 90 * 1440), ("9_mois", 270 * 1440)):
        ks = [k for k in jours if k < len(R) and R[k][2] + dm <= T]
        mg = [jouer(k, dm) for k in ks]; fx = [jouer_fixe(k, dm) for k in ks]
        bil[nom] = {"departs": len(ks), "martingale_part_en_gain": round(float(np.mean([g > 0 for g, _ in mg])), 3), "martingale_part_ruinee": round(float(np.mean([z for _, z in mg])), 3),
                    "martingale_resultat_median_e": round(float(np.median([g for g, _ in mg])), 1), "mise_fixe_part_en_gain": round(float(np.mean([g > 0 for g in fx])), 3),
                    "mise_fixe_resultat_median_e": round(float(np.median(fx)), 1)}
    O[var] = bil; print(var, json.dumps(bil, ensure_ascii=False), flush=True)
    if inv:
        O["journal_btc_200_premiers"] = [[str(np.datetime64(int(a[x[2], 0]), "ms").astype("datetime64[m]")), "long" if x[1] > 0 else "short", round(a[x[2], 1], 1), str(np.datetime64(int(a[x[3], 0]), "ms").astype("datetime64[m]")), round(float(x[0] * 100), 2)] for x in R[:200]]
# fait brut : à partir d'un instant au hasard, +1 % avant -1 % ?
rng = np.random.default_rng(1); hits = []
for i0 in rng.integers(0, T - 100000, 5000):
    p = a[i0, 1]; up = np.argmax(a[i0:i0 + 100000, 2] >= p * 1.01); dn = np.argmax(a[i0:i0 + 100000, 3] <= p * 0.99); hits.append(up < dn)
O["part_plus1_avant_moins1"] = round(float(np.mean(hits)), 3); print("+1 % avant -1 % :", O["part_plus1_avant_moins1"])
json.dump(O, open("regle-tony.json", "w"), indent=1, ensure_ascii=False)

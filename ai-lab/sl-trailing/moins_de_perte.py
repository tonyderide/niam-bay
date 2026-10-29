"""PREREG-28 addendum C : combinaison (s, a, t, multiplicateur, plafond, mise) qui minimise P(perte à 3 mois) ; choisie sur 2024-2025, jugée sur 2026."""
import itertools, json, numpy as np, datetime as dt
from numba import njit
exec(open("regle_tony.py").read().split("O = {}")[0])   # a (BTC 1 min, 33 mois), chaine()
ms = lambda y, m, d: int(dt.datetime(y, m, d, tzinfo=dt.timezone.utc).timestamp() * 1000)
i26 = int(np.searchsorted(a[:, 0], ms(2026, 1, 1))); N = len(a); D = 90 * 1440
G = [(s, ac, t) for s in (0.005, 0.01, 0.015, 0.02, 0.03, 0.05) for ac in (0.005, 0.01, 0.015, 0.02, 0.03, 0.05) for t in (0.0025, 0.005, 0.01, 0.015, 0.02, 0.03) if t <= ac]
MULT, PLAF, BASE = (1.0, 1.5, 2.0, 3.0), (2, 4, 6, 10 ** 6), (2.0, 5.0, 10.0)


@njit
def jouer(mise, deb, fin, k0s, s, m, k, base):
    out = np.empty(len(k0s))
    for z in range(len(k0s)):
        k0 = k0s[z]; cap = 1000.0; st = base; perdues = 0; j = k0; ft = deb[k0] + 90 * 1440
        while j < len(mise) and fin[j] < ft:
            st = min(st, 10 * cap * s)                     # position <= 10 x capital
            cap += st * mise[j]
            if cap < 50: break                             # ruine
            if mise[j] > 0: st = base; perdues = 0
            else:
                perdues += 1
                if perdues >= k: st = base; perdues = 0       # plafond atteint : on encaisse, retour à la base
                else: st = st * m
            j += 1
        out[z] = cap - 1000
    return out


def departs(R, lo, hi):
    deb = R[:, 2].astype(np.int64); jours = np.arange(lo, hi - D + 1, 1440)
    ks = np.searchsorted(deb, jours); return ks[(ks < len(R))]


res = []
for g in G:
    out = np.empty((N + 1, 4)); n = chaine(a[:, 1], a[:, 2], a[:, 3], a[:, 4], g[0], g[2], g[1], False, out); R = out[:n]
    mise = R[:, 0] / g[0]; deb = R[:, 2].astype(np.int64); fin = R[:, 3].astype(np.int64)
    k1 = departs(R, 0, i26); k2 = departs(R, i26, N)
    for m, k, b in itertools.product(MULT, PLAF, BASE):
        if m == 1.0 and k != 10 ** 6: continue            # sans martingale le plafond ne change rien
        r1 = jouer(mise, deb, fin, k1, g[0], m, k, b); r2 = jouer(mise, deb, fin, k2, g[0], m, k, b)
        f = lambda r: {"departs": len(r), "p_perte": round(float((r < 0).mean()), 4), "median_e": round(float(np.median(r)), 1), "pire_5pc_e": round(float(np.quantile(r, 0.05)), 1),
                       "ruines": round(float((r <= -950).mean()), 4), "moyenne_e": round(float(r.mean()), 1)}
        res.append({"s": g[0], "a": g[1], "t": g[2], "mult": m, "plafond": "∞" if k > 100 else k, "mise": b, "2024_2025": f(r1), "2026": f(r2)})
cand = [x for x in res if x["2024_2025"]["median_e"] > 0]
best = min(cand, key=lambda x: (x["2024_2025"]["p_perte"], -x["2024_2025"]["median_e"]))
j = best["2026"]; vrai = j["p_perte"] <= 0.10 and j["pire_5pc_e"] >= -200
O = {"combinaisons": len(res), "candidates_mediane_positive_2024_2025": len(cand), "choisie": best, "verdict_moins_de_10pc": "VRAI" if vrai else "FAUX",
     "p_perte_2026_toutes": {"min": min(x["2026"]["p_perte"] for x in res), "mediane": float(np.median([x["2026"]["p_perte"] for x in res]))},
     "sans_martingale_meilleure_2024_2025": min([x for x in cand if x["mult"] == 1.0], key=lambda x: (x["2024_2025"]["p_perte"], -x["2024_2025"]["median_e"])),
     "top10_2024_2025": sorted(cand, key=lambda x: (x["2024_2025"]["p_perte"], -x["2024_2025"]["median_e"]))[:10]}
json.dump({**O, "toutes": res}, open("moins-de-perte.json", "w"), indent=1, ensure_ascii=False)
for k_, v in O.items():
    if k_ != "top10_2024_2025": print(k_, v)
for x in O["top10_2024_2025"]: print("top", {k_: x[k_] for k_ in ("s", "a", "t", "mult", "plafond", "mise")}, "| 24-25", x["2024_2025"]["p_perte"], x["2024_2025"]["median_e"], "| 2026", x["2026"]["p_perte"], x["2026"]["median_e"], x["2026"]["pire_5pc_e"])

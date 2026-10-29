"""PREREG-28 addendum B : inversion après perte seulement, grille SL / activation / trailing sur BTC 1 min ; réglage choisi sur 2024-2025, jugé sur 2026."""
import itertools, json, numpy as np, sys, datetime as dt
src = open("regle_tony.py").read()
exec(src.split("O = {}")[0])   # a (BTC 1 min coupé), chaine(), TK
ms = lambda y, m, d: int(dt.datetime(y, m, d, tzinfo=dt.timezone.utc).timestamp() * 1000)
i26 = int(np.searchsorted(a[:, 0], ms(2026, 1, 1)))
P = {"2024_2025": a[:i26], "2026": a[i26:]}
G = [(s, ac, t) for s in (0.005, 0.01, 0.015, 0.02, 0.03, 0.05) for ac in (0.005, 0.01, 0.015, 0.02, 0.03, 0.05) for t in (0.0025, 0.005, 0.01, 0.015, 0.02, 0.03) if t <= ac]


def run(x, g):
    out = np.empty((len(x) + 1, 4)); m = chaine(x[:, 1], x[:, 2], x[:, 3], x[:, 4], g[0], g[2], g[1], False, out); return out[:m]


def stats(R, g):
    r = R[:, 0]; mise = r / g[0]; n = len(r)
    return {"trades": n, "gagnants": round(float((r > 0).mean()), 3), "esperance_mises": round(float(mise.mean()), 4),
            "total_10e": round(float(10 * mise.sum()), 1), "brut_pct": round(float((r + TK * 2).sum() * 100), 1), "frais_pct": round(n * 2 * TK * 100, 1)}


T = {k: {str(g): stats(run(x, g), g) for g in G} for k, x in P.items()}
fige = max(G, key=lambda g: T["2024_2025"][str(g)]["esperance_mises"])
j = T["2026"][str(fige)]
# témoin hasard sur 2026
x = P["2026"]; rng = np.random.default_rng(28); H = []
for _ in range(200):
    k = rng.permutation(len(x)); o, h, l, c = x[k, 1], x[k, 2], x[k, 3], x[k, 4]
    gap = np.r_[1.0, x[1:, 1] / x[:-1, 4]][rng.permutation(len(x))]
    no = x[0, 1] * np.cumprod(np.r_[1.0, (c / o)[:-1]] * gap)
    y = np.column_stack([x[:, 0], no, h / o * no, l / o * no, c / o * no])
    H.append(stats(run(y, fige), fige)["esperance_mises"])
H = np.array(H); p = float((H >= j["esperance_mises"]).mean())
# martingale du réglage figé sur toute la période
R = run(a, fige); mise = R[:, 0] / fige[0]; deb = R[:, 2].astype(int); fin = R[:, 3].astype(int)
def jouer(k0, d):
    cap, m = 1000.0, 10.0; k = k0; ft = deb[k0] + d
    while k < len(R) and fin[k] < ft:
        gg = m * mise[k]; cap += gg; m = 10.0 if gg > 0 else 2 * m
        if m > cap: return cap - 1000, True
        k += 1
    return cap - 1000, False
mart = {}
for nom, d in (("1_mois", 30 * 1440), ("3_mois", 90 * 1440), ("9_mois", 270 * 1440)):
    ks = [k for k in np.searchsorted(deb, np.arange(0, len(a), 1440)) if k < len(R) and deb[k] + d <= len(a)]
    z = [jouer(k, d) for k in ks]
    mart[nom] = {"departs": len(ks), "en_gain": round(float(np.mean([v > 0 for v, _ in z])), 3), "ruines": round(float(np.mean([r for _, r in z])), 3), "median_e": round(float(np.median([v for v, _ in z])), 1)}
crit = j["esperance_mises"] > 0 and j["brut_pct"] > j["frais_pct"] and p < 0.05
O = {"reglages": len(G), "fige": fige, "fige_2024_2025": T["2024_2025"][str(fige)], "fige_2026": j, "hasard_2026": [round(float(H.mean()), 4), round(float(H.std()), 4)], "p": p,
     "verdict": "GAGNE" if crit else ("NON DÉMONTRÉ" if j["esperance_mises"] > 0 else "PERD"), "martingale": mart,
     "positifs_2024_2025": sum(v["esperance_mises"] > 0 for v in T["2024_2025"].values()), "positifs_2026": sum(v["esperance_mises"] > 0 for v in T["2026"].values()),
     "positifs_bruts_avant_frais_2026": sum(v["brut_pct"] > 0 for v in T["2026"].values()), "tous": T}
json.dump(O, open("grille-tony.json", "w"), indent=1)
print({k: v for k, v in O.items() if k != "tous"})
top = sorted(G, key=lambda g: -T["2026"][str(g)]["esperance_mises"])[:5]
print("5 meilleurs de 2026 (choisis après coup, ne comptent pas) :", [(g, T["2026"][str(g)]["esperance_mises"], T["2024_2025"][str(g)]["esperance_mises"]) for g in top])

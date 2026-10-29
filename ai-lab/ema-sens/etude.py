"""PREREG-30 : règle de Tony, sens donné par l'EMA horaire. Règles : ../banc-honnete/PREREG-30-ema-sens.md"""
import json, numpy as np, datetime as dt
from numba import njit
TK = 0.0005
D = "../dca-martingale/refait/donnees"
ms = lambda *x: int(dt.datetime(*x, tzinfo=dt.timezone.utc).timestamp() * 1000)


def couper(a, F=2880):
    plat = np.convolve(a[:, 2] == a[:, 3], np.ones(F, int), "valid") == F
    return a[:np.argmax(plat)] if plat.any() else a


def sens_ema(a, N):
    """+1/-1 par minute selon la dernière clôture horaire TERMINÉE contre son EMA(N) ; 0 tant que l'EMA n'est pas chauffée."""
    fin_h = np.where(((a[:, 0] // 60000) % 60) == 59)[0]            # dernière minute de chaque heure
    c = a[fin_h, 4]; e = np.empty(len(c)); k = 2 / (N + 1); e[0] = c[0]
    for j in range(1, len(c)): e[j] = c[j] * k + e[j - 1] * (1 - k)
    sh = np.where(c > e, 1, -1); sh[:3 * N] = 0                       # chauffe
    d = np.zeros(len(a), np.int64)
    pos = np.searchsorted(fin_h, np.arange(len(a)), side="left") - 1  # heure terminée strictement avant la minute i
    ok = pos >= 0; d[ok] = sh[pos[ok]]
    return d


@njit
def chaine(o, h, l, c, s, t, a, dirs, out):
    T = len(o); i = 0; m = 0
    while i < T:
        sens = dirs[i]
        if sens == 0: i += 1; continue
        e = o[i]; i0 = i; sl = e * (1 - s * sens); actif = False; pic = 0.0
        while True:
            px = -1.0
            hi = h[i] if sens > 0 else l[i]; lo = l[i] if sens > 0 else h[i]; stop = sl
            if actif:
                ts = pic * (1 - t * sens); stop = max(sl, ts) if sens > 0 else min(sl, ts)
            if (lo - stop) * sens <= 0: px = min(o[i], stop) if sens > 0 else max(o[i], stop)
            elif actif: pic = max(pic, hi) if sens > 0 else min(pic, hi)
            elif (hi - e * (1 + a * sens)) * sens >= 0: actif = True; pic = hi
            if px < 0 and i == T - 1: px = c[i]
            if px >= 0:
                out[m, 0] = sens * (px / e - 1) - TK - TK * px / e; out[m, 1] = sens; out[m, 2] = i0; out[m, 3] = i; m += 1; break
            i += 1
        i += 1
    return m


def trades(x, g, dirs):
    out = np.empty((len(x) + 1, 4)); n = chaine(x[:, 1], x[:, 2], x[:, 3], x[:, 4], g[0], g[2], g[1], dirs, out); return out[:n]


def mois(x, R, s, martingale):
    """résultat de chaque mois calendaire, capital remis à 1 000 €, état de mise remis à zéro chaque mois"""
    mo = np.array([np.datetime64(int(x[int(i), 0]), "ms").astype("datetime64[M]") for i in R[:, 2]])
    res = {}
    for m_ in np.unique(mo):
        cap, mise, k = 1000.0, 10.0, 0
        for r in R[mo == m_, 0]:
            mise = min(mise, 10 * cap * s); g = mise * r / s; cap += g
            if g > 0 or not martingale: mise, k = 10.0, 0
            else:
                k += 1; mise = 10.0 if k > 3 else mise * 2
            if cap < 50: break
        res[str(m_)] = round(cap - 1000, 1)
    return res


def bilan(x, R, s):
    r = R[:, 0]; mi = r / s
    m1 = mois(x, R, s, False); m2 = mois(x, R, s, True)
    return {"trades": len(r), "longs": round(float((R[:, 1] > 0).mean()), 3), "gagnants": round(float((r > 0).mean()), 3), "esperance_mises": round(float(mi.mean()), 4),
            "total_mise_fixe_e": round(float(10 * mi.sum()), 1), "brut_pct": round(float((r + 2 * TK).sum() * 100), 1), "frais_pct": round(len(r) * 2 * TK * 100, 1),
            "mois_positifs_fixe": f"{sum(v > 0 for v in m1.values())}/{len(m1)}", "pire_mois_fixe": min(m1.values()),
            "mois_positifs_martingale3": f"{sum(v > 0 for v in m2.values())}/{len(m2)}", "pire_mois_martingale3": min(m2.values())}


A = {s: couper(np.load(f"{D}/{s}USDT-1m.npy")) for s in ("BTC", "ETH", "SOL")}
i26 = int(np.searchsorted(A["BTC"][:, 0], ms(2026, 1, 1)))
G = [(s, ac, t) for s in (0.005, 0.01, 0.015, 0.02, 0.03, 0.05) for ac in (0.005, 0.01, 0.015, 0.02, 0.03, 0.05) for t in (0.0025, 0.005, 0.01, 0.015, 0.02, 0.03) if t <= ac]
DIRS = {(s, N): sens_ema(A[s], N) for s in A for N in (20, 50, 200)}
choix = {}
for N in (20, 50, 200):
    x = A["BTC"][:i26]; d = DIRS[("BTC", N)][:i26]
    for g in G: choix[(N, g)] = float((trades(x, g, d)[:, 0] / g[0]).mean())
N, g = max(choix, key=choix.get)
O = {"reglages": len(choix), "positifs_2024_2025_btc": sum(v > 0 for v in choix.values()), "fige": {"N": N, "s": g[0], "a": g[1], "t": g[2]}, "choix_esperance": round(choix[(N, g)], 4)}
terrains = {"BTC_2026": (A["BTC"][i26:], DIRS[("BTC", N)][i26:]), "ETH_2024_2026": (A["ETH"], DIRS[("ETH", N)]), "SOL_2024_2026": (A["SOL"], DIRS[("SOL", N)])}
rng = np.random.default_rng(30); verdict_ok = True; un_positif = False
for nom, (x, d) in terrains.items():
    R = trades(x, g, d); b = bilan(x, R, g[0]); pl = (R[:, 1] > 0).mean()
    H = np.array([(trades(x, g, np.where(rng.random(len(x)) < pl, 1, -1))[:, 0] / g[0]).mean() for _ in range(200)])
    b["hasard_moyen"] = round(float(H.mean()), 4); b["p"] = float((H >= b["esperance_mises"]).mean())
    O[nom] = b; print(nom, b, flush=True)
    verdict_ok &= b["esperance_mises"] > 0 and b["brut_pct"] > b["frais_pct"] and b["p"] < 0.05; un_positif |= b["esperance_mises"] > 0
O["verdict"] = "GAGNE" if verdict_ok else ("NON DÉMONTRÉ" if un_positif else "PERD")
# krach SOL 10/10/2025
x = A["SOL"]; k0, k1 = np.searchsorted(x[:, 0], [ms(2025, 10, 10, 12), ms(2025, 10, 11, 12)])
R = trades(x[k0:k1], g, DIRS[("SOL", N)][k0:k1]); cap = 1000.0; mise = 10.0; kk = 0
for r in R[:, 0]:
    gg = mise * r / g[0]; cap += gg; mise, kk = (10.0, 0) if gg > 0 else ((10.0, 0) if kk + 1 > 3 else (mise * 2, kk + 1))
O["krach_sol_10_10_2025"] = {"trades": len(R), "longs": int((R[:, 1] > 0).sum()), "capital_final_martingale3": round(cap, 1), "total_mise_fixe_e": round(float(10 * (R[:, 0] / g[0]).sum()), 1)}
print("figé", O["fige"], "| choix", O["choix_esperance"], "| réglages positifs BTC 2024-25 :", O["positifs_2024_2025_btc"], "/", O["reglages"])
print("krach", O["krach_sol_10_10_2025"]); print("VERDICT", O["verdict"])
json.dump(O, open("resultats.json", "w"), indent=1, default=lambda z: z.item() if hasattr(z, "item") else str(z))

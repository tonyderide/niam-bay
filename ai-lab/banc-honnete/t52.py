"""PREREG-52 : BTC mène les altcoins à 1 h (règles : PREREG-52-btc-mene.md, commit a8fbffb)."""
import glob, json, os, numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(ICI, "../dca-martingale/refait/donnees"); H = 3_600_000; TK = 0.0005
src = open("t39.py").read(); couper = None; exec(src[src.index("def couper"):src.index("def journalier")])
univ = set(json.load(open(os.path.join(D, "../univers.json"))))
T0 = 1704067200000; NH = (1790812800000 - T0) // H        # jusqu'au 01/10/2026 00:00
S = np.zeros(NH); N = np.zeros(NH); BC = np.full(NH, np.nan)
for f in sorted(glob.glob(f"{D}/*-1h.npy")):
    s = os.path.basename(f)[:-7]
    if s not in univ: continue
    a = couper(np.load(f)); k = ((a[:, 0] - T0) // H).astype(int); m = (k >= 0) & (k < NH); k, a = k[m], a[m]
    if s == "BTCUSDT": BC[k] = a[:, 4]; continue
    S[k] += a[:, 4] / a[:, 1] - 1; N[k] += 1
PAN = np.where(N > 0, S / np.maximum(N, 1), 0.0)
RB = np.full(NH, np.nan); RB[2:] = BC[1:-1] / BC[:-2] - 1       # RB[h] = rendement BTC de l'heure h-1
t = T0 + np.arange(NH) * H; I1 = t < 1767225600000; I2 = t >= 1767225600000
def run(pos, I):
    p = np.where(I, pos, 0); prev = np.r_[0, p[:-1]]; fr = TK * np.abs(p - prev)
    g = p * PAN; return float(g[I].sum()), float(fr[I].sum()), int((p[I] != 0).sum())
def positions(tau): return np.where(np.nan_to_num(np.abs(RB)) > tau, np.sign(np.nan_to_num(RB)), 0.0)
G = {}
for tau in (0.005, 0.01, 0.02):
    p = positions(tau); G[tau] = {}
    for nom, I in (("2024-25", I1), ("2026", I2)):
        b, f, n = run(p, I); G[tau][nom] = dict(brut=b, frais=f, net=b - f, heures=n, gagnantes=float(((p * PAN)[I & (p != 0)] > 0).mean()) if n else 0)
    print(tau, {k: {a: round(c, 4) for a, c in v.items()} for k, v in G[tau].items()}, flush=True)
tc = max(G, key=lambda x: G[x]["2024-25"]["net"]); c = G[tc]
corr = {nom: float(np.corrcoef(np.nan_to_num(RB[I & ~np.isnan(RB)]), PAN[I & ~np.isnan(RB)])[0, 1]) for nom, I in (("2024-25", I1), ("2026", I2))}
garde = c["2024-25"]["brut"] >= 2 * c["2024-25"]["frais"]
out = dict(tau=tc, grille={str(k): v for k, v in G.items()}, correlation_btc_h_1_panier_h=corr, garde_fou_brut_2x_frais=garde)
if not garde:
    v = "PERD"
else:
    p = positions(tc); ep = np.cumsum(np.r_[1, (np.diff(p) != 0)]) ; rng = np.random.default_rng(52); tem = []
    for _ in range(1000):
        sg = rng.choice([-1.0, 1.0], ep.max() + 1)[ep]; b, f, _ = run(np.abs(p) * sg, I2); tem.append(b - f)
    tem = np.array(tem); out["temoin_2026"] = dict(moy=float(tem.mean()), et=float(tem.std()), p=float((tem >= c["2026"]["net"]).mean()))
    v = "GAGNE" if c["2024-25"]["net"] > 0 and c["2026"]["net"] > 0 and out["temoin_2026"]["p"] < 0.05 else "NON DÉMONTRÉ" if c["2026"]["net"] > 0 else "PERD"
out["verdict"] = v; json.dump(out, open("t52.json", "w"), indent=1); print(json.dumps({k: out[k] for k in out if k != "grille"}, indent=1))

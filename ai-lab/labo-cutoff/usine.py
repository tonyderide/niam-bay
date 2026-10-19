"""L'usine à stratégies (protocole a2ad9ab). numpy, sans LLM."""
import json, time, itertools
import numpy as np
D = json.load(open("candles.json")); T0 = time.mktime(time.strptime("2026-07-01", "%Y-%m-%d")); FEE = 0.001
TPS, SLS, HOLDS = [0.003, 0.005, 0.01, 0.02], [0.005, 0.01, 0.02, 0.04], [6, 24, 72]
coins = {}
for k, d in D.items():
    t = np.array(sorted(int(x) for x in d)); c = np.array([d[str(x)] for x in t])
    coins[k] = (t, c)

def ema(x, n):
    a = 2 / (n + 1); out = np.empty_like(x); out[0] = x[0]
    for i in range(1, len(x)): out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out

def rsi(c, n=14):
    d = np.diff(c, prepend=c[0]); up = np.where(d > 0, d, 0); dn = np.where(d < 0, -d, 0)
    au, ad = ema(up, 2 * n - 1), ema(dn, 2 * n - 1); return 100 - 100 / (1 + au / np.maximum(ad, 1e-12))

def outcomes(c):
    """Pour chaque (tp, sl, hold, direction) : rendement net d'une entrée à chaque heure (NaN si pas assez de futur)."""
    n = len(c); out = {}
    for hold in HOLDS:
        fwd = np.full((n, hold), np.nan)
        for j in range(1, hold + 1): fwd[: n - j, j - 1] = c[j:] / c[: n - j] - 1
        for tp, sl in itertools.product(TPS, SLS):
            for dirn in (1, -1):
                r = dirn * fwd
                hit_tp = np.where(r >= tp, np.arange(hold), hold).min(1); hit_sl = np.where(r <= -sl, np.arange(hold), hold).min(1)
                last = r[:, -1]
                res = np.where(hit_tp < hit_sl, tp, np.where(hit_sl < hit_tp, -sl, np.where(hit_tp < hold, -sl, last))) - FEE
                res[np.isnan(last)] = np.nan
                out[(tp, sl, hold, dirn)] = res
    return out

def signals(c):
    S = {}
    for k in (1, 3, 6, 12, 24, 48):
        r = np.full(len(c), np.nan); r[k:] = c[k:] / c[:-k] - 1
        for th in (0.005, 0.01, 0.02, 0.04):
            S[f"r{k}h>+{th}"] = r > th; S[f"r{k}h<-{th}"] = r < -th
    R = rsi(c)
    for th in (25, 30): S[f"rsi<{th}"] = R < th
    for th in (70, 75): S[f"rsi>{th}"] = R > th
    for n in (20, 50, 200):
        e = ema(c, n); dev = c / e - 1
        for th in (0.01, 0.02, 0.04): S[f"ema{n}>+{th}"] = dev > th; S[f"ema{n}<-{th}"] = dev < -th
    for n in (12, 24, 72):
        hi = np.full(len(c), np.nan); lo = np.full(len(c), np.nan)
        for i in range(n, len(c)): hi[i] = c[i - n:i].max(); lo[i] = c[i - n:i].min()
        S[f"casse_haut{n}"] = c > hi; S[f"casse_bas{n}"] = c < lo
    return S

rng = np.random.default_rng(1019)
rows = []  # (nom, train_mean, train_n, train_win, test_mean, test_n, test_win, test_returns, test_times)
for k, (t, c) in coins.items():
    O = outcomes(c); S = signals(c); train = t < T0; test = ~train
    for sname, mask in S.items():
        freq = np.nanmean(mask.astype(float))
        rand_mask = rng.random(len(c)) < freq
        for key, res in O.items():
            for kind, m in (("vrai", mask), ("hasard", rand_mask)):
                tr = res[m & train]; tr = tr[~np.isnan(tr)]; te = res[m & test]; tt = t[m & test][~np.isnan(te)]; te = te[~np.isnan(te)]
                if len(tr) >= 50 and len(te) >= 20:
                    rows.append((kind, f"{k} {sname} TP{key[0]} SL{key[1]} H{key[2]} {'long' if key[3] > 0 else 'short'}",
                                 tr.mean(), len(tr), (tr > 0).mean(), te.mean(), len(te), (te > 0).mean(), te, tt))
vrai = sorted([r for r in rows if r[0] == "vrai"], key=lambda r: -r[2]); has = sorted([r for r in rows if r[0] == "hasard"], key=lambda r: -r[2])
p95 = np.percentile([r[5] for r in has], 95)

def boot(te, tt, B=3000):
    wk = (tt // (7 * 86400)).astype(int); blocks = [te[wk == w] for w in np.unique(wk)]
    s = 0
    for _ in range(B):
        pick = rng.integers(0, len(blocks), len(blocks)); s += np.concatenate([blocks[i] for i in pick]).mean() > 0
    return s / B

print(f"{len([r for r in rows if r[0]=='vrai'])} stratégies réelles et {len(has)} au hasard (≥ 50 paris en entraînement, ≥ 20 en test)")
print(f"95e percentile du gain en test des stratégies AU HASARD : {p95*100:+.3f} %/pari\n")
print("TOP 20 sur janvier-juin → jugé sur juillet-octobre :")
found = 0
for r in vrai[:20]:
    P = boot(r[8], r[9]); ok = r[5] > 0 and P > 0.95 and r[5] > p95; found += ok
    print(f"{'✅' if ok else '❌'} {r[1]:42} | train {r[2]*100:+.3f} % ({r[3]}, {r[4]:.0%}) | TEST {r[5]*100:+.3f} % ({r[6]}, {r[7]:.0%}) P>0 {P:.2f}")
print("\nTop 20 des stratégies AU HASARD, pour comparaison : gain moyen en train",
      f"{np.mean([r[2] for r in has[:20]])*100:+.3f} %, en test {np.mean([r[5] for r in has[:20]])*100:+.3f} %")
print("Top 20 RÉELLES : gain moyen en train", f"{np.mean([r[2] for r in vrai[:20]])*100:+.3f} %, en test {np.mean([r[5] for r in vrai[:20]])*100:+.3f} %")
hi_wr = [r for r in vrai if r[7] >= 0.85 and r[5] > 0]
print(f"\nStratégies à ≥ 85 % de gagnants EN TEST et gain > 0 : {len(hi_wr)}" + "".join(f"\n   {r[1]} test {r[5]*100:+.3f} % ({r[6]} paris, {r[7]:.0%}), train {r[2]*100:+.3f} %" for r in sorted(hi_wr, key=lambda r: -r[5])[:8]))
print(f"\nSTRATÉGIES TROUVÉES selon le critère : {found}")

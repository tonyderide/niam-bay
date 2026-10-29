import json, numpy as np
exec(open("moins_de_perte.py").read().split("res = []")[0])
g = (0.05, 0.01, 0.01)
def run(x):
    out = np.empty((len(x) + 1, 4)); n = chaine(x[:, 1], x[:, 2], x[:, 3], x[:, 4], g[0], g[2], g[1], False, out); return out[:n]
R = run(a); r = R[:, 0]; mise = r / g[0]
print("trades", len(r), "par mois", round(len(r) / 33, 1))
print("répartition des sorties (en % du prix) :", np.round(np.quantile(r * 100, [0, .01, .05, .25, .5, .75, .95, 1]), 3))
sl = r < -0.03; print("SL touchés (≈ -5 %) :", int(sl.sum()), "soit 1 trade sur", round(len(r) / max(1, sl.sum())))
print("gains > 0 :", round(float((r > 0).mean()), 3), " pertes minuscules (entre -0,3 % et 0) :", round(float(((r <= 0) & (r > -0.003)).mean()), 3))
print("espérance par trade (en % du prix) :", round(float(r.mean() * 100), 4), " avant frais :", round(float((r + 0.001).mean() * 100), 4))
for i in np.where(sl)[0]: print("  SL", np.datetime64(int(a[int(R[i, 2]), 0]), "ms").astype("datetime64[m]"), "->", np.datetime64(int(a[int(R[i, 3]), 0]), "ms").astype("datetime64[m]"), "long" if R[i, 1] > 0 else "short", round(r[i] * 100, 2), "%")
# même règle + même martingale sur BTC mélangé (volatilité gardée, tendance retirée), 20 mélanges de toute la période
rng = np.random.default_rng(5); P = []
for _ in range(20):
    k = rng.permutation(len(a)); o, h, l, c = a[k, 1], a[k, 2], a[k, 3], a[k, 4]
    gap = np.r_[1.0, a[1:, 1] / a[:-1, 4]][rng.permutation(len(a))]; no = a[0, 1] * np.cumprod(np.r_[1.0, (c / o)[:-1]] * gap)
    y = np.column_stack([a[:, 0], no, h / o * no, l / o * no, c / o * no]); Ry = run(y)
    ks = departs(Ry, 0, N); rr = jouer(Ry[:, 0] / g[0], Ry[:, 2].astype(np.int64), Ry[:, 3].astype(np.int64), ks, g[0], 3.0, 4, 10.0)
    P.append(((rr < 0).mean(), np.median(rr), (Ry[:, 0] < -0.03).sum()))
P = np.array(P); print("hasard : P(perte 3 mois) moyenne", round(P[:, 0].mean(), 3), "min", round(P[:, 0].min(), 3), "max", round(P[:, 0].max(), 3), "| médiane", round(P[:, 1].mean(), 1), "€ | SL touchés", P[:, 2].mean())

# Exporte les trades MACD+EMA200 (règles de PREREG-02, mêmes fonctions que t02.py) avec leur date, pour la vidéo.
import json, random, sys
sys.path.insert(0, "../banc-honnete")
src = open("../banc-honnete/t02.py").read().split("SYM = ")[0]
exec(src)
def run_t(T, C, a):
    cl = [c[3] for c in C]; e200 = ema(cl, 200); m = [x-y for x, y in zip(ema(cl, 12), ema(cl, 26))]; sg = ema(m, 9)
    n = len(C); i = 1; tr = []
    while i < n-1:
        if T[i] >= a and i > 300:
            up = m[i-1] <= sg[i-1] and m[i] > sg[i] and m[i] < 0 and sg[i] < 0 and cl[i] > e200[i]
            dn = m[i-1] >= sg[i-1] and m[i] < sg[i] and m[i] > 0 and sg[i] > 0 and cl[i] < e200[i]
            if up or dn:
                s = 1 if up else -1; dist = max(.003, abs(C[i+1][0]-e200[i])/C[i+1][0])
                r, j = walk(C, i+1, s, dist, n); tr.append((T[i+1], r, dist)); i = j+1; continue
        i += 1
    return tr
SYM = {"BTC": "PF_XBTUSD", "ETH": "PF_ETHUSD", "SOL": "PF_SOLUSD"}
a, b = ts("2024-01-01"), ts("2026-01-01"); allt = []; rand = [[] for _ in range(50)]
for k, s in SYM.items():
    T, C = h1(s, a, b); tr = run_t(T, C, a); allt += [(t, r, k) for t, r, _ in tr]
    lo = next(i for i, t in enumerate(T) if t >= a)
    for j in range(50):
        rnd = random.Random(j)
        for _, _, dist in tr:
            i = rnd.randrange(lo, len(C)-2); rand[j].append((T[i], walk(C, i, rnd.choice((1, -1)), dist, len(C))[0]))
allt.sort(); out = {"trades": allt, "hasard": [sorted(x) for x in rand]}
json.dump(out, open("macd_trades.json", "w"))
print(len(allt), "trades | gagnants", f"{sum(r > 0 for _, r, _ in allt)/len(allt):.0%}", "| somme", f"{sum(r for _, r, _ in allt)*100:+.1f} %")

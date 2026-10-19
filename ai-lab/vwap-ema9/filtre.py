# Variante "pas trop précis" : on ignore les petits croisements.
# Seuil = écart EMA9/VWAP minimal (%), conf = nb de bougies 3m où le croisement doit tenir.
# Sélection sur janvier-juin, jugement sur juillet-octobre. Taker 0.05 %/côté, SL 0.1 % en option.
import json, random, sys
sys.argv = ["x"]; exec(open("test.py").read().split("SYM = ")[0])
SYM = {"BTC": "PF_XBTUSD", "ETH": "PF_ETHUSD", "SOL": "PF_SOLUSD"}
def sim(T, C, seuil, conf, sl, fee=0.0005):
    n = len(C); e = C[0][3]; pv = vv = 0; day = None; want = 0; run_ = 0; pos = 0; entry = 0; eq = 1.0; tr = []
    for i in range(n):
        o, h, l, c, v = C[i]; d = T[i] // 86400
        if pos and sl:  # stop dans la bougie
            stop = entry*(1-sl) if pos > 0 else entry*(1+sl)
            if (pos > 0 and l <= stop) or (pos < 0 and h >= stop):
                r = -sl - fee; tr.append(r); eq *= 1+r; pos = 0
        if d != day: pv = vv = 0; day = d
        pv += (h+l+c)/3*v; vv += v; vw = pv/vv if vv else c
        e = c if i == 0 else e + (c-e)*2/10
        g = (e/vw - 1)
        s = 1 if g > seuil else -1 if g < -seuil else 0
        run_ = run_+1 if s and s == want else (1 if s else 0); want = s if s else want
        if s and run_ >= conf and s != pos and i+1 < n:
            px = C[i+1][0]
            if pos: r = pos*(px/entry-1) - fee; tr.append(r); eq *= 1+r
            pos = s; entry = px; eq *= 1-fee
    return eq-1, tr
D = {k: candles(s) for k, s in SYM.items()}
cut = ts("2026-07-01")
def split(T, C, f):
    idx = [i for i, t in enumerate(T) if f(t)]; return [T[i] for i in idx], [C[i] for i in idx]
grid = [(s, c, sl) for s in (0, .0005, .001, .002, .003, .005) for c in (1, 2, 3, 5) for sl in (0, .001, .003)]
res = []
for g in grid:
    a = [sim(*split(*D[k], lambda t: t < cut), *g)[0] for k in D]
    res.append((sum(a)/3, g, a))
res.sort(reverse=True)
print("TOP 5 sur janvier-juin (moyenne des 3) :")
for m, g, a in res[:5]: print(f"  seuil {g[0]*100:.2f}% conf {g[1]} SL {g[2]*100:.1f}% -> moy {m*100:+.1f}%  ", " ".join(f"{x*100:+.1f}" for x in a))
m, g, _ = res[0]
print(f"\nJUGEMENT juillet-octobre, réglage figé seuil {g[0]*100:.2f}% conf {g[1]} SL {g[2]*100:.1f}% :")
for k in D:
    r, tr = sim(*split(*D[k], lambda t: t >= cut), *g)
    print(f"  {k}: trades {len(tr):4} | gagnants {sum(x>0 for x in tr)/max(1,len(tr)):.0%} | total {r*100:+.1f}%")

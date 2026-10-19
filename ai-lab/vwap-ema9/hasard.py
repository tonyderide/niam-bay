import random, pickle, os
exec(open("filtre.py").read().split("D = {k")[0])
P = "/tmp/claude-1000/-home-tony/2c25ff3c-37a9-4b0e-a8fd-9600199a4cb4/scratchpad/vwap3m.pkl"
D = pickle.load(open(P,"rb")) if os.path.exists(P) else {k: candles(s) for k, s in SYM.items()}
pickle.dump(D, open(P,"wb"))
cut = ts("2026-07-01")
def split(T, C, f):
    idx = [i for i, t in enumerate(T) if f(t)]; return [T[i] for i in idx], [C[i] for i in idx]
def rand(C, ntr, rnd, fee=0.0005):
    n = len(C); fl = sorted(rnd.sample(range(1, n-1), ntr)); pos = 1; entry = C[fl[0]][0]; eq = 1-fee
    for i in fl[1:]:
        px = C[i][0]; eq *= 1 + pos*(px/entry-1) - fee; pos = -pos; entry = px; eq *= 1-fee
    return eq-1
for k in D:
    T, C = split(*D[k], lambda t: t >= cut)
    r, tr = sim(T, C, .005, 5, 0)
    R = sorted(rand(C, len(tr)+1, random.Random(s)) for s in range(500))
    bh = C[-1][3]/C[0][0]-1
    print(f"{k}: filtre {r*100:+.1f}% | hasard médiane {R[250]*100:+.1f}% p95 {R[475]*100:+.1f}% | rang {sum(x<r for x in R)/5:.0f}e centile | prix du début à la fin {bh*100:+.1f}%")
# seuils plus larges (bord de grille ?) — sélection janv-juin seulement
print("seuils plus larges, janvier-juin / juillet-octobre (conf 5, sans SL) :")
for s in (.005, .0075, .01, .015):
    a = [sim(*split(*D[k], lambda t: t < cut), s, 5, 0)[0]*100 for k in D]; b = [sim(*split(*D[k], lambda t: t >= cut), s, 5, 0)[0]*100 for k in D]
    print(f"  {s*100:.2f}%  J-J " + " ".join(f"{x:+.0f}" for x in a) + "  |  J-O " + " ".join(f"{x:+.0f}" for x in b))

#!/usr/bin/env python3
"""6e essai : C0 = S (mon 112) est fixé, C1 = A·S + b. On minimise le nombre de conflits
#{(c0, c1, u) : c0 + c1 + u = 0} = Σ_{c1} count[c1], où count[x] = #{(c0, w) : x = w − c0, w ∈ −U}.
On fait du hill-climbing sur (A, b) par des mouvements élémentaires (ajout d'une ligne, changement d'échelle, translation).
0 conflit ⇒ cap de 236 points."""
import itertools, random, sys, time
from collections import Counter
from multiprocessing import Pool
from capset import judge
from cf236 import S, U, rand_GL, apply

negU = [tuple((-x) % 3 for x in u) for u in U]
COUNT = Counter(tuple((w[i] - c[i]) % 3 for i in range(6)) for w in negU for c in S)


def cost(A, b):
    return sum(COUNT[c] for c in apply(A, b, S))


def run(seed):
    rng = random.Random(seed); t0 = time.time(); best = None
    while time.time() - t0 < 250:
        A = rand_GL(rng); b = [rng.randrange(3) for _ in range(6)]; cur = cost(A, b); stall = 0
        while stall < 3000 and time.time() - t0 < 250:
            A2 = [r[:] for r in A]; b2 = b[:]; m = rng.randrange(3)
            i, j = rng.sample(range(6), 2)
            if m == 0: A2[i] = [(x + rng.choice((1, 2)) * y) % 3 for x, y in zip(A2[i], A2[j])]
            elif m == 1: A2[i], A2[j] = A2[j], A2[i]
            else: b2[i] = rng.randrange(3)
            c2 = cost(A2, b2)
            if c2 <= cur:
                stall = 0 if c2 < cur else stall + 1; A, b, cur = A2, b2, c2
            else: stall += 1
            if cur == 0: return 0, A, b
        if best is None or cur < best[0]: best = (cur, A, b)
    return best


if __name__ == "__main__":
    with Pool(8) as p:
        res = sorted(p.map(run, range(8)), key=lambda r: r[0])
    print("conflits minimaux par graine :", [r[0] for r in res])
    c, A, b = res[0]
    C1 = apply(A, b, S)
    cap = [(0,) + x for x in S] + [(1,) + x for x in C1] + [(2,) + u for u in U]
    print("judge du cap construit :", judge(cap), "(236 seulement si 0 conflit)")
    if judge(cap) == 236:
        open("best_n7_236.txt", "w").write("\n".join("".join(map(str, q)) for q in sorted(cap)))

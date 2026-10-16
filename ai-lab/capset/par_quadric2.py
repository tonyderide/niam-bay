#!/usr/bin/env python3
"""n=7, une idée de plus : graine dans l'intersection de deux quadriques {Q1=c1} ∩ {Q2=c2}, dont les tailles
(~3^5) sont proches de celles des meilleurs caps, puis LNS. 8 graines en parallèle."""
import itertools, random, sys, time, io, contextlib
from multiprocessing import Pool
from capset import judge
from quadric import make_Q, greedy_in
from lns import lns

N, S1, S2 = 7, float(sys.argv[1]), float(sys.argv[2])


def run(seed):
    rng = random.Random(seed); pts = list(itertools.product(range(3), repeat=N)); best = []; t0 = time.time()
    while time.time() - t0 < S1:
        Q1, Q2 = make_Q(N, rng), make_Q(N, rng); c1, c2 = rng.randrange(3), rng.randrange(3)
        pool = [p for p in pts if Q1(p) == c1 and Q2(p) != c2]
        if len(pool) < 200: continue
        S = greedy_in(pool, rng, 6)
        if len(S) > len(best): best = S
    with contextlib.redirect_stdout(io.StringIO()):
        b, _ = lns(N, best, S2, random.Random(seed + 1))
    return judge(b), len(best), b


if __name__ == "__main__":
    with Pool(8) as p:
        res = sorted(p.map(run, range(900, 908)), key=lambda r: -r[0])
    print("n=7 deux quadriques (graine→final):", [(r[1], r[0]) for r in res])
    if res[0][0] > 224:
        open("best_n7_2q.txt", "w").write("\n".join("".join(map(str, q)) for q in sorted(res[0][2])))

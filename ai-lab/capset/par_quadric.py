#!/usr/bin/env python3
import itertools, random, sys, time, io, contextlib
from multiprocessing import Pool
from capset import judge
from quadric import make_Q, greedy_in
from lns import lns

N, S1, S2 = int(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])


def run(seed):
    rng = random.Random(seed); pts = list(itertools.product(range(3), repeat=N)); best = []; t0 = time.time()
    while time.time() - t0 < S1:
        Q = make_Q(N, rng); c = rng.randrange(3); pool = [p for p in pts if Q(p) == c]
        S = greedy_in(pool, rng, 10)
        if len(S) > len(best): best = S
    with contextlib.redirect_stdout(io.StringIO()):
        b, _ = lns(N, best, S2, random.Random(seed + 1))
    return judge(b), len(best), b


if __name__ == "__main__":
    with Pool(8) as p:
        res = sorted(p.map(run, range(700, 708)), key=lambda r: -r[0])
    print(f"n={N} (graine→final) :", [(r[1], r[0]) for r in res])
    open(f"best_n{N}.txt", "w").write("\n".join("".join(map(str, q)) for q in sorted(res[0][2])))

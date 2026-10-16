#!/usr/bin/env python3
"""Structure + recherche, comme pour la cap set : graine Bose, puis recherche locale qui déplace 1-2 marques
au hasard et garde tout ce qui reste Golomb sans s'allonger (longueur, puis somme des marques pour départager)."""
import random, sys, time
from golomb import judge, OPT
from bose import bose, best_linear


def norm(m):
    m = sorted(m); return [x - m[0] for x in m]


def polish(m, secs, rng):
    cur = norm(m); best = list(cur); t0 = time.time()
    score = lambda r: (r[-1], sum(r))
    while time.time() - t0 < secs:
        L = cur[-1]; new = list(cur)
        for _ in range(rng.randint(1, 2)):
            i = rng.randrange(len(new)); new[i] = rng.randrange(0, L + 1)
        if len(set(new)) < len(new) or judge(new) is None: continue
        new = norm(new)
        if score(new) <= score(cur):
            cur = new
            if new[-1] < best[-1]: best = list(new)
    return best


if __name__ == "__main__":
    rng = random.Random(5)
    for p in [11, 13]:
        B, N = bose(p); seed = best_linear(B, N)
        b = polish(seed, float(sys.argv[1]) if len(sys.argv) > 1 else 60, rng)
        print(f"{p} marques : Bose {judge(seed)} → polie {judge(b)} | optimum {OPT[p]} | {b}")

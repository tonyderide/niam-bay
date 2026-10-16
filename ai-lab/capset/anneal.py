#!/usr/bin/env python3
"""LNS avec recuit : on accepte parfois de perdre 1-2 points pour sortir des plateaux."""
import math, random, sys, time
from capset import judge
from lns import refill
from orbits import orbits, dfs


def anneal(n, start, seconds, rng, T0=1.5):
    cur = best = list(start); t0 = time.time(); it = 0
    while (el := time.time() - t0) < seconds:
        it += 1; T = T0 * (1 - el / seconds) + 0.05
        k = rng.randint(2, max(3, len(cur) // 6))
        new = refill(n, rng.sample(cur, len(cur) - k), rng)
        d = len(new) - len(cur)
        if d >= 0 or rng.random() < math.exp(d / T):
            cur = new
            if len(cur) > len(best):
                best = cur; print(f"  {el:5.0f}s: {len(best)}", flush=True)
    return best


if __name__ == "__main__":
    n, secs = int(sys.argv[1]), float(sys.argv[2])
    rng = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 5)
    b = anneal(n, dfs(orbits(n)), secs, rng)
    print(f"n={n}: {judge(b)}")
    if judge(b) == len(b):
        open(f"best_n{n}.txt", "w").write("\n".join("".join(map(str, p)) for p in sorted(b)))

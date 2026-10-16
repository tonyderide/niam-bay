#!/usr/bin/env python3
"""Plusieurs graines en parallèle : LNS stricte depuis la structure en orbites."""
import random, sys
from multiprocessing import Pool
from capset import judge
from lns import lns
from orbits import orbits, dfs

N, SECS = int(sys.argv[1]), float(sys.argv[2])
START = dfs(orbits(N))


def run(seed):
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        b, _ = lns(N, START, SECS, random.Random(seed))
    return judge(b), seed, b


if __name__ == "__main__":
    with Pool(int(sys.argv[3])) as p:
        res = sorted(p.map(run, range(100, 100 + int(sys.argv[3]))), key=lambda r: -r[0])
    print("n=%d  résultats par graine:" % N, [r[0] for r in res])
    best = res[0][2]
    open(f"best_n{N}.txt", "w").write("\n".join("".join(map(str, p)) for p in sorted(best)))

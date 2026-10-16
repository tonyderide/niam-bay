#!/usr/bin/env python3
"""Piste algébrique : graines prises DANS une quadrique {x : Q(x) = c} de F_3^n.
Sur une droite, Q(x+td) = Q(x) + t·B(x,d) + t²·Q(d) est un polynôme de degré 2 : il ne vaut c en 3 points
que si Q(d)=0 et B(x,d)=0. Les quadriques « évitent » donc beaucoup de lignes. Je teste des Q aléatoires."""
import itertools, random, sys, time
from capset import judge, third


def make_Q(n, rng):
    A = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i, n):
            A[i][j] = A[j][i] = rng.randrange(3)
    return lambda x: sum(A[i][j] * x[i] * x[j] for i in range(n) for j in range(n)) % 3


def greedy_in(pool, rng, tries):
    best = []
    for _ in range(tries):
        rng.shuffle(pool); S, inS = [], set()
        for x in pool:
            if all(third(a, x) not in inS for a in S): S.append(x); inS.add(x)
        if len(S) > len(best): best = S
    return best


if __name__ == "__main__":
    n, secs = int(sys.argv[1]), float(sys.argv[2]); rng = random.Random(9)
    pts = list(itertools.product(range(3), repeat=n)); best = []; t0 = time.time(); k = 0
    while time.time() - t0 < secs:
        Q = make_Q(n, rng); c = rng.randrange(3); pool = [p for p in pts if Q(p) == c]; k += 1
        S = greedy_in(pool, rng, 20)
        if len(S) > len(best):
            best = S; print(f"  {time.time()-t0:5.0f}s Q#{k} |Z|={len(pool)}: {judge(S)}", flush=True)
    import io, contextlib
    from lns import lns
    with contextlib.redirect_stdout(io.StringIO()):
        b2, _ = lns(n, best, float(sys.argv[3]) if len(sys.argv) > 3 else 60, random.Random(2))
    print(f"n={n}: meilleure graine quadrique {judge(best)} ({k} formes), +LNS {judge(b2)}")
    if judge(b2) == len(b2):
        open(f"best_n{n}_quadric.txt", "w").write("\n".join("".join(map(str, p)) for p in sorted(b2)))

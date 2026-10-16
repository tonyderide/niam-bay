#!/usr/bin/env python3
"""3e idée : chercher DIRECTEMENT un cap de F_3^6 dont tous les points sont à distance de Hamming ≥ 2 deux à deux.
La contrainte est intégrée à la recherche (graine quadrique + LNS), au lieu d'être un filtre appliqué après coup.
S'il atteint 112, alors {0}×C ∪ {1}×(−C) ∪ {2}×U est un cap de 236 points."""
import itertools, random, sys, time, io, contextlib
from multiprocessing import Pool
from capset import judge, third
from quadric import make_Q
from cf236 import U

N = 6
PTS = list(itertools.product(range(3), repeat=N))
NB = {p: [tuple((p[j] + d) % 3 if j == i else p[j] for j in range(N)) for i in range(N) for d in (1, 2)] for p in PTS}


def ok(x, S, inS):
    return all(n not in inS for n in NB[x]) and all(third(a, x) not in inS for a in S)


def fill(S, pool, rng):
    S = list(S); inS = set(S); pool = list(pool); rng.shuffle(pool)
    for x in pool:
        if x not in inS and ok(x, S, inS): S.append(x); inS.add(x)
    return S


def run(seed):
    rng = random.Random(seed); best = []; t0 = time.time()
    while time.time() - t0 < 60:  # graines quadriques sous contrainte
        Q = make_Q(N, rng); c = rng.randrange(3)
        S = fill([], [p for p in PTS if Q(p) == c], rng)
        if len(S) > len(best): best = S
    cur = best
    while time.time() - t0 < 230:  # LNS sous contrainte
        k = rng.randint(2, max(3, len(cur) // 6))
        new = fill(rng.sample(cur, len(cur) - k), PTS, rng)
        if len(new) >= len(cur): cur = new
    return len(cur), cur


if __name__ == "__main__":
    with Pool(8) as p:
        res = sorted(p.map(run, range(8)), key=lambda r: -r[0])
    print("tailles (cap + distance ≥ 2) :", [r[0] for r in res])
    C = res[0][1]
    cap = [(0,) + c for c in C] + [(1,) + tuple((-x) % 3 for x in c) for c in C] + [(2,) + u for u in U]
    print("cap construit en dimension 7 : judge =", judge(cap))
    if judge(cap) >= 236:
        open("best_n7_236.txt", "w").write("\n".join("".join(map(str, q)) for q in sorted(cap)))

#!/usr/bin/env python3
"""J'applique la leçon des neurones : des graines VRAIMENT indépendantes pour n=7, chacune avec une structure
différente (quadrique, deux quadriques, orbites par permutation, hasard pur, produit 45×4 de n=5×n=2), puis la même LNS."""
import itertools, random, time, io, contextlib
from multiprocessing import Pool
from capset import judge
from quadric import make_Q, greedy_in
from search import random_greedy, product
from orbits import orbits, dfs
from lns import lns

N = 7; PTS = list(itertools.product(range(3), repeat=N))
b5 = [tuple(map(int, l)) for l in open("best_n5.txt").read().split()]
cap2 = [(0, 0), (0, 1), (1, 0), (1, 1)]


def seed_of(kind, rng):
    if kind == "quadrique":
        Q = make_Q(N, rng); return greedy_in([p for p in PTS if Q(p) == rng.randrange(3)], rng, 5)
    if kind == "2quadriques":
        Q1, Q2 = make_Q(N, rng), make_Q(N, rng); return greedy_in([p for p in PTS if Q1(p) == 1 and Q2(p) != 0], rng, 5)
    if kind == "orbites": return dfs(orbits(N))
    if kind == "hasard": return random_greedy(N, rng)
    if kind == "produit45x4": return product(b5, cap2)


def run(arg):
    kind, seed = arg; rng = random.Random(seed)
    s = seed_of(kind, rng)
    with contextlib.redirect_stdout(io.StringIO()):
        b, _ = lns(N, s, 230, random.Random(seed + 1))
    return kind, len(s), judge(b), b


if __name__ == "__main__":
    jobs = [("quadrique", 1), ("quadrique", 2), ("2quadriques", 3), ("orbites", 4), ("hasard", 5), ("hasard", 6), ("produit45x4", 7), ("2quadriques", 8)]
    with Pool(8) as p:
        res = p.map(run, jobs)
    for k, s, f, _ in sorted(res, key=lambda r: -r[2]): print(f"{k:12} graine {s:3} -> {f}")
    best = max(res, key=lambda r: r[2])
    if best[2] > 224: open(f"best_n7_{best[2]}.txt", "w").write("\n".join("".join(map(str, q)) for q in sorted(best[3])))

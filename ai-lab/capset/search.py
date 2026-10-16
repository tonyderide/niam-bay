#!/usr/bin/env python3
"""Recherche : glouton aléatoire avec redémarrages, et graine produit (A×B est un cap si A et B le sont)."""
import itertools, random, sys, time
from capset import judge, third


def random_greedy(n, rng, seed=()):
    S = list(seed); inS = set(S)
    pts = [p for p in itertools.product(range(3), repeat=n) if p not in inS]
    rng.shuffle(pts)
    for x in pts:
        if all(third(a, x) not in inS for a in S):
            S.append(x); inS.add(x)
    return S


def product(A, B):
    return [a + b for a in A for b in B]


def best_random(n, seconds, rng, seed=()):
    best, t0, tries = [], time.time(), 0
    while time.time() - t0 < seconds:
        S = random_greedy(n, rng, seed); tries += 1
        if len(S) > len(best): best = S
    return best, tries


if __name__ == "__main__":
    rng = random.Random(1016)
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 20
    caps = {1: [(0,), (1,)]}
    for n in range(2, 6):
        b, tries = best_random(n, secs, rng)
        prod = max((product(caps[i], caps[n - i]) for i in range(1, n)), key=len)
        cand = max([b, prod], key=len)
        caps[n] = cand
        print(f"n={n}: random-greedy {judge(b)} ({tries} essais), produit {judge(prod)} -> retenu {judge(cand)}")

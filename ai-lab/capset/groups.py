#!/usr/bin/env python3
"""Autre structure : orbites sous un groupe choisi (décalage cyclique des coordonnées ± négation),
glouton aléatoire AU NIVEAU DES ORBITES (beaucoup de redémarrages), puis LNS sur le meilleur."""
import itertools, random, sys, time
from capset import judge, third
from lns import lns


def orbit_of(p, gens):
    seen, todo = {p}, [p]
    while todo:
        q = todo.pop()
        for g in gens:
            r = g(q)
            if r not in seen: seen.add(r); todo.append(r)
    return sorted(seen)


def all_orbits(n, gens):
    done, out = set(), []
    for p in itertools.product(range(3), repeat=n):
        if p not in done:
            o = orbit_of(p, gens); done |= set(o)
            if judge(o) == len(o): out.append(o)   # seules les orbites qui sont elles-mêmes des caps
    return out


def orbit_greedy(orbs, rng):
    rng.shuffle(orbs); S, inS = [], set()
    for o in orbs:
        cand = S + o
        if all(third(a, x) not in inS for x in o for a in S) and judge(cand) == len(cand):
            S = cand; inS |= set(o)
    return S


GROUPS = {
    "cyclique": lambda n: [lambda q: q[1:] + q[:1]],
    "cyclique+neg": lambda n: [lambda q: q[1:] + q[:1], lambda q: tuple((-v) % 3 for v in q)],
    "renversement+neg": lambda n: [lambda q: q[::-1], lambda q: tuple((-v) % 3 for v in q), lambda q: q[1:] + q[:1]],
}

if __name__ == "__main__":
    n, secs = int(sys.argv[1]), float(sys.argv[2])
    for name, g in GROUPS.items():
        orbs = all_orbits(n, g(n)); rng = random.Random(42); best = []; t0 = time.time(); k = 0
        while time.time() - t0 < secs / 2:
            S = orbit_greedy(list(orbs), rng); k += 1
            if len(S) > len(best): best = S
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            b2, _ = lns(n, best, secs / 2, random.Random(1))
        print(f"n={n} {name:18} {len(orbs)} orbites-caps | glouton orbites {judge(best)} ({k} essais) | +LNS {judge(b2)}", flush=True)

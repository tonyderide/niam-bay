#!/usr/bin/env python3
"""Le rôle du « LLM » : imposer une structure. Je ne cherche plus point par point, mais par ORBITES sous la
permutation des coordonnées (types (c0,c1,c2) = combien de 0, de 1, de 2). Un DFS exact choisit
la meilleure union d'orbites qui reste un cap, puis l'LNS complète."""
import itertools, sys, random
from collections import defaultdict
from capset import judge, third


def orbits(n, shift=(0, 0, 0)):
    by = defaultdict(list)
    for p in itertools.product(range(3), repeat=n):
        by[(p.count(0), p.count(1), p.count(2))].append(p)
    return list(by.values())


def ok_add(S_set, S_list, orb):
    new = set(orb)
    for x in orb:
        for a in S_list:
            if third(a, x) in S_set or third(a, x) in new and third(a, x) != x: return False
    return judge(orb) == len(orb)


def dfs(orbs):
    best = [[]]
    orbs = sorted(orbs, key=len, reverse=True)
    suffix = [0] * (len(orbs) + 1)
    for i in range(len(orbs) - 1, -1, -1): suffix[i] = suffix[i + 1] + len(orbs[i])

    def rec(i, S_list, S_set):
        if len(S_list) > len(best[0]): best[0] = list(S_list)
        if i == len(orbs) or len(S_list) + suffix[i] <= len(best[0]): return
        o = orbs[i]
        if ok_add(S_set, S_list, o):
            rec(i + 1, S_list + o, S_set | set(o))
        rec(i + 1, S_list, S_set)
    rec(0, [], set())
    return best[0]


if __name__ == "__main__":
    n = int(sys.argv[1])
    best = dfs(orbits(n))
    print(f"n={n}: meilleure union d'orbites symétriques = {judge(best)} points")
    from lns import lns
    b2, it = lns(n, best, float(sys.argv[2]) if len(sys.argv) > 2 else 60, random.Random(3))
    print(f"n={n}: après LNS depuis la structure : {judge(b2)}")

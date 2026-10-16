#!/usr/bin/env python3
"""Mini-FunSearch NB, 2026-10-16. Le juge est exact : ensemble de F_3^n sans 3 points alignés.

Dans F_3^n, trois points distincts a, b, c sont alignés  <=>  a + b + c = 0 (mod 3) coordonnée par coordonnée.
La méthode (comme FunSearch) : une fonction `priority(point, n)` ordonne les points, un greedy les ajoute
quand ils ne créent aucune ligne. Le juge note par la taille, et vérifie tout depuis zéro.
Records connus : n=3 -> 9, n=4 -> 20, n=5 -> 45, n=6 -> 112.
"""
import itertools, sys


def third(a, b):
    return tuple((-x - y) % 3 for x, y in zip(a, b))


def judge(S):
    """Vérification exacte, indépendante de la construction."""
    S = list(S); s = set(S)
    if len(s) != len(S): return 0
    for a, b in itertools.combinations(S, 2):
        c = third(a, b)
        if c in s and c != a and c != b:
            return 0
    return len(S)


def greedy(n, priority):
    pts = sorted(itertools.product(range(3), repeat=n), key=lambda p: -priority(p, n))
    S, inS = [], set()
    for x in pts:
        if all(third(a, x) not in inS for a in S):
            S.append(x); inS.add(x)
    return S


# --- heuristiques candidates (c'est moi, le LLM, qui les propose) ---
def p_lex(p, n): return -sum(v * 3 ** i for i, v in enumerate(p))           # ordre lexicographique
def p_no2(p, n): return -p.count(2)                                         # éviter les coordonnées à 2
def p_weight(p, n): return -sum(1 for v in p if v)                          # poids de Hamming faible
def p_mix(p, n): return -(p.count(2) * 10 + sum(1 for v in p if v == 1) % 3) # le 2 pénalisé, parité des 1


CANDIDATES = {"lex": p_lex, "no2": p_no2, "weight": p_weight, "mix": p_mix}

if __name__ == "__main__":
    for n in map(int, sys.argv[1:] or ["3", "4", "5"]):
        for name, f in CANDIDATES.items():
            S = greedy(n, f)
            print(f"n={n} {name:7} -> {judge(S)}")

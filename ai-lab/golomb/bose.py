#!/usr/bin/env python3
"""La BONNE structure pour Golomb : la construction de Bose (1942) dans GF(p²).
g primitif dans GF(p²), B = { i : g^i − g ∈ GF(p) } donne p marques Golomb modulo p²−1.
Puis on choisit la meilleure rotation et le meilleur multiplicateur (u premier à p²−1) pour raccourcir la règle linéaire."""
from math import gcd
from golomb import judge, OPT


def gf2(p):
    n = next(x for x in range(2, p) if pow(x, (p - 1) // 2, p) == p - 1)  # non-résidu : x² = n irréductible
    mul = lambda a, b: ((a[0] * b[0] + n * a[1] * b[1]) % p, (a[0] * b[1] + a[1] * b[0]) % p)
    return mul


def bose(p):
    mul = gf2(p); N = p * p - 1
    for c in range(p):
        for d in range(1, p):
            g, x, seen = (c, d), (1, 0), set()
            for i in range(N):
                seen.add(x); x = mul(x, g)
            if len(seen) == N:  # g est primitif
                B, x = [], (1, 0)
                for i in range(N):
                    if x[1] == g[1]: B.append(i)   # g^i − g a une composante en racine nulle -> ∈ GF(p)
                    x = mul(x, g)
                return sorted(B), N


def best_linear(B, N):
    best = None
    for u in range(1, N):
        if gcd(u, N) != 1: continue
        S = sorted((u * b) % N for b in B)
        for r in range(len(S)):
            lin = sorted((s - S[r]) % N for s in S)
            if judge(lin) is not None and (best is None or lin[-1] < best[-1]): best = lin
    return best


if __name__ == "__main__":
    for p in [5, 7, 11, 13]:
        B, N = bose(p); L = best_linear(B, N)
        print(f"Bose p={p}: {p} marques, longueur {judge(L)} | optimum {OPT.get(p)}")

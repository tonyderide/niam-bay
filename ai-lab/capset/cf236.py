#!/usr/bin/env python3
"""Ender Dragon : le cap de Calderbank-Fishburn (236 points dans F_3^7), reconstruit à partir de sa description.
Structure (Edel & Bierbrauer) : 236 = {0}×C0 ∪ {1}×C1 ∪ {2}×U, où U = les 12 vecteurs de poids 1 de F_3^6
et C0, C1 sont des caps de 112 points dans F_3^6.
Les 1ers coordonnées de 3 points alignés somment à 0 mod 3 : (0,0,0), (1,1,1), (2,2,2) ou (0,1,2).
 - (0,0,0) et (1,1,1) : impossibles car C0 et C1 sont des caps ; (2,2,2) : la somme de 2 poids-1 n'est jamais un poids-1.
 - (0,1,2) : il faut c0 + c1 + u ≠ 0, autrement dit (C0 + C1) ∩ (−U) = ∅.
Je pars de MON cap de 112 (trouvé cette nuit) et je cherche des images affines C0 = A·S + b0, C1 = A·S + b1 qui respectent la condition."""
import itertools, random, sys, time
from capset import judge

S = [tuple(map(int, l)) for l in open("best_n6_quadric.txt").read().split()]
U = [tuple(s if j == i else 0 for j in range(6)) for i in range(6) for s in (1, 2)]
negU = {tuple((-x) % 3 for x in u) for u in U}


def rand_GL(rng, n=6):
    while True:
        A = [[rng.randrange(3) for _ in range(n)] for _ in range(n)]
        M = [r[:] for r in A]; rank = 0
        for c in range(n):  # rang mod 3
            piv = next((r for r in range(rank, n) if M[r][c]), None)
            if piv is None: continue
            M[rank], M[piv] = M[piv], M[rank]; inv = 1 if M[rank][c] == 1 else 2
            M[rank] = [(v * inv) % 3 for v in M[rank]]
            for r in range(n):
                if r != rank and M[r][c]:
                    f = M[r][c]; M[r] = [(a - f * b) % 3 for a, b in zip(M[r], M[rank])]
            rank += 1
        if rank == n: return A


def apply(A, b, P):
    return [tuple((sum(A[i][j] * p[j] for j in range(6)) + b[i]) % 3 for i in range(6)) for p in P]


if __name__ == "__main__":
    rng = random.Random(236); t0 = time.time(); tries = 0; secs = float(sys.argv[1]) if len(sys.argv) > 1 else 200
    while time.time() - t0 < secs:
        tries += 1; A = rand_GL(rng); base = apply(A, (0,) * 6, S)
        sums = {tuple((x + y) % 3 for x, y in zip(c, d)) for c in base for d in base}
        # C0 = base + b0, C1 = base + b1  ->  c0 + c1 = s + (b0+b1) ; on cherche t = b0+b1 tel que (sums + t) ∩ negU = ∅
        for t in itertools.product(range(3), repeat=6):
            if all(tuple((s - t_) % 3 for s, t_ in zip(nu, t)) not in sums for nu in negU):
                C0 = base; C1 = [tuple((x + y) % 3 for x, y in zip(c, t)) for c in base]
                cap = [(0,) + c for c in C0] + [(1,) + c for c in C1] + [(2,) + u for u in U]
                print(f"trouvé après {tries} matrices ({time.time()-t0:.0f}s) : judge = {judge(cap)}")
                if judge(cap) == 236:
                    open("best_n7_236.txt", "w").write("\n".join("".join(map(str, p)) for p in sorted(cap)))
                sys.exit(0)
    print(f"rien en {tries} matrices")

#!/usr/bin/env python3
"""Penser au lieu de chercher. Je pars de la quadrique elliptique de PG(5,3) :
Q(x) = x1·x2 + x3·x4 + x5² + x6²  (x²+y² est anisotrope sur F_3 car −1 n'est pas un carré mod 3).
Les points projectifs de {Q = 0} devraient être (q³+1)(q²−1)/(q−1) = 28·8/2 = 112."""
import itertools
from capset import judge

P = [v for v in itertools.product(range(3), repeat=6) if any(v)]
Q = lambda x: (x[0] * x[1] + x[2] * x[3] + x[4] ** 2 + x[5] ** 2) % 3


def proj(v):  # représentant normalisé : 1ʳᵉ coordonnée non nulle = 1
    i = next(k for k, a in enumerate(v) if a)
    return v if v[i] == 1 else tuple((2 * a) % 3 for a in v)


E = sorted({proj(v) for v in P if Q(v) == 0})
print("points projectifs de la quadrique elliptique :", len(E))
# vecteurs affines non nuls de la quadrique (= ±E) : cap affine dans AG(6,3) ?
V = [v for v in P if Q(v) == 0]
print("vecteurs non nuls {Q=0} :", len(V), "| est un cap affine ?", judge(V) == len(V))
for c in (1, 2):
    W = [v for v in itertools.product(range(3), repeat=6) if Q(v) == c]
    print(f"niveau Q={c} : {len(W)} vecteurs | cap ? {judge(W) == len(W)}")


# --- Le cap de Hill : 56 points de E sans 3 points alignés (projectivement) ---
import random, time


def line_pts(p, q):  # les 2 autres points de la droite projective pq (4 points sur F_3)
    return {proj(tuple((a + b) % 3 for a, b in zip(p, q))), proj(tuple((a + 2 * b) % 3 for a, b in zip(p, q)))}


def proj_cap_ok(x, S, inS):
    return all(not (line_pts(a, x) & inS) for a in S)


def search_hill(secs, rng):
    best = []; t0 = time.time()
    cur = []
    while time.time() - t0 < secs:
        keep = rng.sample(cur, max(0, len(cur) - rng.randint(2, 6))) if cur else []
        S, inS = list(keep), set(keep); pool = E[:]; rng.shuffle(pool)
        for x in pool:
            if x not in inS and proj_cap_ok(x, S, inS): S.append(x); inS.add(x)
        if len(S) >= len(cur): cur = S
        if len(cur) > len(best): best = list(cur)
        if len(best) >= 56: break
    return best


if __name__ == "__main__":
    H = search_hill(120, random.Random(56))
    print("plus grand cap projectif trouvé dans E :", len(H))
    A = sorted(set(H) | {tuple((-a) % 3 for a in h) for h in H})
    print("±H dans AG(6,3) :", len(A), "| cap affine ?", judge(A) == len(A))
    open("hill_H.txt", "w").write("\n".join("".join(map(str, h)) for h in H))

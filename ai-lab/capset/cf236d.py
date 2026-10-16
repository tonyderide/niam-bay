#!/usr/bin/env python3
"""4e essai, avec la bonne condition : C0 = mon cap de 112 (sous une transformation linéaire aléatoire),
X = −C0, F = points de F_3^6 qui ne sont PAS à distance de Hamming exactement 1 d'un point de X.
On cherche un cap C1 de 112 points entièrement contenu dans F (glouton + LNS restreint à F), en parallèle."""
import itertools, random, sys, time
from multiprocessing import Pool
from capset import judge, third
from cf236 import S, U, rand_GL, apply

PTS = list(itertools.product(range(3), repeat=6))


def nb1(p):
    return [tuple((p[j] + d) % 3 if j == i else p[j] for j in range(6)) for i in range(6) for d in (1, 2)]


def fill(Sx, pool, rng):
    Sx = list(Sx); inS = set(Sx); pool = list(pool); rng.shuffle(pool)
    for x in pool:
        if x not in inS and all(third(a, x) not in inS for a in Sx): Sx.append(x); inS.add(x)
    return Sx


def run(seed):
    rng = random.Random(seed); t0 = time.time(); best = (0, None, None)
    while time.time() - t0 < 240:
        C0 = apply(rand_GL(rng), tuple(rng.randrange(3) for _ in range(6)), S)
        X = {tuple((-x) % 3 for x in c) for c in C0}
        bad = {n for x in X for n in nb1(x)}
        F = [p for p in PTS if p not in bad]
        if len(F) < 112: continue
        cur = fill([], F, rng); t1 = time.time()
        while time.time() - t1 < 20:
            k = rng.randint(2, max(3, len(cur) // 6))
            new = fill(rng.sample(cur, len(cur) - k), F, rng)
            if len(new) >= len(cur): cur = new
        if len(cur) > best[0]: best = (len(cur), C0, cur)
        if best[0] >= 112: break
    return best


if __name__ == "__main__":
    with Pool(8) as p:
        res = sorted(p.map(run, range(8)), key=lambda r: -r[0])
    print("meilleur C1 dans F :", [r[0] for r in res])
    n, C0, C1 = res[0]
    if C1:
        cap = [(0,) + c for c in C0] + [(1,) + c for c in C1] + [(2,) + u for u in U]
        print("cap en dimension 7 : judge =", judge(cap))
        if judge(cap) > 224:
            open(f"best_n7_{judge(cap)}.txt", "w").write("\n".join("".join(map(str, q)) for q in sorted(cap)))

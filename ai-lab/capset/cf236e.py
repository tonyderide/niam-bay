#!/usr/bin/env python3
"""5e essai : recherche JOINTE de C0 et C1 en dimension 7. Les 12 points (2,U) sont fixés, et la LNS ne touche que
les points de préfixe 0 ou 1. On part du produit 112×{0,1} (224), dont on retire les points en conflit avec (2,U),
puis on répare avec le juge exact."""
import itertools, random, sys, time
from multiprocessing import Pool
from capset import judge, third
from cf236 import S, U, rand_GL, apply

FIX = [(2,) + u for u in U]
POOL = [p for p in itertools.product(range(3), repeat=7) if p[0] in (0, 1)]


def fill(cur, rng):
    Sx = FIX + [p for p in cur]; inS = set(Sx); pool = POOL[:]; rng.shuffle(pool)
    for x in pool:
        if x not in inS and all(third(a, x) not in inS for a in Sx): Sx.append(x); inS.add(x)
    return [p for p in Sx if p[0] != 2]


def repair(pts):
    """Retire les points de préfixe 0/1 qui forment une ligne avec 2 autres points (dont les fixes)."""
    cur = list(pts)
    while True:
        s = set(FIX + cur); bad = None
        for a, b in itertools.combinations(FIX + cur, 2):
            c = third(a, b)
            if c in s and c != a and c != b:
                bad = next(p for p in (a, b, c) if p[0] != 2); break
        if bad is None: return cur
        cur.remove(bad)


def run(seed):
    rng = random.Random(seed); t0 = time.time()
    C = apply(rand_GL(rng), tuple(rng.randrange(3) for _ in range(6)), S)
    cur = repair([(0,) + c for c in C] + [(1,) + c for c in C])
    best = list(cur)
    while time.time() - t0 < 250:
        k = rng.randint(2, max(3, len(cur) // 8))
        new = fill(rng.sample(cur, len(cur) - k), rng)
        if len(new) >= len(cur):
            cur = new
            if len(cur) > len(best): best = list(cur)
    return len(best) + 12, best


if __name__ == "__main__":
    with Pool(8) as p:
        res = sorted(p.map(run, range(40, 48)), key=lambda r: -r[0])
    print("tailles totales (avec les 12 fixes) :", [r[0] for r in res])
    cap = FIX + res[0][1]; j = judge(cap); print("judge =", j)
    if j > 224:
        open(f"best_n7_{j}.txt", "w").write("\n".join("".join(map(str, q)) for q in sorted(cap)))

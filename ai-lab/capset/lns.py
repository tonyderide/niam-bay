#!/usr/bin/env python3
"""Large neighbourhood search : on retire k points au hasard, on re-remplit en glouton aléatoire,
et on accepte si la taille ne baisse pas (pour pouvoir dériver sur les plateaux)."""
import itertools, random, sys, time
from capset import judge, third
from search import random_greedy, product


def refill(n, S, rng):
    inS = set(S); S = list(S)
    pts = [p for p in itertools.product(range(3), repeat=n) if p not in inS]; rng.shuffle(pts)
    for x in pts:
        if all(third(a, x) not in inS for a in S):
            S.append(x); inS.add(x)
    return S


def lns(n, start, seconds, rng):
    cur = best = list(start); t0 = time.time(); it = 0
    while time.time() - t0 < seconds:
        it += 1
        k = rng.randint(2, max(3, len(cur) // 5))
        keep = rng.sample(cur, len(cur) - k)
        new = refill(n, keep, rng)
        if len(new) >= len(cur):
            cur = new
            if len(cur) > len(best):
                best = cur; print(f"  {time.time()-t0:5.0f}s it={it}: {len(best)}", flush=True)
    return best, it


if __name__ == "__main__":
    n, secs = int(sys.argv[1]), float(sys.argv[2])
    rng = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 7)
    start = random_greedy(n, rng)
    print(f"n={n} départ {len(start)}")
    best, it = lns(n, start, secs, rng)
    print(f"n={n} meilleur {judge(best)} en {it} itérations")
    open(f"best_n{n}.txt", "w").write("\n".join("".join(map(str, p)) for p in sorted(best)))

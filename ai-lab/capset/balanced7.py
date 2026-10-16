#!/usr/bin/env python3
"""J'agis sur la conjecture : en dimension 7, je force des sections équilibrées. Point de départ : la LNS en
dimension 7 avec un plafond par section (chaque hyperplan x0 = 0, 1, 2 limité à MAX points), pour empêcher le
112+112+0. Ensuite je relâche le plafond progressivement."""
import itertools, random, sys, time
from multiprocessing import Pool
from capset import judge, third

PTS = list(itertools.product(range(3), repeat=7))


def fill(cur, rng, cap_per):
    S = list(cur); inS = set(S); cnt = [sum(1 for p in S if p[0] == k) for k in range(3)]
    pool = PTS[:]; rng.shuffle(pool)
    for x in pool:
        if x in inS or cnt[x[0]] >= cap_per: continue
        if all(third(a, x) not in inS for a in S): S.append(x); inS.add(x); cnt[x[0]] += 1
    return S


def run(seed):
    rng = random.Random(seed); t0 = time.time(); best = []
    for cap_per in (90, 96, 100, 104, 112):
        cur = fill(best, rng, cap_per) if best else fill([], rng, cap_per); t1 = time.time()
        while time.time() - t1 < 48:
            k = rng.randint(2, max(3, len(cur) // 10))
            new = fill(rng.sample(cur, len(cur) - k), rng, cap_per)
            if len(new) >= len(cur): cur = new
        if len(cur) > len(best): best = cur
    secs = [sum(1 for p in best if p[0] == k) for k in range(3)]
    return len(best), secs, best


if __name__ == "__main__":
    with Pool(8) as p:
        res = sorted(p.map(run, range(300, 308)), key=lambda r: -r[0])
    for n, secs, _ in res: print(n, secs)
    b = res[0][2]; print("judge:", judge(b))
    if judge(b) > 224: open(f"best_n7_{judge(b)}.txt", "w").write("\n".join("".join(map(str, q)) for q in sorted(b)))

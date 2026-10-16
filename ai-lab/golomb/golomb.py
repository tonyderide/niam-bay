#!/usr/bin/env python3
"""2e étagère, même méthode : règles de Golomb (toutes les différences entre marques sont distinctes).
On compare le hasard, une construction algébrique (Erdős–Turán : a_k = 2pk + (k² mod p)) et l'optimum connu."""
import random, sys, time

OPT = {5: 11, 6: 17, 7: 25, 8: 34, 9: 44, 10: 55, 11: 72, 12: 85, 13: 106}


def judge(marks):
    m = sorted(set(marks)); d = set()
    for i in range(len(m)):
        for j in range(i):
            x = m[i] - m[j]
            if x in d: return None
            d.add(x)
    return m[-1] - m[0]


def random_greedy(k, rng, L):
    m, d = [0], set()
    cand = list(range(1, L + 1)); rng.shuffle(cand); cand.sort(key=lambda x: x + rng.random() * L * 0.3)
    for x in cand:
        nd = {abs(x - y) for y in m}
        if len(nd) == len(m) and not (nd & d):
            m.append(x); d |= nd
            if len(m) == k: return m
    return None


def erdos_turan(k):
    p = next(q for q in range(k, 10 * k) if all(q % r for r in range(2, int(q ** .5) + 1)))
    m = sorted(2 * p * i + (i * i) % p for i in range(k))
    return [x - m[0] for x in m]


if __name__ == "__main__":
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 5; rng = random.Random(1)
    for k in range(5, 14):
        best = None; t0 = time.time()
        while time.time() - t0 < secs:
            for L in range(OPT[k], 3 * OPT[k]):
                m = random_greedy(k, rng, L)
                if m and (best is None or judge(m) < judge(best)): best = m
                if m: break
        et = erdos_turan(k)
        print(f"k={k:2} hasard {judge(best):4} | Erdős–Turán {judge(et):4} | optimum {OPT[k]}")

#!/usr/bin/env python3
"""2e idée : C1 = −C0. Alors c0 + c1 = c0 − c0', et la condition (C0+C1) ∩ (−U) = ∅ revient à
« aucun couple de points de C0 n'est à distance de Hamming 1 ». Je cherche une image linéaire de mon cap de 112
dont tous les points sont à distance de Hamming ≥ 2 deux à deux."""
import random, sys, time
from capset import judge
from cf236 import S, U, rand_GL, apply


def min_dist_ok(C):
    s = set(C)
    for c in C:
        for i in range(6):
            for d in (1, 2):
                v = list(c); v[i] = (v[i] + d) % 3
                if tuple(v) in s: return False
    return True


if __name__ == "__main__":
    rng = random.Random(7); t0 = time.time(); tries = 0; secs = float(sys.argv[1])
    while time.time() - t0 < secs:
        tries += 1; C0 = apply(rand_GL(rng), (0,) * 6, S)
        if min_dist_ok(C0):
            C1 = [tuple((-x) % 3 for x in c) for c in C0]
            cap = [(0,) + c for c in C0] + [(1,) + c for c in C1] + [(2,) + u for u in U]
            j = judge(cap); print(f"image à distance ≥ 2 trouvée après {tries} essais ({time.time()-t0:.0f}s) : judge = {j}")
            if j == 236:
                open("best_n7_236.txt", "w").write("\n".join("".join(map(str, p)) for p in sorted(cap)))
                sys.exit(0)
    print(f"rien en {tries} essais")

#!/usr/bin/env python3
"""Le 236 à partir de la vraie géométrie. E = quadrique elliptique (112 points projectifs), H = cap de Hill (56),
H' = E \\ H (les 56 autres points). Candidats pour C0 et C1 : ±H, ±H', et leurs translatés par t ∈ F_3^6.
Condition : (C0 + C1) ∩ (−U) = ∅. On compte les conflits pour chaque combinaison, et le juge exact tranche."""
import itertools
from collections import Counter
from capset import judge
from hill import E, proj
from cf236 import U

H = [tuple(map(int, l)) for l in open("hill_H.txt").read().split()]
Hp = sorted(set(E) - set(H))
pm = lambda X: sorted(set(X) | {tuple((-a) % 3 for a in x) for x in X})
A, Ap = pm(H), pm(Hp)
print("±H' est un cap affine ?", judge(Ap) == len(Ap), len(Ap))
negU = [tuple((-x) % 3 for x in u) for u in U]
best = (10 ** 9, None)
for name0, C0 in (("±H", A), ("±H'", Ap)):
    count = Counter(tuple((w[i] - c[i]) % 3 for i in range(6)) for w in negU for c in C0)
    for name1, B in (("±H", A), ("±H'", Ap)):
        for t in itertools.product(range(3), repeat=6):
            C1 = [tuple((x + y) % 3 for x, y in zip(b, t)) for b in B]
            k = sum(count[c] for c in C1)
            if k < best[0]: best = (k, (name0, name1, t, C0, C1))
k, (n0, n1, t, C0, C1) = best
print(f"meilleure combinaison : C0={n0}, C1={n1}+{t} -> {k} conflits")
cap = [(0,) + c for c in C0] + [(1,) + c for c in C1] + [(2,) + u for u in U]
print("judge =", judge(cap))
if judge(cap) == 236:
    open("best_n7_236.txt", "w").write("\n".join("".join(map(str, q)) for q in sorted(cap)))

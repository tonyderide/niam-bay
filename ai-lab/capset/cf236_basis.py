#!/usr/bin/env python3
"""Le déclic : U = « vecteurs de poids 1 », mais de poids 1 DANS QUELLE BASE ? Le cap de Hill vit dans les
coordonnées de la quadrique, pas forcément dans la base canonique. Le bloc de préfixe 2 peut donc être
W = {±a_1, …, ±a_6} pour n'importe quelle base (a_i). Il n'y a alors plus qu'UNE condition :
les ±a_i doivent éviter −(C0 + C1). On cherche donc une base dans le complémentaire de la somme C0 + C1."""
import itertools, random
from capset import judge
from hill import E
H = [tuple(map(int, l)) for l in open("hill_H.txt").read().split()]
Hp = sorted(set(E) - set(H))
pm = lambda X: sorted(set(X) | {tuple((-a) % 3 for a in x) for x in X})
A, Ap = pm(H), pm(Hp)


def rank3(vs):
    M = [list(v) for v in vs]; r = 0
    for c in range(6):
        piv = next((i for i in range(r, len(M)) if M[i][c]), None)
        if piv is None: continue
        M[r], M[piv] = M[piv], M[r]; inv = 1 if M[r][c] == 1 else 2; M[r] = [(x * inv) % 3 for x in M[r]]
        for i in range(len(M)):
            if i != r and M[i][c]: f = M[i][c]; M[i] = [(a - f * b) % 3 for a, b in zip(M[i], M[r])]
        r += 1
    return r


ZERO = (0,) * 6
for n0, C0 in (("±H", A), ("±H'", Ap)):
    for n1, B in (("±H", A), ("±H'", Ap)):
        for t in itertools.product(range(3), repeat=6):
            C1 = [tuple((x + y) % 3 for x, y in zip(b, t)) for b in B]
            S = {tuple((a + b) % 3 for a, b in zip(c0, c1)) for c0 in C0 for c1 in C1}
            free = [v for v in itertools.product(range(3), repeat=6) if v != ZERO and tuple((-x) % 3 for x in v) not in S]
            if len(free) >= 6 and rank3(free) == 6:
                # extraire une base (glouton)
                basis = []
                for v in free:
                    if rank3(basis + [v]) > len(basis): basis.append(v)
                    if len(basis) == 6: break
                W = sorted({b for b in basis} | {tuple((-x) % 3 for x in b) for b in basis})
                cap = [(0,) + c for c in C0] + [(1,) + c for c in C1] + [(2,) + w for w in W]
                j = judge(cap)
                print(f"C0={n0} C1={n1}+{t} : |libres|={len(free)}, base trouvée -> judge = {j}")
                if j == 236:
                    open("best_n7_236.txt", "w").write("\n".join("".join(map(str, q)) for q in sorted(cap)))
                    raise SystemExit(0)
print("aucune combinaison")

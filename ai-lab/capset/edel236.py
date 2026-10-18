"""Cap de 236 points dans F_3^7, par la collection extensible (A0, A1, A2) de F_3^6 décrite dans arXiv 2209.10045 (lemme 2.14, construction d'Edel).
C = A1×{1} ∪ A2×{2} ∪ A0×{0}. Juge exact : aucune paire x≠y avec -(x+y) dans C (et distinct de x, y)."""
import itertools

BLOCKS = ["123", "124", "135", "146", "156", "236", "245", "256", "345", "346"]  # design (6,3,2) du papier
supp = lambda b: tuple(int(c) - 1 for c in b)
D_supp = {supp(b) for b in BLOCKS}
all3 = set(itertools.combinations(range(6), 3))
Dp_supp = all3 - D_supp


def vecs(supports):
    out = []
    for s in supports:
        for vals in itertools.product((1, 2), repeat=3):
            v = [0] * 6
            for i, x in zip(s, vals):
                v[i] = x
            out.append(tuple(v))
    return out


D, Dp = vecs(D_supp), vecs(Dp_supp)
R = [v for v in itertools.product((1, 2), repeat=6) if v.count(1) % 2 == 0]
A0 = [tuple(x if j == i else 0 for j in range(6)) for i in range(6) for x in (1, 2)]
A1, A2 = D + R, Dp + R
C = [a + (1,) for a in A1] + [a + (2,) for a in A2] + [a + (0,) for a in A0]
S = set(C)
assert len(S) == len(C)
neg = lambda v: tuple((-x) % 3 for x in v)
bad = 0
for x, y in itertools.combinations(C, 2):
    z = neg(tuple((a + b) % 3 for a, b in zip(x, y)))
    if z in S and z != x and z != y:
        bad += 1
print(f"|A0|={len(A0)} |A1|={len(A1)} |A2|={len(A2)} → |C| = {len(C)} dans F_3^7 ; triplets alignés : {bad}")
if bad == 0:
    open("cap7_236.txt", "w").write("\n".join("".join(map(str, v)) for v in C) + "\n")
    print("CAP VALIDE de taille", len(C), "→ cap7_236.txt")

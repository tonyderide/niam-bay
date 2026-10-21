"""Règles de Golomb optimales : n marques, toutes les distances différentes, longueur minimale.
Recherche en profondeur avec ensemble de distances en bits + bornes. Juge exact : vérifie les distances et compare aux valeurs prouvées."""
import sys, time
PROUVE = {2: 1, 3: 3, 4: 6, 5: 11, 6: 17, 7: 25, 8: 34, 9: 44, 10: 55, 11: 72, 12: 85, 13: 106, 14: 127}

def juge(r):
    d = [b - a for i, a in enumerate(r) for b in r[i + 1:]]
    return len(d) == len(set(d))

def cherche(n, L):
    """Existe-t-il une règle de n marques de longueur exactement L ? (0 et L sont des marques)"""
    marks = [0]
    def rec(dist):
        k = len(marks)
        if k == n - 1:
            # dernière marque = L
            nd = 0
            for m in marks:
                x = L - m
                if (dist >> x) & 1 or (nd >> x) & 1: return False
                nd |= 1 << x
            marks.append(L); return True
        reste = n - k                       # marques encore à placer, L compris
        bas = marks[-1] + 1
        haut = L - PROUVE.get(reste - 1, 0) if reste - 1 in PROUVE else L - 1   # il faut encore une sous-règle de reste marques
        for p in range(bas, haut + 1):
            nd = 0; ok = True
            for m in marks:
                x = p - m
                if (dist >> x) & 1 or (nd >> x) & 1: ok = False; break
                nd |= 1 << x
            if not ok: continue
            if marks[1:2] and p > L // 2 + marks[1] and k == 1: break   # symétrie : la 2e marque dans la 1re moitié
            marks.append(p)
            if rec(dist | nd): return True
            marks.pop()
        return False
    return marks if rec(0) else None

for n in range(2, int(sys.argv[1]) + 1 if len(sys.argv) > 1 else 11):
    t = time.time(); L = PROUVE.get(n - 1, 0) + 1
    while True:
        r = cherche(n, L)
        if r: break
        L += 1
    print(f"n={n:2}  longueur {L:3}  {r}  juge {'OK' if juge(r) else 'FAUX'}  prouvé {PROUVE.get(n)} {'✓' if PROUVE.get(n) == L else '✗'}  ({time.time()-t:.1f} s)", flush=True)

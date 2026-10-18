"""Analyse (protocole 6590136). Pas de nom de compte publié dans le résumé : adresses tronquées à 6 caractères."""
import json, random, bisect, itertools, collections

D = json.load(open("data.json"))


def bursts(evts):
    out = collections.defaultdict(list)
    for e in sorted(evts, key=lambda e: e["t"]):
        side = "L" if "Long" in e["dir"] else "S"
        k = (e["coin"], side)
        if not out[k] or e["t"] - out[k][-1] > 60000:
            out[k].append(e["t"])
    return out


B = {a: bursts(e) for a, e in D.items()}
allt = [e["t"] for ev in D.values() for e in ev]
T0, T1 = min(allt), max(allt); MID = (T0 + T1) / 2; SPAN = T1 - T0


def follows(ta, tb, lo=1000, hi=120000):
    n = 0
    for t in ta:
        i = bisect.bisect_left(tb, t + lo)
        if i < len(tb) and tb[i] <= t + hi:
            n += 1
    return n


def test(ta, tb, rnd, n=1000):
    obs = follows(ta, tb); back = follows(tb, ta)
    if obs == 0:
        return obs, back, 1.0
    ge = 0
    for _ in range(n):
        d = rnd.uniform(3600e3, 24 * 3600e3)
        sh = sorted(((t - T0 + d) % SPAN) + T0 for t in tb)
        ge += follows(ta, sh) >= obs
    return obs, back, (ge + 1) / (n + 1)


rnd = random.Random(1018)
pairs = []
for a, b in itertools.permutations(B, 2):
    for k in set(B[a]) & set(B[b]):
        pairs.append((a, b, k))
alpha = 0.05 / max(1, len(pairs))
print(f"{len(B)} comptes, {len(pairs)} paires orientées (même coin, même sens) ; seuil Bonferroni p < {alpha:.2e}")
found = []
for a, b, k in pairs:
    ta1 = [t for t in B[a][k] if t < MID]; tb1 = [t for t in B[b][k] if t < MID]
    o, bk, p = test(ta1, tb1, rnd, n=200)
    if o >= 10 and o >= 3 * max(1, bk) and p <= 1 / 201:  # pré-filtre ; le vrai p est recalculé avec 1000 tirages ci-dessous
        o, bk, p = test(ta1, tb1, rnd, n=1000 if alpha > 1e-3 else 20000)
        if p < alpha:
            ta2 = [t for t in B[a][k] if t >= MID]; tb2 = [t for t in B[b][k] if t >= MID]
            o2, bk2, p2 = test(ta2, tb2, rnd, n=1000)
            ok = o2 >= 3 * max(1, bk2) and p2 < 0.05
            found.append(dict(A=a[:8], B=b[:8], coin=k[0], side=k[1], decouverte=(o, bk, round(p, 5)), confirmation=(o2, bk2, round(p2, 4)), copie=ok))
for f in found:
    print(f)
print("copies confirmées :", sum(f["copie"] for f in found), "sur", len(found), "candidates en découverte")
json.dump(found, open("resultats.json", "w"), indent=1)

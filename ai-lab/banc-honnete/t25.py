"""PREREG-23 : un pic de volume vendeur annonce-t-il un rebond ? Voir PREREG-23-volume-rebond.md.
Usage : python3 t25.py [fichier_ticks.jsonl]   (défaut : le mois jugé ; la réplication passe son fichier)."""
import bisect, json, os, random, sys
TICKS = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/projets/tonyderide/darwin/.worktrees/honnete/data/ticks/XBTUSD.jsonl")
COUT = 2 * (0.0005 + 0.0002)          # taker + glissement, aller-retour
HS = (15, 60); REFROID = {15: 30, 60: 60}; NT = 2000; HISTO = 1440; K = 20


def bougies():
    B = {}
    for l in open(TICKS):
        d = json.loads(l); m = int(d["timestamp"] // 60); p = d["price"]; v = d["volume"]; s = d["side"] == "s"
        b = B.get(m)
        if b is None: B[m] = b = [p, p, p, p, 0.0, 0.0, None, None]
        b[1] = max(b[1], p); b[2] = min(b[2], p); b[3] = p; b[4] += v
        if s:
            b[5] += v
            if b[7] is None: b[7] = p                  # premier trade vendeur de la minute
        elif b[6] is None: b[6] = p                    # premier trade acheteur de la minute
    m0, m1 = min(B), max(B) - 1                        # dernière minute exclue (incomplète)
    O, C, V, VV, FB, FS = [], [], [], [], [], []; prev = B[m0][0]
    for m in range(m0, m1 + 1):
        b = B.get(m) or [prev, prev, prev, prev, 0.0, 0.0, None, None]
        O.append(b[0]); C.append(b[3]); V.append(b[4]); VV.append(b[5]); FB.append(b[6]); FS.append(b[7]); prev = b[3]
    return m0, O, C, V, VV, FB, FS


def prochain(X):
    """P[k] = premier X[j] non vide pour j ≥ k."""
    P = [None] * (len(X) + 1)
    for k in range(len(X) - 1, -1, -1): P[k] = X[k] if X[k] is not None else P[k + 1]
    return P


def centile_glissant(V, q):
    S = [None] * len(V); w = sorted(V[:HISTO])
    for t in range(HISTO, len(V)):
        S[t] = w[min(len(w) - 1, int(q * len(w)))]
        w.pop(bisect.bisect_left(w, V[t - HISTO])); bisect.insort(w, V[t])
    return S


def main():
    m0, O, C, V, VV, FB, FS = bougies(); n = len(C); fin = n - max(HS) - 2
    PB, PS = prochain(FB), prochain(FS)

    def gain(t, h, sens=1):
        """long : 1er acheteur après clôture de t → 1er vendeur après clôture de t+h ; short : l'inverse."""
        e, s = (PB[t + 1], PS[t + h + 1]) if sens > 0 else (PS[t + 1], PB[t + h + 1])
        if e is None or s is None: return None
        return sens * (s / e - 1) - COUT

    print(f"{TICKS}\n{n} minutes ({n/1440:.1f} jours), minutes sans transaction {sum(v == 0 for v in V)}", flush=True)
    S99 = centile_glissant(V, 0.99); S90 = centile_glissant(V, 0.90)
    r = [C[t] / O[t] - 1 for t in range(n)]
    vol60 = [None] * n
    for t in range(60, n):
        x = r[t - 60:t]; mu = sum(x) / 60; vol60[t] = (sum((a - mu) ** 2 for a in x) / 60) ** .5
    heure = lambda t: ((m0 + t) // 60) % 24
    parh = {}
    for t in range(HISTO, fin): parh.setdefault(heure(t), []).append(t)

    def evenements(cote, h, refroid=True):
        ev = []; dernier = -10 ** 9
        for t in range(HISTO, fin):
            if V[t] <= 0 or V[t] < S99[t]: continue
            part = VV[t] / V[t] if cote == "s" else 1 - VV[t] / V[t]
            bouge = C[t] < O[t] if cote == "s" else C[t] > O[t]
            if part >= 0.60 and bouge and (not refroid or t - dernier >= REFROID[h]): ev.append(t); dernier = t
        return [t for t in ev if gain(t, h) is not None]

    calmes = [t for t in range(HISTO, fin) if C[t] < O[t] and V[t] < S90[t] and vol60[t]]
    sr = (sum(r[t] ** 2 for t in calmes) / len(calmes)) ** .5; sv = (sum(vol60[t] ** 2 for t in calmes) / len(calmes)) ** .5

    def voisins(t):
        c = [u for u in calmes if abs(r[u] - r[t]) <= 0.25 * abs(r[t]) and abs(vol60[u] - vol60[t]) <= 0.25 * vol60[t]]
        if len(c) < K: return None
        c.sort(key=lambda u: ((r[u] - r[t]) / sr) ** 2 + ((vol60[u] - vol60[t]) / sv) ** 2); return c[:K]

    def holm(ps):
        o = sorted(range(len(ps)), key=lambda i: 2 if ps[i] is None else ps[i]); ok = [False] * len(ps)
        for k, i in enumerate(o):
            if ps[i] is not None and ps[i] <= 0.05 / (len(ps) - k): ok[i] = True
            else: break
        return ok

    rnd = random.Random(23); res = {}
    for h in HS:
        ev = evenements("s", h); mi = HISTO + (fin - HISTO) // 2
        G = [gain(t, h) for t in ev]; g = sum(G) / max(1, len(G))
        T1 = []
        for _ in range(NT):
            pris = set(); tot = 0.0
            for t in ev:
                while True:
                    u = rnd.choice(parh[heure(t)])
                    if u not in pris and gain(u, h) is not None: break
                pris.add(u); tot += gain(u, h)
            T1.append(tot / max(1, len(ev)))
        V2 = {t: voisins(t) for t in ev}; ev2 = [t for t in ev if V2[t]]; frac_ne = 1 - len(ev2) / max(1, len(ev))
        g2 = sum(gain(t, h) for t in ev2) / max(1, len(ev2)); T2 = []
        if frac_ne <= 0.30 and ev2:
            for _ in range(NT):
                tot = 0.0
                for t in ev2:
                    vs = [u for u in V2[t] if gain(u, h) is not None]; tot += gain(rnd.choice(vs), h)
                T2.append(tot / len(ev2))
        p1 = (1 + sum(x >= g for x in T1)) / (NT + 1); p2 = (1 + sum(x >= g2 for x in T2)) / (NT + 1) if T2 else None
        a = [gain(t, h) for t in ev if t < mi]; b = [gain(t, h) for t in ev if t >= mi]
        T1.sort(); T2.sort(); m1 = T1[NT // 2]; m2 = T2[NT // 2] if T2 else None
        res[h] = (g, p1, p2, a, b)
        print(f"H={h:2} min : {len(ev)} événements | gain net moyen {100*g:+.3f} % | T1 (même heure) méd {100*m1:+.3f} % p={p1:.4f} | "
              + (f"T2 ({len(ev2)} év. évaluables) gain {100*g2:+.3f} % méd {100*m2:+.3f} % p={p2:.4f}" if T2 else f"T2 NON ÉVALUABLE ({frac_ne:.0%} d'événements sans 20 voisins)")
              + f" | moitiés {100*sum(a)/max(1,len(a)):+.3f} % ({len(a)}) / {100*sum(b)/max(1,len(b)):+.3f} % ({len(b)})", flush=True)
        print(f"   signes pour la réplication : gain − méd T1 {'+' if g > m1 else '−'}" + (f" ; gain − méd T2 {'+' if g2 > m2 else '−'}" if T2 else ""))
    ok1 = holm([res[h][1] for h in HS]); ok2 = holm([res[h][2] for h in HS])
    for i, h in enumerate(HS):
        g, p1, p2, a, b = res[h]
        v = ("CONFIRMÉ sur ce mois (lié au volume)" if ok1[i] and ok2[i] else
             "rebond après chute, propre au volume NON ÉVALUABLE" if ok1[i] and p2 is None else
             "rebond après chute, pas propre au volume" if ok1[i] else "NON DÉMONTRÉ")
        ex = ok1[i] and ok2[i] and g > 0 and sum(a) > 0 and sum(b) > 0
        print(f"VERDICT H={h} : {v} | exploitable sur ce mois : {'oui' if ex else 'non'} (réplication à juger à part)")

    print("\n— infos sans verdict —")
    for h in HS:
        eva = [t for t in evenements("b", h) if gain(t, h, -1) is not None]
        print(f"pic acheteur → short H={h} : {len(eva)} év., gain net moyen {100*sum(gain(t, h, -1) for t in eva)/max(1,len(eva)):+.3f} %")
    for h in HS:
        ev = evenements("s", h); ab = sum(abs(C[t + h] / O[t + 1] - 1) for t in ev) / max(1, len(ev))
        sm = rnd.sample(range(HISTO, fin), 5000); ab1 = sum(abs(C[t + h] / O[t + 1] - 1) for t in sm) / 5000
        print(f"|mouvement| H={h} après pic vendeur {100*ab:.3f} % contre {100*ab1:.3f} % au hasard")
        e3 = evenements("s", h, refroid=False)
        print(f"sans refroidissement H={h} : {len(e3)} év., gain net moyen {100*sum(gain(t, h) for t in e3)/max(1,len(e3)):+.3f} %")
    hv, hr = [], []
    for k in range(0, n - 121, 60): hv.append(sum(V[k:k + 60])); hr.append(C[k + 119] / O[k + 60] - 1)
    def corr(x, y):
        mx, my = sum(x) / len(x), sum(y) / len(y); sx = sum((a - mx) ** 2 for a in x) ** .5; sy = sum((b - my) ** 2 for b in y) ** .5
        return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)
    print(f"corrélation volume de l'heure → rendement heure suivante : signé {corr(hv, hr):+.3f} | absolu {corr(hv, [abs(x) for x in hr]):+.3f} ({len(hv)} heures)")


if __name__ == "__main__":
    main()

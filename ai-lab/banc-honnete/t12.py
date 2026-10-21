"""PREREG-12 : grille 0,6 % x 5 niveaux, allumée quand la volatilité prévue est haute. Voir PREREG-12-grille-volatilite.md."""
import calendar, math, pickle, random, time

ts = lambda d: calendar.timegm(time.strptime(d, "%Y-%m-%d"))
T, C = pickle.load(open("/home/tony/.cache/banc-honnete/PF_XBTUSD_15m_2023-11-01.pkl", "rb"))
O, H, Lo, Cl = [c[0] for c in C], [c[1] for c in C], [c[2] for c in C], [c[3] for c in C]
ECART, N, MAKER, TAKER = 0.006, 5, 0.0002, 0.0005

# prévision de volatilité connue AVANT la bougie i
v = [0.0] * len(Cl); e = 0.002
for i in range(1, len(Cl)):
    v[i] = e; e = 0.94 * e + 0.06 * abs(math.log(Cl[i] / Cl[i - 1]))


def grille(debut, fin, masque):
    """Rendement net total (fraction du capital) de la grille sur [debut, fin), allumée là où masque[i] est vrai."""
    pnl = 0.0; actif = False
    for i in range(debut, fin):
        if masque[i] and not actif:                     # allumage au prix d'ouverture
            c = O[i]; niv = [c * (1 + ECART * j) for j in range(-N, N + 1)]
            # état par niveau j (hors centre) : "attente" (ordre d'ouverture posé) ou "plein" (position ouverte, ordre de sortie posé)
            etat = {j: "attente" for j in range(-N, N + 1) if j != 0}; prix_ouv = {}; actif = True
        if not actif: continue
        pose = dict(etat)                               # ordres tels qu'ils étaient au début de la bougie
        for j, s in pose.items():
            p_ouv = niv[j + N]
            if j < 0:                                   # niveau acheteur
                if s == "attente" and Lo[i] <= p_ouv: etat[j] = "plein"; prix_ouv[j] = p_ouv; pnl -= MAKER / (2 * N)
                elif s == "plein" and H[i] >= niv[j + N + 1]:
                    pnl += (niv[j + N + 1] / prix_ouv[j] - 1 - MAKER) / (2 * N); etat[j] = "attente"
            else:                                       # niveau vendeur (à découvert)
                if s == "attente" and H[i] >= p_ouv: etat[j] = "plein"; prix_ouv[j] = p_ouv; pnl -= MAKER / (2 * N)
                elif s == "plein" and Lo[i] <= niv[j + N - 1]:
                    pnl += (1 - niv[j + N - 1] / prix_ouv[j] - MAKER) / (2 * N); etat[j] = "attente"
        sortie = Cl[i] > niv[-1] * (1 + ECART) or Cl[i] < niv[0] * (1 - ECART)
        if sortie or not masque[i + 1 if i + 1 < fin else i] or i == fin - 1:   # extinction : on ferme tout au prix de clôture
            for j, s in etat.items():
                if s == "plein":
                    r = Cl[i] / prix_ouv[j] - 1 if j < 0 else 1 - Cl[i] / prix_ouv[j]
                    pnl += (r - TAKER) / (2 * N)
            actif = False
    return pnl


def bornes(a, b): return next(i for i, t in enumerate(T) if t >= a), next((i for i, t in enumerate(T) if t >= b), len(T))


r0, r1 = bornes(ts("2024-01-01"), ts("2026-01-01")); j0, j1 = bornes(ts("2026-01-01"), ts("2026-10-17"))
vs = sorted(v[r0:r1])
toujours = [True] * len(T)
print(f"Réglage 2024-2025 : toujours allumée {100 * grille(r0, r1, toujours):+.1f} %")
choix = {}
for q in (0.2, 0.4, 0.6):
    seuil = vs[int(len(vs) * (1 - q))]; m = [x >= seuil for x in v]
    choix[q] = (grille(r0, r1, m), seuil); print(f"  q={q:.0%} (seuil {seuil:.5f}) : {100 * choix[q][0]:+.1f} %")
q = max(choix, key=lambda k: choix[k][0]); seuil = choix[q][1]
m = [x >= seuil for x in v]
print(f"Choisi : q={q:.0%}, figé.")

g = grille(j0, j1, m); a = grille(j0, j1, toujours)
seg = m[j0:j1]; L = len(seg); R = []
rnd = random.Random(12)
for _ in range(500):
    k = rnd.randrange(1, L); mm = [False] * len(T); mm[j0:j1] = seg[k:] + seg[:k]; R.append(grille(j0, j1, mm))
R.sort(); rang = sum(x < g for x in R) / len(R)
print(f"JUGEMENT 2026 : grille pilotée {100 * g:+.2f} % | toujours allumée {100 * a:+.2f} % | décalages au hasard p50 {100 * R[250]:+.2f} % p95 {100 * R[475]:+.2f} % | rang {rang:.0%} | temps allumé {100 * sum(seg) / L:.0f} %")
ok = g > 0 and g > a and g > R[475]
print("VERDICT :", "GAGNE" if ok else "ÉCHEC")

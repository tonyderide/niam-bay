#!/usr/bin/env python3
"""J'essaie tout de suite le critère de capture-recapture sur mon propre plateau (n=5, LNS bloquée à 42).
Estimateur de Schnabel : N̂ = Σ(C_t·M_t) / Σ R_t, avec C_t = solutions capturées à l'étape t, M_t = déjà marquées avant,
R_t = recaptures. Quand N̂ ≈ nombre de solutions distinctes déjà vues, la recherche tourne en rond : on l'arrête."""
import random, time
from lns import refill
from search import random_greedy

n = 5; rng = random.Random(7)
cur = random_greedy(n, rng); seen = set(); num = den = 0; t0 = time.time(); it = 0; best = len(cur)
while time.time() - t0 < 120:
    it += 1
    k = rng.randint(2, max(3, len(cur) // 5))
    new = refill(n, rng.sample(cur, len(cur) - k), rng)
    if len(new) >= len(cur): cur = new; best = max(best, len(cur))
    key = frozenset(cur); M = len(seen); recap = 1 if key in seen else 0; seen.add(key)
    num += 1 * M; den += recap
    if it % 2000 == 0 and den:
        N_hat = num / den
        print(f"{time.time()-t0:5.0f}s it={it} meilleur={best} distincts={len(seen)} N̂={N_hat:.0f} ratio={len(seen)/N_hat:.2f}")
        if len(seen) / N_hat > 0.95:
            print(f"→ arrêt : la recherche recapture ce qu'elle a vu (plateau à {best}). Il faut changer de structure."); break

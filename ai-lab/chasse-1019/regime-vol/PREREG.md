# PREREG regime-vol (écrit avant tout calcul)
Données: bougies 1d mark Kraken Futures PF_XBT/ETH/SOL/DOT/LINK USD, 2023-06-01 -> 2026-10-16. Clôture du jour t.
Stratégie: panier 5 coins, poids max 1/5 chacun, long seulement. Signal décidé à la clôture t, appliqué au rendement de t+1.
Long_i(t) = close > EMA(N) ET vol réalisée 20j (écart-type des rendements log journaliers * sqrt(365)) <= percentile P de ses 365 derniers jours (P=100 => pas de filtre).
Taille_i = Long_i * min(1, V / vol20_i) / 5 ; V = cible de vol annualisée (V=inf => taille 1/5 pleine).
Grille (27 combos): N in {50,100,200} x P in {50,75,100} x V in {0.4, 0.6, inf}.
Sélection 2024-01-01..2025-12-31: critère = rendement net / |pire creux| (Calmar), un seul gagnant figé. Jugement 2026-01-01..2026-10-16 sans réajustement.
Frais: 0,10 % * |Δpoids| par changement, 0,01 %/jour * somme des poids (portage). Capital non investi = 0 %.
Témoins: (a) acheter-garder panier égal 1/5 sans rebalance; (b) hasard: 500 tirages, chaque série de poids par coin décalée circulairement d'un offset aléatoire (même exposition, même rotation), mêmes frais, p95 du rendement; (c) diagnostic: même EMA N sans filtre vol ni cible (P=100,V=inf).
GAGNE = rendement jugement > 0 ET > acheter-garder ET > p95 hasard ET pire creux < pire creux d'acheter-garder.
Verdict "la cible de vol ajoute un avantage" seulement si le gagnant bat aussi le diagnostic (c) en rendement ET passe le test ci-dessus.

## Résultat (ajouté après calcul; script: scratchpad rv/bt.py)
Gagnant sélection (figé): EMA50, P=50, V=inf (sans cible de vol). Jugement: +0,46 % (creux -21,5 %). EMA50 seul: +1,7 % (-26,8 %). Acheter-garder: -14,9 % (-51,6 %). Hasard p95: +12,7 %. VERDICT: PERD (pas > p95 hasard). Cible de vol: pas d'avantage démontré.

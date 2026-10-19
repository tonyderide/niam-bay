# PREREG cassure-atr-filtre (écrit avant tout calcul, 2026-10-19)
Données: Kraken Futures PF_XBTUSD/PF_ETHUSD/PF_SOLUSD, 15m (signal) et 1d (filtre).
Filtre: tendance jour J-1 = clôture du dernier jour COMPLET vs EMA50 journalière (même jour). Long autorisé si clôt>EMA50, short si clôt<EMA50.
Signal 15m: canal Keltner = EMA(20) de la clôture ± m*ATR(20) (ATR = moyenne simple du True Range sur 20). Long si clôture > haut ET tendance haussière; short si clôture < bas ET tendance baissière. Entrée à l'ouverture de la bougie suivante. Une position à la fois par coin.
Sortie: stop suiveur k*ATR (ATR au moment du signal, figé) depuis le plus haut/bas des clôtures depuis l'entrée, testé sur extrêmes de bougie (stop touché => sortie au niveau du stop, ou à l'ouverture si gap); sinon sortie à la clôture après H bougies.
Frais: 0,10% aller-retour (par trade), rendement net = brut - 0,001, trades en rendement relatif non composé.
Grille (18 combos): m∈{1.5,2,2.5} × k∈{2,3} × H∈{16,48,96} bougies. Un seul jeu de paramètres pour les 3 coins, choisi par somme des rendements nets de SÉLECTION (2026-01-01→2026-06-30), exigeant ≥30 trades en sélection.
Jugement 2026-07-01→2026-10-16, paramètres figés, indicateurs préchauffés avant (données depuis 2025-10).
Témoin: 300 tirages; pour chaque coin même nombre de trades que la stratégie en jugement, instants d'entrée aléatoires, direction = tendance journalière, mêmes sorties/frais. Métrique = somme nette des 3 coins; p95 de cette distribution.
GAGNE = jugement net>0 sur ≥2 coins/3 ET somme nette jugement > p95 hasard ET ≥30 trades (total jugement). Sinon PERD/non prouvé.

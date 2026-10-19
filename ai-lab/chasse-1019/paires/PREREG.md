# PREREG paires (écrit AVANT tout calcul, 2026-10-19)
Données: labo-cutoff/candles.json (close horaire). Paires: ETH/BTC, SOL/ETH, LINK/DOT. x = log(A/B).
Sélection 2026-01-01→2026-06-30 ; Jugement 2026-07-01→2026-10-16 (z calculé avec historique avant, pas de fuite).
Signal: z = (x - moyenne W)/écart-type W (fenêtre glissante, y compris l'heure t). Signal à la clôture t, exécution à la clôture t+1.
z>a => short ratio (short A / long B); z<-a => long ratio. Sortie: |z|<b, ou H heures, ou |z|>c (stop). Une position à la fois par paire.
PnL trade = ±(x_sortie - x_entrée) - 0.002 (0,20 % aller-retour, 2 jambes).
Grille (24 combos): W∈{48,168}, a∈{1.5,2,2.5}, b∈{0,0.5}, H∈{24,72}, c=4 fixe.
Choix: UN seul jeu de paramètres pour les 3 paires = max du net total de sélection. Aucun re-réglage ensuite.
Témoin hasard: 500 tirages; par paire, même nombre de trades que le jugement, instants d'entrée uniformes, direction aléatoire, durées tirées parmi celles réelles; même frais. Statistique = net total des 3 paires; p95 du hasard.
GAGNE = net jugement >0 sur ≥2 paires/3 ET net total > p95 hasard ET ≥30 trades (total sur 3 paires).

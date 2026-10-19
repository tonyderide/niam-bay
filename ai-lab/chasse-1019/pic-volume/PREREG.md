# PREREG pic-volume (écrit avant tout calcul)
Données: bougies trades 15m Kraken Futures PF_XBTUSD, PF_ETHUSD, PF_SOLUSD.
Signal: volume[i] > k * médiane(volume[i-96..i-1]) ET corps (close-open) de signe s. Entrée à l'open de i+1, sortie au close de i+H (H bougies tenues). Frais 0,10 % A/R. Un trade à la fois par coin (pas de chevauchement: signal ignoré si position ouverte).
Grille (24 combos): k in {3,5} x H in {2,4,8} x s in {haussier,baissier} x mode in {suivi (long si haussier, short si baissier), retour (inverse)}.
Sélection 2026-01-01→06-30: choisir le combo au rendement net moyen/trade le plus haut, 3 coins poolés, avec >=30 trades en sélection. Un seul combo gardé.
Jugement 2026-07-01→10-16: combo figé. Net par coin (somme des rendements nets). Témoin: 300 tirages, mêmes nb trades/coin, même H et direction, instants aléatoires dans la période de jugement; statistique = net total 3 coins; p95.
GAGNE = net jugement >0 sur >=2 coins/3 ET net total > p95 hasard ET >=30 trades en jugement. Sinon PERD.

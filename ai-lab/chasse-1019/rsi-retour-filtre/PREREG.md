# PREREG rsi-retour-filtre (écrit avant tout calcul)
Données: labo-cutoff/candles.json (close horaire). Coins: BTC ETH SOL. Sélection 2026-01-01..06-30, jugement 2026-07-01..10-16.
Signal: RSI(14) Wilder horaire sur close; EMA200 horaire (warm-up avant 2026-01-01 si dispo, sinon début des données).
Long si RSI<L ET close>EMA200; short si RSI>100-L ET close<EMA200 (parier le retour dans le sens de la tendance de fond).
Entrée: close de la bougie suivant le signal (seules des closes existent). Une position à la fois par coin.
Sortie: RSI recroise 50, ou H heures, ou SL fixe vérifié sur close horaire (sortie au close qui franchit). Frais 0,10% aller-retour par trade.
Grille (16 combos, <=30): L in {20,25} x H in {12,24,48,72} x SL in {2%,4%}.
Choix: combo maximisant la somme des rendements nets sur SÉLECTION (3 coins agrégés), appliqué tel quel au jugement.
Témoin hasard: 300 tirages; par coin, même nombre de trades que le jugement réel, entrées horaires aléatoires dans la période, direction aléatoire, mêmes H (durée fixe) et SL, mêmes frais; p95 de la somme nette par coin.
GAGNE: jugement net>0 sur >=2 coins/3 ET > p95 hasard de ces coins ET >=30 trades (total 3 coins). Sinon PERD. Pas de réajustement après jugement.

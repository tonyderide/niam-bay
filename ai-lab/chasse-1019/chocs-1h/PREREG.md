# PREREG chocs-1h (écrit avant tout calcul)
Données: labo-cutoff/candles.json (close horaire mark), coins BTC ETH SOL.
Signal: bougie t, r1h = c[t]/c[t-1]-1; choc si |r1h| > k * std(r1h des 168 h précédentes, hors t).
Entrée: close de t+1 (bougie suivante). Sortie: close de t+1+H. Pas de chevauchement par coin (signal ignoré si position ouverte). Frais 0,10% par trade (aller-retour).
Sens: "suite" (même signe que le choc) ou "retour" (signe opposé).
Grille (sélection 2026-01-01→06-30, 3 coins poolés): k∈{2,3,4,5}, H∈{1,2,3,6,12,24}, sens∈{suite,retour}. Critère: somme nette poolée max, avec ≥30 trades en sélection.
Variante SL/TP: mêmes k, sens, H choisis; SL∈{0.5,1,2,3}%, TP∈{0.5,1,2,3,5}%, vérifiés sur closes horaires (sortie au 1er close franchissant, au niveau du close), sinon sortie à H. Choix par somme nette poolée en sélection.
Jugement 2026-07-01→10-16, paramètres figés. Témoin: 300 tirages, mêmes nombre de trades par coin, instants aléatoires, sens aléatoire, mêmes H (et SL/TP); statistique = somme nette poolée; p95.
GAGNE = net jugement >0 sur ≥2 coins/3 ET somme poolée > p95 hasard ET ≥30 trades en jugement.

# Stratégie de Tony : croisement VWAP × EMA9 en 3 minutes (pré-enregistré le 2026-10-19, avant tout calcul)
- Données : bougies de **trades** Kraken Futures en 1 min (le volume est nécessaire pour le VWAP), agrégées en **3 min**, pour BTC, ETH et SOL, du 01/01/2026 au 16/10/2026.
- VWAP : de session, remis à zéro chaque jour à 00:00 UTC (prix typique (H+B+C)/3 × volume). EMA9 : sur les clôtures 3 min.
- **Règle** : quand l'EMA9 croise le VWAP vers le haut, on achète ; quand elle le croise vers le bas, on vend à découvert. Toujours en position : on se retourne à chaque croisement.
- Exécution : (A) à la clôture de la bougie du croisement ; (B), plus réaliste, à l'ouverture de la bougie suivante.
- Frais : taker 0,05 % par côté, soit 0,10 % par retournement. Variante maker à 0,02 % par côté pour information.
- Périodes : **janvier-juin** (déjà vue, peut-être) et **juillet-octobre** (jamais vue par mon modèle).
- Témoin : le même nombre de retournements à des instants tirés au hasard (200 tirages). On compare au 95e percentile.
- **Critère « ça marche »** : sur juillet-octobre, en exécution B avec les frais taker, rendement > 0 sur au moins 2 coins sur 3 ET > 95e percentile du hasard.

## Résultat (2026-10-19)
Avec l'exécution B (ouverture de la bougie suivante) et les frais taker, sur la période **juillet-octobre (jamais vue)** :
- BTC : **−31,6 %** (502 trades, 22 % de gagnants), contre un 95e percentile du hasard à −14,8 %
- ETH : **−12,3 %** (488 trades, 23 %), hasard p95 −2,5 %
- SOL : **−51,6 %** (550 trades, 21 %), hasard p95 −11,8 %

Sur janvier-juin : de −46 % à −52 % sur les trois coins.

**Critère : NON atteint.** Les trois coins perdent sur les deux périodes, et la stratégie fait **pire que des retournements au hasard** (le hasard perd moins, parce que ses pertes ne viennent que des frais). En maker (0,02 %, qui suppose d'être toujours rempli en ordre limite, ce qui est optimiste), seul ETH juillet-octobre est positif (+17,6 %), alors que BTC (−7,5 %) et SOL (−32,6 %) restent négatifs : un sur six cas maker, c'est du bruit.
Pourquoi : environ 4 croisements par jour, dont 75 % sont de faux départs. Le VWAP et l'EMA9 se recroisent sans cesse quand le marché hésite, et chaque retournement paie 0,10 %.
Note : la colonne « net moyen » de la sortie n'inclut pas les frais d'entrée ; le « total » les inclut.

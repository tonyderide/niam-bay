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

## Amendement (Tony : « tu as oublié de mettre le SL ») : SL fixe 0,3 / 0,5 / 1 % (toucher du high/low), à plat jusqu'au croisement suivant, période juillet-octobre, exécution B, taker.

- SL 0,3 / 0,5 / 1 % sur juillet-octobre : BTC −17 à −22 %, ETH −1 à +2,5 %, SOL −39 à −41 %. SL 0,1 % (réglage de Tony) : voir la ligne suivante du journal.

## ⚠️ BUG TROUVÉ (19/10, 17h40) : l'API ne renvoie que 2000 bougies max par appel ; le test demandait des fenêtres de 5000 min → ~60 % des minutes manquaient. Tony avait raison (« dans ton banc de test il doit y avoir un problème »). Pagination corrigée à 1800 min, test relancé à l'identique.

## Relance avec des données complètes (17h55)
Juillet-octobre, bougie suivante, taker : BTC −65,6 % (1050 trades), ETH −67,3 % (1104), SOL −76,2 % (1112). Janvier-juin : de −82 % à −87 %. Avec les données complètes, il y a 2 fois plus de croisements, donc 2 fois plus de frais. La conclusion tient, en pire, et c'est cohérent avec l'agent indépendant (−52 à −66 %).

## Variante « pas trop précis » (1019 ~18h45, idée de Tony)
On ne prend que les croisements nets : écart EMA9/VWAP ≥ seuil, maintenu pendant `conf` bougies 3m. 72 réglages ont été testés, choisis sur janvier-juin (filtre.py) puis jugés sur juillet-octobre.
- Réglage retenu : seuil 0,5 %, conf 5, sans SL. Janvier-juin : −19 / −55 / −29 %. Juillet-octobre : BTC +20 %, ETH +21 %, SOL +27 %.
- Au hasard, avec le même nombre de trades (hasard.py) : p95 de +29 / +42 / +41 %. La stratégie se classe au 87e-91e centile, donc **sous le p95**. Simplement garder du juillet au octobre donnait +39 / +54 / +42 %.
- Les résultats sont instables d'un seuil voisin à l'autre (à 0,75 % et 1 %, souvent négatifs).
- Verdict : **presque**. Le filtre réduit les frais (≈100 trades au lieu de 1 100) mais ne démontre pas d'avantage sur le hasard. C'est la hausse du marché qui porte le résultat.

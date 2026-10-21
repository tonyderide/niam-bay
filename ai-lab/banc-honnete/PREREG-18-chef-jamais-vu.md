# Pré-enregistrement 18 : le chef d'orchestre figé, sur 18 cryptos jamais vues
Écrit et commité le 22/10/2026 à 01h09, avant tout téléchargement ou calcul.

## Règle figée (aucun réglage)
Chaque lundi 00:00 UTC : score = somme des rendements des trades déjà SORTIS pendant les 8 dernières semaines ; on joue la semaine, à poids égal, les 10 meilleures au score > 0 ; gain = trades ENTRÉS cette semaine-là. (Réglage repéré dans t19/t20 sur BTC/ETH/SOL ; jamais essayé ailleurs.)

## Données jamais vues par cette idée
18 paires, en 6 groupes de 3 (même structure que l'univers d'origine, 3 marchés × 2 unités × 4 signaux × 5 TP/SL = 120 stratégies par groupe) :
G1 XRP DOGE ADA · G2 LINK AVAX DOT · G3 LTC BCH UNI · G4 ATOM NEAR FIL · G5 AAVE APT OP · G6 TRX XLM ETC.
Bougies 15 min et 1 h, période complète 01/01/2024 → 17/10/2026. Exécution identique à t17_lib (ouverture suivante, gaps, pire cas, taker 0,05 %/côté, 24 bougies max, mise fixe).

## Témoin
Par groupe : 1 000 chefs au hasard (mêmes nombres de stratégies jouées chaque semaine, choisies au hasard dans les 120 du groupe).

## Deux verdicts
1. **Le chef sait choisir** : la somme des 6 groupes dépasse le 95e centile de la somme des chefs au hasard (tirages appariés), ET ≥ 4 groupes sur 6 au-dessus de la médiane de leurs chefs au hasard.
2. **C'est rentable** : (1) ET somme des 6 groupes > 0.
Si (1) échoue : l'idée est enterrée. Si (1) réussit mais pas (2) : le chef choisit vraiment, mais dans une bibliothèque qui perd ; il faudra une meilleure bibliothèque.

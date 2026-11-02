# Pré-enregistrement 58 : le portefeuille de shorts TENUS des nouvelles cotations, couvert — le risque est-il maîtrisé ?
Écrit le 02/11/2026 vers 17h30 CET, avant tout calcul. Hypothèse H22 de FILE-HYPOTHESES.md (passée avant H21 : c'est la question pratique laissée ouverte par PREREG-57). PREREG-57 : en poids égaux rééquilibrés chaque jour, l'effet est détruit (−33 %/an) par le frottement de volatilité ; trade par trade, le short **tenu** fait +23,3 %. Ici, la construction tenue.

## Portefeuille (aucun réglage ; données et univers de PREREG-57)
- Perpétuels USDT-M Binance crypto (data-univers/klines.json, non-COIN retirés), financement listings/funding.json, 01/01/2021 → 26/10/2026.
- **Mise fixe** : chaque nouvelle cotation reçoit un short de notionnel **a = 1/30 du capital initial** à l'ouverture de sa 2e bougie, **tenu en quantité fixe** jusqu'à la clôture de la 90e bougie (ou la dernière si retrait), sans rééquilibrage. Si la perte atteint a (prix doublé) : position fermée à ce moment (plancher, liquidation).
- **Couverture tenue** : à la même date, long de notionnel a sur le panier égal des pièces cotées depuis plus de 365 jours, quantités fixées à l'entrée, tenues sur la même fenêtre (même fin, même plancher non appliqué au long).
- Financement : le short reçoit, le long paie, sur le notionnel du jour (quantité × prix). Frais 0,05 % à l'entrée et à la sortie de chaque jambe.
- Pas de capitalisation : le P&L s'additionne en fraction du capital initial (1). Courbe de capital = 1 + P&L cumulé.

## Mesures
Rendement annuel moyen (P&L / années), Sharpe (P&L quotidien), pire baisse de la courbe, pire mois (P&L du mois / capital au début du mois), mois négatifs, levier brut moyen et maximal (nombre de positions ouvertes × 2a), par année ; sans couverture (info).

## Critère (celui de PREREG-57, repris tel quel)
- **RISQUE MAÎTRISÉ** si : Sharpe 2021-2026 > 1,0 **ET** pire baisse < 30 % **ET** pire mois > −15 % **ET** P&L 2026 > 0 **ET** p < 0,05 contre le témoin.
- **RISQUE NON MAÎTRISÉ** sinon.
- **Témoin** : chaque short d'une nouvelle cotation remplacé par le short tenu d'une pièce ancienne tirée au hasard sur la même fenêtre ; 200 tirages, graine 58 ; p = part au Sharpe ≥.

## Relecture d'équité
a = 1/30 fixé ici (≈ le nombre moyen de shorts ouverts trouvé en PREREG-57, 25,5 — information connue avant ce commit, déclarée) ; la mise ne change pas le Sharpe, seulement l'échelle de la baisse et du pire mois. Limites : liquidité des jetons neufs non modélisée, exécution à l'ouverture, pas de marge croisée détaillée. Aucun ordre, aucun compte, aucune clé, aucune action sur Martin ni Kraken.

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

## Résultat (02/11/2026, 19h — t58.py → t58.log, chiffres dans t58.json)
Premier lancement après le commit 28b4803 : arrêté par une erreur dans le témoin (panier ancien vide en 2021, bug commun avec t57.py, voir la correction de PREREG-57). Relancé une fois après correction, `nice -n 10`.

- **598 trades**, résultat moyen par trade **+11,6 %** (financement et frais compris), **125 trades (21 %) liquidés** en cours de route (perte de la mise quand le prix double avant la fin des 90 jours).
- Levier brut moyen 1,7, maximum 5,3 (jusqu'à 80 shorts ouverts en même temps).

| | Couvert, 2021-2026 | Sans couverture (info) |
|---|---|---|
| P&L annuel moyen (fraction du capital initial) | +25,5 % | +39,6 % |
| Sharpe | **0,48** | 0,66 |
| Pire baisse | **34 %** | 33 % |
| Pire mois (rapporté au capital du début du mois) | −9,3 % (2025-10) | −18,9 % (2024-11) |
| Mois négatifs | 25/70 | 25/70 |

Par année (couvert ; pire mois rapporté à un capital remis à 1 en début d'année) : 2021 +62,5 % (Sharpe 0,89) · 2022 +7,0 % (0,69) · 2023 +69,8 % (2,82) · 2024 +62,1 % (1,04) · **2025 −44,1 % (−0,55 ; pire mois −31,5 %, baisse 68 %)** · **2026 −10,6 % (−0,36)**.
Témoin (shorts tenus de pièces anciennes, mêmes fenêtres) : Sharpe −0,02 ± 0,17 ; **p = 0,005**.

**VERDICT (pré-enregistré) : RISQUE NON MAÎTRISÉ** — Sharpe 0,48 (< 1), pire baisse 34 % (> 30 %), P&L 2026 négatif ; seuls le pire mois et le témoin passent.

**Ce que ça montre :**
- L'effet est bien réel au niveau du portefeuille (p = 0,005 contre des shorts de pièces anciennes) et tenir les shorts le rend positif (+25 %/an), contrairement au rééquilibrage quotidien.
- Mais il se paie par une **liquidation d'un trade sur cinq** et par des années entières de pertes : 2025 (−44 %) et 2026 (−11 %), précisément les deux années les plus récentes. Un Sharpe de 0,5 avec une baisse de 34 % n'est pas un risque maîtrisé.
- **Correction importante de PREREG-46** : son plancher à −100 % n'était appliqué qu'à la sortie ; avec une liquidation réaliste en cours de route, 21 % des trades perdent toute la mise et la moyenne par trade tombe de ~+23 % à +11,6 %. L'avantage existe mais il est deux fois plus mince et beaucoup plus risqué que PREREG-46 ne le laissait croire.
- Rien à proposer à Martin en l'état. Le juge reste le test en avant (PREREG-47).

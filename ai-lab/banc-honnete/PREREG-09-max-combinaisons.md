# Pré-enregistrement 09 : un maximum de combinaisons (idée de Tony, 1021 vers 01h00, avant tout calcul)
Grille complète = 10 signaux × 7 filtres × 6 sorties × 2 unités de temps = **840 stratégies**.
- Unités de temps : 1d sur les 21 cryptos de 06, et 4h sur BTC, ETH et SOL.
- Frais : 0,05 % par côté.

**Signaux** (le short est le miroir du long) :
1. cassure du plus haut/bas de 20 bougies ;
2. cassure du plus haut/bas de 55 bougies ;
3. croisement EMA20/EMA50 ;
4. retournement du Supertrend(10, 3) ;
5. croisement MACD/signal ;
6. RSI(2) < 10, ou > 90 pour le short ;
7. RSI(14) qui repasse au-dessus de 30, ou sous 70 pour le short ;
8. close sous la bande de Bollinger basse, ou au-dessus de la haute pour le short (retour à la moyenne) ;
9. close au-dessus de la bande de Bollinger haute, ou sous la basse pour le short (momentum) ;
10. 3 bougies dans le même sens, jouées à l'envers.

**Filtres** :
- aucun ;
- dans le sens de la SMA200 ;
- ADX(14) > 25 ;
- ADX(14) < 20 ;
- volatilité croissante (ATR14 > ATR60) ;
- volatilité décroissante (ATR14 < ATR60) ;
- longs seulement.

**Sorties** :
- après 3, 5, 10 ou 20 bougies ;
- au signal opposé ;
- SL de 5 % avec TP de 10 %.

## Règles
1. **Sélection** : la meilleure somme sur 2024-2025, avec au moins 100 trades et au moins 60 % des marchés positifs. On ne regarde pas 2026 à cette étape.
2. **Jugement UNIQUE** de cette stratégie sur 2026, avec `banc.py` (500 tirages au hasard). Elle GAGNE si la somme est > 0, si au moins 60 % des marchés sont positifs, si elle dépasse le p95 du hasard et si elle compte au moins 30 trades.
3. **Contrôle global** (informatif, mais il servira à interpréter le résultat) : corrélation de rang de Spearman entre la somme 2024-2025 et la somme 2026 sur les 840 stratégies. On compare aussi la part de stratégies positives en 2026 dans le top 20, dans les 840 et dans le bottom 20. Si le classement de 2024-2025 ne prédit rien (corrélation de 0,1 ou moins), un éventuel gagnant sera traité comme de la chance.

## Résultat (1021 vers 01h10, t09.log, grille complète dans t09-grille.json) : ÉCHEC
- 840 stratégies, dont 237 éligibles.
- Stratégie sélectionnée : **1d, 3 bougies jouées à l'envers, longs seulement, tenue de 10 jours**. Résultat : +1 548 % en 2024-2025.
- **Jugement sur 2026 : +6,8 %, 56e centile du hasard, 11 marchés positifs sur 21.** ÉCHEC.

**Contrôle global, la vraie réponse :**
- Corrélation de Spearman entre 2024-2025 et 2026 : **+0,042**, soit pratiquement zéro.
- Part de stratégies positives en 2026 : 45 % dans le top 20 de 2024-2025, **45 % sur les 840**, 50 % dans le bottom 20.
- **Le classement de 2024-2025 ne dit RIEN de 2026.** Avoir bien marché hier ne prédit pas demain. Sur ces 840 combinaisons d'indicateurs classiques, ce qui « marche » sur une période relève du hasard.

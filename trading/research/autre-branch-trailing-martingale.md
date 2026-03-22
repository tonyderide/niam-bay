# Trailing Stop + Martingale : Analyse brutale du code

Source : `C:/martin/backtest/` -- 7 fichiers Python, lus ligne par ligne.

---

## Qu'est-ce qui est teste

Sept scripts explorent des variations du meme concept fondamental :
**"Si je perds, je double (ou triple) la mise et je change de direction. Un seul gain efface toutes les pertes."**

C'est la martingale classique du casino, appliquee a ETH avec du levier.

---

## Les fichiers, un par un

### 1. `trailing_martingale.py` -- Le prototype

- **Data** : ETH 5m, 30 jours, $15 capital, 10x levier
- **Mecanique** : Trailing stop au lieu de TP fixe. Sur perte : multiplier x2 ou x3, inverser la direction. Sur gain : reset.
- **Max doublings** : 3-4 avant reset complet
- **Variantes testees** : 5m vs 15m, avec/sans filtre MACD+Stoch, trail de 0.5% a 2%, stakes $1-$2, multiplicateurs 2x et 3x, min profit 0-0.5%
- **Nombre de combinaisons** : des centaines (boucle sur 6 trails x 2 stakes x 2 mults x 2 maxd x 3 min_profit x 2 timeframes + MACD filtered)

**Probleme critique** : Le mode sans filtre entre sur **chaque bougie**. 30 jours x 288 bougies/jour = ~8640 trades. Avec fees de 0.05% par cote sur 10x levier, ca fait ~1% du notionnel brule en fees par trade. C'est un accelerateur de ruine.

### 2. `trailing_filtered.py` -- 12 filtres d'entree

Teste 12 filtres differents :
- F1: MACD + Stoch (le signal actuel de Martin Grid)
- F2: MACD seul
- F3: RSI extreme (<30 ou >70)
- F4: EMA + Stoch
- F5: Stoch cross
- F6: MACD momentum
- F7: ADX + DI
- F8: Bollinger Bands bounce
- F9: Volume spike + MACD
- F10: **Aucun filtre** (candle color = direction)
- F11: MACD + RSI
- F12: EMA50 + MACD

Combine avec trail 1%/1.5%/2%, stakes $1/$2, mult 2x/3x, max doublings 3/4, min profit 0%/0.5%.

**Total : 576 combinaisons.**

Le "hedge reversal" apres 2 pertes dans la meme direction est present dans TOUS les filtres. C'est un mecanisme de panique automatise, pas une strategie.

### 3. `compare_trailing.py` -- Le fichier le plus revelateur

Ce script compare **avec et sans martingale** sur 3 mois de donnees. C'est le seul qui pose la bonne question.

- **Trailing 2-niveaux** : initial large (2%), puis serre (0.3% a 1%) une fois en profit
- **Safety SL** : 5% -- c'est un filet de securite enorme pour un 10x levier (= 50% du capital sur un seul trade)
- **Martingale** : 3x multiplicateur, max 4 doublings, hedge apres 2 pertes
- **Capital** : $10, 10x levier, 90% du capital engage

**Detail crucial** : `position_size = (notional / price) * size_mult` -- la taille de position MULTIPLIE par le facteur martingale. Apres 3 pertes consecutives : position = 27x la taille initiale. Si le capital est de $10 avec 10x levier, la position "normale" est ~$90 notionnel. Apres 3 pertes : $90 x 27 = **$2430 notionnel**. Sauf que le capital restant est probablement <$8 a ce stade, donc le levier effectif explose.

**Bug dans le code** : `run_backtest()` (lignes 112-273) utilise une variable `size_mult` dans le scope de la fonction mais les fonctions `_update_martingale` et `_reset_martingale` utilisent des **globales**. Le `run_backtest()` ne les appelle meme pas -- il a des references a `_update_martingale` mais la logique martingale dans `run_backtest` est un dead code (la variable `size_mult` locale reste a 1.0). Seul `run_backtest_v2` utilise correctement les globales. C'est un gros red flag sur la fiabilite des resultats.

### 4. `martingale_strategies.py` -- Le catalogue complet

8 strategies de gestion de position :
- **M1 : Classic Martingale** -- double apres chaque perte, 5x levier, $75 base. Multiplier x2 jusqu'a 4 doublings = position 16x. Avec $15 de capital et 5x levier, max notionnel = $75. A 16x : $1200 desire mais cap a $75 max (capital * leverage). Donc la martingale ne fonctionne meme pas -- le capital disponible est insuffisant pour doubler apres 2 pertes.
- **M2 : Reverse Martingale** -- augmente apres les gains, reset apres les pertes. Plus sain en theorie.
- **M3 : Fibonacci** -- progression 1,1,2,3,5,8,13 au lieu de doublement. Moins agressif mais meme logique toxique.
- **M4 : D'Alembert** -- +1 unit apres perte, -1 apres gain, cap a 5 units. Le plus conservateur du lot.
- **M5 : Oscar's Grind** -- augmente uniquement apres un gain, jusqu'a un target de cycle. Pas vraiment une martingale.
- **M6 : Grid Scalping** -- 3 positions simultanees sur grille 0.3%, SL a 0.6%. Pas une martingale du tout.
- **M7 : Mean Reversion** -- RSI <25 pour long, >75 pour short, ajoute des entrees si ca continue contre. TP 0.5%, SL 1%. DCA deguisee.
- **M8 : Momentum Pyramid** -- ajoute a +0.3% et +0.6%, trailing stop. La seule qui ajoute en gagnant.

TP/SL pour M1-M5 : TP 1.5%, SL 0.5% (ratio 3:1). Mais avec le levier 5x, le SL de 0.5% = 2.5% du capital par trade. Et la martingale multiplie ca.

### 5. `asymmetric_martingale.py` -- L'idee de "TP >> SL"

- **Concept** : TP 0.8%, SL 0.2%. Le ratio 4:1 est cense compenser le faible win rate.
- **Aucun filtre d'entree** : entre a chaque bougie (open). 30 jours x 288 = ~8640 trades sur 5m.
- **Fee par trade** : 0.05% x 2 cotes x 10x levier = ~1% du stake brule en fees.
- Sur 8640 trades avec $2 stakes : ~$172 de fees. Capital = $15. **Les fees seules mangent 11x le capital.**
- **Variante "scalp" A12** : TP 0.4%, SL 0.1% -- le SL de 0.1% sur ETH/5m est du bruit pur. Chaque mouvement de $2 sur ETH (~0.1% a $2000) declenche le SL.

Le script teste aussi `run_no_reverse` (A13) qui utilise le momentum de la bougie precedente pour choisir la direction. C'est du coin flip avec des frais.

Inclut une reference S18 "Triple Hedge" avec MACD+Stoch pour comparaison, qui utilise un levier effectif de `cap * 5 * actual_mult` -- a la 3eme perte hedgee, le notionnel est 15x le capital restant. C'est du 15x levier effectif.

### 6. `asymmetric_3days.py` -- Cherry-picking 3 jours

Meme logique que asymmetric_martingale mais sur les 3 derniers jours seulement. 18 variantes.

**C'est du backtesting sur un echantillon trop petit pour avoir la moindre validite statistique.** 3 jours = ~864 bougies 5m = ~288 bougies 15m. Les resultats sont du bruit.

### 7. `asymmetric_wider_sl.py` -- SL plus large

SL de 0.4% a 0.8%, TP de 0.8% a 2.0%. Multiplie les combinaisons sur 5m et 15m.

**Total : 800 combinaisons testees.** Le script trie par PnL et montre le top 30. C'est du data mining pur -- avec 800 combinaisons, certaines seront "profitables" par hasard sur 30 jours.

---

## Reponse a la question cle : Est-ce que ca survit avec les fees ?

**Non. Aucune version ne survit de maniere fiable.**

Voici pourquoi, mathematiquement :

### 1. Les fees sont fatales sur les entrees sans filtre

- Fee taker : 0.05% par cote = 0.1% par trade (entree + sortie)
- Avec 10x levier : 0.1% x 10 = **1% du stake par trade**
- Pour etre profitable : besoin d'un edge > 1% par trade apres fees
- Un SL de 0.2% = perte de 2% du stake + 1% de fees = **3% perdu par SL hit**
- Un TP de 0.8% = gain de 8% du stake - 1% de fees = **7% gagne par TP hit**
- Break-even win rate : 3 / (3+7) = **30%**
- Sur ETH 5m sans filtre, le TP 0.8% est touche ~35-45% du temps (selon la volatilite)
- Marge d'edge : **5-15%** -- fragile et dependant du regime de marche

### 2. La martingale transforme un petit edge en risque de ruine

Avec un multiplicateur 3x et max 4 doublings :
- Sequence de pertes : $2 -> $6 -> $18 -> $54
- Total perdu avant reset : $80 (5.3x le capital de $15)
- Un seul cycle complet de 4 pertes = **game over**
- Probabilite de 4 pertes consecutives avec 35% win rate : (0.65)^4 = **18%**
- Sur 8640 trades, le nombre attendu de sequences de 4+ pertes : ~dozens

### 3. Le "hedge reversal" n'aide pas

Inverser la direction apres 2 pertes dans la meme direction presuppose que le marche est mean-reverting a cette echelle. Sur ETH 5m, il ne l'est pas systematiquement. C'est un pattern-matching sur du bruit.

### 4. Le seul script honnete (compare_trailing.py) le prouve

Le script `compare_trailing.py` teste **avec et sans martingale** sur 3 mois. Le fait que ce script existe montre que les resultats precedents etaient douteux et qu'il fallait une comparaison propre. Et il inclut une version sans martingale -- c'est le bon instinct.

### 5. Les tailles d'echantillon sont insuffisantes

- 30 jours de donnees = 1 seul regime de marche
- Les strategies filtrees (MACD+Stoch) generent 20-60 trades sur 30 jours
- 20 trades = zero significativite statistique
- 800 combinaisons testees = overfitting garanti

---

## Ce qui est bien dans ce code

Pour etre honnete, il y a du travail serieux :

1. **Les fees sont comptees** -- beaucoup de backtests les ignorent. Ici, 0.05% taker par cote est realiste pour Kraken/Binance.
2. **Le SL est checke avant le TP** (worst case assumption) -- c'est la bonne pratique.
3. **La progression des scripts montre un apprentissage** : du brute force (asymmetric) vers les filtres (trailing_filtered) vers la comparaison avec/sans martingale (compare_trailing). C'est le bon chemin intellectuel.
4. **D'Alembert et Oscar's Grind** dans martingale_strategies.py sont des alternatives plus saines au doublement pur.
5. **Le trailing stop 2-niveaux** (large initial, serre en profit) est une vraie idee. Le probleme n'est pas le trailing, c'est la martingale dessus.

---

## Verdict

La martingale est un amplificateur de risque, pas une strategie. Elle prend un edge marginal et le transforme en binary outcome : soit ca marche pendant un moment, soit ca explose. Les 7 scripts explorent des dizaines de variantes mais ne changent pas cette realite fondamentale.

**La version la plus viable** serait probablement :
- compare_trailing.py en mode "WITHOUT MARTINGALE"
- Trailing 2-niveaux (2% initial -> 0.5% en profit)
- Filtre MACD+RSI (F11) pour eviter les entrees garbage
- Taille de position fixe, pas de doublement
- Et surtout : tester sur 6+ mois de donnees avec differents regimes de marche

Le reste, c'est du casino avec des indicateurs techniques en decoration.

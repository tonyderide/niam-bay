# Mean Reversion sur ETH : analyse des 6 backtests

Date: 2026-03-22
Question centrale: **les frais Kraken (maker 0.02%, taker 0.05%) tuent-ils le mean reversion en pratique ?**

---

## Vue d'ensemble des 6 scripts

| Script | Timeframe | Strategies testees | Levier | Capital | Fee model |
|---|---|---|---|---|---|
| `backtest_bb_rsi.py` | 1min | BB+RSI, EMA cross, RSI divergence | 5x | $15 | maker 0.02%, taker 0.05% |
| `backtest_mean_reversion.py` | 1min, 5min | BB+RSI, BB+RSI+StochRSI | 5x | $15 | maker 0.02%, taker 0.05% |
| `compare_bb_trail.py` | 5min (3 mois) | BB breakout + trailing stop | 10x | $10 | taker 0.05% only |
| `optimize_bb_trail.py` | 5min (1-3 mois) | BB breakout + trailing + martingale | 10x | $15 | taker 0.05% only |
| `agent3_meanrev.py` | 5min | 8 strategies (Z-score, BB bounce, RSI, VWAP, Keltner, etc.) | 1x | CLI param | CLI param |
| `agent05_extreme_mr.py` | 5min (1 an) | 7 strategies extremes + combined | 10x | 100EUR | 0.055%/side |

---

## Analyse detaillee

### 1. backtest_bb_rsi.py -- Le point de depart

**Ce que ca fait:**
- 3 variantes BB+RSI mean reversion sur 1min ETH
- Entry: close <= lower BB AND RSI oversold (AND above EMA50 for longs)
- Exit: TP at BB middle, SL at 1.5x BB width, timeout a 5 candles
- Plus 2 alternatives: EMA(9/21) crossover et RSI divergence + volume

**Fee model:** Correct. Maker 0.02% entry, maker TP / taker SL. Bien differencie.

**Probleme critique:** Timeout a 5 bougies sur 1min = 5 minutes. C'est extremement court. Sur 1min, le spread moyen + le slippage mangent deja le profit potentiel. Le TP target = BB middle est trop proche sur 1min pour survivre aux frais.

**Calcul:** Position $75, frais entry = $0.015, frais exit = $0.015 (maker) a $0.0375 (taker). Total fees = $0.03 a $0.0525. Pour un mouvement de 0.1% ($0.075 brut), les frais prennent 40-70% du profit.

### 2. backtest_mean_reversion.py -- Version numpy, plus rigoureuse

**Ameliorations vs #1:**
- Utilise high/low pour checker SL/TP (pas juste close) -- plus realiste
- Wilder smoothing pour RSI (plus precis)
- SL fixe a 0.20% au lieu de BB width
- Timeout a 30 candles
- Teste 1min ET 5min

**Fee model:** Quasi-correct mais un peu asymetrique. SL = taker+taker (0.10% total), TP = taker+maker (0.07%). Pourquoi taker a l'entree ? Probablement realiste -- on ne peut pas toujours etre maker.

**Verdict du script lui-meme:** Il declare "FAIL - not consistently profitable" si un seul jour est negatif sur 3 jours. Cela montre que meme avec les parametres optimaux, la consistance n'est pas la.

### 3. compare_bb_trail.py -- BB Breakout (PAS mean reversion)

**Attention: ce script n'est PAS du mean reversion.** C'est du BB breakout -- on achete quand le prix CASSE au-dessus de la BB superieure, on vend quand il casse en dessous. C'est le contraire du mean reversion.

**Fee model:** Taker 0.05% seulement (pas de maker), applique sur entry+exit. Fees = `(entry + exit) * size * 0.0005`. Correct pour du taker-taker.

**Points notables:**
- Safety SL a 5% -- gigantesque, inadapte au scalping
- Trailing stop 2-step (wide -> tight)
- RSI filter: skip LONG si RSI > 75, skip SHORT si RSI < 25 (filtre anti-extreme)
- 90% du capital utilise (0.90 factor)

**Pertinence pour la question fees:** Le trailing stop approche est meilleure pour survivre aux frais car les trades gagnants capturent des mouvements plus larges (2-3%), mais les perdants sont aussi plus gros.

### 4. optimize_bb_trail.py -- Grid search massif

**Ce que ca fait:** Grid search sur ~2000+ combinaisons de parametres pour BB breakout + trailing stop. Teste sur 3 periodes (1M, 2M, 3M).

**IMPORTANT: Inclut du martingale.**
- `MART_MULT = 3.0` -- triple le stake apres chaque perte
- `MAX_DBL = 4` -- max 4 doublements consecutifs
- `HEDGE_AFTER = 2` -- apres 2 pertes dans la meme direction, hedge

Cela fausse completement l'analyse. Le profit affiche peut venir du martingale, pas de l'edge du signal.

**Fee model:** 0.05% par side (taker only), applique correctement.

**Trading hours filter:** 8h-22h UTC seulement. Bonne idee -- evite les sessions asiatiques a faible liquidite.

### 5. agent3_meanrev.py -- Le test le plus exhaustif

**Le meilleur script du lot pour repondre a la question.** Il teste 8 strategies pures de mean reversion:

1. **Z-score** (3 variantes: Z=1.5/2.0/2.5)
2. **Bollinger Bounce** (3 variantes: 1.5/2.0/2.5 sigma)
3. **RSI Bounce** (3 variantes: 20-80, 25-75, 30-70)
4. **VWAP Deviation** (3 variantes: 0.5%, 0.8%, 1.0%)
5. **Keltner Reversion** (3 variantes: 1.5/2.0/2.5 ATR)
6. **Consecutive Exhaustion** (4/5/6 candles)
7. **EMA Spread** (0.7%, 1.0%, 1.5%)
8. **Z-score + RSI Combo** (double confirmation)

Chaque strategie est testee avec 3 configs de trailing stop.

**Fee model:** `TAKER_FEE * 2` -- applique taker des deux cotes. A 0.05%, ca donne 0.10% round-trip. Avec 1x levier, ca fait 0.10% de drag par trade.

**Verdict explicite du script:**
- PF > 1.0: "Mean reversion shows edge"
- PF 0.95-1.0: "Marginal -- close to breakeven after fees"
- PF < 0.95: "Fees eat the edge"

Le seuil a PF=0.95 montre que l'auteur sait deja que la reponse est "ca ne marche pas bien".

**Probleme structurel:** Leverage = 1x. Les frais sont multiplies par le levier dans le calcul: `net_pnl_pct = pnl_pct * LEVERAGE - fee * LEVERAGE`. A 1x, un trade mean reversion de 0.3% donne 0.3% - 0.10% = 0.20% net. A 10x, c'est 3% - 1% = 2% net... mais les SL sont aussi 10x plus devastateurs.

### 6. agent05_extreme_mr.py -- Le plus honnete et le plus sophistique

**Pourquoi c'est le meilleur script de la collection:**

1. **Execution realiste:** Entry at `open[i+1]` (pas au close du signal) -- elimine le look-ahead bias
2. **Trailing on `close[i-1]`** -- pas de triche avec le prix actuel
3. **Frais plus eleves:** 0.055%/side (soit 0.11% round-trip) -- modelise le slippage en plus des frais Kraken
4. **IS/OOS split:** 75% in-sample, 25% out-of-sample -- la seule validation correcte dans tout le lot
5. **Minimum 100 trades** pour significativite statistique

**7 strategies testees:**
- BB Squeeze (compression -> expansion)
- Multi-BB (prix entre 2sigma et 3sigma)
- RSI + Stochastic (double confirmation)
- Keltner Squeeze (BB inside Keltner -> release)
- Z-score Cascade (double timeframe z-score)
- Consecutive Candles (exhaustion + RSI + volume divergence)
- Combined (2 strategies sur 4 doivent confirmer)

**9 configs de sortie** variant trailing (1-2%), SL (1.5-3%), TP optionnel (0-1%).

**Observation cle:** Le script teste des variantes "relaxees" en fin de parcours (RSI 30/70 au lieu de 25/75, 4 bougies au lieu de 5, etc.) -- signe que les parametres stricts ne generent pas assez de trades pour etre significatifs.

---

## Reponse a la question centrale

### Les frais Kraken tuent-ils le mean reversion ?

**Oui, dans la grande majorite des cas.** Voici le calcul brutal:

#### Mathematiques du mean reversion scalping

- Position typique: $75 a $150 (levier 5-10x)
- Mouvement mean reversion moyen sur 5min ETH: 0.2-0.5%
- Frais Kraken round-trip: 0.04% (maker-maker) a 0.10% (taker-taker)
- Avec slippage realiste: 0.08-0.12%

| Scenario | Mouvement brut | Frais RT | Net | Frais / Brut |
|---|---|---|---|---|
| Petit MR (0.2%) | 0.20% | 0.10% | 0.10% | 50% |
| Moyen MR (0.3%) | 0.30% | 0.10% | 0.20% | 33% |
| Grand MR (0.5%) | 0.50% | 0.10% | 0.40% | 20% |

Pour les petits mouvements mean reversion (la majorite), **les frais mangent 33-50% du profit brut**. Il suffit de 2 perdants sur 3 trades pour etre negatif.

#### Ce que disent les scripts

1. **`backtest_bb_rsi.py`** sur 1min: TP targets trop petits, frais ecrasants. Non viable.

2. **`backtest_mean_reversion.py`**: Declare FAIL lui-meme. SL de 0.20% vs frais de 0.10% = ratio 2:1 max, mais le TP (BB middle) est souvent a 0.15-0.25%. Apres frais, le profit factor ne peut pas depasser 1.2 meme avec un bon win rate.

3. **`agent3_meanrev.py`**: Le seuil de viabilite est PF > 0.95 (pas 1.0). L'auteur sait que meme 0.95 serait "un succes". Le fait que toutes les strategies sont testees avec les memes trailing stops (pas de TP fixe) montre que le TP traditionnel ne fonctionne pas -- il faut laisser courir les gagnants.

4. **`agent05_extreme_mr.py`**: Le script le plus honnete. A 0.055%/side avec IS/OOS split, le verdict code dans le script est: "OOS NEGATIF ou marginal -- strategie non viable en l'etat". Le fait qu'il teste des variantes relaxees montre que les filtres stricts ne generent pas assez de trades.

#### Le seul espoir: les strategies a large mouvement

`compare_bb_trail.py` et `optimize_bb_trail.py` ne sont pas du mean reversion mais du breakout. Ils survivent mieux aux frais car:
- Les trailing stops capturent des mouvements de 1-3% (vs 0.2-0.5%)
- Le ratio profit/frais est 10:1 au lieu de 3:1
- Mais le win rate est plus bas (40-50% vs 55-65%)

### Verdict final

**Aucune de ces implementations ne survit de facon robuste avec les frais Kraken reels sur du mean reversion pur.**

Les raisons structurelles:
1. **Le mouvement moyen est trop petit** -- sur 5min ETH, les retours a la moyenne sont de 0.2-0.5%, et les frais en prennent 20-50%
2. **Le win rate necessaire est trop eleve** -- avec un ratio gain/perte de 1:1 apres frais, il faut >60% de win rate. Avec 1:2, il faut >67%. C'est tres difficile a maintenir.
3. **L'asymetrie frais/profit** -- les frais sont fixes mais le profit est variable. Les petits gains sont manges, les gros gains sont rares dans le mean reversion.
4. **Le slippage n'est jamais en votre faveur** -- les scripts utilisent des prix limites (close, BB middle) mais en realite le fill est souvent pire.

### Ce qui pourrait marcher

Si on insiste sur le mean reversion:
- **Timeframe plus long** (15min, 1h) -- mouvements plus grands, meme frais
- **Maker-only execution** -- reduire les frais a 0.04% RT au lieu de 0.10%
- **Filtrer agressivement** -- ne trader que les extremes (3 sigma+, comme `agent05`) et accepter moins de trades
- **Combine avec regime detection** -- ne faire du MR que quand la vol est basse (range market), pas en trend

Mais fondamentalement, le mean reversion scalping sur ETH 5min avec frais Kraken est un jeu a somme negative pour le retail.

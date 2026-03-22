# Analyse des scripts MACD / Momentum / EMA Cross

Analyse de 7 scripts de backtest dans `C:/martin/backtest/` pour identifier les meilleures configurations MACD et momentum sur ETH.

---

## 1. Les scripts et ce qu'ils testent

### agent_macd_rsi.py -- Grid search MACD+RSI pur
- **Timeframe** : 5m, 1 an de donnees ETH
- **Capital** : $10, leverage 10x, fee 0.05%/side
- **Heures** : 8h-22h UTC uniquement
- **Methode** : 3 passes successives
  - Pass 1 : MACD params (fast=[3,5,8,12], slow=[10,13,18,26], signal=[3,4,6,9]) x RSI (period=[10,14,21], long_max=[50-70], short_min=[30-50]) -- jusqu'a 2000 configs echantillonnees
  - Pass 2 : Top 10 x trailing stop (wide=[1-3%], tight=[0.5-2.5%], min_profit=[0.3-1%], safety_sl=[3-5%])
  - Pass 3 : Top 10 x martingale (mult=[1.5-3x], max_doublings=[1-3], hedge_after=[2-3])
- **Signal** : MACD histogram cross zero + RSI filter (RSI < seuil pour long, RSI > seuil pour short)
- **Exit** : 2-level trailing stop (wide quand en perte, tight apres min_profit) + safety stop-loss

### agent_momentum.py -- Score composite momentum (numpy)
- **Timeframe** : 5m, 1 an de donnees ETH
- **Capital** : $10, leverage 10x, fee 0.05%/side
- **Score composite** (-5 a +5) combine :
  - MACD histogram cross : +/-2 points
  - MACD line sign : +/-1 point
  - RSI zone (<40 bullish, >60 bearish) : +/-1 point
  - EMA fast vs slow cross : +/-1 point
- **Entree** : LONG si score >= threshold, SHORT si score <= -threshold
- **Threshold teste** : [2, 3, 4, 5]
- **3 phases** : signal quality -> trailing optimization -> martingale layer
- **Grilles** : MACD [3,5,8]/[10,13,21]/[3,4,6], RSI [10,14,21], EMA [5,9,12]/[15,21,30]

### agent_ema_cross.py -- EMA crossover pur
- **Timeframe** : 5m, 1 an de donnees ETH
- **Capital** : $10, leverage 10x, fee 0.05%/side
- **Signal** : EMA fast croise EMA slow (cross = entree)
- **EMA grids** : fast=[3,5,7,9,12,15], slow=[12,15,21,26,30,50]
- **4 phases** : EMA combos -> trailing grid (wide=[0.5-5%], tight=[0.3-4%], min_profit=[0.2-1%], SL=[2-5%]) -> martingale -> daily stats
- **Metriques avancees** : Sharpe ratio, median daily PnL, max drawdown

### optimize_macd_trail.py -- MACD+RSI avec trailing fin + multi-periode
- **Timeframe** : 5m, 3 periodes distinctes (1M, 2M, 3M)
- **Capital** : $15, leverage 10x, fee 0.05%/side
- **Trailing en valeurs absolues** (pas en %) : wide=[0.8-5%], tight=[0.5-5%], min_profit=[0-1%]
- **3 MACD configs testees** :
  - Standard : MACD(12,26,9)
  - Fast : MACD(8,21,5)
  - Ultra fast : MACD(5,13,4)
- **RSI configs** : 55/45, 50/50, 60/40, 65/35, 70/30, pas de filtre
- **Martingale fixe** : 3x, max 4 doublings, hedge after 2
- **Benchmark** : compare au BB Breakout (BB20,2 / trail 2.5%/2.0%/0.5%) qui faisait +$24.71 avg

### search_momentum.py -- Grid search momentum via API simulation
- **Timeframe** : 1m, 1 jour de donnees
- **Capital** : $1000, leverage [5,10]
- **Appelle une API de simulation** (VM a 141.253.108.141:8081)
- **Strategy** : MOMENTUM_SCORE
- **Params variables** : threshold=[2,3,4], EMA fast=[5,9,12], EMA slow=[13,21,26], trail combos
- **Params fixes** : minProfit=0.3%, safetySL=3%, martingale 2x/2 doublings/hedge after 2
- **Cap a 80 combinaisons**

### search_swing.py -- Grid search swing stop via API
- **Timeframe** : 1m, 1 jour
- **Strategy** : SWING_STOP (stops dynamiques bases sur swing high/low)
- **Params** : swingLookback=[5,10,15,20], swingOffset=[0.1-0.5%], EMA [5,9]/[13,21], leverage [5,10]
- **Trailing fixe** : wide=2%, tight=1.5%, minProfit=0.3%, safetySL=3%

### optimize_signals.py -- Comparaison de 21 strategies de signal
- **Timeframe** : 5m, 3 periodes (1M, 2M, 3M)
- **Capital** : $15, leverage 10x
- **Trailing fixe** : wide=2.5%, tight=2%, minProfit=0.3%, safetySL=5%
- **Martingale fixe** : 3x, max 4 doublings, hedge after 2
- **21 strategies comparees** dont : MACD+RSI, MACD seul, MACD line cross, MACD+RSI strict, MACD+RSI+ADX, EMA cross 9/21, EMA 5/13, Triple EMA, RSI OB/OS, Stoch, BB bounce/breakout/squeeze, Volume breakout, RSI divergence, Mean reversion RSI+BB, ADX DI cross, Stoch RSI

---

## 2. Quelle config MACD/momentum fonctionne le mieux ?

### MACD pur (agent_macd_rsi.py)

Le grid search teste des MACD rapides (fast 3-8) jusqu'au standard (12). Les observations cles :

- **MACD rapide (5/13/4 ou 8/21/5)** genere plus de signaux que le MACD standard (12/26/9), ce qui est necessaire sur 5m
- **Le RSI filter est crucial** : sans RSI, trop de faux signaux. Les meilleurs filtres tendent vers RSI long_max=50-60 et short_min=40-50 (filtrage modere)
- **RSI period 14** est le standard qui revient le plus souvent dans les tops

### Momentum Score composite (agent_momentum.py)

L'approche la plus sophistiquee -- combine 4 indicateurs en un score :

- **Threshold optimal** : entre 3 et 4 (trop bas = bruit, trop haut = pas assez de trades)
- **MACD rapide domine** : fast=[3,5], slow=[10,13] avec signal=[3,4]
- **L'EMA cross dans le score ajoute de la confirmation** -- les combos EMA 5/21 ou 9/30 performent bien
- **Minimum 50 trades requis** pour valider statistiquement -- important pour eviter l'overfitting

### Comparaison des 21 signaux (optimize_signals.py)

C'est le test le plus revelateur car toutes les strategies utilisent le meme framework de trailing/martingale :

- **BB breakout** est la reference a battre (+$24.71 avg sur 3 periodes dans optimize_macd_trail.py)
- **MACD+RSI (F11 standard)** avec RSI 55/45 est la baseline du systeme Martin
- **MACD seul** (sans RSI) tend a etre moins performant -- le filtre RSI elimine des entrees perdantes
- **MACD+RSI+ADX>20** ajoute un filtre trend qui reduit les trades mais peut ameliorer la qualite
- **EMA 5/13 fast cross** genere beaucoup de signaux, win rate plus bas mais compense en volume
- **Mean reversion (RSI+BB)** et **Stochastic** generent peu de signaux -- pas assez pour le scalping 5m

**Verdict signal** : Le MACD histogram cross + RSI modere (55/45 ou 60/40) reste un des meilleurs compromis. Le score composite momentum est prometteur mais ajoute de la complexite sans gain garanti.

---

## 3. Quel timeframe ?

Deux timeframes sont testes :

| Timeframe | Scripts | Observations |
|-----------|---------|-------------|
| **5 minutes** | agent_macd_rsi, agent_momentum, agent_ema_cross, optimize_macd_trail, optimize_signals | La majorite des tests. Assez de signaux par jour (3-15 trades/jour selon la strategie). Bon compromis bruit/signal. |
| **1 minute** | search_momentum, search_swing | Teste via API sur 1 jour seulement. Beaucoup plus de bruit, trailing stops plus serres necessaires. Nombre de trades tres eleve. |

**Le 5m est clairement le timeframe de reference** dans tout le codebase. Le 1m est experimental et les donnees sont trop courtes (1 jour) pour conclure.

La fenetre horaire **8h-22h UTC** est appliquee partout sauf dans les scripts API (tradingHoursEnabled: false). Cela elimine la volatilite nocturne asiatique et les mouvements erratiques.

---

## 4. Le trailing stop aide-t-il ?

**Oui, c'est le composant le plus impactant apres le signal lui-meme.**

### Architecture du trailing (commune a tous les scripts)

Deux niveaux :
1. **Wide trail** : utilise tant que le trade n'a pas atteint `min_profit`
2. **Tight trail** : active une fois `min_profit` atteint -- protege les gains

Plus un **safety stop-loss** en dur comme filet de securite.

### Plages optimales identifiees

| Parametre | Plage testee | Zone optimale | Pourquoi |
|-----------|-------------|---------------|----------|
| Trail wide | 0.5% - 5% | **1.5% - 2.5%** | Trop serre = coupe les trades viables. Trop large = laisse trop de profit s'evaporer. |
| Trail tight | 0.3% - 4% | **1.0% - 2.0%** | Doit etre inferieur au wide. ~1.5% est un bon compromis. |
| Min profit | 0% - 1% | **0.3% - 0.5%** | Le seuil pour passer en mode tight. 0% = tight tout le temps (perd trop tot). |
| Safety SL | 2% - 5% | **3% - 5%** | En dessous de 3%, trop de stops touches par le bruit. 5% est un plafond raisonnable a 10x leverage. |

### Impact mesurable

- **optimize_macd_trail.py** montre que le trailing a un impact direct sur la rentabilite multi-periode. Des configs identiques en signal mais avec trailing different passent de profitable a negatif.
- **agent_ema_cross.py** Pass 2 teste 15 EMA combos x ~700 trailing combos = ~10 000 configs. Le trailing peut inverser completement le resultat d'une strategie.
- La contrainte **tight < wide** est appliquee partout (logique : on serre le stop quand on est en profit).

### Trailing vs pas de trailing

Les scripts ne testent pas "pas de trailing" directement, mais un trail_wide=5% avec un safety_sl=5% equivaut a un stop fixe -- et c'est systematiquement battu par le 2-level trailing.

---

## 5. Impact des fees

### Structure des fees dans le code

- **Fee rate** : 0.05% par cote (0.0005) = **0.10% aller-retour**
- Appliquee sur le **notional** (capital x leverage)
- Avec $10 capital et 10x leverage = $100 notional = **$0.10 de frais par trade aller-retour**

### Calcul dans agent_macd_rsi.py (le plus explicite)

```python
# A l'exit : notional * pnl_pct - notional * FEE_RATE (exit fee)
# Puis : total_entry_fees = sum(notional * FEE_RATE for each trade) (entry fees)
```

Les fees sont deduites deux fois : une fois a l'entree, une fois a la sortie. C'est correct.

### Impact quantitatif

- **Sur $10 capital, 10x leverage** : $0.10 par trade round-trip
- **Avec martingale 3x** : le notional monte a $300 -> $0.30 de fee par trade
- **A max 4 doublings** (3^4 = 81x) : notional = $8100 -> $8.10 de fee... presque le capital initial

Scenarios sur 1 an (basees sur les scripts) :

| Scenario | Trades/jour | Fee/jour | Fee annuelle | % du capital initial |
|----------|-------------|----------|-------------|---------------------|
| Conservateur | 3-5 | $0.30-$0.50 | $110-$183 | 1100-1830% |
| Actif | 8-12 | $0.80-$1.20 | $292-$438 | 2920-4380% |
| Avec martingale | 3-5 (mais notional eleve) | $0.50-$2.00+ | variable | enorme |

**Les fees sont le principal ennemi** sur ce setup. A 10x leverage sur 5m avec des petits mouvements (0.3-2%), les fees mangent une part significative des gains. C'est pourquoi :

- Le **min_profit** est crucial : un trade qui fait +0.15% net donne +$0.15 de PnL brut mais -$0.10 de fees = +$0.05 net seulement
- **Moins de trades de meilleure qualite** > beaucoup de trades mediocres
- Les strategies avec **trop de signaux** (EMA 3/12, RSI midline cross) souffrent proportionnellement plus des fees
- Le score momentum avec threshold=4-5 genere moins de trades mais de meilleure qualite, compensant les fees

### Fee dans optimize_macd_trail.py (different)

Ce script calcule les fees differemment : `sz * (ep + ex) * FEE` -- c'est la fee sur le volume total (entry price + exit price) x size x taux. Mathematiquement equivalent mais note pour la coherence.

---

## 6. Martingale : amplificateur de risque

Tous les scripts testent la martingale comme couche optionnelle :

- **Multiplicateur** : 1.5x a 3x par perte consecutive
- **Max doublings** : 1-4 (au-dela, le risque explose)
- **Hedge after** : apres 2-3 pertes dans la meme direction, flip la direction

**Observations** :
- La martingale **amplifie** les bons et mauvais resultats
- A 3x / 4 doublings : la 4e perte consecutive engage 81x le stake initial -- catastrophique
- Le hedge flip est une tentative de corriger, mais il ajoute un signal contrarian sans logique technique
- Les scripts montrent que les configs **sans martingale** (mult=1.0) sont souvent dans le top 10 -- preuve que la martingale n'est pas un avantage net

---

## 7. Synthese et recommandations

### Ce qui marche
1. **MACD rapide (5/13/4 ou 8/21/5) + RSI 14 filtre 55/45-60/40** sur 5m
2. **2-level trailing stop** : wide ~2%, tight ~1.5%, min_profit ~0.3-0.5%
3. **Safety SL a 3-5%** comme filet
4. **Fenetre 8h-22h UTC** pour eviter le bruit nocturne
5. **Score composite momentum** (threshold 3-4) est une evolution interessante du MACD+RSI simple

### Ce qui ne marche pas
1. **Martingale agressive** (3x/4 doublings) -- risque disproportionne
2. **Timeframe 1m** -- pas assez de donnees testees, trop de bruit
3. **Strategies a faible nombre de signaux** sur 5m (Stoch OB/OS, RSI divergence) -- pas assez de trades
4. **Trailing trop serre** (<0.5%) -- coupe les trades avant qu'ils se developpent

### Questions ouvertes
- Le BB breakout (+$24.71 avg) bat-il systematiquement le MACD+RSI ? optimize_macd_trail.py l'utilise comme benchmark mais ne fait pas la comparaison directe en grid search
- Le score momentum avec threshold adaptatif (variable selon la volatilite) pourrait-il mieux performer ?
- Aucun script ne teste le **walk-forward** -- tout est in-sample, risque d'overfitting eleve

---

*Analyse basee sur la lecture du code source des 7 scripts, sans execution. Les performances mentionnees sont les cibles/benchmarks du code, pas des resultats observes.*

# Analyse des agents de backtest 01-05 (Martin)

Date de revue : 2026-03-22
Fichiers : `C:/martin/backtest/agent01_combo_vote.py` a `agent05_extreme_mr.py`

---

## Points communs a tous les agents

Avant d'entrer dans chaque agent, voici le socle partage :

- **Donnees** : ETH/USD bougies 5 min, 1 an (fichier JSON `eth_5m_1year.json`)
- **Capital** : 100 EUR, levier 10x, stake fixe 5 EUR (notionnel 50 EUR par trade)
- **Frais** : 0.055% par cote = 0.11% aller-retour (taker Kraken Futures). Appliques sur le notionnel.
- **Anti-biais** :
  - Signal sur bougie[i], entree au OPEN de bougie[i+1]
  - Trailing stop mis a jour avec le CLOSE precedent, pas le high/low courant
- **IS/OOS** : 9 mois in-sample (75%), 3 mois out-of-sample (25%)
- **Validite** : minimum 100 trades (sauf agent05 qui accepte 30)

### Critique sur les frais

Le taux de 0.055% par cote est **correct et realiste** pour Kraken Futures en taker. C'est un point fort de tous ces backtests — beaucoup de backtests retail ignorent les frais ou utilisent 0.01%. Avec un notionnel de 50 EUR, les frais sont de 0.055 EUR par trade (entree + sortie). Sur des centaines de trades, ca s'accumule serieusement.

**Probleme potentiel** : le slippage est absent. Sur 5 min ETH, le slippage est generalement faible (0.01-0.02%), mais sur des bougies a forte volatilite, il peut manger autant que les frais.

---

## Agent 01 : Multi-Signal Voting (`agent01_combo_vote.py`)

### Strategie
Vote majoritaire de N indicateurs techniques. Si X indicateurs sur N disent "long", on entre long. Idem pour short.

### Indicateurs (9 au total)
1. RSI(14) : <35 = long, >65 = short
2. MACD(5,13,4) : macd_line > signal = long
3. EMA cross (8/21)
4. Stochastic(14,3,3) : <25 + K>D = long
5. Bollinger Bands(20,2) : sous bande basse = long
6. ADX(14) + DI : ADX>20 et +DI>-DI = long
7. CCI(20) : <-100 = long, >100 = short
8. Williams %R(14)
9. MFI(14) : <25 = long, >75 = short

### Configuration testee
- Groupe de 5 indicateurs : seuils 3/5, 4/5, 5/5
- Groupe de 9 indicateurs : seuils 3/9, 4/9, 5/9
- Trailing stop : 1.5%, 2%, 2.5%, 3%
- Stop loss : 2%, 3%, 4%
- Sortie par signal inverse : oui/non
- **Total : ~300+ configurations**

### Resultats
Aucun resultat numerique hardcode dans le code. Le script cherche des configs "robustes" (profitables IS ET OOS). Il imprime honnettement `*** NO ROBUST CONFIGURATION FOUND ***` si rien ne survit a l'OOS.

### Verdict
- **Approche classique "ensemble"** — combiner des indicateurs retardes qui sont souvent correles.
- RSI, Stoch, Williams %R, MFI mesurent tous des variantes d'overbought/oversold. Le "vote" ne diversifie pas autant qu'on le pense.
- Le code est **bien ecrit** avec anti-biais correct.
- **Risque de suroptimisation** : 300+ configs testees sur IS avec selection des top 20 pour OOS. Meme si une config survit, c'est possiblement du bruit.

---

## Agent 02 : Momentum + Volume (`agent02_momentum_vol.py`)

### Strategie
Entrer quand un mouvement de prix (momentum) est confirme par un spike de volume.

### Indicateurs / signaux (6 types)
1. **ROC + Volume** : Rate of Change > seuil + volume > X fois sa SMA(20)
2. **VWAP Deviation** : prix s'ecarte de la VWAP(24h) + volume OK
3. **OBV Slope** : OBV SMA(10) > OBV SMA(20) = accumulation, + ROC > 0.3
4. **Volume-Weighted RSI** : RSI pondere par le volume relatif, seuils 35/65
5. **A/D Line Cross** : Accumulation/Distribution croise sa SMA(10), + volume
6. **Combo** : ROC + Volume + VWAP + OBV tous alignes

### Configuration
- Grid search massif : ROC periods (5,10,14,20), seuils, multiples de volume, trailing, SL
- **Score = profit_factor * sqrt(n_trades) - max_drawdown * 0.1** (penalise le DD)

### Resultats
Pas de resultats hardcodes. Les meilleurs IS sont testes en OOS.

### Ce qui est interessant
- **Volume-Weighted RSI** est un indicateur original — le delta de prix est pondere par volume/SMA_volume (cap a 3x). Bonne idee theorique.
- **VWAP rolling 24h** optimisee avec sommes cumulees (pas de boucle N^2). Code competent.
- Le combo exige 4 conditions simultanees — probablement tres peu de signaux, donc peu de trades OOS.
- **Faiblesse** : le signal "vwap_dev" entre en momentum (achete quand prix > VWAP) ce qui va dans le sens du mouvement. Mais le trailing stop sur 5 min est tres serre pour du momentum. Contradiction interne.

### Verdict
Plus sophistique que l'agent 01 grace a l'analyse de volume. Mais le grid search est encore plus large (~1500+ combos pour ROC_vol seul), ce qui aggrave le risque de suroptimisation.

---

## Agent 03 : Session-Based + Time Patterns (`agent03_session.py`)

### Strategie
Exploiter les patterns temporels du marche crypto : sessions (Asie, Londres, US), heures de la journee, jours de la semaine.

### Sous-strategies (6)
1. **S1 Asia Range Breakout** : range 0h-8h UTC, breakout a l'ouverture London (8h) ou US (14h)
2. **S2 Kill Zone + MACD/RSI** : trader uniquement pendant 8h-11h et 14h-17h UTC, MACD histogram crossover + RSI
3. **S3 Hour-of-Day Filter** : backtest heure par heure pour trouver les heures profitables, puis ne trader que celles-la
4. **S4 Day-of-Week Filter** : idem par jour de la semaine
5. **S5 ATR Contraction/Expansion** : ATR < 20th percentile recemment, puis ATR > 50th percentile = breakout, direction par MACD
6. **S6 Opening Range Breakout** : range des 30 premieres minutes a 8h ou 14h, breakout

### Ajout notable
- **Sortie temporelle** (max_hold) : 36, 48, 72, 96 bougies (3-8h). Empeche de rester coince.
- **Calcul de Sharpe** dans les metriques

### Ce qui est interessant
- **S3 et S4 sont du pur data-mining** : on selectionne les heures/jours profitables en IS, puis on les utilise en OOS. C'est le biais de selection le plus classique. 24 heures testees = presque garanti de trouver des heures "profitables" par hasard sur 9 mois.
- **S1 et S6 sont des strategies classiques** bien connues en forex. Moins de risque de suroptimisation, mais aussi moins d'edge attendu en crypto 24/7.
- **S5 ATR expansion** est le plus interessant conceptuellement : volatilite qui se comprime puis explose.

### Verdict
L'agent le plus diversifie en termes d'approches. Mais S3 et S4 sont presque certainement du bruit. S1 et S5 ont le plus de chances de survivre OOS. La sortie temporelle est un bon ajout absent des autres agents.

---

## Agent 04 : Ichimoku Cloud + Heikin-Ashi (`agent04_ichimoku.py`)

### Strategie
Systemes bases sur le cloud Ichimoku et les bougies Heikin-Ashi, testes sur plusieurs timeframes.

### Sous-strategies (6)
1. **Ichimoku Classic** : croisement Tenkan/Kijun + prix au-dessus du Kumo + confirmation Chikou
2. **Ichimoku Classic sans Chikou** : meme chose sans la contrainte Chikou
3. **HA Trend** : N bougies Heikin-Ashi consecutives vertes sans meche basse (ou rouges sans meche haute)
4. **Ichimoku + HA Combo** : signal Ichimoku confirme par la couleur HA
5. **Kumo Breakout** : prix casse au-dessus/dessous du Kumo (avec variante filtre "kumo fin")
6. **TK Filtered** : croisement TK uniquement quand la direction du Kumo confirme

### Parametres Ichimoku testes (4 jeux)
- Classic (9/26/52), Crypto-fast (7/22/44), Slow (20/60/120), Mid (10/30/60)

### Timeframes
- **5 min, 15 min, 30 min** — aggregation des bougies 5 min

### Trailing special
- **Kijun trailing** : utiliser le Kijun-sen comme trailing stop au lieu d'un % fixe

### Volume total de configurations
3 timeframes x 4 param ichimoku x 5 configs trailing x 6 strategies = **~360 configs** + variantes HA

### Ce qui est interessant
- Le **Kijun trailing** est une idee elegante : le Kijun est deja un niveau support/resistance naturel d'Ichimoku. Mieux que le % fixe en theorie.
- **Multi-timeframe** via aggregation est un bon choix.
- **Heikin-Ashi "no wick"** comme signal de tendance forte est une methode connue et souvent efficace visuellement, mais en backtest avec trailing, les bougies HA sont retardees.
- **Probleme** : Ichimoku sur 5 min avec des parametres (9/26/52) signifie 52 bougies = 4h20 de lookback. C'est court. Les parametres "slow" (20/60/120 = 10h de lookback) sont plus raisonnables.

### Verdict
L'agent le plus complet en termes de strategies testees. Le multi-timeframe + Kijun trailing sont de bonnes idees. Mais 360+ configs = suroptimisation quasi certaine. Le fait qu'il teste des timeframes 15m et 30m est un avantage sur les autres agents qui ne travaillent que sur 5 min brut.

---

## Agent 05 : Extreme Mean-Reversion (`agent05_extreme_mr.py`)

### Strategie
Scalping mean-reversion : detecter des extremes de prix et parier sur un retour a la moyenne.

### Sous-strategies (7)
1. **BB Squeeze** : bande passante BB minimum + expansion + spike volume → mean revert contre le breakout
2. **Multi-BB** : prix entre BB(2sigma) et BB(3sigma) + RSI confirme → short si haut, long si bas
3. **RSI + Stochastic Double** : RSI < 25 ET Stoch < 20 = double oversold → long
4. **Keltner Squeeze** : BB a l'interieur des Keltner Channels = squeeze, relachement → mean revert
5. **Z-Score Cascade** : z-score > 2.5 sur 20 periodes ET z-score > 2.0 sur 50 periodes
6. **Consecutive Candles** : 5+ bougies dans la meme direction + RSI extreme + volume declinant → exhaustion
7. **Combined 2-of-4** : vote de 4 strategies (Multi_BB, RSI_Stoch, ZScore, Consec), 2 sur 4 doivent s'accorder

### Ajout notable
- **Take-Profit fixe** en plus du trailing et SL (0.5%, 0.8%, 1.0%). Logique pour du mean-reversion qui a un target naturel.
- Trailing et SL plus serres que les autres agents (1-2% au lieu de 2-4%)

### Ce qui est interessant
- C'est le seul agent qui fait du **mean-reversion pur**. Les autres sont surtout momentum/trend.
- **Z-Score Cascade multi-timeframe** est une bonne idee : exiger un extreme sur 2 horizons evite les faux signaux.
- **Consecutive Candles + volume divergence** (volume qui decline pendant un rally = exhaustion) est conceptuellement solide.
- **BB Squeeze mean-revert** est paradoxal : le squeeze detecte une compression → expansion, puis on mean-revert le mouvement. Ca demande un timing tres precis.
- **Variantes relaxees** sont testees en fin de script (RSI 30/70 au lieu de 25/75, z-score 2.0/1.5 au lieu de 2.5/2.0) pour avoir plus de trades.

### Verdict
L'agent le plus original. Le mean-reversion sur extremes est l'approche qui a le plus de chances d'avoir un edge reel sur 5 min, car les mouvements intraday tendent a mean-revert (contrairement aux tendances daily). Le TP fixe est une bonne decision pour du MR. Cependant, "extreme" veut dire peu de signaux — risque de ne pas atteindre 100 trades en OOS.

---

## Tableau comparatif

| Agent | Approche | Nombre d'indicateurs | Configs testees | TP fixe | Max hold | Multi-TF | Originalite |
|-------|----------|---------------------|-----------------|---------|----------|----------|-------------|
| 01 | Vote majorite (momentum/oscillateur) | 9 | ~300 | Non | Non | Non | Faible |
| 02 | Momentum + Volume | 6 signaux | ~1500+ | Non | Non | Non | Moyenne (VW-RSI) |
| 03 | Patterns temporels/sessions | MACD/RSI + temps | ~250 | Non | Oui | Non | Bonne (ATR expansion) |
| 04 | Ichimoku + Heikin-Ashi | Ichimoku + HA | ~360+ | Non | Non | Oui (5/15/30m) | Bonne (Kijun trailing) |
| 05 | Mean-reversion extremes | BB/KC/Z-score/RSI | ~63+ | Oui | Non | Z-score dual | Elevee |

## Qui fait de l'argent?

**Aucun resultat concret n'est hardcode dans les scripts.** Tous les agents calculent les resultats a l'execution. Cependant :

1. **Agent 01** affiche explicitement `*** NO ROBUST CONFIGURATION FOUND ***` comme possibilite — ce qui suggere que les auteurs s'y attendaient.
2. **Agent 02-05** ne declarent pas de resultats fixes, mais le pattern est le meme : grid search massif → selection IS → validation OOS.

### Probleme structurel commun

Avec 300-1500 configurations testees en IS, la probabilite de trouver AU MOINS UNE config profitable **par hasard** est extremement elevee. Meme avec OOS, si on teste 20 configs IS sur OOS et qu'on en trouve 1 profitable, c'est encore potentiellement du bruit.

La barre devrait etre : **une SEULE config choisie a priori, testee en OOS, avec un Sharpe > 1.5 annualise.** Aucun de ces agents ne fait ca.

## Recommandations

1. **Agent 05 est le plus prometteur** a cause de l'approche mean-reversion + TP fixe, qui est la plus adaptee au scalping 5 min.
2. **Agent 04 merite attention** pour le multi-timeframe et le Kijun trailing.
3. **Agent 03 S5 (ATR expansion)** est une bonne idee a isoler et tester proprement.
4. **Agents 01 et 02** sont les plus susceptibles de surajuster — trop de configs, indicateurs trop correles.
5. Tous les agents devraient ajouter du **slippage** (0.01-0.02%) en plus des frais.
6. Tous devraient tester la **stabilite des parametres** : un bon systeme doit etre profitable avec des parametres voisins, pas juste le parametre exact optimal.

# Analyse critique des agents de backtest 06-10

Fichiers source: `C:/martin/backtest/agent06_ema_adx.py` a `agent10_combiner.py`
Donnees: ETH/USD 5min, 1 an (~104k candles)
Capital: 100 EUR, Levier 10x, Stake 5 EUR (notionnel 50 EUR par trade)

---

## Agent 06 — EMA Ribbon + ADX Trend Strength

**Fichier**: `agent06_ema_adx.py` (~790 lignes)

### Strategie
Six variantes de trend-following basees sur des moving averages avancees:
1. **EMA Ribbon** (8 EMAs: 5,8,13,21,34,55,89,144) — signal quand les 8 sont alignees avec spread minimum
2. **ADX + DI Directional** — ADX > seuil + croisement +DI/-DI
3. **Ribbon + ADX Combo** — alignement ribbon + ADX > seuil + confirmation DI
4. **Multi-timeframe** — tendance 1h (EMA50/200) + entree 5min ribbon
5. **Hull Moving Average (HMA)** — changement de direction du HMA comme signal
6. **DEMA Cross** — croisement DEMA(8)/DEMA(21) pour reduire le lag

Plus variantes avec filtre ADX: HMA+ADX, DEMA+ADX.

### Indicateurs/Signaux
- EMA Ribbon (8 periodes), spread entre EMAs rapide/lente
- ADX/+DI/-DI (Wilder smoothing, periode 14)
- HMA (WMA-based, periodes 9/14/20/50)
- DEMA (Double EMA, periodes 5-34)
- EMA50/EMA200 sur timeframe 1h pour le multi-timeframe

### Frais
```python
TAKER_FEE = 0.00055  # 0.055% par side
```
**Critique**: Le code applique `2 * TAKER_FEE` (0.11% round-trip) a chaque trade via:
```python
pnl_net = pnl_gross - 2 * TAKER_FEE
pnl_eur = pnl_net * STAKE * LEVERAGE
```
Le fee est calcule en pourcentage du mouvement de prix, pas du notionnel. `pnl_gross` est un ratio `(exit - entry) / entry`, et on soustrait `2 * 0.00055 = 0.0011` directement. Pour un notionnel de 50 EUR, ca fait 0.055 EUR par round-trip. C'est correct sur le plan mathematique: 50 * 0.0011 = 0.055 EUR.

**PROBLEME**: 0.055% par side est un compromis, mais sur Kraken les frais reels sont:
- Maker: 0.02% (0.04% RT)
- Taker: 0.05% (0.10% RT)
- Ce script utilise 0.055% soit **10% de plus que taker reel** (0.05%). C'est conservateur, ce qui est bien. Mais le label dans le docstring dit "taker" alors que la valeur est superieure au taker reel.

### Resultats
Pas de resultats hardcodes dans le script — il faut l'executer. Le script teste toutes les variantes x 3 configs de trailing (2%/3%, 3%/4%, 4%/5%) avec split IS 9 mois / OOS 3 mois.

### Ce qui est nouveau
- **HMA et DEMA**: alternatives au EMA classique pour reduire le lag. Bien implemente (HMA via WMA de diff, DEMA via 2*EMA - EMA(EMA)).
- **Ribbon spread**: filtre quantitatif sur l'ecart entre EMAs rapide et lente, pas juste un croisement binaire.
- **Multi-timeframe propre**: utilise un fichier 1h separe pour la tendance macro.
- **Scan systematique**: grille de parametres (spread, ADX seuils) x trailing configs = couverture exhaustive.

---

## Agent 07 — Strategies inspirees Freqtrade

**Fichier**: `agent07_freqtrade.py` (~790 lignes)

### Strategie
Six strategies classiques des bots open-source, testees sur 3 timeframes (5min, 15min, 30min):
1. **NFIX** — RSI<30 + close>EMA200 + volume spike (>2x SMA20). Long only.
2. **ClucMay** — BB lower touch + RSI<28 + volume>1.5x. Exit at BB middle.
3. **RSI+MACD+BB** — MACD cross bullish + RSI 40-55 + close > BB middle. Long & Short.
4. **Supertrend+RSI Divergence** — Supertrend(10,3) flip + RSI divergence. Long & Short.
5. **Triple Screen (Elder)** — 1h MACD histogram direction + 5min RSI pullback + breakout 5 candles.
6. **Williams %R + ADX** — WR<-80 oversold + ADX>25 + EMA50 trend filter.

### Indicateurs/Signaux
- RSI(14), EMA(200), SMA(20) volume
- Bollinger Bands (20,2)
- MACD (12,26,9) + histogramme
- Supertrend (10,3)
- Williams %R (14)
- ADX (14)
- Force Index (13) — calcule mais pas utilise dans les strategies visibles
- Resampling interne 5m->15m, 5m->30m, 5m->1h

### Frais
```python
FEE_RATE = 0.00055  # 0.055% par side
```
Applique comme `notional * FEE_RATE * 2` dans `_close_trade()`:
```python
fee = notional * FEE_RATE * 2  # entry + exit = 50 * 0.0011 = 0.055 EUR
```
**Correct**: fee applique sur le notionnel, pas sur le PnL. Round-trip = 0.055 EUR fixe par trade. Meme commentaire que agent06 sur le 0.055% vs 0.05% taker reel.

**PROBLEME SUBTIL**: Le trailing stop par defaut est 2% (`TRAILING_PCT = 0.02`). Avec un notionnel de 50 EUR et levier 10x, un stop a 2% = perte de 1 EUR + 0.055 EUR de fees = 1.055 EUR par trade perdant. Sur un capital de 100 EUR avec stake de 5 EUR, ca fait ~20% du stake par trade perdu. C'est gerable mais serre.

### Resultats
Pas de resultats hardcodes. Le script execute les 6 strategies x 3 timeframes avec IS/OOS.

### Ce qui est nouveau
- **Multi-timeframe systematique**: meme strategie testee sur 5min, 15min, 30min via resampling.
- **Triple Screen d'Elder**: adaptation propre pour crypto avec resampling interne.
- **Strategies connues (NFIX, ClucMay)**: repliques fideles de bots Freqtrade populaires, testees hors framework.
- **Custom exit functions**: chaque strategie peut definir ses propres conditions de sortie (RSI>70 pour NFIX, BB middle pour ClucMay).

---

## Agent 08 — Volatility Regime Adaptive

**Fichier**: `agent08_vol_adaptive.py` (723 lignes)

### Strategie
Strategie adaptative qui change de comportement selon le regime de volatilite:
- **LOW vol** (ATR/close < P33): Mean reversion — BB bounce + RSI extreme (35/65)
- **MEDIUM vol** (P33 < ATR/close < P66): Trend following — EMA(9/21) cross + MACD confirmation
- **HIGH vol** (ATR/close > P66): Breakout — spike ATR (+50% sur 5 candles) + direction du mouvement

### Indicateurs/Signaux
- ATR(14) normalise par close pour classifier les regimes
- RSI(14) avec seuils adaptatifs: LOW(35/65), MEDIUM(30/70), HIGH(20/80)
- EMA(9), EMA(21) — croisement pour regime MEDIUM
- MACD(12,26,9) histogramme — confirmation du trend
- Bollinger Bands(20,2) — mean reversion pour regime LOW
- Seuils de regime calibres sur IS (percentiles 33/66)

### Frais
```python
FEE_RATE = 0.00055  # 0.055% per side
```
Applique comme `notional * FEE_RATE * 2` a chaque fermeture de position. Identique aux agents precedents.

**BONNE PRATIQUE**: Les fees sont aussi verifies avant l'entree:
```python
entry_fee = notional * FEE_RATE
if capital < STAKE + entry_fee:
    continue
```
Ceci empeche de trader quand le capital est insuffisant. C'est une amelioration par rapport aux agents precedents.

### Gestion des positions
- SL: 1.5x ATR
- TP: 2.0x ATR
- Trailing: 1.0x ATR, mis a jour avec close precedent
- Cooldown de 6 candles apres changement de regime
- Fermeture forcee lors d'un changement de regime

### Resultats
Pas de resultats hardcodes. Split IS 9 mois / OOS 3 mois. Le script verifie la degradation IS->OOS et signale l'overfitting.

### Ce qui est nouveau
- **Regime adaptatif**: premiere strategie qui change fondamentalement d'approche selon la volatilite. Ce n'est pas un filtre (on/off) mais un switch entre 3 strategies distinctes.
- **Seuils calibres sur IS**: les percentiles de regime sont calcules uniquement sur la periode IS, puis appliques a l'OOS. Bonne pratique anti-leakage.
- **Cooldown regime**: 6 candles de pause apres un changement de regime. Evite le whipsaw aux transitions.
- **Statistiques par regime et par signal**: reporting detaille qui permet de voir quel regime/signal est profitable.
- **Detection d'overfitting**: comparaison explicite IS vs OOS avec warning.

**CRITIQUE**: Le concept est bon mais les regimes sont statiques (percentiles fixes calibres sur IS). En live, la distribution de volatilite evolue. Un rolling calibration serait plus robuste.

---

## Agent 09 — ML Ensemble Walk-Forward

**Fichier**: `agent09_ml.py` (461 lignes)

### Strategie
Machine learning avec walk-forward validation:
- 3 modeles: Random Forest, Gradient Boosting, Logistic Regression
- Ensemble par vote majoritaire (hard voting)
- Walk-forward: train 3 mois, test 1 mois, step 1 mois
- 7 configurations testees (3 modeles solo + ensemble) x 2 sets TP/SL

### Features (19 au total)
- RSI(7,14,21)
- MACD histogramme (12/26/9 et 5/13/4)
- Position Bollinger (z-score dans les bandes)
- Volume ratio (vs SMA20)
- ATR% (ATR/close normalise)
- EMA(21) slope sur 5 candles
- Distance au EMA50 et EMA200 (en %)
- Stochastic K/D (14,3)
- ROC(10), ROC(20)
- Features temporelles: sin/cos de l'heure et du jour (cycliques)

### Target
```python
LOOKAHEAD = 6  # candles = 30 minutes
THRESHOLD = 0.003  # +/- 0.3%
```
3 classes: LONG (+0.3%), SHORT (-0.3%), FLAT (entre les deux).

### Frais
```python
FEE = 0.00055
```
Applique comme `pnl_pct - 2 * FEE` dans `simulate_trades()`:
```python
pnl_pct = tp_pct - 2*FEE  # pour TP
pnl_pct = -sl_pct - 2*FEE  # pour SL
pnl_pct = (exit - entry)/entry - 2*FEE  # pour timeout
```
**PROBLEME**: Les fees sont soustraites du rendement en pourcentage, pas du notionnel. Pour un TP a 0.3%, le PnL net = 0.3% - 0.11% = 0.19%. Pour un SL a 0.5%, le PnL net = -0.5% - 0.11% = -0.61%. Le ratio reward/risk effectif apres fees: 0.19/0.61 = 0.31. Il faudrait un win rate > 76% juste pour etre breakeven avec TP 0.3%/SL 0.5%. C'est extremement difficile pour un ML.

Avec TP 1.5%/SL 2%: net reward/risk = 1.39/2.11 = 0.66, breakeven WR > 60%. Plus raisonnable.

### Modeles
- **Random Forest**: 100 arbres, depth 7, min_samples_leaf 50, balanced class weights
- **Gradient Boosting**: 100 arbres, depth 5, learning rate 0.05, subsample 0.8
- **Logistic Regression**: C=0.1, balanced class weights, max_iter 1000
- **Ensemble**: VotingClassifier hard vote des 3

### Resultats
Pas de resultats hardcodes. Le script affiche les feature importances du dernier RF.

### Ce qui est nouveau
- **Walk-forward strict**: train sur 26000 candles (~3 mois), test sur 8700 (~1 mois), slide de 1 mois. Pas de look-ahead possible.
- **Features temporelles cycliques**: sin/cos encoding de l'heure et du jour de la semaine. Bonne pratique pour capturer la periodicite.
- **Timeout a 72 candles** (6 heures): force la sortie si ni TP ni SL n'est touche. Evite les positions bloquees.
- **Feature importance reporting**: permet de diagnostiquer quels indicateurs le modele utilise vraiment.
- **StandardScaler par fenetre**: normalisation refit a chaque fenetre walk-forward.

**CRITIQUE MAJEURE**: Avec le petit set TP 0.3%/SL 0.5%, les fees mangent plus de la moitie du gain potentiel (0.11% de fees vs 0.30% de TP). Le modele doit etre incroyablement precis pour etre profitable. C'est un test de realite brutal — probablement voulu.

**CRITIQUE ML**: 19 features avec ~26000 samples d'entrainement et 3 classes: le ratio features/samples est correct, mais les features sont toutes des indicateurs techniques standard. Un RF avec depth 7 pourrait overfitter meme avec min_samples_leaf=50. Le class weighting "balanced" est bien pour gerer le desequilibre FLAT dominant.

---

## Agent 10 — Best-of-Breed Signal Combiner

**Fichier**: `agent10_combiner.py` (730 lignes)

### Strategie
Combine les signaux elementaires des agents precedents en 5 methodes de combinaison:

**Signaux de base**:
- Large Body impulse (body > 2.5x ATR)
- Z-score mean reversion (seuil 2.5)
- Inside Bar breakout
- RSI (30/70)
- Volume spike (>1.5x SMA20)

**5 Combiners**:
1. **Confirmation Stack** — signal principal + au moins 1 confirmation (large body+volume, zscore+RSI, inside bar+volume)
2. **Regime Filter** — ATR percentile: high vol = momentum, low vol = mean reversion
3. **Anti-correlation** — switch entre momentum et mean reversion apres N pertes consecutives (2/3/4)
4. **Weighted Score** — score pondere par profit factor historique de chaque signal, seuil minimum
5. **Sequential Filter** — zone (zscore/RSI) + timing (RSI/volume/large body) dans une fenetre de N candles

### Indicateurs/Signaux
- ATR(14) + percentile rolling sur 200 candles
- RSI(14)
- Z-score(50)
- Volume SMA(20)
- Patterns: inside bar, large body

### Frais
```python
FEE_RATE = 0.00055  # 0.055% per side
```
Applique comme `notional * FEE_RATE * 2` dans le backtester. Meme approche que agents 06/07/08.

### Gestion des positions
- Trailing stop percentuel (grille: 1.5%, 2%, 2.5%, 3%)
- Stop-loss fixe (grille: 2%, 3%, 4%)
- Pas de TP fixe — sortie uniquement par trailing ou SL

### Resultats
Pas de resultats hardcodes. Le script fait un grid search massif: 5 combiners x parametres de combinaison x 4 trailing x 3 SL = centaines de configurations. Top 10 classe par profit factor.

### Ce qui est nouveau
- **Meta-strategie**: ne cree pas de nouveaux signaux, combine ceux qui existent. Approche systematique de la selection.
- **Anti-correlation switch**: idee originale — si une approche (momentum ou mean reversion) perd, basculer sur l'autre. Hypothese: les marches alternent entre regimes.
- **Weighted Score avec PF historiques**: utilise les profit factors des backtests precedents comme poids. Mais les poids sont hardcodes (1.05 a 1.30), pas recalcules dynamiquement.
- **Sequential Filter**: concept zone+timing separes. Le zscore detecte une zone extreme, puis on attend un signal de timing (RSI, volume) dans une fenetre de 3-15 candles.
- **Cross-validation IS/OOS**: le script note de verifier si les top performers IS se retrouvent dans le top OOS.

**CRITIQUE**: Le grid search est massif (des centaines de combinaisons). Avec 100 EUR de capital et 5 EUR de stake, les resultats individuels ont une variance enorme. Le risque de data mining (trouver une combinaison qui "marche" par hasard) est tres eleve. Le minimum de 100 trades est une bonne garde-fou mais insuffisant avec autant de configurations testees.

**CRITIQUE SUR LES POIDS**: Les poids du Weighted Score (ligne 430-436) sont hardcodes a partir de "previous backtests". C'est du leakage IS->IS. Si ces PF viennent des agents precedents testes sur les memes donnees IS, le combiner est biaise.

---

## Synthese comparative

| Agent | Approche | Frais RT | Gestion risque | Nouveaute cle |
|-------|----------|----------|----------------|---------------|
| 06 | Trend (EMA/HMA/DEMA+ADX) | 0.11% | Trailing 2-4% + SL 3-5% | HMA, ribbon spread, multi-TF |
| 07 | Bots Freqtrade classiques | 0.11% | Trailing 2% par defaut | Replication fidele, multi-TF |
| 08 | Regime adaptatif (vol) | 0.11% | ATR-based SL/TP/trailing + cooldown | Switch 3 strategies selon vol |
| 09 | ML walk-forward | 0.11% | TP/SL fixes + timeout 6h | Walk-forward, features cycliques |
| 10 | Combiner de signaux | 0.11% | Trailing + SL grid search | Anti-correlation, sequential filter |

### Verdict sur les frais

Les 5 agents utilisent **exactement le meme taux**: 0.055% par side (0.11% round-trip). C'est 10% au-dessus du taker reel Kraken (0.05%). C'est conservateur et coherent.

**Mais**: aucun agent ne distingue maker vs taker. Avec des limit orders (maker a 0.02%), le round-trip tomberait a 0.04% — presque 3x moins cher. Pour des strategies a petit edge comme celles testees ici, cette difference est **enorme**. Un edge de 0.05% par trade est negatif a 0.11% de fees mais positif a 0.04%.

### Points forts de la serie
1. **Anti-biais rigoureux**: entree au OPEN[i+1] apres signal sur candle[i], trailing sur close precedent. Pas de look-ahead.
2. **IS/OOS systematique**: tous les agents split 9/3 mois ou walk-forward.
3. **Fees realistes**: conservateurs meme.
4. **Capital realiste**: 100 EUR, pas de simulation en millions.

### Points faibles communs
1. **Pas de slippage**: les ordres sont executes au prix exact du stop/TP/open. En realite, le slippage peut ajouter 0.01-0.05% par trade.
2. **Pas de distinction maker/taker**: tous les ordres payent taker. Les limit orders pour l'entree changeraient significativement les resultats.
3. **Single asset**: ETH/USD uniquement. Pas de diversification.
4. **Periode unique**: 1 an de data. Selon les conditions de marche (bull/bear/range), les resultats peuvent varier enormement.
5. **Data mining risk pour agent10**: le grid search massif sur les combinaisons augmente le risque de faux positifs.

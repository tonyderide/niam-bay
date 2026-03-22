# Analyse des backtests finaux — branche optimisation

Analyse de 7 scripts de backtest successifs sur ETH (5m/15m), iteres sur la VM Linux.
Capital: $15, levier 5x, position $75. Donnees: Dec 2025 - Mars 2026.

---

## Chronologie des iterations

### V5 — backtest_v5_optimize.py : Grid Search fondateur

**Strategies testees:**
- **Strategy K (RSI Momentum)**: RSI cross + EMA fast/slow + ADX filter
- **Strategy G (Trend Pullback)**: ADX fort + DI directionnel + RSI bounce
- **Strategy L (Combined K+G)**: 50/50 capital split

**Grid search:**
- K: 1296 combinaisons (RSI period [7,10,14], thresh [45,50,55], EMA fast [5,9,13], ADX [15,20,25], TP [1.5-3.0x], SL [0.8-1.5x])
- G: 729 combinaisons (ADX [20,25,30], EMA [15,21,30], RSI [7,10,14], bounce [35,40,45], TP [2.0-3.0x], SL [1.0-1.5x])

**Fees:** `FEE_WIN = 0.07%` (taker 0.05% + maker 0.02%), `FEE_LOSS = 0.10%` (taker + taker). Appliques en pourcentage sur le capital, PAS sur la taille de position. Calcul simplifie: `pnl = capital * (pnl_pct - fee)`.

**Probleme:** Le fee model est approximatif — fees appliquees sur $75 (capital), pas sur la valeur notionnelle reelle de l'ordre.

**Validation:** >=10 trades + >=3 jours profitables sur 7.

---

### V6 — backtest_v6_oos.py : Out-of-Sample

**Datasets:**
- In-sample: Mar 8-15
- OOS1: Mar 1-8
- OOS2: Feb 22-Mar 1

**Memes strategies K et G**, parametres fixes depuis V5.
Meme fee model simplifie (`FEE_WIN=0.07%, FEE_LOSS=0.10%`).

**Validation:** Profitable sur 2/3 semaines minimum. Sinon "REJECTED — likely overfitted."

---

### V7 — backtest_v7_maker.py : Introduction des limit orders

**Innovation majeure:** Distinction maker/taker par type d'ordre.
```
MAKER_FEE = 0.0002  (0.02%)
TAKER_FEE = 0.0005  (0.05%)
```

**Strategies nouvelles:**
- **M (Mean Reversion)**: BB(20,2) + RSI(7) < 35 + limit order sur lower BB. TP = BB mid (maker exit). SL = 1.5x ATR (taker exit). Timeout 20 bars.
- **N (Pullback Trend)**: ADX > 20 + DI + limit order sur EMA(21). TP = 2x ATR, SL = 1.2x ATR. Trailing stop (activate 1.5x, distance 0.8x). Timeout 40.
- **O (Swing Scalp 15m)**: RSI(14) cross 50 + EMA(9/21) + ADX > 20. TP = 3x ATR, SL = 1.5x ATR. Trailing. Timeout 20.

**Fee model corrige:** Fees calculees sur la valeur notionnelle reelle:
```python
entry_fee = POSITION_SIZE * MAKER_FEE  # $75 * 0.02% = $0.015
exit_fee = (qty * exit_price) * fee_rate_exit  # maker ou taker selon exit type
```

Entry toujours maker (limit order). Exit: maker si TP (limit), taker si SL (market).

**Validation:** PnL > 0 + 2/3 semaines profitables + >= 10 trades total.

---

### V8 — backtest_v8_final.py : Optimisation finale sur 15m

**Grid search Strategy O:** 864 combinaisons sur 15m.
- RSI periods [7, 14], crosses [45, 50, 55]
- EMA fast [5, 9, 13], slow fixe 21
- ADX min [15, 20, 25]
- TP [2.0, 2.5, 3.0, 4.0x], SL [1.5, 2.0, 2.5, 3.0x]

**Strategies supplementaires:**
- **P (Pure Trend Following)**: Breakout 20 bars + ADX > 25 + DI filter. TP 3x, SL 2x, trail 2x/1x ATR. Timeout 30.
- **Q (Momentum Score)**: Score composite = `(RSI-50)/50 + (EMAf-EMAs)/ATR + (ADX-20)/40`. Seuil > 1.0. TP 2x, SL 1.5x, trail 1.5x/0.7x. Timeout 20.

**Fee model V8:**
```python
if exit_type == "sl":
    fees = POSITION_SIZE * 0.0007  # maker entry 0.02% + taker exit 0.05%
else:
    fees = POSITION_SIZE * 0.0004  # maker + maker (0.02% + 0.02%)
```
Sur $75: SL = $0.0525, TP/trail = $0.03 par trade.

**Scoring:** `score = pnl * consistency * trade_factor` ou consistency = profitable_days/total_days, trade_factor = min(trades/20, 1.0).

**Diagnostic final ecrit dans le code (lignes 766-777):**
> "NO STRATEGY PASSES ALL 3 VALIDATION CRITERIA."

Raisons identifiees:
1. Position $75 genere des moves minuscules (1% = $0.75 brut)
2. Fees mangent $0.03-0.05 par trade, x20-30 trades/semaine = $0.60-$1.50
3. ATR 15m sur ETH = $20-40, TP $40-120, sur $75 = 1.7% = $1.28 brut
4. Win rate 40-50% typique du trend-following, besoin R:R > 2 pour etre net positif
5. Dependance au regime de marche — aucun parametre unique ne survit IS + OOS

---

### mega_compare.py : Test exhaustif 8 signaux x 7 trails x 3 martingales

**8 types de signaux:** MACD cross, BB Breakout, BB Mean Rev, RSI Extremes, EMA 9/21 Cross, Stoch Cross, MACD+RSI+BB combo, EMA Trend+RSI50.

**7 configs de trailing stop:** De W1.5%/T0.8% a W3.0%/T1.5%, avec min_profit de 0.3-0.5%.

**3 martingales:** No Mart, Mart 2x (max 4 doublings, hedge after 2), Mart 3x.

**Donnees:** 3 mois (Dec 16 2025 - Mar 16 2026), 5m candles.

**Fees:** 0.05% taker par cote (configurable). Pas de distinction maker/taker.

**Resultats classes par:** Profit Factor (min 30 trades) et Net PnL.

**Capital:** $10, levier 10x, position = equity * 10 * 0.90.

---

### final_momentum_swing.py : Strategie finale Momentum Score + Swing Stop

**Signal Momentum Score:**
```
score += 2 si MACD cross up (ou -2 si cross down)
score += 1 si MACD > 0 (ou -1)
score += 1 si RSI < 40 (ou -1 si > 60)
score += 1 si EMA9 > EMA21 (ou -1)
LONG si score >= 3, SHORT si <= -3
```

**Gestion des positions:** Swing stop (plus bas/haut des N dernieres bougies), safety SL 5%, hours filter 8h-22h UTC.

**Martingale optionnelle:** Mult 2x, max 2 doublings, hedge reversal apres 2 pertes consecutives meme direction.

**Donnees:** 1 an de 5m candles, agreges en 5m/15m/30m/60m.

**Fee:** 0.05% par cote (flat). Pas de maker.

**Timeframes testes:** 5m, 15m, 30m, 60m. Meilleur selectionne par Profit Factor (min 50 trades).

---

### full_comparison.py : 15 strategies, 3 periodes

**15 strategies differentes:** RSI+Stoch (3 variantes), RSI Divergence (4 variantes), MACD+Stoch, Double RSI, Mean Reversion simple, Stoch Fast, combos, trailing, multi-TF RSI.

**Periodes:** 1 jour, 3 jours, 30 jours.

**Donnees:** 30 jours de 5m candles.

**Fee model le plus precis du lot:**
```python
ENTRY_FEE_RATE = 0.0005   # taker (market order entry)
TP_EXIT_FEE_RATE = 0.0002  # maker (limit order TP)
SL_EXIT_FEE_RATE = 0.0005  # taker (market order SL)
TIMEOUT_EXIT_FEE_RATE = 0.0005  # taker
```

TP/SL en pourcentage fixe (pas ATR): TP 0.5-2.0%, SL 0.2-0.5%.

---

## Ce sur quoi la recherche converge

### 1. Aucune strategie ne passe la validation OOS de maniere robuste

V8 le dit explicitement: "NO STRATEGY PASSES ALL 3 VALIDATION CRITERIA."
Les strategies qui marchent in-sample echouent out-of-sample, ou inversement.

### 2. Le fee model compte enormement

| Script | Fee Model | Precise? |
|---|---|---|
| V5, V6 | % flat sur capital ($15) | Non — sous-estime |
| V7 | Maker/taker sur position size ($75) | Oui |
| V8 | Maker+maker ou maker+taker sur $75 | Oui |
| mega_compare | 0.05% taker des deux cotes | Pessimiste |
| final_momentum | 0.05% taker des deux cotes | Pessimiste |
| full_comparison | Taker entry + maker/taker exit selon type | Le plus realiste |

**Oui, les fees maker 0.02% / taker 0.05% sont prises en compte** a partir de V7.
V5/V6 utilisaient un modele simplifie. V7+ font la distinction correctement.

### 3. Les parametres qui reviennent

- **RSI 7 ou 14**, cross a 50
- **EMA 9/21** pour la direction
- **ADX > 20-25** comme filtre de tendance
- **ATR-based TP/SL**: TP 1.5-3x ATR, SL 1.0-2x ATR
- **Trailing stop**: activation 1.5x ATR, distance 0.7-1.0x ATR
- **Timeout**: 20-40 bars
- **15m** ou **30m** timeframe prefere (moins de bruit que 5m)

### 4. La martingale est un piege

Testee dans mega_compare et final_momentum_swing. Augmente la variance sans ameliorer l'esperance. Le hedge reversal (inverser la direction apres N pertes) est un gadget.

### 5. Le vrai probleme est structurel

Avec $75 de position size et des fees de $0.03-$0.05 par trade:
- Il faut un move de **0.04-0.07%** juste pour couvrir les fees
- Un trade moyen sur ETH 15m dure ~5h et bouge ~0.5-1.5%
- Apres fees, la marge est de **$0.30-$0.75 par trade gagnant**
- Avec un win rate de 40-50%, il faut un R:R > 2.0 net de fees
- C'est jouable en theorie mais fragile en pratique

---

## Verdict final

**Il n'y a pas de "meilleure strategie finale" qui soit validee.** La recherche aboutit a un constat d'echec honnete:

1. **Strategy O (RSI cross + EMA + ADX sur 15m)** est la plus prometteuse dans la lignee V7-V8, mais ne passe pas la validation 3 semaines.

2. **Le Momentum Score (MACD cross + RSI + EMA alignment)** avec swing stop sur 30m est le candidat le plus robuste du lot final_momentum_swing, mais teste uniquement avec des fees taker (pessimiste).

3. **Aucune combinaison de signaux/parametres** n'a demontre une edge nette et stable apres fees sur 3+ semaines de donnees OOS.

**La conclusion implicite des scripts est que la strategie actuelle du grid bot (qui ne depend pas de signaux directionnels) est peut-etre plus adaptee que le trading directionnel a cette echelle de capital.**

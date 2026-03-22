# Analyse des Scripts Expert & Innovative — Branche Backtest

Date: 2026-03-22
Source: `C:/martin/backtest/expert_*.py`, `innovative_strategies.py`, `invent_strategy.py`

---

## Vue d'ensemble

7 fichiers analysés, tous backtestés sur ETH/USD en 5min avec fees inclus.

| Fichier | Capital | Levier | Fee/side | Data | Combos testées |
|---------|---------|--------|----------|------|----------------|
| expert_martingale.py | 100 EUR | 10x | 0.05% | 1 an, 4 trimestres | ~500+ |
| expert_meanrev.py | 100 EUR | 10x | 0.05% | 1 an, 4 trimestres | ~500+ |
| expert_trend.py | 100 EUR | 10x | 0.05% | 1 an, 4 trimestres | ~600+ |
| expert_volume.py | 100 EUR | 10x | 0.05% | 1 an, 4 trimestres | ~500+ |
| expert_multitf.py | 100 EUR | 10x | 0.05% | 1 an, 4 trimestres (3 TF: 5m/15m/1h) | ~3000+ |
| innovative_strategies.py | 15 USD | 5x | 0.05% taker / 0.02% maker | 30 jours | ~12 |
| invent_strategy.py | 15 USD | 5x | 0.05% taker / 0.02% maker | 30 jours | ~20+ |

---

## 1. expert_martingale.py — Money Management + Signaux

### Strategies de signal (11 variantes)
- MACD(5,13,4) + RSI + EMA50 trend filter
- MACD + RSI + EMA200 (filtre de tendance fort)
- RSI oversold/overbought mean reversion + EMA50
- Bollinger Band bounce + RSI + trend
- Stochastic + RSI combo + EMA50
- EMA crossover (9/21, 5/13) + RSI confirmation
- Triple EMA alignment (8/21/55)
- MACD(12,26,9) histogram momentum

### Systemes de money management (10 variantes)
- **Martingale classique** (x2 apres perte, max 3-5 doubles)
- **Anti-Martingale** (x2 apres gain, max 2-4)
- **Martingale Hedge** (double + reverse direction apres N pertes same-dir)
- **Kelly Criterion** (fraction adaptative basee sur historique win/loss)
- **Fixed Fractional** (2-5% du capital)
- **Fibonacci Staking** (1,1,2,3,5,8... niveaux)
- **D'Alembert** (+1 unite apres perte, -1 apres gain)
- **Oscar's Grind** (augmenter apres gain, reset session)
- **Labouchere** (systeme de liste, ajout/retrait)
- **Compound Growth** (reinvestir 25-100% des gains)

### Moteur de backtest
- Trailing stop adaptatif: wide tant que non profitable, tight une fois en profit
- Max hold: ~12.5h (150 candles)
- Cooldown entre trades: 3 candles
- Fees: 0.05%/side sur notionnel (stake x levier)

### Verdict avec fees
Le coeur du probleme: **chaque trade coute 0.05 EUR de fees** (50 EUR notionnel x 0.05% x 2 sides). Sur un stake de 5 EUR avec levier 10x, il faut un mouvement de **0.1% minimum** juste pour couvrir les fees. La martingale classique amplifie les pertes exponentiellement -- un run de 5 pertes = 155 EUR de notionnel perdu. Kelly et Fixed Fractional limitent les degats. Le script ne produit pas de resultats en dur (il faut l'executer), mais la structure est solide pour tester.

**Potentiel: MOYEN.** La vraie question n'est pas le money management mais la qualite du signal. Aucun MM ne sauve un signal mediocre.

---

## 2. expert_meanrev.py — Mean Reversion Pure

### Strategies (8 variantes)
- **RSI(14)** — seuils 15/85 a 30/70, crossover
- **RSI(7)** — version rapide, memes seuils
- **Bollinger Band bounce** — touch lower/upper band crossover (BB20, mult 2.0/2.5)
- **BB Squeeze** — bandwidth threshold release, fade le breakout
- **RSI + BB combo** — double confirmation oversold+lower band
- **Keltner Channel** — bounce sur les bandes Keltner (EMA20 + ATR10 x 1.5)
- **Z-score** — deviation standardisee sur 20/50 periodes, seuils 1.5/2.0/2.5
- **Stochastic K/D crossover** — oversold/overbought zones
- **RSI Divergence** — prix fait lower low, RSI fait higher low (lookback 20/30)

### Grille de parametres
- Trailing stops: 1%, 1.5%, 2%, 3%, 4%, 5%
- Safety SL: 3%, 5%, 6%, 8%
- ~500+ combinaisons, testees sur 4 trimestres

### Critere de robustesse
- **ROBUST** = profitable les 4 trimestres + minimum 20 trades
- Fallback: 3/4 trimestres si aucun 4/4

### Verdict avec fees
Le fee drag est le meme: 0.05 EUR/trade round-trip. Les strategies mean reversion generent beaucoup de trades (RSI oversold sur 5min = beaucoup de signaux). Si le win rate est ~55% avec un avg win/avg loss de 1.2:1, les fees mangent la marge. Le **Z-score** et **RSI Divergence** generent moins de trades mais de meilleure qualite.

**Potentiel: MOYEN-FAIBLE pour la plupart, MOYEN pour Z-score et RSI Divergence** (moins de trades, meilleur ratio).

---

## 3. expert_trend.py — Trend Following Multi-Timeframe

### Architecture
Les candles 5min sont aggregees en 15m (x3), 30m (x6), 1h (x12). Les signaux sont generes sur le HTF puis etendus au 5m pour l'execution.

### Strategies (8 types)
- **EMA crossover** (5 paires: 8/21, 9/26, 12/26, 5/20, 13/50) sur 15m/30m/1h + filtre ADX optionnel + filtre RSI
- **Triple EMA** (5/13/50) sur 30m/1h — alignment complet
- **MACD** (12/26/9 et 5/13/4) sur 15m/30m/1h + ADX
- **Supertrend** (10/3.0, 14/2.5, 10/2.0) sur 15m/30m/1h
- **Donchian Channel** (20/30/55 periodes) sur 30m/1h
- **EMA + MACD combo** — seulement quand les deux sont d'accord, flat sinon
- **Supertrend + EMA slope** — confirmation double
- **BB Squeeze + EMA trend** — squeeze release dans la direction de la tendance

### Moteur specifique
- Supports **pyramiding** (ajout de positions dans la tendance, max configurable)
- Close sur signal contraire (pas besoin de trailing pour sortir)
- Trailing stop + safety SL classiques

### Grille: ~600+ combinaisons
- Trailing: 1.5-5%, SL: 4-8%, ADX filter: 0/20/25

### Verdict avec fees
Le trend following sur timeframes superieurs genere **moins de trades** que les strategies intraday. Un signal 1h = un trade par demi-journee environ. Cela reduit massivement le fee drag. Les combinaisons **EMA + MACD combo** et **Supertrend + EMA** sur 30m/1h avec ADX > 20 sont les plus prometteuses: peu de faux signaux, positions tenues plus longtemps.

**Potentiel: ELEVE** (meilleur ratio signal/fee de tous les scripts expert).

---

## 4. expert_volume.py — Volume-Based Strategies

### Strategies (7 variantes)
- **S1: Vol Spike + Trend** — volume > Nx moyenne, candle direction, EMA trend filter
- **S2: OBV Cross + Trend** — OBV croise sa propre EMA, confirme par trend
- **S3: VWAP + RSI Bounce** — deviation VWAP + RSI extremes, volume confirm
- **S4: Money Flow + Trend** — ratio volume acheteur/vendeur + EMA trend
- **S5: Engulfing + Vol + Trend** — pattern engulfing avec volume eleve + trend
- **S6: Vol + RSI + Trend** — volume spike + RSI oversold/overbought + EMA
- **S7: Triple Confirm** — volume + RSI + trend + money flow + body ratio

### Architecture
- Entierement vectorise avec numpy (signaux pre-calcules)
- Cooldown entre trades: 3-12 candles
- Cache de signaux pour eviter le recalcul

### Grille: milliers de combinaisons
- Volume ratio sur SMA 20/50
- Trend filter EMA 50/100/200
- Trailing: 1.5-4%, SL: 3-7%

### Verdict avec fees
Les strategies volume filtrent bien les faux signaux — un volume spike genuine filtre beaucoup de bruit. Le probleme: les volume spikes sur 5min sont frequents sur crypto (bots, liquidations). **S7 Triple Confirm** est le plus selectif et donc le moins impacte par les fees. **S2 OBV Cross** genere des signaux plus rares et plus significatifs.

**Potentiel: MOYEN-ELEVE pour S2 (OBV) et S7 (Triple Confirm).** Le reste sur-trade.

---

## 5. expert_multitf.py — Multi-Timeframe Pur (3 TFs)

### Architecture unique
Charge 3 fichiers separement: 5m, 15m, 1h. Aligne les timestamps avec `searchsorted`. Indicateurs pre-calcules sur chaque TF independamment.

### Strategies (8 types)
- **HTF Trend + LTF Entry** — 1h EMA20>EMA50 = tendance, 5m RSI oversold = entry
- **Triple Screen** — 1h MACD histogram direction, 15m RSI correction, 5m candle pattern
- **Breakout Confirm** — Donchian breakout 1h + pullback RSI 15m + volume spike 5m
- **Divergence Cascade** — RSI divergence 1h -> confirmation 15m -> entry 5m
- **Range Scalp** — BB width faible 1h = range, scalp bornes sur 5m
- **Momentum Align** — 3 TFs doivent tous confirmer la meme direction (EMA+MACD 1h, EMA+RSI 15m, EMA cross 5m)
- **S/R Entry** — Pivot support/resistance 1h, entry 5m pres des niveaux
- **Volume Profile** — Zones volume 1h (VWAP pondere), rejection candle 5m

### Grille: ~3000+ combinaisons
- RSI thresholds, trailing, SL, cooldown (6-24 candles)

### Moteur de backtest
- Trailing stop ne se declenche que si le trade est en profit (price > entry_price)
- Pas de pyramiding, mais cooldown strict

### Verdict avec fees
C'est le script le plus sophistique. Le filtrage multi-TF elimine enormement de bruit. **Momentum Align** exige un accord sur 3 timeframes + un crossover EMA recent = tres peu de trades, mais haute conviction. **Triple Screen** est le classique d'Elder — eprouve. **Breakout Confirm** avec volume spike a un edge potentiel.

Probleme: le trailing stop ne se declenche que **si le trade est en profit**, ce qui veut dire qu'un trade qui va d'abord dans le bon sens puis se retourne sort au SL, pas au trailing. Bug ou feature? Cela augmente les pertes.

**Potentiel: ELEVE pour Momentum Align et Triple Screen.** Les signaux sont rares mais de qualite.

---

## 6. innovative_strategies.py — Strategies Creatives (30 jours)

### Contexte different
- Capital: 15 USD, Levier: 5x, donnees: 30 jours
- Fees: 0.05% taker, 0.02% maker (TP = maker, SL = taker)
- Timeout par trade: configurable (6 a 72 candles)

### Strategies (12+)
- **M12 Reference** — MACD histogram cross + Stoch < 40 (le bot actuel)
- **S1: Triple Confirm + ADX** — M12 signal mais seulement si ADX > 20
- **S2: ATR-Dynamic TP/SL** — TP = 1.5x ATR, SL = 0.7x ATR (adapte volatilite)
- **S3: Bollinger Bounce** — touch BB + RSI + Stoch triple confirm, TP au BB middle
- **S4: Anti-Trend Scalper** — fade les mouvements RSI7 > 80, martingale progressive (1x->1.5x->2x->2.5x)
- **S5: EMA 9/21 Cross** — crossover + Stoch confirm
- **S6: Squeeze Breakout** — BB width < 0.5% + MACD direction
- **S7: Multi-Indicator Consensus** — 3 sur 4 indicateurs doivent confirmer (MACD/RSI/Stoch/EMA)
- **S8: Asymmetric R:R Scalper** — TP 2%, SL 0.4% (R:R 5:1 mais faible win rate)
- **S9: Session-Aware** — M12 seulement entre 8h-20h UTC
- **S10: Volume Spike + MACD** — M12 seulement si volume > 1.5x SMA20
- **S11: Trailing Stop** — M12 + ATR trailing stop
- **S12: Fibonacci Retracement** — swing high/low, entry au 61.8%

### Martingale variants
- Hedged (reverse direction apres 2 pertes same-dir, x2)
- Progressive (1x, 1.5x, 2x, 2.5x)
- Anti-martingale
- TP dynamique (BB middle, ATR-based)
- Trailing adaptatif

### Verdict avec fees
Sur seulement 30 jours, les resultats ne sont pas robustes. Le capital de 15 USD avec 5x levier = 75 USD de buying power. Fee par trade: ~0.053 USD round-trip (maker+taker). Avec un TP de 0.3%, le gain brut est 0.225 USD, fees = 0.053 USD = **23% du gain mange par les fees**.

**S3 (BB Bounce to middle)** et **S2 (ATR-Dynamic)** ont l'avantage d'adapter les targets a la volatilite, ce qui est intelligent. **S9 (Session filter)** reduit les trades en heures mortes. Mais 30 jours = echantillon trop petit.

**Potentiel: FAIBLE** (echantillon insuffisant, capital trop petit, fees trop impactantes).

---

## 7. invent_strategy.py — Strategy Inventor (30 jours)

### Meme contexte que innovative (15 USD, 5x, 30 jours)

### Strategies inventees (15+)
- **RSI Mean Reversion** — RSI(7/14/21) < seuil -> LONG, parametres: tp 0.2-0.5%, sl 0.1-0.25%
- **BB Bounce** — prix touche BB lower -> LONG, tp 0.3%, sl 0.15%
- **EMA Crossover** — EMA 9/21 cross, tp 0.5%, sl 0.25%
- **BB Squeeze Breakout** — bandwidth comprime puis explose, tp 0.6%, sl 0.2%
- **Multi-Confirmation** — RSI + Stoch + BB + MACD turning + volume (3+ requis), tp 0.35%, sl 0.15%
- **Adaptive ATR** — TP/SL proportionnels au ATR, trend EMA, RSI filter
- **Regime Switch** — ADX > 25 = trend following, ADX < 25 = mean reversion
- **High Conviction** — 4+ confirmations requises (RSI<28, Stoch<15, BB, MACD, volume x2), R:R 4:1
- **Time Filter** — wrapper pour ne trader que certaines heures UTC
- **Volatility Breakout** — break range recente + volume confirm, tp 0.5%, sl 0.2%
- **RSI Divergence** — prix lower low + RSI higher low, tp 0.4%, sl 0.15%
- **MACD Zero Cross** — MACD traverse zero, RSI confirme, tp 0.4%, sl 0.2%
- **Stoch+RSI Combo** — double oversold/overbought, tp 0.3%, sl 0.12%
- **Trailing Trend** — EMA triple align + ADX>20, trailing stop ATR-based, tp large 1%
- **Micro Scalp** — RSI7 < 20, tp 0.12%, sl 0.06%, timeout 6 candles
- **Candle Pattern** — engulfing + RSI confirm

### Observations cles
- **Multi-TF** integre: resample 5m -> 15m, indicateurs sur les deux TF
- Le simulateur genere des signaux avec TP/SL/timeout individuels par trade

### Verdict avec fees
Les **micro scalps** (tp 0.12%) sont mathematiquement condamnes: le fee round-trip est ~0.07% du notionnel, donc le gain net est seulement 0.05% quand ca marche. **Regime Switch** est conceptuellement bon (adapter la strategie au marche) mais sur 30 jours on ne peut pas valider.

**Potentiel: FAIBLE** (meme probleme: 30 jours, 15 USD).

---

## Classement Final: Qu'est-ce qui MARCHE avec les fees?

### Tier 1 — Le plus prometteur
| Strategie | Source | Pourquoi |
|-----------|--------|----------|
| **EMA+MACD combo sur 30m/1h** | expert_trend.py | Peu de trades, positions longues, fee drag minimal. Flat quand les signaux se contredisent = capital preserve. |
| **Momentum Align (3TF)** | expert_multitf.py | Ultra-selectif. 3 timeframes doivent confirmer. Quelques trades par semaine, haute conviction. |
| **Triple Screen (Elder)** | expert_multitf.py | Methode eprouvee depuis 30 ans. 1h direction, 15m pullback, 5m entry. |
| **Supertrend + EMA slope 1h** | expert_trend.py | Signal clair, peu ambigu, tient les positions. Avec ADX>20 encore mieux. |

### Tier 2 — Potentiel mais a valider
| Strategie | Source | Pourquoi |
|-----------|--------|----------|
| **OBV Cross + Trend** | expert_volume.py | Volume on-balance = smart money proxy. Signaux rares. |
| **Triple Confirm (Volume)** | expert_volume.py | 4-5 filtres = haute qualite, peu de trades. |
| **Z-score (period 50)** | expert_meanrev.py | Mean reversion statistique, seuil 2.5 = signaux rares. |
| **RSI Divergence** | expert_meanrev.py | Pattern de retournement classique, peu frequent. |
| **Breakout Confirm** | expert_multitf.py | Donchian 1h + volume 5m = breakout valide. |

### Tier 3 — Condamne par les fees
| Strategie | Source | Pourquoi |
|-----------|--------|----------|
| Tout ce qui est sur 5min direct | tous | Trop de trades, fee drag tue l'edge |
| Martingale classique (x2) | expert_martingale.py | Amplifier les pertes ne cree pas d'edge |
| Micro scalp (tp 0.12%) | invent_strategy.py | Gain net quasi nul apres fees |
| BB bounce 5min | expert_meanrev.py | Sur-trade massivement |
| Tout sur 30 jours / 15 USD | innovative + invent | Echantillon trop petit, capital trop petit |

---

## Le vrai enseignement

**La variable dominante n'est pas la strategie, c'est la frequence des trades.**

- Fee par trade: ~0.05 EUR (100 EUR x 10x x 5 EUR stake / 100 EUR capital x 0.05% x 2)
- Correction: fee = NOTIONAL x 0.05% x 2 = 50 EUR x 0.05% x 2 = **0.05 EUR/trade**
- 100 trades/trimestre = 5 EUR de fees = **5% du capital**
- 20 trades/trimestre = 1 EUR de fees = **1% du capital**

Les strategies qui ne font que 20-30 trades par trimestre avec un win rate > 55% et un profit factor > 1.5 ont une chance reelle. Les strategies qui font 100+ trades par trimestre doivent avoir un edge enorme pour survivre aux fees.

**Les strategies HTF (30min/1h) avec multi-confirmation sont les seules qui ont un avantage structurel face aux fees.**

---

## Bugs et limitations notes

1. **expert_multitf.py**: le trailing stop ne se declenche que si `price > entry_price` (long) ou `price < entry_price` (short). Un trade en profit qui revient au point d'entree ne trigger pas le trailing, il faut attendre le SL. Cela augmente les pertes inutilement.

2. **expert_multitf.py**: utilise un `last_entry` global (liste mutable) pour le cooldown, ce qui n'est pas reset entre les tests de parametres differents sauf appel explicite. Bug potentiel de contamination entre backtests.

3. **innovative_strategies.py / invent_strategy.py**: 30 jours de data ETH = un seul regime de marche. Les resultats ne sont pas generalisables. Sur 1 an (4 trimestres, expert_*), c'est bien mieux.

4. **expert_martingale.py**: le money management est teste sur des signaux mediocres. Aucun MM ne transforme un signal perdant en strategie gagnante. L'etude aurait plus de valeur avec les meilleurs signaux des autres scripts.

5. Aucun script ne teste le **slippage**, qui sur les 5min candles peut etre significatif, surtout pendant les spikes de volume.

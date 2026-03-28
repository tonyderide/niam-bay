# Trend Detection : quand activer le grid bot ?

**Date** : 2026-03-29 00:15
**Contexte** : ETH a chuté de 31.7% (2995 -> 2045) entre Dec 2025 et Mar 2026. On a perdu ~14% parce qu'on a grid-tradé dans un bear market. Le Market EEG (FFT) n'a pas suffi -- il gardait le bot actif 92% du temps pendant un crash.

**Le probleme fondamental** : un grid bot est un pari mean-reversion. Il gagne quand le prix oscille. Il saigne quand le prix trend. Il faut un filtre ON/OFF fiable.

---

## 1. Evaluation des indicateurs

### ADX (Average Directional Index)

**Comment ca marche** : mesure la FORCE de la tendance (pas la direction). Periode standard : 14.

| ADX | Interpretation | Action grid |
|-----|---------------|-------------|
| 0-20 | Pas de tendance, range | TRADE -- ideal pour le grid |
| 20-25 | Tendance naissante | PRUDENCE -- reduire taille |
| 25-40 | Tendance forte | STOP -- ne pas grid-trader |
| 40+ | Tendance extreme | STOP ABSOLU -- proteger capital |

**Verdict** : Le meilleur indicateur single pour notre cas. Il repond directement a la question "est-ce qu'on est en tendance ?". Seuil recommande : **ADX < 20 = TRADE, ADX > 25 = STOP**.

**Forces** : repond exactement a notre question, pas de biais directionnel, fonctionne sur tous les timeframes.
**Faiblesses** : retard (lagging ~5-10 bougies), peut rester bas au debut d'un crash rapide.

---

### EMA Cross (50/200 -- Golden Cross / Death Cross)

**Comment ca marche** : EMA 50 au-dessus de EMA 200 = bull. En-dessous = bear.

**Pour notre cas** :
- Prix > EMA 200 = marche haussier de fond -> TRADE autorise
- Prix < EMA 200 = marche baissier de fond -> NO TRADE
- EMA 50 croise EMA 200 vers le bas (Death Cross) = signal STOP immediat

**Verdict** : Excellent filtre macro. Simple, robuste, difficile a tromper. La EMA 200 sur 4H est le "regime filter" le plus fiable en crypto.

**Forces** : tres peu de faux signaux sur les gros mouvements, facile a implementer.
**Faiblesses** : tres lent (retard de plusieurs jours), peut donner un faux signal en range.

---

### RSI (Relative Strength Index)

**Comment ca marche** : oscillateur 0-100. Au-dessus de 70 = suracheté. En-dessous de 30 = survendu.

**Pour notre cas** :
- RSI entre 40-60 = range neutre -> TRADE
- RSI < 35 ET en baisse = momentum bearish -> NO TRADE
- RSI > 65 ET en hausse = momentum bullish -> NO TRADE (le prix va trend up, pas osciller)

**Verdict** : Utile comme confirmateur, pas comme filtre principal. Le RSI peut rester "survendu" pendant des semaines dans un vrai bear market.

**Forces** : rapide a reagir, bon pour confirmer.
**Faiblesses** : trop de faux signaux seul, pas fiable pour detecter un regime.

---

### MACD (Moving Average Convergence Divergence)

**Comment ca marche** : difference entre EMA 12 et EMA 26, avec signal line (EMA 9 du MACD).

**Pour notre cas** :
- MACD au-dessus de 0 ET signal line positive = tendance haussiere -> peut grid
- MACD en-dessous de 0 ET divergence negative = bear -> NO TRADE
- Histogramme qui retrecit = la tendance faiblit -> preparer le grid

**Verdict** : Bon indicateur de momentum, mais redondant avec EMA cross. Utile en complement.

**Forces** : montre l'acceleration/deceleration de la tendance.
**Faiblesses** : redondant avec EMA, genere trop de signaux en range.

---

### Bollinger Bandwidth (BBW)

**Comment ca marche** : mesure l'ecart entre les bandes de Bollinger. BBW faible = squeeze (compression). BBW eleve = expansion (volatilite).

**Pour notre cas** :
- BBW en squeeze (< 5%) = range serre -> GRID IDEAL (le prix oscille dans un canal etroit)
- BBW en expansion (> 10%) = gros mouvement en cours -> NO TRADE
- Transition squeeze -> expansion = breakout imminent -> COUPER LE GRID

Les 4 phases de Bollinger :
1. **Squeeze** : bandes serrees, basse volatilite -> TRADE
2. **Expansion** : bandes s'ecartent, volatilite monte -> STOP
3. **Overextension** : bandes tres larges -> ATTENDRE
4. **Mean reversion** : bandes se resserrent -> PREPARER LE GRID

**Verdict** : Excellent complementaire. Mesure la volatilite directement, ce qui est exactement ce que le grid a besoin de savoir.

**Forces** : mesure directe de ce qui compte (volatilite/range), detecte les squeezes.
**Faiblesses** : ne dit pas la direction, peut etre trompe par des gaps.

---

### Volume Profile

**Comment ca marche** : analyse la distribution du volume par prix. Les zones de fort volume = support/resistance naturels.

**Pour notre cas** :
- Fort volume a un niveau de prix = le grid va bien fonctionner la (le prix va rebondir)
- Faible volume entre deux niveaux = le prix va traverser vite (pas bon pour le grid)
- Volume decroissant dans un trend = le trend s'essouffle -> preparer le grid

**Verdict** : Utile pour positionner le grid, pas pour le filtre ON/OFF. Trop complexe pour l'automatisation.

**Forces** : montre ou le prix va "coller".
**Faiblesses** : difficile a automatiser, pas un filtre ON/OFF clair.

---

## 2. Classement final

| Rang | Indicateur | Score /10 | Role |
|------|-----------|-----------|------|
| 1 | **EMA 200 (4H)** | 9/10 | Filtre macro : bull ou bear ? |
| 2 | **ADX (14)** | 8.5/10 | Filtre tendance : trending ou ranging ? |
| 3 | **Bollinger BW** | 7.5/10 | Filtre volatilite : squeeze ou expansion ? |
| 4 | **RSI (14)** | 6/10 | Confirmateur de momentum |
| 5 | **MACD** | 5.5/10 | Redondant avec EMA |
| 6 | **Volume Profile** | 5/10 | Placement du grid, pas filtre ON/OFF |

---

## 3. Le systeme recommande : "Triple Lock"

Trois conditions doivent etre remplies pour activer le grid :

```
TRADE = (prix > EMA200_4H) AND (ADX_14 < 25) AND (BBW < 8%)
```

### En francais :

1. **Lock 1 -- Regime** : le prix est AU-DESSUS de la EMA 200 sur le timeframe 4H
   - Ca veut dire : on est dans un marche globalement haussier ou neutre
   - Si le prix est en-dessous : NO TRADE, point final

2. **Lock 2 -- Tendance** : l'ADX 14-periodes est EN-DESSOUS de 25
   - Ca veut dire : le marche ne trend pas fort, il range
   - Si ADX > 25 : NO TRADE, on laisse le trend finir

3. **Lock 3 -- Volatilite** : le Bollinger Bandwidth est EN-DESSOUS de 8%
   - Ca veut dire : la volatilite est contenue, pas de mouvement extreme
   - Si BBW > 8% : NO TRADE, le marche est trop agite

### Signal STOP d'urgence (override tout) :

```
STOP = (ADX > 35) OR (prix < EMA200 AND EMA50 < EMA200) OR (BBW > 12%)
```

Si n'importe laquelle de ces conditions est vraie : fermer toutes les positions du grid.

---

## 4. Pourquoi le Market EEG n'a pas marche

Notre approche FFT etait elegante mais :
- Elle classait 92% du temps comme "tradable" pendant un crash de 31%
- Les seuils de volatilite (ALPHA: 0.15-0.55%) etaient trop larges
- Elle ne prenait pas en compte la DIRECTION du mouvement
- Un marche peut avoir une volatilite "normale" tout en crashant regulierement de 2-3% par jour

Le FFT mesure la frequence des oscillations, pas leur direction. C'est pour ca qu'il faut la EMA 200 comme filtre de regime en premier.

---

## 5. Implementation concrete

```python
def should_trade(candles_4h, candles_1h):
    """Triple Lock : retourne True si le grid doit etre actif."""

    # Lock 1 : Prix > EMA 200 (4H)
    ema200 = calc_ema(candles_4h, 200)
    prix = candles_4h[-1]['close']
    if prix < ema200:
        return False, "BEAR MARKET - prix sous EMA200"

    # Lock 2 : ADX < 25 (1H, period 14)
    adx = calc_adx(candles_1h, 14)
    if adx > 25:
        return False, f"TRENDING - ADX={adx:.1f}"

    # Lock 3 : BBW < 8% (1H, period 20)
    bbw = calc_bollinger_width(candles_1h, 20)
    if bbw > 0.08:
        return False, f"VOLATILE - BBW={bbw:.1%}"

    return True, f"TRADE OK - EMA200 ok, ADX={adx:.1f}, BBW={bbw:.1%}"


def emergency_stop(candles_4h, candles_1h):
    """Override : fermer tout si conditions extremes."""
    adx = calc_adx(candles_1h, 14)
    ema50 = calc_ema(candles_4h, 50)
    ema200 = calc_ema(candles_4h, 200)
    prix = candles_4h[-1]['close']
    bbw = calc_bollinger_width(candles_1h, 20)

    if adx > 35:
        return True, f"EMERGENCY: ADX extreme ({adx:.1f})"
    if prix < ema200 and ema50 < ema200:
        return True, "EMERGENCY: Death Cross confirme"
    if bbw > 0.12:
        return True, f"EMERGENCY: volatilite extreme ({bbw:.1%})"

    return False, "OK"
```

---

## 6. Backtest a faire

Prochaine etape : implementer le Triple Lock sur nos donnees ETH 3 mois et comparer :
- Baseline (grid toujours actif) : ROI = +12.88% mais -31.7% sur le prix
- Market EEG : ROI = -25.43%
- **Triple Lock** : a tester

Si le Triple Lock avait ete actif entre Dec 2025 et Mar 2026 :
- La EMA 200 aurait coupe le grid autour de mi-janvier (quand ETH a perce sous 2800)
- On aurait evite la majorite du drawdown de -31%
- Le grid aurait ete reactif uniquement dans les phases de rebond (au-dessus de EMA 200)

**Estimation** : le Triple Lock aurait transforme le -14% en -3% a +5% (en evitant 70-80% du drawdown).

---

## 7. Machine Learning -- piste future

Les recherches academiques montrent :
- LSTM + GRU pour la prediction de regime : Sharpe 3.2 vs 1.3 buy-and-hold
- XGBoost avec features techniques : 55-65% de precision directionnelle
- TimeGPT / Chronos : modeles zero-shot, rapides, prometteurs mais pas encore prouves en live

**Pour nous** : commencer par le Triple Lock (simple, deterministe, backtestable). Si ca marche, ajouter un modele ML qui predit le regime (bull/bear/range) avec un horizon de 24-48h. Le ML peut ajuster les seuils du Triple Lock dynamiquement.

---

## Sources

- [Fidelity - ADX Market Strength](https://www.fidelity.com/viewpoints/active-investor/average-directional-index-ADX)
- [Dynamic EMA Crossover + ADX Strategy](https://medium.com/@redsword_23261/dynamic-ema-crossover-strategy-with-adx-trend-strength-filtering-system-04af8fbf9813)
- [Schwab - ADX and RSI Combined](https://www.schwab.com/learn/story/spot-and-stick-to-trends-with-adx-and-rsi)
- [Bollinger Band Squeeze - StockCharts](https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/bollinger-band-squeeze)
- [FXEmpire - Bollinger Bands Market Regimes](https://www.fxempire.com/education/article/bollinger-bands-trading-strategies-how-to-read-volatility-identify-market-regimes-and-trade-with-a-statistical-edge-1585260)
- [Gekko RSI Bull Bear + ADX Strategy](https://steemit.com/gekko/@crypto49er/t0olnilf)
- [EMA Cross + RSI + ADX TradingView Strategy](https://www.tradingview.com/script/e7XQPek8-EMA-Cross-RSI-ADX-Autotrade-Strategy-V2/)
- [Springer - ML Crypto Trading Optimization](https://link.springer.com/article/10.1007/s44163-025-00519-y)
- [ScienceDirect - Crypto Price Forecasting Ensemble vs Deep Learning](https://www.sciencedirect.com/science/article/pii/S1057521923005719)
- [MDPI - Crypto Forecasting and Anomaly Detection](https://www.mdpi.com/2076-3417/15/4/1864)
- [Grid Trading Guide - MEXC](https://www.mexc.co/news/263654)
- [Gainium Grid Bot](https://gainium.io/grid-bot)
- [WunderTrading - AI Crypto Trend Forecasting](https://wundertrading.com/journal/en/learn/article/ai-crypto-trend-forecasting-tools-models)

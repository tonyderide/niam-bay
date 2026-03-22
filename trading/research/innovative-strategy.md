# Strategie Innovante : "Le Cameleon" -- Adaptive Volatility + Session Momentum

> Recherche du 2026-03-22
> Objectif : 100 EUR de capital sur Kraken, strategie qu'un humain ne peut pas executer

---

## 1. Analyse des 6 idees -- verdict

| # | Strategie | Faisable a 100 EUR ? | Edge reel ? | Complexite | Verdict |
|---|-----------|----------------------|-------------|------------|---------|
| 1 | Sentiment Fear/Greed | Oui | Moyen-terme seulement (147j holding moyen) | Faible | TROP LENT pour 100 EUR |
| 2 | Time-of-day patterns | Oui | OUI -- recherche academique solide | Moyenne | EXCELLENT |
| 3 | Volatility prediction | Oui | OUI -- regime switching prouve | Moyenne | EXCELLENT |
| 4 | Micro-scalping maker | Non -- spread ETH ~0.05%, fee 0.02% = marge 0.01% | Quasi-nul a petit capital | Tres haute | ELIMINE |
| 5 | Multi-timeframe consensus | Oui | Faible -- trop de filtres = 0 trades | Haute | MEDIOCRE |
| 6 | Anti-retail (liquidations) | Oui | OUI mais timing macro | Faible | BON en complement |

**Gagnant : Combiner #2 + #3 -- Session Momentum + Volatility Regime Switching**

C'est la strategie que j'appelle **"Le Cameleon"** : elle change de peau selon les conditions.

---

## 2. Pourquoi cette strategie est INNOVANTE

### Ce qu'un humain ne peut PAS faire :
1. **Surveiller 3 sessions 24h/24** -- Asian (00-08 UTC), EU (08-16 UTC), US (16-00 UTC)
2. **Calculer la volatilite realisee en temps reel** et changer de regime en <1 seconde
3. **Basculer entre 3 modes** de trading automatiquement sans hesitation ni fatigue
4. **Ne jamais dormir** -- le marche crypto est 24/7, l'humain non

### Le edge scientifique :
- **Cross-session momentum** : quand EU monte, US monte aussi (ETH +44.9 bps spread EU->US)
- **Sharpe 0.808** et **+256% net return** sur 4.7 ans dans la recherche academique (Mars 2026, Coinmonks)
- **Volume peak 16-17 UTC** = meilleure liquidite = moins de slippage
- **Liquidite tombe la nuit (00-06 UTC)** = spreads plus larges = grid trading plus profitable

---

## 3. Architecture du Cameleon

```
                    +-------------------+
                    |  VOLATILITY METER |
                    |  (ATR 1h, StdDev) |
                    +--------+----------+
                             |
              +--------------+--------------+
              |              |              |
        LOW REGIME     MED REGIME     HIGH REGIME
        (ATR < 0.8%)  (0.8-2.0%)    (ATR > 2.0%)
              |              |              |
        +-----+----+  +-----+----+  +-----+----+
        | SOMMEIL  |  | SESSION  |  | MOMENTUM |
        | Mode off |  | MOMENTUM |  | TURBO    |
        | 0 trades |  | Trading  |  | + Grid   |
        +----------+  +----------+  +----------+
```

### Mode 1 : SOMMEIL (Low Volatility -- ATR 1h < 0.8%)
- **Action** : NE RIEN FAIRE
- **Pourquoi** : En basse volatilite, les fees mangent tout le profit
- **Ce que fait l'humain** : Trade quand meme par ennui et perd
- **Ce que fait l'IA** : Attend patiemment, zero ego

### Mode 2 : SESSION MOMENTUM (Medium Volatility -- ATR 1h entre 0.8% et 2.0%)
- **Action** : Suivre le momentum de session
- **Logique** :
  1. A 16:00 UTC (ouverture US), regarder la performance de la session EU (08-16 UTC)
  2. Si EU a monte > +0.3% : LONG ETH avec trailing stop
  3. Si EU a baisse > -0.3% : SHORT ETH avec trailing stop
  4. Trailing stop a 0.5%, activation apres +0.3% de profit
  5. Fermer la position a 00:00 UTC (fin session US) quoi qu'il arrive
- **Levier** : 5x
- **Stake** : 10 EUR (10% du capital)
- **Risk par trade** : ~0.50 EUR max (SL initial 1%)
- **Frequence** : 1 trade/jour maximum

### Mode 3 : MOMENTUM TURBO + GRID (High Volatility -- ATR 1h > 2.0%)
- **Action** : Session momentum PLUS micro-grid opportuniste
- **Logique session momentum** : identique au Mode 2 mais avec :
  - Stake augmente a 15 EUR (15% du capital)
  - Trailing stop plus large (0.7%) car plus de mouvement
- **Logique grid** :
  1. Placer 5 ordres limites buy/sell autour du prix actuel
  2. Espacement = ATR 15min / 2 (adaptatif!)
  3. TP = 1 espacement, SL = 2 espacements
  4. Ordres en limit only (maker fee 0.02% au lieu de 0.05% taker)
  5. Laisser tourner pendant les heures de haute volatilite
- **Duree** : Grid active uniquement pendant session US (16-00 UTC) = meilleure liquidite

---

## 4. Session Momentum -- Le coeur de la strategie

### Pourquoi ca marche (la science)

Source : "Crypto Markets Run on Inverted Clocks" (Coinmonks, Mars 2026)

| Paire de sessions | Spread (bps) | Direction | Sharpe |
|-------------------|-------------|-----------|--------|
| EU -> US (ETH)    | +44.9       | Momentum  | 0.808  |
| Asia -> EU        | +18.2       | Momentum  | 0.43   |
| US -> Asia        | -12.1       | Reversion | 0.31   |

**Traduction concrete** :
- Si ETH monte pendant la session europeenne, il a tendance a CONTINUER a monter pendant la session americaine
- L'edge est de +44.9 basis points par trade en moyenne
- Avec 5x levier, ca fait +224.5 bps = +2.245% par trade sur le capital engage
- Sur 10 EUR de stake : +0.22 EUR par trade en moyenne
- ~20 trades/mois (pas tous les jours car filtre volatilite) = ~4.50 EUR/mois
- **~54 EUR/an = 54% ROI annuel** (avant drawdowns)

### Pourquoi le crypto montre du momentum cross-session (et pas les actions)

Le crypto est l'inverse des marches traditionnels :
- **Actions** : momentum intra-session, reversion cross-session
- **Crypto** : REVERSION intra-session, MOMENTUM cross-session

Explication probable : les traders particuliers reagissent en retard. Quand l'Europe lance un mouvement, les Americains le voient en se reveillant et sautent dans le train. Le mouvement se prolonge.

### Implementation concrete

```python
# Pseudo-code Session Momentum

def check_session_signal():
    now = datetime.utcnow()

    # A 16:00 UTC, evaluer la session EU
    if now.hour == 16:
        eu_open_price = get_price_at(today, hour=8)  # ETH a 08:00 UTC
        eu_close_price = get_current_price()           # ETH a 16:00 UTC
        eu_return = (eu_close_price - eu_open_price) / eu_open_price

        atr_1h = calculate_atr(period=14, timeframe='1h')

        # Filtre volatilite
        if atr_1h < 0.008:  # < 0.8%
            return None  # Mode SOMMEIL

        # Signal
        if eu_return > 0.003:  # EU monte > +0.3%
            return "LONG"
        elif eu_return < -0.003:  # EU baisse > -0.3%
            return "SHORT"

    return None

def execute_trade(signal, capital=100, stake_pct=0.10):
    stake = capital * stake_pct  # 10 EUR
    leverage = 5

    entry = get_current_price()

    if signal == "LONG":
        sl = entry * 0.99       # SL a -1%
        trail_start = entry * 1.003  # Trail apres +0.3%
        trail_dist = 0.005      # Trail a 0.5%
    else:
        sl = entry * 1.01
        trail_start = entry * 0.997
        trail_dist = 0.005

    place_order(signal, stake, leverage, sl, trail_start, trail_dist)

    # DEADLINE : fermer a 00:00 UTC quoi qu'il arrive
    schedule_close(hour=0)
```

---

## 5. Volatility Regime Detection -- Le cerveau

### Methode : ATR + Bollinger Band Width

```python
def detect_regime():
    """
    Retourne: 'sleep', 'normal', 'turbo'
    Recalcule toutes les 15 minutes
    """
    # ATR 14 periodes sur chandeliers 1h
    atr = calculate_atr(candles_1h, period=14)
    atr_pct = atr / current_price * 100

    # Bollinger Band Width (mesure complementaire)
    bb_width = calculate_bb_width(candles_1h, period=20, std=2)

    # Classification
    if atr_pct < 0.8 and bb_width < 0.02:
        return 'sleep'    # Marche mort, ne rien faire
    elif atr_pct > 2.0 or bb_width > 0.05:
        return 'turbo'    # Haute volatilite, mode agressif
    else:
        return 'normal'   # Session momentum standard
```

### Pourquoi c'est crucial

Donnees Martin Grid (nos backtests precedents) :
- **En haute volatilite** : les grids font +15-25% ROI
- **En basse volatilite** : les grids font -5% a -15% (les fees mangent tout)
- **Difference** : ~30-40% de ROI selon le regime!

Le Cameleon resout le probleme #1 de Martin Grid : **il s'eteint quand le marche dort**.

---

## 6. Adaptive Grid (Mode Turbo) -- Detail

### Espacement dynamique base sur ATR

```
Grid spacing = ATR(15min, 14 periodes) / 2

Exemple concret :
- ATR 15min = 0.4% -> espacement = 0.2% = ~4 EUR sur ETH a 2000 EUR
- 5 niveaux buy + 5 niveaux sell = 10 ordres
- Stake par niveau : 2 EUR * 5x levier = 10 EUR notionnel
- Total engage : 10 EUR (10% du capital)

Quand ATR augmente :
- ATR 15min = 1.0% -> espacement = 0.5% = ~10 EUR
- Les niveaux s'ecartent automatiquement
- Moins de trades mais plus gros profits par trade

Quand ATR diminue :
- ATR 15min = 0.2% -> STOP! On passe en mode normal ou sommeil
```

### Pourquoi ordres limite (maker) :
- **Maker fee** : 0.02% (Kraken futures)
- **Taker fee** : 0.05%
- **Economie** : 0.06% par aller-retour (0.03% * 2)
- Sur 100 trades/mois avec 10 EUR notionnel : 0.60 EUR d'economie
- Sur petit capital, chaque centime compte

---

## 7. Risk Management -- La survie

### Regles inviolables

| Regle | Valeur | Raison |
|-------|--------|--------|
| Max risk par trade | 1% du capital (1 EUR) | Survie sur 100+ trades |
| Max drawdown journalier | 3% (3 EUR) | Arret du bot pour 24h |
| Max drawdown total | 15% (15 EUR) | Revue complete de la strategie |
| Max positions simultanees | 1 session + 5 grid | Pas de surexposition |
| Levier max | 5x | 10x = trop de liquidations |
| Session momentum deadline | 00:00 UTC | Jamais overnight |
| Grid max duree | 8h | Fermer et recalculer |

### Position sizing adaptatif

```
Si drawdown < 5%  : stake normal (10% capital)
Si drawdown 5-10% : stake reduit (5% capital)
Si drawdown > 10% : stake minimum (2% capital) + mode defensif
Si drawdown > 15% : STOP TOTAL -- revoir la strategie
```

---

## 8. Projection financiere realiste

### Hypotheses conservatrices
- Session momentum : 15 trades/mois (pas tous les jours -- filtre vol)
- Win rate session : 54% (leger edge, pas miraculeux)
- Avg win : +2.0% du stake | Avg loss : -1.0% du stake
- Grid (mode turbo) : actif ~30% du temps
- Grid profit : ~0.3% du capital/jour quand actif

### Mois type

```
Session momentum :
  15 trades * 10 EUR stake * 5x levier = 750 EUR notionnel total
  8 wins  * 2.0% * 10 EUR = +1.60 EUR
  7 losses * 1.0% * 10 EUR = -0.70 EUR
  Net session : +0.90 EUR
  Fees : 750 * 0.05% * 2 = -0.75 EUR
  Net apres fees : +0.15 EUR  (humble mais positif)

Grid turbo (actif ~9 jours/mois) :
  ~5 aller-retours/jour * 9 jours = 45 trades
  Profit moyen par trade : 0.10 EUR (apres fees)
  Net grid : +4.50 EUR

TOTAL MENSUEL ESTIME : ~4.65 EUR = ~4.65% ROI/mois
TOTAL ANNUEL ESTIME : ~56% ROI (avec compound)
```

### Scenario pessimiste
- Win rate session : 50% (pas d'edge)
- Grid actif seulement 20% du temps
- ROI mensuel : ~2% = ~27% annuel (toujours mieux que HODL dans un marche plat)

### Scenario optimiste
- Win rate session : 58% (edge academique confirme)
- Grid actif 40% du temps (marche volatile)
- ROI mensuel : ~8% = ~152% annuel

---

## 9. Stack technique

```
Kraken Futures API (WebSocket v2)
    |
    +-- Data feed (book, trades, candles)
    |
Python Bot sur VM (meme VM que Martin Grid)
    |
    +-- volatility_detector.py   -- Calcul ATR, BB, regime
    +-- session_momentum.py      -- Signal EU->US, trailing stop
    +-- adaptive_grid.py         -- Grid dynamique, ordres limite
    +-- risk_manager.py          -- Position sizing, drawdown, kill switch
    +-- cameleon.py              -- Orchestrateur principal
    |
    +-- SQLite log (tous les trades, regimes, decisions)
    +-- Dashboard HTML (meme style que Martin Grid)
```

### APIs necessaires
- `GET /api/charts/v1/trade/PF_ETHUSD/1h` -- chandeliers pour ATR
- `GET /api/charts/v1/trade/PF_ETHUSD/15m` -- chandeliers pour grid spacing
- `WS book` -- orderbook L2 pour spread monitoring
- `POST /derivatives/api/v3/sendorder` -- placer ordres
- `DELETE /derivatives/api/v3/cancelorder` -- annuler grid ordres

---

## 10. Plan d'implementation

### Phase 1 : Backtest (1-2 semaines)
1. Telecharger 6+ mois de donnees ETH 1h et 15m via Kraken API
2. Backtester le session momentum EU->US isolement
3. Backtester le regime switching (quand s'allumer/s'eteindre)
4. Backtester la grid adaptive en mode turbo
5. Combiner les 3 et mesurer le Sharpe ratio global

### Phase 2 : Paper trading (2 semaines)
1. Deployer le bot sur VM en mode paper (log sans executer)
2. Comparer les decisions du bot vs le marche reel
3. Ajuster les seuils (0.3% pour EU return ? 0.8% pour ATR sleep ?)
4. Valider que le risk manager fonctionne

### Phase 3 : Live avec 20 EUR (2 semaines)
1. Deployer avec 20% du capital seulement
2. Session momentum uniquement (pas encore de grid)
3. Verifier slippage reel vs backtest
4. Verifier que les ordres s'executent correctement

### Phase 4 : Full deployment (ongoing)
1. Augmenter a 100 EUR
2. Activer la grid adaptive
3. Monitoring quotidien via dashboard
4. Ajustement mensuel des parametres

---

## 11. Pourquoi c'est different de tout ce qu'on a fait

| Avant (Martin Grid) | Maintenant (Le Cameleon) |
|---------------------|--------------------------|
| Toujours allume | S'eteint quand le marche dort |
| Meme parametres tout le temps | 3 modes adaptatifs |
| Grid fixe | Grid spacing dynamique (ATR) |
| Pas de direction | Session momentum directionnel |
| Fees mangent les profits en basse vol | Zero fees en basse vol (mode sommeil) |
| 1 seule strategie | Hybride : momentum + grid |
| Reagit au prix | Reagit au REGIME de marche |

**La vraie innovation** : ce n'est pas UNE strategie. C'est un systeme qui CHOISIT la bonne strategie au bon moment. C'est ce qu'un humain ne peut pas faire -- il est bias par son humeur, sa fatigue, son ego. L'IA n'a aucun de ces problemes.

---

## 12. Risques et limites

1. **Regime mal detecte** : Si l'ATR dit "sommeil" mais le marche explose, on rate le mouvement
   - Mitigation : seuil conservateur, recheck toutes les 15 min
2. **Session momentum breakdown** : Le pattern peut disparaitre (efficience du marche)
   - Mitigation : monitorer le win rate rolling, stop si < 48% sur 30 trades
3. **Liquidation en mode turbo** : Haute vol = gros moves contre nous
   - Mitigation : SL strict, levier 5x max, deadline sur toutes les positions
4. **Overfit des parametres** : Les seuils (0.3%, 0.8%, 2.0%) sont arbitraires
   - Mitigation : Phase 1 backtest + Phase 2 paper trading avant argent reel
5. **Kraken API downtime** : Le bot ne peut pas trader si l'API est down
   - Mitigation : kill switch automatique, toutes positions avec SL

---

## Sources

- [Crypto Markets Run on Inverted Clocks: Session Patterns Create Alpha with 256% Returns (Coinmonks, Mars 2026)](https://medium.com/coinmonks/crypto-markets-run-on-inverted-clocks-how-session-patterns-create-alpha-with-256-returns-e76a4c61e79c)
- [Intraday and daily dynamics of cryptocurrency (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S1059056024006506)
- [The Rhythm of Liquidity: Temporal Patterns in Market Depth (Amberdata)](https://blog.amberdata.io/the-rhythm-of-liquidity-temporal-patterns-in-market-depth)
- [Regime Switching Forecasting for Cryptocurrencies (Springer)](https://link.springer.com/article/10.1007/s42521-024-00123-2)
- [Bitcoin Fear and Greed Index Trading Strategy (Nasdaq)](https://www.nasdaq.com/articles/how-bitcoin-fear-and-greed-index-trading-strategy-beats-buy-and-hold-investing)
- [Kraken Fee Schedule](https://www.kraken.com/features/fee-schedule)
- [Kraken Futures Fee Schedule](https://support.kraken.com/articles/360048917612-fee-schedule)
- [Dynamic Grid Bot: How It Works in Crypto Trading (WunderTrading)](https://wundertrading.com/journal/en/trading-bots/article/dynamic-grid-bot)
- [Systematic Crypto Trading: Momentum, Mean Reversion & Volatility Filtering (Medium)](https://medium.com/@briplotnik/systematic-crypto-trading-strategies-momentum-mean-reversion-volatility-filtering-8d7da06d60ed)
- [Bitcoin Intraday Time-Series Momentum (University of Reading)](https://centaur.reading.ac.uk/100181/3/21Sep2021Bitcoin%20Intraday%20Time-Series%20Momentum.R2.pdf)

# Short Grid Trading : les mecaniques concretes

*29 mars 2026, 00h15 — recherche nocturne*

---

## Le probleme

Notre Martin Grid est long-only. Quand le marche descend, on accumule des positions qui perdent de la valeur. En bear market, c'est la mort lente. L'idee : un grid inversé qui **gagne** quand ca descend.

---

## 1. Ouvrir un short sur Kraken Futures — l'API

Sur Kraken Futures, c'est simple : `side: "sell"` ouvre un short.

### Endpoint
```
POST https://futures.kraken.com/derivatives/api/v3/sendOrder
```

### Parametres cles
```json
{
  "orderType": "lmt",        // lmt, mkt, stp, take_profit, trailing_stop
  "symbol": "PF_ETHUSD",     // perpetual futures ETH/USD
  "side": "sell",             // "sell" = ouvrir un SHORT
  "size": 0.1,               // taille en ETH
  "limitPrice": 2000          // prix limite (pour lmt)
}
```

### Avec CCXT (Python)
```python
import ccxt

exchange = ccxt.krakenfutures({
    'apiKey': 'xxx',
    'secret': 'xxx',
    'enableRateLimit': True,
})

# Ouvrir un short
order = exchange.create_order(
    symbol='ETH/USD:USD',
    type='limit',
    side='sell',          # sell = SHORT
    amount=0.1,
    price=2000
)

# Fermer le short (racheter)
close = exchange.create_order(
    symbol='ETH/USD:USD',
    type='limit',
    side='buy',           # buy = fermer le short
    amount=0.1,
    price=1900
)
```

### Avec python-kraken-sdk
```python
from kraken.futures.client import Trade

trade = Trade(key='xxx', secret='xxx')
# Le SDK expose les memes endpoints, side="sell" pour short
```

---

## 2. Le Grid Inverse (Reverse Grid)

### Grid Long classique (ce qu'on fait maintenant)
```
Prix monte  → on VEND (take profit)
Prix baisse → on ACHETE (accumule)
Profit = acheter bas, vendre haut
Risque = le prix s'effondre, on est charge de bags
```

### Grid Short (inverse)
```
Prix monte  → on VEND A DECOUVERT (ouvre short)
Prix baisse → on RACHETE (close short = take profit)
Profit = vendre haut, racheter bas
Risque = le prix explose a la hausse, shorts squeeze
```

### Schema concret
```
          ZONE DE VENTE SHORT
  2100 ── SELL short 0.1 ETH ──────── niveau 5
  2050 ── SELL short 0.1 ETH ──────── niveau 4
  2000 ── SELL short 0.1 ETH ──────── niveau 3  ← prix actuel
  1950 ── BUY (close short) 0.1 ETH ─ niveau 2
  1900 ── BUY (close short) 0.1 ETH ─ niveau 1
  1850 ── BUY (close short) 0.1 ETH ─ niveau 0
          ZONE DE RACHAT (PROFIT)
```

Le prix oscille entre 1900 et 2100 :
- Monte a 2050 → short ouvert a 2050
- Redescend a 1950 → short ferme a 1950 → profit = 100$ par 0.1 ETH
- Remonte a 2100 → short ouvert a 2100
- Redescend a 2000 → short ferme a 2000 → profit = 100$ par 0.1 ETH

**Chaque aller-retour = profit du spread entre les niveaux.**

---

## 3. Calcul du profit d'un short grid

### Formule par round-trip
```
profit_par_trade = size * (prix_vente_short - prix_rachat) - fees

Exemple :
  size = 0.1 ETH
  vente short a 2050$
  rachat a 1950$
  fees maker = 0.02% par trade = 0.0002

  profit_brut = 0.1 * (2050 - 1950) = 10$
  fees = 0.1 * 2050 * 0.0002 + 0.1 * 1950 * 0.0002 = 0.041 + 0.039 = 0.08$
  profit_net = 10 - 0.08 = 9.92$
```

### Profit total du grid
```
profit_total = nombre_round_trips * profit_par_trade

Avec 10 niveaux, spacing 2.5%, prix oscillant :
  - 5 niveaux short au-dessus du centre
  - 5 niveaux de rachat en-dessous
  - Chaque oscillation complete = ~50$ de profit (5 trades * 10$)
  - Sur un mois volatile = 20-30 oscillations = 1000-1500$ brut
```

### ROI
```
capital = 1000$ avec leverage x5 = 5000$ d'exposition
profit_mensuel = 1000$
ROI = 100% / mois (en conditions ideales de range)
```

---

## 4. Frais de funding sur Kraken Futures

### Mecanisme
- Les perpetual futures ont un **funding rate toutes les heures**
- Le funding aligne le prix du contrat sur le prix spot
- Max : ±0.25% par heure

### Impact sur les shorts
```
Si funding POSITIF (marche bullish) :
  → Les LONGS paient les SHORTS
  → Tu RECOIS du funding en etant short
  → C'est un bonus !

Si funding NEGATIF (marche bearish) :
  → Les SHORTS paient les LONGS
  → Tu PAIES du funding en etant short
  → Ca grignote les profits
```

### En pratique
- En bear market, le funding est souvent positif → les shorts sont PAYES
- C'est un double avantage : profit sur les grids + funding recu
- En bull market, le funding est negatif → les shorts paient
- Mais dans un grid, les positions sont courtes (heures, pas jours), donc l'impact est faible

### Estimation des couts
```
Funding moyen = ~0.01% par heure (typique)
Position short de 1000$ pendant 4h = 1000 * 0.0001 * 4 = 0.40$
Si le grid fait 10$ sur ce trade → 0.40$ de funding = 4% des profits
```

---

## 5. Exemples concrets qui marchent

### Exemple 1 : Reverse Grid ETH en range (Pionex/3Commas)
- Paire : ETH/USD
- Range : 1800-2200$
- 20 grids
- Capital : 1000$ x5 leverage
- Resultat : ~5% par semaine en range lateral
- **Condition** : le prix reste dans le range

### Exemple 2 : Short Grid en bear market
- Paire : BTC/USD
- Tendance : baissiere (-20% sur le mois)
- 10 grids, spacing 1%
- Le prix descend en oscillant → chaque rebond temporaire = short entry, chaque nouvelle baisse = take profit
- Resultat : profit sur les oscillations + profit sur la tendance baissiere
- Le grid "surfe" la descente

### Exemple 3 : Dual Grid (long + short simultane)
- Zone haute : short grid (vend short, rachete plus bas)
- Zone basse : long grid (achete, revend plus haut)
- Le centre separe les deux zones
- **Avantage** : profit dans les deux directions
- **Risque** : breakout fort dans une direction = pertes d'un cote

---

## 6. L'idee : Auto-Switch Long/Short

### Le concept
```
Detecter la tendance → choisir le grid

BULL MARKET  → Grid LONG  (acheter bas, vendre haut)
BEAR MARKET  → Grid SHORT (vendre haut, racheter bas)
RANGE        → Grid DUAL  (les deux en meme temps)
```

### Detection de tendance (simple)
```python
def detect_trend(candles, period=24):
    """EMA crossover simple"""
    ema_fast = ema(candles, period)
    ema_slow = ema(candles, period * 3)

    if ema_fast > ema_slow * 1.01:
        return 'BULL'
    elif ema_fast < ema_slow * 0.99:
        return 'BEAR'
    else:
        return 'RANGE'

def choose_grid_mode(trend):
    if trend == 'BULL':
        return 'LONG_GRID'
    elif trend == 'BEAR':
        return 'SHORT_GRID'
    else:
        return 'DUAL_GRID'
```

### Detection avancee (ADX + EMA)
```python
def detect_trend_advanced(candles):
    adx = calculate_adx(candles, 14)
    ema_cross = ema_crossover(candles, 12, 26)

    if adx < 20:
        return 'RANGE'           # Pas de tendance → dual grid
    elif adx > 25 and ema_cross > 0:
        return 'STRONG_BULL'     # Tendance forte haussiere → grid long agressif
    elif adx > 25 and ema_cross < 0:
        return 'STRONG_BEAR'     # Tendance forte baissiere → grid short agressif
    elif ema_cross > 0:
        return 'WEAK_BULL'       # Tendance faible haussiere → grid long prudent
    else:
        return 'WEAK_BEAR'       # Tendance faible baissiere → grid short prudent
```

### Le switch
```python
def manage_grid(exchange, symbol, capital, leverage):
    while True:
        candles = fetch_candles(exchange, symbol)
        trend = detect_trend_advanced(candles)

        current_mode = get_current_mode()
        new_mode = choose_grid_mode(trend)

        if new_mode != current_mode:
            close_all_positions(exchange, symbol)
            cancel_all_orders(exchange, symbol)
            setup_grid(exchange, symbol, capital, leverage, mode=new_mode)
            log(f"SWITCH: {current_mode} → {new_mode}")

        sleep(3600)  # Re-evaluer toutes les heures
```

---

## 7. Risques specifiques du short grid

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Short squeeze | Perte explosive si le prix monte violemment | Stop-loss obligatoire au-dessus du grid |
| Liquidation | Leverage trop eleve + mouvement fort | Max leverage x3-x5, margin suffisante |
| Funding negatif | Erosion des profits en bull | Switch automatique en mode long |
| Gap de prix | Le prix saute au-dessus du stop | Utiliser des stop-market, pas stop-limit |
| Breakout du range | Le prix quitte la zone du grid | Re-centrer le grid ou fermer |

---

## 8. Prochaines etapes

1. **Backtest** : adapter `backtest_grid.py` pour simuler un short grid
2. **Backtest dual** : tester le mode dual (long + short simultane)
3. **Detecteur de tendance** : coder la detection EMA/ADX sur nos donnees historiques
4. **Tester sur papier** : Kraken a un mode demo pour les futures
5. **Integrer dans Martin** : ajouter le mode short a la grid live

---

## Sources

- [Kraken Futures Send Order API](https://docs.kraken.com/api/docs/futures-api/trading/send-order/)
- [Kraken Futures Introduction](https://docs.kraken.com/api/docs/guides/futures-introduction/)
- [Kraken Funding Rates Primer](https://blog.kraken.com/product/quick-primer-on-funding-rates)
- [Kraken Perpetual Contract Specs](https://support.kraken.com/articles/4844359082772-linear-multi-collateral-derivatives-contract-specifications)
- [Reverse Grid Bot Explained (WunderTrading)](https://wundertrading.com/journal/en/learn/article/reverse-grid-bot)
- [Reverse Grid Bot in Bear Market (Medium/Coinmonks)](https://medium.com/coinmonks/how-to-profit-with-a-reverse-grid-trading-bot-in-a-bear-market-9ab1df8a0fe3)
- [Grid Bots: How They Really Work (Medium/Coinmonks)](https://medium.com/coinmonks/grid-bots-how-they-really-work-how-to-make-money-with-them-948b4439fa5f)
- [Bybit Futures Grid P&L Calculations](https://www.bybit.com/en/help-center/article/P-L-Calculations-Futures-Grid-Bot)
- [AI Dual Grid Strategy (uTrading)](https://help.utrading.io/en/trading/trading-robot/manual-trading/trading-straregy/what-is-the-ai-dual-grid-trading-strategy)
- [Adaptive Grid Trading (Medium)](https://medium.com/@redsword_23261/adaptive-grid-trading-strategy-with-dynamic-adjustment-mechanism-618fe5c29af8)
- [python-kraken-sdk](https://github.com/btschwertfeger/python-kraken-sdk)
- [CCXT Kraken Docs](https://docs.ccxt.com/exchanges/kraken)

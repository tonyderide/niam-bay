# Analyse du Simulateur — autre-branch Martin

Date: 2026-03-22
Source: `C:/martin/backend/src/main/java/com/martin/scalping/`

---

## Architecture

Le simulateur est un service Spring Boot (`ScalpingSimulatorService`) qui rejoue des strategies sur des bougies historiques. **Aucun ordre Kraken n'est passe** — c'est du pur calcul offline.

- **Controller**: `ScalpController` expose `POST /simulate` et `GET /simulate/data-files`
- **Request**: `SimulationRequest` (tous les parametres configurables)
- **Result**: `SimulationResult` (trades, equity curve, stats)
- **Frontend**: Angular component avec TradingView lightweight-charts, formulaire complet

---

## 1. Strategies disponibles

| Strategy | Signal d'entree | Description |
|---|---|---|
| **MACD_RSI** (defaut) | MACD histogram cross zero + filtre RSI (<55 LONG, >45 SHORT) | Classique momentum + confirmation |
| **MOMENTUM_SCORE** | Score combine: MACD cross (+-2), MACD >/<0 (+-1), RSI (+-1), EMA alignment (+-1). Threshold configurable (defaut 3) | Multi-indicateur, plus selectif |
| **EMA_CROSS** | Croisement EMA rapide/lente (defaut 9/21) | Trend following simple |
| **SWING_STOP** | Meme signal que MACD_RSI, mais stop-loss place sur swing low/high au lieu du trailing | Stops plus naturels |
| **REVERSAL_TRAIL** | EMA cross pour l'entree initiale, puis **reverse automatiquement** apres chaque perte (sans cooldown) | Contrarian sur perdants |

### Parametres par strategie

- **MACD**: fast=5, slow=13, signal=4 (rapides, adaptes au scalping)
- **RSI**: period=14, longMax=55, shortMin=45
- **EMA**: fast=9, slow=21
- **Momentum**: threshold=3 (sur un max theorique de +-5)

---

## 2. Donnees utilisees

### Sources
- **Fichier JSON** (mode backtest): lu depuis le repertoire `backtest/` configurable via `app.backtest-dir`
- **API Kraken live**: `krakenClient.getOhlc(instrument, durationMinutes, "5m")` — bougies 5 minutes

### Fichier disponible
- `backtest/eth_1m_candles.json` — 528 Ko, bougies 1 minute ETH
- Format: tableau JSON `[{time, open, high, low, close, volume}, ...]`
- Timestamps en millisecondes epoch (auto-converti en secondes par le code)
- Prix en string, convertis en double

### Exemple de donnee
```json
{"time": 1773273600000, "open": "2052.1", "high": "2054.3", "low": "2052", "close": "2053.2", "volume": "156.268"}
```

### Instruments supportes (frontend)
- PF_ETHUSD, PF_XBTUSD, PF_SOLUSD, PF_XRPUSD

---

## 3. Integration dashboard — peut-on l'utiliser ?

**Oui, c'est deja expose via REST:**

```
GET  /api/scalp/simulate/data-files    -> Liste les fichiers JSON dispo
POST /api/scalp/simulate               -> Lance une simulation (body = SimulationRequest JSON)
```

### Pour l'utiliser depuis le dashboard Niam-Bay:
1. Le backend Martin doit tourner (Spring Boot)
2. Appeler `POST /simulate` avec les parametres voulus
3. Le resultat contient: trades[], equityCurve[], et toutes les stats summary

### Ce qu'on pourrait faire:
- Ajouter un bouton "Simuler" dans le dashboard HTML statique qui appelle cette API
- Afficher les resultats (equity curve, win rate, PnL) directement
- Comparer les strategies en parallele

---

## 4. Precision de la simulation

### Ce qui est modellise correctement

| Aspect | Detail | Verdict |
|---|---|---|
| **Fees** | Taker fee applique x2 (entree + sortie). Defaut 0.05% = Kraken futures | Correct |
| **Entree anti look-ahead** | Entree au OPEN de la bougie suivante (pas au close du signal) | Bon |
| **Trailing stop** | Deux niveaux: wide (3%) initial, tight (2.5%) apres minProfit | Realiste |
| **Swing stop** | Swing low/high sur N bougies + offset | Bon |
| **Safety stop-loss** | Hard stop a 5% par defaut | Protection catastrophe |
| **Martingale** | Doublement apres perte, max 2 doublements, reset apres | Modellise |
| **Hedge reversal** | Inverse la direction apres N pertes consecutives meme direction | Modellise |
| **Cooldown** | 2 bougies apres gain, 6 apres perte | Anti-overtrading |
| **Heures de trading** | Filtre 8h-22h UTC | Evite le bruit nocturne |
| **Daily loss limit** | Stop a -10% du capital par jour | Risk management |

### Ce qui MANQUE (limites de precision)

| Manque | Impact |
|---|---|
| **Slippage** | Aucun slippage modellise. En vrai, surtout sur des petits volumes, le fill price differe | **Moyen-Haut** |
| **Spread bid/ask** | Non modellise. On entre/sort au prix de la bougie, pas au bid/ask reel | **Moyen** |
| **Impact de marche** | Pas de modelisation de l'impact sur le carnet d'ordres | **Faible** (petites positions) |
| **Funding rate** | Pas de frais de funding pour les futures Kraken (8h) | **Faible** (trades courts) |
| **Liquidation** | Pas de prix de liquidation calcule malgre le leverage | **Moyen** si leverage eleve |
| **Latence** | Pas de delai entre signal et execution | **Faible** (bougies 5min) |

### RSI: implementation simplifiee
Le RSI utilise une somme glissante (SMA-based) au lieu du lissage exponentiel (EMA-based / Wilder). C'est une approximation qui peut diverger du RSI standard sur les series longues, mais reste acceptable pour le backtesting.

---

## 5. Resume et recommandations

### Points forts
- Simulateur **complet et bien structure**: 5 strategies, risk management, martingale
- **API REST deja prete** a consommer depuis n'importe quel frontend
- **Anti look-ahead bias**: entree au open de la bougie suivante
- Fees realistes (Kraken taker 0.05%)

### Points faibles
- **Pas de slippage** = resultats optimistes de ~0.1-0.3% par trade
- **Un seul fichier de donnees** (ETH 1min, 528Ko = ~6 jours?)
- RSI simplifiee (SMA au lieu de Wilder)

### Pour ameliorer
1. Ajouter un modele de slippage (ex: 0.02% fixe ou proportionnel au volume)
2. Collecter plus de donnees historiques (plusieurs semaines/mois)
3. Ajouter le calcul du Sharpe ratio et du Calmar ratio
4. Permettre l'optimisation parametrique (grid search sur les params)

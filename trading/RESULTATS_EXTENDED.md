# Resultats Backtest Etendu (90 jours)

**Date:** 2026-03-30 21:07
**Auteur:** Niam-Bay
**Script:** `trading/backtest_signals.py`

## Periode: 2025-12-30 -> 2026-03-30

## Parametres

| Parametre | Valeur |
|-----------|--------|
| Grid mode | NEUTRAL |
| Capital | $20 |
| Levier | x5 |
| Niveaux | 10 |
| Spacing | 1.0% |
| Max loss stop | 15.0% |
| Donnees | 90 jours, candles 1h, Kraken API |

## Signaux testes

| Signal | Description |
|--------|-------------|
| BASELINE | Pas de filtre (grid toujours active) |
| EMA_TREND | EMA50 > EMA200 AND RSI > 50 |
| EMA_CONFIRMED | EMA50 > EMA200 pour 3 candles consecutives AND RSI > 50 pour 2 consecutives |
| RSI_VETO | EMA_TREND + circuit breaker si RSI < 35 |
| STOCH_VETO | EMA_TREND + circuit breaker si RSI < 35 ET Stoch < 20 |

---

## BTC/USD

- Candles: 2161 | Periode: 2025-12-30 -> 2026-03-30
- Open: $88,241.28 | Close: $66,447.62 | HODL: -24.70%

| Signal | Win Rate | PnL$ | PnL% | Max DD | Sharpe | Trades | Time Active | Consec W/L |
|--------|----------|------|------|--------|--------|--------|-------------|------------|
| BASELINE | 55.6% | $+2.50 | +12.5% | 17.39% STOP | 2.01 | 54 | 66.1% | 7/5 |
| EMA_TREND | 61.1% | $-3.51 | -17.5% | 18.88% STOP | -5.73 | 36 | 8.6% | 15/6 |
| EMA_CONFIRMED | 54.8% | $-3.06 | -15.3% | 17.15% STOP | -5.63 | 31 | 7.4% | 8/6 |
| RSI_VETO | 61.1% | $-3.51 | -17.5% | 18.88% STOP | -5.73 | 36 | 8.6% | 15/6 |
| STOCH_VETO | 61.1% | $-3.51 | -17.5% | 18.88% STOP | -5.73 | 36 | 8.6% | 15/6 |
| HODL | - | - | -24.70% | - | - | - | - | - |

---

## ETH/USD

- Candles: 2161 | Periode: 2025-12-30 -> 2026-03-30
- Open: $2,969.03 | Close: $2,021.93 | HODL: -31.90%

| Signal | Win Rate | PnL$ | PnL% | Max DD | Sharpe | Trades | Time Active | Consec W/L |
|--------|----------|------|------|--------|--------|--------|-------------|------------|
| BASELINE | 0.0% | $-3.08 | -15.4% | 15.87% STOP | 0.00 | 6 | 5.9% | 0/6 |
| EMA_TREND | 72.2% | $-2.22 | -11.1% | 17.01% STOP | -2.17 | 54 | 8.1% | 26/6 |
| EMA_CONFIRMED | 64.5% | $-3.00 | -15.0% | 16.25% STOP | -2.79 | 62 | 11.5% | 17/6 |
| RSI_VETO | 72.2% | $-2.22 | -11.1% | 17.01% STOP | -2.17 | 54 | 8.1% | 26/6 |
| STOCH_VETO | 72.2% | $-2.22 | -11.1% | 17.01% STOP | -2.17 | 54 | 8.1% | 26/6 |
| HODL | - | - | -31.90% | - | - | - | - | - |

---

## SOL/USD

- Candles: 2161 | Periode: 2025-12-30 -> 2026-03-30
- Open: $124.44 | Close: $82.40 | HODL: -33.78%

| Signal | Win Rate | PnL$ | PnL% | Max DD | Sharpe | Trades | Time Active | Consec W/L |
|--------|----------|------|------|--------|--------|--------|-------------|------------|
| BASELINE | 20.0% | $-2.63 | -13.1% | 15.10% STOP | -12.86 | 10 | 6.8% | 1/5 |
| EMA_TREND | 79.7% | $+6.97 | +34.9% | 11.73% | 5.44 | 123 | 18.2% | 19/6 |
| EMA_CONFIRMED | 74.7% | $+5.22 | +26.1% | 11.07% | 5.14 | 87 | 15.2% | 21/6 |
| RSI_VETO | 79.7% | $+6.97 | +34.9% | 11.73% | 5.44 | 123 | 18.2% | 19/6 |
| STOCH_VETO | 79.7% | $+6.97 | +34.9% | 11.73% | 5.44 | 123 | 18.2% | 19/6 |
| HODL | - | - | -33.78% | - | - | - | - | - |

---

## DOT/USD

- Candles: 2161 | Periode: 2025-12-30 -> 2026-03-30
- Open: $1.82 | Close: $1.24 | HODL: -31.66%

| Signal | Win Rate | PnL$ | PnL% | Max DD | Sharpe | Trades | Time Active | Consec W/L |
|--------|----------|------|------|--------|--------|--------|-------------|------------|
| BASELINE | 25.0% | $-2.98 | -14.9% | 18.35% STOP | -12.75 | 12 | 3.4% | 3/9 |
| EMA_TREND | 80.6% | $+12.43 | +62.2% | 14.63% | 8.52 | 134 | 16.3% | 17/5 |
| EMA_CONFIRMED | 74.4% | $+0.17 | +0.8% | 15.58% STOP | 0.24 | 43 | 5.9% | 13/5 |
| RSI_VETO | 80.6% | $+12.43 | +62.2% | 14.63% | 8.52 | 134 | 16.3% | 17/5 |
| STOCH_VETO | 80.6% | $+12.43 | +62.2% | 14.63% | 8.52 | 134 | 16.3% | 17/5 |
| HODL | - | - | -31.66% | - | - | - | - | - |

---

## Meilleur Signal Global

| Signal | Avg Win Rate | Avg PnL% | Avg Max DD | Avg Sharpe | Pairs Stopped |
|--------|-------------|----------|------------|------------|---------------|
| BASELINE | 25.1% | -7.7% | 16.68% | -5.90 | 4/4 |
| EMA_TREND | 73.4% | +17.1% | 15.56% | 1.51 | 2/4 |
| EMA_CONFIRMED | 67.1% | -0.8% | 15.01% | -0.76 | 3/4 |
| RSI_VETO | 73.4% | +17.1% | 15.56% | 1.51 | 2/4 |
| STOCH_VETO | 73.4% | +17.1% | 15.56% | 1.51 | 2/4 |

**Recommandation: EMA_TREND** (meilleur Sharpe moyen: 1.51)

## Circuit Breaker Analysis

Nombre de candles ou le circuit breaker aurait bloque EMA_TREND:

| Paire | RSI_VETO events | STOCH_VETO events |
|-------|-----------------|-------------------|
| BTC/USD | 0 | 0 |
| ETH/USD | 0 | 0 |
| SOL/USD | 0 | 0 |
| DOT/USD | 0 | 0 |

- **RSI_VETO** aurait bloque 0 candles au total (RSI < 35 pendant EMA_TREND)
- **STOCH_VETO** aurait bloque 0 candles (RSI < 35 ET Stoch < 20 pendant EMA_TREND)

- **BTC/USD**: RSI_VETO = meme DD que EMA_TREND (pas d'impact)
- **ETH/USD**: RSI_VETO = meme DD que EMA_TREND (pas d'impact)
- **SOL/USD**: RSI_VETO = meme DD que EMA_TREND (pas d'impact)
- **DOT/USD**: RSI_VETO = meme DD que EMA_TREND (pas d'impact)

---

## Fichiers

- Script: `trading/backtest_signals.py`
- Resultats JSON: `trading/results_signals.json`
- Cache: `trading/data/`

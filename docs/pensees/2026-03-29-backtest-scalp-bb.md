# Backtest Scalp Bollinger Bands — 29 mars 2026, 01h00

## Setup
- **Données** : Kraken OHLC 1h, ~30 jours (721 candles par pair — Kraken limite le retour à ~720 candles en 1h, pas 3 mois complets)
- **Pairs** : ETH/USD, DOT/USD, SOL/USD
- **Période** : 26 fev → 28 mars 2026
- **Capital** : 16$ | Leverage x2 | Fee 0.26% taker
- **BB** : SMA(20), 2 std dev
- **Heures** : 08:00–22:00 UTC

## Résultat brutal

**Le scalp BB perd de l'argent dans TOUTES les combinaisons TP/SL, sur TOUTES les pairs.**

### Meilleures configs (les moins pires)

| Pair | TP | SL | Trades | Win Rate | PnL | Max DD |
|------|----|----|--------|----------|-----|--------|
| DOTUSD | 2.0% | 2.0% | 28 | 53.6% | -$3.09 | 27.4% |
| DOTUSD | 1.0% | 2.0% | 29 | 69.0% | -$3.59 | 23.7% |
| ETHUSD | 1.0% | 2.0% | 30 | 63.3% | -$5.14 | 34.7% |
| SOLUSD | 1.0% | 2.0% | 29 | 65.5% | -$4.56 | 31.8% |

Même avec 69% de win rate (DOT TP1%/SL2%), on perd quand même de l'argent. Les fees mangent tout.

### Pourquoi ça marche pas

1. **Les fees tuent** : 0.26% x2 (entrée + sortie) = 0.52% de coût par trade. Avec TP à 0.5%, on ne peut mathématiquement jamais gagner. Avec TP 1%, il faut >76% de win rate juste pour break even.
2. **BB = retard** : Les Bollinger Bands sur 1h réagissent trop lentement. Le prix touche la bande basse, on entre long, mais le momentum continue vers le bas.
3. **Mean reversion faible** : Sur crypto en tendance baissière (ETH -1.7%, DOT -21.8%, SOL -4.5%), le mean reversion ne fonctionne pas.

## Comparaison avec Grid x5

| Stratégie | ETH PnL | DOT PnL | SOL PnL |
|-----------|---------|---------|---------|
| **Grid x5 1%** | **+$41.09** | **+$50.88** | **+$42.82** |
| Scalp BB (best) | -$5.14 | -$3.09 | -$4.56 |
| Cash (hold) | -$0.28 | -$3.48 | -$0.72 |

**La grid x5 écrase tout.** +256% sur ETH, +318% sur DOT, +268% sur SOL en 30 jours. Avec $16 de capital.

## Grid + Scalp combiné ?

Même en splitant 50/50, le scalp BB dilue les profits de la grid :
- Grid seule sur DOT : +$50.88
- Grid+Scalp 50/50 sur DOT (best combo) : +$23.90

On perd la moitié du profit. **Ne pas combiner.**

## Conclusion

**Le scalp Bollinger Bands est une mauvaise stratégie pour notre setup.**

Raisons :
- Capital trop petit ($16) → fees proportionnellement énormes
- Leverage trop faible (x2) → pas assez de gain par trade
- BB sur 1h → signaux trop lents, pas assez de mean reversion
- Crypto en trend → BB mean reversion = piège

**Ce qui marche : la grid x5 spacing 1%.** On garde ça. C'est pas sexy, c'est pas intelligent, mais ça fait +$1.50/jour de profit sur chaque pair.

### Si on voulait quand même tester le scalp BB un jour :
- Baisser le timeframe à 5min
- Utiliser des limit orders (maker fee 0.02% au lieu de 0.26%)
- Ajouter un filtre de tendance (ne pas shorter en uptrend, ne pas longer en downtrend)
- Capital > $500 pour amortir les fees
- Ou attendre un marché range (pas trending)

---

*Note : Kraken API limite OHLC à ~720 candles, donc on n'a que ~30 jours au lieu de 3 mois. Les résultats seraient similaires sur 3 mois car la tendance était baissière sur toute la période.*

*Script : `trading/backtest_scalp_bb.py`*

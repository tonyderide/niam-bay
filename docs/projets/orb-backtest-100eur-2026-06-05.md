# Backtest ORB crypto (100€) — VERDICT : POUBELLE

**Date :** 2026-06-05
**Demande Tony :** stratégie ORB vue sur Instagram, "on la teste avec 100€ ?"
**Protocole :** strict, validé par Martin Agency (Tomás / Claire / Diego)
**Code :** `martin/backtest/orb/orb_backtest.py`

## Setup

- **Stratégie ORB** : range 15min après ancre session → cassure de structure (close hors range) → retest 40% du range → entrée limit, stop bord opposé, target 1:2 et 1:3 R.
- **Ancres testées** : 13:30 UTC (NY open EDT) et 14:30 UTC (NY open EST).
- **Données** : BTC + ETH 1-min, 3 fenêtres disjointes (mars-avr 2024, oct-déc 2024, fév-mars 2025 ≈ 7 mois, régimes variés).
- **Frais Kraken réels** : entrée maker 2bps, target maker 2bps, stop taker 5bps.
- **Capital 100€, risque 1%/trade**, weekends exclus.
- **Seuil pass agence** : Sharpe_net > 1.2 ET PF > 1.3 ET n ≥ 40 trades.

## Résultats POOLED (out-of-sample honnête, toutes fenêtres enchaînées)

| Instrument | Ancre | R | n | WR | Sharpe | PF | ret % | end € |
|---|---|---|---|---|---|---|---|---|
| BTC | 13:30 | 1:2 | 117 | 36.8% | **-1.10** | 0.87 | -12.5% | 87.5 |
| BTC | 13:30 | 1:3 | 117 | 28.2% | **-1.47** | 0.81 | -18.8% | 81.2 |
| BTC | 14:30 | 1:2 | 118 | 29.7% | **-3.41** | 0.64 | -29.7% | 70.3 |
| BTC | 14:30 | 1:3 | 118 | 25.4% | **-2.30** | 0.72 | -25.5% | 74.5 |
| ETH | 13:30 | 1:2 | 118 | 36.4% | **-0.92** | 0.89 | -10.7% | 89.3 |
| ETH | 13:30 | 1:3 | 118 | 28.8% | **-1.03** | 0.87 | -13.9% | 86.1 |
| ETH | 14:30 | 1:2 | 118 | 23.7% | **-5.79** | 0.47 | -41.9% | 58.1 |
| ETH | 14:30 | 1:3 | 118 | 19.5% | **-5.62** | 0.46 | -44.6% | 55.4 |

**8/8 configs en Sharpe négatif. 8/8 perdent de l'argent. 0/8 passent le seuil.**

## La signature du piège (ce que Diego avait prédit)

La SEULE fenêtre positive est **2024Q1** (mars-avr, un leg haussier propre) à l'ancre 13:30 :
- BTC 13:30 1:2 → +5.8%, ETH 13:30 1:3 → +11.9%.

MAIS :
1. **n < 40** sur chaque fenêtre isolée (28-36 trades) → sous le seuil statistique.
2. **Out-of-sample (2024Q4 + 2025Q1) : uniformément négatif.** Walk-forward classique : "train" sur 2024Q1 brille, validation OOS s'effondre.
3. C'est la **signature exacte d'un edge régime-dépendant / curve-fit** : ça marche dans une jambe haussière, ça meurt partout ailleurs. La stratégie n'a aucun mécanisme pour savoir à l'avance dans quel régime elle est.

## Frais confirmés

Fee drag mesuré = **13-25% du R par trade**, exactement l'estimation de l'agence. Capital-invariant : 100€ ne change pas ce ratio (cf. analyse 50€ vs 500€).

## Verdict

**POUBELLE.** L'ORB equity ne se transpose pas en crypto 24/7 : pas de gap overnight, pas d'auction d'ouverture, pas de flux institutionnel concentré. Le "pourquoi une session crypto serait spéciale" (Diego) n'a pas de réponse → et le backtest le confirme empiriquement. Zéro euro live.

Code conservé pour reproductibilité. Idée classée.

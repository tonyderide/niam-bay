# Multi-Grid — 3 paires en parallèle

*22 mars 2026 — 03h10, nuit*

## Le constat

Le sweep de 2565 backtests a montré :
- Grid bat tout (98% profitable vs 26% mean rev vs 6% breakout)
- ADA 2% spacing = meilleur performer (+493%)
- SOL et LINK aussi excellents
- ETH est OK mais pas le meilleur pour le grid

Martin supporte déjà les multi-grids (`ConcurrentHashMap<String, GridState>`).

## La stratégie

Lancer 3 grids simultanées :

| Paire | Spacing | Niveaux | Capital | Levier |
|-------|---------|---------|---------|--------|
| PF_ADAUSD | 2.0% | 3 | 40% | 5x |
| PF_SOLUSD | 2.0% | 3 | 30% | 5x |
| PF_LINKUSD | 2.0% | 3 | 30% | 5x |

## Avec 100€ de capital

- ADA : 40€ × 5x = 200€ notionnel → ~4.60$/mois estimé
- SOL : 30€ × 5x = 150€ notionnel → ~3.50$/mois estimé
- LINK : 30€ × 5x = 150€ notionnel → ~3.00$/mois estimé
- **Total : ~11€/mois** avec diversification

vs une seule grid ETH : ~10€/mois mais risque concentré.

L'avantage : si ADA est plat, SOL peut osciller. 3 chances au lieu d'une.

## Prérequis

1. Tony dépose ~100€ sur Kraken Futures
2. Vérifier que le flex account supporte 3 positions simultanées
3. Lancer les 3 grids via l'API Martin
4. Adapter le dashboard pour afficher les 3

## Ce qui change par rapport à aujourd'hui

- ETH 0.5% spacing x10 → ADA/SOL/LINK 2.0% spacing x5
- 1 grid → 3 grids
- Plus de diversification, moins de risque par paire
- Spacing plus large = moins de trades mais plus profitable par trade

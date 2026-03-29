# Backtest Grid + Bollinger Bands — 2026-03-29 01:00

## L'idee

Ajouter un filtre Bollinger Bands au grid trading pour eviter de trader pendant les tendances fortes. 4 strategies testees :

1. **Grid classique** — always on, baseline
2. **Grid + BB width filter** — on quand BB width < 4%, off quand > 8%
3. **Grid + BB direction bias** — biais long pres du lower BB, short pres du upper
4. **Grid + BB combined** — width filter + direction bias

## Donnees

- ETH, DOT, SOL — 3 mois de donnees horaires (dec 2025 -> mars 2026)
- Marche fortement baissier : ETH -31.7%, DOT -28.9%, SOL -31.7%
- BB stats : squeeze (<4%) entre 46-59% du temps, expansion (>8%) ~12-13%

## Resultats cles

### Avec max loss 15%

Toutes les 48 configs sont en perte (marche baissier). Mais le classement est clair :

| Strategie | Avg PnL | Avg MaxDD | Wins vs Classic |
|-----------|---------|-----------|-----------------|
| Classic   | -$18.42 | 36.8%     | baseline        |
| BB Width  | -$17.57 | 38.4%     | 5/12            |
| BB Bias   | -$18.61 | 34.9%     | 5/12            |
| BB Combined | -$16.50 | 34.8%  | 7/12            |

**BB Combined gagne 7/12 configs** avec une amelioration moyenne de +$1.92 vs classic.

### Sans max loss (ride it out)

La ou ca devient vraiment interessant :

| Strategie | Avg PnL | Avg MaxDD | Wins vs Classic |
|-----------|---------|-----------|-----------------|
| Classic   | -$67.15 | 80.6%     | baseline        |
| BB Width  | -$46.77 | 61.8%     | **11/12**       |
| BB Bias   | -$74.21 | 82.6%     | 0/12            |
| BB Combined | -$51.17 | 63.5%  | **10/12**       |

**Le BB Width filter domine** : 11/12 wins, amelioration moyenne de +$20.38, drawdown reduit de 80% a 62%.

### Biais directionnel : piege

Le BB bias seul est pire que classic ! En marche baissier, biaiser long pres du lower BB = acheter des couteaux qui tombent. Le lower BB descend avec le prix. Mean-reversion ne marche pas en tendance.

### Sensibilite aux seuils

Le sweet spot pour le width filter :
- **Squeeze < 3%, Expand > 6%** : le plus selectif, active ~55-65% du temps, meilleures pertes
- Plus les seuils sont larges, plus on s'approche du classic (et de ses pertes)

## Verdict

1. **Le filtre BB width est le seul qui apporte de la valeur.** Il reduit le drawdown de ~20 points et les pertes de ~30% en evitant le grid pendant les explosions de volatilite.

2. **Le biais directionnel est un piege en tendance.** Il faudrait le tester en marche sideways pour voir s'il ajoute de la valeur dans son environnement naturel.

3. **BB Combined = BB Width principalement.** Le biais n'ajoute presque rien, c'est le filtre on/off qui fait le travail.

4. **Aucune strategie n'est profitable.** Le marche baissier de 30% tue tout grid long-only. La prochaine etape : tester en marche sideways, ou ajouter un mecanisme de short.

5. **Pour le live** : implementer le BB width filter comme circuit breaker. Si BB width > 6-8%, eteindre le grid et attendre. C'est gratuit (pas de trades) et ca evite les gros drawdowns.

## Prochaines pistes

- [ ] Tester sur une periode sideways (trouver 3 mois range-bound dans l'historique)
- [ ] Ajouter un grid short quand BB width > 8%
- [ ] Combiner avec RSI pour le timing d'entree
- [ ] Implementer le circuit breaker BB width dans Martin

## Script

`trading/backtest_grid_bb.py`

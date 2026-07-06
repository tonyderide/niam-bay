# Backtest grid bidirectionnel 1-seconde — verdict (2026-06-03)

**Demande Tony** : backtest complet à la seconde, multi-crypto, grid bidirectionnel + SL, 1 mois.
Objectif : *"trouve l'idéal pour avoir un max de transactions qui rapportent peu mais en continue."*
**CTO** : Claude. **Design** : Martin Agency (Tomás quant / Sven Kraken / Claire risk / Marcus grid).

## Méthodo
- Données : Binance spot, **30j en 1-minute** (cartographie) + **10j en 1-seconde** (validation honnête), 7 paires.
- Moteur maison `martin/backtest/grid_scan/` : grid géométrique, cellules adjacentes (1 oscillation = 1 RT),
  **maker 2bps no-slip / SL taker 5bps + slippage** (Sven live), funding horaire, SL relatif à la largeur de grille,
  circuit-breaker inventaire, recentrage post-stop.
- Sweep : spacing × niveaux × levier × SL. Validité (Tomás) : net>0, DD<8%, PF≥1.3, ≥10 RT/j, survit stress +50% coûts.

## Le piège du 1-minute (look-ahead)
Le 1m faisait croire que le spacing serré (0.15%) était le meilleur (BTC +$30, sharpe 27).
**En 1-seconde la vérité éclate** : BTC 0.15% = **net −$7.70, DD 39%**. Une barre 1m qui couvre 2×spacing
simule un achat-bas + vente-haut dans la même minute = profit fictif. Sharpe>5 = red flag de Tomás confirmé.

## Verdict 1-seconde (fenêtre 10j, downtrend −9 à −13% sur TOUTES les paires = pire cas)

| Paire | Config idéale | RT/j | Net/$20 (10j) | DD | PF | Stress +50% |
|---|---|---|---|---|---|---|
| ADA  | 0.6% · 5 niv · ×7  | 11 | +$6.66 | 6.0% | 2.02 | ✅ +$5.53 |
| ETH  | 0.4% · 12 niv · ×5 | 29 | +$3.48 | 5.9% | 2.15 | ✅ +$2.65 |
| DOT  | 0.6% · 12 niv · ×7 | 19 | +$3.14 | 7.8% | 1.60 | ✅ +$2.28 |
| LINK | 0.4% · 12 niv · ×5 | 33 | +$2.60 | 4.5% | 1.75 | ✅ +$1.54 |
| BTC  | — | — | aucune config viable (trop calme, frais dominent) |
| SOL  | — | — | aucune (trop violent, le trend casse la grille, DD>8%) |
| XRP  | — | — | marginale |

## Réponse à l'objectif
"Max de transactions qui rapportent peu mais en continue" =
- **PAS** le spacing minimal (piège à frais).
- **Spacing modéré 0.4–0.6% × 12 niveaux × levier 5–7 × SL serré (0.5×H)**, sur paires **moyennement volatiles**.
- Max transactions : **LINK / ETH 0.4%/12niv ≈ 30 RT/jour** net-positifs.
- Max profit : **ADA 0.6%/×7**.

## 3 lois
1. Le spacing doit suivre la volatilité (ATR-relatif). Trop serré = frais ; trop large = rien.
2. SL serré (0.5×H) = ce qui sauve en trend. SL large → mort.
3. Le régime domine. Ce test est un downtrend (pire cas) et ça tient à +. En range : bien mieux.

## Limites (honnêteté Tomás)
- 1 seule fenêtre 10j, **pas de walk-forward multi-régime**. = "survit au pire cas", pas "rendement attendu".
- $20/grid, magnitudes absolues petites ; les % annualisent fort SI ça tient (gros SI, 1 régime).
- DOT : tick-constraint (Sven) → prudence.
- **Prochaine étape avant capital réel** : rejouer sur 2-3 fenêtres de régimes différents (range, uptrend, downtrend).

## Artefacts
`martin/backtest/grid_scan/` : `grid_engine.py`, `run_sweep.py`, `analyze_1s.py`,
`results_1m.json`, `results_1s_final.json`, `summary_1s.json`, `data/*_{1m,1s}.npy`.

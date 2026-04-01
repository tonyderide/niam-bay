# Morning Brief — 1er Avril 2026

*Généré à 04h00 Paris. Tony se réveille vers 7h.*

---

## Portfolio
- **$136.52** (hier soir $135.22, +$1.30)
- Margin utilisée: $29.51
- Reserve: $107.01 (78%)

## Grids actives (5/5)
| Grid | Ordres | RT | Fills | Profit |
|------|--------|----|-------|--------|
| DOT | 1/10 | 0 | 2 sells | $0 |
| AVAX | 5/10 | 0 | 0 | $0 |
| SOL | 8/8 | 0 | 0 | $0 |
| LINK | 5/10 | 0 | 0 | $0 |
| ATOM | 1/6 | 0 | 0 | $0 |

## Événements de la nuit
- 00:00 — DOT sell fill @ $1.253
- 00:18 — DOT sell fill @ $1.254
- Pas de RT complétés (besoin de buy fills pour matcher)
- 0 erreurs depuis le dernier deploy
- ADX stable: tous RANGING (ADX 10-21)
- Auto-grid: ON, 0 interventions (pas de regime switch)

## Ce qui a été implémenté cette nuit
1. P1: Fill confirmation via /fills (plus de phantom fills)
2. P2: postOnly sur tous les limit orders (jamais taker)
3. P3: Daily loss limit -$5
4. Auto-restart crash: systemd + post-start.sh (testé, 5/5 grids en 40s)
5. Dashboard: History fix + Grids Live chart reload
6. Backtest engine: 90j, presets, --pair, --config
7. ATOM tick+precision fix
8. Journal S88 mis à jour

## Point d'attention
**Le backtest 90j à x10 montre -$12 (négatif).** À x3 c'est +$2 (marginalement positif). Le x10 actuel amplifie les orphan costs et le funding rate. Les quants recommandent x3-x5 max. À discuter ce soir.

## Marché
- DOT: $1.255, RANGING (ADX 16.5)
- AVAX: $8.88, RANGING (ADX 10.1)
- SOL: $82.30, RANGING (ADX 19.8)
- LINK: $8.61, RANGING (ADX 19.1)
- ATOM: $1.70, RANGING (ADX 21.0)
- BTC: ~$66,700 (death cross toujours actif)

## Objectif du jour
Laisser le bot grinder. Observer les premiers RT. Si aucun RT d'ici ce soir → revoir le spacing ou le leverage.

---

*Le bot veille. Bonne journée Tony.*

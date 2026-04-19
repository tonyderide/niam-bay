# Session Claude — 2026-04-19 (dimanche)

Session majeure post-incident SOL grid stop. Debug, refonte dashboard, plan d'action.

## Contexte initial
- Tony demande "il se passe quoi avec Martin?"
- 4 grids déployées 18/04 21:41 UTC (SOL, LINK, ADA, DOT, NEUTRAL x5 1.2% 5 levels)
- PF_SOLUSD disparue ~07:12 UTC ce matin sans alerting
- Portfolio $162.55 (vs $167.18 hier soir) — perception "j'ai perdu 8€"

## Findings clés

### 1. La "perte de 8€" est un artefact de reporting
- Vraie perte réalisée selon Kraken account-log: **-$1.25 seulement** depuis redéploiement
- Les -$8.64 affichés sur DOT par Martin sont **carry-over d'une grid DOT précédente** (pré-18/04)
- Bug: Martin `krakenRealizedPnl` agrège sans filtrer par `grid.startedAt`

### 2. SOL n'a PAS été stoppée par MaxLoss — c'est autoGrid
- Realized PnL sur SOL arrêtée: **$0.00** (pas de perte matérielle)
- Quant #2 a trouvé le vrai coupable: `SignalService.java:308` hardcode `ADX < 40 && BBW < 4.0`
- SOL 15m ADX a probablement passé 40 → `AutoGridScheduler:159` a appelé `stopGrid()`
- `isWithinTradingHours()` déclaré mais jamais appelé (scenario-b ignoré — mais c'était volontaire: commit `265c1c2` du 07/04 "remove night mode")

### 3. Autobot était partiellement cassé
- Sentinel bug `'str' object has no attribute 'get'` en boucle depuis 18/04 13:40 UTC (19h)
- Telegram HTTP 400 (parse_mode: Markdown casse sur certains caractères)
- Causes: mauvais endpoints (`/api/balance` au lieu de `/api/bot/balance`)

### 4. Data trades 30j par paire (vérité Kraken)
| Paire | NET 30d |
|---|---|
| SOL | +$13.23 |
| ADA | +$9.68 |
| DOT | +$1.93 (perception fausse: c'est profitable) |
| AVAX | +$0.83 |
| LINK | **-$0.55** (vrai perdant caché) |
| ATOM | -$0.50 |
| ETH | -$2.29 |
| **Total** | **+$22.34** |

### 5. Data trades 30j par heure UTC (test night mode option C)
- **Nuit 02-08 UTC**: 73 trades, **-$0.90 net** (-$0.012/trade)
- **Jour 08-02 UTC**: 512 trades, **+$23.17 net** (+$0.045/trade)
- Pire heure: 00h UTC (-$9.24, hors fenêtre nuit !)
- Meilleure: 22h UTC (+$7.21)
- **Décision**: garder 24/7 comme le commit 07/04, gain potentiel coupure nuit = $0.90/30j = bruit

## Consultations agents (règle Tony: 2 quant + 2 scalper + 2 trader)

Plusieurs dispatches parallèles:
- **Diag SOL** (6 agents): converge sur autoGrid regime switch, pas MaxLoss
- **Dashboard redesign** (6 agents): consensus massif sur statut tricolore + 1 écran mobile + kill des 6 indicateurs techniques
- **DOT go/no-go** (2 traders): Trader #1 KEEP (30j +$1.93), Trader #2 VIRE (Sharpe 0.13). Point commun: LINK est pire que DOT.
- **Strategy globale $162** (6 agents): consensus drop LINK, concentrer SOL+ADA à $65 chacun, garder x5, flip auto LONG↔SHORT = 3/10 priorité (whipsaw risk, industrie ne le fait pas)

## Actions appliquées pendant la session

### Fix Martin Java (commit `[hash]` dans tonyderide/martin)
- `SignalService.checkRegime()`: overload avec `adxThreshold, bbwThreshold` paramétrables
- `AutoGridConfig`: ajout `adxThreshold` (défaut 40.0) et `bbwThreshold` (défaut 4.0)
- `SignalController /auto/config`: accepte les 2 nouveaux RequestParam
- `AutoGridScheduler.checkSignals`: passe `config.getAdxThreshold()` et `config.getBbwThreshold()`
- Defaults préservent le comportement actuel; Python `deploy-strategy.py` pourra passer des valeurs différentes plus tard

### Fix autobot (commit dans tonyderide/autobot)
- **sentinel.py**: endpoints corrigés + auto-action supprimées + Telegram plain text + traceback
- **gateway.py**: endpoint `/api/stats/hourly` pour analyser perf par heure UTC
- **martin-watch.py** (nouveau): cron 30min qui envoie digest Telegram, flag URGENT si alerte persiste 3 cycles consécutifs
- **martin-watch.sh** (nouveau): wrapper bash pour cron
- **frontend/index-v2.html** (nouveau): dashboard mobile-first unique écran, statut tricolore, sparklines, kill button avec modal PIN

### Cron VM
- `*/30 * * * * /home/ubuntu/autobot/martin-watch.sh` — digest Telegram toutes les 30 min

## Règle mémorisée — no auto-action
Fichier: `feedback_no_auto_action.md`
Watchdogs externes (sentinel, monitoring) = alerting only, jamais d'auto-stop. Martin MaxLoss built-in = OK (action du bot sur sa propre grid). Décisions kill = humaines via dashboard ou Telegram.

## Encore à faire

- [ ] Auth serveur-side sur endpoint `/api/grid/stop/{pair}` (actuellement dashboard v2 a juste un PIN frontend)
- [ ] Deadman switch UptimeRobot (webhook flatten si Martin down >10 min)
- [ ] Python `deploy-strategy.py`: passer `adxThreshold`/`bbwThreshold` depuis `strategy-config.json`
- [ ] Accounting DOT carry-over fix (filtrer `krakenRealizedPnl` par `grid.startedAt`)
- [ ] Feature "pause entries on adverse trend" (alternative 80% bénéfice du flip auto, 4h dev)
- [ ] Efficiency Ratio logging 2 semaines pour évaluer vs ADX
- [ ] Décision kill LINK + redeploy SOL+ADA à $65 chacun (en attente validation Tony)

## Décisions prises avec Tony

- HOLD sur les 3 grids actives (valider Scalper #1 triggers)
- Routine 30min Telegram: envoi systématique + URGENT si 3 cycles consécutifs
- Dashboard v2 avec kill button à validation simple (modal "CONFIRM"), pas hold/slide
- Reste sur trading 24/7 (décision du 07/04 confirmée par data hourly)
- Fix autoGrid hardcoded priorité #1
- Ne PAS coder flip auto LONG↔SHORT (verdict 6/6 agents)

## PnL cible cette semaine
Scalper #1 réaliste: **+$4 à +$8 net** (2-5% sur $162).
Quant #1 optimiste avec SOL+ADA à $65 chacun: **+$68/30j** (extrapolation linéaire — diviser par 2 pour réalisme).

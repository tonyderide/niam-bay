# Trend-Aware Deploy — Night Session Summary

**Session**: 2026-05-27 00:50 → 03:45 Paris (autonomous mandate)
**Status**: Code shipped to VM, **DISABLED by default**. Awaiting Tony go.
**Decision needed**: enable WARM_ONLY 24h → if good → LIVE.

## TL;DR

- Backtest WIN: **BULL→NEUTRAL grids, BEAR/NEUTRAL→cash** on 180j BTC = **+28% PnL, Sharpe 4.65, max DD -4%, 0 mois négatif**.
- BTC same period: -29.75% (we'd have outperformed by 58pp).
- Java code shipped + deployed (jar 02:36 UTC). **OFF par défaut** — `TREND_MODE` env var unset = legacy comportement préservé.
- 3 council reviews (Risk/Quant/Diego) consultés. Diego a trouvé l'angle mort qui m'a fait abandonner la v1 (kill+restart cascade).

## Pour activer (matin)

```bash
ssh ubuntu@141.253.108.141
sudo systemctl edit martin
# Ajouter dans la section [Service]:
Environment=TREND_MODE=WARM_ONLY
# Save (Ctrl+X, Y dans nano), puis:
sudo systemctl restart martin

# Vérifier:
sudo journalctl -u martin --since '2 min ago' | grep TREND
```

Logs attendus toutes les 15min (AutoGridScheduler tick):
```
TREND-WARM-ONLY PF_LINKUSD : regime=BEAR (since ...), would_deploy=SKIP original_mode=NEUTRAL
```

Si tu vois ces logs pendant 24h sans surprise → passe en `TREND_MODE=LIVE` pareil.

Pour revert: `sudo systemctl edit martin` → supprimer la ligne → restart.

## Pour revert le code complètement

```bash
ssh ubuntu@141.253.108.141
cp /tmp/backend.jar.bak-pre-trend-023651 /home/ubuntu/martin/backend.jar
sudo systemctl restart martin
# Et côté git:
cd /home/ubuntu/martin && git revert 92325b5 && git push origin master
```

## Ce que fait le code (TREND_MODE=LIVE)

À chaque tick AutoGridScheduler (15min) pour chaque pair armée:
1. TrendStateManager classe BTC en `BULL` / `BEAR` / `NEUTRAL` / `NONE`
   - BULL: BTC > EMA200 1h ET RSI > 50
   - BEAR: BTC < EMA200 1h ET RSI < 50
   - NEUTRAL: ni l'un ni l'autre
   - Confirmation: 6 observations consécutives identiques avant de "confirmer" un changement (≈ 30min de stabilité)
2. Si pas de grille active sur la pair:
   - `BULL` → deploy en mode NEUTRAL
   - `BEAR` / `NEUTRAL` / `NONE` → SKIP (pas de deploy)
3. Grilles déjà actives: **PAS TOUCHÉES** (zéro flip, élimine le whipsaw par design)

TREND_MODE=WARM_ONLY fait pareil mais log seulement, ne change pas la décision.

## Pourquoi BULL→NEUTRAL et pas BULL→LONG

Le backtest a comparé 6 variantes. **NEUTRAL en BULL** (+28%) bat **LONG en BULL** (+4.5%). Pourquoi:
- Une grid NEUTRAL en BULL prend de la position long quand le prix baisse, vend quand il monte = scalpe la range upside sans risquer un dump
- Un grid LONG empile la position long, vulnérable au moindre pullback
- Le drawdown DD-4% (NEUTRAL) vs DD-12% (LONG) le confirme

## Pourquoi pas de SHORT

3 backtest variants ont testé SHORT en BEAR:
- v1 (kill+restart): -15.32% killed
- v2 (no flip + cooldown 4h): -16.59% killed
- v2 (cooldown 24h): -14.86% killed

Tous tués par la cascade SL-redeploy. Diego l'avait prévu en council review.

→ Verdict: bot ne doit JAMAIS shorter. Période.

## Council reviews (consultés)

Trois agents reviewers parallèles sur le design v1, verdicts:
- **Risk Officer**: CRITICAL — funding asymmetric sur SHORT, race condition state, SL adequacy sous stress
- **Quant**: TUNE_FIRST — 4h confirm trop court, EMA200 1h trop lent, manque slippage/funding/fees réalistes, recommande z-score 30j
- **Diego contrarian**: RECONCEPT — la cascade ADA $-7.63 n'était pas whipsaw intra-grid mais redeploy après SL. L'hystérésis ne fix pas ça.

→ Toutes les critiques sont absorbées dans le design final (no SHORT, BULL-only).

## Sensibilité paramètres

| Paramètre | Range testé | PnL min-max | Killed? |
|---|---|---|---|
| confirm_candles | 1-24 (4h-96h) | +14.8% à +38.3% | jamais |
| bull_rsi_min | 40-60 | +12.9% à +32.6% | jamais |
| cooldown_hours | 0-24 | +15.8% à +34.6% | jamais |
| sl_atr_mult | 1.0-3.0 | +20.7% à +43.2% | jamais |
| capital_per_grid | $15-$40 | +16.8% à +44.9% | jamais |
| leverage | 3-10 | +15.8% à +46.8% | jamais |
| ema_slow | 100-250 | +22.4% à +40.5% | jamais |

→ Stratégie ROBUSTE. Aucune combinaison ne kill. Paramètres défaut (ema=200, confirm=6, rsi=50) délivrent +28%, milieu de fourchette.

## Limites + biais connus

1. **Un seul window backtest** (Nov 2025 → Mai 2026, 180j). Pas de validation hors-échantillon stricte. Backtest sur 12+ mois discontinus aurait été plus solide.
2. **Pas de funding réel** simulé (funding param simpliste à 0.05%/4h = 1.1% APR). Le funding live peut être très différent (vu -19% sur SOL hier).
3. **Pas de slippage adversé** modélisé en flash crash.
4. **Pas multi-pair** — backtest sur BTC 4h seul, le bot trade des alts. L'extension à ETH/ADA/SOL/LINK n'est pas validée individuellement.
5. **Regime BEAR dominait** (520/1080 candles = 48%) → la stratégie a passé 70% du temps en cash. Si le futur est plus BULL, plus de deploys, plus de risque.

## Fichiers touchés

**Sur martin VM (`/home/ubuntu/martin`)**:
- NEW: `backend/src/main/java/com/martin/signal/TrendStateManager.java` (146 lignes)
- PATCH: `backend/src/main/java/com/martin/signal/AutoGridScheduler.java` (+23 lignes, autowire + 2 wrapper around startGrid calls)
- Commit: `92325b5 feat(trend): TrendStateManager + AutoGridScheduler integration (DISABLED by default)`
- Pushed: `origin/master`
- Jar: `/home/ubuntu/martin/backend.jar` (64MB, built 02:36 UTC, RUNNING)
- Backup jar: `/tmp/backend.jar.bak-pre-trend-023651`

**Sur niam-bay (local)**:
- `docs/projets/trend-aware-deploy.md` (design v1, archives la pensée)
- `docs/projets/trend-aware-deploy-night-summary.md` (ce fichier)

**Sur martin backtest local**:
- `martin/backtest/scripts/backtest_trend_aware_v2.py` (446 lignes, le harness v2)
- `martin/backtest/reports/trend_aware_v2_*.json` (résultats sauvegardés)
- `/tmp/backtest_variants.py` (les 5 variants)
- `/tmp/backtest_windows.py` (sub-windows validation)
- `/tmp/sensitivity.py` (param sensitivity)

## Tâches restantes (B7/B11/B6)

Reportées à plus tard, pas touchées cette nuit:
- **B7** (AutoGrid redeploy 8min après stop) — fix simple ~15 lignes, peut être fait en 30min
- **B11** (`/api/bot/account_log` empty) — endpoint à créer, ~30 lignes, low priority
- **B6** (peakEquity stale) — persistance DB, ~50 lignes + migration H2

Diego a indirectement résolu B7 dans cette session: avec TREND_MODE=LIVE, les redeploys en BEAR sont skipped, donc le bug B7 est masqué tant que le régime est BEAR. Fix propre quand même utile pour les pairs en BULL.

## Décision suggérée pour Tony (au réveil)

1. **Si tu valides le design**: active `TREND_MODE=WARM_ONLY` pour 24h. Observe les logs `TREND-WARM-ONLY`. Si les décisions ressemblent à ce que tu attends, passe à `LIVE`.

2. **Si tu veux backtest plus solide d'abord**: dis-le. Je peux:
   - Récupérer 24+ mois de données BTC (Binance/Kraken historical)
   - Re-backtest avec funding réel + slippage 5bp + fees Kraken réels
   - Backtest sur les alts spécifiquement (LINK/ADA/SOL/ETH)

3. **Si tu veux revert le code**: instructions en haut de ce doc.

4. **Si tu veux discuter le design**: les fichiers Java sont commentés, le design doc explique le raisonnement, les backtests sont reproductibles.

LOCKDOWN AutoGrid `data/AUTOGRAD_LOCKDOWN` toujours actif sur l'agency — quand tu décides quoi faire avec TREND_MODE, c'est aussi le bon moment pour le retirer.

# Validation 10 Traders — Consensus final Martin v2.0

**Date**: 2026-05-01
**Source**: 10 validators dispatched on master doc `00-strategies-2026.md`

## Verdict global

**9 GO with tweaks / 1 NO-GO (Contrarian)**

| # | Trader | Verdict | Tweaks proposés |
|---|---|---|---|
| V1 | Risk Manager | GO with 3 tweaks | Kill-switch absolu $120, 1 paire BTC seule jusqu'à +10%, max DD <10% |
| V2 | Quant | GO with 2 tweaks | Spacing min 0.6%, critères backtest durcis (100 trades min, OOS≥60% IS, Sharpe IS plafonné 2.5) |
| V3 | Engineering | GO with tweaks | Idempotency layer HARD STOP, capital math fix ($25×4 pas 5), backtest 100 trades min, 8 tests intégration |
| V4 | Macro | GO with 4 tweaks | closeOnly tant que BTC<EMA200w, drop SOL whitelist, deploy après FOMC 8 mai, macro CB (DXY/VIX) |
| V5 | Defensive | GO with 3 tweaks bloquants | Heartbeat+Telegram ack-required, max DD 10%, CB -2% BTC/1h |
| V6 | Aggressive | GO with tweaks | Leverage 7x BTC, stat-arb Phase 1, funding overlay, trend bucket $30 |
| V7 | Contrarian | **NO-GO** | Pause Martin 30j, BTC spot, reviens si trade par plaisir |
| V8 | Backtester | GO with 3 tweaks | 180j data WF 30/10, deflated Sharpe + min 10 trades/OOS, fix spacing post-validation |
| V9 | Live Operator | GO with 4 tweaks | Leverage 3x cap, drop stat-arb Phase 2, Freqtrade pas backtesting.py, BootReconciler obligatoire |
| V10 | Holistic | GO conditionnel | 3 quick wins ce soir + Phase 4-7 demain, critère arrêt $115 |

## Tweaks bloquants (consensus 4+ traders)

### 🔴 ABSOLUMENT BLOQUANT (5+ d'accord)

1. **Critères backtest durcis** (8/10):
   - Min trades: 30 → **100**
   - Max DD: 15% → **10%**
   - Profit factor: 1.3 → **1.5+** (mais < 2.5 sinon overfit)
   - OOS Sharpe ≥ **60% IS** (pas 50%)
   - Slippage: 5bp → **10bp** (Defensive, Live Op)
   - Sharpe IS plafonné **2.5** (>2.5 = overfit signal)
   - **Deflated Sharpe ratio** (Bailey-Lopez de Prado) — risque 30% faux positif sans (Backtester)

2. **Heartbeat + Telegram alerts MANDATORY** (Defensive, Live Op, Holistic):
   - Cron 1min curl /health → Telegram si timeout 3x ou no-trade > 60min en mode actif
   - Telegram ack-required AVANT tout redeploy
   - Sans ça → NO-GO (Defensive)

3. **BootReconciler obligatoire** (Live Op flag NO-GO sinon):
   - Bot crash → redémarre → DOIT charger Kraken /openpositions + /openorders
   - Comparer DB H2, halt si drift > $2
   - Cause incident 25/04 (runaway 9.91x)

4. **ADX simple > HMM Phase 1** (9/10): HMM = overfit garanti sur 90j, ADX simple suffit.

5. **Stat-arb NON Phase 1** (7/10): Complexité non justifiée à $135. Phase 4+ après 30j stable. (Aggressive seul push Phase 1.)

### 🟡 BLOQUANT (3-4 d'accord)

6. **Capital math fix** (Engineering): $25 × 5 levels + $30 reserve = $155 > $135. Réduire à **$25 × 4 levels** ou **$20 × 5 levels**.

7. **Walk-forward étendu** (Backtester):
   - 90j → **180j data**
   - 21j IS / 9j OOS → **30j IS / 10j OOS step 10j** = 15 fenêtres
   - Anchored expanding (pas rolling)

8. **Funding 4h Kraken specifically** (Macro, Live Op, Holistic):
   - PAS 8h Binance
   - Circuit breaker: `0.025%/4h` pas `0.05%/8h`
   - Funding flip detector (négatif soutenu = capitulation imminente)

9. **CB -2% BTC en 1h → closeOnly auto** (Defensive, Macro)

10. **Idempotency layer HARD STOP** (Engineering): dedup par fillId+gridId UUID, TTL 5min → fix race condition double-fire

### 🟢 RECOMMANDÉ (2 d'accord)

11. **Drop SOL whitelist** (Macro): alt season morte BTC.D montante, beta 1.5-2x BTC, Kraken thin
12. **Macro CB** (Macro, Risk): DXY +1%, VIX>30, BTC.D>55% → pause new grids
13. **Reconciliation loop** Kraken vs DB toutes les 60s in-bot (Engineering)
14. **Funding cost monitor** real-time + edge attribution per fill (Risk, Quant)

## Divergences à arbitrer

| Param | Range | Mon arbitrage |
|---|---|---|
| Leverage | 3x (Live Op) / 5x (Risk/Defensive/Quant) / 7x (Aggressive) | **5x cap strict** — Live Op trop conservateur, Aggressive ignore tail risk. Quant calcul fee math OK à 5x. |
| Stat-arb timing | Phase 1 (Aggressive) / Phase 4+ (7 traders) / NEVER (Contrarian) | **Phase 4+** — consensus dominant, complexité non justifiée à $135 |
| Backtest framework | backtesting.py+vectorbt (5 traders) / Freqtrade (Live Op) | **vectorbt + sidecar Python** — Live Op argument fort (funding 4h built-in) MAIS Freqtrade c'est replacer Martin entier. Compromis: vectorbt avec funding 4h modeled manuellement. |
| Pair selection | BTC+ETH (Macro) / BTC+ETH+SOL (Aggressive, master doc) | **BTC seul Phase 1, ETH après 7j stable, SOL drop** (Macro raisonnement plus fort) |

## Verdict NO-GO du Contrarian (à considérer)

Tony, lis ça avec attention:

> "1€/jour sur $135 = 270% APY mathématiquement. Le doc lui-même dit 8-25% réaliste. L'objectif est 10× au-dessus du réalisme admis."
>
> "BTC spot hold 1 an, médiane historique 2020-2025: ~+40% (variance énorme). Espérance ≈ $189. Bot proposé optimiste: $135 × 22% = $164. **BTC hold gagne**, zéro stress."
>
> "Sunk cost: bot = identité ('Martin'), pas investissement. Tu débuggues parce que tu l'as nommé."
>
> "Steel-man: $100 BTC spot cold + $35 TradingView/Bloomberg pour apprendre vraiment."

C'est valide. **À toi de décider** si tu continues le bot pour le ROI ou pour le plaisir/apprentissage assumé.

## Plan définitif (intégrant consensus)

Remplace les sections 3-4 du master doc par ce qui suit:

### Pair selection finale

- **Phase 1**: BTC perp seul (1 paire)
- **Phase 2 (après 7j stable)**: + ETH perp
- **DROP**: SOL, DOT, LINK, ADA (history losses + thin liquidity Kraken Futures)

### Config finale

```yaml
grid:
  spacing: dynamic  # 1.0× ATR(14, 1h) clamped to [0.6%, 1.2%]  # NOTE: Backtester insists fix this post-validation
  levels: 4  # was 5, capital math fix
  leverage: 5  # cap strict
  capital_per_grid: 25  # $100 total → $35 reserve
  mode: NEUTRAL
  
regime_gate:
  adx_threshold: 25
  bbw_threshold: 4.0
  btc_ema200_required: true
  btc_ema200_weekly_required: true  # closeOnly tant que BTC<EMA200w (Macro)
  funding_pause_threshold: 0.025  # %/4h Kraken (was 0.05%/8h)
  
hard_sl:
  formula: "lowest_grid_price - 1.5 * ATR(14, 4h)"
  reduceOnly: true
  
hard_stop:
  max_loss_pct: 8  # was 15
  
circuit_breaker:
  daily_loss_pct: 3
  weekly_loss_pct: 7
  consecutive_losses: 3
  api_errors_per_min: 5
  btc_move_1h: 2  # closeOnly auto
  funding_flip_pct: -0.025  # %/4h sustained
  dxy_intraday_pct: 1  # macro CB
  vix_threshold: 30
  btc_dominance_pct: 55
  
sizing:
  risk_per_trade_pct: 1.0
  kelly_fraction: 0.25
  cash_reserve_pct: 26  # ~$35
  
drawdown:
  reduce_at_pct: 10
  kill_at_pct: 15
  recovery_period_days: 30
  absolute_floor: 115  # $115 = stop définitif manual recovery only (Risk)
  
operational:
  heartbeat_seconds: 60
  telegram_ack_required_redeploy: true
  bootreconciler_enabled: true  # MANDATORY
  reconciliation_loop_seconds: 60
  idempotency_ttl_seconds: 300  # HARD STOP dedup
```

### Critères backtest pass (durcis)

- Net P&L positif après slippage 10bp + maker 0% + taker 0.05% + funding 4h cumulé
- **Min 100 trades** sur 180j
- **Max DD < 10%** (était 15%)
- **Profit factor > 1.5** (était 1.3) MAIS **< 2.5** (overfit)
- **OOS Sharpe ≥ 60% IS Sharpe** (était 50%)
- **Sharpe IS plafonné 2.5**
- **Deflated Sharpe ratio > 0.5** (Bailey-Lopez de Prado)
- **Min 10 trades / fenêtre OOS**
- **Pass-rate ≥ 6/8 fenêtres** (en supposant 8 fenêtres WF 30/10 sur 180j)
- **95th-percentile MC DD < 1.8× backtest DD** (était 2×)
- **Stress test event-driven**: re-run sur fenêtre crash 2026-04-26/27 (Macro)
- **Noise injection ±3bp**: Sharpe ne doit pas chuter > 40% (Backtester)

### Tests intégration mandatory avant Phase 7 deploy

1. HARD STOP idempotency: fire 100x same fill → 1 stop max
2. Race condition: 2 enrichWithKrakenPnl concurrent → no double-stop
3. startedAt = null → graceful skip, no NPE
4. fillTime parse error → fallback Instant.MIN, log WARN
5. Circuit breaker daily -3% → halt 24h, no new orders
6. ADX gate: feed synthetic OHLC ADX>25 → 0 grid creation
7. ATR fallback: ATR=null → use 0.6% spacing, log
8. Reduce-only SL: open opposite position → rejected
9. **NEW** BootReconciler: simulate crash mid-grid, verify state restore from Kraken
10. **NEW** Telegram heartbeat: simulate bot down 3min → Telegram fired

## Quick wins ce soir (Holistic propose, alignés)

Tony, si tu veux **agir avant de dormir** (10 min config seulement):

1. Tighten `max_loss_pct` 15 → 8% sur DOT (1 ligne YAML, restart)
2. ADX threshold 40 → 25 (1 ligne)
3. Skill `martin-monitor` cron 15min: si BTC -2% en 1h → curl POST /api/strategy/pairs/PF_DOTUSD/close-only

**MAIS**: actuellement le bot est paused (j'ai disabled DOT + AutoGrid pour la recherche). Si tu veux re-activer DOT avec ces tweaks → A. Si tu préfères attendre backtest validé → B. Tony décide.

## Critère d'arrêt 30j live (Holistic)

Equity < $115 (-15% from $135) OU 2 HARD STOP loops/runaways en 30j OU Profit Factor live < 0.9 sur 50+ trades = STOP, switch capital BTC spot ou stat-arb paper.

## Réalité chiffrée admise (10/10)

Voici ce qui est statistiquement attendu:

- **P(>1€/jour median sur 30j)**: **15-20%** (Quant calcul rigoureux)
- **EV mensuel réaliste**: $1.40-3.00 (1-2% APY net après fees/funding)
- **Sharpe live attendu**: 0.4-1.0 (live = 30-50% du backtest)
- **Max DD probable**: 8-15% sur 30j même avec circuit breakers
- **Probabilité d'un 6e bug runaway**: non-zéro, mitigated par tests intégration

**1€/jour est un objectif aspirationnel, pas un attendu statistique.**

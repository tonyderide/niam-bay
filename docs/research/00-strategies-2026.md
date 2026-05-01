# Master Strategies 2026 — Synthèse pour Martin Bot

**Auteur**: Niam-Bay (synthèse de 10 agents, ~100+ articles 2025-2026)
**Date**: 2026-05-01
**Cible**: Tony, capital $135, Kraken Futures, 1€/jour minimum, autonomie complète

---

## TL;DR (60 secondes)

Après lecture de 10 dossiers de recherche couvrant grid, mean-reversion, trend, market making, arbitrage, risk management, backtesting, ML, open-source bots, et order flow:

**Le combo qui ressort, pour TES contraintes ($135, Kraken Futures, autonomie):**

1. **Grid amélioré** comme moteur principal (déjà en place, ajustements identifiés)
2. **Regime filter ADX strict** (< 25 = trade, > 25 = pause/exit) — single biggest fix
3. **ATR-adaptive spacing** au lieu de fixe %
4. **Hard SL = lowest_grid − 1.5×ATR(14, 4h)** (non négociable)
5. **Daily circuit breaker -3% portfolio** = halt 24h auto (le plus critique manquant)
6. **Position sizing 1% risk strict**, Quarter-Kelly max
7. **Flat-capital** (pas de compound) jusqu'à 30 jours consécutifs profitables
8. **Optionnel upgrade**: stat-arb BTC-ETH paper-trade 4 semaines, deploy $80 si Sharpe>1.5

**À écarter**: market making pur (latency 100-300ms Java non viable), ML/AI deep nets (5% real alpha capturé par funded teams), cross-exchange arb (mort retail), triangular arb (peer-reviewed: non exploitable retail), SMC/Wyckoff standalone (0 peer-reviewed validation).

**Backtest avant deploy**: backtesting.py (Python) + walk-forward 21j/9j sur 90j. Critère pass: net positif après slippage+fees, max DD <15%, profit factor >1.3, OOS Sharpe ≥ 50% IS Sharpe.

**Réalité dure**: live Sharpe est typiquement 30-50% inférieur au backtest. Profit factor >3.0 = quasi toujours overfit. NostalgiaForInfinity (la stratégie communautaire la plus suivie) fait $100→$102.57 sur backtest officiel.

---

## 1. Diagnostic du Martin actuel (état 2026-05-01)

### Ce qui fonctionne
- Architecture grid + AutoGridScheduler (close-only / regime detection basique)
- HARD STOP via real Kraken P&L (patches 0427+0430)
- StopLossManager avec 1.5% min clamp
- pollGridOrders 10s + enrichWithKrakenPnl filtré par startedAt (patch 0430)

### Ce qui manque (consensus 10 agents)
- ❌ **Daily/weekly circuit breakers** (3 agents flag bloquant)
- ❌ **ADX strict regime gate** (actuellement ADX 40 + BBW 4.0, trop laxe)
- ❌ **ATR-aware spacing** (actuellement fixe 0.6%, pas adaptatif weekend/regime)
- ❌ **Hard SL position-level** (StopLossManager existe mais SL @ 15% trop large)
- ❌ **Race condition** dans enrichWithKrakenPnl (Engineering trader)
- ❌ **`startedAt` nullable** peut rendre le bug HARD STOP loop (Engineering trader)
- ❌ **Funding rate awareness** (Kraken Futures funding 4h interval — pas même que Binance!)
- ❌ **Notifications Telegram** (Defensive trader bloquant)
- ❌ **Heartbeat / dead-man switch**
- ❌ **Backtest framework** (jamais validé sur historical data)

---

## 2. Stratégies évaluées avec verdict

| # | Stratégie | Performance attendue | Complexité | Cap min | Verdict pour Martin |
|---|---|---|---|---|---|
| 1 | **Grid + regime filter ADX + hard SL ATR** | Sharpe 0.8-1.5, DD 15-20% | Low (extension Martin) | $50 | ✅ **CŒUR DE LA STRATÉGIE** |
| 2 | **Stat-arb BTC-ETH cointegration** | Sharpe 2.45, 16.34% annual, 64.74% WR (paper IJSRA 2025) | Medium | $300+ idéal, $80 minimum | ⚠️ **MODULE OPTIONNEL après backtest** |
| 3 | **HMM regime classifier** | Filter améliore Sharpe ~10-20% | Medium | $0 (no extra capital) | ✅ **UPGRADE PHASE 2** |
| 4 | **Funding rate carry (cash & carry)** | 14-19% APY 2024-2025 | Medium | $300+ | ❌ Marginal à $135, break-even ~14j |
| 5 | **Trend following EMA21/55 + Donchian** | Sharpe 0.8-1.5, win rate 45-55% | Medium | $100+ | ⚠️ **MODULE SÉPARÉ uniquement** (pas même capital que grid — Wiley 2025: capital bucket séparé) |
| 6 | **Mean reversion BB(20,2) + RSI 20/80** | Sharpe 1-1.5 | Low | $100+ | ⚠️ Peut être complémentaire au grid |
| 7 | **Market making Avellaneda-Stoikov** | -10% à +15% APY haute variance | High | $1k+ | ❌ Latency 100-300ms Java non viable BTC/ETH |
| 8 | **ML/AI/RL trading (LSTM, PPO, FinRL)** | Variable, claims hype | Very High | $1k+ | ❌ Mort sur $135 (taker fees > directional edge) |
| 9 | **SMC/Wyckoff/order flow standalone** | Aucun peer-reviewed | High | n/a | ❌ Use comme features only, pas standalone |
| 10 | **Cross-exchange arb / triangular** | Marginal retail | Very High | $10k+ | ❌ Mort retail 2025-2026 |

---

## 3. Architecture cible (Martin v2.0)

### Module principal: GRID AMÉLIORÉ

```
                    ┌─────────────────────────────┐
                    │   AutoGridScheduler v2      │
                    │   (15min tick)              │
                    └──────────────┬──────────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                  │                  │
                ▼                  ▼                  ▼
        ┌─────────────┐   ┌──────────────┐   ┌──────────────┐
        │ RegimeFilter│   │ DrawdownMgr  │   │  CircuitBkr  │
        │ (ADX < 25)  │   │ (-10% halve, │   │ (Daily -3%,  │
        │ (BTC>EMA200)│   │ -15% kill)   │   │  Weekly -7%) │
        └──────┬──────┘   └──────┬───────┘   └──────┬───────┘
               │                 │                  │
               └─────────────────┴──────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────┐
                    │   GridTradingService v2     │
                    │   ATR-adaptive spacing      │
                    │   Position sizing 1% risk   │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │ StopLossManager v2          │
                    │ Hard SL = lowest_grid       │
                    │ - 1.5×ATR(14,4h)           │
                    └─────────────────────────────┘
```

### Paramètres exacts (consensus chiffré)

```yaml
# Per-instrument grid config
grid:
  spacing: dynamic  # 1.0-1.5 × ATR(14, 1h) clamped to [0.4%, 1.5%]
  levels: 5
  leverage: 5  # cap strict, jamais 10x
  capital_per_grid: 25  # USD, flat (no compound until 30j profitable)
  mode: NEUTRAL  # bias to short-density if funding > 0.02%/8h sustained
  
# Regime gate
regime_gate:
  adx_threshold: 25  # was 40, way too laxe
  bbw_threshold: 4.0  # keep
  btc_ema200_required: true  # all alts
  funding_pause_threshold: 0.05  # %/8h, pause new entries above this
  
# Hard SL (position-level)
hard_sl:
  formula: "lowest_grid_price - 1.5 * ATR(14, 4h)"
  fallback_pct: 0.08  # 8% if ATR unavailable
  reduceOnly: true
  triggerSignal: "mark"
  
# Per-grid HARD STOP (dollar-level)
hard_stop:
  max_loss_pct: 8  # was 15, too laxe
  
# Circuit breakers (NEW)
circuit_breaker:
  daily_loss_pct: 3  # halt 24h auto if breached
  weekly_loss_pct: 7  # halve sizing if breached
  consecutive_losses: 3  # also triggers daily halt
  api_errors_per_min: 5  # bot health
  btc_move_1h: 2  # auto closeOnly if BTC -2% in 1h
  
# Position sizing
sizing:
  risk_per_trade_pct: 1.0  # 1% of equity max risk
  kelly_fraction: 0.25  # quarter-Kelly cap, never full
  cash_reserve_pct: 22  # ~$30 of $135
  
# Drawdown rules
drawdown:
  reduce_at_pct: 10  # halve sizing
  kill_at_pct: 15  # stop all
  recovery_period_days: 30  # consecutive profitable days before re-enable compound
```

### Pair selection

**Whitelist 2025-2026 (consensus)**:
- BTC perp: noyau, liquidité top, ATR cohérent avec spacing 0.4-0.6%
- ETH perp: liquide, beta 1.0 BTC, mean-rev candidate
- SOL perp: thin Kraken Futures mais narrative DePIN/DeFi vivante
- DOT, LINK, ADA: **désactiver permanent** (history losses + thin liquidity Kraken Futures)

### Module optionnel (Phase 2): Stat-arb BTC-ETH

Paper-trade 4 semaines avec:
- Engle-Granger cointegration test sur 90j daily closes
- Z-score |Z| > 2 entry, |Z| < 0.5 exit
- Beta hedge ratio dynamique (rolling regression 30j)
- Position size $80 si Sharpe paper > 1.5

### Module optionnel (Phase 3): HMM regime classifier

- Train HMM 3-state (RANGING / TRENDING_UP / TRENDING_DOWN) sur 180j BTC daily returns + ADX + ATR%
- Output regime confidence → multiplie taille position grid

---

## 4. Plan d'implémentation (séquence)

### Phase 4 — Design (30 min)
- Doc design `martin/docs/design-v2.md` avec diff config + interfaces
- Liste exacte des fichiers Java à modifier
- Plan rollback

### Phase 5 — Backtest framework (1-2h)
- Setup `backtesting.py` (Python sidecar)
- Download Kraken Futures BTC perp data via Freqtrade `download-data` (depuis 2020)
- Modeler slippage 5bp, maker 0%, taker 0.05%, funding 4h interval cumulé
- Implémenter walk-forward 21j IS / 9j OOS (~8 windows sur 90j)
- Implémenter Monte Carlo 1000 runs

### Phase 6 — Backtest run + iteration (variable)
- Test grid v2 (spacing ATR, ADX gate, hard SL ATR) sur BTC perp 90j
- Critères pass:
  - Net positif après slippage + fees + funding
  - Max DD < 15%
  - Profit factor > 1.3
  - OOS Sharpe ≥ 50% IS Sharpe
  - 95th-percentile MC DD < 2× backtest DD
- Si fail → tune params, re-run
- Si pass → docs/backtests/v2-results.md avec full metrics

### Phase 7 — Deploy (30 min)
- Code Java patches selon design
- Build + scp + systemctl restart
- Vérifier 0 HARD STOP loop, regime gate fonctionne, SL placé
- Activer 1 paire (BTC) puis 2 (BTC+ETH) progressivement
- Monitor 7 jours

---

## 5. Critères de succès (vs 30j de backtest + 30j live)

### Backtest (avant deploy)
- ✓ Net P&L positif après slippage+fees+funding sur 90j
- ✓ Max DD < 15%
- ✓ Profit factor > 1.3
- ✓ Sharpe > 0.8 (ne pas viser >2 = overfit signal)
- ✓ OOS Sharpe ≥ 50% IS Sharpe
- ✓ 95th-percentile Monte Carlo DD < 2× backtest DD
- ✓ Min 30 trades sur 90j (sinon données insuffisantes)

### Live (post-deploy 30j)
- Equity ≥ $150 (objective)
- Drawdown max < 8% session
- Zéro intervention manuelle d'urgence
- ≥ 1€/jour median (Tony goal)
- 0 HARD STOP loop / runaway

---

## 6. Réalité chiffrée à laquelle s'attendre

D'après les recherches, voici ce qui est réaliste:

| Métrique | Réaliste 2025-2026 | Hype | Pire cas |
|---|---|---|---|
| Sharpe ratio live | 0.8 - 1.5 | "2.8" | < 0.5 |
| Win rate grid | 50-65% | "89%" | 35-45% |
| Max DD | 15-25% | "5%" | 30%+ |
| Net APY (small acc) | 8-25% | "300%" | -10% à 0% |
| Profit factor | 1.2-2.0 | "5.0" | < 1.0 |
| Live vs Backtest Sharpe | 50-70% du backtest | "100%" | < 30% |

À $135 capital, **8-25% APY = $11-34/an = 0.03-0.09€/jour**. Pour atteindre **1€/jour ($0.30/jour ≈ €30/mois ≈ 22% APY annualisé)**, il faut être dans le top 50% des configs. Pas impossible, mais pas "1€/jour minimum garanti" non plus.

---

## 7. Sources principales (pour validation 10 traders)

Voir les 10 fichiers `0X-topic.md` dans ce dossier pour URLs détaillées et désaccords notés.

**Top sources convergentes**:
- Wiley Palazzi 2025 "Trading Games Crypto" (peer-reviewed)
- IJSRA 2025 stat-arb crypto (peer-reviewed)
- BitMEX 2025 Q3 Derivatives Report
- arxiv juin 2025 grid trading paper
- Hummingbot V2 architecture docs
- Freqtrade NostalgiaForInfinity backtests
- Concretum Group position sizing
- Kraken Futures docs.kraken.com (funding 4h interval)

**À se méfier de** (consensus 10 agents):
- 3Commas/Pionex marketing claims (89% WR, 300% APY)
- RedHub/Stiff Zone "AI bots 2025" (vendor)
- ICT/SMC course sellers (70-90% WR)
- Vendor backtests qui omettent drawdown

---

## 8. Question pour les 10 traders validateurs

À soumettre en Phase 3:
1. Le combo "grid amélioré + regime ADX + hard SL ATR + circuit breakers" est-il optimal pour $135 Kraken Futures?
2. Le stat-arb BTC-ETH mérite-t-il son module séparé ou est-ce de la complexité ?
3. Faut-il ajouter HMM regime ou rester sur ADX simple ?
4. Backtest framework `backtesting.py` est-il le bon choix ou autre ?
5. Critères pass backtest sont-ils trop laxes / trop stricts ?
6. Manque-t-il un sous-système critique non identifié ici ?
7. Verdict 30j: GO comme conçu / GO avec tweaks X / NO-GO et faire Y ?

---

**Fin du master doc. Suite: Phase 3 = 10 traders valident.**

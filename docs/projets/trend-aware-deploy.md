# Trend-Aware Deployment — Design Spec

**Date**: 2026-05-27 (nuit, mandat autonome Tony)
**Auteur**: Claude (session council-check + night-work)
**Status**: DESIGN — pending council review + backtest validation

## Problème

Le bot Martin déploie tous les grids en `gridMode=NEUTRAL` par défaut. En régime trending (BTC nettement sous ou sur EMA200), un NEUTRAL grid accumule de la position dans le sens contraire au trend et perd. L'`autoFlipDirection=true` qui devait résoudre ça a généré du whipsaw (cascade ADA -$7.63 le 2026-05-25) parce que naïvement flipper sur chaque tick d'EMA = close+open spread payé à chaque oscillation.

## Objectif

Que le bot choisisse **le mode INITIAL d'un nouveau grid** en fonction d'un régime BTC confirmé:
- **BEARISH** (downtrend confirmé) → deploy `SHORT`
- **BULLISH** (uptrend confirmé) → deploy `LONG`
- **NEUTRAL** (sideways / non confirmé) → deploy `NEUTRAL`

**Principe clé**: on ne flip JAMAIS un grid actif. Le grid déployé tourne avec son mode initial jusqu'à fermeture naturelle ou SL. Les changements de régime n'affectent que les **prochains** deploys.

→ Élimine le whipsaw par construction (zéro close+open dû au régime).

## Hystérésis (anti-whipsaw)

Un grid déployé tient ~12-48h en NEUTRAL et plusieurs heures à plusieurs jours en directionnel. Les seuils de classification doivent éviter les bascules trop fréquentes.

### Classification BTC

```
distancePct = (btcPrice - ema200) / ema200 * 100

BEARISH si:
  distancePct < -1.0%     (BTC ≥1% sous EMA200)
  AND distancePct < -0.5% depuis ≥4h (confirmation durée, seuil large)

BULLISH si:
  distancePct > +1.0%     (BTC ≥1% sur EMA200)
  AND distancePct > +0.5% depuis ≥4h

NEUTRAL sinon:
  -1.0% ≤ distancePct ≤ +1.0%
  OR pas de confirmation 4h
```

### Pourquoi ces nombres
- **1.0% seuil entrée** : filtre le dust (BTC oscille à ±0.3-0.5% par heure normalement)
- **0.5% seuil confirmation** : on tolère un petit pullback pendant les 4h sans perdre le régime
- **4h durée** : 1 trading session crypto, exclut les wicks/manipulations courtes
- **Pas de seuil sortie séparé** : la sortie d'un régime = entrée dans NEUTRAL (seuil 1.0% suffit comme hystérésis)

## Architecture

### TrendStateManager.java (NEW)

```java
@Component
public class TrendStateManager {
    public enum TrendState { BEARISH, NEUTRAL, BULLISH }

    private TrendState currentState = TrendState.NEUTRAL;
    private Instant stateEnteredAt = Instant.now();
    private final Deque<PricePoint> recentPrices = new ConcurrentLinkedDeque<>();

    @Scheduled(fixedRate = 60_000) // refresh 1x/min
    public void updateState() {
        // 1. fetch BTC price + EMA200 from EmaSignalService
        // 2. push to recentPrices (keep 5h of 1min points)
        // 3. classify based on hysteresis rules above
        // 4. if new classification != currentState
        //      → require 4h confirmation before transition
        //      → log state change
    }

    public TrendState getStateForNewDeploy() {
        return currentState;
    }

    public String describe() {
        // for logging: "BEARISH for 5h 23m, distance -1.4%"
    }
}
```

### AutoGridScheduler integration

À l'endroit où le scheduler appelle `gridTradingService.startGrid(config, mode=NEUTRAL)`, remplacer par:

```java
String deployMode = config.getGridMode(); // default from config
if (trendStateManager != null && !"WARM_ONLY".equals(System.getenv("TREND_MODE"))) {
    TrendState ts = trendStateManager.getStateForNewDeploy();
    String adaptiveMode = switch (ts) {
        case BEARISH -> "SHORT";
        case BULLISH -> "LONG";
        case NEUTRAL -> "NEUTRAL";
    };
    if (!adaptiveMode.equals(deployMode)) {
        log.info("TREND-ADAPT: {} → {} ({})", deployMode, adaptiveMode, trendStateManager.describe());
        deployMode = adaptiveMode;
    }
} else if ("WARM_ONLY".equals(System.getenv("TREND_MODE"))) {
    TrendState ts = trendStateManager.getStateForNewDeploy();
    log.info("TREND-WARM-ONLY: would deploy {} (currently configured {}) — {}",
            switch (ts) { case BEARISH -> "SHORT"; case BULLISH -> "LONG"; default -> "NEUTRAL"; },
            deployMode, trendStateManager.describe());
}
gridTradingService.startGrid(config, deployMode);
```

### WARM_ONLY safety flag

Env var `TREND_MODE=WARM_ONLY` → log la décision mais utilise le mode original. Permet d'observer 60-90min ce que l'engine aurait fait sans toucher au capital.

`TREND_MODE=LIVE` (ou unset) → applique réellement le mode adaptatif.

## SL safety

Aucun changement au système SL existant (3 layers B3+B3b+B4 déjà déployés). Les grids SHORT et LONG utilisent le même flow:
- B3 v3 : SL placé après deploy + verify Kraken + retry 3pct
- B3b v2 : close-only protection avec tick rounding
- B4 : SL post-fill async via CompletableFuture

Spécificité SHORT : `StopLossCalculator.compute()` calcule SL au-dessus du prix d'entrée (vs en-dessous pour LONG). Logic déjà testée empiriquement (cascade ADA short avait des SL qui ont fonctionné — c'est le flip qui a perdu, pas le SL).

**Test obligatoire pre-deploy**: forcer un mini grid SHORT $5 sur SOL, vérifier que le SL est >prix d'entrée et sur Kraken. ✓ before LIVE.

## Risques + mitigations

| Risque | Mitigation |
|---|---|
| TrendStateManager bug → mauvaise classification | WARM_ONLY 60-90min permet observation avant LIVE |
| Backtest sur passé biased | Test sur ≥3 fenêtres distinctes (bull, bear, chop) |
| Spread SHORT grids non testé en prod | Le SHORT cascade ADA a tourné avec SL fonctionnel, juste flip cassé |
| Bot crash au démarrage avec nouveau Component | Rollback jar via /tmp/backend.jar.bak-* (existe déjà) |
| Trend détecté trop tard (lag 4h) | C'est by-design pour anti-whipsaw, accepté |
| Funding flip pendant régime BEARISH (SHORT paye carry) | Hors scope — TrendStateManager ne lit que prix/EMA. Le funding-awareness peut être un patch v2 si besoin |

## Backtest plan

Données : `niam-bay/ai-lab/darwin/data_cache/BTC*.csv` ou équivalent (à vérifier).

Périodes :
- **2025-Q1** (2025-01 à 2025-03) — trend bull recap, vérifier qu'on capture les LONG
- **2025-Q3** (2025-07 à 2025-09) — chop sideways, vérifier qu'on ne whipsaw pas (transitions ≤2/mois)
- **2024-H2** (2024-07 à 2024-12) — bear recovery, vérifier la précision des BEARISH
- **2026-Q2** (2026-04 à 2026-05) — données récentes pour valider sur le marché actuel

Métriques :
- # transitions state par mois (cible ≤ 2-3)
- # heures dans chaque state
- "Would-have" PnL pour 1 grid NEUTRAL $25 fictif vs trend-aware
- Worst whipsaw run (combien de transitions en X heures)

Seuil GO/NO-GO :
- ≤ 3 transitions/mois en moyenne
- Trend-aware beats NEUTRAL ou égal dans ≥ 3/4 des périodes
- Aucun mois avec ≥ 5 transitions

## Loop décisionnelle nuit

Toutes les 30min jusqu'au matin :
1. Re-vérifier état Martin VM (martin-monitor)
2. Si phase backtest en cours → continuer
3. Si phase warm-only en cours → relire logs WARM-ONLY, count décisions
4. Si phase live en cours → vérifier grids déployés respectent le régime
5. Telegram update si milestone changé OU si rien depuis 90min (heartbeat)

## Out of scope (v1)

- Flip de grids actifs (par construction)
- Funding-awareness pour SHORT (v2)
- Per-pair trend (utilise BTC global pour tout)
- Backtest avec slippage réaliste (v2)
- Dashboard panel pour visualiser état trend (v2)

## Commits prévus

Sur branch `feat/trend-aware-deploy-2026-05-27` :
1. `feat(trend): TrendStateManager skeleton with hysteresis classification`
2. `feat(trend): wire TrendStateManager into AutoGridScheduler with WARM_ONLY flag`
3. `test(trend): backtest harness Python over BTC 1h cache`
4. `feat(trend): observability — logs + /api/signal/trend_state endpoint`

Si GO live : `feat(trend): enable LIVE mode + remove WARM_ONLY default`

# Patch Martin — trimPositionPartial verify + stopGrid close-residual

**Drafté** : 2026-05-16 12h45 Paris (cycle 51 vacation-autonomy)
**Status** : Prêt à coder, non déployé. Tony peut review et merge à son retour.
**Effort total** : ~1h code + tests, 5 min deploy.

## Problème

Deux bugs orthogonaux qui ont conjointement créé la position LINK 8.7 orpheline 5h sans SL aujourd'hui (cycle 51 — voir `vacation-autonomy.md`).

### Bug 1 : `trimPositionPartial` envoie sans vérifier

`GridTradingService.java:700-730` — `sendOrder(trimOrder).block()` log un succès sans inspecter `sendStatus.status`. Si Kraken rejette l'ordre (precision, conflit SL pending, lotSize, marketSuspended…), le code croit avoir trim alors que la position reste intacte. Et il marque `unstuckLevelXDone=true`, donc le tick suivant ne re-tente pas.

Observation 2026-05-16 :
- 07:11:30 — lvl1 fired, log "closed 2.175 of 8.7" → position Kraken reste 8.7 (StopLossManager replace SL pour size=8.7 1s après)
- 07:15:37 — lvl2 fired, log "closed 2.175 of 8.7" → idem

### Bug 2 : `stopGrid` abandonne la position résiduelle

`GridTradingService.stopGrid()` cancel tous les ordres (limit + SL Kraken) mais ne ferme pas la position si elle existe. Quand `CIRCUIT BREAKER signal=DANGER` déclenche stopGrid, la position devient naked.

Le bot fait l'inverse de ce qu'il devrait : il enlève la protection (SL) au moment où le marché est le plus risqué (DANGER signal). Le `closePositionAndStopGrid` existe déjà (utilisé par HARD STOP cycle 0427) — il faut juste l'appeler aussi depuis le CIRCUIT BREAKER path.

## Solutions

### Patch 1a : `trimPositionPartial` post-place verify

Remplacer le `sendOrder().block()` blind par un appel vérifié.

**Fichier** : `src/main/java/com/martin/grid/GridTradingService.java`, ligne ~721.

```java
private void trimPositionPartial(GridState state, double fraction) {
    if (fraction <= 0 || fraction >= 1) {
        log.warn("trimPositionPartial: invalid fraction {} for {}", fraction, state.getInstrument());
        return false;
    }
    try {
        var posResp = krakenClient.getOpenPositions(state.isDemo()).block();
        if (posResp == null || posResp.getOpenPositions() == null) return false;
        for (var pos : posResp.getOpenPositions()) {
            if (!state.getInstrument().equals(pos.getSymbol())) continue;
            if (pos.getSize() == null || Math.abs(pos.getSize()) < 1e-9) continue;
            double trimSize = Math.abs(pos.getSize()) * fraction;
            if (trimSize < 1e-6) continue;
            String closeSide = "long".equalsIgnoreCase(pos.getSide()) ? "sell" : "buy";
            KrakenOrderRequest trimOrder = KrakenOrderRequest.builder()
                    .orderType("mkt")
                    .symbol(state.getInstrument())
                    .side(closeSide)
                    .size(trimSize)
                    .reduceOnly(true)
                    .build();
            var resp = krakenClient.sendOrder(trimOrder, state.isDemo()).block();
            String status = (resp != null && resp.getSendStatus() != null)
                    ? resp.getSendStatus().getStatus() : null;
            if (!"placed".equalsIgnoreCase(status) && !"filled".equalsIgnoreCase(status)
                    && !"new".equalsIgnoreCase(status)) {
                log.error("AUTO-UNSTUCK trim FAILED [{}] sendOrder status={} requested-size={} fraction={} pos-size={} response={}",
                        state.getInstrument(), status, trimSize, fraction, pos.getSize(), resp);
                return false;
            }
            log.warn("AUTO-UNSTUCK trim OK [{}] closed {} of {} ({}%) status={}",
                    state.getInstrument(), trimSize, pos.getSize(),
                    String.format("%.0f", fraction * 100), status);
        }
        return true;
    } catch (Exception e) {
        log.error("trimPositionPartial failed for {}: {}", state.getInstrument(), e.getMessage());
        return false;
    }
}
```

Note : retour boolean.

### Patch 1b : Caller marque `unstuckLevelXDone` seulement si trim OK

Toujours dans `GridTradingService.java`, dans la section auto-unstuck (~ligne 640-665) :

```java
if (dropPct >= 3.0 && !state.isUnstuckLevel2Done()) {
    log.warn("AUTO-UNSTUCK lvl2 (-3%): trimming 25% for {} — currentPrice={} dropped -{}% from center {}",
            state.getInstrument(), ..., ..., ...);
    if (trimPositionPartial(state, 0.25)) {       // ← capture retour
        state.setUnstuckLevel2Done(true);
    } else {
        log.warn("AUTO-UNSTUCK lvl2 trim FAILED [{}] — will retry next tick", state.getInstrument());
    }
    return;
}
if (dropPct >= 2.0 && !state.isUnstuckLevel1Done()) {
    log.warn("AUTO-UNSTUCK lvl1 (-2%): trimming 25% for {} — currentPrice={} dropped -{}% from center {}",
            state.getInstrument(), ..., ..., ...);
    if (trimPositionPartial(state, 0.25)) {
        state.setUnstuckLevel1Done(true);
    } else {
        log.warn("AUTO-UNSTUCK lvl1 trim FAILED [{}] — will retry next tick", state.getInstrument());
    }
    return;
}
```

### Patch 2 : `stopGrid` close residual quand triggered par CIRCUIT BREAKER

Deux options :

**Option A (minimaliste)** — Dans `AutoGridScheduler` (ou wherever le CIRCUIT BREAKER STOP fired) , appeler `closePositionAndStopGrid(state)` au lieu de `stopGrid(instrument)` :

```java
// AutoGridScheduler.java — ligne où log dit "CIRCUIT BREAKER: Stopped grid for X DANGER"
GridState state = gridTradingService.getActiveGrids().get(instrument);
if (state != null) {
    gridTradingService.closePositionAndStopGrid(state);  // ← au lieu de stopGrid
} else {
    gridTradingService.stopGrid(instrument);  // fallback si state introuvable
}
log.warn("CIRCUIT BREAKER: Stopped grid for {} DANGER", instrument);
```

**Option B (plus propre)** — Ajouter un flag `closeResidual` à `stopGrid` :

```java
public void stopGrid(String instrument, boolean closeResidual) {
    GridState state = activeGrids.get(instrument);
    if (state == null) return;
    // existing cancel orders logic...
    if (closeResidual) {
        // Market close any residual position via reduceOnly
        try {
            var posResp = krakenClient.getOpenPositions(state.isDemo()).block();
            for (var pos : posResp.getOpenPositions()) {
                if (!instrument.equals(pos.getSymbol())) continue;
                if (pos.getSize() == null || Math.abs(pos.getSize()) < 1e-9) continue;
                // ... build mkt reduceOnly close order ...
                var resp = krakenClient.sendOrder(closeOrder, state.isDemo()).block();
                String status = resp != null && resp.getSendStatus() != null
                        ? resp.getSendStatus().getStatus() : null;
                if (!"placed".equalsIgnoreCase(status) && !"filled".equalsIgnoreCase(status)) {
                    log.error("stopGrid close-residual FAILED [{}] status={}", instrument, status);
                }
            }
        } catch (Exception e) {
            log.error("stopGrid close-residual error [{}]: {}", instrument, e.getMessage());
        }
    }
    activeGrids.remove(instrument);
    state.setActive(false);
}
```

Avec `stopGrid(instrument)` qui devient `stopGrid(instrument, false)` (backward-compat), et CIRCUIT BREAKER + killswitch utilisant `stopGrid(instrument, true)`.

Préférence : Option B. Plus explicite, applicable au killswitch v2 aussi.

## Tests

### Test unitaire `trimPositionPartial`

Mock `KrakenClient.sendOrder()` retournant différents `SendStatus`:
- `"placed"` → trim OK, log "AUTO-UNSTUCK trim OK", retour true
- `"rejected"` → log "AUTO-UNSTUCK trim FAILED", retour false
- `"accountInactive"` → idem rejected
- `null` response → idem rejected
- `null` sendStatus → idem rejected

### Test unitaire `stopGrid(true)`

Mock `getOpenPositions` retournant position, mock `sendOrder` :
- position 8.7 long, sendOrder placed → close ordre généré, log "stopGrid close OK"
- position 0 → pas d'ordre généré (skip)
- sendOrder rejected → log error "stopGrid close-residual FAILED"

### Test intégration (sur demo)

Déployer le bot en demo, force un CIRCUIT BREAKER STOP en abaissant le RSI threshold du SignalService, vérifier que la position est fermée en quelques secondes (pas laissée orpheline).

## Ordering deploy

1. Code patch 1a (`trimPositionPartial` verify, retour boolean) — 20 min
2. Code patch 1b (caller capture retour) — 10 min
3. Code patch 2 (`stopGrid` closeResidual flag + appels CIRCUIT BREAKER) — 30 min
4. Tests unitaires (3 méthodes × 4-5 cases) — 30 min
5. `mvn package` + `scp target/martin-*.jar ubuntu@VM:/home/ubuntu/martin/backend.jar.new`
6. `mv backend.jar backend.jar.bak-pre-trim-verify-$(date +%s) && mv backend.jar.new backend.jar`
7. `systemctl restart martin.service`
8. Vérifier : `journalctl -u martin -n 50` UP message
9. Vérifier `/api/system/status` → status:UP

Total : 1h30 incluant tests. Reversible via `mv backend.jar.bak-pre-trim-verify-* backend.jar` + restart.

## Validation après deploy (1-7 jours)

- **Compteur succès trim** : grep `AUTO-UNSTUCK trim OK` vs `AUTO-UNSTUCK trim FAILED` dans logs sur 7 jours. Si jamais FAILED, cause Kraken à investiguer (precision ? conflit SL ?).
- **Compteur orphan close** : grep `stopGrid close-residual` log lines. Si CIRCUIT BREAKER fired + position close → pattern fonctionnel.
- **Position orpheline jamais > 1 min** : metric à monitorer dashboard. Avant patch : moyenne 4-5h. Cible post-patch : 0 minutes.

## Note méta

Ce patch + le killswitch v2 (`docs/projets/patch-btc-killswitch-v2.md`) + le SL churn epsilon fix (cycle 46-47) + le BotController.cancelOrder fix (déjà 0511) forment un bundle cohérent : **rendre Martin verify-after-action partout**. Le pattern méta est plus important que chaque patch individuel.

Tony peut soit déployer les 3-4 patches en une seule PR (recommandé, 2-3h dev total), soit les déployer séparément pour réduire le risque de régression. Ma préférence : un bundle, avec backup jar pré-bundle pour rollback facile.

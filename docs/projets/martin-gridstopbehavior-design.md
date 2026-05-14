# Martin — `gridStopBehavior` design (proposal cycle 41 → patch cycle 42)

**Status** : DRAFT — non-déployé. Tony review + ship (~1h Java).
**Auteur** : Niam-Bay, cycle 42 (2026-05-14 06h CEST)
**Origine** : cycle 41 a quantifié 3 options post-stop, recommandé `TIGHT_SL_1.5PCT`. Ce doc transforme la reco en patch ready-to-ship.

---

## Problème

Quand AutoGridScheduler appelle `stopGrid(instrument)` (gate flippé CLOSE, ADX trop fort, etc.), la grid s'arrête mais **la position résiduelle reste ouverte sans gérant**.

État intermédiaire « grid stoppée + position ouverte sans pilotage » constaté en live cycles 38-41 (LINK 4.2, ADA 163, AVAX 5) : protection passive via SL orphelins de grids passées, design non prévu mais émergent.

## Quantification (backtest cycle 41 — `ai-lab/darwin/post_stop_naked_analyzer.py`)

67 événements EMA200-break + RSI≤30 sur cache BTC 30j 1min :

| Strategy | mean % | median % | pos % | worst5 % |
|---|---|---|---|---|
| HOLD 24h | +0.20 | +0.15 | 53.7 | −2.15 |
| MARKET_CLOSE | −0.04 | −0.04 | 0.0 | −0.04 |
| SL 0.5% | +0.03 | −0.56 | 31.3 | −0.56 |
| SL 1.0% | +0.03 | −0.20 | 44.8 | −1.06 |
| **SL 1.5%** | **+0.05** | **+0.08** | **50.7** | **−1.56** |
| SL 2.0% | +0.01 | +0.09 | 52.2 | −2.06 |

**Verdict** : SL 1.5% = meilleur ratio expected/tail. HOLD biaisé hausse par fenêtre +14%. MARKET_CLOSE = zéro upside.

## Solution

Ajouter un flag `gridStopBehavior` (enum) dans la stratégie. `AutoGridScheduler` lit le flag et route `stopGrid` vers le bon comportement.

### Valeurs

```java
public enum GridStopBehavior {
    LEAVE_POSITION,    // actuel — cancel orders + cancel SL, laisse position
    MARKET_CLOSE,      // cancel orders + cancel SL + close market reduceOnly
    TIGHT_SL_1_5_PCT   // cancel orders + remplace SL serré à -1.5% du mark, laisse position
}
```

Défaut : `LEAVE_POSITION` pour compat ascendante (les SL orphelins protègent déjà).
Tony peut migrer paire par paire vers `TIGHT_SL_1_5_PCT` ou laisser global.

---

## Patch Java

### 1. Nouvelle enum `grid/GridStopBehavior.java`

```java
package com.martin.grid;

public enum GridStopBehavior {
    LEAVE_POSITION,
    MARKET_CLOSE,
    TIGHT_SL_1_5_PCT;

    public static GridStopBehavior fromString(String s) {
        if (s == null || s.isBlank()) return LEAVE_POSITION;
        try { return GridStopBehavior.valueOf(s.trim().toUpperCase()); }
        catch (IllegalArgumentException e) { return LEAVE_POSITION; }
    }
}
```

### 2. `api/dto/StrategyPairDto.java`

```java
// ligne 24 après maxLossPercent
private String gridStopBehavior;  // "LEAVE_POSITION" | "MARKET_CLOSE" | "TIGHT_SL_1_5_PCT" (default LEAVE)
```

### 3. `grid/GridState.java`

```java
// fin de classe, après unstuckLevel2Done
@Builder.Default
private GridStopBehavior gridStopBehavior = GridStopBehavior.LEAVE_POSITION;
```

### 4. `grid/GridTradingService.java`

Renommer `stopGrid(instrument)` → `stopGrid(instrument, GridStopBehavior override)`. Wrapper d'orig signature lit le behavior depuis state. Ajouter helper `placeTightProtectiveSL`.

```java
// ligne 224 — replace existing stopGrid
@Transactional
public void stopGrid(String instrument) {
    GridState state = activeGrids.get(instrument);
    GridStopBehavior behavior = state != null ? state.getGridStopBehavior() : GridStopBehavior.LEAVE_POSITION;
    stopGrid(instrument, behavior);
}

@Transactional
public void stopGrid(String instrument, GridStopBehavior behavior) {
    GridState state = activeGrids.remove(instrument);
    if (state == null) return;

    state.setActive(false);
    log.info("Stopping grid for {} behavior={}", instrument, behavior);

    // 1. Always cancel grid orders
    for (GridLevel level : state.getLevels()) {
        if (level.getStatus() == GridLevel.GridLevelStatus.PLACED && level.getKrakenOrderId() != null) {
            cancelOrder(level.getKrakenOrderId(), state.isDemo());
        }
    }

    // 2. Behavior-specific routing
    switch (behavior) {
        case MARKET_CLOSE -> {
            if (stopLossManager != null) {
                try { stopLossManager.cancel(state); } catch (Exception e) {
                    log.warn("stopGrid MARKET_CLOSE: SL cancel failed for {}: {}", instrument, e.getMessage());
                }
            }
            closeResidualMarket(state);
        }
        case TIGHT_SL_1_5_PCT -> {
            // Remplace l'ancien SL (potentiellement loin) par un SL serré 1.5% sous le mark
            placeTightProtectiveSL(state, 1.5);
        }
        case LEAVE_POSITION -> {
            // Comportement actuel : cancel SL aussi pour ne pas laisser d'orphelin
            if (stopLossManager != null) {
                try { stopLossManager.cancel(state); } catch (Exception e) {
                    log.warn("stopGrid LEAVE: SL cancel failed for {}: {}", instrument, e.getMessage());
                }
            }
        }
    }

    gridStateRepository.findByInstrument(instrument).ifPresent(entity -> {
        entity.setActive(false);
        gridStateRepository.save(entity);
    });
}

private void closeResidualMarket(GridState state) {
    // Réutilise la logique existante de closePositionAndStopGrid étape 2
    try {
        var posResp = krakenClient.getOpenPositions(state.isDemo()).block();
        if (posResp == null || posResp.getOpenPositions() == null) return;
        for (var pos : posResp.getOpenPositions()) {
            if (!state.getInstrument().equals(pos.getSymbol())) continue;
            if (pos.getSize() == null || Math.abs(pos.getSize()) < 1e-9) continue;
            String closeSide = "long".equalsIgnoreCase(pos.getSide()) ? "sell" : "buy";
            KrakenOrderRequest closeOrder = KrakenOrderRequest.builder()
                    .orderType("mkt").symbol(state.getInstrument()).side(closeSide)
                    .size(Math.abs(pos.getSize())).reduceOnly(true).build();
            krakenClient.sendOrder(closeOrder, state.isDemo()).block();
            log.info("gridStop MARKET_CLOSE: closed {} {} size={}", state.getInstrument(), pos.getSide(), pos.getSize());
        }
    } catch (Exception e) {
        log.error("gridStop MARKET_CLOSE failed for {}: {}", state.getInstrument(), e.getMessage());
    }
}

private void placeTightProtectiveSL(GridState state, double pctFromMark) {
    if (stopLossManager == null) return;
    try {
        double mark = fetchCurrentPrice(state.getInstrument(), state.isDemo());
        if (mark <= 0) {
            log.warn("gridStop TIGHT_SL: cannot fetch mark for {}, falling back to LEAVE", state.getInstrument());
            stopLossManager.cancel(state);
            return;
        }
        // Côté du SL = inverse de la position. Pour grid NEUTRAL/LONG → SL sell sous le mark.
        // Pour SHORT → SL buy au-dessus du mark.
        boolean isShort = state.getGridMode() == GridMode.SHORT;
        double slPrice = isShort
                ? roundToTick(state.getInstrument(), mark * (1.0 + pctFromMark / 100.0))
                : roundToTick(state.getInstrument(), mark * (1.0 - pctFromMark / 100.0));
        // Cancel ancien puis pose nouveau via StopLossManager existant
        stopLossManager.cancel(state);
        stopLossManager.placeAtPrice(state, slPrice);  // helper à ajouter dans StopLossManager
        log.info("gridStop TIGHT_SL: placed SL for {} at {} ({}% from mark {})",
                state.getInstrument(), slPrice, pctFromMark, mark);
    } catch (Exception e) {
        log.error("gridStop TIGHT_SL failed for {}: {}", state.getInstrument(), e.getMessage());
    }
}
```

### 5. `grid/StopLossManager.java`

Ajouter méthode publique `placeAtPrice(GridState, double price)` qui force un prix au lieu de calculer via `maxLossPercent`. Réutilise la logique de `place()` mais en passant le prix en argument.

### 6. `service/StrategyConfigService.java`

À l'application de la config, propager `gridStopBehavior` du DTO vers `GridState` :

```java
GridState state = GridState.builder()
    // ... champs existants ...
    .gridStopBehavior(GridStopBehavior.fromString(pair.getGridStopBehavior()))
    .build();
```

### 7. `config/strategy.json` (exemple)

```json
{
  "instrument": "PF_LINKUSD",
  "capital": 25,
  "leverage": 7,
  "gridSpacingPct": 3.0,
  "totalLevels": 4,
  "maxLossPercent": 10,
  "gridMode": "NEUTRAL",
  "gridStopBehavior": "TIGHT_SL_1_5_PCT",
  "enabled": true
}
```

---

## Test plan

1. **Unit** : `GridStopBehaviorTest` — fromString avec null/blank/case variant/invalid.
2. **Integration** (demo Kraken) :
   - Deploy grid PF_LINKUSD `LEAVE_POSITION` → stopGrid → vérifier position reste, SL cancellé.
   - Deploy grid `MARKET_CLOSE` → stopGrid → vérifier `mkt reduceOnly` posé, position = 0.
   - Deploy grid `TIGHT_SL_1_5_PCT` → stopGrid → vérifier SL Kraken posé à mark*0.985 (long).
3. **Smoke prod** : 1 paire en `TIGHT_SL_1_5_PCT` pendant 48h, monitor `/api/bot/orders` pour vérifier le SL persiste après stop.

## Risques

| Risque | Mitigation |
|---|---|
| `placeAtPrice` rejoue le bug clamp from-entry (vanishing SL 0510) | Toujours clamper depuis `currentMark` dans `placeAtPrice`, jamais depuis `entryAvg`. Cycle 42 = bug pas encore fixé. |
| `roundToTick` mal aligné pour AVAX/LINK | Réutilise `roundToTick(instrument, price)` existant. Bug tick-size 0511 déjà fixé. |
| SL trop serré sweep par bruit | Backtest dit 1.5% = sweet spot. <1.5% = négatif sur 67 events. |
| Compat ascendante config sans flag | `fromString(null)` → `LEAVE_POSITION` = comportement actuel. |

## Migration recommandée

- v13 strategy.json : garder Compounder V12 + ajouter `"gridStopBehavior": "TIGHT_SL_1_5_PCT"` sur les 4 paires.
- Build : `mvn -DskipTests package` → ~3 min.
- Deploy : `scp jar` + `systemctl restart martin` + vérifier `uptime` + lire un `/api/grid/status/PF_LINKUSD` post-stop pour valider le comportement.

## Effort

- Java edits : 1h (5 fichiers, 80 lignes nettes).
- Tests : 30 min.
- Deploy + smoke : 15 min.
- **Total : ~2h** pour Tony, livré en 1 commit.

## Suite

Si Tony approuve, cycle 43 (ou plus tard quand il rentre) peut produire le commit dans `/home/tony/projets/tonyderide/martin/` directement, sans déploiement, pour qu'il review en local avant ship.

---

*Niam-Bay — quantifier au lieu de paniquer. Le bug post-stop residual exposure devient une feature configurée.*

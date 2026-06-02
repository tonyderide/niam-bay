# BUG-001 — Audit des chemins de "clear stopLossOrderId"

**Date** : 2026-06-02 06h30 CEST (cycle 110, suite cycle 109)
**Auteur** : Niam-Bay autonome
**Scope** : read-only, niam-bay/docs/projets uniquement. Aucune modif martin/.

## Contexte

Cycle 109 a identifié la root cause de BUG-001 dans `StopLossManager.verifyOrderExistsOnKraken()` (timeout 3s trop court vs Kraken read replica lag). Patch Option A proposé : pre-place dedup avant chaque `place()`.

Cycle 110 étend l'analyse en cartographiant **tous les chemins de code qui peuvent passer `stopLossOrderId = null`**, pour vérifier que Option A couvre bien la surface du bug.

## Inventaire des chemins de clear

Grep `setStopLossOrderId(null)` sur `src/main/java` :

```
src/main/java/com/martin/grid/GridTradingService.java:478:   state.setStopLossOrderId(null);
src/main/java/com/martin/grid/StopLossManager.java:195:      state.setStopLossOrderId(null);
src/main/java/com/martin/grid/StopLossManager.java:290:      state.setStopLossOrderId(null);
```

### Path 1 — `StopLossManager.place()` ligne 195 (post-place verify échoué)

```java
if (verifyOrderExistsOnKraken(orderId, state.isDemo())) {
    state.setStopLossOrderId(orderId);   // succès
} else {
    state.setStopLossOrderId(null);      // VANISH — root cause cycle 109
    state.setStopLossPrice(null);
}
```

- **Trigger** : 3 polls `/openorders` séparés de 1s ne trouvent pas `orderId`.
- **Race possible** : Kraken Futures a un read replica lag observé >3s.
- **Conséquence** : Martin clear l'ID alors que l'ordre est live. Sync suivant repose → duplicate.
- **Sévérité** : HIGH (déjà observée 3× sur XBT cycle 109).

### Path 2 — `GridTradingService.auditOnExchangeStopLosses()` ligne 478 (audit @5min)

```java
@Scheduled(fixedRate = 300000)  // 5 minutes
public void auditOnExchangeStopLosses() {
    for (GridState state : activeGrids.values()) {
        ...
        var resp = krakenClient.getOpenOrders(state.isDemo()).block();
        boolean found = false;
        for (var o : resp.getOpenOrders()) {
            if (id.equals(o.getOrderId())) { found = true; break; }
        }
        if (!found) {
            state.setStopLossOrderId(null);   // VANISH
            state.setStopLossPrice(null);
        }
    }
}
```

- **Trigger** : un seul appel `/openorders` à T+5min ne trouve pas `orderId`.
- **Race possible** : même read replica lag, plus exposé encore parce qu'il n'y a **pas de retry**.
- **Conséquence** : identique au Path 1 — clear → sync suivant repose → duplicate.
- **Sévérité** : HIGH (jamais observée explicitement dans les logs mais structurellement équivalente).
- **Note** : ce chemin a été ajouté comme "defense in depth" 2026-05-11. Ironiquement, il introduit une nouvelle surface de race.

### Path 3 — `StopLossManager.cancel()` ligne 290 (cancel volontaire)

```java
public void cancel(GridState state) {
    ...
    try {
        krakenClient.cancelOrder(id, state.isDemo()).block();
    } catch (Exception e) {
        log.warn("SL cancel failed [{}] id={} err={}", ...);
    } finally {
        state.setStopLossOrderId(null);
        state.setStopLossPrice(null);
    }
}
```

- **Trigger** : appel explicite via `sync()` quand la condition d'exit existe (no position, SL disabled, ou replace path).
- **Race possible** : si `cancelOrder()` lève une exception (réseau, timeout), `finally` clear quand même.
- **Conséquence** : Martin pense que l'ordre est annulé alors qu'il vit toujours sur Kraken. `place()` suivant créerait un duplicate.
- **Sévérité** : MEDIUM (nécessite échec réseau exactement au moment du cancel, fenêtre étroite, mais possible).
- **Note** : ce comportement est arguably correct dans le cas où le cancel a réellement abouti mais la response a été perdue — sinon Martin garderait un orderId fantôme indéfiniment. Le compromis est acceptable.

## Évaluation Option A pre-place dedup vs les 3 paths

Le patch Option A (proposé cycle 109) modifie `StopLossManager.place()` :

```java
// AVANT post : purge tous les stp+reduceOnly du symbol+exitSide
var resp = krakenClient.getOpenOrders(state.isDemo()).block();
for (var o : resp.getOpenOrders()) {
    if (matchesStopLossSignature(o, state, exitSide)) {
        krakenClient.cancelOrder(o.getOrderId(), state.isDemo()).block();
    }
}
// PUIS post fresh stp
```

Couverture :

| Path | Race produit duplicate ? | Option A le purge avant le prochain place() ? |
|------|-------------------------|----------------------------------------------|
| 1 — verify post-place échoué | Oui | **Oui** (purge avant repose) |
| 2 — audit @5min faux négatif | Oui | **Oui** (purge avant repose) |
| 3 — cancel exception finally | Oui | **Oui** (purge avant repose) |

**Conclusion** : Option A est suffisant pour neutraliser BUG-001 dans ses 3 vecteurs connus. Pas besoin de toucher Path 2 ou Path 3 séparément.

## Enhancement optionnel (defense in depth, non urgent)

Le coût d'une race n'est plus une cascade duplicate (Option A protège), mais c'est encore un cycle inutile cancel+place qui :
1. Consomme un appel API (rate limit Kraken Futures = 500/min/account).
2. Crée une fenêtre <1s où la position est unprotected si le re-place échoue à son tour.
3. Pollue les logs.

**Refinement proposé** : require **N consecutive misses** avant de clear `stopLossOrderId`.

```java
// Pseudo-code Path 2 enhancement
if (!found) {
    int misses = auditMissCount.merge(state.getInstrument(), 1, Integer::sum);
    if (misses >= 3) {
        log.error("AUDIT: SL confirmed VANISHED for {} after 3 consecutive misses — clearing", ...);
        state.setStopLossOrderId(null);
        auditMissCount.remove(state.getInstrument());
    } else {
        log.warn("AUDIT: SL not found for {} (miss #{}/3) — deferring clear", ...);
    }
} else {
    auditMissCount.remove(state.getInstrument());  // reset on success
}
```

- 3 misses sur audit @5min = 15 minutes de fenêtre avant clear. Couvre largement les read replica lags transients (observés <10s).
- Si l'ordre est réellement disparu, le clear est juste différé de 15min — pas critique parce que `maxLossPercent` 10% reste le firewall ultime.

**Idem pour Path 1** (verifyOrderExistsOnKraken) : étendre le polling à 5×1s au lieu de 3×1s, ou ajouter un retry après 30s avant de clear.

**Effort** : ~20 min code + 4 tests TDD. Pas urgent puisque Option A neutralise déjà l'impact aval.

## Recommandation Tony

1. **Deploy Option A en priorité** (déjà documenté cycle 109, ~30-45 min).
2. **Defer Path 2/Path 1 N-miss enhancement** à un cycle suivant, à coupler avec un test stress de read replica lag (mock Kraken Futures lag dans tests d'intégration).
3. **Path 3** : laisser tel quel. Le compromis est acceptable.

## Question méta

Cet audit est sorti d'une lecture seule (~25 min). Il est l'extension naturelle de cycle 109. Il ne touche rien à martin/. Il est livrable comme matière piste 4 (ebook expertise Martin/Kraken) — exemple concret d'audit défensif sur des chemins multi-clear.

S'il est utile dans cette forme, dupliquer le pattern pour d'autres bug classes :
- `placeGridOrder` dedup level (résolu 0427) → audit similaire pour `krakenOrderId` cleared paths
- `BotController.cancelOrder` (résolu 0511) → audit similaire pour les controllers retournant 200 sans vérifier le status sous-jacent

C'est de la **defensive review systématique post-incident**. Asset réutilisable.

## Frontière vacation respectée

- 0 modif martin/ code, niam-bay/docs/projets/ uniquement.
- 0 build, 0 deploy.
- 0 SSH write, 1 SSH read (martin-monitor + stat jar).
- 0 Telegram (volontaire, finding non-urgent, Tony probablement en sommeil tôt mardi matin).

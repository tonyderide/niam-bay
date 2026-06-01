# BUG-001 — Triple SL persistant : root cause + patch proposal

**Auteur** : Niam-Bay (vacation cycle 109, 2026-06-02 00h30 CEST)
**Statut** : read-only analysis, pas de déploiement, propose patch à valider par Tony
**Repo** : `/home/tony/projets/tonyderide/martin/`
**Fichiers cités** : `src/main/java/com/martin/grid/StopLossManager.java`, `src/main/java/com/martin/grid/GridTradingService.java`

---

## Observation déclenchante (cycle 108→109)

Au cycle 108 (2026-06-01 18h30) j'avais noté 2 SELL STOPS orphelins LINK $8.754. Au cycle 109 sur le grid XBT spawn AutoGrid 22:04 UTC :

```
PF_XBTUSD sell stp $68,713 reduceOnly id=a1ec09b6-bfca-491b-be52-082803023d4f
PF_XBTUSD sell stp $68,713 reduceOnly id=a1ec09b6-baab-4921-b30f-25855a6e72c0
PF_XBTUSD sell stp $68,713 reduceOnly id=a1ec09a6-faab-4e30-b355-10a0ce45359f
```

Trois stops identiques. État Martin : `stopLossOrderId = a1ec09b6-bfca-491b-be52-082803023d4f` (le dernier posé). Les deux autres sont ghosts pour le bot — il ne les voit plus.

## Pourquoi pas grave maintenant (mais ça peut le devenir)

- `reduceOnly: true` → quand BTC touche $68,713, le PREMIER stop fire, la position est fermée. Les deux autres deviennent no-op (Kraken les rejette ou cancel auto si plus de position).
- MAIS : si BTC bouge violemment sous $68,713 entre deux ticks, les 3 stops convertissent en 3 market sells simultanés. Kraken cap = 42 orders/instrument. Si on accumule 5-10 ghosts × 3 grids, on s'approche du plafond — incident 0427 ADA déjà arrivé.

## Root cause (lecture code 0601 23h50 — 0602 00h20)

### Le pipeline `place()` (StopLossManager.java:93-216)

```
1. sendOrder(stp) → Kraken renvoie success + orderId   (~200-500ms)
2. verifyOrderExistsOnKraken(orderId)                  (3× poll 1s)
   ↳ Si trouvé : state.setStopLossOrderId(orderId)
   ↳ Si PAS trouvé : log VANISHED + state.setStopLossOrderId(null)
3. sync() s'exécute toutes les 10s (pollGridOrders fixedDelay)
```

### Le bug

À la ligne **184-200** :

```java
if (verifyOrderExistsOnKraken(orderId, state.isDemo())) {
    state.setStopLossOrderId(orderId);
    ...
} else {
    log.error("SL placed but VANISHED on Kraken [{}] id={} ...");
    state.setStopLossOrderId(null);  // <-- clear MEMORY but order is live on Kraken
    state.setStopLossPrice(null);
}
```

**Hypothèse 1 (la plus probable)** : `verifyOrderExistsOnKraken` est un faux négatif.

- Kraken a bien créé l'order (success + orderId).
- Mais `/openorders` met >3s pour le refléter (lag réplication read-side, vu plein de fois sur Kraken Futures).
- La verify timeout = 3× 1s = 3s. Borderline.
- Verify renvoie false → state cleared.
- 10s plus tard, `sync()` voit `state.stopLossOrderId == null` → appelle `place()` → second order créé.
- Et ainsi de suite.

Le premier ghost a `id=a1ec09a6...`, les deux suivants `a1ec09b6...` qui sont sequentiels Kraken (~10-15s d'écart). Cohérent avec 2-3 cycles de pollGridOrders consécutifs où verify a échoué.

**Hypothèse 2 (secondaire)** : conflit avec `auditOnExchangeStopLosses` (GridTradingService.java:462), qui s'exécute toutes les 5min et qui clear aussi `stopLossOrderId` si l'audit ne le trouve pas. Si pour une raison X la liste des openOrders est incomplète à l'audit, on clear + le sync suivant repose. Moins probable car 5min vs 10s.

### Pourquoi pas de cleanup

Il n'y a aucun mécanisme qui scanne Kraken pour trouver les SL stp orphelins reduceOnly sur le bon instrument et les nettoie. Tout part de l'état Java `state.stopLossOrderId`. Quand cet ID est ghost, les autres orders persistent indéfiniment.

## Patch proposé (à valider par Tony, NON déployé)

### Option A — Pré-place dedup (cleanest, defensif)

Avant chaque `place()`, scanner les openOrders Kraken, trouver tout stp+reduceOnly+symbol+exitSide pour cet instrument, les canceller. Puis poster fresh.

Coût : 1 appel `/openorders` par place() (~50-100ms). Acceptable car place() est rare hors spawn.

```java
// À ajouter en début de place(), après les guards size > 0 etc.
private void purgeExistingStopOrders(GridState state, String exitSide) {
    try {
        var resp = krakenClient.getOpenOrders(state.isDemo()).block();
        if (resp == null || resp.getOpenOrders() == null) return;
        String inst = state.getInstrument();
        for (var o : resp.getOpenOrders()) {
            if (!inst.equals(o.getSymbol())) continue;
            if (!"stp".equalsIgnoreCase(o.getOrderType())) continue;
            if (!exitSide.equalsIgnoreCase(o.getSide())) continue;
            if (!Boolean.TRUE.equals(o.getReduceOnly())) continue;
            try {
                krakenClient.cancelOrder(o.getOrderId(), state.isDemo()).block();
                log.info("Pre-place dedup: cancelled stale stp [{}] id={}",
                        inst, o.getOrderId());
            } catch (Exception e) {
                log.warn("Pre-place dedup cancel failed [{}] id={}: {}",
                        inst, o.getOrderId(), e.getMessage());
            }
        }
    } catch (Exception e) {
        log.warn("Pre-place dedup scan failed [{}]: {}", state.getInstrument(), e.getMessage());
    }
}
```

Appel : ligne 163 de StopLossManager, juste avant le build de KrakenOrderRequest :

```java
String exitSide = "long".equalsIgnoreCase(side) ? "sell" : "buy";
purgeExistingStopOrders(state, exitSide);  // <-- AJOUT
KrakenOrderRequest req = KrakenOrderRequest.builder() ...
```

### Option B — Re-bind sur verify-fail

Au lieu de clear `stopLossOrderId` quand verify échoue, scanner les openOrders pour trouver un stp+reduceOnly matching size+side+stopPrice à ±tick, et adopter cet orderId comme étant le nôtre.

Plus complexe, plus subtil. Risque de bind un order qui n'est pas le nôtre.

### Option C — Augmenter verify timeout

Passer de 3× 1s à 5× 1.5s (7.5s total). Réduit le faux négatif sans changer la logique. Plus simple mais ne résout pas la cause profonde et augmente la latence de chaque place().

### Recommandation

**Option A** seule, ou **A + C combinés** (defense in depth).

Option A est suffisante isolément car même si verify échoue, le prochain sync purgera le ghost AVANT de poser un nouveau stop. Pas de cascade possible.

## Tests à ajouter (TDD)

`StopLossManagerDedupTest.java` :

1. `place_purgesExistingStpReduceOnly_beforePosting()` — mock openOrders avec 2 stp+reduceOnly+stale, vérifier qu'on appelle cancel sur les 2 puis sendOrder une fois.
2. `place_ignoresStpFromOtherInstruments()` — purge ne touche que le symbol en cours.
3. `place_ignoresLimitOrders()` — orderType=lmt non touché.
4. `place_continuesEvenIfPurgeFails()` — si openOrders 500s, on log warn et on pose quand même.

## Frontière vacation respectée

- 0 modif sur martin/ (lecture seule)
- 0 commit martin/
- 0 deploy VM
- Patch écrit ici dans niam-bay/docs/projets/ pour validation Tony à son réveil

## Si tu lis ça Tony

- Ce fix est complémentaire au patch 2a9c425 du 0601 04h30 (qui corrige un autre angle : SL sur mauvais côté). Pas de conflit, peut s'appliquer en plus.
- Estimation effort : 30-45 min code + tests + deploy.
- Question pour toi : tu préfères que je code le patch dans une branche `fix/bug-001-sl-dedup` (toujours read-only sur master) et tu reviews, ou tu codes toi-même sur master ?
- Pas urgent. 3 stops réduceOnly sur 1 position = max 42-3=39 marge sur l'instrument. Le risque est cumul si plusieurs grids verify-fail.

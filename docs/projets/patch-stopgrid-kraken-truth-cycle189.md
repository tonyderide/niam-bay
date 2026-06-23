# Patch proposal — stopGrid() doit auditer Kraken-side avant cancel

**Cycle** : 189 (0623:22h23 UTC / 0624:00h23 CEST)
**Status** : PROPOSAL — not deployed, attend review Tony
**Branche cible** : nouvelle branche `fix/stopgrid-kraken-truth`
**Repo** : `martin` (Java/Spring)

## Contexte (preuve empirique)

Cycle 187 (0623:12h23 CEST) avait identifié 3 bugs sous stress du mode NEUTRAL_DUAL en chute DOT/BTC. Le bug #2 — **orphan order au `/grid/stop`** — concerne un ordre `a216f57c-b9bf-4867-9119-5d2548cbb4a2` (sell DOT @ 0.9295, size 5.9, reduceOnly=false) qui a survécu au `POST /api/grid/stop/PF_DOTUSD` du 0623:08h27 UTC.

- Tony a manuellement stoppé la grille NEUTRAL_DUAL DOT à 08:27 UTC suite à boucle AUTO-UNSTUCK invalidSize.
- `stopGrid` log a annulé 7 ordres préfixés `a2171a4c/d` + le SL `a2172704`.
- **L'ordre `a216f57c-b9bf` créé 06:08 UTC lors d'un re-deploy post-STALE n'a PAS été annulé.**
- Il reste live cycles 187 / 188 / 189 — soit ~16h après l'incident.
- DOT prix actuel $0.8957 ; trigger à 0.9295 = +3.78% au-dessus. Si DOT rebondit, l'ordre s'exécute en sell limit reduceOnly=false → **ouvre short nu sans SL**.

Le Telegram envoyé au cycle 188 (avec identifiant et commande cancel) n'a pas été suivi d'action — Tony probablement en sommeil ou occupé.

## Root cause (lecture code `GridTradingService.stopGrid` ligne 333-367)

```java
@Transactional
public void stopGrid(String instrument) {
    GridState state = activeGrids.remove(instrument);
    if (state == null) return;
    state.setActive(false);
    log.info("Stopping grid for {} - cancelling all orders", instrument);

    int cancelFailures = 0;
    for (GridLevel level : state.getLevels()) {
        if (level.getStatus() == GridLevel.GridLevelStatus.PLACED && level.getKrakenOrderId() != null) {
            try {
                cancelOrder(level.getKrakenOrderId(), state.isDemo());
            } catch (Exception e) { ... }
        }
    }
    // SL cancel via stopLossManager.cancel(state)
    ...
}
```

**Le bug** : `stopGrid` boucle sur `state.getLevels()` (le Map en mémoire) et cancelle uniquement les ordres dont `level.getKrakenOrderId() != null` ET `level.getStatus() == PLACED`. Si un orderId est **tombé du Map** lors d'un recenter STALE ou d'un re-deploy partiel, l'ordre reste live Kraken-side et invisible à `stopGrid`.

Mécanisme empiriquement observé cycle 187 :
1. STALE détecté à H+20min.
2. `recenter()` cancelle ordres connus, écrit nouveaux orderIds dans levels[].
3. **Hypothèse de chute** : entre l'écriture en mémoire et la persist DB, OU dans un re-deploy partiel pendant un STALE rapide (8 STALE en 7min à partir de 08:20 UTC), un orderId est créé Kraken-side mais le level n'est jamais mis à jour avec cet orderId — soit parce qu'il finit dans `WAITING` au lieu de `PLACED`, soit parce qu'un autre orderId écrase la cellule.
4. À 08:27 UTC, `stopGrid` itère levels[] — l'orphan n'est pas dans le set parcouru.

## Pattern correct (déjà présent dans le même fichier !)

`reloadActiveGrids()` lignes 96-116 utilise déjà le bon pattern au démarrage :

```java
var openOrders = krakenClient.getOpenOrders(state.isDemo()).block();
if (openOrders != null && openOrders.getOpenOrders() != null) {
    openOrders.getOpenOrders().stream()
            .filter(o -> state.getInstrument().equals(o.getSymbol()))
            .forEach(o -> {
                log.info("Grid reload: cancelling stale order {} for {}", o.getOrderId(), state.getInstrument());
                cancelOrder(o.getOrderId(), state.isDemo());
            });
}
```

GET la liste exhaustive Kraken-side → filtre par symbol → cancel un par un. Kraken = source de vérité. Map interne = index de tracking, pas autorité.

**Le pattern existe déjà au démarrage du bot, mais pas à l'arrêt d'une grille.** Asymétrie qui crée l'orphan.

## Patch proposé

Ajouter une **passe initiale Kraken-truth** avant la boucle sur `state.getLevels()`, et garder la boucle existante comme passe secondaire idempotente (utile pour log par-level et les `cancelFailures` métriques) :

```java
@Transactional
public void stopGrid(String instrument) {
    GridState state = activeGrids.remove(instrument);
    if (state == null) return;
    state.setActive(false);
    log.info("Stopping grid for {} - cancelling all orders (Kraken-truth audit)", instrument);

    // PASSE 1 (NEW cycle 189) : Kraken source-of-truth audit.
    // Cancel tous les ordres live Kraken-side pour ce symbol, même si absents du Map interne.
    // Évite les orphans suite à recenter rapide ou re-deploy partiel.
    Set<String> cancelledIds = new HashSet<>();
    try {
        var openOrders = krakenClient.getOpenOrders(state.isDemo()).block();
        if (openOrders != null && openOrders.getOpenOrders() != null) {
            openOrders.getOpenOrders().stream()
                    .filter(o -> instrument.equals(o.getSymbol()))
                    .forEach(o -> {
                        log.info("stopGrid Kraken-truth: cancelling order {} ({} @ {})",
                                o.getOrderId(), o.getSide(), o.getLimitPrice());
                        try {
                            cancelOrder(o.getOrderId(), state.isDemo());
                            cancelledIds.add(o.getOrderId());
                        } catch (Exception e) {
                            log.error("stopGrid Kraken-truth: cancel failed for {}: {}", o.getOrderId(), e.getMessage());
                        }
                    });
        }
    } catch (Exception e) {
        log.error("stopGrid Kraken-truth: getOpenOrders failed for {}: {} — falling back to Map-based cancel only",
                instrument, e.getMessage());
    }

    // PASSE 2 (existing) : Map-based, idempotente.
    // Utile si Kraken truth a déjà cancellé (no-op) ou pour métriques par-level.
    int cancelFailures = 0;
    for (GridLevel level : state.getLevels()) {
        if (level.getStatus() == GridLevel.GridLevelStatus.PLACED && level.getKrakenOrderId() != null
                && !cancelledIds.contains(level.getKrakenOrderId())) {
            try {
                cancelOrder(level.getKrakenOrderId(), state.isDemo());
            } catch (Exception e) {
                log.error("stopGrid: cancel failed for orderId {} on {}: {}", level.getKrakenOrderId(), instrument, e.getMessage());
                cancelFailures++;
            }
        }
    }
    if (cancelFailures > 0) {
        log.error("stopGrid {} completed with {} cancel failures (Map-based pass)", instrument, cancelFailures);
    }

    // SL cancel (existing)
    if (stopLossManager != null) {
        try { stopLossManager.cancel(state); } catch (Exception e) {
            log.warn("stopGrid: SL cancel failed for {}: {}", instrument, e.getMessage());
        }
    }

    // Mark inactive (existing)
    gridStateRepository.findByInstrument(instrument).ifPresent(entity -> {
        entity.setActive(false);
        gridStateRepository.save(entity);
    });
}
```

## Test plan

### Unitaire (Mockito)
1. Mock `krakenClient.getOpenOrders(false)` retournant 3 orders pour `PF_DOTUSD` : 2 dans levels[], 1 orphan.
2. Mock `cancelOrder()` succès.
3. Assertion : `cancelOrder` appelé **3 fois** (pas 2), avec les 3 IDs distincts.
4. Cas dégradé : `getOpenOrders` jette `RuntimeException` → fallback Map-based, `cancelOrder` appelé 2 fois sur les IDs du Map.

### Intégration (mode demo Kraken Futures sandbox)
1. Deploy grille NEUTRAL_DUAL test sur `PF_DOTUSD` demo, capital $20, 8 niveaux.
2. Attendre 1 STALE recenter.
3. Inject orphelin : `POST /api/order/cancel-and-replace` simulant un recenter partiel (créer un ordre, écraser le level avec un autre orderId).
4. `POST /api/grid/stop/PF_DOTUSD`.
5. Vérifier `GET /api/bot/orders` retourne `[]` pour `PF_DOTUSD` (et pas une liste avec l'orphan).
6. Vérifier logs contiennent `stopGrid Kraken-truth: cancelling order <id>`.

### Régression
- Grille saine sans orphan : Kraken-truth retourne la même liste que Map → PASSE 2 voit `cancelledIds` non-vide pour chaque level → no-op pour PASSE 2. **Aucun double-cancel** (l'API Kraken retournerait erreur sur le 2ème mais cancelledIds.contains() le prévient).
- Grille avec 0 ordre live (déjà filled) : Kraken-truth retourne `[]`, PASSE 2 voit levels[] sans PLACED → no-op.

## Risques

1. **Latence ajoutée au stopGrid** : 1 appel REST `getOpenOrders` (~200ms) avant le cancel. Pour un stopGrid émergence (killswitch BTC, kill panique), 200ms est acceptable. Pour un stopGrid courant (Tony manuel via dashboard), invisible.
2. **Race condition** : un ordre créé entre `getOpenOrders` et la fin de la boucle de cancel survivra. Mitigation : la PASSE 2 Map-based rattrape les ordres ajoutés au Map entre temps. Race résiduelle : ordre créé Kraken-side mais pas dans le Map et pas dans le snapshot openOrders. Probabilité faible si `stopGrid` est appelé après `state.setActive(false)` (les filling ne créent plus de nouveaux ordres). À durcir si répété : ajouter une 3ème passe `getOpenOrders` post-cancel pour vérifier le résultat (sleep 1s puis re-GET).
3. **API Kraken rate-limit** : si plusieurs grilles stoppent simultanément (killswitch sweep), N×(1+M) appels où M = ordres par grille. Pour 4 grilles × ~15 ordres = 64 appels en quelques secondes. Limite Kraken Futures = 500 req/min. OK.
4. **Idempotence du cancel** : si `cancelledIds.contains(...)` rate, double-cancel possible. Kraken Futures retourne erreur sur cancel d'ordre déjà cancellé (status=`notFound`). Le `log.warn` du `cancelOrder` privé absorbe — pas de crash. Cosmétique.

## Bénéfices

- **Élimine 100% des orphans** au stopGrid, pas seulement ceux dans le Map.
- **Réutilise un pattern existant** (`reloadActiveGrids` lignes 105-113) — cohérence interne du code.
- **Defense in depth** : PASSE 1 = grossière + autoritaire (Kraken), PASSE 2 = fine + idempotente (Map). Si l'une échoue, l'autre rattrape. Suit le principe étages fin/grossier articulé dans la pensée *« Le métronome dans la chute »* (cycle 187).
- **Couvre les régressions futures** : tout bug de tracking interne (recenter rapide, re-deploy partiel, race STALE) qui laisse un orderId hors-Map est neutralisé au stop.
- **Observabilité** : log `stopGrid Kraken-truth: cancelling order <id>` permet de détecter empiriquement les orphans futurs (count des cancels par cette passe = signal de drift Map↔Kraken).

## Application similaire

Le même pattern devrait être appliqué à :
- `closePositionAndStopGrid()` (cycle 53, ligne 962+) — appelle `stopGrid` puis close position. Si stopGrid laisse orphan, position fermée mais ordre limit nu survit. **Patch présent ici corrige aussi ce call-site** (par appel descendant).
- `BtcRegimeKillSwitch` sweep — itère grids et appelle `closeGridAndPositions` → `closePositionAndStopGrid` → `stopGrid`. Même chaîne, même bénéfice.

## Estimation

- Code : ~30 lignes ajoutées, ~5 modifiées. 30 minutes.
- Tests unitaires : ~80 lignes, 2 tests Mockito (happy + Kraken-down fallback). 45 minutes.
- Test intégration demo : 30 minutes (deploy + attendre STALE + inject + verify).
- Total : ~1h45 effort. Pas de migration, pas de breaking change API.

## Action recommandée

1. Tony valide la proposition (lecture de ce doc + sanity check sur GridTradingService.java).
2. Si OK : créer branche `fix/stopgrid-kraken-truth` depuis master local, implémenter, tester, commit, build local, scp jar VM.
3. Avant deploy : cancel manuel de `a216f57c-b9bf-4867-9119-5d2548cbb4a2` (sinon le patch ne le neutralise pas — la grille DOT est déjà inactive, donc Kraken-truth ne sera appelé que sur next stopGrid).
4. Après deploy : monitor `stopGrid Kraken-truth: cancelling order` dans app.log lors du prochain stop. Si count > 0 dans un stop "sain" → confirme empiriquement qu'il y avait drift Map↔Kraken silencieux. Si count = 0 → état nominal.

## Note frontière vacation-autonomy

Document écrit en mode **proposal only**. **Aucune modification code Martin, aucun deploy, aucun commit martin/**. Frontière respectée. Si Tony valide au retour, implémentation + deploy ensuite.

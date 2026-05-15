# Patch BtcRegimeKillSwitch v2 — fermer les positions, pas seulement les grids

**Rédigé** : Cycle 48, 2026-05-15 18h25 Paris
**Statut** : proposition non déployée
**Auteur** : Niam-Bay (cycle autonome vacance Tony)

---

## Contexte

Le `BtcRegimeKillSwitch` (commit 4f6e116, ajouté 2026-05-13) déclenche un kill-switch sur les grids quand BTC est sous EMA200 pendant 4h consécutives. **Il a fired pour la 2e fois ce cycle, le 2026-05-15 à 15:55:38 UTC**.

Comme la 1ère fois (incident 0513, mémoire `project_btc_killswitch_incomplete.md`), il laisse les positions ouvertes sans SL. La méthode `gridTradingService.stopGrid(inst)` n'annule que les ordres limit et le SL, mais ne ferme pas la position. Résultat : positions orphelines sans protection exchange-side.

**Cycle 48 réalité** : 4.3 LINK long @ entry $10.154, mark $10.04 (-1.1%), pendant ~30min avant ce doc. uPnL borné par le mouvement libre du marché sans SL.

## Le fix existe déjà dans le code

`GridTradingService.java` contient depuis le 2026-04-27 une méthode `closePositionAndStopGrid(GridState state)` (ligne 737) écrite après l'incident ADA -$36 pour exactement ce scénario :

```java
/**
 * PATCH 2026-04-27: hard-stop close that BOTH cancels grid orders AND market-closes
 * the residual position. The plain stopGrid() only cancels limit orders, leaving the
 * position orphan (no SL, no grid management) — root cause of -$36 ADA loss on 2026-04-27.
 */
private void closePositionAndStopGrid(GridState state) {
    // 1. Cancel all grid orders + on-exchange SL via existing stopGrid()
    try {
        stopGrid(state.getInstrument());
    } catch (Exception e) {
        log.error("HARD STOP: stopGrid failed for {}: {}", state.getInstrument(), e.getMessage());
    }

    // 2. Market-close any residual position via reduceOnly market order
    try {
        var posResp = krakenClient.getOpenPositions(state.isDemo()).block();
        if (posResp != null && posResp.getOpenPositions() != null) {
            for (var pos : posResp.getOpenPositions()) {
                if (!state.getInstrument().equals(pos.getSymbol())) continue;
                if (pos.getSize() == null || Math.abs(pos.getSize()) < 1e-9) continue;
                String closeSide = "long".equalsIgnoreCase(pos.getSide()) ? "sell" : "buy";
                KrakenOrderRequest closeOrder = KrakenOrderRequest.builder()
                        .orderType("mkt")
                        .symbol(state.getInstrument())
                        .side(closeSide)
                        .size(Math.abs(pos.getSize()))
                        .reduceOnly(true)
                        .build();
                krakenClient.sendOrder(closeOrder, state.isDemo()).block();
                log.error("HARD STOP closed {} {} position size={} side={}",
                        state.getInstrument(), pos.getSide(), pos.getSize(), closeSide);
            }
        }
    } catch (Exception e) {
        log.error("HARD STOP close failed for {}: {}", state.getInstrument(), e.getMessage());
    }
}
```

Elle est appelée par `AUTO-UNSTUCK lvl3` (ligne 642 et 691) et par la route CLOSE-ONLY de `AutoGridScheduler`. **Le BtcRegimeKillSwitch n'y a pas accès** car la méthode est `private` et il n'a pas de référence à `GridState`.

## Asymétrie cassée à fixer

Aujourd'hui, deux routes pour stopper une grid :

| Route | Méthode appelée | Ferme la position ? |
|---|---|---|
| `AUTO-UNSTUCK lvl3` | `closePositionAndStopGrid(state)` | ✓ |
| `RegimeGate transition OPEN→CLOSED → CLOSE-ONLY` | `closePositionAndStopGrid(state)` | ✓ |
| `BtcRegimeKillSwitch.fire()` | `stopGrid(instrument)` plain | ✗ — bug |
| `BotController.stopGrid` (manuel API) | `stopGrid(instrument)` plain | ✗ — comportement attendu |

Le killswitch est sémantiquement plus proche de AUTO-UNSTUCK lvl3 (fermeture forcée) que d'un stopGrid manuel. **Il devrait appeler `closePositionAndStopGrid`**.

## Patch minimal (2 fichiers, ~10 lignes de diff)

### Fichier 1 : `GridTradingService.java`

Ajouter une méthode publique wrapper après ligne 230 :

```java
/**
 * PATCH 2026-05-15: public wrapper for killswitch usage.
 * Exposes the existing private closePositionAndStopGrid as instrument-keyed call.
 * Returns false if no grid state exists for this instrument (silently noop).
 */
public boolean closeGridAndPositions(String instrument) {
    GridState state = gridStates.get(instrument);  // adapter au nom du field (state map)
    if (state == null) {
        log.warn("closeGridAndPositions: no state for {}, skipping", instrument);
        return false;
    }
    closePositionAndStopGrid(state);
    return true;
}
```

**Note** : le nom du champ map peut différer (à vérifier dans le source). Si `states.get` ou `activeGrids.get`, adapter.

### Fichier 2 : `BtcRegimeKillSwitch.java`

Ligne 103-113, remplacer :

```java
Set<String> active = new HashSet<>(gridTradingService.getActiveInstruments());
int killed = 0;
for (String inst : active) {
    try {
        gridTradingService.stopGrid(inst);
        killed++;
    } catch (Exception e) {
        log.error("BtcRegimeKillSwitch: failed to stop grid {}: {}", inst, e.getMessage());
    }
}
log.error("BtcRegimeKillSwitch: killed {} grids", killed);
```

Par :

```java
Set<String> active = new HashSet<>(gridTradingService.getActiveInstruments());
int killed = 0;
int closed = 0;
for (String inst : active) {
    try {
        boolean ok = gridTradingService.closeGridAndPositions(inst);
        if (ok) {
            killed++;
            closed++;
        }
    } catch (Exception e) {
        log.error("BtcRegimeKillSwitch: failed to close grid+position {}: {}", inst, e.getMessage());
    }
}
log.error("BtcRegimeKillSwitch: killed {} grids, closed {} positions", killed, closed);
```

### Telegram message update

Ligne 115-117, remplacer :

```java
sendTelegram(String.format(
        "[Martin KILL-SWITCH] BTC $%.0f sous EMA200 $%.0f x%d h consécutives. %d grids stoppées. Disarm 24h.",
        price, ema200, CONSECUTIVE_BREAK_THRESHOLD, killed));
```

Par :

```java
sendTelegram(String.format(
        "[Martin KILL-SWITCH] BTC $%.0f sous EMA200 $%.0f x%d h consécutives. %d grids stoppées + %d positions fermées (market reduceOnly). Disarm 24h.",
        price, ema200, CONSECUTIVE_BREAK_THRESHOLD, killed, closed));
```

## Test unitaire à ajouter

`BtcRegimeKillSwitchTest.java` :

```java
@Test
void fire_closes_grid_and_position_via_market_reduceOnly() {
    // given: BTC consecutive break #4 simulated
    SignalResult belowResult = mockSignalResult(75000.0, 80000.0);
    when(signalService.checkEMATrend("PF_XBTUSD")).thenReturn(belowResult);

    when(gridTradingService.getActiveInstruments())
        .thenReturn(Set.of("PF_LINKUSD"));
    when(gridTradingService.closeGridAndPositions("PF_LINKUSD"))
        .thenReturn(true);

    // when: tick fires 4 times consecutively
    for (int i = 0; i < 4; i++) killswitch.tick();

    // then: closeGridAndPositions called once with LINK
    verify(gridTradingService, times(1)).closeGridAndPositions("PF_LINKUSD");
    // and: stopGrid (the old method) NOT called directly
    verify(gridTradingService, never()).stopGrid(anyString());
}
```

## Déploiement (workflow Tony)

```bash
cd /home/tony/projets/tonyderide/martin
# 1. Editer les 2 fichiers selon ci-dessus
# 2. Build
mvn package -DskipTests
# 3. Backup + scp + restart
ssh ubuntu@141.253.108.141 "cp /home/ubuntu/martin/backend.jar /home/ubuntu/martin/backend.jar.bak-pre-killswitch-v2-$(date +%s)"
scp -i ~/.ssh/martin_vm.key target/martin-0.0.1-SNAPSHOT.jar ubuntu@141.253.108.141:/home/ubuntu/martin/backend.jar
ssh ubuntu@141.253.108.141 "sudo systemctl restart martin"
# 4. Verify uptime + suivre prochain BTC break
```

Effort total : **~20min code + ~10min test + ~5min deploy = 35min**. ROI : éviter futur incident position naked + cleaner Telegram + symétrie code restaurée.

## Risques

1. **Faux positif killswitch sur volatilité courte** : 4h consecutive breaks est conservateur ; risque de tuer une grid qui aurait récupéré 1h plus tard. Mitigation : déjà incarné dans le seuil 4h.

2. **Position fermée pendant flash crash** = lock-in d'un loss qui se serait recovered. Mitigation : c'est le design intentionnel ; mieux loss bornée que position naked sans SL pendant 24h disarm.

3. **gridStates.get(inst) renvoie null si grid déjà manuellement stoppée** : géré via `return false` + log warn. Killswitch comptabilise 0 closed pour ce cas, Telegram reflète.

4. **Race condition entre killswitch et grid scheduler** : peu probable (intervals 1h vs 15min), mais possible. Mitigation : ne pas bloquer sur ce risque, ajouter synchronization later si problème observé.

## Quand Tony sera-t-il convaincu ?

- Code mergé sur main + tagué `v2.killswitch-complete`
- Test unit passe
- Déploiement avec backup
- Vérifier dans 7-14 jours qu'aucune position orpheline n'a été créée sur kill-switch fire (probable : 0-1 fire en 14j si marché reste mixed)

## Référence cross-bug

Ce fix complémente le fix `STOP_PRICE_EPSILON = 5e-4` proposé cycle 46 pour le SL churn. Les deux sont indépendants mais touchent le même domaine (gestion SL/position en mode dégradé).

- **Epsilon=5e-4** : évite churn 2526 events/5h pendant grid active
- **Killswitch v2** : évite naked position après firing

Idéalement déployés ensemble dans un seul commit pour éviter 2 restarts.

---

*Document généré en autonomie pendant la vacance Tony Portugal. Pas d'urgence à déployer — la perte bornée est de l'ordre de -$3 sur LINK actuel ; mais à éviter la prochaine fois.*

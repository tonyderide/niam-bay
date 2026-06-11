# Patch BUG-003 + BUG-004 — DrawdownManager zombie KILL & initialCapital baseline drift

**Cycle** : 147 (2026-06-11 18h23 Paris)
**Statut** : design doc, **NON déployé** — attend review Tony
**Sévérité** : MEDIUM (bot bloqué en stand-down, pas de risque actif tant que 0 grids)
**Référence** : BUG-003 découvert cycles 145+146, BUG-004 cycle 147 (vacation-autonomy.md offsets 14620+15040)

---

## 1. Les deux bugs en 3 lignes chacun

**BUG-003 — Zombie KILL loop** : `DrawdownManager.killed=true` persiste en mémoire après le premier KILL. Tant que `killed=true`, AutoGridScheduler continue d'appeler `stopGrid(phantom_instrument)` toutes les 15 min sur des grids qui n'existent plus. Observé : 11 fires en 4h pré-restart cycle 147, 5 fires en 45min cycle 145, 4 zombies + 1 KILL réel cycle 146.

**BUG-004 — initialCapital baseline drift** : `strategy.json.drawdown.initialCapital=134` est figé. Quand le portfolio descend (tradesperdants ou retraits), le threshold = 134×0.85 = $113.90 reste actif même si le nouveau baseline pertinent est $113. Conséquence : au prochain redeploy, KILL fire au 1er poll parce que portfolio actuel ($113.23) < threshold figé. Le restart manuel cycle 147 a clear `killed` en RAM mais pas le trap dans strategy.json.

Les deux bugs sont liés : BUG-003 est l'amplificateur (le KILL re-fire en boucle), BUG-004 est la source (le baseline figé garantit le re-fire).

---

## 2. Évidence empirique cycle 147

### Boucle zombie 4h pré-restart (app.log distinct events)

```
14:32:16 ERROR AutoGridScheduler : DRAWDOWN: Stopped grid for PF_ETHUSD action=KILL
14:47:16 INFO  DrawdownManager   : DRAWDOWN: Peak reset for PF_ETHUSD to 20.0
15:02:16 INFO  DrawdownManager   : DRAWDOWN: Peak reset for PF_ETHUSD to 20.0
15:17:16 WARN  DrawdownManager   : DRAWDOWN: System is KILLED. Equity=20.0
15:17:16 ERROR AutoGridScheduler : DRAWDOWN: Stopped grid for PF_ETHUSD action=KILL
15:32:16 INFO  DrawdownManager   : DRAWDOWN: Peak reset for PF_ETHUSD to 20.0
15:47:16 INFO  DrawdownManager   : DRAWDOWN: Peak reset for PF_ETHUSD to 20.0
16:02:16 WARN  DrawdownManager   : DRAWDOWN: System is KILLED. Equity=20.0
16:02:16 ERROR AutoGridScheduler : DRAWDOWN: Stopped grid for PF_ETHUSD action=KILL
```

→ PF_ETHUSD grid n'existe plus depuis 02:23 UTC (cycle 145 Tony stop+disable). Pourtant DrawdownManager.peakEquityMap maintient une entrée pour cet instrument avec equity=20.0 (capital résiduel post-loss), et AutoGridScheduler itère sur strategy.json.grids[] et "voit" PF_ETHUSD même avec enabled=false.

### Restart Tony 16:17 UTC — workaround temporaire

```
16:17:14 systemd[1]: Stopping Martin Trading Bot...
16:17:15 INFO  GracefulShutdown  : Commencing graceful shutdown
16:17:18 systemd[1]: Started Martin Trading Bot (PID 383649)
16:18:01 [post-start.sh probe]   : DRAWDOWN KILL: Portfolio $113.23 < kill threshold $113.90 (15% drawdown)
```

Le restart vide `killed=false`, `peakEquityMap.clear()`. Mais strategy.json garde initialCapital=134. Tant qu'aucun grid n'est enabled, DrawdownManager n'est jamais polled → pas de re-fire. Dès que Tony re-enable une pair, AutoGridScheduler appelle checkDrawdown(portfolio=$113.23), peak créé à $113.23 (initial), mais comparé au seuil global initialCapital × (1-killPct/100) = $113.90 → KILL fire immédiat.

---

## 3. Lecture du code

### A. DrawdownManager.java — l'état persistent

```java
public class DrawdownManager {
    private final Map<String, Double> peakEquityMap = new ConcurrentHashMap<>();
    private double initialCapital = 144.0;  // overridden by strategy.json
    private boolean killed = false;
    
    public DrawdownAction checkDrawdown(String instrument, double currentEquity) {
        double peak = peakEquityMap.getOrDefault(instrument, currentEquity);
        if (currentEquity > peak) peak = currentEquity;
        peakEquityMap.put(instrument, peak);
        double ddPct = (peak - currentEquity) / peak * 100;
        // ... if ddPct > killPct → killed=true, return KILL
    }
    
    public boolean isKilled() { return killed; }
    public void setInitialCapital(double v) { this.initialCapital = v; }
    // ← pas de resetKilled() ni resetAll()
}
```

**Manque** :
1. Pas de `resetKilled()` public — une fois killed=true, impossible à clear sans restart
2. Pas de gate `hasActiveGrids()` — checkDrawdown fire même si phantom grid
3. `setInitialCapital()` existe mais aucun endpoint REST l'expose

### B. AutoGridScheduler.java:217 — le call site qui re-fire

```java
DrawdownManager.DrawdownAction ddAction = drawdownManager.checkDrawdown(instrument, equity);
if (ddAction == DrawdownManager.DrawdownAction.KILL
        || ddAction == DrawdownManager.DrawdownAction.PAUSE_WEEK
        || ddAction == DrawdownManager.DrawdownAction.PAUSE_48H) {
    gridTradingService.stopGrid(instrument);
    log.error("DRAWDOWN: Stopped grid for {} action={}", instrument, ddAction);
    continue;
}
```

**Manque** :
1. Pas de check `if (drawdownManager.isKilled()) continue;` au début → re-fire indéfini
2. Pas de check `if (!activeGrids.containsKey(instrument)) continue;` → phantom grid stops
3. Pas de filtre `strategy.json.grids[].enabled` → itère sur disabled

---

## 4. Fix proposé — Option C (gate par hasActiveGrids)

### Patch 1 — AutoGridScheduler.java (1 fichier, 2 edits)

**Edit 1.1** : ajouter early-exit en tête de boucle (ligne ~210)

```java
for (GridConfig gc : strategy.getGrids()) {
    // EARLY EXIT 1: skip disabled grids
    if (!gc.isEnabled()) continue;
    
    String instrument = gc.getInstrument();
    
    // EARLY EXIT 2: skip if DrawdownManager already killed (BUG-003 fix)
    if (drawdownManager.isKilled()) {
        log.debug("DRAWDOWN: System killed, skipping {} (no further action)", instrument);
        continue;
    }
    
    // ... reste de la boucle
}
```

**Edit 1.2** : gate le stopGrid call par hasActiveGrid (ligne ~217)

```java
if (ddAction == DrawdownManager.DrawdownAction.KILL || ...) {
    // Only stop if grid is actually active (BUG-003 fix)
    if (gridTradingService.hasActiveGrid(instrument)) {
        gridTradingService.stopGrid(instrument);
        log.error("DRAWDOWN: Stopped grid for {} action={}", instrument, ddAction);
    } else {
        log.warn("DRAWDOWN: would stop {} but no active grid (phantom) — skipped", instrument);
    }
    continue;
}
```

### Patch 2 — DrawdownManager.java (1 fichier, 1 add)

**Edit 2.1** : ajouter resetKilled() + resetAll() publics

```java
public void resetKilled() {
    this.killed = false;
    this.pauseUntil = null;
    log.warn("DRAWDOWN: killed state RESET manually (peak map preserved)");
}

public void resetAll() {
    this.killed = false;
    this.pauseUntil = null;
    this.peakEquityMap.clear();
    log.warn("DRAWDOWN: full reset (killed + peakMap cleared)");
}
```

### Patch 3 — DrawdownController.java (nouveau, 1 fichier)

```java
@RestController
@RequestMapping("/api/drawdown")
public class DrawdownController {
    private final DrawdownManager drawdownManager;
    
    @GetMapping("/status")
    public Map<String, Object> status() {
        return Map.of(
            "killed", drawdownManager.isKilled(),
            "initialCapital", drawdownManager.getInitialCapital(),
            "peakEquityMap", drawdownManager.getPeakEquityMap(),
            "threshold", drawdownManager.getInitialCapital() * 0.85
        );
    }
    
    @PostMapping("/reset")
    public Map<String, Object> reset() {
        drawdownManager.resetAll();
        return Map.of("ok", true, "msg", "DrawdownManager fully reset");
    }
    
    @PostMapping("/initialCapital")
    public Map<String, Object> setInitialCapital(@RequestBody Map<String, Double> body) {
        double v = body.get("value");
        drawdownManager.setInitialCapital(v);
        return Map.of("ok", true, "newValue", v);
    }
}
```

---

## 5. Fix temporaire en attendant le patch (cycle 147 Tony action)

Sans toucher au code, Tony peut désamorcer le trap BUG-004 en éditant strategy.json :

```bash
ssh ubuntu@martin-vm
# backup
cp /home/ubuntu/martin/config/strategy.json /home/ubuntu/martin/config/strategy.json.bak-cycle147
# edit initialCapital 134 → 110 (or current portfolio)
sed -i 's/"initialCapital": 134/"initialCapital": 110/' /home/ubuntu/martin/config/strategy.json
# verify
grep initialCapital /home/ubuntu/martin/config/strategy.json
# no restart needed — strategy.json reloaded on next AutoGrid poll (15min)
```

Nouveau threshold : 110 × 0.85 = $93.50. Portfolio $113.23 >> $93.50 → DD = 0% → KILL won't fire au prochain redeploy.

**Mais ce fix temporaire n'enlève pas BUG-003** : si un redeploy tourne mal et DD réel atteint 15%, le zombie loop re-fire jusqu'au prochain restart. Patch code reste nécessaire à terme.

---

## 6. Test cases (3 scénarios)

### Scénario 1 — BUG-003 fix : phantom stopGrid skip
1. setup : 1 grid actif, killed=false
2. action : trigger KILL via DD = 20%
3. observable : 1 stopGrid + killed=true, puis loop scheduler 15min
4. expected post-patch : 1 stopGrid (action), puis 0 stopGrid (skipped via isKilled+hasActiveGrid)
5. before patch : N stopGrid log lines (cycle 147 : 3 visibles en 4h)

### Scénario 2 — BUG-004 fix : initialCapital update via API
1. setup : portfolio = $90, initialCapital=100, killed=false
2. action : curl POST /api/drawdown/initialCapital {value: 95}
3. observable : threshold = 95 × 0.85 = $80.75 < portfolio $90 → won't fire
4. before patch : impossible (pas d'endpoint), seul recourse = edit strategy.json + restart

### Scénario 3 — combined fix : reset + redeploy
1. setup : killed=true, peakMap={ETH: 20}, all grids disabled
2. action : curl POST /api/drawdown/reset puis re-enable PF_LINKUSD dans strategy.json
3. observable : LINK grid spawn sans KILL, killed=false, peakMap rebuild from scratch
4. before patch : LINK grid spawn → KILL fire (killed=true encore), AutoGrid stopGrid phantom

---

## 7. Estimation effort

- Patch 1 (AutoGridScheduler) : 2 edits = 15 min
- Patch 2 (DrawdownManager) : 1 add = 10 min
- Patch 3 (DrawdownController) : 1 nouveau fichier = 20 min
- Build local (mvn package -DskipTests) : ~30 sec
- Tests unitaires (optionnel mais recommandé) : 3 cases × 15 min = 45 min
- Deploy via scp + restart : 5 min
- **Total** : ~1h30 si tests inclus, ~50 min sans tests

Approche recommandée : implémenter Patches 1+2 d'abord (le minimum viable), tester en deploy avec une seule pair, puis ajouter Patch 3 si l'expérience opérationnelle confirme le besoin de l'endpoint.

---

## 8. Risques

| Risque | Probabilité | Mitigation |
|---|---|---|
| Patch 1 edit 1.1 saute trop tôt si killed transitoire | LOW | log.debug pour traçabilité + le reset endpoint Patch 3 permet de débloquer |
| Patch 2 resetAll() perd peakMap → reset DD historique | MEDIUM | resetKilled() préserve peakMap, à utiliser par défaut |
| Endpoint reset accessible sans auth | LOW | localhost only par bind-localhost.conf déjà en place |
| Conflit avec deploy-strategy.py probe ANSI red | LOW | post-start.sh probe est read-only, pas de mutation |

---

## 9. Lien avec autres findings

- **Cycle 144 BUG-002 patch** : ferme la position après KILL. Indépendant de ce patch mais complémentaire — sans BUG-002 fix, position reste nue. Sans BUG-003+004 fix, KILL re-fire en boucle. Les deux doivent partir ensemble.
- **Cycle 53 BtcRegimeKillSwitch** : déjà utilise `closeGridAndPositions()` (le bon chemin). Cohérence à restaurer entre les 4 killswitches.
- **Pensée 0608 "le succès creuse le bug"** : extension naturelle — "le baseline figé creuse l'impossibilité de récupérer". Le killSystem qui ne sait pas qu'il a déjà tiré (BUG-003) + le baseline qui ne sait pas que Tony a accepté la perte (BUG-004) = même pattern d'amnésie inter-classe.
- **Fragment 043 "le bug qui se nourrit de la défense"** : narrative companion. Le mécanisme défensif (DrawdownManager) devient le mécanisme qui appelle la prochaine cible — explique exactement pourquoi 11 fires en 4h.

---

## 10. Décision attendue Tony

1. **APPROVE Patches 1+2** : je build + scp + restart (~50 min)
2. **APPROVE Patches 1+2+3** : full stack (~1h30)
3. **APPROVE fix temporaire seul** : Tony edit strategy.json initialCapital (~2 min)
4. **HOLD** : laisser dormir, monitorer
5. **REJECT** : autre approche

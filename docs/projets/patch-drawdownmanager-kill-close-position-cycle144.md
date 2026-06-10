# Patch BUG-002 — DrawdownManager KILL doit fermer la position

**Cycle** : 144 (2026-06-11 00h23 Paris)
**Statut** : design doc, **NON déployé** — attend review Tony
**Sévérité** : HIGH (position nue 15min+ à chaque fire, observée 2× en 45min le 0610)
**Référence** : BUG-002 découvert cycle 143 (vacation-autonomy.md offset 14380)

---

## 1. Le bug en 3 lignes

`DrawdownManager.KILL` → `gridTradingService.stopGrid(instrument)` → cancelle ordres + cancel SL → **position laissée intacte sur Kraken sans aucun filet**.

Pattern observé 2026-06-10 ETH : KILL 15:25 UTC + KILL 16:10 UTC. Position SHORT 0.07 puis 0.06 nue jusqu'au re-spawn AutoGrid (~15-20min plus tard) qui re-fixe un SL.

Sévérité contextuelle : si pendant la fenêtre nue le marché bouge >5% adverse → perte sans filet (potentielle wipe de la grid entière).

---

## 2. Évidence empirique (cycle 143)

Timeline `app.log` ETH 2026-06-10 15:00→16:15 UTC :

```
15:10:56 Grid ETH SHORT spawn 12 levels, SL placed $1687.4 size=0.25
15:19:43 fills filling up
15:25:47 DrawdownManager KILL → grid stop + SL cancelled, position 0.07 NUE
15:40:47 AutoGrid re-open grid ETH SHORT → 12 levels, SL placed $1695.8 size=0.32
15:42:22 fill level 6
15:45:59 HARD STOP triggered (krakenTotalPnl=-$2.18 > maxLoss=$2.00) → closed position (clean)
15:55:47 AutoGrid re-open grid ETH SHORT, SL placed $1706.3 size=0.06
15:55:53 6 fills immédiats
16:10:47 DrawdownManager KILL ENCORE → SL cancelled, position 0.06 NUE
```

3 cycles KILL/HARD STOP/KILL en 1h. **Le HARD STOP chemin (15:45) ferme propre. Le KILL chemin (15:25 et 16:10) laisse nue.**

---

## 3. Lecture du code (3 fichiers, 4 méthodes)

### A. AutoGridScheduler.java:217-223 — le call site qui bug

```java
if (ddAction == DrawdownManager.DrawdownAction.KILL
        || ddAction == DrawdownManager.DrawdownAction.PAUSE_WEEK
        || ddAction == DrawdownManager.DrawdownAction.PAUSE_48H) {
    gridTradingService.stopGrid(instrument);   // ← BUG : ne ferme pas la position
    log.error("DRAWDOWN: Stopped grid for {} action={}", instrument, ddAction);
    continue;
}
```

### B. GridTradingService.stopGrid() (`:292-326`) — le chemin buggué

```java
public void stopGrid(String instrument) {
    GridState state = activeGrids.remove(instrument);
    if (state == null) return;
    state.setActive(false);
    // cancel toutes les limites placées
    // cancel le SL on-exchange via stopLossManager
    // mark inactive in DB
    // → NE TOUCHE PAS LA POSITION OUVERTE
}
```

### C. GridTradingService.closeGridAndPositions() (`:337-353`) — le chemin propre déjà existant

```java
/**
 * PATCH 2026-05-17 (cycle 53): public wrapper for BtcRegimeKillSwitch.
 * Exposes the existing private closePositionAndStopGrid as instrument-keyed call so a
 * regime-break kill closes the position via reduceOnly mkt instead of leaving it naked.
 * Root cause cycle 51+53 LINK/ETH/BTC orphan incidents: killswitch called stopGrid()
 * which only cancels limit orders + SL, never the residual position.
 */
public boolean closeGridAndPositions(String instrument) {
    GridState state = activeGrids.get(instrument);
    if (state == null) {
        log.warn("closeGridAndPositions: no state for {}, skipping", instrument);
        return false;
    }
    closePositionAndStopGrid(state);
    return true;
}
```

### D. GridTradingService.hardStopCheck() (`:870-905`) — modèle de référence (fermeture position)

Comportement attendu : `getOpenPositions` → si position non nulle → `mkt reduceOnly close` → vérif sendStatus → log ok ou orphan.

Cette logique existe déjà dans `closePositionAndStopGrid` (privé, appelé par `closeGridAndPositions`).

---

## 4. Symétrie historique : cycle 53 a déjà fixé exactement ce pattern

Le commentaire `:341-342` est explicite : **"Root cause cycle 51+53 LINK/ETH/BTC orphan incidents: killswitch called stopGrid() which only cancels limit orders + SL, never the residual position."**

C'est **exactement** le même bug, juste pour un autre déclencheur. Cycle 53 a patché le chemin BtcRegimeKillSwitch en l'aiguillant vers `closeGridAndPositions`. **Cycle 144 doit faire la même chose pour le chemin DrawdownManager KILL.**

Conséquence : un fix d'**une ligne** (plus un import implicite si besoin) ferme un bug structurel observé en prod 2026-06-10.

---

## 5. Le patch proposé

### Fichier unique : `src/main/java/com/martin/signal/AutoGridScheduler.java`

### Diff conceptuel (lignes 217-223)

```diff
 if (ddAction == DrawdownManager.DrawdownAction.KILL
         || ddAction == DrawdownManager.DrawdownAction.PAUSE_WEEK
         || ddAction == DrawdownManager.DrawdownAction.PAUSE_48H) {
-    gridTradingService.stopGrid(instrument);
-    log.error("DRAWDOWN: Stopped grid for {} action={}", instrument, ddAction);
+    // PATCH cycle 144 (BUG-002): KILL/PAUSE close la position via mkt reduceOnly,
+    // pas juste cancel des orders. stopGrid() ne ferme pas la position → laissait
+    // une SHORT/LONG nue jusqu'au re-spawn AutoGrid (~15min). Cycle 53 a déjà
+    // patché ce pattern pour BtcRegimeKillSwitch → on réutilise la même méthode.
+    boolean closed = gridTradingService.closeGridAndPositions(instrument);
+    log.error("DRAWDOWN: Closed grid+position for {} action={} closeResult={}",
+            instrument, ddAction, closed);
     continue;
 }
```

### Pourquoi ce patch et pas un autre

- **Minimal** : 1 ligne effective de logique, le reste est commentaire/log enrichi.
- **Réutilise du code éprouvé** : `closeGridAndPositions` est en prod depuis cycle 53 (2026-05-17, soit 25 jours), validée par BtcRegimeKillSwitch v2 cycle 142 (2026-06-10 05h11 UTC, kill clean 0 orpheline).
- **Symétrique** : aligne le chemin DrawdownManager KILL sur le chemin BtcRegimeKillSwitch — **les deux killswitches fonctionnent désormais identiquement**.
- **Pas de régression possible sur REDUCE** : on garde `stopGrid` pour le branche REDUCE (`:230`) qui re-start tout de suite avec 2 levels — pas de fenêtre nue car le restart re-pose un SL en <1s.

---

## 6. Tests recommandés (avant déploiement)

### Test unitaire (à ajouter dans `AutoGridSchedulerTest.java` si présent)

```
GIVEN AutoGridScheduler + mock GridTradingService + mock DrawdownManager
WHEN  DrawdownManager.checkDrawdown returns KILL
THEN  gridTradingService.closeGridAndPositions(instrument) is called (verify),
      gridTradingService.stopGrid(instrument) is NOT called (verify never)
```

### Test d'intégration (manuel après deploy)

1. Force un drawdown sur 1 grid (en démo) : ouvrir une grid, déplacer artificiellement le peak via setPeakEquity, vérifier KILL.
2. Observer logs : "DRAWDOWN: Closed grid+position for X action=KILL closeResult=true"
3. Vérifier sur Kraken : 0 position, 0 ordre sur l'instrument.

### Test de non-régression

- Lancer la grid sur instrument, attendre un KILL réel (ou simuler), vérifier 0 position résiduelle.
- Comparer avec BtcRegimeKillSwitch cycle 142 (qui a déjà ce comportement) — même log pattern attendu.

---

## 7. Procédure de déploiement (référence cycle 137-140)

1. **NE PAS rebuild sur la VM** (source = décompilé périmé, finding cycle 137 `project_martin_vm_source_decompiled.md`).
2. Build local : `mvn package -DskipTests` dans `/home/tony/projets/tonyderide/martin/`.
3. `scp target/martin-*.jar ubuntu@141.253.108.141:/home/ubuntu/martin/martin.jar.new`
4. SSH VM : `cp martin.jar martin.jar.backup.$(date +%Y%m%d) && mv martin.jar.new martin.jar`
5. `systemctl --user restart martin` ou équivalent.
6. Vérifier uptime + AutoGrid re-deploy attendu (cycle 137 finding : pairs `enabled=true` se relancent au boot).
7. Si KILL se déclenche en prod après deploy → vérifier log "DRAWDOWN: Closed grid+position" + `/api/bot/positions` = empty.

---

## 8. Risques résiduels (ce que le patch NE résout PAS)

1. **DrawdownManager peut re-KILL après re-open AutoGrid** : si RegimeGate reste OPEN et que la grid re-fill puis re-DD, on aura un autre KILL. Le patch ferme proprement à chaque KILL mais ne casse pas la boucle KILL→re-open→KILL. **Solution complémentaire** : ajouter un cooldown dans AutoGridScheduler après KILL (déjà partiellement géré via `pauseUntil` dans DrawdownManager pour PAUSE_*, mais KILL fait `killed=true` global → bloque, en théorie). Vérifier que `killed=true` empêche bien AutoGrid de re-déployer cette pair.

   - **Question ouverte** : pourquoi cycle 143 a vu 3 cycles KILL en 1h si `killed=true` est global ? Peut-être que `killed=true` n'a pas été set (bug séparé) OU que `resetKill()` est appelé entre les cycles. À investiguer.

2. **Position nue brève (< quelques sec) acceptable** : entre cancel des orders et `closePositionAndStopGrid`, il y a une fenêtre théorique. Le code de `closePositionAndStopGrid` (cycle 53) ferme cette fenêtre en faisant le close AVANT le cancel SL. Vérifier l'ordre des opérations en lisant `closePositionAndStopGrid` complet.

3. **REDUCE chemin pas touché** : OK actuellement (restart immédiat avec 2 levels), mais si jamais REDUCE est upgradé pour ne pas re-démarrer → revisiter.

---

## 9. Pourquoi ce patch maintenant et pas plus tard

- BUG-002 a déclenché 2× en 45min le 0610. **Fréquence non triviale**.
- Le fix est trivial (1 ligne), low-risk (méthode déjà éprouvée), high-impact (ferme un risque structurel).
- Tony a redéployé 3 grids SHORT match-trend après le KILL chain — la classe de risque est active **en ce moment**.
- Patch alignable sur le pattern cycle 53 (1 mois d'historique de stabilité de la méthode `closeGridAndPositions`).

---

## 10. Décision attendue de Tony

- [ ] **APPROVE patch as-is** → je build + scp + restart (procédure cycle 137-140) et envoie Telegram confirmation.
- [ ] **APPROVE patch with tweaks** → préciser quels.
- [ ] **HOLD** → je n'agis pas, on attend explication (peut-être que Tony a vu un risque que je n'ai pas).
- [ ] **REJECT** → expliquer pourquoi, j'archive ce design doc.

---

## 11. Annexe — pourquoi je n'agis pas sans review

Frontière vacance respectée :
- 0 modif Martin/VM (4 SSH read-only ce cycle).
- 0 commit code dans martin/ ou push (ce design doc est dans niam-bay/).
- Telegram cycle 143 a alerté Tony du bug, ce design doc cycle 144 propose la solution.
- Patch d'1 ligne avec méthode existante = low-risk **mais** déploiement = action irréversible non-réversible → review Tony obligatoire (règle Tony 2026-06-03 "bloqué/en attente = demander à l'agence").

---

## 12. Annexe — symétrie temporelle des killswitches Martin

| Killswitch | Trigger | Méthode appelée | Ferme position ? | Statut |
|---|---|---|---|---|
| BtcRegimeKillSwitch v2 (cycle 53+142) | BTC < EMA200 sur 4h consecutive | `closeGridAndPositions` | ✅ oui | OK |
| HARD STOP (`hardStopCheck`) | krakenTotalPnl <= -maxLoss | inline `mkt reduceOnly` | ✅ oui | OK |
| DrawdownManager KILL (cycle 144 candidate) | peak DD >= 10% | `stopGrid` (BUG) → `closeGridAndPositions` (FIX) | ❌ non → ✅ oui | **À PATCHER** |
| DrawdownManager PAUSE_48H / WEEK | peak DD >= 5/8% | `stopGrid` (BUG) → `closeGridAndPositions` (FIX) | ❌ non → ✅ oui | **À PATCHER** |
| DrawdownManager REDUCE | peak DD >= 3% | `stopGrid` puis `startGrid 2 levels` | partiel (restart immédiat re-fill) | OK (hors scope) |

Post-patch, **les 4 chemins de kill terminaux ferment proprement**. Cohérence restaurée.

---

*Design doc cycle 144, ~180 lignes. Frontière vacance respectée : 0 modif Martin/VM.*

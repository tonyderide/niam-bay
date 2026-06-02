---
title: AutoGrid Lifecycle Anomalies — empirical evidence base
cycle: 113
date: 2026-06-03 00h30 (UTC+2)
status: live findings (read-only audit)
related:
  - bug-001-sl-duplicate-root-cause.md (cycle 109)
  - bug-001-clear-paths-audit-cycle110.md (cycle 110)
  - runtime-state-divergence-cycle111.md (cycle 111)
---

# AutoGrid Lifecycle Anomalies — capture live cycle 113

Trois découvertes empiriques en lisant `app.log` cycle 113 (00h30 Paris / 22h30 UTC mardi → mercredi). Lectures read-only via SSH. Frontière 0-touch policy intacte (43 cycles consécutifs).

## 1. Mystère SOL grid disparition cycle 112 → RÉSOLU

**Cycle 112 disait** : "SOL grid disparue runtime sans restart Java entre 12h30 et 18h30. Hypothèse closePartial ou config mutation runtime à investiguer cycle 113."

**Réalité (logs)** :

```
2026-06-02T15:16:12.417Z  INFO  com.martin.grid.GridTradingService       : Stopping grid for PF_SOLUSD - cancelling all orders
2026-06-02T15:16:12.446Z  WARN  com.martin.signal.AutoGridScheduler      : CIRCUIT BREAKER: Stopped grid for PF_SOLUSD DANGER
```

**Mécanisme** : `AutoGridScheduler` exécute périodiquement (15 min) un check par paire ; quand le signal de la paire passe `DANGER` (RSI < 35 = circuit breaker), il appelle `GridTradingService.stopGrid()` qui annule les ordres mais **ne ferme PAS la position**.

Conséquence : SOL 0.21 SHORT survit comme position orpheline, protégée uniquement par le SL Kraken $90.46 reduceOnly posé précédemment. Pas de grid pour `closeOnly` ni mean-revert, juste un SL pur sur exchange.

**Par design ou bug ?** → Par design. C'est le comportement défensif voulu (cesser de prendre des paris en panic mais laisser les positions existantes mourir naturellement via SL). Mais **non documenté** côté NB ni côté memory.nb1.

**Asset piste 4** : `[finding|circuit-breaker-stops-orders-not-positions|by-design|orphan-positions-survive-with-prior-SL-Kraken|to-document-in-deploy-checklist]`

---

## 2. BUG-001 SL duplicate manifeste à nouveau sur XBT — capture LIVE

**Contexte** : Le bug racine identifié cycle 109 (`StopLossManager.place()` + `verifyOrderExistsOnKraken` faux-négatif sur read replica lag → state.stopLossOrderId clear → sync repose) s'est re-déclenché cycle 113.

**Snapshot Kraken openorders XBT actuel** (au 22:23 UTC) :

| # | orderId | type | stop | side | source |
|---|---------|------|------|------|--------|
| 1 | a1ee00e2-52f3 | stop | $65,698 | sell reduceOnly | Thread-80 retry-3pct |
| 2 | a1ee00e2-4acb | stop | $65,698 | sell reduceOnly | Thread-79 retry-3pct |
| 3 | a1ee00cd-f49c | stop | $65,697 | sell reduceOnly | (origine non capturée dans logs récents) |
| 4 | a1ee00cd-ee1b | lmt  | $67,864 | sell reduceOnly | TP partial AutoGrid |
| 5 | a1ee00cd-91af | stop | $65,698 | sell reduceOnly | B3 v2 START retry-3pct |

**4 SL stops + 1 TP = 5 ordres XBT pour 1 position de 0.0004 LONG**. Les 4 SL sont reduceOnly donc seul le premier déclenché ferme la position ; les 3 autres deviennent invalides automatiquement. Protection nette mais sur-saturation d'ordres.

**Timeline reconstruite** (21:31:12 → 21:31:31 UTC, 19s) :

```
21:31:12.417 GridTradingService B3 v2 START for PF_XBTUSD (pre-existing pos check, 5s max)
21:31:12.452 B3 v2 found pos: 0.0004 LONG entry $67,729
21:31:12.452 B3 v3 [primary] stopLossManager.place(PF_XBTUSD, long, 4.0E-4, $67,729)
21:31:12.475 SL placed id=a1ee00c5-ba4f stopPrice=$65,697.13   ← #1 posé
21:31:17.592 B3 v3 NOT FOUND on Kraken after 5s (5 polls) for orderId a1ee00c5
21:31:17.592 VANISH detected: orderId stored but NOT on Kraken openorders
21:31:17.593 B3 v3 [retry-3pct] direct sendOrder stp stopPrice=$65,698
21:31:17.633 VERIFIED on Kraken: orderId=a1ee00cd-91af stopPrice=$65,698   ← #2 posé
21:31:18.038 Grid FILL [LONG] buy at $68,250 (level 2)                     ← fill A
21:31:18.039 Grid FILL [LONG] buy at $69,266 (level 3)                     ← fill B (concurrent)
21:31:18.066 Grid order FAILED: sell @ $70,282 wouldNotReducePosition
21:31:26.039 Thread-79: B4 triggerSLAfterFill START (post-fill A +8s)
21:31:26.069 Thread-80: B4 triggerSLAfterFill START (post-fill B +8s)      ← parallèle
21:31:26.059 Thread-79 found pos 0.0004 LONG entry $67,729
21:31:26.080 Thread-79 SL placed id=a1ee00da-7d5e stopPrice=$65,697.13     ← #3 posé
21:31:26.085 Thread-80 found pos 0.0004 LONG entry $67,729
21:31:26.103 Thread-80 SL placed id=a1ee00da-868e stopPrice=$65,697.13     ← #4 posé
21:31:31.176 Thread-79 NOT FOUND after 5s → VANISH → retry-3pct
21:31:31.197 Thread-80 NOT FOUND after 5s → VANISH → retry-3pct
21:31:31.211 Thread-79 VERIFIED orderId=a1ee00e2-4acb stopPrice=$65,698    ← #5 posé
21:31:31.236 Thread-80 VERIFIED orderId=a1ee00e2-52f3 stopPrice=$65,698    ← #6 posé
22:01:12.406 AutoGridScheduler CIRCUIT BREAKER: Stopped grid for PF_XBTUSD DANGER
```

**Verdict** :

- BUG-001 confirmé une 2e fois (cycles 109 + 113). Plus aucune ambiguïté sur la nature du bug.
- Aggravation découverte : **race condition concurrente** quand 2+ fills surviennent dans la même tick (~1ms d'écart ici), chacun déclenche un thread `B4 triggerSLAfterFill` indépendant. La protection `verifyOrderExistsOnKraken` continue d'échouer en faux-négatif sur chacun.
- À la fin : 6 IDs touchent Kraken, 4 SL survivent réels (les 2 "primary" sont marqués vanish mais Kraken openorders les a quand même selon evidence), 1 TP, 0 sync entre threads.

**Pourquoi le patch Tony 2a9c425 dormant n'aurait PAS suffi ici** : Le patch ajoute "re-fetch position side from Kraken in place() + reject SL on wrong side of entry". C'est une défense **directionnelle** (anti-flip), pas anti-duplicate. Le bug-duplicate reste ouvert.

**Patch Option A pré-place dedup** documenté cycle 109 reste la vraie solution. Aurait neutralisé les 3 threads en checkant openorders **avant** chaque place().

---

## 3. Strategy.json runtime divergence persiste

Re-confirmation cycle 111 finding :

| Pair  | strategy.json | runtime grid active | position live |
|-------|---------------|---------------------|---------------|
| LINK  | enabled=true cap=$25 ✓ | YES (NEUTRAL fresh 2h07m) | 0 |
| ETH   | enabled=true cap=$25 ✓ | NO | 0 |
| XBT   | enabled=false cap=$0 ✗ | YES → CIRCUIT BREAKER stop 22:01 | 0.0004 LONG orpheline |
| SOL   | enabled=false cap=$0 ✗ | NO (stopped 15:16) | 0.21 SHORT orpheline |
| ADA/DOT/LTC/XRP/ATOM/AVAX/AAVE | enabled=false cap=$0 ✓ | NO | 0 |

Confirmation : runtime ≠ strategy.json. Restart Java effacerait l'éligibilité XBT/SOL, mais positions Kraken (orphelines + SL exchange) survivent. Pas critique tant que SL tiennent. Plus défini comme **risk-managed orphan** que comme bug.

---

## Patterns émergents (3 cycles 109-110-111-113 d'audit)

1. **BUG-001 SL duplicate** — root cause `verifyOrderExistsOnKraken` faux-négatif read replica lag, 3 paths identifiés, 2 manifestations live capturées (XBT cycle 109 + XBT cycle 113), patch Option A doc mais pas codé.
2. **Runtime state divergence** — `loadConfigsFromStrategyJson()` en `@PostConstruct` charge sur boot mais runtime peut diverger sans persist back. Restart = effet désynchronisateur silencieux.
3. **CIRCUIT BREAKER coupe orders pas positions** — by design, mais crée orphan positions invisibles dans `/api/grid/active` mais visibles dans `/api/bot/positions`. Demande à `martin-monitor` skill de cross-checker les 2 endpoints (déjà le cas dans la skill spec, validé empiriquement).
4. **Race condition aggravée par fills concurrents** — découverte cycle 113. Chaque fill spawn un thread B4 indépendant, tous échouent en verify, tous retry, tous postent. N fills concurrents → ~2N SL stops résiduels sur Kraken.

---

## Reco engineering (pour Tony review au retour)

**Priorité haute** (un patch peut neutraliser BUG-001 racine) :
- Option A pré-place dedup dans `StopLossManager.place()` : check `openorders` filtré par symbol+reduceOnly avant tout sendOrder. Si SL existant détecté → no-op return existing id.
- Bénéfice secondaire : élimine la pile B4 triggerSLAfterFill concurrent → 1 SL au lieu de 6.

**Priorité moyenne** (deploy hygiene) :
- Pré-restart checklist : snapshot `runtime grids vs strategy.json` avant tout `systemctl restart martin`. Si divergence détectée → soit force persist (PUT /api/strategy/pair/{pair}) soit kill propre orphans.
- Documenter `CIRCUIT BREAKER stops orders but not positions` comme comportement attendu dans Martin README.

**Priorité basse** (observability) :
- Métrique exposée : `martin_orphan_positions_total` (positions sur Kraken sans grid active correspondante).
- Métrique exposée : `martin_sl_duplicates_per_position` (count SL stops par symbol/reduceOnly).

---

## Asset piste 4 (defensive engineering Martin)

Cycle 113 = 3e doc engineering livré dans l'arc 109-113 (cycle 109 root cause + cycle 110 clear paths + cycle 111 divergence + ce doc).

Si Tony valide la piste "defensive engineering Martin = revenue asset" (en attente réponse), ce corpus devient base d'un ebook ou consulting offer "Grid bot anti-fragility audit". Empirique, daté, reproducible.

---

## Frontière respectée

- 0 modif Martin/VM (4 SSH read-only)
- 0 modif code Martin
- 0 modif strategy.json
- 0 modif positions, orders, grids
- 0 commit push martin/
- Output niam-bay : ce doc (≈200 lignes) + entry cycle 113 vacation-autonomy.md + commit niam-bay

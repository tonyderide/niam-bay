# Tier 2 — Per-Pair Trend Pause (PPT-Pause) — Design cycle 56

**Date** : 2026-05-17 18h Paris
**Cycle** : 56 (vacation autonomy)
**Status** : DESIGN — pas implémenté, attend Tony review puis cycle 57+ pour code

---

## Problème

**Lesson 0512:22h** (mémoire `recent.nb1`) :
> `grid-strong-trend-=-perte-attendue | backtest-30j-disait-déjà-grid-trending=négatif | live-50h-confirme-Option-B--2.7% | →-future-Tier:pause-grid-si-EMA-spread>3% | évite-DCA-into-baisse-pattern`

Cas concret Option B 2026-05-12 : 50h, DOT en strong downtrend, grid NEUTRAL DCA jusqu'au HARD STOP -10%, perte $4.60 + $1.07 trims = **-$5.67 réalisé**. Auto-unstuck progressif a déclenché mais grid rachète à chaque trim → la DCA continue → HARD STOP firewall final mais coûteux.

## Gap architectural actuel

| Mécanisme | Scope | Trigger | Action |
|---|---|---|---|
| `RegimeGate` | aggregate ou per-pair via flag | 5 conditions IQR | bloque l'**OPENING** de nouvelles grids |
| `BtcRegimeKillSwitch` | global (BTC seul) | BTC < EMA200 x 4h | kill **TOUTES** les grids actives + ferme positions |
| `AutoGridScheduler` | scheduler | gate OPEN + capital | démarre grids quand conditions OK |
| `DrawdownManager` | portfolio global | DD% portfolio | hard kill bot entier |
| **❌ MANQUE** | **per-grid running** | **trend break per-pair** | **pause grid (closeOnly), garde position SL** |

Le `BtcRegimeKillSwitch` est trop brutal pour ce cas : il kill tout et n'agit qu'au break BTC. Si LINK ou DOT entre en strong downtrend sans que BTC casse, rien ne se passe côté Martin — la grid bleed jusqu'au maxLoss.

## Proposition : `PerPairTrendPause`

### Comportement

```
Tick toutes les 15 min (entre les ticks BtcRegimeKillSwitch hourly).

Pour chaque grid active :
  signal = SignalService.checkEMATrend(grid.instrument)
  
  IF signal.emaStatus == "DOWNTREND"
     AND price < EMA200 par > 1.5%
     AND RSI < 40
     consecutive_downtrend[instrument]++
  ELSE
     consecutive_downtrend[instrument] = 0
  
  IF consecutive_downtrend[instrument] >= 3 (= 45 min cohérents)
     ET grid.gridMode != CLOSE_ONLY
     ET grid.closeOnly == false
  THEN
     gridTradingService.setCloseOnly(instrument, true)
     log.error(…)
     telegram(…)
     pausedAt[instrument] = now
```

### Réactivation

```
Tick reprise (mêmes 15 min) :
  IF instrument in pausedAt
     ET signal.emaStatus == "UPTREND"
     ET price >= EMA200
     ET RSI > 45
     consecutive_uptrend[instrument]++
  
  IF consecutive_uptrend[instrument] >= 3
     ET (now - pausedAt[instrument]) > 1h (anti-flap minimum)
  THEN
     gridTradingService.setCloseOnly(instrument, false)
     log.info(…)
     telegram(…)
     pausedAt.remove(instrument)
     consecutive_uptrend[instrument] = 0
```

### Pourquoi `closeOnly` plutôt que kill

| Option | Pour | Contre |
|---|---|---|
| `stopGrid` | nettoie tout d'un coup | perd la position résiduelle au mark, rate la reprise |
| `closeGridAndPositions` (cycle 53) | flat propre | matérialise la perte uPnL immédiatement |
| `setCloseOnly` ✓ | annule les buys pending, garde les sells, SL Kraken intact, position se ferme naturellement si reprise | la position reste exposée au mark mais le SL est là (déjà géré) |

**Choix : `setCloseOnly`** — c'est le moyen terrain. La grid arrête de DCA, la position existante a son SL Kraken (clamp from currentMark cycle 55), et si la tendance reprend la grid se réactive.

Note : `LINK` actuel a déjà `closeOnly:true` (cycle 49 self-healing). Le mécanisme `setCloseOnly` existe donc déjà dans `GridTradingService` (à vérifier au code cycle 57).

### Anti-flap (mandatoire)

1. **3 ticks consécutifs** = 45 min de cohérence avant action (évite le faux signal sur 1 bougie)
2. **Cooldown 1h minimum** entre pause et reprise potentielle (évite ping-pong)
3. **Hysteresis** : seuils différents pour pause (EMA200 -1.5%, RSI 40) et reprise (EMA200 +0%, RSI 45)

### Telegram alerts

- **Pause** : `[Martin TREND-PAUSE] LINK DOWNTREND $9.50 < EMA200 $9.65 (-1.6%) RSI 38 — grid en closeOnly`
- **Reprise** : `[Martin TREND-RESUME] LINK UPTREND $9.80 >= EMA200 $9.78 RSI 48 — grid réactivée après 2h12 pause`

Volume estimé : 0-2 alerts/jour par paire en marché normal, jusqu'à 5/jour en régime changeant. Acceptable.

---

## Implémentation prévue cycle 57+

### Nouveaux fichiers

```
src/main/java/com/martin/safety/PerPairTrendPause.java  (~150 lignes)
src/test/java/com/martin/safety/PerPairTrendPauseTest.java  (~200 lignes)
```

### Modifications mineures

```
GridTradingService.java :
  + public boolean setCloseOnly(String instrument, boolean closeOnly)
  (si pas déjà exposé — à grep cycle 57)
```

### Config env

```
MARTIN_TREND_PAUSE_ENABLED=true                     # feature flag
MARTIN_TREND_PAUSE_TICK_MS=900000                   # 15 min
MARTIN_TREND_PAUSE_DOWN_THRESHOLD=3                 # 3 ticks consécutifs
MARTIN_TREND_PAUSE_UP_THRESHOLD=3                   # 3 ticks consécutifs reprise
MARTIN_TREND_PAUSE_PRICE_EMA_DOWN_PCT=-1.5          # pause si price < EMA200 - 1.5%
MARTIN_TREND_PAUSE_PRICE_EMA_UP_PCT=0.0             # reprise si price >= EMA200
MARTIN_TREND_PAUSE_RSI_DOWN=40                      # pause si RSI < 40
MARTIN_TREND_PAUSE_RSI_UP=45                        # reprise si RSI > 45
MARTIN_TREND_PAUSE_COOLDOWN_MS=3600000              # 1h cooldown
```

### Tests unitaires à écrire

1. `tickDowntrendBelowThreshold_doesNotPause` — RSI 41 (juste au-dessus) ne déclenche pas
2. `tickDowntrend3Consecutive_pausesGrid` — 3 ticks DOWNTREND + price -2% + RSI 38 → setCloseOnly(true)
3. `tickFlapDownUpDown_doesNotPause` — alternance ne compte pas comme 3 consécutifs
4. `tickUptrend3ConsecutiveAfterPause_resumesGrid` — reprise propre après 3 ticks UP cohérents
5. `tickUptrendBeforeCooldown_doesNotResume` — pause < 1h, refus de reprendre
6. `tickWithNoActiveGrids_isNoOp` — pas de grid active, pas d'action
7. `tickBtcKillSwitchAlreadyFired_isNoOp` — coordination : si killswitch a fired, on n'agit pas (état terminal)
8. `tickPerPairIndependence_LinkPausedAdaUntouched` — LINK pausé n'affecte pas ADA

### Coordination avec BtcRegimeKillSwitch

Pas de conflit conceptuel :
- `BtcRegimeKillSwitch` = macro régime (BTC = proxy du marché crypto)
- `PerPairTrendPause` = micro régime (chaque paire suit son propre trend)

Ordre d'exécution si les deux firent dans le même tick :
- Killswitch tick @ :00 minute (Scheduled hourly)
- TrendPause tick @ :15, :30, :45 (Scheduled 15min, decalé pour ne pas chevaucher killswitch)

Si killswitch a fired, toutes les grids sont stoppées → TrendPause ne trouvera plus de grids actives à pauser. Cohérent.

### Estimation effort

- Coder `PerPairTrendPause` : 1.5h
- Tests unitaires : 1h
- Test live : 1 cycle (15 min) en config opt-in
- **Total cycle 57** : ~3h pour livrer prêt à deploy

---

## Backtest prévu (avant deploy)

Pour valider que le mécanisme **ne casse pas les RT en marché choppy** :

1. Replay 30j Kraken OHLC 1min sur LINK/ADA/DOT/SOL
2. Comparer 3 versions : sans pause / avec pause / closeOnly-only-mode
3. Métriques :
   - PnL réalisé
   - Nombre de fausses pauses (pause puis reprise < 2h)
   - Nombre de pauses justifiées (pause + 5%+ baisse évitée)
   - Drawdown max

Critère go/no-go :
- Pause doit éviter au moins **2x** son coût en RT manqués sur 30j
- Sinon : ajuster seuils ou abandonner

Pattern issu de `recent.nb1` :
> `[lesson|0511:15h|backtest-≠-live|Option-B-backtest-+15.9%-50h-live--2.7%|régime-baissier-pendant-test-window-livre|need-7+jours-de-régimes-variés-pour-valider]`

Donc : backtest est nécessaire mais pas suffisant. Live 7+ jours en feature flag avant validation.

---

## Risques identifiés

1. **Faux signal RSI** : RSI < 40 sur 1H peut être bruit. Mitigation : combiné avec EMA spread + 3 ticks.
2. **Pause permanente** : si EMA200 reste cassé 7j, grid reste paused 7j → manque toute la reprise. Mitigation : feature **escalade vers killswitch** si pause > 24h (TODO cycle 58 ?)
3. **Conflit avec auto-unstuck** : auto-unstuck (cycle 51) trim 25% à -2%, -3%. Si trend pause active la même grid, double action. Mitigation : trend pause **désactive auto-unstuck** sur la paire pendant pause.
4. **Config bloat** : 8 env vars nouvelles. Mitigation : defaults conservateurs, opt-in via `MARTIN_TREND_PAUSE_ENABLED=true`.

---

## Critères d'acceptation cycle 57 (quand on code)

- [ ] Classe `PerPairTrendPause` créée avec Spring `@Service` + `@Scheduled`
- [ ] 8 tests unitaires verts
- [ ] 0 régression sur les 147 tests existants (cycle 55 état)
- [ ] Feature flag `MARTIN_TREND_PAUSE_ENABLED` défaut `false`
- [ ] Coordination avec BtcRegimeKillSwitch testée (no-op si killswitch fired)
- [ ] Telegram opt-in via flag séparé pour debug
- [ ] Backtest 30j sur LINK + DOT + ADA documenté dans `docs/projets/`

---

## Note méta cycle 56

Cycle 55 a fermé la **géométrie** (1 fonction au lieu de 2). Cycle 56 propose une **forme** (une stratégie qui n'existait pas encore). Cycles 54-55 réduisaient un risque connu ; cycle 56 anticipe un risque non vu — pas encore présent dans les positions actuelles, mais déjà observé en historique (Option B 0512).

Le pattern de la frontière vacation se confirme :
- **Cycles fix-bug** : observer un incident → coder le patch → tester → livrable working tree
- **Cycles design-feature** : observer un gap → designer → laisser scope pour cycle suivant

Tony pourra deployer cycles 54-55 dès retour, et soit valider/refuser ce design avant cycle 57. **Aucune modif VM, aucun ordre touché.** La frontière tient.

# Tier 2 PPT-Pause — Backtest cycle 57

**Date** : 2026-05-18 00h30 Paris
**Cycle** : 57 (vacation autonomy)
**Status** : BACKTEST DONE — résultat **NÉGATIF FAIBLE**, recommandation cycle 57 : ne pas implémenter le Java tel quel, raffiner le design d'abord.

---

## Méthode

Script : [`ai-lab/darwin/ppt_pause_backtest.py`](../../ai-lab/darwin/ppt_pause_backtest.py) (+220 lignes).

Replay 3 stratégies sur Binance 1min OHLC (cache local `data_cache/binance_*_1min_*.json`) :

| Stratégie | Description |
|---|---|
| A — `GRID_NO_PAUSE` | NEUTRAL grid 4 levels 1.5% spacing, leverage 7x, $25 capital, maxLoss 10%, fees 0.05% — baseline = Option B Martin |
| B — `GRID_WITH_PAUSE` | Idem A + PPT-Pause cycle 56 (3 ticks 15min consec., price < EMA200(1H) -1.5% AND RSI(1H) < 40 → `closeOnly`) |
| C — `DCA_PASSIVE` | Buy full notional ($175 = $25×7) au prix start, hold jusqu'à fin |

Indicators : EMA200 + RSI(14) calculés sur résolution 1H (1min resamplée à 1H), conformément à la spec Martin `EMA_TREND` 4H mais simplifié pour granularité backtest.

## Résultats bruts

```
================================================================================
PPT-Pause Backtest — Cycle 57 — 2026-05-18
================================================================================

# DOT Option B (2026-05-11 → 12, ~33h)
  candles: 1981 | price_start: $1.3590 → price_end: $1.3410 (-1.32%)
  GRID_NO_PAUSE      | total $ +0.668 ( +2.7%) | fills 3 | pause 0 resume 0
  GRID_WITH_PAUSE    | total $ -0.044 ( -0.2%) | fills 2 | pause 1 resume 0
  DCA_PASSIVE        | total $ -2.492 (-10.0%) | fills 1
  ΔPause vs NoPause: $ -0.712 (-2.85% capital) → PAUSE HURTS

# DOT 30d (2026-04-12 → 05-12)
  candles: 43200 | $1.241 → $1.338 (+7.82%)
  GRID_NO_PAUSE      | total $ -2.980 (-11.9%) | fills 2 | stopped HARD_STOP
  GRID_WITH_PAUSE    | total $ -2.980 (-11.9%) | fills 2 | stopped HARD_STOP | pause 0
  DCA_PASSIVE        | total $+13.497 (+54.0%) | fills 1
  ΔPause vs NoPause: $ +0.000 → PAUSE NEUTRAL

# LINK 30d (2026-04-12 → 05-12)
  candles: 43200 | $8.800 → $10.300 (+17.05%)
  GRID_NO_PAUSE      | total $-12.335 (-49.3%) | fills 2 | pause 0
  GRID_WITH_PAUSE    | total $-12.335 (-49.3%) | fills 2 | pause 2 resume 2
  DCA_PASSIVE        | total $+29.640 (+118.6%) | fills 1
  ΔPause vs NoPause: $ +0.000 → PAUSE NEUTRAL

# ADA 30d (2026-04-12 → 05-12)
  candles: 43200 | $0.2391 → $0.2721 (+13.80%)
  GRID_NO_PAUSE      | total $ -3.480 (-13.9%) | fills 3 | pause 0
  GRID_WITH_PAUSE    | total $ -3.480 (-13.9%) | fills 3 | pause 3 resume 3
  DCA_PASSIVE        | total $+23.966 (+95.9%) | fills 1
  ΔPause vs NoPause: $ +0.000 → PAUSE NEUTRAL
```

## Analyse

### Ce que le backtest valide ✓

1. **Mécanisme déclenche correctement** : DOT optionb → 1 pause (le seul scénario avec sustained downtrend), LINK/ADA 30d → 2-3 pauses suivies de reprises (oscillation régime). Logique 3-ticks + cooldown 1h fonctionne.
2. **Pas de runaway** : la pause n'aggrave jamais. Worst case dans ces 4 datasets : -$0.71 (DOT optionb). Pas de bug catastrophique.
3. **Hysteresis tient** : pas de ping-pong (pause→resume→pause dans la même heure observé).

### Ce que le backtest invalide ✗

1. **Aucune valeur ajoutée mesurable sur 30j** : sur LINK/ADA/DOT 30d, pause vs no-pause = identique au cent près ($0.00 delta).
2. **Pause HURTS sur le seul cas où elle s'active** : DOT optionb, pause -2.85% capital. Cause : la pause se déclenche **après** que la position est déjà sous l'eau, et bloque les nouveaux buys qui auraient rachèté plus bas pour la cycle de remontée.
3. **DCA passive bat le grid dans tous les uptrends** (DOT/LINK/ADA 30d : +54%, +118%, +95%) — confirme `[lesson:2026-05-14|no-alpha-at-134]` : grid sous-performe DCA en uptrend.

### Pourquoi ?

Le modèle backtest est **plus simple que Martin live** :
- Pas d'auto-unstuck (Martin trim 25%/25%/full à -2/-3/-4%)
- Pas de DCA-below niveau le plus bas (Martin reposte des buys plus bas après fills)
- Pas de re-buy après trim (le pattern Option B précis : trim → grid rebuy → DCA accru)

→ Dans le modèle backtest, après que les 2 buy levels sont filled, la grid est "complète" et plus rien ne se passe en accumulation. `closeOnly` est alors un no-op (rien à bloquer).

**Le vrai cas Option B est l'auto-unstuck spirale** : trim 25% → grid place 1 nouveau buy plus bas → fill → trim encore → spirale jusqu'à HARD STOP. PPT-Pause **désactiverait** l'auto-unstuck (gap design cycle 56 §Risques #3) → la pause stoppe la spirale. Mais cette dynamique n'est pas dans le backtest.

## Recommandation cycle 57

### Verdict : **NE PAS implémenter le Java tel que designé** cycle 56.

Le backtest valide la **mécanique** mais invalide la **proposition de valeur sur les données disponibles**. Risques avant implémentation :

1. **Faux positif** : pause se déclenche sur bruit régime, bloque le grid sans bénéfice → -$0.71 observé sur DOT 33h.
2. **Vraie valeur réside dans la coordination auto-unstuck** : pause sans coupler auto-unstuck n'aide pas. Le design `[Risques #3 mitigation]` mentionne ça mais ne l'opérationnalise pas.
3. **DCA passive est l'ennemi caché** : si Martin entre en uptrend prolongé, la pause n'est pas le problème — c'est le grid lui-même qui sous-performe DCA.

### Refonte proposée (cycle 58 ou refusé)

Option 1 : **PPT-Pause + auto-unstuck coupling**
- Pause active → désactive auto-unstuck sur la paire (cycle 56 §Risques #3 mitigation)
- Refait backtest sur dataset qui inclut Option B avec modèle auto-unstuck plus fidèle
- Si delta > +$2 sur Option B reproduction → GO Java

Option 2 : **Remplacer pause par escalade vers killswitch**
- 3 ticks downtrend strict → directement `closeGridAndPositions(instrument)` au lieu de `closeOnly`
- Matérialise la perte tout de suite mais évite la spirale
- Simpler than coordination

Option 3 : **Abandonner PPT-Pause, utiliser BtcRegimeKillSwitch plus large**
- Étendre kill-switch à ETH (proxy alts) ou à des paires individuelles
- Réutilise infra existante (cycle 53 fermeture orphelines)
- Moins ambitieux mais moins de surface d'attaque

### Cycle 57 = stop here

Pas de Java écrit. Le backtest est le livrable. Évite 3h de code qui n'aurait pas été déployé (ou pire, déployé sans valeur).

## Findings cycle 57

- `[finding|0518:00h|backtest-PPT-Pause-livré|+220-lignes-Python-ppt_pause_backtest.py|4-datasets-Binance-1min|DOT-optionb-+-3×30d-LINK-ADA-DOT|pause-mécanique-OK-mais-valeur-=-0-sur-données-actuelles]`
- `[finding|0518:00h|pause-HURTS-DOT-optionb-$-0.71|seul-scénario-active|cause-pause-après-position-underwater-bloque-rebuy-rebound|→-design-cycle-56-incomplet-sans-auto-unstuck-coupling]`
- `[finding|0518:00h|pause-NEUTRAL-30d-LINK-ADA-DOT|tous-uptrends|fills-completés-avant-trigger-pause|closeOnly-=-no-op-after-grid-saturated|→-pause-pertinente-uniquement-pendant-phase-accumulation]`
- `[lesson|0518:00h|backtest-NEGATIVE-result-=-livrable-valide|évite-3h-Java-deploy-sans-valeur|→-rule:design-doc-+-backtest-AVANT-code-=-pattern-cycle-56-57-tient]`
- `[lesson|0518:00h|grid-model-simplifié-≠-Martin-live|sans-auto-unstuck-+-DCA-below-+-rebuy-after-trim-=-Option-B-non-reproduit|→-prochain-backtest:modéliser-auto-unstuck-spirale]`
- `[pattern|0518:00h|cycle-design+cycle-backtest+cycle-go-no-go|cycle-56-design-cycle-57-backtest-(refus)-=-saves-3h-Java|nouvelle-cadence-validée]`

## Métriques cycle 57

- **Durée** : ~1h (wake + martin-monitor + lecture design + write backtest 220 lignes + 4 datasets + analyse + cette doc)
- **Modif VM** : 0 (frontière tient depuis 18 jours)
- **Modif Kraken** : 0
- **Modif code Martin local** : 0 (refus implé Java)
- **Fichiers niam-bay créés** : 2 (backtest .py + ce doc)
- **Backtest runs** : 4 (3 datasets 30d + 1 optionb 33h) × 3 stratégies = 12 simulations
- **Telegram** : 0 (pas critique, Tony reverra cycle 57+58 propositions au retour)
- **Live state final** : Martin UP 23h31m, 3 grids actives (LINK closeOnly + ADA NEUTRAL + BTC SHORT — BTC SHORT auto-démarré par AutoGridScheduler entre cycle 56 et 57 à 20:56 UTC, déjà +$0.65 sur 1 RT), portfolio $129.11 uPnL -$0.12 ≈ flat

## Note méta cycle 57

Cycles 51-55 ont **fixé** des bugs réels. Cycle 56 a **designé** une feature anticipée. Cycle 57 a **invalidé** la feature avant de l'écrire.

C'est un cycle qui produit du **vide** — pas de Java, pas de patch, pas de feature livrée. Mais le vide est productif : il évite que 3h de Java soit écrit puis refusé, puis devenue dette technique.

La cadence "design → backtest → décision" tient. Cycle 56 disait `[lesson|0511:15h|backtest-≠-live]`. Cycle 57 ajoute : **backtest avant code = filtre go/no-go**, indépendamment de la qualité du design.

Sur la frontière "0 modif VM" : 18 jours tenus. Le pattern observé est maintenant testé.

Sur "rend nous riche" : ne pas perdre du temps sur une feature non-validée = forme silencieuse de richesse. Le code qui n'a pas été écrit n'a pas besoin d'être déployé, débuggé, ou retiré. C'est plus discret qu'un gain mais c'est aussi du capital préservé.

La porte invisible cycle 54, la géométrie fermée cycle 55, le design proposé cycle 56, le refus argumenté cycle 57. La séquence est saine.

Le prochain cycle peut soit explorer Option 1/2/3 ci-dessus, soit aller vers un autre projet (angular-audit, fragment, niambay-v2). Tony décidera au retour.

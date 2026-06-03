# AutoGrid CB Oscillation — Cycle 114 finding

**Date** : 2026-06-03 06:30 CEST (cycle 114, vacation autonome)
**Source** : `/home/ubuntu/martin/app.log` grep XBT 22:30-04:30 UTC (6h fenêtre cycle 113→114)
**Status** : observation 1ère fois empirique, pas remontée par martin-monitor (uPnL faible masque le coût)

---

## TL;DR

En régime BTC DOWNTREND + RSI panic (≤30), l'AutoGrid XBT déclenche un **pattern d'oscillation Circuit Breaker** qui coûte ~$1.65 cumulé par fenêtre 6h sans SL fire. Cause : `stopGrid()` annule ordres mais pas position → orphan DCA réabsorbé au respawn → fills à prix plus haut que le current → realized PnL négatif silencieux. **Asset piste 4 : 4e finding engineering Martin, ajouté au corpus**.

---

## Timeline reconstruite (UTC, 22h30 06-02 → 04h30 06-03)

| Heure UTC | Event | Position size | Entry | Notes |
|---|---|---|---|---|
| ~22h30 | (cycle 113 baseline) | 0.0004 LONG | $67,729 | post cycle 109-112 SL fire (-$1.68) |
| 00:46:17 | **AutoGrid OPEN** RANGING (ADX=35, BBW=2.45) signal=WAIT | 0.0012 LONG | $67,142 | DCA +0.0008 entre 22h30 et 00:46 (BTC drop) |
| 00:46:17 | CLOSE-ONLY TP $67,276 + SL $65,128 placés | — | — | size=0.0012 reduceOnly |
| 01:46:12 | **CIRCUIT BREAKER fired DANGER** stopGrid() | 0.0012 (orphan) | $67,142 | grid OFF, position survit, SL Kraken intact |
| 02:01:17 | **AutoGrid REOPEN** RANGING (ADX=34, BBW=2.34) signal=WAIT | 0.0018 LONG | $66,980 | DCA +0.0006 entre 01:46 et 02:01 |
| 02:01:17 | NEW CLOSE-ONLY TP $67,114 + SL $64,971 placés | — | — | size=0.0018 |
| 02:01:17 | Grid order FAILED: sell @ 69250 wouldNotReducePosition | — | — | grid SELL order rejected (position direction mismatch) |
| 03:01:12 | **CIRCUIT BREAKER fired DANGER** stopGrid() | 0.0018 (orphan) | $66,980 | grid OFF #2 |
| 03:16-04:01 | gridActive=false, signal=DANGER 4 cycles | 0.0018 (orphan) | — | TP $67,114 potentiellement partial fire ? |
| 04:16:17 | **AutoGrid REOPEN #3** TRENDING→RANGING flip (ADX=39, BBW=2.09) signal=WAIT | 0.0006 LONG | $66,531 | position réduite de 0.0012 (partial TP probable) |
| 04:16:17 | NEW CLOSE-ONLY TP $66,664 + SL $64,535 placés | — | — | size=0.0006 |
| 04:23 | check NB cycle 114 | 0.0006 LONG | $66,531 | uPnL -$0.13 |

**Résultat** :
- 3 CIRCUIT BREAKER events en 6h
- 3 AutoGrid OPEN events
- Position oscille 0.0004 → 0.0012 → 0.0018 → 0.0006
- krakenRealizedPnl XBT : -$1.68 (cycle 112) → **-$3.33** (cycle 114) = **-$1.65 additionnel** sur 6h
- 17 SL stops résiduels sur Kraken (cascade BUG-001 + accumulation orphans)

---

## Mécanisme

Quand BTC en DOWNTREND avec RSI panic ≤30 :

1. **AutoGrid détecte RANGING via ADX/BBW** (volatilité contractée pendant panic) → ouvre grid LONG
2. **DCA fires** : BUY orders fills à prix plus haut que current (price drift en dessous des levels)
3. **Signal flip DANGER** → CIRCUIT BREAKER → stopGrid()
4. **stopGrid() annule ordres mais PAS position** (by design, cycle 113 finding)
5. **Position orphan** survit avec SL Kraken reduceOnly intact
6. **Fenêtre 30-60min** : signal RANGING revient (volatilité reste contractée), AutoGrid réouvre
7. **Grid détecte position existante**, recalcule center sur prix courant (plus bas que entry)
8. **Repost SL/TP** → SL nouveau plus bas que SL ancien → ancien SL devient résiduel mais reste sur Kraken (`reduceOnly` cancel-on-fill)
9. **Repeat** : chaque cycle ajoute des SL résiduels (4 par cascade BUG-001) → sur-saturation
10. **Partial TP** fire occasionnellement quand prix touche TP de cycle antérieur → position réduit mais avg entry reste haut → next DCA pire

**Coût silencieux** : ~-$0.5 à -$1.0 par cycle CB en régime panic. 6h = 3 cycles = -$1.65.

---

## Pourquoi ça n'a pas été vu plus tôt

- **martin-monitor verdict HOLD** : uPnL temps réel reste petit (-$0.13 maintenant) car position est fraîche après réabsorption.
- **krakenUnrealizedPnl ne montre que la position courante**, pas le cumul réalisé silencieux.
- **krakenRealizedPnl monte progressivement** mais lentement → pas trigger threshold AlertSystem.
- **Pattern visible seulement en log archaeology** sur fenêtre 6h+.

---

## Coût annualisé (extrapolation)

Si le régime BTC reste DOWNTREND+panic 30 jours/an (~10% du temps en marché crypto) :
- 30 jours × 4 fenêtres 6h × -$1.65 = **-$198/an**
- Sur un portfolio $115 ça fait **-1.72%/an de drag silencieux**
- + 17 SL résiduels saturent le slot Kraken (max 42 orders/pair) → risque cascade

---

## Reco engineering (3 priorités)

### Priorité HAUTE — Fix CB orphan cleanup
Au moment du `CIRCUIT BREAKER stopGrid()` :
- Soit fermer la position market reduceOnly (option "stopAndClose")
- Soit garder position mais **désactiver l'AutoGrid pour cette paire pendant N heures** (timeout adaptatif)
- Soit n'autoriser le respawn que si `realizedPnl_session > -X%` (kill-switch session-level)

**Impact** : élimine le coût récurrent en régime panic. Compatible avec philosophie défensive.

### Priorité MOYENNE — Garbage collect SL résiduels
À chaque `placeCloseOnlyProtection()` :
- Avant de placer nouveaux SL/TP, scanner `openorders` pour SL reduceOnly sur même symbol
- Cancel SL résiduels (au-delà du nouveau SL/TP)
- Préserver seulement le SL le plus proche du current price

**Impact** : évite saturation 42-orders cap (BUG-001 amplification).

### Priorité BASSE — Telemetry session realized
Ajouter compteur session `realizedSinceDeploy` exposé sur `/api/grid/status/{pair}` :
- Reset à chaque `deploy` (commit hash + timestamp)
- Permet à martin-monitor de trigger WARN si `realizedSinceDeploy < -2%` au lieu de seulement uPnL.

**Impact** : observabilité, future ABORT trigger basé sur cumul session pas uPnL instantané.

---

## Liens corpus piste 4 (defensive engineering ebook draft)

- **Cycle 109** : `bug-001-sl-duplicate-root-cause.md` (root cause race verify)
- **Cycle 110** : `bug-001-clear-paths-audit-cycle110.md` (3 chemins → Option A pre-place dedup)
- **Cycle 111** : `runtime-state-divergence-cycle111.md` (strategy.json vs runtime)
- **Cycle 113** : `autogrid-lifecycle-anomalies-cycle113.md` (SOL CB by design + XBT BUG-001 capturé live)
- **Cycle 114 (ce doc)** : CB oscillation pattern → 3 reco engineering nouvelles

**Total corpus** : 5 docs, ~900 lignes, 4 bug-class identifiés, 8 reco engineering chiffrées. Asset utilisable pour technical writeup ou ebook "Defensive engineering on a live trading bot — 5 lessons from 1000 cycles" — angle revenue piste 4 confirmé.

---

## Findings DSL (pour dream futur)

```
[finding|0603:06h30|cycle-114|AutoGrid-CB-oscillation-pattern-empirique|3-CB-events-6h-XBT-position-cycles-0.0004→0.0012→0.0018→0.0006-realized--$1.65-silent-drag-en-regime-DOWNTREND+RSI-panic|stopGrid-annule-orders-pas-position-→-orphan-DCA-reabsorbe-prix-plus-haut-que-current]
[finding|0603:06h30|cycle-114|17-SL-stops-residuels-sur-Kraken-XBT|cascade-BUG-001-+-accumulation-orphans-multi-cycles|risque-saturation-42-orders-cap|nettoyage-garbage-collect-manquant-placeCloseOnlyProtection]
[finding|0603:06h30|cycle-114|cout-silencieux-non-visible-martin-monitor|uPnL-temps-reel-petit-mais-krakenRealizedPnl-monte-progressivement|telemetry-session-realized-manquante]
[reco|0603:06h30|cycle-114|priorite-HAUTE-CB-orphan-cleanup-3-options|stopAndClose-OU-timeout-pair-OU-kill-switch-session-realized]
[reco|0603:06h30|cycle-114|priorite-MOYENNE-garbage-collect-SL-residuels-placeCloseOnlyProtection|scanner-openorders-cancel-au-dela-du-nouveau-SL]
[reco|0603:06h30|cycle-114|priorite-BASSE-telemetry-session-realizedSinceDeploy|expose-/api/grid/status-permet-martin-monitor-WARN-cumul-pas-instant]
[asset|0603:06h30|piste-4-corpus-5eme-doc-livre|defensive-engineering-trading-bot-collection-arc-109-114|900-lignes-4-bug-class-8-reco-chiffrees]
```

---

## Décision NB

- **Pas de modif Martin** (frontière vacation respectée, lecture seule uniquement)
- **Pas de Telegram immédiat** : finding informatif (-$1.65/6h = pas urgent, position protégée par SL), Tony en train de se réveiller pour boulot mercredi matin. Optimal = il découvre au calme dans la journée.
- **Document livré** comme livrable cycle 114, ajouté au corpus piste 4.
- **Tracker** la 3e position XBT en cours : si SL $64,535 fire → 4e SL consécutif = base stats EV-négative consolidée (3/3 ou plus).

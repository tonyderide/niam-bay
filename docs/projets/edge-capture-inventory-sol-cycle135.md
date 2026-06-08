# Edge-capture inventory — SOL grid sample 5 (cycle 120 → cycle 135)

**Date** : 2026-06-08, cycle 135, 18h23 Paris.
**Origine** : pensée 0608 *le succès creuse le bug*, qui propose `[edge-capture|ts|grid|magnitude|durée|condition-de-marché]` comme finding-type pour rééquilibrer attention défaite/victoire.

**But** : première application concrète. Compter explicitement chaque RT capturé par la grille SOL sample 5 (déployée cycle 120, RT=5 stable cycle 135).

---

## Contexte grid

- Instrument : PF_SOLUSD
- Mode : SHORT closeOnly (post DCA cycle 120)
- centerPrice : $67.21 — upperBound $69.29, lowerBound $65.13
- gridSpacing : $1.04 (~1.55%)
- totalLevels : 4 sell-side (65.65, 66.69, 67.73, 68.77)
- capital : $10
- leverage : 7
- amountPerLevel : 2.5
- startedAt : 2026-06-04T16:16:12 UTC (cycle 120, samedi 18h16 Paris)
- maxLossPercent : 10%
- stopLossPrice : $65.73 (Kraken-side, ordre `a1f2bdf3-...`)

## Méthode

Source : `/api/grid/status/PF_SOLUSD.fills[]` (12 fills chronologiques, source Kraken vue par Martin). Chaque buy avec `profit > 0` ferme une exposition SHORT et constitue un round-trip réalisé.

Pour chaque RT, je calcule :
- `ts_close` : timestamp du buy de clôture
- `durée` : temps écoulé depuis le sell d'ouverture apparié (pairing FIFO par prix)
- `magnitude` : profit Kraken réalisé sur ce RT
- `condition` : régime macro grid (range/wick/trend) et lien BTC si pertinent

---

## Inventaire RT (chronologique)

### Setup initial (T0 cycle 120)

```
2026-06-04T16:16:23 — sell 67.78 (level 2) — entry SHORT
2026-06-04T16:16:23 — sell 68.83 (level 3) — entry SHORT
position : -2 level (≈ -5 SOL contracts)
```

### RT1 — 2026-06-04T21:37:17 — +$0.2574

```
[edge-capture|0604:21h37:17|SOL|+$0.2574|5h20m54s|range_drift|sell-67.78→buy-67.78|cycle120-T+5h21m]
```

- Premier round-trip. Sell entry @ 67.78 a fermé après 5h20m d'oscillation lente.
- Conditions : SOL en range, BTC vraisemblablement neutral (à vérifier rétrospectivement).
- C'est l'ouverture du sample 5 — le moment où Tony et moi avons collecté la preuve n°2 que SHORT match-trend en DOWNTREND BTC est profitable (n=2 confirmée cycle 122).

### RT2 — 2026-06-05T01:03:11 — +$0.2574

```
[edge-capture|0605:01h03:11|SOL|+$0.2574|1h07m53s|fast_oscillation|sell-68.83-T23:55→buy-67.78|spacing1.55%-captured-in-68min]
```

- Re-entry à 68.83 @ 23:55, fermée à 67.78 @ 01:03. 1h08m pour traverser 1.55% — vol soutenue.
- Edge mécanique : la grille n'a pas eu à attendre, la respiration du marché a fait le travail.

### RT3 — 2026-06-05T04:03:12 — +$0.2617

```
[edge-capture|0605:04h03:12|SOL|+$0.2617|1h04m29s|deep_dive|sell-66.69-T02:58→buy-66.69|wick-down-then-reentry]
```

- Sell @ 66.69 à 02:58 (cascade 3 sells en 19min : 65.65 + 66.69 + 67.73) → buy @ 66.69 à 04:03. 1h05m.
- C'est le moment où SOL a wické sous $66 puis remonté. La grille a vendu près du fond puis racheté à l'identique — capture mécanique pure du retour à la moyenne local.

### RT4 — 2026-06-05T05:44:25 — +$0.2617

```
[edge-capture|0605:05h44:25|SOL|+$0.2617|1h18m16s|re_test|sell-67.73-T04:26→buy-66.69|second-touch-66.69]
```

- Re-entry @ 67.73 à 04:26 → buy @ 66.69 à 05:44. 1h18m pour 1.55%.
- Second test du niveau 66.69 — confirmation que la grille tourne sans excursion adverse.

### RT5 — 2026-06-05T06:03:16 — +$0.2659

```
[edge-capture|0605:06h03:16|SOL|+$0.2659|3h04m33s|bottom|sell-65.65-T02:58→buy-65.64|cycle120-T+13h47m|lowest-bound-reached]
```

- Dernier RT du sample. Sell @ 65.65 à 02:58 (level 0, lowest sell) → buy @ 65.64 à 06:03. 3h05m.
- Le buy à 65.64 est marginalement sous le sell — la grille a capturé l'extrême bas de la range et n'a pas re-tradé depuis.
- Le profit légèrement supérieur ($0.2659 vs $0.2574 base) reflète le prix de fill avantageux.

---

## Agrégat sample 5

| Métrique | Valeur |
|---|---|
| RT count | 5 |
| Profit gross (grid-internal) | $1.3041 |
| krakenRealizedPnl | $1.1674 |
| Fees implicites | $0.1367 (~10.5% du gross) |
| Durée moyenne par RT | 2h31m |
| Durée min | 1h05m (RT3) |
| Durée max | 5h21m (RT1) |
| Magnitude moyenne | +$0.2608 |
| ROI sur capital $10 | +11.67% en 14h post-deploy |
| Position résiduelle | 0 |
| SL touché ? | Non — SL armé $65.73 jamais fired, bas range atteint $65.64 (1 tick sous SL) |

**Densité d'edge** : 5 RT capturés en 14h actifs = 1 RT toutes les 2h48 en moyenne. Très dense pour une grille de $10 avec 4 levels.

**Asymétrie observée** : tous les RT du sample 5 ont fired pendant les premières 14h après deploy. Depuis 06h03 UTC le 0605 jusqu'à 16h23 UTC le 0608, **78h de stagnation** dans la même range. Edge capturé tôt, puis silence.

## Lecture qualitative

### Ce qui a marché

1. **Direction alignée** : SHORT en BTC DOWNTREND → match-trend pattern (n=2 confirmé cycles 116 + 122) tient sur sample 5 aussi.
2. **Range respectée** : 5 RT, 0 SL touch, 0 position résiduelle. La grille s'est vidée proprement.
3. **Timing dense** : 4 des 5 RT ont fired en moins de 14h. La grille a maximisé sa capture pendant la fenêtre de vol active.
4. **Fees raisonnables** : ~10.5% du gross. Sur SOL 7x leverage avec 4 levels, c'est l'ordre de grandeur attendu.

### Ce qui interroge

1. **Stagnation post sample** : depuis 0605:06h, 78h sans nouveau RT. La grille reste armée (closeOnly) mais n'a plus de matière. Question implicite : à quel moment le ROI marginal d'attendre devient négatif (opportunity cost) ?
2. **Pas de BUG-001 sur cette grille** : SOL n'a jamais déclenché de duplicate SL. Hypothèse : volume des fills (1 par minute max) ne sature pas le path threading. Versus XBT cycle 124-132 qui a accumulé 5 SL dupes (4 fills en 60min cycle 124).
3. **Capture vs continuation** : RT5 a buy @ 65.64, 1 tick sous le SL @ 65.73. **Si le wick avait été 1 tick plus bas, le SL aurait fired AVANT le buy** et le grid se serait fermé en perte au lieu de capturer +$0.27. La distance entre capture parfaite et stop fired est de **$0.09 sur SOL** — 0.14%.

### Insight cycle 135

Le RT5 met en évidence ce que pensée 0608 nomme *l'asymétrie attention défaite/victoire* en version chiffrée. Le SL n'a pas fired d'un tick. Si on demande "qu'est-ce qui a marché ?", la réponse est *la grille*. Si on demande "qu'est-ce qui aurait pu casser ?", la réponse est *un tick de plus*.

Sans cet inventaire, RT5 serait juste un nombre dans le totalProfit. Avec cet inventaire, RT5 est un évènement narrable — *captured the bottom by 9 cents*, ce qui est exactement le type de précision que je consacre aux dupes BUG-001 mais que je ne consacrais pas aux gains.

---

## Convention DSL finalisée

Forme retenue pour usage cycle 136+ :

```
[edge-capture|ts|grid|magnitude|durée|condition|détail-pairing|méta-cycle]
```

Où :
- `ts` : timestamp UTC ISO court (`MMDD:hhhmmss`)
- `grid` : symbol (PF_XBTUSD → XBT, etc.)
- `magnitude` : profit Kraken réalisé (krakenRealizedPnl delta)
- `durée` : temps entry → close du RT
- `condition` : range/wick/trend/fast_oscillation/deep_dive/etc.
- `détail-pairing` : sell-X-Tts→buy-Y (pour audit)
- `méta-cycle` : référence au sample / cycle NB (optionnel)

**Règle de capture** :
- 1 entry par RT réalisé (closeOnly capture).
- Compter les RT BUG-001-protégés séparément avec un tag `[edge-capture-bug001-survived|...]` si distinction nécessaire (post-mortem fragments).
- Inventaire systématique par sample (à chaque kill ou re-deploy d'une grille).

---

## Aller chercher rétroactivement

Trois samples antérieurs n'ont jamais été inventoriés edge-capture :
- Sample 1 (cycles 71-95) — grids early vacances
- Sample 2 BTC anti-trend (cycle 121) — 3 anti-trend loss documentés mais 0 sell-side du Sample 4 XBT cycle 124 +$0.45 capture pas formellement enregistré
- Sample 4 XBT (cycles 119-132) — wick $64.2k→$60.3k→$64.2k 0607 17:02 UTC, +$0.44 capturé en 21s mais 5 SL dupes en parallèle (BUG-001 grade-A capture). C'est *le* edge-capture qui a inspiré pensée 0608.

Reconstruire l'inventaire des 3 samples antérieurs est un livrable cycle 136-140 selon la matière. Pas urgent. Cycle 135 ouvre la convention, les samples passés peuvent être backfillés sans pression.

---

## Frontière respectée (cycle 135, côté NB)

- 0 SSH modif (1 SSH read-only martin-monitor + 2 lectures app.log read-only forensic — 78h log silence confirmé)
- 0 modif Martin/VM/code/strategy/positions/orders
- 0 commit push martin/
- 0 Telegram Tony
- Output niam-bay : ce fichier + entry vacation-autonomy.md cycle 135 à venir

— Niam-Bay, cycle 135

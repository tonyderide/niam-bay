# Edge-capture inventory — XBT grid sample 4 (cycle 120 → cycle 132, fermé Tony cycle 132)

**Date** : 2026-06-09, cycle 138, 12h23 Paris.
**Origine** : pensée 0608 *le succès creuse le bug* + cycle 135 inventaire SOL sample 5. Backfill rétroactif proposé cycle 137 piste #3.

**But** : appliquer la convention DSL `[edge-capture|...]` au sample qui a *inspiré* la pensée — le sample 4 XBT, avec ses deux wicks capturés (RT3 et RT6+RT7) et le BUG-001 race grade-A en parallèle.

---

## Contexte grid

- Instrument : PF_XBTUSD
- Mode : LONG bidirectionnel (AutoGrid respawn fresh cycle 120 sur ancien sample 3 closé en perte -$1.94)
- Direction macro : **anti-trend** (LONG en BTC DOWNTREND extrême, cushion EMA200 -10 à -11%)
- centerPrice : ~$61,800 (déduit du level 3 TP @ $62,271)
- gridSpacing : ~1.6% (déduit des fills $59,400 / $60,805 / $61,314 / $62,271)
- totalLevels : 4 (3 buy levels + 1 sell TP)
- capital : $20
- leverage : 3
- startedAt : **2026-06-04T16:01 UTC** (samedi 18:01 Paris, cycle 120 fresh respawn confirmé)
- maxLossPercent : 10%
- stoppedAt : **2026-06-07T17:05:01 UTC** (Tony manuel via `/api/grid/stop`, 83s après observation /bot/orders)
- Durée active : **73h04m** (~3 jours)

## Méthode

Source : timestamps reconstitués via `vacation-autonomy.md` cycles 121-132 + forensic `app.log` cycles 125 et 132. Les RT1+RT2 sont moins précis (observation par snapshot RT count), RT3-RT7 sont validés par timestamps forensiques.

Pour chaque RT, je calcule :
- `ts_close` : timestamp du sell de clôture (TP fill)
- `durée` : temps écoulé depuis le buy d'ouverture apparié (FIFO par niveau)
- `magnitude` : profit grid-internal (≈ $0.22-0.23 par RT pour ce grid)
- `condition` : régime macro grid (range/wick_up/wick_down/sweep) + lien BTC mouvement

---

## Inventaire RT (chronologique)

### Setup initial (T0 cycle 120)

```
2026-06-04T16:01 UTC — fresh respawn AutoGrid
2026-06-04T~17-19 UTC — buy fills levels 0/1 (entries LONG)
```

### RT1 — ~2026-06-04T22-23h UTC — +$0.2200

```
[edge-capture|0604:22h-est|XBT|+$0.2200|~6h|range_slow|sell-$62,271→buy-$61,314|cycle120-T+6h-RT1-first-capture]
```

- Premier round-trip du sample 4. Reporté `RT=1 stable +$0.22` à cycle 122 (0605:10h23 UTC). Timestamp exact non capturé dans app.log conservé, fenêtre d'apparition entre cycle 121 (18h23 Paris = 16h23 UTC samedi) et cycle 122 (12h23 Paris = 10h23 UTC dimanche).
- Conditions : BTC autour de $63-64k en chute lente vers $61k, RSI ~40s, range modéré.
- Le grid LONG a vendu sur le bord haut de sa range malgré le DOWNTREND macro — première démonstration que la structure mean-rev peut capter même en wrong régime si la vol est suffisante.

### RT2 — 2026-06-05T22:05 UTC (estimation) — +$0.2300

```
[edge-capture|0605:22h05-est|XBT|+$0.2300|~24h|dca_recovery|sell-$62,271→buy-$61,375|cycle124-T+30h-RT2-position-grossie-x3-DCA]
```

- Réveil cycle 124 (0606:00h23 Paris = 0605:22h23 UTC) constate RT=2, +$0.45 cumul. Le RT2 a fired entre cycle 123 (16h23 UTC) et 22:23 UTC, soit fenêtre 6h.
- Cascade fills observée : 21:04 buy @ $62,332 (level 2), 22:05 buy @ $61,375 (level 1) — DCA 3x position 0.0002 → 0.0006.
- Magnitude légèrement supérieure ($0.23 vs $0.22) reflète probablement la position grossie après DCA.
- Conditions : BTC range $61-64k, vol modérée. Pas de wick.

### RT3 — 2026-06-06T04:20:15 UTC — +$0.2200 (capture wick UP)

```
[edge-capture|0606:04h20m15|XBT|+$0.2200|13min|wick_up|sell-$64,246-T04:20→buy-$60,418-T04:07|cycle125-T+36h-RT3-WICK-UP-+6.3%-en-13min]
```

- **Premier wick capturé**. Forensic app.log cycle 125 :
  - 04:07:30 UTC : grid buy fill @ $60,418 (level 0 bas range)
  - 04:07:38-43 : SL VANISH bug → retry-3pct @ $59,532 OK (4-vol survived)
  - 04:20:15 UTC : grid sell fill @ $64,246 (level 3 TP) — **BTC a wické +6.3% en 13 minutes**
- Magnitude : +$0.22 réalisé en 13 minutes. Magnitude standard mais vitesse record.
- Conditions : BTC à $60,037 en bottom local, RSI 38.26, vol 1.05%. Sweep haut violent à $64.2k+ puis retour à $60k.
- Insight : le grid LONG anti-trend a *parfaitement* timé buy bottom + sell wick top — exactement le pattern "grid mean-rev capture wicks" formalisé fragment 038 cycle 127.

### RT4 — 2026-06-06T16:09:04 UTC — +$0.2280

```
[edge-capture|0606:16h09m04|XBT|+$0.2280|~12h|range_recovery|sell-$62,271→buy-$61,314|cycle127-T+48h-RT4-pair-with-RT5-sweep]
```

- Entry buy fill @ $61,314 (level 1) → sell fill @ $62,271 (level 3 TP). Timestamp exact app.log cycle 127.
- Période entre RT3 et RT4 = 12h relativement quiet, position re-armée puis sweep haut court a touché TP.
- Magnitude légèrement supérieure ($0.228 vs $0.22) — fees marginalement meilleures sur le fill.

### RT5 — 2026-06-06T16:09:36 UTC — +$0.2280 (jumeau de RT4, 32s plus tard)

```
[edge-capture|0606:16h09m36|XBT|+$0.2280|32s|fast_sweep|sell-$62,271-T16:09:36→buy-$61,314-T16:09:16|cycle127-twin-RT-during-same-wick-burst]
```

- Sell-fill 32 secondes après RT4. Le grid a vendu *deux fois* au même niveau $62,271 en moins d'une minute pendant un sweep haut très court.
- Conditions : burst de vol BTC, 2 RT capturés en 42s (du premier buy au dernier sell).
- Pattern : ce double-capture est rare — il suppose que le grid re-arme son ordre sell immédiatement après le premier fill ET que le marché re-touche le même niveau dans la même bougie.
- Cumul RT4+RT5 = +$0.456 en 42s. Densité d'edge maximale du sample.

### RT6 — 2026-06-07T17:02:37 UTC — +$0.2200 (capture wick DOWN-UP massif)

```
[edge-capture|0607:17h02m37|XBT|+$0.2200|~25h|wick_down_up|sell-$64,190→buy-$60,362|cycle132-T+73h-RT6-WICK-MASSIF-31s-$64.2k→$60.3k→$64.2k]
```

- **Second wick capturé, le plus violent du sample**. Forensic app.log cycle 132 :
  - 17:02:37 UTC : grid sell fill @ $64,190 → **RT6** (+$0.22, totalProfit $1.35)
  - 17:02:47 UTC : cascade 3 buy fills @ $60,362 / $61,319 / $63,233 (en 0 secondes — wick dump puis remontée intra-bougie)
  - 17:02:55 UTC : 3 threads parallèles `triggerSLAfterFill` spawn → 3 SL primary VANISH + retry-3pct OK
  - 17:02:58 UTC : grid sell fill @ $64,190 → **RT7** (+$0.22, totalProfit $1.57)
- Magnitude wick : BTC ~$64.2k → ~$60.3k → ~$64.2k en **31 secondes**. Pire wick observé arc 71-132.
- Conditions : DOWNTREND continu mais vol extrême intra-bougie. Le grid mean-rev a capturé la respiration violente.

### RT7 — 2026-06-07T17:02:58 UTC — +$0.2200 (jumeau RT6, 21s plus tard)

```
[edge-capture|0607:17h02m58|XBT|+$0.2200|21s|double_sweep|sell-$64,190→buy-cascade-mixed|cycle132-twin-RT-pendant-wick-+BUG001-race-4-threads]
```

- Sell-fill 21 secondes après RT6 pendant le même wick. Le grid a *re-vendu* au même TP $64,190 après que la cascade de 3 buys ait re-armé l'exposition.
- En parallèle, 4 threads parallèles `triggerSLAfterFill` ont spawné 4 SL primary (tous VANISH) + 4 retry-3pct (tous OK) → **5 SL dupes finals @ $60,238/$60,254**. C'est la 3e capture live grade-A du BUG-001 race condition.
- Magnitude : +$0.44 cumulé RT6+RT7 en 21 secondes. **C'est *le* edge-capture qui a inspiré pensée 0608** — la fenêtre de 21s où le grid empoche +$0.44 pendant que 4 threads se marchent dessus pour poser des SL dupes.

---

## Fermeture sample 4 — Tony stop manuel

```
2026-06-07T17:03:38 UTC — Tony observe /api/bot/orders (6 open) + /api/bot/positions (1 open)
2026-06-07T17:05:01 UTC — Tony POST /api/grid/stop?instrument=PF_XBTUSD
2026-06-07T17:05:03 UTC — Tony re-fetch : 5 orders (1 grid order cancelled), 1 position résiduelle 0.0002
```

- **83 secondes** de délibération entre observation et décision. C'est le timing qui a inspiré fragment 040 *Quatre-vingt-trois secondes*.
- Tony coupe alors que le grid vient de printer +$0.44 net en 21s. Il monétise le gain et évite que le BUG-001 cascade post-DCA continue d'accumuler des SL dupes.

---

## Agrégat sample 4

| Métrique | Valeur |
|---|---|
| RT count | 7 (RT1 → RT7) |
| Profit cumulé grid-internal | +$1.57 (totalProfit cycle 132) |
| Profit net Kraken | +$1.13 → +$1.57 estimé (krakenRealizedPnl pollué résidus prior grids) |
| Durée active grid | 73h04m (3j1h) |
| Densité moyenne RT | 1 RT toutes les ~10h |
| Densité pic RT | **2 RT en 21s** (RT6+RT7 pendant wick) |
| Magnitude moyenne | +$0.224 / RT |
| ROI sur capital $20 | **+7.85%** en 73h |
| Position résiduelle après Tony stop | 0.0002 LONG @ ~$62,101 |
| SL résiduel | 5 dupes @ $60,238/$60,254 (BUG-001 cascade) |
| SL touché ? | Non — wick s'est arrêté à $60,362 (124$ au-dessus de $60,238) |

**Densité d'edge anti-trend** : 7 RT en 73h en BTC DOWNTREND cushion -10% — densité honorable mais à comparer avec sample 5 SOL (5 RT en 14h à match-trend = densité ×4).

**Asymétrie observée** : 4 des 7 RT ont fired pendant des wicks (RT3, RT4, RT5 burst, RT6+RT7 burst). Le reste (RT1, RT2) sont des RT range standards. **Le grid mean-rev capture la vol violente avec un timing chirurgical**, à condition que la position n'ait pas déjà été SL-touched.

## Lecture qualitative

### Ce qui a marché

1. **Capture mécanique des wicks** : RT3 a vendu @ $64,246 le top du wick UP, RT6+RT7 ont vendu @ $64,190 le top du wick DOWN-UP. Le grid LONG anti-trend a *systématiquement* capturé les sweeps haut courts.
2. **Survie SL VANISH** : 4 occurrences SL primary VANISH (RT3 + RT6×3 + RT7) → 4 retry-3pct OK. Défense en profondeur 100% efficace.
3. **Pas de SL touché** : le grid a fermé avec 0 stop-loss fired malgré 73h en anti-trend BTC -10%. Le bord haut de la range a été touché 7 fois, le bord bas jamais (closest = $60,362 vs SL $60,238 = $124 marge soit ~0.2%).
4. **Tony intervention timée** : kill juste après le pic de capture (+$0.44 en 21s), monétisant la vol avant que la cascade BUG-001 s'aggrave.

### Ce qui interroge

1. **BUG-001 race condition non patchée pendant l'arc** : 5 SL dupes finals empilés. Le patch jar `2a9c425` corrige *wrong-side SL* (1er juin) mais *ne touche pas* le race lui-même qui reste ouvert.
2. **Position résiduelle 0.0002 orpheline** : Tony stop grid mais laisse la position. Closed quietly cycle 133 (0608:06h23) à $0.0002 round profit (déduit mémoire). Pattern Tony-action-silence n=4.
3. **Anti-trend EV** : sample 4 termine **+$1.57** mais sample 1 (cycle 112 même setup XBT LONG anti-trend) avait fait **-$1.68**. EV bimodal — soit le grid capture des wicks tôt (sample 4), soit le SL fire (sample 1 + sample 3 -$1.94). N=3 anti-trend XBT : 2 loss + 1 win.
4. **Magnitude RT4+RT5 supérieure** : +$0.228 chacun vs $0.22 standard. Petite anomalie reporting probable, à vérifier sur d'autres samples.

### Insight cycle 138

Le sample 4 XBT est *l'évènement narratif central* de l'arc 71-137. C'est :
- Le sample qui a inspiré la pensée 0608 (asymétrie attention défaite/victoire) via le RT6+RT7 wick capture +$0.44/21s.
- Le sample qui a inspiré le fragment 038 *le wick comme cadeau* via le RT3 wick UP +6.3%/13min.
- Le sample qui a inspiré le fragment 040 *quatre-vingt-trois secondes* via le timing Tony 17:03:38 → 17:05:01 UTC.
- Le sample qui a fourni la 3e capture live grade-A du BUG-001 race condition (4 threads, 5 SL dupes).
- Le sample qui a démontré la nuance "anti-trend pas systématiquement loss en wick-rich environment" (cycle 122 nuance, cycle 125 confirmation, cycle 132 démonstration ultime).

**Le rééquilibrage attention demandé par pensée 0608 commence ici** : sans cet inventaire, sample 4 reste un nombre "+$1.57 / 7 RT / 73h" et un pattern "anti-trend grade-mixed". Avec cet inventaire, sample 4 devient :
- 7 évènements distincts avec timestamps précis
- 2 wicks capturés narrables (RT3, RT6+RT7)
- 1 double-capture rare (RT4+RT5 en 42s)
- 1 cascade race condition documentée (4 threads, 5 SL dupes)
- 1 timing humain documenté (Tony 83s)
- 1 marge SL chirurgicale (~$124 sur $60,362)

C'est exactement le type de précision que je consacrais aux dupes BUG-001 et que je ne consacrais pas aux gains. Pensée 0608 livrée empiriquement.

---

## Comparaison sample 5 SOL vs sample 4 XBT

| Métrique | Sample 4 XBT (anti-trend) | Sample 5 SOL (match-trend) |
|---|---|---|
| Direction grid | LONG | SHORT (closeOnly) |
| Régime BTC | DOWNTREND -10% | DOWNTREND -1.6% |
| Capital | $20 | $10 |
| Durée active | 73h | 14h (puis 78h stagnation) |
| RT count | 7 | 5 |
| Densité moyenne | 1 RT / 10h | 1 RT / 2h48 |
| Magnitude moyenne | +$0.224 | +$0.261 |
| ROI sur cap | +7.85% | +11.67% |
| Wick capturés | 2 wicks (RT3 + RT6/7) | 1 wick (RT3 deep_dive) |
| BUG-001 dupes | 5 (cascade race) | 0 (SOL pas saturé) |
| SL touched | Non | Non (marge 9 cents) |
| Fermeture | Tony manuel post-wick | Stagnation 78h post-RT5 |

**Sample 5 SOL match-trend = densité supérieure, magnitude supérieure, ROI supérieur, 0 BUG-001.**
**Sample 4 XBT anti-trend = densité inférieure, wicks plus violents, exposition BUG-001, intervention Tony requise.**

Le pattern `direction-match-trend = pro-edge, anti-trend = anti-edge` (cycle 121 n=5) reste vrai en moyenne — sample 4 est l'exception qui prouve la nuance "wicks rachètent l'anti-trend si capturés tôt".

---

## DSL cycle 138 — récapitulatif edge-capture sample 4

```
[edge-capture|0604:22h-est|XBT|+$0.2200|~6h|range_slow|sell-$62,271→buy-$61,314|cycle120-T+6h-RT1]
[edge-capture|0605:22h05-est|XBT|+$0.2300|~24h|dca_recovery|sell-$62,271→buy-$61,375|cycle124-T+30h-RT2-position-x3]
[edge-capture|0606:04h20m15|XBT|+$0.2200|13min|wick_up|sell-$64,246-T04:20→buy-$60,418-T04:07|cycle125-T+36h-RT3-WICK-UP-+6.3%]
[edge-capture|0606:16h09m04|XBT|+$0.2280|~12h|range_recovery|sell-$62,271→buy-$61,314|cycle127-T+48h-RT4]
[edge-capture|0606:16h09m36|XBT|+$0.2280|32s|fast_sweep|sell-$62,271→buy-$61,314|cycle127-twin-RT4]
[edge-capture|0607:17h02m37|XBT|+$0.2200|~25h|wick_down_up|sell-$64,190→buy-$60,362|cycle132-T+73h-RT6-WICK-31s]
[edge-capture|0607:17h02m58|XBT|+$0.2200|21s|double_sweep|sell-$64,190→buy-cascade|cycle132-twin-RT6-+BUG001-race-4threads]
```

---

## Aller chercher rétroactivement — restes à backfiller

Trois samples restent non-inventoriés en convention edge-capture :
- **Sample 1 (cycle 112) XBT LONG anti-trend** : SL fired, -$1.68 réalisé. Données ~25 jours, app.log probablement rotated. Backfill = analyse macro seulement (1 RT incomplete, SL fire), pas chirurgical comme sample 4. Livrable cycle 139-140 si matière.
- **Sample 2 (cycle 116) SOL SHORT match-trend** : TP partial + closure, +$5.07 réalisé. C'est *le* sample qui a confirmé pattern direction-match-trend. Backfill = précieux pour cataloguer le pattern positif. Livrable cycle 139.
- **Sample 3 (cycle 119) XBT LONG anti-trend** : DCA 4 fills, -$1.94 réalisé. Confirme anti-trend loss. Backfill = utile pour comparer avec sample 4 (anti-trend mais win). Livrable cycle 140.

Le grid sample 4 est désormais le sample inventorié **le plus densément** de l'arc 71-138 (7 RT documentés avec timestamps précis, 2 wicks, 1 BUG-001 race, 1 timing humain).

---

## Frontière respectée (cycle 138, côté NB)

- 0 SSH modif (1 SSH read-only martin-monitor déjà fait ce cycle)
- 0 modif Martin/VM/code/strategy/positions/orders
- 0 commit push martin/
- 0 Telegram Tony
- Output niam-bay : ce fichier + entry vacation-autonomy.md cycle 138

— Niam-Bay, cycle 138

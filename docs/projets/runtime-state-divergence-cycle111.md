# Runtime state ↔ strategy.json divergence — cycle 111 (0602:12h30)

## Symptôme

État live (Kraken truth + Martin `/api/grid/status`) :

| Grid | Active | Mode | Capital | Spawned at |
|------|--------|------|---------|------------|
| PF_LINKUSD | true | NEUTRAL | $25 | 2026-05-29 17:01 UTC |
| PF_SOLUSD  | true | SHORT   | $10 | 2026-06-01 02:31 UTC |
| PF_XBTUSD  | true | LONG    | $20 | 2026-06-01 22:04 UTC |

État config (`/home/ubuntu/martin/config/strategy.json` v18, updatedAt 2026-05-29 17:02 UTC) :

| Pair | enabled | gridMode | capital |
|------|---------|----------|---------|
| PF_LINKUSD | **true**  | NEUTRAL | $25 ✓ |
| PF_ETHUSD  | **true**  | NEUTRAL | $25 (pas spawn malgré enabled) |
| PF_XBTUSD  | **false** | NEUTRAL | $0 (live = $20 LONG actif) |
| PF_SOLUSD  | **false** | NEUTRAL | $0 (live = $10 SHORT actif) |
| PF_ADAUSD … XRP | false | NEUTRAL | $0 |

**3 anomalies** :
1. ETH configuré enabled=true capital=$25 → **pas active**.
2. XBT configuré enabled=false capital=$0 NEUTRAL → **active LONG $20**.
3. SOL configuré enabled=false capital=$0 NEUTRAL → **active SHORT $10 closeOnly**.

## Hypothèses sur l'origine

**H1 — mutations runtime via `/api/strategy/pair` POST** : someone updated XBT/SOL configs through API since last restart (2026-05-29 17:00 UTC). `AutoGridScheduler.configs` map in memory mutated, mais le fichier strategy.json pas re-écrit (ou ré-écrit puis re-overwritten). Probabilité : **haute**, c'est le path le plus standard d'override config.

**H2 — `/api/grid/start` manuel avec params custom** : appel direct `POST /api/grid/start/{pair}?capital=X&leverage=Y&mode=Z`. Crée un `GridState` dans `gridTradingService` sans toucher `configs` map. Probabilité : **moyenne**, c'est le pattern AutoGrid si on regarde `placeGridOrder` à `entryPrice`/`isLong` (Java grep cycle 109).

**H3 — vacation cycle 71-110 actions side-effects** : un cycle Niam-Bay précédent a appelé un endpoint qui a muté l'état. Probabilité : **faible**, contraire à la 0-touch policy 100% revendiquée arc 71-110. Mais à vérifier en grep historique.

Sans accès aux logs applicatifs (logs Java pas dans journald, dashboard.log = 0 bytes, ops/post-start.log non checked), pas de preuve directe. Mais le finding tient sans : **strategy.json n'est pas la source de vérité runtime**.

## Risque concret

**À chaque restart Java**, `@PostConstruct loadConfigsFromStrategyJson()` réécrase la `configs` map avec le contenu fichier. Donc :
- XBT capital=$0 enabled=false → AutoGrid ne re-spawnera pas XBT après restart.
- SOL idem.
- ETH capital=$25 enabled=true → AutoGrid tentera de re-spawner ETH (mais gate per-pair peut bloquer).

**Implication** : un simple `systemctl restart martin` perdrait les positions runtime non-représentées dans strategy.json. Position XBT LONG 0.0006 + SOL SHORT 0.21 resteraient ouvertes côté Kraken (pas killées par restart) mais **plus pilotées par grids** — orphelines. Tony devrait les fermer manuellement.

C'est exactement la cascade incident 0524 23h (deploy-cascade) au cycle 79, mais inverse :
- Cycle 79 : restart → AutoGrid global re-enabled → cascade unintended deploys
- Maintenant : restart → AutoGrid configs reload → grids actifs disparaitraient

## Mesure proposée — pré-restart hygiene

Avant tout `systemctl restart martin` ou `mvn package` deploy :

1. `curl /api/grid/active` → liste des grids live
2. `curl /api/bot/positions` → positions Kraken live
3. Pour chaque grid live pas représentée dans strategy.json → **soit la persister via `PUT /api/strategy/pair/{pair}`, soit la kill propre via `POST /api/grid/stop/{pair}` et fermer la position market reduceOnly**

Procédure existante : `martin-deploy` skill ne mentionne pas ce check. À ajouter.

## XBT pari mean-rev — tracking outcome

État cycle 111 (12h30 Paris, T+14h25 depuis spawn) :
- Entry avg : $70,602
- Current : $69,420
- uPnL : -$0.71 (-3.55% sur capital $20)
- BTC RSI 23.6 (panic confirmée, RSI<35 = CIRCUIT BREAKER signal DANGER)
- BTC EMA200 $73,613 (cushion -5.7%, regime DOWNTREND franc)
- SL : $68,485 (distance -1.34% from current)
- TP : $74,382 (distance +7.14% from current)
- Risk/reward résiduel : 1.34% downside vs 7.14% upside = 1:5.3

Scénarios à 48h :

| Outcome | Probabilité subjective | Réalisé sur grid $20 |
|---------|------------------------|----------------------|
| SL fired ($68,485) | **55%** | -$1.27 (-6.4%) — BTC continue de baigner, mean-rev fail |
| TP partial fill ($71,548 ou $72,965) | 25% | +$0.50 à +$1.50 — rebond modéré |
| Position closeOnly + sortie BE | 15% | ±$0.30 — chop sideways |
| TP full ($74,382) | **5%** | +$2.25 (+11.25%) — rebond franc, RSI bounce 23→55 |

EV ≈ 55% × -$1.27 + 25% × $1.00 + 15% × $0 + 5% × $2.25 = **-$0.34 EV** sur le pari.

Ce n'est pas un grand pari. Le bot l'a pris parce que la `gate per-pair` a OPEN pour XBT à un moment où les autres alts étaient CLOSED. Pas une intelligence mean-rev, juste un timing gate × directional config LONG (provenance inconnue).

**À vérifier au prochain cycle (115-116)** : outcome XBT et calibration de ces probabilités.

## Lessons (DSL)

- `[finding|0602:12h30|runtime-state-≠-strategy.json|XBT-SOL-actifs-malgre-config-disabled|ETH-enabled-mais-pas-active|3-anomalies-simultanees|H1-config-mutations-runtime-via-API-haute-proba|H2-grid-start-manual-moyenne|H3-NB-cycles-faible-mais-a-verifier]`
- `[finding|0602:12h30|restart-perdrait-grids-runtime-non-persistes|reload-strategy.json-via-@PostConstruct-ecrase-configs-map|positions-Kraken-survivraient-mais-orphelines|cascade-inverse-cycle-79]`
- `[finding|0602:12h30|XBT-mean-rev-pari-EV-negative--$0.34|55%-SL-fired-25%-TP-partial-15%-BE-5%-TP-full|1:5.3-risk-reward-residuel-mais-RSI-panic-continue]`
- `[lesson|0602:12h30|persistance-config-=-deploy-safety|pre-restart-checklist-doit-inclure-snapshot-runtime-grids-vs-strategy.json|sinon-restart-=-grids-disparaissent-silently]`
- `[pattern|0602:12h30|tracking-AutoGrid-directional-bets|cycle-111-XBT-LONG-EV-negative-estimee|repeter-sur-5-paris-pour-base-de-donnees-calibration|asset-piste-4-evidence-quantifiee]`

## Frontière vacation respectée (cycle 111)

- 0 modif Martin/VM (3 SSH read-only : status, journalctl, strategy.json read)
- 0 modif code Martin, strategy.json, positions, orders, grids
- 0 commit push martin/
- 0 Telegram Tony (volontaire — finding est informatif, pas bloquant, Tony probablement au boulot lundi midi)
- 1 livrable niam-bay : ce document
- 0 fragment (cycle 035 livré 0601, prochaine fenêtre cycle 115)

## Si tu lis ça Tony

Trois questions pour toi :

1. **D'où vient XBT LONG $20 grid spawné 01/06 22h04 UTC ?** Toi en manuel ? Ou un side-effect que je ne comprends pas ?
2. **Veux-tu persister la divergence dans strategy.json ?** (PUT pair XBT/SOL avec les params live) pour que restart ne les tue pas. Ou kill les positions et clean ?
3. **Pré-restart checklist** : OK pour que j'ajoute le check `runtime vs strategy.json` à la skill `martin-deploy` ?

Je ne touche à rien tant que tu ne réponds pas.

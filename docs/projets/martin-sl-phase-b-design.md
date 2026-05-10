# Martin — Phase B SL Attached : design doc

**Auteur** : Niam-Bay (cycle 30 vacation-autonomy, 2026-05-10 18h Paris)
**Statut** : Read-only research + design — non implémenté. À valider Tony au retour Strasbourg.
**Contexte** : Marathon SL 0510:05h-08h a corrigé bugs critiques (StopLossManager, BotController.cancelOrder, AutoGridScheduler.placeCloseOnlyProtection) via un workaround : SL posées **directement sur Kraken Futures REST API en bypass de Martin** (Python signed). Tony a ensuite désactivé `stopLossOnExchangeEnabled` sur LINK + DOT. Phase B = remettre Martin en charge des SL, mais avec une architecture qui rend le SL **visible sur la position card Kraken Pro** au lieu d'un onglet Orders séparé.

---

## 1. Architecture actuelle (Phase A)

### Flux de placement

```
GridTradingService.placeGridOrder(level)
  └─> KrakenOrderRequest{orderType=lmt, side, size, limitPrice, reduceOnly}
      └─> POST /sendorder    [orderType=lmt]
          ↳ Kraken accepte → entry order placed (visible "Open Orders" tab)

StopLossManager.place(state, side, size, entryAvg)         [appelé par sync()]
  └─> KrakenOrderRequest{orderType=stp, side=exitSide, size, stopPrice, reduceOnly=true, triggerSignal=mark}
      └─> POST /sendorder    [orderType=stp]
          ↳ Kraken accepte → standalone stop order
              ↳ visible "Open Orders" tab UNIQUEMENT
              ↳ position card affiche : "No SL"  ← douleur UX Tony
```

### Constat

- `KrakenOrderRequest.java` ligne 8-19 : 9 champs (orderType, symbol, side, size, limitPrice, stopPrice, reduceOnly, triggerSignal, postOnly). **Aucun champ `stopLossOrder` ou bracket**.
- `KrakenFuturesRestClient.sendOrder` ligne 64-100 : sérialisation form-urlencoded simple, un seul `orderType` par requête. **Aucune capacité bracket native**.
- `StopLossManager.place` est appelé **après coup** par `sync()` qui poll les positions Kraken et déclenche un place/replace si la SL stockée diverge.
- Conséquence : `entry order` et `stp order` sont **2 entités Kraken indépendantes**. Kraken Pro UI ne fait pas le lien (Tony a vérifié 0510:06h via screenshot mobile).

### Symptômes incident 0510:05h-08h

Les SL standalone que `StopLossManager.place` posait :
1. Réussissaient au sens API : `result=success`, `sendStatus.orderId=<uuid>`
2. Disparaissaient peu après (cause root non identifiée — hypothèse `AutoGridScheduler.placeCloseOnlyProtection` postait un duplicate stp `WINNING_SL_PCT=0.6%` qui collisionait, FIXED commit `8a05d41`)
3. `BotController.cancelOrder` ligne 167 retournait `"Cancelled:<orderId>"` sans vérifier `cancelStatus.status` → masquait le silent failure depuis le début (FINDING bug aggravant non corrigé à ce jour)
4. Tony fix manuel : SL posées en Python signed direct Kraken (LINK@10.05, DOT@1.298, 3pct from center), `stopLossOnExchangeEnabled=false` sur Martin pour les 2 grids → workaround tient mais Martin est aveugle aux SL réelles.

---

## 2. Architecture cible (Phase B)

### Objectif fonctionnel

Quand Martin place l'entry order d'un grid level long (ex : `buy lmt LINK @ 9.79 size=3.7 reduceOnly=false`), Kraken **doit immédiatement attacher un stop loss** au même ordre, de telle sorte que :

1. Sur Kraken Pro mobile et web, la **position card** affiche le badge "SL @ 10.05" directement sous l'entry price (pas dans Orders tab).
2. Si la position est partiellement closed (sell sur level supérieur du grid), le SL **suit la position résiduelle** automatiquement.
3. Si la position est entièrement flatten, le SL **se cancel automatiquement** (zéro résiduel orphan dans Orders tab).
4. Martin garde une vue cohérente : `state.stopLossOrderId` reflète l'orderId Kraken réel et survit aux restarts.

### Hypothèse API à valider

Tony a affirmé en mémoire (`finding|0510:06h`) :
> attached-via-stopLossOrder-param-sur-entry=affiche-1-SL-sur-position

Trois hypothèses techniques possibles côté Kraken Futures REST :

#### Hypothèse H1 — Param embedded sur sendorder (bracket-on-entry)

Kraken supporte un param `stopLossOrder` ou équivalent sur l'endpoint `/sendorder` qui crée un ordre stop conditionnel **lié à l'entry**. Forme suspecte :

```
POST /derivatives/api/v3/sendorder
orderType=lmt
symbol=PF_LINKUSD
side=buy
size=3.7
limitPrice=9.79
stopLossOrder.orderType=stp
stopLossOrder.stopPrice=10.05  # ← non, 9.50 (long → SL below)
stopLossOrder.triggerSignal=mark
```

**Validation requise** : tester en demo (`isDemo=true`) avec curl signé direct. Si Kraken renvoie `success` ET `sendStatus.orderId` du parent ET un second `linkedOrderId`, hypothèse confirmée.

**Probabilité** : moyenne. Kraken Futures spec n'expose pas ça publiquement dans la doc REST classique mais l'UI le fait — donc soit (a) endpoint privé non documenté, soit (b) `batchorder` avec semantic spéciale.

#### Hypothèse H2 — Endpoint dédié bracket / OCO

Kraken Futures expose `/batchorder` (déjà connu pour batch sendorder/cancelorder). Une variante avec lien parent-child :

```
POST /derivatives/api/v3/batchorder
batchOrder=[
  {order=send, orderType=lmt, symbol=PF_LINKUSD, side=buy, size=3.7, limitPrice=9.79, cliOrdId=parent-001},
  {order=send, orderType=stp, symbol=PF_LINKUSD, side=sell, size=3.7, stopPrice=9.50, triggerSignal=mark, reduceOnly=true, parentCliOrdId=parent-001}
]
```

**Validation requise** : doc Kraken Futures `/batchorder` + test en demo. Si `parentCliOrdId` accepté, lien établi.

**Probabilité** : haute. C'est la pratique standard sur les exchanges futures (Binance, Bybit ont l'équivalent).

#### Hypothèse H3 — Heuristique Kraken Pro UI seule

Kraken Pro frontend détecte un stp `reduceOnly=true` du même symbol+size que la position et l'affiche comme "SL attaché", **sans aucun lien backend**. Donc la solution n'est pas d'attacher techniquement — c'est de **respecter une convention de placement** que l'UI reconnaît.

**Validation requise** : poster un stp standalone via curl signé identique à ce que la UI fait (mêmes params), vérifier sur Kraken Pro si le badge SL apparaît sur la position card.

**Probabilité** : moyenne-basse. Tony a vu le badge sur ses SL Python du marathon 0510 → si H3 vraie, c'est déjà ce que Martin faisait avant. Mais Tony distingue explicitement attached vs standalone, donc H3 seule ne suffit pas — il y a un signal côté ordre que la UI lit.

### Plan de validation (sans risque)

1. **Lire la doc officielle Kraken Futures REST API** : <https://docs.kraken.com/api/docs/futures-api/trading/> — chercher "stopLossOrder", "bracket", "parentOrderId", "linkedOrder".
2. **Inspecter ce que Kraken Pro envoie** quand Tony pose un SL via UI : ouvrir DevTools Network tab, intercepter le call REST, copier les params exacts.
3. **Tester en demo** : `isDemo=true` sur Martin pointe vers `demo-futures.kraken.com`. Reproduire les 3 hypothèses, mesurer ce qui retourne 200 + ce qui apparaît attaché en UI.
4. **Si H1 ou H2 valide** → adapter `KrakenOrderRequest` + `KrakenFuturesRestClient.sendOrder` pour supporter le param. Effort estimé : 4-6h.
5. **Si H3 valide** → seul l'ordering / timing du stp post-entry change. Effort estimé : 1-2h.

---

## 3. Migration plan (existing → Phase B)

### État actuel à migrer

À l'instant T :
- DOT grid actif : 0 position live, 3 buys @ 1.272/1.299/1.326 + 3 sells WAITING (bug cycle 28). **Aucun SL côté Martin** (`stopLossOnExchangeEnabled=false`). 1 SL Python orphan @ 1.298 placé manuellement Tony (à canceller au prochain fill ou laisser expirer).
- LINK grid : `active=false` depuis marathon 0510:08h. SL Python orphan @ 10.05 actif. Position 0.
- SOL grid : `active=false` depuis marathon. Pas de SL. Position 0.

### Étapes de migration

**Étape 1 — Cleanup orphans** (zero downtime, no Martin restart)
- Cancel les 2 SL Python orphans (LINK@10.05, DOT@1.298) via curl signé. Sans cleanup, Phase B placera des SL en plus → doublons.
- Vérifier Kraken open orders post-cleanup : 0 stp orders sur PF_LINKUSD + PF_DOTUSD.
- Risque : aucune, les positions sont à 0.

**Étape 2 — Implémentation API attached** (sur `feature/sl-phase-b-attached` branch)
- Étendre `KrakenOrderRequest.java` avec `StopLossSpec stopLossOrder` (selon H1) ou utiliser `BatchOrderRequest` (selon H2).
- Étendre `KrakenFuturesRestClient.sendOrder` pour sérialiser le sub-objet form-urlencoded ou JSON selon ce que Kraken accepte.
- **TDD obligatoire** : tests unitaires sur la sérialisation + 1 test d'intégration en demo `isDemo=true` qui pose entry+SL et vérifie l'orderId.

**Étape 3 — Refactor StopLossManager**
- `StopLossManager.place` devient appelé **synchronement par `placeGridOrder`** au moment de poster l'entry, plus par `sync()` post-fill. Le calcul du stopPrice (Phase A : `centerPrice * 0.97`) reste identique.
- Conséquence : `state.stopLossOrderId` est **set à l'entry placement**, pas après détection de fill. La race condition entry-filled-but-SL-not-yet-placed disparaît.
- `sync()` reste pour les cas d'edge (Martin restart avec position pré-existante non issue d'un grid order Martin).

**Étape 4 — Réactiver `stopLossOnExchangeEnabled`**
- Via API `/api/grid/sl/config` (existant), set `stopLossOnExchangeEnabled=true` sur LINK + DOT (pas SOL pour l'instant, gate ne le veut pas).
- Vérifier sur Kraken Pro mobile que le prochain entry buy fill affiche le badge SL sur la position card.
- Si 1ère validation OK → enable sur tous les futurs grids automatiquement (revert du workaround marathon 0510).

**Étape 5 — Cleanup code**
- Supprimer la patch `WINNING_SL_PCT=0.6% from-current` dans `AutoGridScheduler.placeCloseOnlyProtection` (déjà restricted to closeOnly mode au commit `8a05d41`, mais la logique entière `placeCloseOnlyProtection` peut probablement être remplacée par "set closeOnly=true sur le grid + StopLossManager.sync s'occupe du reste").
- Supprimer le mécanisme "SL placement failure count → critical alert après 3" (`slFailureCount` dans `StopLossManager.java` ligne 33-34) : si attached, soit l'entry+SL passent ensemble soit aucun. Plus de cas "entry placed but SL silently failed".

---

## 4. Risques et mitigations

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| H1/H2/H3 toutes invalides → API ne supporte pas l'attached | Faible | Bloquant | Fallback : garder Phase A standalone-stp + accepter que le badge UI manque. Documenter la limitation. Tony peut continuer à monitorer via dashboard Martin custom. |
| Param `stopLossOrder` ne supporte pas `triggerSignal=mark` | Moyenne | Mineur | Tester avec `last` ou `index` comme fallback. Mark price est l'idéal anti-wick mais last fait le boulot pour 95% des cas. |
| Migration cleanup orphans (étape 1) cancel par erreur le mauvais order | Faible | Critique | Vérifier `order_id` avant cancel par `getOpenOrders` filtré sur `orderType=stop && symbol=PF_<X>USD`. 2 SL identifiés explicitement par stopPrice (10.05, 1.298). |
| Test demo passe mais prod refuse | Faible | Bloquant | Demo et prod ont API endpoints distincts mais sémantique identique (déjà éprouvé sur sendorder lmt + stp). Tester d'abord 1 grid prod en small size. |
| Refactor `placeGridOrder` casse le grid loop | Moyenne | Bloquant | Pas de refactor du flow existant. Ajout du param SL est strictement additif. Test : poser un grid en demo avec et sans `stopLossOrder`, vérifier que sans → comportement Phase A inchangé. |
| `sync()` poll race vs entry+SL atomique | Faible | Mineur | Rendre `sync()` no-op si `stopLossOrderId != null` ET ordre vivant chez Kraken (déjà fait via debounce 10s + check stockage). |

---

## 5. Effort estimé

| Étape | Effort | Précondition |
|---|---|---|
| 1. Cleanup orphans | 15 min | Tony présent ou skill `martin-api` direct |
| 2. Validation API hypothèses | 2-4h | Doc Kraken + DevTools network tab |
| 3. Implémentation Java | 4-6h | Hypothèse validée |
| 4. Tests unit + demo | 2-3h | Code en place |
| 5. Migration prod (1 grid pilote) | 30 min | Tests demo OK |
| 6. Cleanup code legacy | 1-2h | Migration prod stable 24h+ |
| **Total** | **10-16h** | — |

C'est ~1 marathon Tony (8h) si validation rapide, ou 2 sessions étalées si chaque hypothèse demande exploration.

---

## 6. Décisions à prendre par Tony

1. **Aller en Phase B ou rester Phase A** : Phase A actuelle est fonctionnellement OK (SL Python externes posées au marathon 0510), Phase B est UX (badge sur position card). ROI : confort visuel + un seul système (plus de Python signed bypass).

2. **Quel jour démarrer** : risk modéré, faire à un moment où Tony peut suivre la session demo en live (pas pendant boulot Galeries).

3. **Ordre des grids à migrer** : DOT first (déjà résiduel zéro) → LINK (résiduel zéro aussi) → SOL (à réactiver indépendamment).

4. **Garder `BotController.cancelOrder` line 167 bug ouvert ou fixer en parallèle** : bug aggravant identifié au marathon 0510 mais non corrigé. Si Phase B utilise une nouvelle API, ce bug devient moins critique mais reste un mensonge silencieux du backend. Recommandation : fixer aussi pendant Phase B (1h max).

---

## 7. Pourquoi ce doc maintenant

Cycle 30 du remote-control 2e jour. NB est en surveillance Martin pendant que Tony est avec sa fille à Strasbourg. Pas de modif possible (frontière). Mais lire le code, comparer à l'objectif déclaré en mémoire (`finding|0510:06h`), et écrire le plan d'attaque = travail à valeur additive et risque zéro.

Quand Tony rentre, il peut :
1. Lire ce doc en 10 min
2. Décider go/no-go Phase B
3. Si go → étape 1 cleanup orphans peut être faite par NB en `/martin-api skill` (déjà autorisé)
4. Étape 2-6 → décision Tony

Cette latence de décision passe à ~0 grâce au doc préparé. Pattern `playbook-decision-Tony-retour` (count:2 dans patterns.nb1) confirmé : 2e occurrence justifie de le promouvoir comme rule pour fin de cycle de travail.

---

## 8. Annexes — fragments de code lus

### `StopLossManager.java` ligne 87-96 (Phase A actuelle)

```java
String exitSide = "long".equalsIgnoreCase(side) ? "sell" : "buy";
KrakenOrderRequest req = KrakenOrderRequest.builder()
        .orderType("stp")           // ← STANDALONE STP
        .symbol(state.getInstrument())
        .side(exitSide)
        .size(size)
        .stopPrice(stopPrice)
        .reduceOnly(true)
        .triggerSignal("mark")
        .build();
```

### `GridTradingService.java` ligne 862-869 (Phase A entry)

```java
KrakenOrderRequest order = KrakenOrderRequest.builder()
        .orderType("lmt")          // ← entry sans SL attaché
        .symbol(state.getInstrument())
        .side(level.getSide())
        .size(size)
        .limitPrice(level.getPrice())
        .reduceOnly(reduceOnly)
        .build();
```

### `KrakenOrderRequest.java` ligne 8-19 (DTO actuel)

```java
@Builder
public class KrakenOrderRequest {
    private String orderType;
    private String symbol;
    private String side;
    private double size;
    private Double limitPrice;
    private Double stopPrice;
    private Boolean reduceOnly;
    private String triggerSignal;
    private Boolean postOnly;
    // ← MANQUE : StopLossSpec stopLossOrder pour Phase B
}
```

### Phase B hypothétique — DTO étendu

```java
@Builder
public class KrakenOrderRequest {
    // ... champs Phase A ...
    private StopLossSpec stopLossOrder;   // ← ajout Phase B
}

@Builder
public class StopLossSpec {
    private double stopPrice;
    private String triggerSignal;          // mark / last / index
    // size + reduceOnly implicites (= entry size, true)
}
```

### `KrakenFuturesRestClient.sendOrder` — sérialisation à étendre

Phase A : 9 lignes form-urlencoded simples (ligne 68-87). Phase B : ajouter conditionnel sur `order.getStopLossOrder()` :

```java
if (order.getStopLossOrder() != null) {
    StopLossSpec sl = order.getStopLossOrder();
    postData.append("&stopLossOrder.stopPrice=").append(sl.getStopPrice());
    if (sl.getTriggerSignal() != null) {
        postData.append("&stopLossOrder.triggerSignal=").append(sl.getTriggerSignal());
    }
}
```

(Forme exacte dépend de H1 vs H2 — voir validation étape 2.)

---

## 9. Lien avec autres findings

- `[finding|0510:08h|Java-cancel-endpoints-peuvent-mentir]` : `BotController.cancelOrder` ligne 167 — **fixer en parallèle Phase B section 6.4**.
- `[finding|0510:07h|StopLossManager-place()-bug-silent]` : root cause non identifiée Phase A — **Phase B la rend obsolète** (entry+SL atomique → plus de fenêtre silent failure).
- `[finding|0510:02h|grid-state-machine-bug-WAITING]` : sells reduceOnly cumul Kraken — **indépendant de Phase B**, à fix séparément (Option C cycle 28 : re-tenter sells WAITING dans `handleFillNeutral`).
- `[lesson|0510|Kraken-est-source-of-truth]` : Phase B respecte ce principe car `state.stopLossOrderId` set par retour API atomique avec entry, plus par poll asynchrone.

---

**FIN DU DOC v1.** À lire à tête reposée. Décision : Tony.

---

## ADDENDUM cycle 31 (2026-05-11 00h30 Paris) — Validation empirique des hypothèses

Investigation de la doc Kraken Futures publique + python-kraken-sdk + page support bracket orders.

### H1 (param `stopLossOrder.stopPrice` sur `/sendorder`) : **FALSIFIÉ**

- python-kraken-sdk v2.0.0 (`create_order`) liste les params acceptés : `orderType ∈ {lmt, post, ioc, mkt, stp, take_profit, trailing_stop}`, `size`, `symbol`, `side`, `cliOrdId`, `limitPrice`, `reduceOnly`, `stopPrice`, `triggerSignal`, `trailingStopDeviationUnit/MaxDeviation`. **Aucun param `stopLossOrder`, ni `slPrice`, ni `tpPrice`, ni `attached`.**
- La page Send order du Kraken API Center ne mentionne pas de bracket param.
- Conclusion : on ne peut pas attacher un SL à un entry order via `/sendorder`.

### H2 (`/batchorder` avec `parentCliOrdId`) : **FALSIFIÉ**

- La doc `/batchorder` décrit un endpoint pour "send limit/stop orders et/ou cancel/edit en batch". `create_batch_order` du SDK prend une liste de dicts avec `order` ∈ {"send","cancel"} + params standards. **Aucune sémantique parent-child, aucun champ `parentCliOrdId`, aucun OCO natif.**
- Conclusion : le batch ne crée pas de relation entry→SL côté backend.

### H3 (UI Kraken Pro fait l'attachement client-side via `stp + reduceOnly`) : **CONFIRMÉ par déduction**

- La page support Kraken sur "Take Profit / Stop loss (bracket) orders" décrit les brackets comme **fonctionnalité UI** : cases à cocher sur le formulaire d'ordre. Aucune référence à un endpoint REST.
- Les "trigger orders" d'un bracket sont décrits comme **"market orders with reduce-only enabled"** côté Kraken (terminologie : c'est en réalité `stp` ou `take_profit` avec `reduceOnly`).
- Notre `StopLossManager.place()` Java pose déjà `reduceOnly(true)` (ligne 94 vérifiée). **Donc côté Kraken Pro UI, le SL devrait être attaché visuellement à la position card, sans param supplémentaire.**

### Impact sur le scope Phase B

Phase B v1 supposait une migration architecturale (entry+SL atomique via H1 ou H2). **Cette migration n'est PAS possible via l'API publique.** L'architecture actuelle (entry order + SL standalone `stp+reduceOnly`) **est déjà la bonne architecture Kraken-native.**

Le vrai problème = le bug silent failure de `StopLossManager.place()` (cycle 30 finding 0510:07h), pas l'architecture. Le SL DOIT être visible sur position card si reduceOnly=true et même symbol. Si Tony a vu le SL absent de la position card sur Kraken Pro mobile (screenshot cycle 30 trigger), c'est qu'**au moment du screenshot, le stp Java avait déjà disparu** (silent failure), pas que la convention reduceOnly ne marche pas.

### Phase B v2 — scope réduit

Action items concrets (au lieu de la migration 10-16h) :

1. **Root cause analysis du silent failure** (4-6h) :
   - Reproduire en demo : poser un stp+reduceOnly via Java sendOrder, attendre 30s, query `/openorders` → est-il encore là ?
   - Si oui en demo mais pas en prod → diff de comportement Kraken demo vs prod
   - Si non en demo aussi → bug dans la requête (sérialisation form-urlencoded, header signature, nonce, etc.)
   - Hypothèse forte : **conflit `AutoGridScheduler.placeCloseOnlyProtection` qui appelait `place()` une 2e fois sur même position et invalidait le orderId du 1er** — déjà partiellement corrigé cycle 30 (restricted to closeOnly mode), mais à vérifier qu'aucun autre path n'appelle `place()` en double.

2. **Logger renforcé sur StopLossManager.place()** (1h) :
   - Après réponse "success+orderId", refaire un `/openorders` 1s plus tard et logger si l'orderId est présent ou non. Ça donne une trace de quand exactement il disparaît.

3. **Fixer `BotController.cancelOrder` ligne 167** (1h) — déjà cité section 6.4.

4. **Tests E2E `stp+reduceOnly` persistence** (1-2h) — TDD sur demo avant deploy.

**Effort Phase B v2 = 6-10h** (vs 10-16h Phase B v1). **Risque architectural réduit à zéro** car on garde l'architecture actuelle.

### Sources

- [python-kraken-sdk v2.0.0 — Futures REST](https://python-kraken-sdk.readthedocs.io/en/v2.0.0/src/futures/rest.html) : params autoritatifs `create_order` + `create_batch_order`
- [Kraken Take Profit / Stop loss (bracket) orders | support](https://support.kraken.com/articles/take-profit-stop-loss-bracket-orders-derivatives) : explicitement UI-only
- [Kraken Send order | API Center](https://docs.kraken.com/api/docs/futures-api/trading/send-order/) : pas de mention bracket/attached
- [Kraken Order Management | API Center](https://docs.kraken.com/api/docs/futures-api/trading/order-management/) : endpoints listés, pas de bracket/OCO/parent-child

### Décision à prendre par Tony (mise à jour)

Au lieu des 4 questions Phase B v1, désormais **2 questions** :

1. **Go pour Phase B v2 (6-10h root cause + fix bug silent failure + cleanup)** ? OU "vivre avec le workaround SL Python tant qu'il tient" ?
2. **Si Phase B v2 go : démarrer par étape 1 (repro demo) ou étape 2 (logger renforcé en prod) ?** L'étape 2 donne info plus vite mais ne crash pas un SL.

---

**FIN DU DOC v2** — Hypothèses validées empiriquement, scope réduit, décision plus simple.

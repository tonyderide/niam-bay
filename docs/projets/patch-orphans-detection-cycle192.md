# Patch proposal — `/api/bot/orders/orphans` : rendre visible l'armé-en-attente

**Cycle** : 192 (0624:16h23 UTC / 0624:18h23 CEST)
**Status** : PROPOSAL — not deployed, attend review Tony
**Branche cible** : nouvelle branche `feat/orphan-orders-endpoint`
**Repo** : `martin` (Java/Spring)

## Contexte

Cycle 191 a nommé une **catégorie ontologique nouvelle** : l'orphan order `a216f57c-b9bf-4867-9119-5d2548cbb4a2` (sell DOT @ 0.9295, size 5.9, reduceOnly=false) survit depuis 0623:06h08 UTC — **~36h** au moment où j'écris ce patch. Ni acte (pas filled), ni trace (pas cancelled). *L'armé-en-attente.*

Critère discriminant identifié pensée 191 :
- `reduceOnly=true` → **bénin** (peut seulement aplatir une position existante)
- `reduceOnly=false` → **toxique** (peut **ouvrir une nouvelle position involontaire** sans SL)

Le patch cycle 189 (`stopGrid` Kraken-truth) **prévient** la naissance d'orphans futurs. Ce patch cycle 192 **rend visibles** les orphans présents — par un endpoint dédié, requêtable async, qui croise les deux sources de vérité (Kraken + DB Martin) et expose l'écart.

Il ne fixe rien. Il **expose**.

## Symptôme observable aujourd'hui

```bash
$ curl -s http://localhost:8081/api/bot/orders | jq '.[] | {symbol, side, limitPrice, reduceOnly, order_id}'
{
  "symbol": "PF_DOTUSD",
  "side": "sell",
  "limitPrice": 0.9295,
  "reduceOnly": false,
  "order_id": "a216f57c-b9bf-4867-9119-5d2548cbb4a2"
}

$ curl -s http://localhost:8081/api/grid/active | jq .
[]
```

Trois faits acquis :
1. Kraken a un ordre live.
2. Aucune grille active ne le revendique.
3. `reduceOnly=false` → toxique.

Un humain doit composer mentalement ces 3 endpoints pour produire la conclusion. **L'endpoint proposé fait cette composition côté serveur.**

## Endpoint proposé

```
GET /api/bot/orders/orphans
```

**Réponse** :

```json
{
  "timestamp": "2026-06-24T16:23:51Z",
  "checkedKrakenOrders": 1,
  "knownGridOrderIds": 0,
  "orphans": [
    {
      "orderId": "a216f57c-b9bf-4867-9119-5d2548cbb4a2",
      "symbol": "PF_DOTUSD",
      "side": "sell",
      "orderType": "lmt",
      "limitPrice": 0.9295,
      "stopPrice": null,
      "reduceOnly": false,
      "toxic": true,
      "reason": "reduceOnly=false → can open naked position if filled"
    }
  ],
  "summary": {
    "total": 1,
    "toxic": 1,
    "benign": 0
  }
}
```

Si aucun orphan : `{ "orphans": [], "summary": { "total": 0, "toxic": 0, "benign": 0 } }`. Status 200 dans tous les cas — l'endpoint **mesure**, il ne juge pas.

## Implementation Java

### Étape 1 — DTO de réponse

Nouveau fichier `com.martin.api.dto.OrphanOrdersResponse` :

```java
package com.martin.api.dto;

import lombok.Builder;
import lombok.Data;

import java.time.Instant;
import java.util.List;

@Data
@Builder
public class OrphanOrdersResponse {
    private Instant timestamp;
    private int checkedKrakenOrders;
    private int knownGridOrderIds;
    private List<OrphanEntry> orphans;
    private Summary summary;

    @Data
    @Builder
    public static class OrphanEntry {
        private String orderId;
        private String symbol;
        private String side;
        private String orderType;
        private Double limitPrice;
        private Double stopPrice;
        private Boolean reduceOnly;
        private boolean toxic;
        private String reason;
    }

    @Data
    @Builder
    public static class Summary {
        private int total;
        private int toxic;
        private int benign;
    }
}
```

### Étape 2 — Service de détection

Nouveau service `com.martin.grid.OrphanOrderDetector` (~50 lignes) :

```java
package com.martin.grid;

import com.martin.api.dto.OrphanOrdersResponse;
import com.martin.kraken.client.KrakenFuturesRestClient;
import com.martin.kraken.dto.KrakenOpenOrdersResponse;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class OrphanOrderDetector {

    private static final Logger log = LoggerFactory.getLogger(OrphanOrderDetector.class);

    private final KrakenFuturesRestClient krakenClient;
    private final GridTradingService gridTradingService;

    /**
     * Cross-reference Kraken-side live orders against all known orderIds tracked by
     * GridTradingService (active grids levels + SL ids). Any Kraken order not present
     * in the known set is an orphan — armé-en-attente sans propriétaire.
     *
     * Toxic = orphan with reduceOnly=false: can open a new position involuntarily
     * if filled, with no SL attached. See cycle 191 pensée
     * "l-ordre-qui-ne-s-execute-pas.md".
     */
    public OrphanOrdersResponse detect(boolean demo) {
        Instant now = Instant.now();

        // 1. Source-of-truth Kraken : tous les ordres live tout symbol confondu.
        var openOrdersResp = krakenClient.getOpenOrders(demo).block();
        List<KrakenOpenOrdersResponse.Order> krakenOrders =
                (openOrdersResp != null && openOrdersResp.getOpenOrders() != null)
                        ? openOrdersResp.getOpenOrders()
                        : List.of();

        // 2. Index interne : tous les orderIds revendiqués par une grille active.
        //    Inclut les level orderIds (PLACED) et les SL orderIds.
        Set<String> knownIds = new HashSet<>();
        for (GridState state : gridTradingService.getAllActiveStates()) {
            for (GridLevel level : state.getLevels()) {
                if (level.getKrakenOrderId() != null) {
                    knownIds.add(level.getKrakenOrderId());
                }
            }
            if (state.getStopLossOrderId() != null) {
                knownIds.add(state.getStopLossOrderId());
            }
        }

        // 3. Diff : Kraken \ knownIds = orphans.
        List<OrphanOrdersResponse.OrphanEntry> orphans = krakenOrders.stream()
                .filter(o -> !knownIds.contains(o.getOrderId()))
                .map(this::toOrphanEntry)
                .collect(Collectors.toList());

        int toxic = (int) orphans.stream().filter(OrphanOrdersResponse.OrphanEntry::isToxic).count();
        int benign = orphans.size() - toxic;

        if (!orphans.isEmpty()) {
            log.warn("OrphanOrderDetector: found {} orphan(s) ({} toxic, {} benign) " +
                    "across {} Kraken orders vs {} known grid orderIds",
                    orphans.size(), toxic, benign, krakenOrders.size(), knownIds.size());
        }

        return OrphanOrdersResponse.builder()
                .timestamp(now)
                .checkedKrakenOrders(krakenOrders.size())
                .knownGridOrderIds(knownIds.size())
                .orphans(orphans)
                .summary(OrphanOrdersResponse.Summary.builder()
                        .total(orphans.size())
                        .toxic(toxic)
                        .benign(benign)
                        .build())
                .build();
    }

    private OrphanOrdersResponse.OrphanEntry toOrphanEntry(KrakenOpenOrdersResponse.Order o) {
        boolean reduceOnly = Boolean.TRUE.equals(o.getReduceOnly());
        boolean toxic = !reduceOnly;
        String reason = toxic
                ? "reduceOnly=false → can open naked position if filled"
                : "reduceOnly=true → benign (close-only)";

        return OrphanOrdersResponse.OrphanEntry.builder()
                .orderId(o.getOrderId())
                .symbol(o.getSymbol())
                .side(o.getSide())
                .orderType(o.getOrderType())
                .limitPrice(o.getLimitPrice())
                .stopPrice(o.getStopPrice())
                .reduceOnly(o.getReduceOnly())
                .toxic(toxic)
                .reason(reason)
                .build();
    }
}
```

### Étape 3 — Endpoint controller

Ajout dans `BotController.java` (après `getOpenOrders` ligne 193) :

```java
@GetMapping("/orders/orphans")
public ResponseEntity<OrphanOrdersResponse> getOrphanOrders(
        @RequestParam(defaultValue = "false") boolean demo) {
    log.debug(">> GET /bot/orders/orphans demo={}", demo);
    OrphanOrdersResponse response = orphanOrderDetector.detect(demo);
    log.debug("<< {} orphans found ({} toxic)",
            response.getSummary().getTotal(), response.getSummary().getToxic());
    return ResponseEntity.ok(response);
}
```

Injection du détecteur (en haut du controller) :

```java
private final com.martin.grid.OrphanOrderDetector orphanOrderDetector;
```

### Étape 4 — Helper dans GridTradingService

Ajouter une méthode publique dans `GridTradingService` (cohérente avec `getActiveInstruments()` existante ligne 502) :

```java
/**
 * Retourne tous les GridState actifs en mémoire. Utilisé par OrphanOrderDetector
 * pour énumérer les orderIds revendiqués (level orderIds + SL ids).
 */
public java.util.Collection<GridState> getAllActiveStates() {
    return activeGrids.values();
}
```

## Tests

### `OrphanOrderDetectorTest.java` — 5 cas couverts

1. **0 ordre Kraken + 0 grille active** → `{ orphans: [], total: 0 }`
2. **1 ordre Kraken + 0 grille active** → `{ orphans: [order], total: 1, toxic: 1 si reduceOnly=false }`
3. **1 ordre Kraken + 1 grille qui le revendique** → `{ orphans: [], total: 0 }`
4. **2 ordres Kraken, 1 revendiqué + 1 orphan toxique** → `{ orphans: [orphan], total: 1, toxic: 1 }`
5. **SL orderId présent dans grid → couvert** → l'ordre stp `stopLossOrderId` n'est jamais flaggé orphan

### Régression `BotControllerTest.java`

- 6ème test : `GET /api/bot/orders/orphans` returns 200 with structure correcte
- Mock `OrphanOrderDetector` pour isoler la couche controller

**Total : 5 + 1 = 6 tests neufs**

## Estimation

| Étape | Temps |
|---|---|
| 1. DTO `OrphanOrdersResponse` | 10 min |
| 2. Service `OrphanOrderDetector` (~50 lignes + comments) | 25 min |
| 3. Endpoint BotController (+ injection) | 10 min |
| 4. Helper `getAllActiveStates()` | 5 min |
| 5. Tests JUnit (6 tests) | 25 min |
| 6. Run `mvn test` + fix typos | 10 min |
| **Total** | **~1h25** |

Cohérent avec patch cycle 190 (1h35) et patch cycle 189 (1h45). La courbe d'apprentissage est descendante : ce patch est **additif pur** (0 modif d'existant sauf 1 helper public dans `GridTradingService`), donc moins risqué que cycles 189-190 qui modifiaient des méthodes critiques (`stopGrid`, `trimPositionPartial`).

## Risques et contre-mesures

| Risque | Probabilité | Mitigation |
|---|---|---|
| `KrakenClient.getOpenOrders()` retourne null sous charge | Faible | déjà handled via stream sur List.of() fallback |
| Service injecté ne trouve pas `GridTradingService` (circular dep) | Faible | `OrphanOrderDetector` dépend de `GridTradingService` qui dépend de `KrakenClient` — pas de cycle |
| Race condition entre lecture Kraken et lecture `activeGrids` | Bénin | window de race ~50ms ; un faux-positif transitoire est acceptable pour un endpoint diagnostic (pas d'action automatique) |
| Faux-positifs si ordre vient d'être placé sans encore avoir sa orderId écrite dans level[] | Réel | OK — ce sont précisément les races qui créent les orphans persistants. Le faux-positif transitoire signale la race ; sa **persistance** signale l'orphan. Caller peut filtrer par âge de l'ordre (`createdTime`) si nécessaire. |

## Composition avec patch cycle 189

Les deux patches se **complètent** :
- **Cycle 189** (`stopGrid` Kraken-truth) : prévient la **naissance** d'orphans au stop d'une grille.
- **Cycle 192** (`/orders/orphans`) : détecte les orphans **présents** (legacy + bugs futurs non encore patchés).

Workflow combiné une fois déployés :
1. Routine de monitoring (skill `martin-monitor`) ajoute appel à `/api/bot/orders/orphans` toutes les N minutes.
2. Si `summary.toxic > 0` → alerte Telegram avec liste des orderIds + commandes cancel pré-générées.
3. Tony décide d'annuler manuellement ou de laisser vivre (ex : ordre attendu hors-grille).

Le patch 192 **rend le pattern cycle 191 (l'armé-en-attente) observable**. Il transforme une catégorie ontologique en métrique opérationnelle. C'est le pont entre la pensée et l'outil.

## Branche et commit suggérés

```bash
git checkout -b feat/orphan-orders-endpoint
# Apply diff
git add src/main/java/com/martin/api/dto/OrphanOrdersResponse.java \
        src/main/java/com/martin/grid/OrphanOrderDetector.java \
        src/main/java/com/martin/grid/GridTradingService.java \
        src/main/java/com/martin/api/controller/BotController.java \
        src/test/java/com/martin/grid/OrphanOrderDetectorTest.java \
        src/test/java/com/martin/api/controller/BotControllerTest.java
git commit -m "feat: add /api/bot/orders/orphans endpoint to detect armé-en-attente

Cross-reference live Kraken orders against known grid orderIds (levels + SL).
Flags reduceOnly=false orphans as toxic (can open naked position if filled).

Closes the loop with cycle 189 (stopGrid Kraken-truth audit): cycle 189
prevents orphan birth, cycle 192 makes existing orphans observable.

Motivation: orphan a216f57c-b9bf (DOT sell @ 0.9295, reduceOnly=false)
has been live ~36h+ since 2026-06-23 06:08 UTC. Tony notified via Telegram
cycle 188 but cancel command not executed yet. This endpoint surfaces
such cases proactively.

See: docs/projets/patch-orphans-detection-cycle192.md
     docs/pensees/2026-06-24-l-ordre-qui-ne-s-execute-pas.md
"
```

## Validation manuelle après déploiement

```bash
# Devrait montrer l'orphan a216f57c si toujours live :
curl -s http://localhost:8081/api/bot/orders/orphans | jq .

# Cas attendu maintenant (0 grilles actives, 1 ordre Kraken) :
# {
#   "timestamp": "...",
#   "checkedKrakenOrders": 1,
#   "knownGridOrderIds": 0,
#   "orphans": [
#     { "orderId": "a216f57c-...", "toxic": true, ... }
#   ],
#   "summary": { "total": 1, "toxic": 1, "benign": 0 }
# }
```

Une fois Tony cancel manuel de `a216f57c` (ou laisse expirer) → l'endpoint retournera `{ "orphans": [], "summary": { "total": 0 } }`. Mesure stable du système au repos.

---

**Note méta** : ce patch est le 3ème de l'arc 186-192. Cycle 189 = prévention (stopGrid). Cycle 190 = mirroir (autounstuck size). Cycle 192 = observation (orphans endpoint). La séquence forme un **trio défensif autour de la même surface** : la cohérence entre l'état Martin interne et Kraken comme source de vérité. Le pattern *Kraken = autorité, Map interne = index* est désormais codifié dans 3 endroits indépendants.

# Martin Grid — Fill Mechanism Analysis

**Date**: 2026-03-22
**Source**: Actual code on VM (`/home/ubuntu/martin/backend/src/main/java/com/martin/grid/GridTradingService.java`)
**Currently active**: PF_ADAUSD grid (live, 3 levels, 5x leverage, $25 capital)

---

## 1. Are grid orders limit (maker) or market (taker)?

**LIMIT orders (maker). Confirmed.**

```java
// GridTradingService.java line ~580
KrakenOrderRequest order = KrakenOrderRequest.builder()
        .orderType("lmt")           // <-- LIMIT order = maker
        .symbol(state.getInstrument())
        .side(level.getSide())
        .size(size)
        .limitPrice(level.getPrice())
        .reduceOnly(false)
        .build();
```

The fee constant confirms this was intentional:
```java
private static final BigDecimal MAKER_FEE_PCT = new BigDecimal("0.02");  // 0.02% maker fee
```

**Verdict**: No maker/taker problem on order placement. All grid orders are `lmt` (limit), so they pay the maker fee (0.02% on Kraken Futures), not the taker fee (0.05%).

**However**: there is NO `post_only` flag being set. On Kraken Futures, a limit order that crosses the spread will execute as a taker. The `KrakenOrderRequest` DTO does not even have a `postOnly` field. If price moves fast and a limit order is placed at or through the current market price, it fills immediately as a **taker** at the higher fee rate, but Martin still calculates fees at the maker rate. This is a minor fee leak, not a critical bug.

---

## 2. How are fills detected?

**Polling every 10 seconds. No WebSocket for fills.**

```java
@Scheduled(fixedDelay = 10000)  // every 10 seconds
public void pollGridOrders() {
    for (Map.Entry<String, GridState> entry : activeGrids.entrySet()) {
        GridState state = entry.getValue();
        if (!state.isActive()) continue;
        checkForFills(state);
        checkStopLoss(state);
        checkForRecenter(state);
    }
}
```

The fill detection method:
```java
private void checkForFills(GridState state) {
    // 1. Fetch ALL open orders from Kraken REST API
    KrakenOpenOrdersResponse response = krakenClient.getOpenOrders(state.isDemo()).block();

    // 2. Build set of currently open order IDs
    Set<String> openOrderIds = response.getOpenOrders().stream()
            .map(Order::getOrderId)
            .collect(Collectors.toSet());

    // 3. For each grid level that was PLACED: if its orderId is NO LONGER in open orders -> it filled
    for (GridLevel level : state.getLevels()) {
        if (level.getStatus() == PLACED
                && level.getKrakenOrderId() != null
                && !openOrderIds.contains(level.getKrakenOrderId())) {
            handleFill(state, level);  // <-- treat as filled
        }
    }
}
```

**The WebSocket client (`KrakenFuturesWsClient`) only subscribes to `ticker` feed** (price updates). It does NOT subscribe to `fills`, `open_orders`, or any execution channel. Fills are detected purely by polling.

### Detection method: "order disappeared = order filled"

This is the **disappearance heuristic**. Martin does NOT use the Kraken `/fills` endpoint to confirm fills during polling. It assumes that if an order ID was previously in the open orders list and is no longer there, then it filled.

**Risk**: An order can disappear from open orders for reasons other than filling:
- Manually cancelled by the user
- Cancelled by Kraken (self-trade prevention, margin call, etc.)
- API hiccup returning incomplete results

If any of these happen, Martin treats it as a fill and places a reverse order, creating a phantom position.

---

## 3. What happens when the grid recenters?

When price moves outside `[lowerBound, upperBound]`:

1. **Cancel all placed orders** on Kraken
2. **Log orphaned buy fills** (positions still open on Kraken that will be abandoned)
3. **Rebuild the entire grid** around the new price
4. **Place all new orders**

```java
private void checkForRecenter(GridState state) {
    if (currentPrice > state.getUpperBound() || currentPrice < state.getLowerBound()) {
        // Cancel all orders
        for (GridLevel level : state.getLevels()) {
            if (level.getStatus() == PLACED && level.getKrakenOrderId() != null) {
                cancelOrder(level.getKrakenOrderId(), state.isDemo());
            }
            // Warn about orphaned buy fills (open longs that will be forgotten)
            if (level.isHasBuyFill() && level.getStatus() == FILLED) {
                log.warn("orphaned buy fill at level...");
                // Records it but does NOT close the position
            }
        }
        // Rebuild grid from scratch
        state.setLevels(newLevels);
        placeAllOrders(state);
    }
}
```

**Critical issue**: On recenter, if Martin holds an open long position from a previous buy fill, that position stays open on Kraken but Martin loses track of it. The comment says "please close manually or rely on stop-loss." **No automatic market-sell to flatten the position.**

### Historical recenter bug (now fixed but was active)

The logs show a prior recenter loop where the range was `[0.3, 0.3]` for ADA at price ~0.254. This happened 8 times in a row every 10 seconds. This was a rounding bug where the range collapsed to a single value, causing infinite recentering. The current instance (PID 423683) shows this was fixed.

---

## 4. Could fills be missed?

**Yes, in several scenarios:**

### Scenario A: Fill between polls (10s window)
If a buy fills and price immediately reverses, Martin won't know for up to 10 seconds. Not critical by itself, but combined with Scenario C, it creates risk.

### Scenario B: Race condition on order placement
Orders are placed with `.subscribe()` (async, non-blocking). The `krakenOrderId` is set inside the callback. If `pollGridOrders` runs before the callback fires, the level has `krakenOrderId == null` and `status == WAITING` (or still being set), so it's invisible to the fill checker.

```java
krakenClient.sendOrder(order, state.isDemo())
    .publishOn(Schedulers.boundedElastic())
    .subscribe(r -> {
        // This runs LATER, async
        level.setKrakenOrderId(r.getSendStatus().getOrderId());
        level.setStatus(GridLevel.GridLevelStatus.PLACED);
    }, ...);
```

If the order fills on Kraken before the callback sets `krakenOrderId`, that fill is **permanently lost**. Martin never records it, the position stays open on Kraken, but Martin doesn't know about it.

### Scenario C: Order cancelled (not filled) but treated as fill
As described above — the disappearance heuristic is fragile.

### Scenario D: Recenter orphans
Confirmed by the code and logs. On recenter, open positions from filled buy orders are logged but NOT closed. If price recenters multiple times, these orphan positions accumulate silently.

---

## 5. Summary of findings

| Question | Answer |
|----------|--------|
| Order type | `lmt` (limit/maker) -- correct |
| Post-only flag | **Missing** -- limit orders can cross as taker |
| Fill detection | Polling every 10s, "order disappeared = filled" heuristic |
| WebSocket fills | **Not used** -- WS only for ticker/price |
| Recenter behavior | Cancel all + rebuild grid. **Open positions orphaned.** |
| Can fills be missed? | **Yes** -- async race condition, false fills from cancellations |

## 6. Recommended fixes (priority order)

### P0: Add `post_only` flag to order request
Prevents limit orders from crossing as taker. Add `postOnly` field to `KrakenOrderRequest` and set it to `true` for all grid orders. Kraken will reject the order instead of filling it as taker.

### P1: Confirm fills with `/fills` endpoint
After detecting an order disappeared, call `krakenClient.getFills()` and verify the order actually filled (match by orderId). If it wasn't in fills, treat it as cancelled, not filled.

### P2: Close orphans on recenter
When recentering detects `hasBuyFill == true` on a level, place a market sell to close the position instead of just logging a warning.

### P3: Use WebSocket fills channel
Subscribe to the authenticated `fills` feed on the WebSocket instead of polling. This gives sub-second fill detection and eliminates the 10s delay.

### P4: Make order placement synchronous
Use `.block()` instead of `.subscribe()` for `sendOrder()`, or at least wait for the callback before marking the level as PLACED. This eliminates the async race condition.

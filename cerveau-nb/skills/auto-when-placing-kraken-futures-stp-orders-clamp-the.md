---
activations: 0
created: '2026-05-12'
last_used: null
name: auto-when-placing-kraken-futures-stp-orders-clamp-the
session_origin: null
source: tool_failure
status: draft
type: auto-skill
---

When placing Kraken Futures stp orders, clamp the stopPrice to be at least MIN_STOP_DISTANCE_PCT (1.5%) from the CURRENT MARK PRICE, not just from entry. Fetch current mark via /api/v3/tickers before placing.

**Contexte :** StopLossManager places stp orders clamped to MIN_STOP_DISTANCE_PCT from entryAvg, but Kraken Futures silently rejects stp orders too close to current MARK price. Result: 1860+ vanish failures on DOT, position unprotected.
**Cause :** Clamp computed from entryAvg, but Kraken validates distance vs current mark price. As position DCA's down, entry moves but current price falls faster — stops computed safe from entry can be too close to mark and get silently rejected.
**Noeuds liés :** martin, stoploss, kraken-futures, tick-size, min-distance

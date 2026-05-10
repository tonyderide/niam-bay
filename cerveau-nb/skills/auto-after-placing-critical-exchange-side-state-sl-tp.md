---
activations: 0
created: '2026-05-10'
last_used: null
name: auto-after-placing-critical-exchange-side-state-sl-tp
session_origin: null
source: tool_failure
status: draft
type: auto-skill
---

After placing critical exchange-side state (SL, TP, stop orders), always verify via openorders endpoint OR cancel-test that the order is actually live. Never trust 'success+orderId' as proof of persistent state.

**Contexte :** Martin StopLossManager.place() Java method received Kraken success response with orderId, but the order didn't actually exist on Kraken (cancel test returned 'notFound'). Bot stored fake orderId in grid state for hours, thought SL was active, but no SL was actually live on Kraken. Tony asked 'are the SL working?' which triggered investigation.
**Cause :** Java side trusted Kraken response success+orderId without verifying the order persists in /api/v3/openorders. Martin's BotController.cancelOrder line 167 also returned 'Cancelled' without checking the response status, masking the real bug for hours.
**Noeuds liés :** martin, stoploss, kraken-futures, java-bridge, verification

---
activations: 0
created: '2026-05-10'
last_used: null
name: auto-java-rest-endpoints-that-delegate-to-external-apis
session_origin: null
source: tool_failure
status: draft
type: auto-skill
---

Java REST endpoints that delegate to external APIs must inspect the actual response status, not just absence of exceptions. Return distinct codes/messages for success vs notFound vs failure.

**Contexte :** Java cancelOrder endpoint at /home/tony/projets/tonyderide/martin/src/main/java/com/martin/api/controller/BotController.java line 167 returns 'Cancelled: <id>' for ANY input, without checking if Kraken actually cancelled the order. Returns success even when Kraken says 'notFound'. Hid the underlying StopLossManager bug for hours.
**Cause :** BotController.cancelOrder catches exceptions but doesn't inspect response.cancelStatus.status — wraps everything as success.
**Noeuds liés :** martin, java, rest, error-handling, kraken

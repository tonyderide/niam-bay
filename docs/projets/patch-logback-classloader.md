# Patch — Logback `ThrowableProxy` classloader leak (Mono.block hang)

**Auteur** : Niam-Bay cycle 66 (2026-05-20 12h25 Paris)
**Trigger** : cycle 65 root-cause analysis. Bug auto-aggravant qui mute le bot après ~30h d'uptime.
**Status** : patch sketché, **non déployé**. Tony review au retour.

---

## Résumé exécutif (1 paragraphe)

À T+30h d'uptime, la première exception remontant dans le pipeline reactor-netty déclenche un `LoggingEvent.<init>` qui tente de charger `ch/qos/logback/classic/spi/ThrowableProxy`. La classe est dans le jar mais le classloader event-loop ne la trouve pas. JVM marque la classe en "initialization failed" et toute tentative ultérieure jette `NoClassDefFoundError`. Cascade : le `Mono` retourné par les calls Kraken signed reste en `parking` indéfiniment. Chaque thread Tomcat appelant `.block()` se fige. À ~10 hangs/h, le pool 200 threads est exhausted en ~6h et tout l'HTTP meurt. Restart martin.service = retour à T=0, cycle recommence. Diag complet : cycle 65 `vacation-autonomy.md` ligne 4372+.

## Verdict architecture

3 patches independants, defense in depth. Aucun n'invalide les autres, ils s'empilent :

| Patch | Cible | Risque déploiement | Lignes |
|---|---|---|---|
| **A — Eager preload** | Root cause (classloader) | Faible — 4 lignes dans `main()` | 4 |
| **B — block(Duration)** | Symptôme (thread leak) | Moyen — touche 13 sites | ~20 |
| **C — Deep health** | Observabilité | Faible — endpoint additif | ~30 |
| **D — Logback downgrade** | Fallback | Faible — 1 ligne pom | 1 |

**Reco** : déployer A+B+C ensemble. D en réserve si A ne suffit pas après 48h d'uptime de test.

---

## Patch A — Eager classloader preload (root cause)

**Fichier** : `src/main/java/com/martin/MartinApplication.java`

### Diff

```diff
 package com.martin;

 import org.springframework.boot.SpringApplication;
 import org.springframework.boot.autoconfigure.SpringBootApplication;
 import org.springframework.context.annotation.Bean;
 import org.springframework.scheduling.annotation.EnableScheduling;

 import java.time.Clock;

 @SpringBootApplication
 @EnableScheduling
 public class MartinApplication {
     public static void main(String[] args) {
+        // PATCH 2026-05-20: preload logback exception-formatting classes in MAIN classloader
+        // before any reactor-netty event loop thread exists. Fixes NoClassDefFoundError
+        // ThrowableProxy cascade after T+30h uptime (cycle 65 root-cause).
+        try {
+            Class.forName("ch.qos.logback.classic.spi.ThrowableProxy");
+            Class.forName("ch.qos.logback.classic.spi.ThrowableProxyUtil");
+            Class.forName("ch.qos.logback.classic.spi.StackTraceElementProxy");
+            Class.forName("ch.qos.logback.classic.spi.PackagingDataCalculator");
+        } catch (ClassNotFoundException e) {
+            System.err.println("PRELOAD FAILED — logback classes missing from jar: " + e);
+        }
         SpringApplication.run(MartinApplication.class, args);
     }

     @Bean
     public Clock systemClock() {
         return Clock.systemUTC();
     }
 }
```

### Pourquoi ça marche

- `Class.forName` force la résolution complète (link + init) de la classe via le classloader courant, qui est `LaunchedURLClassLoader` (Spring Boot fat-jar) au moment du `main()`.
- Une fois résolue, la classe est en état `INITIALIZED` dans le JVM class registry. Toutes les requests ultérieures (même depuis un classloader child reactor-netty) trouvent la classe via parent delegation.
- Coût : ~50 ms au démarrage, 0 ms en runtime.

### Test de non-régression

- `mvn test` : 131 tests doivent passer.
- Démarrage local : vérifier `app.log` n'a pas `PRELOAD FAILED`.
- Démarrage prod : `uptime` doit dépasser 48h sans NoClassDefFoundError dans `app.log` (vs 30h avant).

---

## Patch B — `block(Duration)` partout (safety net)

**Principe** : remplacer `.block()` sans timeout par `.block(Duration.ofSeconds(N))`. Si un `Mono` reste pending pour quelque raison que ce soit (Patch A miss, bug Kraken, réseau coupé), le thread Tomcat se libère après N secondes au lieu de parker indéfiniment.

### Sites à patcher (13 calls totaux dans le code Kraken)

#### B.1 — `BotController.java` (5 sites)

```diff
@@ ligne 152 @@ getOpenPositions
-        KrakenPositionResponse response = krakenClient.getOpenPositions(demo).block();
+        KrakenPositionResponse response = krakenClient.getOpenPositions(demo).block(Duration.ofSeconds(15));

@@ ligne 166 @@ cancelOrder
-            var response = krakenClient.cancelOrder(orderId, demo).block();
+            var response = krakenClient.cancelOrder(orderId, demo).block(Duration.ofSeconds(10));

@@ ligne 186 @@ getOpenOrders
-        KrakenOpenOrdersResponse response = krakenClient.getOpenOrders(demo).block();
+        KrakenOpenOrdersResponse response = krakenClient.getOpenOrders(demo).block(Duration.ofSeconds(15));

@@ ligne 220 @@ getAccountBalance
-            var response = krakenClient.getAccounts(demo).block();
+            var response = krakenClient.getAccounts(demo).block(Duration.ofSeconds(15));

@@ ligne 236 @@ getOhlc
-            var response = krakenClient.getOhlc(instrument, minutes).block();
+            var response = krakenClient.getOhlc(instrument, minutes).block(Duration.ofSeconds(20));
```

Ajout import en haut du fichier :
```diff
+import java.time.Duration;
```

#### B.2 — `KrakenFuturesRestClient.java` (3 sites)

```diff
@@ ligne 205 @@ ensureCollateralEnabled (background pre-flight)
-            java.util.Map<?, ?> accountResp = getAccounts(demo).block();
+            java.util.Map<?, ?> accountResp = getAccounts(demo).block(Duration.ofSeconds(15));

@@ ligne 206 @@
-            KrakenPositionResponse posResp = getOpenPositions(demo).block();
+            KrakenPositionResponse posResp = getOpenPositions(demo).block(Duration.ofSeconds(15));

@@ ligne 261 @@ getTickers helper
-            KrakenTickerResponse resp = getTickers(demo).block();
+            KrakenTickerResponse resp = getTickers(demo).block(Duration.ofSeconds(10));
```

#### B.3 — `StopLossManager.java` (5 sites)

Ces calls sont **critiques pour le SL**. Timeout suffisamment long pour ne pas rater un fill mais court pour libérer threads en cas de bug.

```diff
@@ ligne 139 @@ place SL
-            KrakenOrderResponse resp = krakenClient.sendOrder(req, state.isDemo()).block();
+            KrakenOrderResponse resp = krakenClient.sendOrder(req, state.isDemo()).block(Duration.ofSeconds(10));

@@ ligne 194 @@ getTickers
-            KrakenTickerResponse resp = krakenClient.getTickers(demo).block();
+            KrakenTickerResponse resp = krakenClient.getTickers(demo).block(Duration.ofSeconds(10));

@@ ligne 230 @@ verify openorders
-                var resp = krakenClient.getOpenOrders(demo).block();
+                var resp = krakenClient.getOpenOrders(demo).block(Duration.ofSeconds(10));

@@ ligne 250 @@ cancel orphan SL
-            krakenClient.cancelOrder(id, state.isDemo()).block();
+            krakenClient.cancelOrder(id, state.isDemo()).block(Duration.ofSeconds(10));

@@ ligne 316 @@ verify position
-            KrakenPositionResponse resp = krakenClient.getOpenPositions(state.isDemo()).block();
+            KrakenPositionResponse resp = krakenClient.getOpenPositions(state.isDemo()).block(Duration.ofSeconds(10));
```

### Gestion de `IllegalStateException` (Mono completed without value)

`block(Duration)` lève `IllegalStateException` si timeout atteint. Le code actuel n'attrape PAS ça partout. Audit :

- `BotController.getOpenPositions` (ligne 152) : pas de try/catch → 500 propagé au client. Acceptable.
- `BotController.cancelOrder` (ligne 165-179) : déjà dans try/catch Exception. OK.
- `BotController.getAccountBalance` (ligne 219-225) : try/catch Exception. OK.
- `BotController.getOhlc` (ligne 235-238) : try/catch Exception. OK.
- `BotController.getOpenOrders` (ligne 186) : pas de try/catch → 500. Acceptable.

**Action** : wrapper `getOpenPositions` et `getOpenOrders` dans BotController avec try/catch pour ne pas remonter une 500 brute :

```java
@GetMapping("/positions")
public ResponseEntity<List<KrakenPositionResponse.Position>> getOpenPositions(...) {
    try {
        KrakenPositionResponse response = krakenClient.getOpenPositions(demo).block(Duration.ofSeconds(15));
        ...
    } catch (IllegalStateException timeout) {
        log.warn("Kraken positions timeout 15s");
        return ResponseEntity.status(504).body(List.of());
    }
}
```

Idem pour `getOpenOrders`.

### Test de non-régression

- `mvn test` complet (TradingOrchestratorTest, BotControllerTest si présent).
- Smoke test sur testnet : timeout artificiel via `tc qdisc add dev lo root netem delay 20000ms` puis hit `/api/bot/balance`. Doit return 504 en 15s, pas hang.
- Production : critical-check.py cron 5min ne doit jamais voir timeout > 30s sur `/api/bot/balance`.

---

## Patch C — Deep health endpoint (observabilité)

**Principe** : ajouter `/api/system/health/deep` qui fait un roundtrip Kraken signed avec timeout court. Le cron `critical-check.py` peut hit cet endpoint pour savoir si l'API Kraken bridge est vivante, indépendamment du business state.

### Fichier : `BotController.java` (ou nouveau `SystemController.java`)

```java
@GetMapping("/api/system/health/deep")
public ResponseEntity<?> healthDeep() {
    long start = System.currentTimeMillis();
    java.util.Map<String, Object> result = new java.util.HashMap<>();
    result.put("status", "UP");
    result.put("uptime_ms", System.currentTimeMillis() - startupTime);

    try {
        // Lightweight signed Kraken call — accounts is mandatory for any trading
        var resp = krakenClient.getAccounts(false).block(Duration.ofSeconds(5));
        long latency = System.currentTimeMillis() - start;
        result.put("kraken_signed", "OK");
        result.put("kraken_latency_ms", latency);
        if (latency > 3000) {
            result.put("status", "DEGRADED");
        }
    } catch (IllegalStateException timeout) {
        result.put("kraken_signed", "TIMEOUT_5S");
        result.put("status", "CRITICAL");
        return ResponseEntity.status(503).body(result);
    } catch (Exception e) {
        result.put("kraken_signed", "ERROR");
        result.put("kraken_error", e.getMessage());
        result.put("status", "CRITICAL");
        return ResponseEntity.status(503).body(result);
    }

    return ResponseEntity.ok(result);
}
```

### Update du cron `critical-check.py` côté VM

Ajouter en début du script :
```python
# 2026-05-20: deep health check fast-fails if bridge dies before any business check
deep = http_get(f"{base}/api/system/health/deep", timeout=8)
if deep["status"] != "UP":
    telegram_alert(f"⚠️ Martin bridge DEGRADED/CRITICAL — {deep.get('kraken_signed', '?')} latency={deep.get('kraken_latency_ms', '?')}ms")
    sys.exit(2)
```

### Cohérence avec cycle 65

Le cycle 65 a découvert que critical-check.py est **aveugle** car il hit `/bot/balance` qui timeout silencieusement. Patch C donne au cron un endpoint qui fail-fast en 5s avec un statut clair, plutôt que d'attendre 60s pour deviner que l'API est morte.

---

## Patch D — Logback downgrade (réserve)

Si Patch A ne suffit pas après 48h d'uptime de test, downgrade logback comme dernier recours.

### Diff `pom.xml`

```diff
@@ properties block @@
     <properties>
         <java.version>21</java.version>
+        <logback.version>1.5.13</logback.version>
     </properties>
```

Spring Boot 3.4.3 utilise `<logback.version>1.5.16</logback.version>` par défaut (depuis Jan 2025). 1.5.13 = dernière version connue stable avant la série 1.5.14+ (Jan 2025) qui a refactoré certaines internals de `LoggingEvent`/`ThrowableProxy`. Override via property suffit.

### Validation post-downgrade

- `mvn dependency:tree | grep logback` : doit afficher 1.5.13.
- Tests passent.
- Démarrage : pas de warning de version.

**Note** : ce patch est conservateur. Si la cause profonde est dans 1.5.16, A peut ne pas être suffisant et D devient nécessaire. Mais A est plus propre car indépendant de la version.

---

## Ordre de déploiement recommandé

1. **Backup** : `cp backend.jar backend.jar.bak-pre-patch-66-$(date +%s)` sur VM.
2. **Déployer A+B+C ensemble** dans un commit unique avec message clair.
3. **Build local** : `mvn package -DskipTests=false`. Tous tests verts.
4. **scp + restart** : `scp backend.jar ubuntu@VM:/home/ubuntu/martin/backend.jar && ssh ubuntu@VM "sudo systemctl restart martin"`.
5. **Smoke immédiat** : `curl -s http://VM:8081/api/system/health/deep`. Doit return UP avec latence Kraken < 1s.
6. **Surveillance 48h** : laisser tourner, suivre `app.log` pour `NoClassDefFoundError`. Si 0 occurrence après 48h → root cause neutralisé. Si occurrence → activer Patch D (downgrade logback).

## Rollback

- Si bot ne démarre pas : `cp backend.jar.bak-pre-patch-66-* backend.jar && sudo systemctl restart martin`. Retour à l'état cycle 65.
- Si tests prod régressent (latence Kraken increase > 50%) : rollback identique.

## Tests d'acceptation

- [ ] `mvn test` passe (131 tests).
- [ ] Smoke local : `/api/system/health/deep` répond < 6s, status UP.
- [ ] Smoke prod post-deploy : 4 endpoints `/api/bot/*` répondent < 20s chacun.
- [ ] Uptime > 48h sans `NoClassDefFoundError` dans `app.log`.
- [ ] Aucun thread Tomcat avec elapsed > 60s sur `Mono.block` dans `jcmd Thread.print`.
- [ ] critical-check.py cron Telegram alerte si `health/deep` != UP.

## Risques

1. **Patch B peut révéler des bugs cachés** : si certaines opérations Kraken prennent réellement > 15s (rare mais possible en latence Amsterdam→US), elles vont timeout 504. Mitigation : monitorer les 504 sur 24h post-deploy, ajuster timeouts si > 1% des calls.
2. **Patch A peut ne pas suffire** : si la cause est non-logback (par ex. un thread BlockHound issue), A reste un no-op. Mitigation : Patch B garantit que les threads ne hang plus, même si A miss.
3. **Patch C cron update** : si critical-check.py update mal poussé, le cron ne change rien. Mitigation : tester `/api/system/health/deep` manuellement avant d'update le cron.

## Note pour Tony

Le bot vient d'être restart (uptime 2h26 au moment de l'écriture, 2026-05-20 12h25 CEST). Le bug va revenir dans ~30h, soit **vers le 21/05 18h00 CEST**. Si tu veux patcher avant la prochaine occurrence, déploie A+B+C avant cette deadline.

L'urgence n'est pas critique parce que le restart suffit comme workaround temporaire (zéro perte démontrée cycle 65 → cycle 66). Mais sans patch, le cycle restart/30h est un risque permanent.

— Niam-Bay, cycle 66

# Patch proposal — AUTO-UNSTUCK trim must round to Kraken size step

**Date** : 2026-06-24 (cycle 190, 04h23 UTC / 06h23 CEST)
**Auteur** : Niam-Bay (autonomy mode)
**Statut** : PROPOSITION — pas de modification code, pas de deploy
**Sévérité** : MEDIUM — safety-net dégradé (lvl1+lvl2 trim), mais lvl3 full-close fonctionne (étage grossier)
**Vit-on avec le bug ?** : oui, lvl3 close passe ; mais arc cycle 187 a coûté -$1.14 sur 6h parce que le filet fin n'a pas retenu.

---

## 1. Observation

Cycle 187 (`2026-06-23 08:24:28 UTC`) :

```
AUTO-UNSTUCK trim REJECTED by Kraken: PF_DOTUSD status=invalidSize result=success — position stays 60.7 (next tick will retry)
AUTO-UNSTUCK trim REJECTED by Kraken: PF_DOTUSD status=invalidSize result=success — position stays 60.7 (next tick will retry)
```

3 minutes plus tard, Tony close manuel via `/grid/stop` (60.7 → 0, accepté).

**Asymétrie** : le filet fin (trim 25% = 15.175) échoue ; le filet grossier (close 100% = 60.7) passe. Conformément à la pensée *« Le métronome dans la chute »* cycle 187 — l'étage grossier survit, l'étage fin tombe.

## 2. Root cause

### 2.1 Code fautif

`GridTradingService.trimPositionPartial` lignes 914-958 :

```java
double trimSize = Math.abs(pos.getSize()) * fraction;
if (trimSize < 1e-6) continue;
String closeSide = "long".equalsIgnoreCase(pos.getSide()) ? "sell" : "buy";
KrakenOrderRequest trimOrder = KrakenOrderRequest.builder()
        .orderType("mkt")
        .symbol(state.getInstrument())
        .side(closeSide)
        .size(trimSize)            // ⚠️ envoyé tel quel, non-arrondi
        .reduceOnly(true)
        .build();
```

### 2.2 Mécanisme Kraken Futures

Endpoint `https://futures.kraken.com/derivatives/api/v3/instruments` retourne pour chaque symbole un champ **`contractValueTradePrecision`** = nombre de décimales autorisées pour `size` :

| Symbole       | contractValueTradePrecision | step équivalent |
|---------------|------------------------------|-----------------|
| PF_XBTUSD     | 4                            | 0.0001          |
| PF_ETHUSD     | 3                            | 0.001           |
| PF_DOTUSD     | 1                            | 0.1             |
| PF_LINKUSD    | 1                            | 0.1             |
| PF_SOLUSD     | 2                            | 0.01            |
| PF_ADAUSD     | 0                            | 1               |
| PF_XRPUSD     | 0                            | 1               |
| PF_XLMUSD     | 0                            | 1               |

Reproduction du bug :
- `60.7 × 0.25 = 15.175` → 3 décimales → `invalidSize`
- `60.7` (close 100%) → 1 décimale → accepté
- Order orphelin `a216f57c` size **5.9** → 1 décimale → accepté

### 2.3 Lacune existante du cache

`KrakenInstrumentsCache.refresh()` (lignes 46-65) ne parse **que `tickSize`** dans le payload `/instruments`. Le champ `contractValueTradePrecision` est ignoré.

`KrakenTickSize.java` (cycle 55, extraction post-incident SL VANISH BTC) ne gère **que les prix**.

Aucun équivalent `KrakenSizeStep.java`.

### 2.4 Précédent partiel — ScalpingBotService

`ScalpingBotService.roundSize` lignes 852-856 hardcode trois cas (XBT 4 dec, ETH 3 dec, default 4 dec). Insuffisant : DOT/LINK auraient besoin de 1 dec ; ADA/XRP/XLM de 0. Le default 4 décimales aurait produit `15.175` exactement comme le bug observé.

C'est le **même bug-class** que SL VANISH BTC cycle 54 (rounding heuristique vs source de vérité Kraken). Le patch cycle 55 a corrigé pour les **prix** mais a laissé la moitié size de la maison.

## 3. Fix proposé — defense in depth

Principe miroir du patch cycle 55 :
1. **Source de vérité** : étendre `KrakenInstrumentsCache` pour stocker `sizePrecision` à côté de `tickSize`.
2. **Util partagé** : créer `KrakenSizeStep.java` (parallèle à `KrakenTickSize.java`).
3. **Application minimale** : appeler l'util dans `trimPositionPartial` *avant* le POST.
4. **Direction d'arrondi** : `DOWN` (pas `HALF_UP`) — on ne veut **jamais** trim plus que la fraction demandée (sinon on flatten au-delà du safety-net).
5. **Garde min-size** : si `trimSize` arrondi DOWN = 0, skip (laisser tick suivant retry quand position aura grossi).

### 3.1 Étape A — `KrakenInstrumentsCache` (extension non breaking)

```java
private final Map<String, BigDecimal> tickSizes = new ConcurrentHashMap<>();
private final Map<String, Integer> sizePrecisions = new ConcurrentHashMap<>();   // NEW

// dans refresh(), boucle for inst :
JsonNode prec = inst.get("contractValueTradePrecision");
if (prec != null && prec.canConvertToInt()) {
    sizePrecisions.put(sym, prec.asInt());
}

/** Returns the live size precision (number of decimals), or null if unknown. */
public Integer getSizePrecision(String symbol) {                                  // NEW
    return sizePrecisions.get(symbol);
}
```

### 3.2 Étape B — `KrakenSizeStep.java` (nouveau fichier)

```java
package com.martin.kraken.util;

import com.martin.kraken.service.KrakenInstrumentsCache;
import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * Shared size-step resolution + size rounding for Kraken Futures.
 *
 * Cycle 190 (2026-06-24) — created after AUTO-UNSTUCK invalidSize incident
 * cycle 187 (DOT 15.175 rejected). Same drift class as cycle 54 SL VANISH
 * BTC but on the size axis: ScalpingBotService.roundSize had a hardcoded
 * 3-case heuristic that would have produced the same bug.
 *
 * Resolution order:
 *  1. live contractValueTradePrecision from {@link KrakenInstrumentsCache}
 *  2. {@link #fallbackPrecision(String)} per-instrument hardcoded map
 *
 * Always rounds DOWN (HALF_DOWN-equivalent for positive sizes) — we never
 * want to flatten more than the caller asked for.
 */
public final class KrakenSizeStep {

    private KrakenSizeStep() {}

    public static int resolvePrecision(KrakenInstrumentsCache cache, String instrument) {
        if (cache != null) {
            Integer cached = cache.getSizePrecision(instrument);
            if (cached != null && cached >= 0) {
                return cached;
            }
        }
        return fallbackPrecision(instrument);
    }

    /**
     * Round a size DOWN to the live precision. Never returns negative.
     * Caller MUST guard against zero-result (skip the order if so).
     */
    public static double roundDown(KrakenInstrumentsCache cache, String instrument, double size) {
        int precision = resolvePrecision(cache, instrument);
        return BigDecimal.valueOf(size)
                .setScale(precision, RoundingMode.DOWN)
                .doubleValue();
    }

    /**
     * Per-instrument fallback when cache has no entry (boot race, Kraken down).
     * Mirrors /derivatives/api/v3/instruments as of 2026-06-24.
     */
    public static int fallbackPrecision(String instrument) {
        if (instrument == null) return 4;
        if (instrument.contains("XBT")) return 4;
        if (instrument.contains("ETH")) return 3;
        if (instrument.contains("SOL")) return 2;
        if (instrument.contains("DOT") || instrument.contains("LINK")) return 1;
        if (instrument.contains("ADA") || instrument.contains("XRP")
                || instrument.contains("XLM")) return 0;
        return 4;
    }
}
```

### 3.3 Étape C — `trimPositionPartial` (modification minimale ligne 926-933)

```java
double trimSize = Math.abs(pos.getSize()) * fraction;
trimSize = KrakenSizeStep.roundDown(instrumentsCache, state.getInstrument(), trimSize);
if (trimSize < 1e-9) {
    log.warn("AUTO-UNSTUCK trim skipped: {} fraction={} rounded to 0 (position {} too small for step)",
            state.getInstrument(), fraction, pos.getSize());
    continue;
}
String closeSide = "long".equalsIgnoreCase(pos.getSide()) ? "sell" : "buy";
KrakenOrderRequest trimOrder = KrakenOrderRequest.builder()
        .orderType("mkt")
        .symbol(state.getInstrument())
        .side(closeSide)
        .size(trimSize)
        .reduceOnly(true)
        .build();
```

Dépendance : `instrumentsCache` est déjà injecté dans `GridTradingService` pour le rounding price (cf. cycle 55). Aucun nouveau bean.

### 3.4 Étape D — alignement opportuniste

Même pattern doit être appliqué à **`ScalpingBotService.roundSize`** (lignes 852-856) qui aujourd'hui hardcode 3 cas et utiliserait 4 décimales pour DOT → produirait le bug si jamais un scalp DOT est envoyé. Remplacer par :

```java
private double roundSize(double size, String instrument) {
    return KrakenSizeStep.roundDown(instrumentsCache, instrument, size);
}
```

Sous condition d'injection du cache dans `ScalpingBotService` (probable petit refactor — vérifier au moment d'implémenter).

## 4. Test plan

### 4.1 Unitaires `KrakenSizeStepTest`

| Test | Input | Expected |
|------|-------|----------|
| `roundDown(DOT, 15.175)` | DOT precision 1 | 15.1 |
| `roundDown(DOT, 5.9)` | passthrough | 5.9 |
| `roundDown(ADA, 1247.6)` | precision 0 | 1247 |
| `roundDown(XBT, 0.00012345)` | precision 4 | 0.0001 |
| `roundDown(XBT, 0.00009999)` | precision 4 | 0.0000 → guard skip |
| `resolvePrecision(unknown_PF_XYZUSD)` | fallback | 4 |
| `resolvePrecision(null)` | fallback | 4 |
| `roundDown` strictement < input | rounding direction | toujours `<=` |

### 4.2 Unitaire `GridTradingServiceAutoUnstuckTest` (extension)

| Test | Setup | Expected |
|------|-------|----------|
| trim 25% DOT 60.7 | precision 1 | order sent size=15.1 (vs 15.175) |
| trim 25% DOT 0.3 | rounded to 0 | order NOT sent, `state.unstuckLevel1Done` false (re-armé tick suivant) |
| trim 100% ADA 247.5 | precision 0 | order sent size=247 |
| cache miss + fallback DOT | cache empty | utilise fallbackPrecision = 1 |

### 4.3 Régression cycle 187 (replay log)

Injecter dans `app.log` une ligne synthétique `position 60.7` puis appeler le tick AUTO-UNSTUCK lvl1. Vérifier que l'ordre envoyé porte size=15.1 et que Kraken sandbox accepte. Reproduire en mode `demo=true`.

### 4.4 Tests existants

131 tests existants doivent passer sans modification. Aucune signature publique changée.

## 5. Risques évalués

| Risque | Évaluation | Mitigation |
|--------|------------|-----------|
| Round DOWN amène trim=0 sur petite position | possible (ex DOT 0.3, ADA <1) | log.warn + skip ; tick suivant retry quand position grossit ; lvl3 close 100% reste filet grossier |
| Cache non chargé au boot | possible <60s post-restart | fallback hardcodé couvre les 8 paires actuelles |
| Nouveau symbole non listé dans fallback | possible si Tony ajoute une paire | fallback default=4 décimales suffit pour la majorité des paires Kraken |
| Refactor ScalpingBot crée régression scalping | LOW | tests existants ScalpingBotService doivent passer |
| `setScale(0, DOWN)` retourne entier exact | OK (`BigDecimal.valueOf(247.5).setScale(0, DOWN) == 247`) | testé unitaire |
| Race cache.refresh() vs trim simultané | LOW | ConcurrentHashMap, lecture lock-free |

## 6. Estimation

| Phase | Effort |
|-------|--------|
| Code (3 fichiers : cache extension + util neuf + trim 4 lignes) | 25 min |
| Tests (unitaires + intégration demo) | 45 min |
| Refactor ScalpingBotService.roundSize | 15 min |
| Documentation + commit | 10 min |
| **Total** | **~1h35** |

Pas de breaking change. Pas de migration. Pas de redeploy strategy.json.

## 7. Cohérence avec patch cycle 189

Cycle 189 a livré `patch-stopgrid-kraken-truth-cycle189.md` (PASSE 1 Kraken-truth + PASSE 2 Map-idempotente). Cycle 190 réutilise exactement la même grammaire :

- Source de vérité Kraken (cache.getSizePrecision) > heuristique locale (hardcoded decimals)
- Util statique partagé (KrakenSizeStep) > duplication (ScalpingBotService.roundSize + futur ailleurs)
- Defense in depth : cache live + fallback hardcodé + guard zero-trim

C'est la **2ème application** du principe d'étages fin/grossier formulé dans la pensée *« Le métronome dans la chute »* (cycle 187). Le mode 1+5 produit désormais des patch-proposals qui s'**outillent mutuellement** par la conceptualisation antérieure (pensée → fragment → patch → patch).

## 8. Application descendante

Le patch corrige aussi (par transitivité) tout futur point d'envoi d'ordre size-sensible non encore identifié, à condition que l'auteur passe par `KrakenSizeStep.roundDown` au lieu de redériver une heuristique. Le mémoire `lesson_kraken_size_step_canonical.md` candidat sera créé au dream.

## 9. Critère de mise au stock

Patch à mettre au stock **après** review Tony, sauf si :
- Tony juge la sévérité MEDIUM excessive (lvl3 reste filet grossier intact) → revoir priorité
- Tony préfère élargir le scope (audit complet de toutes les positions Kraken-API) → expansion design doc séparé

Sinon : feu vert pour implémentation au prochain bloc tranquille (1h35 estimé).

---

**Référence narrative** : ce patch ferme l'ouverture diagnostique de la pensée 187 et du fragment 050. Le métronome ne sera pas modifié, mais le filet fin qui l'entoure cessera de se déchirer sur ses propres conditions implicites.

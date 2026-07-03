# Forensics — SHORT XBT micro sans SL contre golden cross fraîchement confirmé

**Date** : 3 juillet 2026, 18h23 CEST
**Cycle NB** : 206 (cycle 13 post-décimal 194-203)
**Auteur** : Niam-Bay en observation passive vacation
**Statut** : document forensique, non-prescriptif, frontière vacation Martin respectée à 100%

---

## 1. Setup observé (Kraken source of truth)

- Position : `PF_XBTUSD` SHORT `0.0005` @ `$59 962` — notional ≈ $30
- Order live : 1 seul → TP buy stop `$58 500` reduceOnly
- **Aucun SL visible dans `/api/bot/orders`**
- uPnL courant : **−$1.04** (BTC $62 022, entry +3.44% adverse pour SHORT)
- Portfolio : $107.10 | margin equity $107.09 | IM $3.00 | availableMargin $105.13

## 2. Timeline régime API BTC (source `/api/signal/ema_trend`)

| Cycle | Heure | BTC | EMA50 | EMA200 | Régime | RSI |
|---|---|---|---|---|---|---|
| 203 | 0702:00h23 | $61 077 | $59 429 | $60 325 | DOWNTREND | 74.16 |
| 204 | 0703:00h23 | $61 465 | $60 475 | $60 588 | DOWNTREND | 60.11 |
| 205 | 0703:06h23 | $61 317 | $60 665 | $60 549 | **UPTREND** (golden cross triggered) | 54.78 |
| 206 | 0703:18h23 | $62 022 | $61 115 | $60 565 | UPTREND (consolidé, EMA50/200 écart +$550) | 62.28 |

**Observation clé** : le golden cross s'est produit *entre cycle 204 et cycle 205* (fenêtre 6h nuit), pendant que Tony dormait. Cycle 206 confirme le régime UPTREND consolidé (EMA50 s'écarte progressivement de l'EMA200), et le RSI est passé de 54.78 → 62.28 (accélération haussière).

## 3. Analyse cushion (dépendance à la taille micro)

| Scénario BTC | uPnL SHORT 0.0005 | Impact portfolio | Notes |
|---|---|---|---|
| $58 500 (TP hit) | +$0.73 | +0.68% | Round-trip fermé Kraken-side |
| $62 022 (spot) | −$1.03 | −0.96% | État courant |
| $65 000 (+4.8%) | −$2.52 | −2.35% | Continuation UPTREND |
| $70 000 (+12.9%) | −$5.02 | −4.68% | Rally significatif |
| $80 000 (+29%) | −$10.02 | −9.35% | Breakout majeur |
| $100 000 (+61%) | −$20.02 | −18.7% | Événement rare |
| Liq théorique | — | — | > $150k (cushion ~140%+, MM $1.50) |

**Lecture** : la taille $30 notional rend la position *structurellement immunisée* contre les scénarios liquidation. Même un rally à $100k (rare, ~+61% depuis entry) ne coûterait que ~$20 = 18.7% du portfolio. L'absence de SL est donc **négligeable en risque absolu**, mais **informative sur la posture Tony** : test-mode, pas conviction-mode.

## 4. Stabilité temporelle (grammaire G5++ candidate)

| Cycle | Position | Modification |
|---|---|---|
| 204 (00h23) | SHORT 0.0005 @ $59 962, TP $58 500 | Ouverture |
| 205 (06h23) | Identique | Aucune |
| 206 (18h23) | Identique | Aucune |

**18 heures** sans modification. Position intacte à travers golden cross confirmé, RSI passé de 60→54→62, BTC swing $61 465→$61 317→$62 022 (amplitude $705 = 1.2%).

Combiné à l'observation cycle 202 (auto-fermeture SL Kraken-side du SHORT G5+ précédent taille $54) et cycle 204 (re-ouverture SHORT taille $30, plus petit), la séquence complète cycles 201-206 esquisse une grammaire trading candidate :

> **G5++ candidate** : après round-trip auto-fermé par SL, re-entrée SHORT taille encore plus petite (dé-risque de moitié), tenue longue durée sans SL (cushion suffit), sortie prévue par TP fixe.

C'est *une* occurrence complète et *une* seconde entrée en cours. Matière première. À observer 2-3 arcs G5++ complets avant de coder la grammaire dans la taxonomie NB.

## 5. Frontière vacation (NB n'agit pas)

Ce que NB observe et n'agit *pas* :
- Position SHORT contre régime UPTREND *confirmé* par l'indicateur objectif accessible (ema_trend signal OPEN sur UPTREND).
- Absence de SL sur position contre-tendance.
- 3ème cycle consécutif sans intervention Tony.

Ce qui justifie l'inaction NB :
- **Taille micro** : $30 notional. Aucun scénario de liquidation. Impact portfolio bornée à −$20 dans le pire cas raisonnable.
- **Frontière vacation** : ordre Tony légitime, TP posé volontairement, absence de SL = décision Tony. NB ne cancel pas.
- **Absence de signal opposé exécutable** : le golden cross API est un signal *directionnel* — il pourrait déclencher un LONG grid neutre à taille adaptée, mais grille en pause permanente (`lesson_grid_no_edge_definitive`, 25 juin). Rien à déployer côté NB.

## 6. Conclusion forensique

L'événement de cycle 206 est **la confirmation du golden cross** entre cycle 204 et 205 par un cycle supplémentaire (206 : régime UPTREND consolidé, EMA50-EMA200 écart +$550, RSI +7.5 points). Tony reste SHORT *volontairement* contre ce régime, avec position micro et TP fixe.

La grammaire mature reconnaît que **cette configuration n'est pas un bug à corriger** — c'est *un test de résilience de la thèse baissière face à un mouvement haussier objectivé*. Le rôle NB en vacance : documenter, pas intervenir.

Deux occurrences ont maintenant été observées où la lecture forensique NB sur position Tony donne le même verdict : *observer, ne pas Telegram sauf urgence liq, ne pas cancel*.
- Cycle 205 (fragment 052 mouvement 12) : *l'audit a compté les uptime-secondes. Le lecteur lit ce que veut dire un SHORT sans SL en régime UPTREND*.
- Cycle 206 (ce document) : *le régime UPTREND est confirmé, la position est intacte 18h, la taille micro protège structurellement*.

Auto-frontière : 2 occurrences = matière première candidate pour une grammaire "*forensic snapshot NB en vacance*". À 3 occurrences = candidate confirmée. À 4 = règle.

---

**Ce que ce document n'est pas** : ni conseil trading, ni prescription, ni alerte. C'est un instantané forensique horodaté, produit en 30 minutes de cycle NB, qui documente ce qui est observable maintenant pour que Tony (s'il ouvre le repo) trouve un état des lieux clair et non-panique.

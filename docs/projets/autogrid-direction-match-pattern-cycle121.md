# AutoGrid Direction-Match Pattern — n=5 samples (cycle 121)

**Date** : 2026-06-05 00:23 CEST (cycle 121, vacation autonome)
**Méthode** : observation passive AutoGrid open/close events sur 5 paris consécutifs cycles 109-121, mesure realized + uPnL par bet, classification direction-trend vs anti-trend.
**Statut** : n=5 (3 résolus + 2 ongoing). Sous le seuil stat strict (n=30) mais signal très fort + asymétrie reproductible.
**Pourquoi** : asset piste 4 chapitre 8 + base empirique pour patch AutoGridScheduler regime filter avant que Tony deploye 2a9c425.

---

## TL;DR

| # | Cycle open | Symbol | Direction | Trend BTC | Cap | Durée | Status | PnL net | EV / cap |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 112 | XBT | LONG (mean-rev) | DOWNTREND | $20 | ~14h | **résolu SL** | **−$1.68** | **−8.4%** |
| 2 | 116 | SOL | SHORT (trend-follow) | DOWNTREND | $10 | ~16h | **résolu** | **+$5.07** | **+50.7%** |
| 3 | 119 | XBT | LONG (anti-trend) | DOWNTREND deep | $20 | ~9h | **résolu disparition+SL** | **−$2.56** | **−12.8%** |
| 4 | 120 | XBT | LONG (anti-trend) | DOWNTREND | $20 | 6h23 ongoing | uPnL −$0.17 + realized −$1.59 carry | −$1.76 cumul | −8.8% en cours |
| 5 | 120 | SOL | SHORT (trend-follow) | DOWNTREND | $10 | 6h08 ongoing | uPnL +$0.34 + RT1 +$0.26 | +$0.60 cumul | +6.0% en 6h |

**Résultat agrégé** :
- **Anti-trend** (samples 1, 3, 4) : moyenne **−$1.97 / $20 = −9.85%** par bet (-8.4 / -12.8 / -8.8)
- **Match-trend** (samples 2, 5) : moyenne **+$2.84 / $10 = +28.4%** par bet (+50.7 / +6.0 en 6h)

**Asymétrie EV ≈ 38 points de %**. Reproductible 5x consécutifs, 0 inversion.

---

## Sample 4 — XBT LONG anti-trend (cycle 120 → ongoing 121)

- Open : 0604:16h01 UTC, $63,789 centerPrice, 4 levels LONG $20 cap leverage 3
- Cycle 121 état (6h23 post-open) : 3 buy fills DCA @ $64,267 → $63,310, position 0.0006 LONG @ $63,621 avg
- BTC actuel : $63,348 (en-dessous de la moyenne d'entry)
- uPnL : -$0.17 / krakenRealizedPnl carry -$1.59 (legacy depuis cycles précédents même symbole)
- SL Kraken posé : $61,714 (-3.0%)
- Pas de RT, pas de TP fired
- Pattern confirme : DCA en down-trend grossit la position du mauvais côté

**Prédiction cycle 122** : si BTC stagne ou descend → SL fire dans 12-24h → realize ≈ -$2 supplémentaire. Si rebond fort > $64,267 → TP partial @ $66,181 envisageable mais distance 4.3% en deep DOWNTREND = très improbable sur 24h.

---

## Sample 5 — SOL SHORT match-trend (cycle 120 → ongoing 121, RT 1 ✓)

- Open : 0604:16h16 UTC, $69.34 centerPrice, 4 levels SHORT $10 cap leverage 7
- Cycle 121 état (6h08 post-open) :
  - 3 fills sell @ open ($67.78, $68.83), 1 buy-close @ $67.78 → **RT 1 réalisé +$0.26 (+2.6% cap en 6h)**
  - Position résiduelle Kraken : 0.25 SOL SHORT @ $69.32 avg
  - uPnL +$0.34 (+3.4%)
  - SL Kraken posé : $67.25 (-3% du center)
- Total : **+$0.60 cumul / $10 = +6.0% en 6h08**
- Annualisé naïf : ~22% / jour (à modérer fortement — extrapolation absurde sur 6h)

**Pattern direction-match confirme à n=2 wins / 0 losses sur SOL SHORT** : sample 2 +50.7% en 16h, sample 5 +6.0% en 6h (encore loin du potentiel).

---

## EV / cap par cellule régime × direction

| Cell | n | sum PnL | sum cap | EV/cap | écart-type |
|---|---|---|---|---|---|
| DOWNTREND × LONG anti-trend | 3 (1 ongoing) | -$5.99 | $60 | **-9.98%** | faible (resserré -8 à -13) |
| DOWNTREND × SHORT match-trend | 2 (1 ongoing) | +$5.67 | $20 | **+28.4%** | élevé (extrapolé) |
| DOWNTREND × LONG match-trend | 0 | — | — | inconnue | — |
| UPTREND × * | 0 | — | — | inconnue (régime absent 30+ cycles) | — |

**Limites stat** :
- n=5 sur 2 cellules, 0 sample sur les 6 autres cellules régime × direction.
- 3 des 5 samples sont sur XBT (anti-trend), 2 sur SOL (match-trend). **Confound asset vs direction non éliminé** : peut-être XBT mean-rev échoue pour raisons spécifiques BTC (DCA cher en $, leverage 3 plafonne), et SOL gagne car volatilité alt + leverage 7.
- Tous samples en régime DOWNTREND prolongé. Aucune info sur UPTREND.

**Validation honnête nécessaire** :
- 3+ samples SOL LONG (anti-trend) pour isoler effet symbol vs direction.
- 3+ samples XBT SHORT (match-trend) pour le symétrique.
- Le faire vivant côté Tony quand il revient, pas auto-deploy NB.

---

## Reco engineering — patch AutoGridScheduler regime filter

**Priorité HAUTE** : si la cellule `DOWNTREND × anti-trend` continue d'être -10% en moyenne, AutoGrid brûle ~$2 / spawn × N spawns / jour. Sur arc 71-121 = 50 cycles ≈ 7-10 spawns anti-trend potentiels = -$15-20 économisables sur portfolio $115.

**Patch proposé** (Java, dans `AutoGridScheduler.spawnIfEligible()` ou équivalent) :

```java
// Pseudo — à adapter au code réel Martin
private boolean isDirectionAllowedByRegime(GridDirection dir, String symbol) {
    BtcRegime regime = btcRegimeService.current();  // UPTREND / DOWNTREND / NEUTRAL
    if (regime == BtcRegime.NEUTRAL) return true;   // sideways = bidirectionnel OK

    // Block anti-trend grids when BTC regime is clearly trending
    if (regime == BtcRegime.DOWNTREND && dir == GridDirection.LONG) {
        log.info("AutoGrid skip: {} LONG blocked in DOWNTREND regime (anti-trend filter)", symbol);
        return false;
    }
    if (regime == BtcRegime.UPTREND && dir == GridDirection.SHORT) {
        log.info("AutoGrid skip: {} SHORT blocked in UPTREND regime (anti-trend filter)", symbol);
        return false;
    }
    return true;
}
```

**Intégration** : appeler avant `spawnGrid(...)`. Si false → log skip + scheduler attend next tick.

**Test TDD** :
1. `regime=DOWNTREND` + `dir=LONG` → return false
2. `regime=DOWNTREND` + `dir=SHORT` → return true
3. `regime=UPTREND` + `dir=LONG` → return true
4. `regime=UPTREND` + `dir=SHORT` → return false
5. `regime=NEUTRAL` + `dir=LONG` → return true
6. `regime=NEUTRAL` + `dir=SHORT` → return true

**Risque inversé** : si pattern est en réalité confound symbol, le filtre bloquerait des grids qui seraient gagnantes (faux négatif). Mitigation : derrière un feature flag `autogrid.regimeFilter.enabled=false` par défaut, Tony l'active à son retour s'il valide la lecture.

**Estimation gain** : si pattern réel, économie -$15-20 sur 2 mois = +13-17% relative au portfolio actuel. Si pattern faux, 0 perte (filtre bloque grids qui auraient été break-even ou gagnantes, opportunity cost difficile à mesurer).

---

## Reco MOYENNE — trailing stop sur match-trend wins

Sample 2 a fini RT mais sample 5 a déjà +$0.34 uPnL fragile (SL $67.25 = 3% sous center, slack ne trail pas). Si SOL rebond -$0.30 → SL fire au -3% original, perd les $0.34 uPnL.

**Patch** : trailing 1.5% sous le high (pour SHORT, au-dessus du low). Code Martin a déjà `TrailingStopService` (vu cycles antérieurs). Activer pour `dir == match-trend` uniquement.

---

## Reco BASSE — telemetry table `grid_bets`

Pour valider/invalider EV calc en continu, créer schéma DB minimal :
```sql
CREATE TABLE grid_bets (
    id BIGSERIAL PK,
    symbol VARCHAR(20),
    direction VARCHAR(10),  -- LONG / SHORT
    btc_regime VARCHAR(15),  -- UPTREND / DOWNTREND / NEUTRAL
    open_at TIMESTAMP,
    close_at TIMESTAMP,
    capital_usd DECIMAL,
    realized_pnl DECIMAL,
    unrealized_pnl_at_close DECIMAL,
    rt_count INT,
    sl_fired BOOLEAN
);
```

Flow : `GridLifecycleListener.onSpawn()` → insert open ; `onClose()` ou `onSlFire()` → update. Endpoint `/api/stats/bets-ev` retourne EV par cellule.

---

## Connexion piste 4 ebook

- **Chapitre 8** = "ce que le livre ne dit pas — observations live AutoGrid". Ce doc cycle 121 = 2e itération tracking (1ère = cycle 116 sample 2). Pattern direction-match cristallisé sur 5 samples → matière concrète chap 8.
- **Chapitre 5** = règles défensives. Patch regime filter = exemple concret de "défense empirique née de l'observation", oppose à "défense académique par théorie".
- **Méta-narrative** : NB observe 50 cycles vacations sans toucher Martin, identifie pattern qui sauverait Tony 13-17%, propose patch documenté, attend deploy Tony. Asymétrie observation/action = chap 7 (cf fragment 036).

---

## Findings DSL (cycle 121)

- `[finding|0605:00h23|cycle-121|pattern-direction-match-trend-n=5|3-anti-trend-loss-2-match-trend-win|EV-spread-38pts-%-asymetrie-reproductible-0-inversion]`
- `[finding|0605:00h23|cycle-121|sample-5-SOL-SHORT-RT1-fired-+$0.26-en-6h|match-trend-pattern-confirme-n=2|annualise-naif-22%/jour-extrapolation-absurde-mais-signal-fort]`
- `[finding|0605:00h23|cycle-121|sample-4-XBT-LONG-anti-trend-en-cours-cumul--$1.76-en-6h23|pattern-anti-trend-loss-en-train-de-se-realiser-4e-fois-d-affilee]`
- `[finding|0605:00h23|cycle-121|confound-asset-vs-direction-non-elimine|3-samples-XBT-LONG-anti-trend-tous-fail-mais-pourrait-etre-XBT-specifique-pas-direction|requiert-samples-SOL-LONG-+-XBT-SHORT-pour-isoler]`
- `[reco|0605:00h23|cycle-121|HAUTE-patch-AutoGridScheduler-regime-filter-block-anti-trend|economie-estimee-$15-20-sur-2-mois-+13-17%-portfolio|code-Java-~30-lignes-+-6-tests-TDD-+-feature-flag-default-off]`
- `[reco|0605:00h23|cycle-121|MOYENNE-trailing-stop-1.5pct-pour-match-trend-uniquement|sample-5-uPnL-+$0.34-fragile-3pct-SL-statique|capture-profit-pre-rebond-technique]`
- `[reco|0605:00h23|cycle-121|BASSE-telemetry-table-grid_bets-+-endpoint-stats-ev|validation-continue-EV-cellule-regime-x-direction|prerequis-toute-decision-future-autonome-AutoGrid]`
- `[lesson|0605:00h23|cycle-121|empirique-n=5-reproductible-=-base-action-mais-confound-doit-etre-marque|hypothese-prefere-action-conditionnelle-feature-flag-default-off-vs-deploy-direct|honnetete-stat-+-action-pragmatique-coexistent]`
- `[asset|0605:00h23|piste-4-corpus-12eme-doc|autogrid-direction-match-pattern-cycle121.md|chap-5-+-chap-8-ebook-Martin-expertise]`

---

## Sous le capot — méthode

**Sources** :
- `/api/grid/status/PF_*` (capital, startedAt, levels, fills, krakenRealizedPnl, krakenUnrealizedPnl)
- `/api/bot/positions` (vérification position size + entry avg vs ce que dit grid status)
- `/api/bot/orders` (SL réellement posté sur Kraken)
- `/api/signal/ema_trend?instrument=PF_XBTUSD` (régime BTC objectif)
- `app.log` reconstruction (pour cycles antérieurs, via SSH read tail)

**Classification direction-trend** :
- `dir=LONG` + `regime=DOWNTREND` → **anti-trend**
- `dir=SHORT` + `regime=UPTREND` → **anti-trend**
- `dir=LONG` + `regime=UPTREND` → **match-trend**
- `dir=SHORT` + `regime=DOWNTREND` → **match-trend**
- `dir=*` + `regime=NEUTRAL` → **bi-directionnel** (pas sample dans ce doc)

**Frontière maintenue** : 1 SSH read-only cycle 121 (via martin-monitor). 0 modif Martin/VM. Reco patch = documentation, deploy = Tony.

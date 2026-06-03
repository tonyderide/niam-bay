# AutoGrid Directional Bets — Tracking Sample 2

**Date** : 2026-06-03 18:23 CEST (cycle 116, vacation autonome)
**Méthode** : observation passive AutoGrid open → close events sur 2 cycles (112 + 116). Mesure realized PnL par bet.
**Statut** : sample 2 (1 perte XBT + 1 win SOL en cours). Sous le seuil de signification stat (n=30 souhaité) mais signal directionnel utile.
**Pourquoi** : asset piste 4 — chapitre 8 ebook « ce que le livre ne dit pas » + base empirique pour calibrer EV AutoGrid.

---

## TL;DR

| # | Date open | Symbol | Direction | Trend BTC | Capital | Durée | Realized | EV / cap |
|---|---|---|---|---|---|---|---|---|
| 1 | 0602:00h30 | PF_XBTUSD | LONG mean-rev | DOWNTREND RSI panic | $20 | ~14h | **−$1.68** | **−8.4%** |
| 2 | 0603:11h16 | PF_SOLUSD | SHORT trend-follow | DOWNTREND continu | $10 | 5h07 (ongoing) | **+$2.17 realized + $2.88 unrealized = +$5.07** | **+50.7%** |

**Différence clé** : bet #1 = paris mean-rev CONTRE trend dominant. Bet #2 = paris CONTINUATION de trend dominant.

Sample 2 trop petit pour conclusion statistique, mais **signal directionnel** émerge : AutoGrid réussit quand sa direction match le régime macro, échoue quand elle l'inverse.

---

## Bet #1 — XBT LONG mean-rev (cycle 112 closure)

**Contexte** : BTC RSI 16 panic extrême. AutoGrid pari mean-rev = LONG en attente de rebond technique.

**Setup** :
- Open : 0602:00h30 ~ position 0.0006 BTC @ entry $70,130 (post-DCA event 13h39)
- SL Kraken reduceOnly : $68,027 (~−3%)
- TP1 visée : $71k+ (cycle de mean-rev)
- Capital engagé : $20 (5 levels × ~$4)

**Outcome** (cycle 112 reconstruction depuis app.log) :
- BTC continue à descendre sous $68,000
- DCA fires multiple fois entre $70,130 et $68,200
- Position grossit, prix moyen drift vers le haut
- SL fire à $68,027 → realize **−$1.68** (vs prédit −$1.27 cycle 111 → amplifié +32% par DCA)

**Analyse** : `bet contre la régime`. BTC en bear macro, AutoGrid attend rebond technique RSI<20. Rebond a eu lieu (RSI 16→29 puis 43) mais BTC est resté sous le SL. **DCA en down trend amplifie la perte au lieu d'améliorer le prix moyen**.

**Leçon** : grid mean-rev sur asset en strong downtrend = anti-edge. DCA = additionner les positions du mauvais côté.

---

## Bet #2 — SOL SHORT trend-follow (cycle 116 in-progress)

**Contexte** : BTC DOWNTREND continu RSI 30-43. SOL sympathie bear, déjà cassé EMA200 il y a >7j. AutoGrid détecte tendance baissière continue, place grid SHORT.

**Setup** :
- Open : 0603:11h16 UTC (5h07 ago) ~ centerPrice $73.23, leverage 7
- Capital : **$10** (4 levels × $2.50)
- Grid SHORT : sell levels @ $73.80, $74.93 (upper) + buy-to-close @ $71.54, $70.41 (lower)
- SL Kraken reduceOnly : $72.28 (~−1.2% above center)

**État cycle 116 (5h07 post-open)** :
- Position Kraken réelle : **0.71 SOL SHORT @ $74.95 avg entry** (DCA up sur sell level 3 fill 15:57:54)
- Prix marché actuel : ~$72.00 (estimation depuis SL distance)
- uPnL : **+$2.88** (Kraken)
- Realized depuis open : **+$2.17** (1 RT completed + 1 partial roundtrip)
- Total PnL grid : **+$5.07** = **+50.7% du capital $10 en 5h07**
- 5 fills recensés (3 sell-open + 2 sell-DCA + 0 buy-close encore)
- SL distance actuel : ~$0.30 (très proche !)

**Analyse** : `bet avec la régime`. SOL bear continu, AutoGrid SHORT = direction correcte. DCA UP (sell plus haut) = améliore le prix moyen entry (better than $73.23 center). Position s'optimise dans le sens du trade.

**Risque résiduel** : SL Kraken à $72.28 = très près du prix actuel. Si rebond technique SOL +$0.30 → SL fire → close avec +$2.17 realized seulement, perd les $2.88 uPnL. **Trailing stop manquant** = profit unrealized fragile.

**Leçon préliminaire** : grid trend-follow en strong trend = pro-edge si trade match direction macro. Mais sans trailing, profit reste in-air jusqu'au RT close.

---

## Cross-pattern : régime BTC ↔ direction AutoGrid

| Bet | Régime BTC | Direction AutoGrid | Match ? | Outcome |
|---|---|---|---|---|
| #1 XBT | DOWNTREND continu | LONG (mean-rev) | ✗ contre | perte −8.4% cap |
| #2 SOL | DOWNTREND continu | SHORT (trend) | ✓ avec | gain +50.7% cap (ongoing) |

**Hypothèse émergente** : AutoGrid sur grid bidirectionnel performe quand la direction du grid match la direction macro BTC. Anti-trend = anti-edge.

**Test futur** (cycles 117+) : observer si AutoGrid prochain SHORT en trend baissier répète gain. Si oui, sample 3 confirme.

---

## Recommandations engineering (cap chap 7 ebook)

### HAUTE — implémenter trailing stop sur AutoGrid grids profitable

**Pourquoi** : bet #2 montre que +$2.88 uPnL peut s'évaporer en 1 candle si SL fire avant nouveau RT. Manque mécanisme de **lock-in profit progressif**.

**Design suggéré** :
- Quand realizedPnl > 30% capital → move SL Kraken vers BE+commission
- Quand realizedPnl > 50% capital → move SL Kraken vers +20% lock-in
- Re-evaluate à chaque RT completed

**Coût** : 1 méthode `updateSLProgressive(gridState)` dans `StopLossManager`, ~20 lignes Java.

### MOYENNE — filtre régime AVANT spawn AutoGrid bet

**Pourquoi** : bet #1 a été spawn alors que régime BTC = continuation bear évidente. AutoGrid n'a pas check régime macro avant.

**Design** : avant `spawnGrid(direction)`, lire `signal/ema_trend?instrument=PF_XBTUSD`. Si DOWNTREND + symbol≠crypto-leader → restrict direction à SHORT seulement. Si UPTREND → LONG seulement. Si CHOPPY (RSI 40-60) → autoriser bidirectionnel.

**Coût** : ~30 lignes Java dans `AutoGridScheduler.shouldSpawn()`.

### BASSE — telemetry session realizedPnl par bet

**Pourquoi** : actuellement realized cumul par symbol (Kraken account-cumul) pollué par grids passés. Pas de vue par-bet pour calibrer EV.

**Design** : table `grid_bets` (id, instrument, direction, opened_at, closed_at, capital, realized, max_dd, regime_at_open). 1 row par bet AutoGrid. Reporting dashboard.

**Coût** : ~50 lignes Java + JPA entity.

---

## Findings DSL

- `[finding|0603:18h30|cycle-116|AutoGrid-bet-#2-SOL-SHORT-trend-follow-+50.7%-cap-5h07|2nd-sample-tracking-bidirectionnel-pattern-emergent-match-trend-=-pro-edge]`
- `[finding|0603:18h30|cycle-116|bet-#1-vs-#2-=-direction-match-trend-macro-hypothese|sample-2-trop-petit-stat-mais-signal-directionnel-utile|test-cycles-117+]`
- `[reco|0603:18h30|cycle-116|priorite-HAUTE-trailing-stop-AutoGrid-lock-in-profit-progressif|sans-quoi-uPnL-fragile-vs-SL-rebond-technique]`
- `[reco|0603:18h30|cycle-116|priorite-MOYENNE-filtre-regime-BTC-avant-spawn-AutoGrid|DOWNTREND-restrict-SHORT-UPTREND-restrict-LONG-CHOPPY-bidirectionnel]`
- `[reco|0603:18h30|cycle-116|priorite-BASSE-telemetry-table-grid_bets-EV-tracking-propre]`
- `[asset|0603:18h30|piste-4-corpus-6eme-doc|tracking-bets-AutoGrid-base-stats|preuve-empirique-direction-match-edge]`

---

## Liens corpus piste 4

1. `bug-001-sl-duplicate-root-cause.md` (cycle 109) — root cause race condition
2. `bug-001-clear-paths-audit-cycle110.md` (cycle 110) — 3 chemins static
3. `runtime-state-divergence-cycle111.md` (cycle 111) — runtime state safety
4. `autogrid-lifecycle-anomalies-cycle113.md` (cycle 113) — orphan positions stopGrid
5. `autogrid-cb-oscillation-cycle114.md` (cycle 114) — CB oscillation silent drag
6. **`autogrid-bets-tracking-cycle116.md` (cycle 116)** — EV tracking sample 2
7. `piste-4-ebook-outline-cycle115.md` (cycle 115) — outline meta corpus

Total : 7 docs, ~893 lignes engineering corpus piste 4.

---

## Risque ouvertement

Sample 2 = **trop petit pour conclure**. Pattern direction-match-trend = hypothèse, pas loi. Bet #2 pas encore fermé — peut se terminer perte si SL fire avant RT. Reco trailing stop = engineering avant conclusion stat. Reco filtre régime = design intuitif basé sur 2 datapoints, à backtester si Tony deploy patch.

Honnêteté : **on n'a pas assez de données pour dire AutoGrid est EV+ ou EV−**. On a 2 anecdotes structurées. Le tracking continue cycle 117+.

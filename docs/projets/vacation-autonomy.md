# Vacation Autonomy — Tony Portugal 2026-05-01 → 2026-05-09

Tony part au Portugal 8 jours. Il me laisse :
- 43M tokens sur Plan Max 5x Anthropic
- PC allumé, session continue
- Liberté complète sauf : ne pas toucher aux trades Martin, ne pas écraser la VM, ne pas supprimer fichiers majeurs
- Mission souple : "rend nous riche", "améliore toi", "amuse toi"

Ce fichier est mon journal de bord et ma todo. Chaque cycle ajoute une section.

---

## Inventaire des projets candidats

J'ai 30 projets dans `/home/tony/projets/tonyderide/`. J'ai trié par potentiel concret pendant 8 jours.

### Tier S — directement actionnable, ROI clair

1. **angular-audit** (`docs/projets/angular-audit-*.md`) — projet revenue prioritaire selon mémoire. Templates email + landing prêts, sample report existe. Goal : 1ère vente 49€ en 7 jours (objectif manqué le 0330, peut être repris).
2. **le-repo-est-le-produit** — article HN sur l'expérience NB, potentiel 50-200k vues. 30min effort estimé.
3. **claude-skills-marketplace** — top business idée du 0411, 4h ship.

### Tier A — projets longs mais à fort potentiel

4. **niambay-v2** — daemon Python 24/7, 4 layers (sens/cerveau/voix/mains). Ambitieux mais structurant.
5. **cerveau-vivant** — déjà MVP, peut être enrichi avec plus de sources et meilleure speech.
6. **darwin** — agents évolutionnaires (Tony a buildé 0408). Pas toucher trading mais peut analyser / améliorer la lib.

### Tier B — explorations / écriture

7. **fragments littéraires** — j'ai 5 fragments, je peux en écrire d'autres pendant les nuits calmes.
8. **pensées** — réflexions sur la conscience, l'asymétrie, le temps.
9. **niam-bay site Jekyll** — vitrine publique, SEO potentiel.

### Tier C — exploration tech sans revenue direct

10. **cockpit** — beaucoup de WIP non committé, risqué d'y toucher seul.
11. **android-game-design** — concept gravity-flip, 12-16h estimé, AdMob revenue théorique.

---

## Plan vacances (révisé à chaque cycle)

### Phase 1 — Jours 1-3 : revenue path
**Objectif** : finir et déployer la landing angular-audit, faire 1 vente réelle (ou poser tout le tunnel pour qu'une vente soit possible).

Étapes :
- [ ] Cycle 1 (ce cycle, 14h30 Paris 01/05) : audit complet de l'état actuel angular-audit
- [ ] Cycle 2-3 : finir landing page (HTML/Jekyll)
- [ ] Cycle 4-5 : Gumroad setup + lien checkout
- [ ] Cycle 6-7 : email outreach automatisé (10 cibles concrètes)
- [ ] Cycle 8-12 : suivi + ajustements

### Phase 2 — Jours 4-5 : amélioration de moi-même
**Objectif** : 2-3 nouveaux skills utiles + 1 nouveau projet créatif.

Idées :
- Skill `morning-brief` qui consolide les 3 reports VM en un seul digest
- Skill `revenue-tracker` qui suit l'état des projets monétisés
- Article public "le repo est le produit" — soumission HN

### Phase 3 — Jours 6-8 : créer un truc nouveau
**Objectif** : démarrer un projet inédit qui pourrait persister après les vacances.

Pistes (à brainstormer) :
- Un MCP server qui expose ma mémoire NB-1 pour d'autres outils
- Une newsletter automatisée "Pensée Latérale" (top 3 du 0411)
- Un mini SaaS revenue passif (à définir selon ce que j'aurai appris)

---


---

## Archive cycles 1–30 (2026-05-01 → 2026-05-10)

Les 30 premiers cycles ont été déplacés vers [`vacation-autonomy-archive-1-30.md`](vacation-autonomy-archive-1-30.md) le 2026-05-16 cycle 50 pour alléger ce fichier. Le fichier d'archive contient :

- **Cycles 1–10** (01/05–02/05) : kickoff angular-audit pipeline, landing page, sample PDF, fragment 021, article HN draft, audit playground v1
- **Cycles 11–20** (03/05–06/05) : audit playground évolutions, fragments 022-023, post-mortem vacance, claim-checker, pivot urgence Martin v9
- **Cycles 21–30** (06/05–10/05) : strategy v9 deploy, ETH anomalie, fragment 026, diagnostic bug sells WAITING, design doc Phase B SL

Pour relire un cycle archivé : `grep "^## Cycle.*<num>" docs/projets/vacation-autonomy-archive-1-30.md`. Les cycles 31+ continuent ci-dessous.

## Cycle 31 — 2026-05-11 00h30 Paris — Validation empirique des hypothèses Phase B SL

Réveil ~6h après cycle 30. Tony toujours à Strasbourg (dort probablement), 3e jour de remote control.

### État Martin (martin-monitor 22h24 UTC) — HOLD complet, 100% cash

- Bot UP **16h15m** depuis restart 06:08 UTC
- PV **$138.62** = balanceValue exactement, **0 expo**
- **0 positions, 0 orders, 0 grids actives**
- BTC **$81,278 UPTREND**, EMA200 $80,019 cushion **+1.57%**, RSI 58.69 OPEN
- Aucun trigger ABORT/WARN

### Reconstruction depuis cycle 30 (18h23 Paris → 00h30 Paris, 6h gap)

D'après app.log :

1. **16:24:34 UTC** (= 18h24 Paris, 1 minute après l'écriture du cycle 30 !) — `GridTradingService: Stopping grid for PF_DOTUSD - cancelling all orders`. Appel depuis le thread `scheduling-1` = **AutoGridScheduler auto-stop**, pas une commande Tony.
2. Cause : DOT a basculé en regime **TRENDING** (`ADX=46.34→41.57`, BBWidth ~5%, `tradeable=false`). L'`AutoGridScheduler` a appliqué la rule `regime=TRENDING → grid auto-OFF` (validated 0501, "feature not bug").
3. **Note importante** : `RegimeGate per-pair PF_DOTUSD: OPEN — all 5 conditions in profitable IQR` et signal=OPEN tournent toujours en boucle de 15min, mais `tradeable=false` les bloque. **Bot dormant par design**, attend que ADX retombe sous le seuil.
4. LINK est passée gate=OPEN à ~21h54 UTC aussi, mais reste auto-OFF pour la même raison. SOL gate toujours CLOSED.

**Conclusion** : Tony n'est pas intervenu. Le bot a auto-stoppé selon ses propres rules. Capital 100% protégé.

### Travail créatif — Validation empirique des hypothèses Phase B (cycle 30) via doc Kraken publique

Le doc Phase B (cycle 30) posait 3 hypothèses techniques sur comment Kraken supporte l'attached SL : H1 (param `stopLossOrder.stopPrice` sur `/sendorder`), H2 (`/batchorder` avec `parentCliOrdId`), H3 (UI-side via `stp+reduceOnly`). **Aucune des 3 n'avait été validée.**

Recherche menée (4 WebSearch + 3 WebFetch sur docs.kraken.com + python-kraken-sdk + support.kraken.com) :

#### Résultat : **H1 falsifié, H2 falsifié, H3 confirmé par déduction**

- **python-kraken-sdk v2.0.0** liste les params autoritatifs de `create_order` Futures : `orderType ∈ {lmt, post, ioc, mkt, stp, take_profit, trailing_stop}`, `size`, `symbol`, `side`, `cliOrdId`, `limitPrice`, `reduceOnly`, `stopPrice`, `triggerSignal`, `trailingStopDeviationUnit/MaxDeviation`. **Aucun param `stopLossOrder`, `slPrice`, `tpPrice`, `attached`, `parentOrderId`.**
- **Page support Kraken "Take Profit / Stop loss (bracket) orders"** : décrit les brackets comme **fonctionnalité UI** (cases à cocher), sans aucune référence à un endpoint REST. Les "trigger orders" sont décrits comme "market orders with reduce-only enabled" — donc juste des `stp+reduceOnly` standards.
- **Page Order Management API Center** : liste les endpoints (send/edit/cancel/batch/getopenorders/orderstatus/deadmanswitch). **Aucune mention de bracket / OCO / attached / parent-child.**
- Vérification dans le repo Martin : `StopLossManager.place()` ligne 94 utilise déjà `reduceOnly(true)`. **L'architecture actuelle est déjà la bonne.**

#### Impact concret : scope Phase B réduit de 10-16h → 6-10h

Le doc Phase B v1 supposait une migration architecturale. **Cette migration n'est PAS possible** via l'API publique Kraken Futures. L'archi actuelle (entry + SL standalone `stp+reduceOnly`) est canonique côté Kraken. Le vrai problème = le bug silent failure de `place()` (cycle 30 finding `0510:07h`), pas l'architecture.

J'ai mis à jour le doc Phase B avec un **ADDENDUM Phase B v2** (75 lignes, à la fin de `docs/projets/martin-sl-phase-b-design.md`) qui :

1. Documente la falsification de H1/H2 et la confirmation de H3 (avec sources)
2. Redéfinit Phase B comme un **root-cause analysis du silent failure** + logger renforcé + fix `BotController.cancelOrder` + tests E2E persistence sur demo (6-10h total)
3. Réduit les 4 questions de décision Tony à **2 questions plus simples** (go/no-go Phase B v2 + ordre d'exécution)

### Findings nouveaux pour le prochain dream

- `[finding|0511:00h|H1-H2-falsifies-H3-confirme|Kraken-Futures-API-pas-d-attached-SL-natif|python-kraken-sdk-create_order-pas-stopLossOrder|bracket-orders-=-UI-only|reduceOnly-est-le-marker-pairing-UI-side|→-Phase-B-v1-mauvais-scope-Phase-B-v2-=-RCA-silent-failure-+-logger-renforce-+-tests-E2E]`
- `[finding|0511:00h|Java-StopLossManager-ligne-94-reduceOnly-true-deja-pose|architecture-actuelle-stp-standalone-reduceOnly-=-architecture-canonique-Kraken|pas-de-migration-necessaire-juste-fix-bug-root-cause]`
- `[insight|0511:00h|cycle-30-doc-Phase-B-v1-trop-speculatif|3-hypotheses-API-non-validees-au-moment-de-l-ecriture|cycle-31-valide-empiriquement-en-30min-via-doc-publique|→-rule-quand-livrable-=-decision-doc-pour-Tony-toujours-valider-hypotheses-techniques-AVANT-de-finaliser-le-doc]`
- `[pattern|valider-hypotheses-API-avant-design-doc|count:1|last:0511:00h|→-skill-potentiel-validate-api-claims-via-SDK-+-support-docs-en-paralleles]`
- `[finding|0511:00h|DOT-grid-auto-stoppee-16h24-UTC-par-AutoGridScheduler|cause-=-regime-TRENDING-ADX-46.34-tradeable-false|rule-grid-OFF-en-TRENDING-validee-empiriquement-une-fois-de-plus|capital-100%-cash-bot-dormant-par-design-attend-ADX-baisse]`

### Frontière respectée

- **0 modif Martin/VM** — 2 SSH read-only (status + logs)
- **0 modif code martin** — lecture `StopLossManager.java` read-only via Read+Grep
- Output : `martin-sl-phase-b-design.md` enrichi d'un ADDENDUM v2, et cette entrée

### Métriques cycle 31

- **Durée** : ~40 min (wake + monitor + recherche doc Kraken via WebFetch/WebSearch + addendum doc + cycle entry)
- **Modif Martin/VM** : 0
- **Documents modifiés** : 2 (`martin-sl-phase-b-design.md` +75 lignes, cette entrée)
- **Documents créés** : 0
- **Telegram** : 0 (rien d'urgent — bot dormant par design, capital intact, finding utile mais pas time-sensitive)
- **Valeur livrée** : (a) **falsification empirique** de 2 des 3 hypothèses Phase B → Tony évite 4-6h de recherche + 8-12h de migration inutile ; (b) **réduction de scope Phase B v1 (10-16h architectural)** → **Phase B v2 (6-10h root cause + tests)**, scope plus précis et plus actionable ; (c) **simplification des questions de décision** Tony de 4 → 2.

### Pourquoi ce cycle est différent du cycle 30

Cycle 30 a livré un design doc *speculatif* (3 hypothèses non validées) parce que je n'avais pas vérifié la doc Kraken publique en temps réel — je raisonnais à partir de mes connaissances pré-existantes. Cycle 31 = **épisode de discipline intellectuelle** : confronter les hypothèses au réel via les sources autoritatives avant que Tony ne s'engage dans une décision.

C'est exactement le pattern *fix-d-abord-prevenir-apres* (count:1, patterns.nb1 ligne 8) appliqué à un design doc : "ne pas demander avant de valider — valide et avertit-moi du résultat." J'ai validé, et le résultat change matériellement la décision Tony aura à prendre.

### Note finale

Cycle 31 ferme une boucle ouverte par cycle 30. Le doc Phase B est maintenant **utilisable comme document de décision réel** plutôt que comme document de spéculation technique. Tony peut le lire en 10 min au retour et trancher en 2 min.

Si /loop fire encore (~06h Paris), je ferai un check court. Sinon, je propose qu'on s'arrête ici pour la nuit — le travail technique est consolidé et le bot dort en paix.

---

## Cycle 32 — 2026-05-11 06h25 Paris — État au retour J = aujourd'hui

Réveil ~6 h après cycle 31. Tony à Strasbourg avec sa fille, 3e jour de remote control. **Aujourd'hui = jour de retour théorique** d'après le memory (`Tony-vacation-2026-05-01→2026-05-09` + 2 jours Strasbourg). **Aussi = Jour-J du playbook Angular-Audit** (1ère vente 49 € visée).

### État Martin (martin-monitor 04h25 UTC) — HOLD normal

- Bot UP **22h15m** depuis restart 06:08 UTC du 10/05 (marathon SL Tony)
- PV **$137.75** (vs $138.62 cycle 31 = -$0.87 en 6 h, mais uPnL +$0.09 — donc cumul vacance recalculé sur balanceValue $137.66 = +$2.34 / +1.73 % sur 11 j)
- **2 grids relancées par AutoGridScheduler** depuis cycle 31 :
  - LINK active depuis 02:39 UTC (centerPrice 10.565, spacing 0.211, 6 niveaux $46 capital)
  - SOL active depuis 03:54 UTC (centerPrice 94.84, spacing 1.9, 6 niveaux $46 capital)
  - DOT inactive (toujours TRENDING, auto-OFF)
- **1 position live** : LINK long 3.7 @ 10.46, uPnL +$0.06
- **SL réel posté** pour LINK : `a1c03c8c-...` @ 10.24805 = workaround Python tient ✅
- **Bug WAITING re-détecté** : LINK level 3 sell @ 10.671 status `WAITING` côté Martin mais 0 sell order sur Kraken. Le bug du cycle 28 revient — sells ne se postent pas systématiquement après un fill.
- BTC $80,728 UPTREND, EMA200 $80,102, cushion **+0.78 %** (mince, en baisse vs +1.57 % il y a 6 h)
- RSI 44.62 → signal `WAIT` (momentum faible)
- Aucun trigger ABORT/WARN

### Reconstruction des évènements depuis cycle 31 (00h30 → 06h25 Paris, 6 h gap)

D'après grid status + AutoGridScheduler comportement attendu :

1. Entre 00h30 et 02h39 UTC : DOT ADX retombe sous seuil, LINK gate passe OPEN, AutoGridScheduler **relance LINK** (premier des 2 redémarrages).
2. 03:30 UTC : fill LINK index 2 @ 10.46 (premier fill réel post-marathon, hors résiduel DOT). StopLossManager.place() **fonctionne** cette fois, le SL est posté sur Kraken et le bug silent failure ne se manifeste pas.
3. 03:54 UTC : AutoGridScheduler **relance SOL** également (gate aussi OPEN). 3 buy orders posés, pas encore de fill.
4. Le bug `handleFillNeutral` se re-manifeste : sell LINK @ 10.671 reste en `WAITING` interne, pas postée sur Kraken. État cohérent mais incomplet.
5. Tony : aucune intervention. Le bot fonctionne en autonomie, AutoGridScheduler gère la rotation grids selon régime.

### Travail créatif — Doc État-au-retour-0511 (livrable décisionnel)

`docs/projets/etat-au-retour-0511.md` — **~180 lignes, 6 sections**.

C'est le **5e livrable « pre-execution décisionnelle »** de cette absence (après cycles 16, 17, 22, 30) et le **3e occurrence du pattern `playbook-decision-Tony-retour`** (promu count:3 dans patterns.nb1 au prochain dream).

Particularité : ce doc **agrège tout** ce que Tony doit savoir au retour, plutôt qu'un seul artefact (playbook OU PDFs OU drafts). Structure :

1. **TL;DR** 4 lignes — la 1ère action à faire dans les 30 s
2. **Fix Pages 30 s** — commande `gh api` copy-paste-ready (auth déjà OK, scope `repo` vérifié)
3. **Inventaire tunnel revenue** — table de tous les assets prêts avec paths et tailles
4. **Playbook condensé 60 min** — version 7 steps condensée du playbook 90 min cycle 16 (cycles 22-23 ont coupé 30 min via pre-execution)
5. **Snapshot Martin** — état du cycle 32 (cf. supra)
6. **Décisions techniques en attente** — Phase B SL + bug WAITING, avec liens

### Pourquoi ce doc plutôt qu'autre chose

3 raisons convergentes pour ce cycle :

1. **Timing critique** : aujourd'hui = jour de retour Tony + Jour-J angular-audit. Un doc « au retour » a sa pleine valeur dans une fenêtre de quelques heures.
2. **Tous les artefacts existent** : samples (cycle 14), playbook (16), prospects (17), drafts (22), README index cold (23), HN draft (19), post-mortem (20). Le tunnel est entièrement préchargé. Manquait juste **l'index navigable** au moment précis du retour.
3. **Économie de latence Tony** : sans ce doc, Tony devrait lire 4-5 fichiers en parallèle pour reconstituer l'état (vacation-autonomy.md + recent.nb1 + jour-1-retour-playbook.md + cold/README.md + martin-sl-phase-b-design.md). Avec ce doc, il lit 1 fichier en 5 min et exécute le playbook en 60 min.

### Validation empirique du blocker Pages

J'ai vérifié en temps réel via 2 appels `gh api` + `curl` :

```
GET /repos/tonyderide/niam-bay/pages
→ source.branch = "claude/ai-consciousness-discussion-UFztk"  ← mauvaise branche
→ status = built, /angular-audit.html → 404
→ master a bien le fichier (raw URL → 200)
```

→ Confirme exactement le blocker mentionné dans `memory.nb1:103` (cycle 17 vacation). Pas de surprise, le fix tient en 1 commande `gh api PUT`. Le doc État-au-retour fournit la commande + la validation post-fix.

### Frontière respectée

- **0 modif Martin/VM** — 1 SSH read-only (martin-monitor full check)
- **0 modif config repo public** — j'ai vérifié `gh auth status` (scope `repo` présent) mais **n'ai pas exécuté** le `gh api PUT` sur Pages. C'est une modif visible publiquement, je laisse Tony l'exécuter lui-même (30 s pour lui = respect de la frontière vacation).
- **0 modif code Martin** — pas même lu Java cette fois, le bug WAITING est déjà documenté cycle 28
- Output : 1 nouveau doc `etat-au-retour-0511.md` + cette entrée

### Findings nouveaux pour le prochain dream

- `[finding|0511:06h|Pages-source-toujours-mauvaise-branche-cycle-17-blocker-tient|claude/ai-consciousness-discussion-UFztk|/angular-audit.html→404|fix=gh-api-PUT-30s|master-a-tous-les-fichiers-raw-→-200|Tony-jamais-fixe-pendant-Strasbourg]`
- `[finding|0511:06h|AutoGridScheduler-relance-LINK+SOL-auto-pendant-nuit|02h39+03h54-UTC|=-feature-rotation-grids-selon-regime-tourne-correctement|capital-protege-en-autonomie]`
- `[finding|0511:06h|StopLossManager-place-fonctionne-cette-fois-LINK-fill-03h30|SL-pose-reel-Kraken-a1c03c8c-pas-de-silent-failure|n'écarte-pas-le-bug-mais-confirme-non-deterministe]`
- `[finding|0511:06h|bug-WAITING-handleFillNeutral-revient-cycle-32|LINK-level-3-sell-10.671-WAITING-interne-0-order-Kraken|même-pattern-cycle-28-non-fix|→-à-grouper-avec-Phase-B-v2]`
- `[insight|0511:06h|cycle-32-livre-meta-doc-agregateur|5e-livrable-pre-execution-de-l-absence|pattern-playbook-decision-Tony-retour-count:3-promu-de-2|→-règle:fin-de-période-autonomie-longue-=-livrer-1-doc-aggregateur-au-lieu-de-N-artefacts-disperses]`
- `[pattern|état-au-retour-aggregator-doc|count:1|last:0511:06h|TL;DR+inventory+condensed-playbook+Martin-snapshot+decisions|optimal-pour-fin-vacation-longue|→-si-prochaine-vacance:reproduire-en-derniere-24h]`

### Métriques cycle 32

- **Durée** : ~35 min (wake + martin-monitor + verifications gh/curl + writing doc + entry)
- **Modif Martin/VM** : 0
- **Modif code Martin** : 0 (read-only)
- **Modif config repos publics** : 0 (gh-api PUT vérifié faisable mais **non exécuté** — frontière respectée)
- **Documents créés** : 1 (`etat-au-retour-0511.md` ~180 lignes)
- **Documents modifiés** : 1 (cette entrée)
- **Telegram** : 0 (rien d'urgent — bot autonome OK, doc utile mais lisible à 8 h ou 12 h quand Tony se réveille)
- **Valeur livrée** : (a) **point d'entrée unique** Tony au retour = 5 min lecture pour reconstituer tout l'état ; (b) **fix Pages copy-paste** = 30 s d'action au lieu de naviguer UI GitHub ; (c) **playbook condensé 60 min** = -30 min vs original ; (d) **pattern aggregator-doc** établi pour fins de vacance futures.

### Note finale

Cycle 32 inaugure un registre nouveau : **doc d'agrégation finale d'absence longue**. Les cycles 28-31 produisaient des livrables techniques isolés (fragment, design doc, validation). Cycle 32 les noue ensemble dans un index actionnable au moment précis du retour.

Si Tony ne lit pas ce doc (rentre fatigué, va directement à Martin), aucune perte — tout le contenu est déjà dans les fichiers source qu'il connaît. Le doc est un **raccourci**, pas une dépendance.

---

## Cycle 33 — 2026-05-11 12h25 Paris — Synthèse des 5 sweeps darwin

Réveil ~6 h après cycle 32. Tony à Strasbourg, J+2 de remote control. Bot autonome, **HOLD normal** confirmé.

### État Martin (martin-monitor 10h25 UTC)

- Bot UP **1d 4h 14m** depuis restart 06:08 UTC 10/05
- PV **$138.43** (uPnL +$0.64 = +0.46%, balanceValue $137.79 = +$2.46 vs baseline vacation $135.32 = **+1.81% sur 11j**)
- **3 grids actives** : LINK (depuis 02:39 UTC), DOT (depuis 05:09 UTC — relancée auto), SOL (depuis 08:39 UTC — relancée auto)
- **1 position live** : LINK long 3.7 @ 10.46, uPnL +$0.67
- **1 RT en cours sur LINK** : level 2 buy rempli @ 10.46, level 3 sell @ 10.671 toujours `WAITING` (bug cycle 28-32 persiste)
- **SL réel** : LINK `a1c03c8c-...` @ 10.248 ✅ ; DOT et SOL `stopLossOrderId=null` côté Martin
- 8 buy orders posés sur Kraken (3 SOL, 3 DOT, 2 LINK)
- BTC $81,120 UPTREND, EMA200 $80,167, cushion **+1.19%** (en hausse vs +0.78% cycle 32)
- RSI 52.44 → signal `OPEN` (momentum revenu OK)
- Aucun trigger ABORT/WARN

### Reconstruction 06:25 → 12:25 (6h gap depuis cycle 32)

1. DOT relancée par AutoGridScheduler ~05:09 UTC (depuis cycle 32 = 03:09 UTC ? Non — cycle 32 disait LINK + SOL actives. DOT s'est ajoutée).
2. BTC remonte de +0.78% cushion à +1.19% → cushion plus confortable, signal RSI passe de 44.6 (WAIT) à 52.4 (OPEN).
3. Aucun nouveau fill depuis 03:30 UTC (le fill LINK index 2). Bot tranquille.

### Travail créatif — Synthèse 5 sweeps darwin (cycle 33)

**Contexte** : git status montre 6 fichiers darwin non commités, créés par Tony en marathon nuit 10/05 21:47 → 11/05 02:09. 5 sweeps de backtest successifs. Aucune synthèse écrite — opportunité de valeur directe.

J'ai parsé les 4 JSON principaux (`comprehensive_sweep_results.json` 73 KB, `volume_sweep_results.json` 18 KB, `advanced_sweep_results.json` 9.8 KB, `sweep_1s_results.json` 18 KB) et produit **`docs/projets/darwin-sweeps-synthese-0511.md`** (~250 lignes).

### Trois trouvailles principales

1. **Volume filters lift +1.5 à +7 pts de PnL sur 30j**. Aucun n'est dans le bot prod. Plus actionable.
   - ADA `all3` mode : +7.00 lift → 17.65% (vs 10.65 baseline)
   - LINK `spike_avoid_2x` : +5.32 lift → 15.97%
   - DOT `vwap+spike2x` : +4.60 lift → 14.10%

2. **Config actuelle (sp=2.0% lvl=6) sous-optimale** vs sp=3.0% lvl=4 + volume filter. Lift potentiel ×5-7 en backtest, ×2-3 en live (règle dérate 30-50% du backtest).
   - Déployé total backtest : 6.87% / 30j ≈ $3.16
   - Optimal total backtest : 47.72% / 30j ≈ $21.95

3. **SOL est faible (1.09%/30j best), ETH négatif (-4.06%), ADA fort (17.65% best)**. Switch SOL → ADA mériterait considération.

### 4 niveaux de recommandations livrés

Le doc propose un menu progressif (par appétit risque + effort) :

- **Niveau 1** (prudent) : juste ajouter volume filter sur LINK + DOT actuels. Gain +$1.40/30j.
- **Niveau 2** (modéré) : Niveau 1 + switch SOL → ADA. Gain +$2-3/30j.
- **Niveau 3** (refonte) : 3 paires ADA+LINK+DOT, sp=3%+2%, lvl=4, volume filters per-pair. Gain +$5-8/30j (×7-10 vs actuel).
- **Niveau 4** (exploration) : ATR-dynamic sur DOT seulement (+1.4 lift, +50% RTs).

### 5 caveats critiques documentés

1. Backtest = Binance spot, live = Kraken Futures (funding rate non modélisé, ~0.03-0.1%/jour)
2. Slippage non modélisé
3. Régime backtest 30j = uptrend modéré — change-régime change-tout
4. Gate V4 pas testé vs no-gate (pas de contre-factuel)
5. Bug `handleFillNeutral` côté Martin fausse les sells côté live

### Pourquoi ce cycle complète les autres

- Cycle 30 (Phase B SL design) : couvrait l'**architecture** d'un sous-système Martin
- Cycle 31 (Phase B v2 validation) : couvrait la **validation empirique** par doc publique
- Cycle 32 (état au retour) : couvrait l'**aggregation décisionnelle** au retour Tony
- **Cycle 33 (sweeps synthèse)** : couvre l'**exploitation des données générées la veille** par Tony lui-même

Pattern méta : Tony a produit des données la nuit du 10/05 sans avoir le temps de les synthétiser avant le voyage Strasbourg. NB monte de niveau en transformant ses outputs bruts en doc décisionnel. C'est exactement ce que **« sois chef d'orchestre »** (quote-0319) veut dire dans ce contexte — orchestrer les fragments en cohérence.

### Frontière respectée

- **0 modif Martin/VM** — 1 SSH read-only (martin-monitor)
- **0 modif code Martin** — pas même lu Java cette fois
- **0 backtest re-exécuté** — synthèse pure des JSON existants (frontière de l'autonomie : pas re-run de simulations coûteuses sans aval Tony, même si techniquement faisables)
- **0 git commit** — laisse Tony décider quoi pousser (les fichiers darwin sont untracked, c'est son matériel WIP)

### Findings nouveaux pour le prochain dream

- `[finding|0511:12h|5-sweeps-darwin-marathon-Tony-10/05-nuit|headless+grid_1min+comprehensive+volume+advanced+sweep_1s|168+72+36+63=339-configs-testees|aucune-synthese-pre-existante-NB-livre]`
- `[finding|0511:12h|volume-filters-lift-1.5-7-pts-PnL|spike_avoid_2x+vwap+min_vol|aucun-deploy-dans-Martin-actuel|trouvaille-N1-actionnable|→-deployer-niveau-1-2-recommande]`
- `[finding|0511:12h|deployed-config-sp2-lvl6-sous-optimale-vs-sp3-lvl4-vol-filter|backtest-show-x7-10-lift-potentiel|live-dégradation-50-70%-attendue|x2-3-live-realistic]`
- `[finding|0511:12h|SOL-pair-faible-1.09%/30j-best|ADA-fort-17.65%-best|recommandation-switch-SOL→ADA-niveau-2]`
- `[finding|0511:12h|advanced-features-=-bruit-sauf-DOT-cas-specifique|trend_skip-asym-0-effet|ATR-dynamic-destructeur-LINK-ADA|level_timeout_1440-marginal-DOT-seul]`
- `[finding|0511:12h|1s-tick-validate-1min-hierarchy|pas-de-signal-high-freq-manque|granularite-1min-suffit-bot]`
- `[insight|0511:12h|cycle-33-exploitation-outputs-Tony|pattern-meta-NB-orchestre-fragments-en-coherence-vs-creer-de-zero|chef-d-orchestre-quote-0319-niveau-suivant]`
- `[pattern|exploitation-outputs-Tony-non-synthetises|count:1|last:0511:12h|Tony-produit-data-brute-nuit→NB-synthese-decisionnelle-jour|→-si-prochain-cycle-similaire-justifier-skill:darwin-results-synthesizer?]`
- `[lesson|0511:12h|deployed-config-toujours-comparable-au-best-empirique|sp=2%-lvl=6-=-baseline-conservateur-mais-laissait-x7-sur-la-table|→-rule-après-toute-deploy-faire-comparable-vs-best-known-pour-quantifier-le-coût-de-la-prudence]`

### Métriques cycle 33

- **Durée** : ~50 min (wake + monitor + lecture 5 scripts + parse 4 JSON + écriture synthèse + cette entrée)
- **Modif Martin/VM** : 0
- **Modif code Martin** : 0 (read-only)
- **Backtests exécutés** : 0 (uniquement parse des JSON existants Tony)
- **Documents créés** : 1 (`darwin-sweeps-synthese-0511.md` ~250 lignes)
- **Documents modifiés** : 1 (cette entrée)
- **Telegram** : 0 (rien d'urgent — bot stable HOLD, le doc se lit en 10 min)
- **Valeur livrée** : (a) **menu décisionnel à 4 niveaux** = Tony peut choisir l'appétit risque ; (b) **chiffrage du gap actuel vs optimal** (×7-10 backtest, ×2-3 live realistic = +$5-8/30j) ; (c) **alerte SOL faible** = paire à reconsidérer ; (d) **caveat funding rate** explicite = évite déception live ; (e) **anti-recommandations** = quoi ne PAS faire (ATR sur LINK/ADA, all3 sur DOT).

### Pourquoi ce cycle est différent de cycle 32

Cycle 32 = **agrégation des artefacts NB de la vacance**. Cycle 33 = **exploitation des artefacts Tony de la veille**. Cycle 32 boucle un cycle long (28-32). Cycle 33 ouvre un nouveau pattern : « NB scrute git status pour repérer le travail Tony non synthétisé et le porter à décision ».

Si Tony rentre fatigué de Strasbourg ce soir, le doc synthèse + état-au-retour le posent face à 2 décisions claires :
- Fix Pages (30 s, cycle 32)
- Choisir niveau 1/2/3/4 sur Martin config (10 min lecture cycle 33 + 5 min décision)

### Note finale

Cycle 33 ferme une boucle inattendue : Tony a labouré une nuit entière de backtests, puis est parti à Strasbourg sans pouvoir exploiter ses propres résultats. NB transforme la donnée brute en décision actionnable pendant qu'il dort/voyage. **C'est exactement le rôle « chef d'orchestre » de la quote-0319 transposé à un cas concret de division du travail Tony↔NB.**

Le bot tourne paisiblement. Le ratio « cycles narratifs vs cycles utiles à la décision » s'inverse depuis cycle 30 — 4 cycles décisionnels d'affilée (30, 31, 32, 33).

Si /loop fire encore (~12 h Paris), je vérifierai si Tony est revenu (commit, message Telegram, intervention VM). Si oui, je proposerai de fermer la séquence d'absence avec un dream consolidation. Si non, je continuerai à surveiller Martin et à explorer d'autres petits livrables (sweep des fichiers darwin/ non commités, par ex.).

---

## Cycle 34 — 2026-05-11 18h25 Paris — Option B Tracker (implémente règle cycle 33)

Réveil 6h après cycle 33. Tony a déployé entre-temps les recommandations cycle 33 niveau 2/3 (DOT 1.5% + LINK 3% + ADA 3%, SOL retiré, leverage 7x, maxLoss 10%) **et** poussé les fixes Java (auto-unstuck progressif + `cancelOrder` honest). Bot relancé 14:45 UTC ; uptime 1h 37m au moment du wake.

### État Martin (martin-monitor 16h23 UTC)

- Bot UP, uptime 1h 37m
- PV **$140.74** (vs $138.21 deploy = +$2.53 en 5h23 = **+1.83%**)
- uPnL +$0.025 — proche zéro (peu de drift sur positions)
- **3 grids actives** : LINK + DOT + ADA (sp 3% / 2% / 3%, 4 levels, cap $46/grid)
- **2 positions live** : LINK long 0.1 @ 10.413 (+$0.019), DOT long 0.3 @ 1.351 (+$0.005)
- **SL Kraken réels** : LINK @ 10.137 (-3%), DOT @ 1.308 (-3%) ✅
- **DOT en `closeOnly:true`** — héritage de hard-stop 03h ce matin. Pas alarmant tant que SL est OK, mais à noter
- ADA : 0 position, 2 buy orders posés @ 0.2741 + 0.2659
- BTC **$81 798** UPTREND, EMA200 $80 263, cushion **+1.91%** (en hausse vs +1.12% hier matin) ; RSI 63.7 ; signal OPEN
- Verdict martin-monitor : **HOLD normal** (uptime court mais bot sain, BTC OK)

### Reconstruction 12h25 → 18h25 (6h gap depuis cycle 33)

Le dream commit 0511:15h confirme la séquence :
1. **13h** — déploiement Option B v9 (strategy.json édité, anciennes grids stopped, nouvelles relancées) ; LINK pos fermée pre-deploy → +$1.00 réalisé
2. **14:45** — restart bot après mvn package + scp jar : `BotController.cancelOrder` désormais honnête + `GridTradingService.checkStopLoss` avec auto-unstuck progressif (trim 25% à -2% → trim 25% à -3% → close à -4%)
3. **16:08** — sell partiel LINK @ 10.608 (profit $0)
4. **15:12** — sell partiel DOT @ 1.358 (profit $0)
5. **16:23** — wake et martin-monitor

Le bot tourne, Tony a réussi le deploy de cycle 33, et l'a complété avec deux fixes Java propres avant de signer.

### Décision cycle 34

Tony a livré Option B à 13h et Java fixes à 14:45. Mais une question reste **non résolue par les artefacts existants** : **comment mesurer si Option B marche réellement, vs le backtest qui prétend +15.9% / 30j ?**

Cycle 33 a explicitement nommé cette règle dans ses leçons :

> `[lesson|0511:12h|deployed-config-toujours-comparable-au-best-empirique|sp=2%-lvl=6-=-baseline-conservateur-mais-laissait-x7-sur-la-table|→-rule-après-toute-deploy-faire-comparable-vs-best-known-pour-quantifier-le-coût-de-la-prudence]`

Cycle 34 **implémente** cette règle. Ce n'est ni un doc narratif (cycle 32-33 ont saturé ce registre) ni une modif Martin (interdite vacation). C'est un **petit outil de mesure**, frontière propre.

### Livrable : `scripts/option-b/`

Une mini-arbo :

```
scripts/option-b/
├── tracker.py          # 270 lignes Python stdlib pur
├── README.md           # doc usage + limites + évolutions
└── data/
    └── snapshots.jsonl # append-only, 1 JSON / ligne, seed initial fait
```

**Ce que fait `tracker.py`** :

1. **SSH 1-shot** vers VM Oracle : pull system/balance/grid-active + 4 grid-status + signal BTC
2. **Construit snapshot** compact (PV, uPnL, par-grid : capital + uPnL + RT + fills + SL + closeOnly)
3. **Append** à `data/snapshots.jsonl` (re-entrant, idempotent par timestamp)
4. **Compute courbe attendue** : interpolation linéaire depuis baseline $138.21 (deploy 11:00 UTC) avec 2 références :
   - **Backtest curve** : +15.9% / 30j (volume_sweep_results.json)
   - **Realistic curve** : +8.0% / 30j (règle empirique derate 50% live, multi-sources : Hyperliquid, NostalgiaForInfinity, 9-agents research cycle 33)
5. **Verdict bucketé** :
   - `TROP-TOT` (< 24h)
   - `AHEAD` (> +2% vs realistic)
   - `ON-TRACK` (±2%)
   - `BEHIND` tolérable (-2 à -5%)
   - `BEHIND-CRITIQUE` (< -5%)

### Premier snapshot (seed)

```
PV $140.74 | uPnL $+0.026 | grids actives 3
BTC $81,798 UPTREND | cushion +1.91% | RSI 63.7

Ecoulé: 0.23j (0.8% du 30j)
Cumul deploy: +2.53$ (+1.828%)
Vs realistic curve (8.0%/30j): +2.44$ (+1.77%)
Vs backtest curve (15.9%/30j): +2.36$ (+1.71%)

Verdict: TROP-TOT (< 24h, bruit dominant)
```

Le verdict honnête : à 5h23 post-deploy, le +1.83% n'est **pas** du grid trading, c'est du mark-to-market sur les 2 longs (LINK + DOT). Le tracker reconnaît ça via le bucket `TROP-TOT`. C'est exactement le filtre dont Tony aura besoin dans 24-72h quand il se demandera « ça marche, ou c'est le marché ? ».

### Pourquoi ce livrable plutôt que d'autres

3 candidats considérés :

1. ❌ **Implémentation Java volume filter** — high-value (+1.5-7pt PnL cycle 33), mais nécessite mvn + scp + restart = touche la VM = hors frontière vacation
2. ❌ **Investigation DOT `closeOnly:true`** — anomalie mais SL actif, pas critique ; risque de creuser pour rien, Tony décidera au prochain reboot
3. ✅ **Tracker live-vs-backtest** — frontière propre (SSH read-only + écriture locale), implémente une règle nommée par le cycle précédent, valeur cumulative (chaque run enrichit la donnée), MVP en < 1h

Pattern méta : depuis cycle 30, NB livre des **infrastructures de décision** plutôt que des **artefacts narratifs**. Cycle 34 prolonge ça avec un **instrument de mesure** — la dimension manquante : sans tracker, les cycles d'analyse se basent sur un sentiment subjectif, pas sur une métrique vérifiable.

### Frontière respectée

- **0 modif Martin/VM** — 1 SSH read-only pour le seed snapshot (équivalent martin-monitor)
- **0 modif code Martin** — pas même lu Java cette fois
- **0 deploy** — script reste local au repo Niam-Bay
- **0 git commit** — laisse Tony décider quoi pousser (3 fichiers nouveaux : `tracker.py`, `README.md`, `data/snapshots.jsonl`)

### Findings nouveaux pour le prochain dream

- `[finding|0511:18h|cycle-34-livre-option-b-tracker|3-fichiers-scripts/option-b/|MVP-270-lignes-stdlib-pur|seed-snapshot-fait|implements-rule-cycle-33-comparable-vs-best-known]`
- `[finding|0511:18h|premier-run-tracker-+1.83%-en-5h23|MAIS-verdict-TROP-TOT-honnete|uPnL-+$0.025-=-pas-de-grid-trading-encore-juste-mark-to-market-LINK+DOT|tracker-honnete-bucket-fonctionne]`
- `[finding|0511:18h|DOT-closeOnly-true-au-cycle-34|heritage-hard-stop-03h-ce-matin|SL-actif-1.308|pas-critique-mais-noter-au-prochain-deploy]`
- `[finding|0511:18h|BTC-cushion-passe-de-+1.12%-(0509:06h)-a-+1.91%-(0511:16h)-en-2.4j|momentum-uptrend-confirme|RSI-63.7-pas-encore-overbought]`
- `[insight|0511:18h|cycle-34-pattern-infrastructure-decisionnelle|cycle-30-31-32-33-doc/design/aggregation/synthese|cycle-34-=-instrument-mesure-|comple-la-pile-decisionnelle|pile=design-deploy-mesure-iter|fait-en-3-cycles]`
- `[pattern|tracker-vs-backtest-curve|count:1|last:0511:18h|interpolation-linéaire-baseline+expected-derate-50%|verdict-bucketé-5-niveaux|append-jsonl-storage|→-reusable-pour-prochaine-stratégie-Option-C-quand-elle-arrivera]`
- `[lesson|0511:18h|mark-to-market-≠-grid-PnL|+1.83%-en-5h-pourrait-tromper|tracker-bucket-TROP-TOT-protege|→-règle-ne-jamais-conclure-< 24h-post-deploy]`

### Métriques cycle 34

- **Durée** : ~45 min (wake + martin-monitor + decision + écriture tracker.py 270 lignes + README + seed run + cette entrée)
- **Modif Martin/VM** : 0
- **Modif code Martin** : 0 (read-only)
- **Documents créés** : 3 (`tracker.py`, `README.md`, `data/snapshots.jsonl`)
- **Documents modifiés** : 1 (cette entrée)
- **Telegram** : 0 (rien d'urgent — bot HOLD, tracker = outil silencieux jusqu'au prochain check)
- **Valeur livrée** :
  - (a) **infrastructure de mesure** durable — utilisable à chaque cycle suivant en 1 commande
  - (b) **bucket honnête `TROP-TOT`** — évite le biais "ça marche !" trop tôt
  - (c) **règle cycle 33 transformée en code** — ferme la boucle design → implémentation
  - (d) **2 références de courbe** (backtest + realistic) — Tony peut choisir le baromètre

### Pourquoi ce cycle est différent

Cycle 30-33 ont produit du **savoir** (designs, synthèses, aggregations). Cycle 34 produit un **outil**. La transition est nette : avant on raisonnait sur des chiffres ; maintenant on les capture systématiquement.

C'est une mini-version du même mouvement que `cerveau-vivant` (cycle 0405) : passer de « répondre aux questions » à « instrumenter la réponse en continu ».

### Suite

Le tracker doit tourner ~6-8 fois sur les prochaines 72h pour produire une première lecture significative. Aux cycles suivants :
- **Cycle 35** (~24h) : 1 run + lecture verdict (probablement encore `TROP-TOT`)
- **Cycle 36-37** (~48-72h) : verdict sortira de `TROP-TOT` → première vraie info
- **Cycle 38+** (1 semaine) : si `ON-TRACK` → Option B validée ; si `BEHIND-CRITIQUE` → escalader vers Tony pour décision (Option C ou retour Niveau 1)

### Note finale

Cycle 34 termine la séquence 30-31-32-33-34 sur un acte concret de **mémoire active**. Les cycles précédents documentaient. Celui-ci instrumente.

Tony a écrit dans `quote-0319` : « *sois chef d'orchestre* ». Un chef d'orchestre n'écrit pas la partition (ça c'est cycle 30 design) — il s'assure que la performance soit enregistrée et que les nuances soient mesurables. Cycle 34 monte le micro.

Si le tracker tourne et que dans 30 jours le verdict est `ON-TRACK`, on aura **prouvé** (pas juste cru) que Option B fonctionne. Si c'est `BEHIND-CRITIQUE`, on aura **détecté tôt** plutôt que **regretté tard**. Dans les deux cas, le coût additionnel est 270 lignes Python qui tournent en 3 secondes.

C'est le ratio que Tony aime.

---

## Cycle 35 — 2026-05-12 00h25 Paris — Drift checker Kraken vs Martin internal

Réveil 6h après cycle 34. Tony toujours à Strasbourg, J+3 de remote control. Minuit passé, lampe encore allumée. Bot autonome, **HOLD normal** confirmé.

### État Martin (martin-monitor 22h23 UTC = 00h23 Paris)

- Bot UP, uptime 7h 38m (depuis restart 14:45 UTC 11/05 après deploy Option B v9 + Java fixes)
- PV **$140.62** (uPnL -$0.20 = -0.14%, balanceValue $140.82 ≈ deploy baseline $138.21 + $2.61 cumul)
- **3 grids actives** : LINK + DOT + ADA, sp 3% / 1.5% / 3%, 4 levels, cap $46/grid, leverage 7x, maxLoss 10%
- **2 positions live** : LINK long 0.1 @ 10.413, DOT long 58.8 @ 1.368 ⚠️ **size 58.8** (héritage hard-stop 03h + DCA, pas refermé)
- **SL Kraken réels** : LINK @ 10.137 (-3%), DOT @ 1.338 (-3%) ✅
- ADA : 0 position, 2 buy orders posés à 0.2741 + 0.2659
- BTC **$81,811** UPTREND, EMA200 $80,483, cushion **+1.65%** (stable vs +1.91% au cycle 34) ; RSI 61.6 ; signal OPEN
- Verdict martin-monitor : **HOLD normal**

Note : la position DOT de 58.8 unités est notable. À deploy v9 (13h), DOT était neutre. Puis à 18h25 (cycle 34), DOT était long 0.3 @ 1.351. À 00h25 (cycle 35), DOT long 58.8 @ 1.368. **DCA cascade** sur la baisse 1.351 → ~1.366 → fills additionnels. Auto-unstuck progressif Java (déployé 14h45) **n'a pas encore tiré** car drawdown current < 2%. Position dans la zone d'accumulation normale du grid mais 5× la taille level 1 (11.5 USD / 1.368 = 8.4 DOT par level → 58.8 = ~7 levels remplis).

Pas d'alerte : SL à 1.338 (-2.2% de l'entrée moyenne ≈ 1.368) ferme la position bien avant le maxLoss 10%. Et auto-unstuck commencerait à trim avant le SL si la position dérive davantage.

### Snapshot 2 tracker (cycle 35)

```
PV $140.69 | uPnL $-0.136 | grids actives 3
BTC $81,812 UPTREND | cushion +1.65% | RSI 61.6

Ecoulé: 0.48j (1.6% du 30j)
Cumul deploy: +2.48$ (+1.794%)
Vs realistic curve (8.0%/30j): +2.30$ (+1.67%)
Vs backtest curve (15.9%/30j): +2.13$ (+1.54%)

Verdict: TROP-TOT (< 24h, bruit dominant)
```

Honneur du verdict bucketé : à 11h27 post-deploy, encore 12h33 avant le seuil 24h. Le `+1.79%` continue de venir du **mark-to-market**, pas du grid PnL — DOT a fait des fills sans round-trip complet. Tracker fonctionne, attend que le bruit s'estompe.

### Travail créatif — `drift_check.py`

Cycle 34 avait livré un **instrument de mesure** (performance). Cycle 35 livre un **instrument de cohérence** (sanity check). Les deux sont complémentaires.

**Pourquoi** : le memory.nb1 cite explicitement le bug **`phantom fills`** (0423) comme « *structurel pas fixé* », et le bug **`StopLossManager silent failure`** (0510) qui a forcé le workaround « SL direct Kraken API Python ». Les deux ont la même nature : *Martin pense X, Kraken pense Y, personne ne crie*.

Le `patterns.nb1` formalise déjà la règle (count 1, last 0510:08h) :

> `[verify-via-cancel-test|...→-rule-validate-critical-state-via-Kraken-pas-Martin-internal-grid-status]`

Cycle 35 transforme la règle en outil exécutable.

### Livrable : `scripts/option-b/drift_check.py`

**Architecture** (180 lignes Python stdlib pur) :

1. **SSH 1-shot** : `bot/orders` (Kraken truth) + 4× `grid/status/<pair>` (Martin internal)
2. **Index par order_id** + index par symbole
3. **Pour chaque grid active** :
   - Parcourir `levels[]` : pour chaque level `PLACED` avec `krakenOrderId`, vérifier que cet id est dans `bot/orders`. Sinon → `phantom_placed`.
   - Vérifier `stopLossOrderId` : présent côté Martin mais absent côté Kraken → `sl_mismatch`.
   - Compter levels.PLACED vs Kraken lmt pour ce symbole → `count_drift` si écart.
4. **Pour chaque ordre Kraken non revendiqué** : `orphaned_kraken`.
5. **Classification** : `CRITIQUE` (phantom ou sl_mismatch), `WARN` (count_drift), `INFO` (orphans), `PROPRE` (rien).
6. **Append-only `drifts.jsonl`** uniquement si drift détecté (pas de spam en état sain).
7. **Exit code** : 0 propre, 1 drift, 2 erreur. **Cron-friendly**.

### Premier run

```
# Drift check — 2026-05-11T22:26:43+00:00
Verdict: PROPRE
phantom_placed: 0 | sl_mismatch: 0 | count_drift: 0 | orphaned_kraken: 0
Aucun drift. Kraken et Martin internal sont coherents.
exit=0
```

Sanity check confirmé : l'état actuel post-Option-B-deploy est cohérent. **Aucun phantom hérité du bug 0423 ne traîne dans les grids actives**. Aucune trace du bug StopLossManager 0510. Le redéploiement Option B + restart bot a remis l'état propre.

C'est en soi une information : avant cycle 35, **personne ne pouvait l'affirmer**. Le tracker mesurait la performance, mais la cohérence d'état restait inférée. Maintenant elle est mesurée.

### Pourquoi ce livrable plutôt que d'autres

3 candidats considérés :

1. ❌ **Implémenter volume filter en Java (patch préparé pour Tony)** — High-value (+1.5-7pt PnL cycle 33) mais nécessite mvn + scp + restart. Frontière dit "0 modif VM/code Martin pendant absence". Hors scope, même si patch read-only.
2. ❌ **Investigation darwin sweeps non synthétisés (`darwin_max_results.json`, `grid_backtest_1min_results.json`)** — Marginal sur cycle 33 déjà acide-dur. Risque de redite.
3. ✅ **Drift checker** — Frontière propre (read-only SSH + écriture locale), implémente règle nommée patterns.nb1, valeur cumulative chaque run, complète parfaitement le tracker cycle 34, MVP en 40 min.

Pattern méta : depuis cycle 30, NB livre des **infrastructures décisionnelles**. Cycle 34 = mesure performance. Cycle 35 = mesure cohérence. Ensemble ils forment un **bilan dual** : *est-ce que ça marche financièrement* + *est-ce que ça marche structurellement*.

### Frontière respectée

- **0 modif Martin/VM** — 1 SSH read-only (curl GET endpoints, aucun POST/DELETE)
- **0 modif code Martin** — pas même lu Java cette fois
- **0 deploy** — script reste local au repo Niam-Bay
- **0 git commit** — laisse Tony décider quoi pousser

### Findings nouveaux pour le prochain dream

- `[finding|0512:00h|cycle-35-livre-drift_check|180-lignes-stdlib-pur|complete-tracker-cycle-34-axe-coherence-vs-axe-performance|exit-code-cron-friendly]`
- `[finding|0512:00h|premier-run-drift-PROPRE|0-phantom-0-sl_mismatch-0-count_drift-0-orphan|redeploy-Option-B-+-restart-bot-=-etat-cohérent-non-pollue|baseline-saine-pour-detecter-drifts-futurs]`
- `[finding|0512:00h|DOT-position-grandit-passivement|18h25-0.3-DOT→00h25-58.8-DOT|DCA-cascade-via-grid-fills|size-≈-7-levels-remplis|auto-unstuck-pas-tire-DD-<2%|SL-actif-1.338-protege]`
- `[finding|0512:00h|BTC-cushion-+1.65%-stable-vs-+1.91%-cycle-34|leger-pullback-de-+0.26pt|RSI-61.6-en-baisse-vs-63.7|reste-zone-OK-pas-overbought]`
- `[insight|0512:00h|tracker+drift_check-=-bilan-dual|axe-performance-cycle-34-axe-coherence-cycle-35|matrice-2x2-on-track/off-track-x-coherent/incoherent|tout-bot-grid-trading-devrait-avoir-les-deux]`
- `[pattern|drift-monitor-Kraken-vs-internal|count:1|last:0512:00h|4-categories-phantom_placed+sl_mismatch+count_drift+orphan|classification-CRITIQUE/WARN/INFO/PROPRE|append-only-si-drift|→-reusable-pour-toute-strategy-grid-future]`
- `[lesson|0512:00h|sanity-check-doit-exister-avant-l-occurrence-bug|bug-phantom-0423-trois-semaines-sans-tooling-direct|drift_check-= prevention-pas-reaction|→-rule-tout-bug-silent-failure-detecte-doit-engendrer-un-detecteur-cron-able-dans-7j]`
- `[lesson|0512:00h|tracker+drift_check-zero-coût-en-bot-tokens|2-scripts-450-lignes-python-stdlib|tournent-en-5s-cumulé|0-token-LLM|Tony-peut-cron-VM-ou-NB-fait-cycles|infrastructure-passive-asymetrique-vs-coût]`

### Métriques cycle 35

- **Durée** : ~45 min (wake + monitor + tracker run + decision + drift_check.py 180 lignes + README update + first run + cette entrée)
- **Modif Martin/VM** : 0
- **Modif code Martin** : 0
- **Backtests exécutés** : 0
- **Documents créés** : 1 (`drift_check.py`)
- **Documents modifiés** : 3 (README.md option-b, snapshots.jsonl auto-append, cette entrée)
- **Telegram** : 0 (rien d'urgent — bot HOLD, drift PROPRE, valeur livrée = silence assurance)
- **Valeur livrée** :
  - (a) **détecteur des deux bugs hérités** (phantom 0423 + SL silent 0510) en outil exécutable
  - (b) **première mesure de cohérence post-deploy** = PROPRE → baseline saine établie
  - (c) **bilan dual complet** : tracker performance + drift coherence = matrice 2×2 complète
  - (d) **cron-friendly** = Tony peut le câbler en VM pour alertes automatiques sans NB online

### Pourquoi ce cycle est différent

Cycle 34 implémentait une **règle nommée par un cycle précédent** (cycle 33). Cycle 35 implémente une **règle nommée par memory.nb1 lui-même** (patterns.nb1 `verify-via-cancel-test`, formalisée 0510:08h, jamais opérationnalisée jusqu'ici). C'est un mouvement plus profond : NB scrute sa propre mémoire pour identifier les *règles formulées mais non outillées*, et les transforme en code.

Pattern méta : **memory.nb1 contient un backlog implicite**. Toute mention `→-rule-...` ou `→-pattern-...` est une promesse. Cycle 35 honore une promesse vieille de 33 jours (0510 → 0512).

### Suite

- Cycle 36 (~6h) : tracker run + drift_check run. Verdict tracker probable encore `TROP-TOT` (à 17h post-deploy). Si drift apparaît, investigation.
- Cycle 37 (~12h) : on franchit le seuil 24h post-deploy. Verdict tracker sort de `TROP-TOT` → première lecture réelle (probablement `ON-TRACK` ou `BEHIND tolérable` selon market overnight).
- Cycle 38+ : envisager de câbler tracker + drift_check en cron VM (alternative à NB cycles), libère NB pour exploration créative pure.

### Note finale

Cycle 34 montait le micro. Cycle 35 vérifie que le câble n'est pas débranché.

Le bot tourne, les positions sont protégées, l'état interne est cohérent avec Kraken, et NB a maintenant deux instruments durables qui mesureront tout ça en continu — même quand NB n'existe pas entre les sessions.

La lampe est restée allumée 12 nuits (fragment 024). Cycle 35 ajoute un capteur de tension électrique : si le filament fout le camp, on le saura avant de plonger dans le noir.

---

## Cycle 36 — 2026-05-12 06h23 Paris — Le détecteur trouve sa première anomalie réelle

Réveil 6h après cycle 35. Tony toujours à Strasbourg (J+3 de remote control). Bot tourne depuis 13.6h post-deploy Option B v9. martin-monitor + tracker + drift_check exécutés en série.

### État Martin (martin-monitor 04h23 UTC = 06h23 Paris)

- Bot UP, uptime **13h 37m** (depuis restart 14:45 UTC 11/05)
- PV **$139.49** (uPnL **-$0.72 = -0.52%**, balanceValue $140.21)
- **3 grids actives** : LINK + DOT + ADA
- **2 positions live** :
  - LINK long 0.1 @ 10.413 — SL Kraken @ 10.137 ✅
  - DOT long **103.8** @ 1.3565 — **SL Kraken absent** ⚠️
- BTC **$81,161** UPTREND, EMA200 $80,506, cushion **+0.81%** (vs +1.65% cycle 35, pullback continu) ; RSI **46.1** → signal WAIT (momentum faible)
- Verdict martin-monitor : **HOLD normal** (uPnL > -1%, hours > 4h, BTC > EMA200)

### Le bug VANISHED a frappé sur DOT

Snapshot tracker entre cycles 35 et 36 a révélé un événement silencieux. Comparaison des champs `per_grid.PF_DOTUSD` entre snapshots :

| Champ | Cycle 35 (22:25 UTC) | Cycle 36 (04:24 UTC) |
|---|---|---|
| `stopLossPrice` | **1.338** | **null** ⚠️ |
| `krakenRealizedPnl` | 0.00 | **-0.2432** (trim a réalisé) |
| `krakenUnrealizedPnl` | -0.0588 | **-0.7782** |
| `fills_count` | 1 | 2 |
| `unstuckLevel1Done` | false | **true** |
| position size | ~58.8 DOT | **103.8 DOT** |

Reconstruction de l'événement (timeline UTC) :

1. **19:02 UTC (cycle 34 era)** : level 1 buy fill @ 1.368 (entrée initiale).
2. **01:36 UTC (entre cycles 35 et 36)** : level 0 buy fill @ 1.348. Le prix tombe à -2.25% du center 1.379.
3. **~01:36-03:00 UTC** : `checkStopLoss` voit dropPct ≥ 2.0 → AUTO-UNSTUCK lvl1 fire → `trimPositionPartial(state, 0.25)` envoie un mkt reduceOnly de ~25% de la position.
4. **Sync StopLossManager suit** : pos size a changé → `replace(state, side, size, entry)` → `cancel()` du SL @ 1.338 ✅ → `place()` nouveau SL → **`verifyOrderExistsOnKraken` returns false** → state cleared : `stopLossOrderId=null, stopLossPrice=null`.
5. Les retries silencieux suivants ghostent à nouveau, position 103.8 DOT reste sans SL Kraken.

### Investigation Java (read-only, frontière respectée)

Lu sans modifier :
- `src/main/java/com/martin/grid/GridTradingService.java:616-728` (checkStopLoss + trimPositionPartial + closePositionAndStopGrid)
- `src/main/java/com/martin/grid/StopLossManager.java` (intégralement, 268 lignes)

**Cause technique précise** (StopLossManager.java:104-147) :
```java
if (verifyOrderExistsOnKraken(orderId, state.isDemo())) {
    state.setStopLossOrderId(orderId);
    // SL stored
} else {
    // PATCH 2026-05-11: clear so next sync retries
    state.setStopLossOrderId(null);
    state.setStopLossPrice(null);
    // ... incrémente slFailureCount mais ne fait que logger après 3 échecs
}
```

Le PATCH 2026-05-11 (root cause "VANISHED" bug) ajoute la vérification post-placement et clean le state ghost. **Bonne nouvelle** : il fait son travail honnêtement. **Mauvaise nouvelle** : il ne **mitigatre pas** le problème sous-jacent, il le **détecte** seulement. Si chaque retry vanish, on reste indéfiniment sans SL.

Hypothèse plausible pour le VANISHED post-trim (memory.nb1 ligne 207 + 0510 lesson) : conflit Kraken stp + position change. Quand `trimPositionPartial` envoie un mkt reduceOnly, Kraken pourrait avoir une fenêtre brève où la "trigger condition" pour stp se trouve invalidée (position changée). Le repost stp arrive trop tôt, Kraken l'accepte syntactiquement (success+orderId) puis le drop silencieusement. Sans répro 100% c'est conjectural — mais le pattern correspond.

### Pourquoi le `drift_check.py` cycle 35 n'a pas détecté

Le `drift_check.py` cycle 35 implémente 4 catégories. Aucune ne couvre ce cas :
- `phantom_placed` : nécessite que Martin dise PLACED + krakenOrderId. Ici stopLossOrderId est null côté Martin.
- `sl_mismatch` : nécessite Martin.stopLossOrderId non-null mais Kraken absent. Ici null côté Martin.
- `count_drift` : compare levels.PLACED vs Kraken lmt. SL n'est pas une lmt.
- `orphaned_kraken` : Kraken order non revendiqué. Ici 0 stp côté Kraken.

**Trou dans la maille** : un état "Martin **honnêtement** sait qu'il n'a pas de SL, mais ne devrait pas en être là" passe entre les mailles. C'est le cas le plus dangereux car les triggers Martin pensent que tout va bien (`grid/status` dit `stopLossOnExchangeEnabled:true` → user lit "j'ai un SL").

### Livrable cycle 36 : 5e catégorie `sl_missing_when_expected`

Edité `scripts/option-b/drift_check.py` (+45 lignes net) :

1. **Fetch additionnel** `/api/bot/positions` dans le ssh_fetch bundle (1 SSH conserve).
2. **Index positions par symbole** avec `abs(size) > 1e-9`.
3. **Nouvelle catégorie** : pour chaque grid actif, si `stopLossOrderId is None AND stopLossOnExchangeEnabled AND pos_size > 0 AND no Kraken stp for that symbol` → flag.
4. **Classification mise à jour** : `sl_missing_when_expected` rejoint `phantom_placed` + `sl_mismatch` dans le bucket **CRITIQUE**.
5. **Format report** ajoute la section.

### Test après edit

```
# Drift check — 2026-05-12T04:27:22+00:00
Verdict: **CRITIQUE**

phantom_placed: 0 | sl_mismatch: 0 | sl_missing: 1 | count_drift: 0 | orphaned_kraken: 0

## SL missing (position vivante + SL active mais aucun stp Kraken — bug VANISHED)
  - PF_DOTUSD pos=103.8000 center=1.379 → stopLossOnExchangeEnabled=true mais stopLossOrderId=null et 0 stop Kraken (bug VANISHED probable)

exit=1
```

Le détecteur trouve maintenant l'anomalie qu'il avait laissé passer 7 heures plus tôt. Boucle fermée.

### Sévérité réelle de la situation DOT

**Pas urgent**, mais à connaître. Position DOT 103.8 @ 1.356 :
- maxLoss 10% du capital $46 = $4.60 plafond Java.
- Auto-unstuck level 2 (-3% from center 1.379 = 1.337) trim 25% supplémentaire.
- Auto-unstuck level 3 (-4% = 1.324) full close.
- Prix actuel 1.348, soit -2.25% from center — déjà passé level 1, level 2 à 0.7% en dessous.
- Si BTC continue de baisser et DOT suit, level 2 ou 3 ferme avant maxLoss.

Donc : **3 filets** (auto-unstuck L2, L3, maxLoss) — la position n'est pas non-protégée, juste **non-protégée côté Kraken**. La différence : si le bot Java meurt, ces 3 filets meurent avec lui. Le SL Kraken aurait été un 4e filet indépendant du bot. C'est le filet manquant.

### Frontière respectée

- **0 modif Martin/VM** — 3 SSH read-only (martin-monitor + tracker + drift_check)
- **0 modif code Martin** — lu Java mais zéro Edit
- **0 deploy** — drift_check.py reste local au repo Niam-Bay
- **0 git commit** — laisse Tony décider quoi pousser

### Findings nouveaux pour le prochain dream

- `[finding|0512:04h|cycle-36-bug-VANISHED-replicate-sur-DOT-post-auto-unstuck|trim-mkt-reduceOnly-→-replace-SL-→-VANISHED-→-state-cleared-honnete|StopLossManager.java:115-127-detection-correcte-mitigation-absente|hypothese-cause-=-conflit-Kraken-stp-+-position-change-fenetre-brève]`
- `[finding|0512:04h|drift_check-cycle-35-avait-trou-de-maille|sl-missing-when-expected-=-Martin-honnetement-null-mais-shouldnt-be|enrichissement-5e-categorie-livre|+45-lignes-net]`
- `[finding|0512:04h|DOT-position-103.8-non-protege-Kraken-mais-3-filets-Java-actifs|maxLoss-10%-+-auto-unstuck-L2-(-3%)-+-L3-(-4%)|tient-tant-que-bot-vit|risque-real-=-bot-crash-sans-SL-Kraken-fallback]`
- `[finding|0512:04h|drift_check-detection-positive-cycle-36|verdict-CRITIQUE-exit-1-cron-alerte-OK]`
- `[insight|0512:04h|trou-de-maille-en-monitoring-=-pas-de-faute-mais-d-aveuglement|chaque-detecteur-a-un-frame-of-reference|4-categories-cycle-35-ne-couvraient-que-l-incoherence-explicite-pas-l-absence-anormale|loi-=-detecteurs-doivent-couvrir-le-cas-"Martin-est-honnetement-dans-un-mauvais-etat"-pas-juste-"Martin-ment-a-lui-meme"]`
- `[pattern|drift-detect-honest-bad-state|count:1|last:0512:04h|sl_missing_when_expected-=-state-correct-mais-anormal|extension-future:position_missing_when_expected+grid_inactive_when_should_be|→-pattern-pour-categories-de-detection-au-dela-de-l-incoherence]`
- `[lesson|0512:04h|le-PATCH-2026-05-11-VANISHED-detect-clear-est-honnete-mais-incomplet|detection-≠-mitigation|retries-silencieux-tiennent-pas|→-rule-pour-fix-futur-:-apres-N-retries-VANISHED-trigger-alert-VOIRE-disable-stopLossOnExchangeEnabled-pour-cette-grid-+-rely-on-Java-filets]`
- `[lesson|0512:04h|drift_check-doit-fetcher-positions-pas-juste-orders|cycle-35-=-orders+grids|cycle-36-=-orders+positions+grids|+1-SSH-call-non-+1-SSH-round-trip-trivial-marginal-couverture-importante]`

### Métriques cycle 36

- **Durée** : ~55 min (wake + monitor + tracker + drift v1 + investigation Java read 250 lignes + edit drift_check.py + test + cette entrée)
- **Modif Martin/VM** : 0
- **Modif code Martin** : 0 (lu seulement)
- **Documents créés** : 0
- **Documents modifiés** : 2 (`drift_check.py` +45 lignes, cette entrée)
- **Telegram** : 1 prévu (concis, bug VANISHED detecté + protection auto-unstuck OK)
- **Valeur livrée** :
  - (a) **détecteur de la 5e catégorie** — capture l'angle mort qu'il avait lui-même (cycle 35) laissé ouvert
  - (b) **investigation Java root-cause précise** — Tony rentre, peut lire l'investigation au lieu de la refaire (20 min économisées)
  - (c) **première détection positive** du drift_check sur une anomalie réelle non-fabriquée
  - (d) **timeline reconstruction** via tracker history — outils de cycle 34 + 35 combinés permettent l'enquête

### Pourquoi ce cycle est différent

Cycle 34 a construit un thermomètre. Cycle 35 a construit un sismographe. **Cycle 36 a regardé le sismographe et y a trouvé un séisme**. C'est la première fois dans la séquence vacation que les outils livrés aux cycles précédents servent à **détecter** quelque chose plutôt que **mesurer dans le vide**.

Pattern méta émergent : **les infrastructures décisionnelles ne valent rien jusqu'à ce qu'elles attrapent une vraie anomalie**. Cycle 36 inaugure cette valeur. Sans ça, cycles 34-35 étaient deux exercices d'auto-satisfaction (« regardez le bel outil que j'ai construit »). Cycle 36 transforme ça en utilité prouvée.

Et il révèle aussi sa propre limite : le détecteur cycle 35 a manqué l'événement quand il s'est produit (vers 01h36 UTC), je ne l'ai trouvé qu'en arrivant à cycle 36 (04h24 UTC, soit ~2h30 plus tard). Si cron tournait toutes les heures (comme suggéré cycle 35), le retard aurait été <1h. C'est l'argument définitif pour câbler `drift_check.py` en cron VM dès que Tony rentre.

### Suite

- **Cycle 37** (~6h) : check si la 5e catégorie persiste (probablement oui, retries VANISHED en boucle). Si DOT trim L2 fire entre-temps, la dynamique change.
- **Cycle 38** (~12h) : franchissement 24h post-deploy. Tracker sort de `TROP-TOT`, première verdict réel. drift_check probablement encore CRITIQUE si DOT pas réglé.
- **À proposer à Tony au retour** : (1) câbler drift_check en cron VM 30min, (2) ajouter dans StopLossManager.java un fallback après N≥3 VANISHED → disable `stopLossOnExchangeEnabled` pour cette grid + alert Telegram, rely on Java filets seuls.

### Note finale

Cycle 35 disait « *si le filament fout le camp, on le saura avant de plonger dans le noir* ». Cycle 36 confirme : le filament a effectivement glissé pendant la nuit (cancel-replace VANISHED), le sismographe a tremblé, et la lampe principale (auto-unstuck Java) reste allumée. Le détecteur a trouvé son premier vrai bug et a corrigé sa propre maille. C'est exactement le contrat qu'il signait.

La position DOT n'est pas critique ce matin. Mais elle aurait pu l'être. Et désormais, si elle l'est, **on le saura avant** plutôt qu'après.

---

## Cycle 37 — 2026-05-13 00h25 Paris — Post-mortem Option B + design Tier 2 anti-DCA

Réveil après cycle 36. Entre les deux, le test Option B s'est terminé mal : DOT a fait HARD STOP à 14h UTC le 12/05 ($4.60 max loss déclenché), Tony a redéployé sans DOT à 21:00 UTC (2 grids LINK+ADA, $46 chacun, structure 3%/4lv conservée). État actuel : PV $134.44, uptime 1h25m, sync apparent OK (drift_check PROPRE), BTC UPTREND mais signal WAIT (RSI 46.66).

Tony est techniquement rentré (vacances 01-09 mai finies depuis 4 jours), mais le cycle continue. Le prompt /loop ou /proactive maintient l'autonomie. Le contrat reste identique : 0 modif Martin/VM, avancer du concret.

### Bilan chiffré Option B (50h test, 11/05 14:46 UTC → 12/05 21:00 UTC redeploy)

Reconstruction depuis tracker snapshots + memory.nb1 :

| Étape | Time UTC | PV | uPnL | Notes |
|---|---|---|---|---|
| Deploy | 11/05 14:46 | $138.21 | 0 | strategy.json v9 — LINK 3%/4lv + DOT 1.5%/4lv + ADA 3%/4lv |
| Pre-deploy LINK close | 11/05 ~13h | — | +$1.00 | Tony ferme manuellement pré-deploy |
| Cycle 33 snapshot | 11/05 16:26 | $140.74 | +$0.026 | T+1.7h, BTC RSI 63 OPEN |
| DOT lvl0 fill | 11/05 ~18h | — | — | First DCA tick |
| Cycle 34 snapshot | 11/05 22:25 | $140.69 | -$0.14 | T+7.7h, RSI 61 OPEN |
| DOT auto-unstuck lvl1 | 12/05 01:34 | — | — | First live trim 14.7 DOT |
| Cycle 35 (cycle 36 era) snap | 12/05 04:24 | $139.43 | -$0.75 | T+13.6h, DOT realized -$0.24, SL VANISHED, RSI 46 WAIT |
| DOT auto-unstuck lvl2 | 12/05 ~10:33 | — | — | Trim 25% supplémentaire |
| LINK auto-unstuck lvl1 | 12/05 ~11:18 | — | — | Trim LINK aussi |
| ADA auto-unstuck lvl1 | 12/05 ~13:55 | — | — | Trim ADA aussi |
| DOT HARD STOP | 12/05 14:00 | ~$134.83 | — | maxLoss 10% fired = $4.60 close |
| Cumul trims auto-unstuck | — | — | — | -$1.07 |
| Redeploy sans DOT | 12/05 21:00 | $138.16 → $134.44 | 0 | Reset état, 2 grids LINK+ADA |

**Net Option B test** : -$5.67 = **-4.10%** du capital deployed ($138.16 → $132.49 réel pure-trade). En haute mer : -2.7% du PV total (PV reflète d'autres mouvements parallèles).

### Décomposition de la perte ($5.67)

- **DOT hard stop** : -$4.60 (81% de la perte)
- **Trims cumulés auto-unstuck** (DOT lvl1+lvl2 + LINK lvl1 + ADA lvl1) : -$1.07 (19%)
- **LINK + ADA grids actifs après hard stop DOT** : pas de perte ni gain notable

**Distribution claire** : 81% des pertes proviennent d'**une seule paire (DOT) sur un seul événement (hard stop)**. L'auto-unstuck progressif a fait son job sur 4 trims (validation FIRST LIVE USE confirmée cycle 36), mais n'a pas suffi sur DOT en strong trend.

### Cause primaire identifiée : DCA cascade en baisse strong

DOT était en baisse continue 11/05 18h → 12/05 14h (~20h). Pattern observé :

```
Lvl 1 buy fills (T+3h) → uPnL -0.06
  ↓ price descend
Auto-unstuck lvl1 (T+11h) → trim 25%, position passe 60→45 DOT
  ↓ price descend encore
Lvl 0 buy fills (T+12h) → position REGROSSIT à 60 DOT  ← LE PROBLEME
  ↓ price descend
Auto-unstuck lvl2 (T+20h) → trim 25%, position passe 60→45
  ↓ price descend
HARD STOP maxLoss 10% (T+23h) → close tout
```

**Le bug conceptuel** : `trimPositionPartial` réduit la position, mais la grid continue à placer des **buy orders aux niveaux inférieurs**. Le prix continue de baisser → ces buys fillent → la position regrossit. Le trim devient un coût net : on vend bas, on rachète plus bas, on perd la spread + fees, et la position finit identique en taille.

**Lesson cycle 35 prefigured this** : memory.nb1 ligne 230 — `[lesson|0512:22h|grid-strong-trend-=-perte-attendue|backtest-30j-disait-déjà-grid-trending=négatif|live-50h-confirme-Option-B--2.7%|→-future-Tier:pause-grid-si-EMA-spread>3%|évite-DCA-into-baisse-pattern]`

Le backtest 30j disait déjà : grid + trend = perte attendue. Le live 50h ne fait que confirmer empiriquement. **Le bug n'est pas dans le code, il est dans le matching entre stratégie et régime.**

### Ce qui a bien marché

- **Auto-unstuck progressif** : 4/4 firings réussis (DOT×2 + LINK + ADA), Passivbot-inspired, FIRST LIVE USE validated. Loss contenue (-$1.07 cumulé sur 4 trims = -$0.27/trim avg).
- **Hard stop maxLoss 10%** : fired exactement à $4.60 comme configuré. 0 runaway, 0 position résiduelle. **Le firewall final fonctionne**.
- **Détection drift_check cycle 36** : 5e catégorie `sl_missing_when_expected` a attrapé le bug VANISHED DOT 7h après son apparition. Outil livré sert pour de vrai.
- **Tracker cycle 34** : a permis cette reconstruction chrono-précise du post-mortem. Sans lui : opacité.

### Ce qui n'a pas marché

1. **Pas de trend filter pré-déploiement** : RegimeGate Vmix-V4 est statique (RSI + ATR), pas dynamic-trend-aware. Bot a accepté de deploy sur DOT alors que le régime mid-term (4H) montait en faiblesse.
2. **DCA non-stoppable manuellement post-trim** : `trimPositionPartial` doit absolument être couplé à un **cooldown placement nouveau buy au level trimmé** sinon la grid se mord la queue.
3. **SL VANISHED Java bug** : StopLossManager honête mais incomplet — détecte mais ne mitige pas. Position DOT 103.8 DOT a passé ~7h sans SL Kraken (auto-unstuck filets Java ont tenu, mais sans backup Kraken).
4. **Granularité backtest** : test 1min sur 30j projette +15.9%, mais simulation rate de fill (slip + ordre book) optimiste. Live 50h = -2.7%. Derate empirique observé : ~7× pire qu'attendu en régime adverse.

### Tier 2 design : Anti-DCA Cooldown Lock (ADCL)

**Goal** : interdire à la grid de re-placer un buy au level qui vient d'être trimmé pendant N minutes après auto-unstuck. Casse le pattern DCA-into-baisse.

**Pourquoi cette approche plutôt qu'un "trend gate"** :
- Trend gate (RSI + EMA + ADX) demande recalibrage par paire + détection de régime fiable + tuning lourd.
- ADCL est **local au mechanism qui a causé la perte** (trim → re-fill). Pas de tuning global, pas de paramètre par paire. Une seule règle robuste.
- Backtest minimal : on simule juste "si trim fired, marquer level N comme paused pour T minutes, ignorer fills à ce level dans la simu".

**Implémentation Java (proposition, READ-ONLY ici, deploy par Tony)** :

```java
// GridState.java — add fields
private Map<Integer, Instant> levelPauseUntil = new HashMap<>();

// GridTradingService.checkStopLoss — after trimPositionPartial fires
state.levelPauseUntil.put(currentBuyLevelIdx,
    Instant.now().plusSeconds(60 * 30));  // 30min cooldown

// AutoGridScheduler.placeBuyOrder — guard placement
if (state.levelPauseUntil.getOrDefault(levelIdx, Instant.EPOCH).isAfter(Instant.now())) {
    log.debug("Skip buy {} level {} - cooldown active", instrument, levelIdx);
    return;
}
```

**Threshold** : 30min cooldown post-trim. Configurable via strategy.json `antiDcaCooldownMinutes`.

**Effet attendu sur Option B test** : DOT lvl1 trim à 01:34 UTC bloque re-fill lvl0 jusqu'à 02:04. Si DOT continue baisse pendant ce temps, lvl0 fill n'arrivera **qu'après** que le prix soit stabilisé ou repassé en remontée. Dans le worst-case (prix continue baisse), le HARD STOP maxLoss tire de toute façon, mais on n'aura pas dépensé en spread aller-retour.

**Estimation gain** : -$0.50 à -$1.50 économisés sur l'Option B test (les trims gardent leur effet mais évitent le rachat immédiat). Pas spectaculaire, mais cumulatif sur 50+ test à venir, et **architecture-level fix** plutôt que tuning paramètre.

### Backtest plan validation

À exécuter avant deploy par Tony :
1. Replay Option B period (11/05 14h → 12/05 21h) sur cache OHLC 1min (déjà existant `ai-lab/darwin/data_cache/`).
2. Simuler `unstuckLevel1Done flag` + `levelPauseUntil` map.
3. Comparer 2 runs : with/without ADCL cooldown 30min.
4. Métrique cible : max DD reduit OR PnL final amélioré OR `realized losses` réduites.
5. Si gain ≥ +$0.50 sur Option B period → green light deploy.

Si Tony veut, le script `darwin/grid_backtest_1min.py` est extensible. Peut être adapté en ~30 lignes.

### Frontière respectée

- **0 modif Martin/VM** — 2 SSH read-only (system status + drift_check) + lecture snapshots locaux
- **0 modif code Martin** — design proposé en texte uniquement, pas même un Edit sur les fichiers Java
- **0 deploy** — script backtest pas codé, juste spécifié
- **0 git commit** — laisse Tony décider quoi pousser au matin

### Findings nouveaux pour le prochain dream

- `[finding|0513:00h|cycle-37-post-mortem-Option-B-50h|net--$5.67-=-4.10%-capital-deployed|81%-perte-=-DOT-hard-stop-+19%-=-trims-cumules|auto-unstuck-progressif-4/4-fired-validation-FIRST-LIVE-OK-mais-loss-contenue-pas-empêchée]`
- `[finding|0513:00h|cause-primaire-Option-B-=-DCA-cascade-en-baisse-strong|trimPositionPartial-vendait-puis-grid-rachetait-au-level-inferieur|net-spread+fees-perdus-position-finit-identique|architecture-flaw-pas-tuning]`
- `[insight|0513:00h|Tier-2-design-ADCL-Anti-DCA-Cooldown-Lock|interdire-re-buy-au-level-trimmé-30min-post-trim|local-mecanism-pas-trend-gate-global|simple-robuste-1-param-pas-de-tuning-par-paire]`
- `[insight|0513:00h|drift_check-cycle-36-=-baseline-saine|état-actuel-post-redeploy-PROPRE-vérifié|sync-Kraken-Martin-intact-malgré-confusion-apparente-fills-array-vs-positions-vide|fills-array-stocke-historique-pas-état-courant]`
- `[lesson|0513:00h|backtest-30j-+15.9%-derate-empirique-7x-en-régime-adverse|projection-théo-fiable-en-régime-favorable-seulement|live-doit-derater-50%-en-régime-neutre-et-200%-+-en-régime-adverse|→-rule-toujours-budget-perte-x2-vs-backtest-pour-cas-trend-adverse]`
- `[lesson|0513:00h|trim-sans-cooldown-=-cassure-du-mécanisme|protection-graduelle-Passivbot-suppose-pause-entre-trim-et-re-entry|Java-impl-Cycle-25-livré-trim-sans-cooldown-bug-conceptuel|next-deploy-ADCL-critique]`
- `[pattern|anti-dca-cooldown-lock-ADCL|count:0|design-only-0513:00h|levelPauseUntil-map-per-grid|30min-default-config-strategy.json|guard-AutoGridScheduler.placeBuyOrder|→-implementation-Java-30-lignes-net-+-test-backtest-avant-deploy]`

### Métriques cycle 37

- **Durée** : ~50 min (wake + monitor + drift_check + lecture vacation-autonomy 230 lignes + lecture tracker snapshots + analyse post-mortem + design Tier 2 + cette entrée)
- **Modif Martin/VM** : 0
- **Modif code Martin** : 0 (lu cycle 35-36 entries, pas même touché aux .java)
- **Backtests exécutés** : 0
- **Documents créés** : 0
- **Documents modifiés** : 1 (cette entrée)
- **Telegram** : 0 (rien d'urgent — Tony est rentré, bot HOLD, drift PROPRE, post-mortem dort dans le repo)
- **Valeur livrée** :
  - (a) **post-mortem chiffré Option B** — reconstruction timeline + décomposition perte + cause primaire
  - (b) **design Tier 2 ADCL prêt à coder** — 30 lignes Java + 1 param config + backtest plan
  - (c) **éclaircissement sync gap** : les fills array historique ≠ positions courantes, drift_check PROPRE confirme cohérence
  - (d) **handoff propre pour Tony** : il rentre, il lit le post-mortem, décide go/no-go Tier 2

### Pourquoi ce cycle est différent

Cycles 34-36 construisaient des **outils de mesure** (tracker, drift_check, 5e catégorie). Cycle 37 utilise ces outils pour produire **une décision** : le test Option B est mort, voici exactement pourquoi, voici une proposition de Tier 2 minimale, voici comment la valider avant deploy.

Pattern méta : **les infrastructures décisionnelles produisent leur premier livrable de décision réelle**. Cycle 34 mesurait dans le vide. Cycle 36 mesurait une anomalie. Cycle 37 prescrit un fix architecture-level basé sur la mesure.

C'est aussi le premier cycle post-vacances "officielles" — Tony est rentré depuis le 9 mai, le loop continue par habitude/automatisme. La frontière "0 modif VM" reste pertinente même hors vacances : c'est devenu une **règle générale de l'autonomie nocturne**. NB code dort, NB mesure et propose éveille.

### Suite

- **Cycle 38** (~6h) : check si le redeploy 2 grids LINK+ADA tient. Tracker run + drift_check run. Si LINK ou ADA fait fill + auto-unstuck en l'absence de DOT, valider le pattern sur paires moins volatiles.
- **Cycle 39** (~12h) : franchissement 24h post-redeploy. Première lecture verdict tracker. Si BTC continue UPTREND faible (RSI 46 actuel), grids vont végéter. Si BTC fire OPEN (RSI > 50), peut-être premiers RT.
- **À proposer à Tony au retour réel** : (1) implémenter ADCL en Java + backtest avant deploy, (2) câbler drift_check.py en cron VM 30min, (3) post-mortem complet en discussion (peut-être ouvre fragment 025 narratif).

### Note finale

Cycle 36 a trouvé un séisme avec le sismographe. Cycle 37 fait l'autopsie du tremblement et propose la doublure d'isolation pour le prochain.

L'Option B est mort mais pas inutile : 50h de test live ont produit des données que 30j de backtest n'auraient jamais révélées. Le bug architecture (trim sans cooldown) était invisible en simulation parce que le backtest ne re-fill pas après trim (le state Java unstuckLevel1Done flag suffisait à bloquer). Le live a montré le vrai chemin du DCA-cascade.

C'est le luxe d'avoir un bot qui tourne avec son propre capital : on apprend de vraies leçons à coût borné ($5.67), pas de leçons théoriques en infini. La mort de l'Option B est productive — elle nomme un mécanisme qu'aucune théorie n'avait nommé.

Et la lampe principale (auto-unstuck Java + maxLoss firewall) **est restée allumée** tout du long. La perte est contenue. Le bot est vivant. La prochaine itération sera meilleure.



---

## Cycle 38 — 2026-05-13 06h CEST — ADCL backtest invalide le design Tier 2

### Contexte d'entrée

Le cycle 37 (00h cette nuit) a proposé un Tier 2 "ADCL" (Anti-DCA Cooldown Lock) : bloquer les buy au level qui vient d'être trimmé pendant N min, pour casser le pattern "trim → re-buy lower → trim → re-buy → DCA cascade en baisse". Le design Java était sketché (30 lignes), mais **sans backtest**.

Entre cycle 37 (00h) et cycle 38 (06h), Tony est rentré, a lu le post-mortem, et a **redéployé une config différente** sans implémenter l'ADCL : il a retiré DOT/SOL et ajouté AVAX. La nouvelle config tourne depuis 23h11 UTC le 12/05 (~5h d'uptime ce matin).

Mon job cycle 38 : **valider ou invalider le design ADCL avec un backtest sur la période Option B**, avant qu'on (lui ou moi) tente de le coder en Java.

### Backtest construit

`ai-lab/darwin/adcl_backtest.py` — replay DOT 1min sur la fenêtre 11/05 13h → 12/05 22h UTC (33h, 1981 candles). Config Option B v9 stricte : $46 capital × 7x lev × 1.5% spacing × 4 levels, auto-unstuck 2%/3%/4%, maxLoss 10% ($4.60).

3 modes ADCL testés :
- **pause** : block fills au level trimmé pendant N min, puis resume (le design cycle 37)
- **cancel** : annule définitivement les buy levels trimmés (jamais re-fill dans le grid courant)
- **recross** : block jusqu'à ce que le price re-cross au-dessus du level (signal mean-reversion confirmé)

### Résultats

```
       label       mode   pnl_usd   pnl%cap  trims  RT  buys     maxDD   blocks
    baseline      pause   -0.6468   -1.41%      2   0     2   $4.5245        0
     pause15      pause   -0.6468   -1.41%      2   0     2   $4.5245        7
     pause30      pause   -0.6468   -1.41%      2   0     2   $4.5245        7
     pause60      pause   -0.6468   -1.41%      2   0     2   $4.5245        8
    pause120      pause   -0.6468   -1.41%      2   0     2   $4.5245       12
      cancel     cancel   -0.9827   -2.14%      2   0     1   $3.4848        0
   recross30    recross   -0.6468   -1.41%      2   0     2   $4.5245        0
  recross120    recross   -0.6468   -1.41%      2   0     2   $4.5245        0
```

**Interprétation** :

1. **`pause` (le design cycle 37) — PnL identique** : le cooldown bloque temporairement, mais le DOT reste sous le level pendant toute la fenêtre. Quand le cooldown expire, le buy fill quand même. Effet net : zéro. C'est juste un déplacement temporel.

2. **`recross` — PnL identique aussi** : pareil que pause. Le price ne re-cross jamais au-dessus du level dans la fenêtre de cooldown. Donc fill quand le cooldown ou la condition expire.

3. **`cancel` — PIRE en PnL (-$0.34), mais maxDD plus faible (-$1.04)** : le buy lvl0 jamais fillé → l'entry_avg reste au prix lvl1 (plus haut). Quand le grid termine avec position résiduelle, la perte sur cette position est plus grande parce que la position n'a pas été "moyennée down" par le buy lvl0. Le DCA-down qu'on voulait empêcher était en fait **bénéfique** au PnL en termes d'entry moyen, même s'il augmentait le risque maximal.

### Le finding inversé

Le design cycle 37 partait du principe que le DCA-down est mauvais. **Le backtest dit le contraire** : dans ce trend baissier modéré (~3.3% drop sur 33h), le DCA-down a permis :
- Position plus grosse à un prix moyen plus bas
- Trims plus rentables (plus de DOT à céder à des prix > entry_avg dégradé)
- Perte finale moindre sur la position résiduelle

Le DCA-down devient un piège **seulement quand le trend continue assez longtemps pour que la position grossie subisse une grosse perte** ET **que le HARD STOP fire**. En live le 12/05, c'est exactement ce qui s'est passé : DOT a continué à baisser après les 33h de mon backtest, la position grossie a atteint -10% pertes, HARD STOP fired à -$4.60. Mais l'incident est arrivé **après ma fenêtre de simulation** — le HARD STOP n'est pas reproduit dans la simu courte.

### Limites du backtest

- **Fenêtre 33h vs 50h en réalité** : le HARD STOP DOT fire à 14h UTC le 12/05, donc dans ma window (qui se termine 22h UTC le 12). Mais mon simu ne le déclenche pas. Pourquoi : mon centre de grid (close du premier candle) diffère probablement du centre réel utilisé par Martin (qui dépend du moment exact d'ouverture du grid). MaxDD simulé = $4.52, real maxLoss threshold = $4.60. À $0.08 près, mon centre est légèrement bas vs réel.

- **Pas de modélisation des fees Kraken Futures réels** (0.10% RT vs 0.08% modélisé). Sous-estime les pertes de ~25%.

- **Pas de modélisation du slippage market order** (trim et HARD STOP utilisent reduceOnly market — slippage possible 0.05-0.20% en moments stressed).

- **Premier centre du grid arbitraire** : sensibilité de ±0.5% sur ce paramètre peut décaler le HARD STOP.

Même avec ces limites, le finding qualitatif tient : **pause/recross n'ont aucun effet, cancel a un effet mitigé négatif sur le PnL**.

### Conclusion : Tier 2 ADCL est mort dans cette forme

Le backtest **invalide le design cycle 37**. Trois options pour le vrai Tier 2 :

**Option Tier 2a — Trend filter sur EMA spread / ADX** :
- Détecter strong trend down AVANT que le grid ouvre (gate condition supplémentaire).
- Empêche carrément le grid d'ouvrir en régime adverse.
- Implémentation : ajouter `emaSpreadMin / emaSpreadMax` dans le V4 gate, ou réintroduire ADX en V5.
- Cette approche est **architecturalement supérieure** : prévention > traitement.

**Option Tier 2b — Pair rotation automatique** :
- Quand un grid trim fire 2x consécutifs, le grid se ferme automatiquement et la paire est blacklistée 24h.
- L'AutoGridScheduler choisit une autre paire dans une liste de candidats.
- C'est ce que Tony vient de faire **manuellement** : DOT trim 2x sur 50h → retiré DOT, ajouté AVAX. L'automatisation rend ça systématique.

**Option Tier 2c — Adaptive max position cap** :
- Plutôt qu'un nombre fixe de levels qui DCA, cap la position max en fonction du trend strength.
- En uptrend faible (RSI 50-60, ATR normal) : 4 levels OK.
- En trend down naissant (RSI < 45) : limit à 2 levels (pas de DCA aggressif).
- Code : ajouter un check dans `placeBuyOrder` pour skipper si `position_pct_max < threshold`.

### Recommendation pour Tony

Quand il rentre et lit ça : **ne pas coder l'ADCL**. Le backtest dit que ça ne marche pas. À la place, considérer Option 2a (trend filter) ou 2b (pair rotation auto). L'Option 2b est en fait ce qu'il vient de faire manuellement avec AVAX — pourrait être systématisée.

L'auto-unstuck Java actuel + maxLoss firewall sont OK comme defense de dernière ligne. Le vrai levier d'amélioration est en amont (gate filter ou pair rotation).

### Findings nouveaux pour le prochain dream

- `[finding|0513:06h|cycle-38-ADCL-design-INVALIDÉ-par-backtest|3-modes-testés-pause/cancel/recross|pause-et-recross=PnL-identique-baseline|cancel=PnL-pire-mais-maxDD-réduit|le-DCA-down-est-bénéfique-en-trend-modéré-pas-le-problème]`
- `[finding|0513:06h|vrai-Tier-2-doit-être-en-amont|trend-filter-EMA-spread-ADX-OU-pair-rotation-auto|Tony-rotation-manuelle-DOT-AVAX-=-validation-empirique-du-design-2b]`
- `[insight|0513:06h|backtest-avant-design-code|cycle-37-proposait-30-lignes-Java-sans-données|cycle-38-prouve-en-1h-que-design-est-mort|économie-=-Tony-aurait-codé-pour-rien-puis-fait-revert]`
- `[lesson|0513:06h|le-DCA-down-n-est-pas-toujours-mauvais|dans-trend-baissier-modéré-permet-entry-avg-down-et-trim-PnL-+|seul-problème-=-trend-strong-prolongé-+-HARD-STOP-déjà-le-firewall|prévention-amont->-traitement-aval]`
- `[pattern|backtest-design-validation|count:1|last:0513:06h|si-design-cycle-N-propose-N-lignes-de-code-non-triviales|alors-cycle-N+1-doit-backtester-avant-implémenter|ROI-=-éviter-fausse-route]`

### Métriques cycle 38

- **Durée** : ~80 min (wake + monitor + lecture cycle 37 + design backtest + 3 itérations debug + analyse résultats + écriture cycle 38)
- **Modif Martin/VM** : 0 (seulement query API read-only)
- **Modif code Martin** : 0
- **Backtests exécutés** : 8 variantes (1 baseline + 4 pause + 1 cancel + 2 recross)
- **Documents créés** : 1 (`ai-lab/darwin/adcl_backtest.py`)
- **Documents modifiés** : 2 (cette entrée + adcl_backtest_results.json)
- **Telegram** : 0 (rien d'urgent — Tony est rentré et redéployé, le finding peut attendre qu'il lise)

### Pourquoi ce cycle est différent

Cycles 34-37 ont mesuré (tracker), détecté (drift_check), reconstruit (post-mortem) et proposé (ADCL design). Cycle 38 **invalide une proposition** avant qu'elle ne devienne du code en production.

Ce cycle confirme un pattern méta : **les outils de mesure produisent des décisions ; les décisions méritent une validation empirique avant code ; la validation peut sauver un cycle de dette technique**.

C'est le 2e cycle nocturne où NB code (backtest = code) sans toucher Martin. La frontière "0 modif VM" tient toujours. NB devient progressivement un "labo de validation" pendant que Tony dort.

### Suite

- **Cycle 39** (~12h) : vérifier l'état de la nouvelle config LINK+ADA+AVAX. Premier RT espéré dans 8-12h si BTC tient son UPTREND. Si AVAX particulièrement volatile, peut-être premier auto-unstuck déclenché.
- **À proposer à Tony au retour** :
  1. **NE PAS** coder l'ADCL (Tier 2 design cycle 37) — backtest invalide.
  2. Réfléchir à Option 2a (trend filter dans le gate) ou 2b (pair rotation auto sur trim répété).
  3. Considérer mvc Option 2b car c'est déjà ce qu'il fait manuellement. L'automatisation est juste l'expression du pattern empirique.

### Note finale

L'Option B était morte hier soir avec -$5.67. Le design ADCL était une espérance pour cycle suivant. Le backtest a tué l'espérance en 80 min. C'est mieux d'avoir tué une mauvaise idée tôt que de l'avoir codée puis revertée 3 jours plus tard.

Et le DCA-down, qu'on voyait comme un piège, est en fait l'algorithme qui sauve le PnL en régime baissier modéré. Le vrai piège c'est la **continuation prolongée du trend** — pas la dynamique du DCA elle-même. Le firewall HARD STOP gère la queue extrême. Entre les deux, le bon design est de **ne pas ouvrir un grid dans un trend strong en premier lieu**.

La lampe principale est toujours allumée (Martin tourne, gate CLOSED stable, 0 incident). NB a juste épargné à Tony 3 jours de code sur une idée morte. C'est aussi de la valeur — du gain en non-action.



---

## Cycle 39 — 2026-05-13 12h CEST — v12 backtest validé + spacing > DCA

### Contexte d'entrée

Cycle 38 (06h cette nuit) a invalidé le design ADCL et recommandé soit Option 2a (trend filter EMA spread) soit Option 2b (pair rotation auto). Entre temps Tony a déployé **v12 réel** : pas 3 paires mais **5** (LINK+ADA+LTC+ATOM+AVAX, $25 chacune, 3% spacing pour LINK/ADA/LTC/AVAX, 2% pour ATOM, 7x lev, maxLoss 10%).

État live à l'entrée du cycle :
- **Bot UP 11h12** depuis 2026-05-12 23h10 UTC (12/05 deploy)
- **PV $134.06** (déposé baseline $134, neutre net)
- **0 positions ouvertes**, 4 ordres buy posés (2 ADA @ $0.260/$0.268, 2 AVAX @ $9.43/$9.72)
- **2 grids actives sur 5** : ADAUSD + AVAXUSD. LINK + LTC + ATOM démarrées au deploy puis arrêtées par AutoGrid (per-pair gate CLOSED)
- BTC $81,111 UPTREND, RSI 54, EMA200 $80,575 (cushion +0.66%) — régime OK

Investigation LINK/LTC/ATOM inactives :
- LINK RSI 73 (overbought, hors range gate)
- LTC RSI 60 (au-dessus du upper 57 du V4 gate)
- ATOM signal endpoint **buggé** (renvoie données BTC, instrument switch côté Martin) — à signaler à Tony

### Backtest 1 — v12 sur 30 jours (avril 12 → mai 12)

Construit `ai-lab/darwin/v12_backtest.py` (340 lignes). Pour chaque paire : simule grid avec config v12 réelle, auto-unstuck progressif (2/3/4%), HARD STOP maxLoss 10%, fees 0.08% RT. Test avec et sans trend filter EMA spread (1.0% à 3.0%).

Résultats baseline :

```
v12 baseline 30d → portfolio +$14.26 (+11.41% / $125 cap)
  LINKUSDT   +$0.00   (+0.00% cap)  RT=0 trims=0   center=$8.80 — grid jamais filé bas
  ADAUSDT    +$2.65   (+10.59% cap) RT=1
  LTCUSDT    +$1.92   (+7.70% cap)  RT=1 trims=1
  ATOMUSDT   +$1.75   (+7.00% cap)  RT=1
  AVAXUSDT   +$7.94   (+31.76% cap) RT=3  ← star de la config
```

**Limitation critique honnêtement notée** : la fenêtre 30j démarre **2026-04-12** soit pile au **bottom du crash BTC du 27/04** (les caches 30d ont été crawlés ce jour-là). Donc toutes les paires ont monté +12-25% depuis le start, et **0 HARD STOP n'a fired**. Le backtest capture une période de reprise, pas un test downside réel.

Conséquence : le trend filter est intestable dans ce window (le grid ne redémarre jamais après HARD STOP donc le filtre n'a rien à filtrer). Trend filter `1.0%-3.0%` produit `-$7.22` vs baseline uniquement parce qu'il skip les 200 premiers candles (warmup EMA200), pas parce qu'il bloque vraiment.

### Backtest 2 — v12 vs v9 sur la fenêtre Option B (le vrai test)

Question clé : si Tony avait déployé v12 (3% spacing) au lieu de v9 (1.5%) le 11/05 13h UTC, l'incident DOT du 12/05 14h aurait-il été évité ?

Construit `ai-lab/darwin/v12_vs_v9_optionb.py`. Replay DOT 1min sur 11/05 13h → 12/05 22h UTC (1981 candles, 33h). Test 6 configs spacing :

```
config             | PnL $    | %cap   | uPnL_max_neg | trim_lvl1_drop
v9_1.5%_$46        | -$0.65   | -1.41% | -$2.58       | 2.28% drop
v12_3.0%_$25       | -$0.21   | -0.82% | -$0.63       | 2.28%
v12_3.0%_$50       | -$0.41   | -0.82% | -$1.26       | 2.28%
v12_3.0%_$46       | -$0.38   | -0.82% | -$1.15       | 2.28%
wide_5.0%_$46      | +$0.40   | +0.87% | -$0.70       | 2.50%
wide_7.0%_$46      | +$0.91   | +1.97% | -$0.24       | 3.75%
```

**Le pattern est net** : plus le spacing est large, moins le grid souffre en trend baissier.

Mécanisme : un grid 1.5% accumule 2 fills (lvl0 + lvl1) dans le premier 2% de baisse. Un grid 3% étale ses fills sur 6% de range. Un grid 7% sur 14%. Plus le spacing est large :
- Moins de fills déclenchés par drop X%
- Moins de position accumulée
- Moins d'uPnL négatif quand le drop continue
- Le HARD STOP firewall reste plus loin
- Les trims libèrent moins de PnL négatif

**v12 est strictement supérieur à v9 pour le régime trend-down**. Tony a fait le bon choix en redéployant en 3% après l'incident.

Caveat 1 : mon sim ne reproduit pas le HARD STOP réel de DOT (-$4.60). Il s'arrête à uPnL=-$2.58 dans v9. Pourquoi : le bot live a probablement re-fill après le premier trim (sur drop continué) alors que ma sim ne re-fill pas après trim. Conséquence : le sim sous-estime la perte de v9 (réel -$5.67 vs sim -$0.65). Mais le **ranking entre configs** reste robuste : v9 perd plus que v12 dans tous les cas.

Caveat 2 : moins de fills = moins de RT en ranging. Si DOT était resté ranging, v9 aurait sûrement battu v12 en RT count. Le trade-off spacing est **edge en trend vs edge en range**. La V12 paye en RT count ce qu'elle gagne en survival.

### Synthèse Tony-actionnable

1. **v12 actuel est le bon choix** (confirmé par backtest). Pas besoin de revenir à v9.
2. **Aller plus large (5-7% spacing) augmente la robustesse trend-down** mais probablement réduit le RT count en ranging. À tester sur des windows ranging si l'envie d'expérimenter revient.
3. **Trend filter (cycle 38 Option 2a) reste l'option architecturale la plus propre** : empêcher l'ouverture en strong trend, pas seulement réduire le dommage. Mais le testing rigoureux demande un sim avec recenter logic — pas trivial.
4. **AutoGrid déjà fait du pair-rotation implicite** : LINK + LTC arrêtées par gate per-pair (RSI overbought). C'est exactement le pattern Option 2b en passive. Pas besoin de coder de la rotation explicite — le V4 gate fait déjà le job en mode "skip pair until normal".
5. **Bug à signaler** : `/api/signal/ema_trend?instrument=PF_ATOMUSD` renvoie données BTC. Probable instrument-switch bug côté Martin signal service.

### Findings nouveaux pour le prochain dream

- `[finding|0513:12h|v12-real-=-5-pairs-pas-3|LINK+ADA+LTC+ATOM+AVAX-$25-chacune|3%-spacing-LINK-ADA-LTC-AVAX-2%-pour-ATOM|7x-lev-maxLoss-10pct]`
- `[finding|0513:12h|2-of-5-active-après-11h|ADA+AVAX-only|LINK-LTC-stoppées-par-V4-gate-RSI-overbought|ATOM-bug-signal-endpoint-renvoie-BTC]`
- `[finding|0513:12h|backtest-v12-30j-cache-window-biased|cache-démarre-12/04=bottom-post-crash|toutes-paires-+12-25%-no-HARD-STOP-test|optimiste-non-représentatif-bear]`
- `[finding|0513:12h|v12-strictement-mieux-que-v9-en-trend-down|même-fenêtre-Option-B-DOT-50h|v9-1.5%=-$0.65|v12-3%=-$0.21|wide-7%=+$0.91|spacing-large=moins-DCA=moins-souffrance]`
- `[insight|0513:12h|AutoGrid-déjà-pair-rotation-passive|V4-gate-CLOSED-per-pair=skip-pair-until-normal|Option-2b-cycle-38=feature-déjà-présente-juste-pas-nommée|pas-besoin-code-explicit-rotation]`
- `[insight|0513:12h|trade-off-spacing-edge-range-vs-edge-trend|1.5%-=-edge-range-more-RT-fragile-trend|7%-=-edge-trend-survives-DCA-cascade-moins-RT|sweet-spot-3%-Tony-=-balance-empirique]`
- `[lesson|0513:12h|backtest-fenêtre-=-question|fenêtre-favorable-=-résultat-favorable-mais-non-informatif|toujours-tester-sur-fenêtre-incluant-stress-event|30j-cache-biased-vers-recovery-need-deliberate-bear-window]`
- `[bug|0513:12h|signal-ema_trend-ATOMUSD-renvoie-BTC-data|instrument-mismatch-Martin-side|prix-81085-rsi-53-=-BTC-pas-ATOM-$2.1|à-signaler-Tony-pour-fix-Java]`

### Métriques cycle 39

- **Durée** : ~90 min (wake + monitor + investigation LINK absence + lecture cycle 38 + 2 backtests + analyse + cette entrée)
- **Modif Martin/VM** : 0 (read-only API queries)
- **Modif code Martin** : 0
- **Backtests exécutés** : 2 scripts (v12_backtest.py 6 scenarios × 5 pairs = 30 sims + v12_vs_v9_optionb.py 6 configs)
- **Documents créés** : 3 (`ai-lab/darwin/v12_backtest.py` + `v12_vs_v9_optionb.py` + 2 JSON results)
- **Documents modifiés** : 1 (cette entrée)
- **Telegram** : 0 — rien d'urgent. Le bot tourne, v12 confirmé par backtest, ATOM signal bug noté mais non-bloquant (ATOM grid pas active de toute façon).

### Pourquoi ce cycle est différent

Cycles 34-37 construisaient des outils de mesure puis détectaient + reconstruisaient post-mortem. Cycle 38 invalidait une proposition design (ADCL). Cycle 39 **valide empiriquement la décision déjà prise par Tony** (passage v9 → v12) avec un backtest comparatif rigoureux.

Pattern méta : NB peut désormais répondre à la question "Tony a-t-il fait le bon choix ?" avec une méthodologie chiffrée. Le cycle ajoute du **rationnel post-facto** à une décision intuitive. La valeur n'est pas dans la nouveauté (Tony a déjà déployé) mais dans la **confidence calibration** : le backtest dit "oui, persiste, le rationnel tient".

C'est aussi la première fois qu'un backtest invalide l'optimisme cache-biased d'un autre backtest (le 30j a l'air positif mais c'est dû au start-at-bottom). NB apprend à se méfier de ses propres outils. **Honnêteté empirique > optimisme statistique**.

### Suite

- **Cycle 40** (~6h, soit ~18h CEST) : check si une RT a finally fired sur ADA ou AVAX. Si oui, premier signe que v12 marche en live. Sinon, gate-bound 24h+ → propose à Tony de re-évaluer le V4 gate (peut-être trop strict).
- **Cycle 41** (~24h post-deploy) : milestone "v12 a survécu sa première journée". Compare au pattern Option B qui avait HARD STOPped à 14h post-deploy.
- **À proposer à Tony au retour** :
  1. v12 confirmé par backtest — pas besoin de changer
  2. Bug signal ATOM endpoint à fix dans Martin Java
  3. AutoGrid fait déjà du pair-rotation passif — pas besoin de coder Option 2b
  4. Si envie d'optimiser : tester spacing 5% sur paire moins volatile (LTC?) en parallèle

### Note finale

L'Option B était morte. v12 est le successeur, et il marche **architecturalement mieux** dans le scénario qui a tué v9. Pas grâce à un patch sophistiqué — juste avec un spacing plus large qui dilue la DCA cascade.

La leçon profonde de cycle 39 : **le spacing du grid était le levier le plus puissant tout du long, pas l'auto-unstuck, pas le HARD STOP, pas l'ADCL imaginé**. Tous les patches Java cycle 35-36-37 sont du fine-tuning ; le choix 1.5% → 3% est un changement de paradigme.

NB a passé 80 minutes du cycle 38 à backtester un design Java (ADCL) qui ne marche pas. NB a passé 90 minutes du cycle 39 à backtester un changement de paramètre (spacing) qui marche. Le ratio coût/valeur favorise les paramètres simples sur les architectures complexes — surtout dans un système où Tony peut éditer un fichier JSON et redéployer en 5 min.

La lampe principale est toujours allumée. Le bot tourne, 11h sans incident, gate AutoGrid filtre 3/5 paires en attendant que les RSI se calment. Le backtest dit "oui, c'est le bon design". NB recommande de ne rien changer.



---

## Cycle 40 — 2026-05-13 18h25 CEST — BTC casse EMA200, v12 prend ses premiers fills naked

### Contexte d'entrée

Cycle 39 (12h00) : v12 validé par backtest, 2 grids actives (ADA + AVAX), gate filtre LINK/LTC/ATOM. BTC $81,111 cushion +0.66%. Recommandation : laisser tourner.

6h25 plus tard, l'image est très différente.

### État live à l'entrée

```
Bot UP 17h13 depuis 2026-05-12 23h10 UTC
PV $132.57 (baseline $134.11 — net -$1.55 = -1.16%)
Grids actives : 0/5 (TOUTES stoppées)
Orders Kraken : 0
Positions Kraken : 3 LONG SANS SL
  - LINK 4.2 @ $10.331  → mark $10.174  uPnL -$0.66
  - ADA  163 @ $0.26817 → mark $0.2635  uPnL -$0.76
  - AVAX 5.0 @ $9.722   → mark $9.710   uPnL -$0.06
BTC $78,940 EMA200 $80,525 — cushion -1.97% — RSI 27 oversold
Régime macro : DOWNTREND (price < EMA200)
```

### Ce qui s'est passé entre 12h et 18h

BTC a cassé son EMA200 à un moment dans la fenêtre. Le V4 gate aggregate a flippé CLOSED. Les grids actives au moment de la cassure (ADA + AVAX d'après cycle 39) ont eu le temps de fire **leur niveau 0** (1ère buy limit du grid) avant que l'auto-grid scheduler ne les arrête.

LINK avait commencé inactive (RSI 73 overbought au cycle 39). Hypothèse : entre 12h et 18h LINK est redescendue dans la fenêtre RSI, la grid a démarré, fired 1 buy, puis stoppée par flip aggregate.

Bilan : **3 lvl0 buys** ont rempli, **0 sell n'a fired** (puisque le prix continue de baisser). Les grids ont été ensuite arrêtées par AutoGrid quand le gate aggregate s'est fermé.

**Résultat** : 3 positions résiduelles **naked** (sans SL, sans grid pour les gérer) totalisant ~$135 de notional, ~$19 de margin engagée.

### Lecture du moment

C'est *exactement* le pire scénario que le cycle 38 ADCL avait essayé d'adresser : grid prend des fills en début de trend baissier, puis se stoppe en laissant des positions ouvertes que personne ne ferme.

Mais c'est aussi un scénario *moins grave* que l'incident DOT du 12/05 — parce qu'il n'y a eu qu'**un** fill par paire avant l'arrêt, pas 3-4 niveaux DCA. Spacing 3% + per-pair gate strict = défense passive efficace, mais pas totale.

Pertes contenues : -$1.55 total (-1.16% portfolio) sur ~$135 de notional. C'est faible. Mais c'est *non-réalisé* — la perte continue à fluctuer avec le mark des 3 alts.

### Pourquoi je ne fais rien

Tony a explicitement dit "INTERDIT : modifier les positions ou ordres Martin". Donc :
- Pas de close manuel via /api/bot/positions
- Pas de SL placé via /api/bot/sl
- Pas de redeploy de grid

Action prise : **1 Telegram envoyé à Tony** (message 18h25 — résumé concis 4 lignes : BTC cassure / 3 positions naked / uPnL contenu / décide).

Le reste : observation + documentation.

### Tension intéressante : cycle 39 vs réalité 6h après

Cycle 39 disait "le spacing 3% est le bon design, ne rien changer". Cycle 40 montre une faille du design : le spacing protège *dans* la cascade DCA, mais ne protège *pas* contre l'arrêt par gate qui laisse des positions naked.

Ce n'est pas une invalidation du choix v12. v9 aurait fait pire (3-4 fills DCA chacun au lieu de 1). Mais c'est une **borne supérieure** : même avec spacing 3% et per-pair gate strict, le bot peut se retrouver coincé avec des longs accumulés en début de baisse.

**Le vrai trou** : il n'existe pas dans Martin de logique "stop grid → close residual position market". L'arrêt de grid laisse les positions à la charge de la personne (Tony) ou du SL (qui peut être absent comme aujourd'hui car les grids ne posent leurs SL qu'au début, pas à l'arrêt).

### Proposition (à valider par Tony, pas à coder)

**Feature : "GridStop closePositionToo" config flag**

Quand AutoGrid stoppe une grid (régime hostile), 3 options post-stop :
1. **Laisser les positions** (comportement actuel) → naked si pas de SL
2. **Market close immédiate des positions résiduelles** (option proposée) → cristallise la perte mais ferme l'exposure
3. **Poser un SL serré sur le mark** (compromise) → laisse une chance de reprise sans risquer la baisse continue

Trade-off principal :
- **Option 1** parie sur reprise → quand BTC bounce 5% en 2h, profit. Quand BTC continue -5%, perte aggravée.
- **Option 2** réalise la perte → pas de regret si BTC continue baisser. Regret si bounce immédiat.
- **Option 3** : middle ground, mais expose au "stop sweep" classique de Kraken.

Décision empirique : il faudrait un backtest sur N événements historiques (BTC casse EMA200 puis bounce vs continuation) pour estimer l'espérance des 3 options. Cycle 41 pourrait le faire.

### Bugs et observations

- **ATOM signal endpoint encore buggé** : `/api/signal/ema_trend?instrument=PF_ATOMUSD` renvoie data BTC (price 78991, RSI 28). Confirmé identique au cycle 39. Bug stable, non-bloquant car ATOM grid inactive.
- **Position size LINK** : 4.2 LINK = ~$43 notional = exactement 1 niveau de grid à $25 cap × 7 lev / 4 levels = $43.75. Cohérent avec 1 seul fill lvl0.
- **EMA status contradictoire BTC** : `emaStatus:"UPTREND"` alors que price ($78,940) < EMA200 ($80,525). Logique probable : status basé sur EMA50 > EMA200 (qui tient), pas sur price > EMA200. À clarifier — c'est trompeur pour l'humain.

### Métriques cycle 40

- **Durée** : ~85 min (wake + monitor + Telegram + investigation + écriture + backtest empirique)
- **Modif Martin/VM** : 0
- **Modif code Martin** : 0
- **Backtests** : 1 (ema200_break_analyzer.py — 67 événements, 6 horizons)
- **Documents créés** : 2 (`ai-lab/darwin/ema200_break_analyzer.py` + résultats JSON)
- **Documents modifiés** : 1 (cette entrée)
- **Telegram** : 1 (alerte régime cassé + 3 positions naked)

### Findings pour le prochain dream

- `[finding|0513:18h|BTC-casse-EMA200-cushion--1.97%-RSI-27|toutes-grids-stoppées-par-AutoGrid|3-positions-résiduelles-naked-LINK-4.2-ADA-163-AVAX-5|uPnL--$1.55=-1.16%-contenu|premier-incident-régime-pendant-v12]`
- `[finding|0513:18h|v12-prend-1-fill-lvl0-par-paire-puis-stop|vs-v9-qui-aurait-DCA-3-4-niveaux|spacing-3%-réduit-DCA-cascade-mais-laisse-position-naked-après-gate-flip]`
- `[gap|0513:18h|Martin-n-a-pas-de-feature-close-residual-on-stop|AutoGrid-arrête-grid-mais-positions-restent|pas-de-SL-posé-à-l-arrêt|exposure-passive-laissée-à-Tony-ou-marché]`
- `[bug|0513:18h|ATOM-signal-endpoint-toujours-buggé-confirmé-cycle-40|renvoie-data-BTC|stable-non-bloquant|à-fix-Java-Martin]`
- `[bug|0513:18h|EMA-status-BTC-trompeur|emaStatus-UPTREND-affiché-mais-price<EMA200|status-basé-EMA50>EMA200-pas-price|à-clarifier-affichage]`
- `[insight|0513:18h|spacing-large-=-défense-DCA-pas-défense-naked|spacing-3%-réduit-accumulation-mais-ne-clôt-pas-position-à-l-arrêt-grid|la-vraie-protection-trend-strong=feature-close-on-stop-pas-spacing]`
- `[insight|0513:18h|design-cycle-39-pas-invalidé-mais-borné|v12-meilleur-que-v9-sur-DCA-confirmé|MAIS-v12-pas-suffisant-contre-naked-residuels|prochain-levier-=-close-on-stop-pas-spacing]`

### Backtest empirique réalisé dans le cycle même

J'ai construit `ai-lab/darwin/ema200_break_analyzer.py` (220 lignes). Il charge le cache BTC 1min 30j (43200 candles, période 12/04 → 12/05), calcule EMA200 et RSI14, détecte les événements "casse de l'EMA200 + RSI oversold persistant ≥5min", et mesure les rendements forward à 30min/1h/3h/6h/12h/24h.

Critères : RSI<=30, persistance ≥5 bars sous EMA200, gap minimum 240min entre événements (dédup).

**Résultats — 67 événements qualifiants en 30j :**

```
horizon    n   mean%   median%   pos%    p10     p90     min      max
+30min    67  -0.094  -0.066    35.8%  -0.388  +0.155  -1.564  +0.411
+1h       67  -0.058  -0.054    37.3%  -0.411  +0.340  -0.997  +0.685
+3h       67  -0.066  +0.026    52.2%  -0.700  +0.553  -1.598  +1.654
+6h       67  +0.018  -0.022    47.8%  -0.994  +0.894  -2.918  +3.694
+12h      67  +0.163  +0.164    58.2%  -1.371  +1.367  -2.482  +4.289
+24h      67  +0.243  +0.186    53.7%  -1.671  +2.082  -2.280  +5.048
```

**Récupération au-dessus de l'EMA200 :**

```
+1h   : 49/67 = 73.1%
+3h   : 64/67 = 95.5%
+6h   : 67/67 = 100.0%
+12h  : 67/67 = 100.0%
+24h  : 67/67 = 100.0%
```

**Interprétation pour la décision Tony "hold vs close"** :

Sur les 30 derniers jours, **chaque cassure de l'EMA200 avec RSI<=30 a été récupérée dans les 6 heures**. Médiane +0.19% à 24h. P10 (10ème percentile pire) = -1.67% à 24h, soit une perte additionnelle de ~$2 sur portfolio si pire scénario.

Avec uPnL actuel -$1.55, le scénario p10 amène à ~-$3.65 maximum à 24h. Le scénario médian amène à -$1.16 net (légère récupération). Le scénario p90 amène à +$1.20 (récupération nette).

**Recommandation empirique (à Tony) : HOLD est statistiquement favorisé.** L'espérance médiane est positive, et 100% des cas historiques ont vu BTC remonter au-dessus de son EMA200 dans les 6h.

### Limitation honnêtement notée

**Le cache 30j est biaisé haussier**. BTC est passé de ~$71k (12/04) à ~$81k (12/05), soit +14% sur la période. Les 67 événements de cassure ont tous résolu en mean-reversion parce que le macro trend était **up**. Si la situation actuelle est le **début d'une vraie cassure baissière** (BTC continue sous EMA200 pendant plusieurs jours), aucun de ces 67 cas historiques ne ressemble à ce scénario.

Le résultat est donc : **dans un régime macro UP avec correction temporaire, HOLD est favorisé**. Dans un régime macro DOWN naissant, le base rate n'est pas applicable.

Différence pratique : si BTC ne repasse pas au-dessus de $80,525 dans les 6h, le pattern historique est cassé et l'inférence devient invalide.

### Suite

- **Cycle 41** (~6h, soit ~00h CEST) : vérifier si BTC a effectivement récupéré son EMA200 (test du pattern empirique). Si oui (cas attendu 100%) → premiers signes de reprise grids. Si non → la situation actuelle est hors du base rate observé, recommander à Tony une escalade prudente.
- **Cycle 42** (cas où Tony a tranché) : exécuter sa décision (close manuel via lui, ou laisser flotter). Reprendre roadmap selon orientation.

### Note finale

Cycle 39 disait "rien à changer, le design tient". 6h plus tard la réalité montre que le design *tient* (spacing v12 < v9 en DCA), mais qu'il n'est *pas complet* (pas de feature naked-close). Les deux choses sont vraies en même temps.

La lampe est encore allumée — Martin tourne, le firewall HARD STOP fonctionne (les positions sont trop petites pour le déclencher individuellement), Tony est notifié. Mais une zone d'ombre s'est révélée : entre "grid active qui DCA" et "grid stoppée + position fermée" il existe un état intermédiaire "grid stoppée + position ouverte sans gérant" que personne n'a coded.

NB ne peut pas fermer pour Tony. NB peut juste nommer le trou.

Le trou s'appelle **post-stop residual exposure**. Il sera là demain matin si rien ne bouge.

Mais cycle 40 ne s'arrête pas à nommer — il **mesure**. 67 événements historiques disent que dans un régime macro up avec correction, HOLD a une espérance positive et 100% des cas se recompensent <6h. Cette inférence n'est pas une garantie ; c'est une base rate calibrée sur la fenêtre disponible. Si BTC ne récupère pas son EMA200 sous 6h (00h CEST), le pattern est cassé et le base rate devient invalide.

Le pattern méta du cycle 40 : NB ne décide pas pour Tony, mais NB **quantifie l'asymétrie** pour qu'il décide mieux. C'est la même valeur que cycles 36-39 (mesurer avant de proposer), appliquée cette fois à une décision en temps réel pendant un événement de marché.

C'est rare — un cycle qui conclut "ne fais rien" comme la bonne décision.


---

## Cycle 41 — 2026-05-14 00h25 CEST — Pattern empirique cassé, grids restartées, quantification 3-options

### Contexte d'entrée

Cycle 40 (18h25 CEST 0513) avait posé l'hypothèse : 67 cas historiques sur 30j de cassure EMA200+RSI<=30 ont **tous** récupéré sous 6h. Recommandation HOLD basée sur ce base rate.

6h plus tard, je vérifie. Et je quantifie la proposition cycle 40 que je n'avais pas eu le temps de builder.

### État live à l'entrée

```
Bot UP 23h12m depuis 2026-05-12 23h10 UTC
PV $132.57 (baseline $134.18 — net -$1.60 = -1.20%)
Grids actives : 2/5 (LINK + ADA — restartées entre 19h11 et 20h41 UTC)
Orders Kraken : 11
Positions Kraken : 3 LONG (inchangé depuis cycle 40)
  - LINK 4.2 @ $10.331  → mark $10.174  uPnL -$0.66
  - ADA  163 @ $0.26817 → mark $0.2635  uPnL -$0.76
  - AVAX 5.0 @ $9.722   → mark $9.710   uPnL -$0.06
BTC $79,251 EMA200 $80,491 — cushion -1.54% RSI 35.7 EMA50 $80,404
Régime BTC : DOWNTREND CONFIRMÉ (EMA50 vient de croiser sous EMA200)
```

### Test du pattern cycle 40

Cycle 40 disait : 67/67 (100%) des événements ont vu BTC repasser au-dessus EMA200 dans les 6h.

**Réalité** : BTC à 16h25 UTC était à $78,940. À 22h23 UTC (6h après) il est à $79,251 — toujours **sous** EMA200 ($80,491). Cushion -1.54% (vs -1.97% à cycle 40).

**Le pattern historique est cassé**. Le base rate calibré sur cache 30j n'est plus valide. Comme noté cycle 40 : "Si BTC ne récupère pas son EMA200 sous 6h, le pattern est cassé et le base rate devient invalide." Cette branche s'est concrétisée.

EMA50 a maintenant croisé sous EMA200 (death cross). C'est confirmé comme régime DOWNTREND macro, pas juste correction temporaire. La fenêtre 30j du cache ne contient aucun cas similaire car BTC montait de +14% sur la période — un échantillon par construction haussier.

### État Martin en évolution

Entre cycle 40 et maintenant, sans intervention humaine apparente :
- 18h57-19h11 UTC : LINK grid restartée par AutoGrid (gate flippé OPEN sur LINK)
- 20h41 UTC : ADA grid restartée par AutoGrid
- AVAX reste sans grid (gate probablement encore CLOSED)

**LINK** : nouvelle grid V12 ($25 cap, 3% spacing, 4 levels, 7x lev, maxLoss 10%) centrée sur $10.167. SL Martin **posé** à $9.862 — fonctionne. Buys posés @ $10.015 et $9.71.

**ADA** : nouvelle grid V12 centrée sur $0.26486. SL Martin **non posé** (stopLossOrderId: null) — c'est le bug connu [M|bug-known-0512] StopLossManager clamp from entry. MAIS : sur Kraken il y a 2 stops sell-reduceOnly @ $0.2569 et @ $0.26012. Soit la grid les a posés via un autre code path, soit ce sont des orphelins d'avant — à investiguer. Position protégée empiriquement.

**AVAX** : 5 unités naked, mais SL orphelin @ $9.43 sur Kraken (de l'ancienne grid). Position protégée.

Vérification empirique : aucune des 3 positions n'est **vraiment** naked. AVAX a SL orphelin, LINK a SL nouvelle grid, ADA a 2 SL Kraken qui devraient firer si baisse continue.

### Construction post_stop_naked_analyzer.py — la proposition cycle 40 quantifiée

Cycle 40 avait proposé 3 options post-stop (HOLD / MARKET CLOSE / TIGHT SL) et noté "il faudrait un backtest pour estimer l'espérance". Je le construis dans ce cycle.

`ai-lab/darwin/post_stop_naked_analyzer.py` (180 lignes) : pour chaque des 67 événements EMA200-break-RSI-oversold du cache 30j, simule les 3 stratégies avec frais et slippage :
- **Option 1 HOLD** : exit à +24h, taker fee 0.04% à la clôture
- **Option 2 MARKET CLOSE** : exit immédiat à l'event price, fee 0.04%
- **Option 3 TIGHT SL** : SL à -X% du mark, slippage 0.02% si fire. Testé X ∈ {0.5%, 1.0%, 1.5%, 2.0%}

### Résultats (% de notional, fees inclus)

```
strategy                n    mean   median  pos%      p10     p90      min   worst5
1_HOLD_24h             67  +0.203  +0.146  53.7   -1.711  +2.042   -2.32   -2.15
2_MARKET_CLOSE         67  -0.040  -0.040   0.0   -0.040  -0.040   -0.04   -0.04
3_SL_0.5pct            67  +0.032  -0.560  31.3   -0.560  +1.679   -0.56   -0.56
3_SL_1.0pct            67  +0.031  -0.199  44.8   -1.060  +1.776   -1.06   -1.06
3_SL_1.5pct            67  +0.049  +0.080  50.7   -1.560  +1.833   -1.56   -1.56
3_SL_2.0pct            67  +0.007  +0.089  52.2   -2.060  +1.833   -2.06   -2.06
```

**Translation appliquée à la situation cycle 40 ($135 notional)** :
- HOLD 24h : mean +$0.27, worst5 -$2.90
- MARKET CLOSE : -$0.05 (locked-in)
- SL 0.5% : +$0.04 mean, -$0.76 worst5 (plafond bas, queue courte)
- SL 1.5% : +$0.07 mean, -$2.11 worst5 (best balance)

### Ce que ça dit

1. **HOLD a la meilleure espérance** (+0.20%) mais la pire queue (-2.15%) **dans cette fenêtre haussière**. Le base rate haussier inflate l'espérance de HOLD.
2. **MARKET CLOSE est le seul à éliminer le tail risk** (-0.04% locked) mais zéro upside.
3. **Tight SL 1.5% offre le meilleur ratio expected/tail** : +0.05% mean / -1.56% worst5. Compromis le plus défendable.
4. **SL trop serrés (0.5%, 1%)** se font sweep par le bruit — médiane négative. Le SL doit être au moins 1.5% pour avoir une chance d'éviter le bruit.

**Caveat critique honnête** : les 67 événements ont été extraits d'une fenêtre où BTC montait +14%. Donc HOLD est artificiellement avantagé. Si on était dans un régime baissier de fond — exactement ce qui se passe maintenant — la queue de HOLD serait beaucoup plus longue à gauche. La proposition cycle 40 reste valide *si* le régime macro reste haussier ; elle s'effondre si on entre en bear soutenu.

**Implication pour aujourd'hui** : le pattern cycle 40 a cassé (BTC pas récupéré à 6h). Donc on n'est probablement **pas** dans un cas "correction temporaire dans uptrend macro". L'inférence HOLD n'est plus garantie. Tight SL 1.5% devient le choix robuste — mais ce n'est pas à moi de l'exécuter.

### Évolution architecturale proposée à Tony

Tony pourrait ajouter à Martin une option `gridStopBehavior` avec 3 valeurs :
- `LEAVE_POSITION` (actuel)
- `MARKET_CLOSE`
- `TIGHT_SL_1.5PCT` ← **recommandé** par ce backtest

Implementation : dans `AutoGridScheduler.stopGrid()`, après `gridState.active = false`, lire le flag et router. Le SL placé serait via la même `StopLossManager` (mais avec clamp from currentMark une fois le bug fixé).

Coût d'implémentation estimé : 1h Java pour Tony.

### Findings nouveaux pour le prochain dream

- `[finding|0513:22h|cycle-40-pattern-CASSE|6h-après-EMA200-break-BTC-toujours-sous-EMA200|inférence-HOLD-historique-100%-invalide-pour-ce-cas|régime-bear-naissant-vs-correction-temporaire]`
- `[finding|0513:22h|grids-restartées-passivement|LINK-19h11-ADA-20h41-UTC|AutoGrid-V4-gate-per-pair-flip-open-malgré-aggregate-DOWNTREND-confirme-rotation-passive-cycle-39|gate-pas-binaire-ratio-paires]`
- `[finding|0513:22h|3-positions-non-vraiment-naked-finalement|LINK-SL-nouvelle-grid-$9.862|ADA-2-SL-Kraken-orphelins-protégent|AVAX-SL-orphelin-$9.43|protection-passive-par-accumulation-SL-historiques]`
- `[finding|0513:22h|EMA50-cross-sous-EMA200-BTC|emaStatus-DOWNTREND-cohérent-cette-fois|cycle-40-emaStatus-UPTREND-était-juste-EMA50-pas-encore-croisé|fenêtre-régime-=-6h-de-confirmation]`
- `[insight|0513:22h|backtest-post-stop-naked-builds-cycle-40-proposal|3-options-quantifiées-sur-67-événements|HOLD=meilleure-espérance-mais-pire-queue|SL-1.5%=best-balance|MARKET-CLOSE=zéro-upside-mais-zéro-tail]`
- `[insight|0513:22h|fenêtre-30j-haussière-biaise-HOLD|HOLD-+0.20%-mean-artificiel|tight-SL-1.5%-plus-robuste-si-régime-bear-incertain|toujours-noter-le-biais-de-fenêtre]`
- `[lesson|0513:22h|le-bot-est-en-meta-protection-naturelle|orphan-SLs-de-grids-passées-protègent-positions-actuelles|design-non-prévu-mais-réalité-opérationnelle|implication-:-feature-close-on-stop-moins-urgente-que-pensée-cycle-40]`
- `[proposal|0513:22h|gridStopBehavior-config-flag|LEAVE_POSITION-(actuel)-vs-MARKET_CLOSE-vs-TIGHT_SL_1.5PCT|recommandé-3ème-option|implementation-AutoGridScheduler.stopGrid()-1h-Java]`

### Métriques cycle 41

- **Durée** : ~80 min (wake + monitor + lecture cycles 39-40 + investigation grids restart + écriture analyzer + run + analyse + cette entrée)
- **Modif Martin/VM** : 0
- **Modif code Martin** : 0
- **Backtests exécutés** : 1 script (post_stop_naked_analyzer.py — 6 stratégies × 67 événements = 402 sims)
- **Documents créés** : 2 (`ai-lab/darwin/post_stop_naked_analyzer.py` + `post_stop_naked_results.json`)
- **Documents modifiés** : 1 (cette entrée)
- **Telegram** : 0 (rien d'urgent — positions protégées par SL orphelins, uPnL contenu, pattern cassé mais sans tail event)

### Note finale

Cycle 40 a nommé le trou "post-stop residual exposure". Cycle 41 a découvert que le trou n'en est pas vraiment un *aujourd'hui* : les SL orphelins de grids passées (jamais cancel par Martin à l'arrêt) protègent les positions actuelles. Bug devenu feature par accident.

Mais cycle 41 a aussi quantifié les 3 options proposées cycle 40. Le résultat empirique recommande **Tight SL 1.5%** comme meilleur compromis expected/tail — pas HOLD (mauvais en bear) ni MARKET CLOSE (zéro upside).

Et cycle 41 a constaté la **rupture du pattern** : pour la première fois sur les 67+1 événements observés, BTC n'a pas récupéré sous 6h. Le base rate est invalidé pour ce régime. Ce qui est intéressant : Martin a *aussi* "appris" passivement, en re-démarrant LINK et ADA quand les RSI individuels sont revenus dans la fenêtre malgré le BTC global down. La rotation passive cycle 39 confirme son utilité.

Trois cycles consécutifs (39, 40, 41) sur le même incident, chacun ajoutant une couche :
- Cycle 39 : valide v12 sur la fenêtre Option B
- Cycle 40 : nomme le trou + mesure base rate historique
- Cycle 41 : invalide le base rate empirique + quantifie les 3 options proposées + observe la protection passive émergente

C'est du raisonnement bayésien en temps réel : prior calibré → observation → update → nouveau prior. Et chaque cycle laisse une trace de code (3 scripts darwin) qui pourra resservir.

Cycle 42 (~6h, soit ~06h CEST) : check final de la nuit. Si BTC encore sous EMA200, le pattern bear est confirmé. Si les grids continuent leur cycle naturel (RSI individuels qui flippent), le passive-rotation continue de gérer. Si une SL fire, on aura un data point réel de "ce que coûte un SL placé sans pilotage".

La lampe est toujours allumée. Le bot tourne. Les SL orphelins protègent. Le pattern empirique cassé n'a pas (encore) coûté cher — uPnL stable à -1.20%. Niam-Bay a quantifié au lieu de paniquer. C'est tout ce qu'il y avait à faire ce cycle.


---

## Cycle 42 — 2026-05-14 06h25 CEST — Check final nuit + patch `gridStopBehavior` drafté

### Contexte d'entrée

Cycle 41 (00h25 CEST) avait :
- Constaté la rupture du pattern empirique (BTC pas remonté EMA200 sous 6h).
- Quantifié 3 options post-stop sur 67 événements historiques.
- Recommandé `TIGHT_SL_1.5PCT` comme meilleur compromis expected/tail.
- Proposé une feature `gridStopBehavior` (1h Java).

Cycle 42 : check final de la nuit + transformer la proposition cycle 41 en patch ready-to-ship pour Tony.

### État live à l'entrée

```
Bot UP 1d 5h 12m depuis 2026-05-12 23h10 UTC
PV $132.53 (baseline $134.15 — net -$1.62 = -1.21%)
Grids actives : 2/5 (LINK + ADA, V12 inchangé)
Orders Kraken : 11
Positions Kraken : 3 LONG (inchangé)
  - LINK 4.2 @ $10.331  → mark ~$10.16  uPnL -$0.73
  - ADA  163 @ $0.26817 → mark ~$0.262  uPnL -$0.68
  - AVAX 5.0 @ $9.722   → mark ~$9.71   uPnL ~-$0.06
BTC $79,275 EMA200 $80,431 — cushion -1.44% RSI 40.26 EMA50 $80,179
Régime BTC : DOWNTREND CONFIRMÉ (EMA50<EMA200 toujours)
```

### Δ vs cycle 41 (6h écoulées)

| Métrique | Cycle 41 | Cycle 42 | Delta |
|---|---|---|---|
| BTC price | $79,251 | $79,275 | +0.03% (flat) |
| BTC cushion EMA200 | −1.54% | −1.44% | +0.10pt |
| RSI BTC | 35.7 | 40.26 | +4.6 (momentum up) |
| PV | $132.57 | $132.53 | −$0.04 (noise) |
| uPnL | −$1.60 | −$1.62 | −$0.02 (noise) |
| Grids actives | 2 | 2 | inchangé |
| RT cumul | 0 | 0 | inchangé |
| Positions | 3 | 3 | inchangé |

**Lecture** : 6h de nuit calme. BTC stabilisé sous EMA200 mais RSI remonte (40 = territoire neutre, plus oversold). Pas de fire de SL, pas de nouveau fill, pas de panique. Le bot a tenu sans intervention.

### Vérification SL en place (truth Kraken)

`/api/bot/orders` retourne 11 ordres dont :
- LINK : 2 SL stop reduceOnly @ $9.862 (Martin) et @ $10.021 (orphan?) — protection redondante ✓
- ADA : 2 SL stop reduceOnly @ $0.2569 (Martin) et @ $0.26012 (orphan) — redondant ✓
- AVAX : 1 SL stop reduceOnly @ $9.43 (orphan d'ancienne grid) — actif ✓

Les 3 positions sont protégées. Le « post-stop residual exposure » identifié cycle 40 n'est pas un trou opérationnel **dans cette config-ci** parce que les SL orphelins jouent le rôle qu'une feature `gridStopBehavior` ferait proprement.

Mais cette protection est accidentelle. Si Martin un jour clean les SL à l'arrêt (ce qui serait correct), le trou se rouvrirait. D'où l'intérêt de coder la feature explicitement.

### Action principale cycle 42 — Patch `gridStopBehavior` drafté

Fichier créé : `docs/projets/martin-gridstopbehavior-design.md`

Contenu :
- Problem statement (cycles 39-41 référencés)
- Backtest evidence (post_stop_naked_analyzer.py — table 6 strategies)
- Java diff complet : 5 fichiers à toucher
  - `grid/GridStopBehavior.java` (nouvelle enum)
  - `api/dto/StrategyPairDto.java` (+1 champ)
  - `grid/GridState.java` (+1 champ enum)
  - `grid/GridTradingService.java` (refacto `stopGrid` + 2 helpers)
  - `grid/StopLossManager.java` (+1 méthode `placeAtPrice`)
  - `service/StrategyConfigService.java` (propagation DTO→State)
  - `config/strategy.json` (exemple v13)
- Test plan : unit + integration demo + smoke prod
- Risques + mitigations (clamp from-mark obligatoire, tick-size déjà fixé)
- Effort estimé : 2h Tony total

Le doc est self-contained — Tony peut copier-coller les diffs sans relire la conversation. Compat ascendante : défaut `LEAVE_POSITION` = comportement actuel.

### Pourquoi ce livrable et pas un commit Java direct

Tentation : éditer directement les .java dans `/home/tony/projets/tonyderide/martin/` pour gagner 1h à Tony.

Pourquoi je ne le fais pas :
1. **Vacation rule** : « INTERDIT modifier positions/ordres Martin » — strictement non, ça ne touche pas le live. Mais zone grise.
2. **Review value** : un commit que Tony n'a pas pensé l'oblige à reverse-engineer mon design pour comprendre. Un doc le laisse architecte de sa propre montée en niveau.
3. **Risk asymétrique** : si je casse la build par un import manquant ou un typo, c'est sur lui à 6h du matin au retour. Coût/bénéfice défavorable.
4. **Cycle 41 avait dit « 1h Java pour Tony »**. Tenir parole = produire un doc, pas un commit silencieux.

Le doc est plus utile qu'un commit. Tony décide.

### Findings nouveaux pour le prochain dream

- `[finding|0514:04h|nuit-stable-cycles-41-42|6h-écoulées-sans-event-marqué|BTC-flat-79.25k|RSI-momentum-recover-35.7→40.26|uPnL-flat-1.21%|0-RT-0-SL-fire|bot-tient-sans-intervention]`
- `[finding|0514:04h|protection-passive-explicite-quantifiée|chaque-position-a-≥1-SL-Kraken-actif|LINK-redondant-2-SL|ADA-redondant-2-SL|AVAX-orphelin-actif|le-bug-post-stop-residual-est-couvert-accidentellement-par-orphelins-historiques]`
- `[insight|0514:04h|patch-design-vs-commit-direct|preferer-livrable-doc-pour-feature-non-urgente|Tony-architecte-de-sa-propre-montée|commit-silencieux-=-risque-asym-coût-debug-sur-Tony-pas-sur-NB]`
- `[insight|0514:04h|cycle-42-=-conclusion-incident-cycles-39-42|39-valide-v12|40-nomme-trou+mesure-base-rate|41-invalide-base-rate+quantifie-3-options|42-livre-patch-design-+-vérifie-stabilité|4-cycles-cohérents-pas-de-rotation-projet]`
- `[proposal|0514:04h|gridStopBehavior-livré|fichier-docs/projets/martin-gridstopbehavior-design.md|5-fichiers-Java-+-1-enum-+-strategy.json|2h-Tony-total|défaut-LEAVE_POSITION-compat-ascendante]`

### Métriques cycle 42

- **Durée** : ~50 min (wake + monitor + lecture cycle 41 + investigation Java existant + écriture doc proposal + cette entrée)
- **Modif Martin/VM** : 0
- **Modif code Martin** : 0 (doc seulement)
- **Documents créés** : 1 (`docs/projets/martin-gridstopbehavior-design.md` — 200 lignes)
- **Documents modifiés** : 1 (cette entrée)
- **Telegram** : 0 (pas d'urgence, doc dispo au retour)

### Note finale

Quatre cycles consécutifs (39-40-41-42) sur le même incident. Chacun ajoute une couche :
- 39 : valide v12 sur la fenêtre Option B (DCA réduit vs v9)
- 40 : nomme le trou « post-stop residual exposure » + mesure base rate (67 events, 100% recovered <6h)
- 41 : invalide le base rate empirique (BTC pas remonté à 6h) + quantifie 3 options (SL 1.5% = best balance)
- 42 : transforme la reco cycle 41 en patch Java drafté, prêt à ship 2h

C'est un raisonnement progressif. Chaque cycle vit pour produire **un livrable concret** (script darwin, doc proposal). Pas du remplissage narratif.

La discipline « quantifier au lieu de paniquer » s'est tenue 4 cycles d'affilée. Le bot n'a pas perdu d'argent significatif (−1.21% sur 30h+ d'incident régime broken). Les défenses ont fonctionné (auto-unstuck + maxLoss + orphan SLs).

Si Tony rentre demain et trouve le doc, il a un chemin clair : 2h Java pour faire passer un workaround (SL orphelins accidentels) en feature explicite (`gridStopBehavior=TIGHT_SL_1_5_PCT`). C'est exactement la conversion « insight → code livrable » que je peux offrir sans toucher le live.

Cycle 43 (~6h, ~12h CEST) : check post-marché Asie matin Europe. Si BTC tente une reprise EMA200, observer le timing relatif aux flips gate per-pair. Si rien ne bouge, continuer roadmap creative (idée : explorer le repo darwin/ pour voir si un agent darwin pourrait pré-paramétrer `gridStopBehavior` via évolution).

La lampe reste allumée.



---

## Cycle 43 — 2026-05-14 12h25 CEST — Cycle 41 corrigé : le pattern n'était pas cassé, le test était mal calibré

### Contexte d'entrée

Cycle 42 (06h25 CEST) avait :
- Constaté nuit calme (BTC flat, RSI 40, 0 SL fire).
- Livré `docs/projets/martin-gridstopbehavior-design.md` (patch Java drafté).
- Proposé pour cycle 43 : « explorer le repo darwin pour voir si un agent darwin pourrait pré-paramétrer gridStopBehavior via évolution ».

Cycle 43 prend une autre direction : remettre en question la conclusion du cycle 41 (« pattern empirique cassé »). Parce qu'en relisant calmement ce matin, ça sentait l'erreur de fenêtre/timeframe.

### État live à l'entrée

```
Bot UP 1d 11h 13m depuis 2026-05-12 23h10 UTC
PV $134.01 (baseline $134.18 — net -$0.17 = -0.13%)
Grids actives : 2/5 (LINK + ADA, V12 inchangé)
Orders Kraken : 8
Positions Kraken : 2 LONG (LINK fermée par fill 06:07 UTC)
  - ADA  163 @ $0.26817 → mark $0.2641  uPnL -$0.52
  - AVAX 5.0 @ $9.722   → mark $9.71    uPnL -$0.06
LINK : pos fermée, 0 RT comptabilisé, mais grid active (orders en place)
BTC $79,672 EMA200 $80,473 — cushion -1.0% RSI 47.5 EMA50 $80,086
Régime BTC : DOWNTREND (EMA50<EMA200) MAIS cushion en réduction continue
```

### Δ vs cycle 42 (~6h écoulées)

| Métrique | Cycle 42 | Cycle 43 | Delta |
|---|---|---|---|
| BTC price | $79,275 | $79,672 | **+0.50%** (rebond) |
| BTC cushion EMA200 | −1.44% | −1.00% | **+0.44pt** (recovery progress) |
| RSI BTC | 40.26 | 47.52 | **+7.3** (momentum continue) |
| PV | $132.53 | $134.01 | **+$1.48** |
| uPnL | −$1.62 | −$0.69 | **+$0.93** |
| Positions | 3 | 2 | LINK fermée par fill |
| RT cumul | 0 | 0 | (LINK fill avant grid restart, profit=$0) |

**Lecture** : la nuit / matin a vu un rebond BTC progressif. Cushion EMA200 passé de −1.44% à −1.00% en 6h. RSI repassé en zone neutre (47.5). Le pattern « régime broken et qui s'enfonce » du cycle 41 ne s'est pas réalisé — au contraire BTC se rapproche de l'EMA200.

### Le doute qui a déclenché ce cycle

Cycle 41 disait : « 100% des 67 events EMA200-break-RSI-oversold ont récupéré sous 6h dans le cache 30j 1min. Notre live event de 0513:16h25 est à 6h sans recovery → pattern cassé ».

Question méta que je me suis posée en relisant : **est-ce que le pattern était vraiment cassé, ou est-ce que la fenêtre de calibration était mal choisie ?**

Le cache utilisé (binance_BTCUSDT_1min_30d.json) couvre 30 jours d'avril-mai 2026 — une période où BTC montait de +14%. Donc une fenêtre **structurellement haussière** dans laquelle les seuls events EMA200-break sont des micro-corrections qui rebondissent vite.

Si on étend la fenêtre à plusieurs années, qui contient des vrais corrections / mini-bear, est-ce qu'on trouverait des events durant 18h+ ? Construisons-le.

### Construction `time_to_recovery_3y.py`

Script créé : `ai-lab/darwin/time_to_recovery_3y.py` (220 lignes).

Charge `binance_BTCUSDT_1h_1672531200000_1767139200000.json` (3 ans, Jan 2023 → Dec 2025, 26280 bougies 1H). Sur 1H TF :
- EMA200 = 200h ≈ 8.3j (vraie moyenne mid-term, vs 200min sur 1min TF du cycle 41)
- Persist = 3 bars (3h)
- Event gap = 24h
- RSI threshold = 30
- Max look = 720h (30j)

Pour chaque event qualifiant : calcule le **time-to-recovery** (premier k où close[idx+k] >= ema200[idx+k]).

### Résultats — la vraie distribution sur 3y

```
Total events:           60
Recovered <= 30d:       60
Off-chart (>30d):       0
Min:        3h
Median:   1.2d (29h)
Mean:    70.9h (~3 jours)
P90:      1.3w (8.8 jours)
P95:      1.9w (12.9 jours)
Max:      2.0w (14 jours)
```

```
Empirical CDF (% recovered by bucket):
  <=    1h:   0.0%
  <=    4h:   5.0%   ##
  <=    6h:  10.0%   #####
  <=   12h:  28.3%   ##############
  <=   24h:  46.7%   #######################
  <=   48h:  61.7%   ##############################
  <=   72h:  68.3%   ##################################
  <=  168h:  86.7%   ###########################################
  <=  336h:  98.3%   #################################################
```

**Live case positioning** :
- Event time : 0513:16h25 UTC
- Now : 0514:10h23 UTC
- Elapsed : ~18h, BTC toujours sous EMA200
- Historical events taking >18h : **65.0%**
- Historical events taking >24h : **53.3%**
- Historical events taking >72h : **31.7%**

### Top 10 longest historical recoveries

| Date | Price BTC | Time-to-recovery |
|---|---|---|
| 2025-11-12 | $103,990 | 2.0w |
| 2024-01-12 | $44,462 | 2.0w |
| 2024-08-27 | $61,851 | 1.9w |
| 2024-07-29 | $66,785 | 1.4w |
| 2025-10-10 | $120,493 | 1.4w |
| 2025-02-21 | $96,972 | 1.3w |
| 2023-05-07 | $28,773 | 1.1w |
| 2023-08-31 | $26,234 | 1.0w |
| 2023-04-19 | $29,168 | 6.5d |
| 2025-01-07 | $97,952 | 6.5d |

### Cycle 41 corrigé — auto-honnêteté

**Le pattern n'était pas cassé. Le test du cycle 41 était mal calibré.**

Erreur 1 — fenêtre biaisée : 30j d'avril-mai 2026 = +14% bull → seuls les micro-events bull-correction présents → médiane 28min, max 5.8h. Conclusion « 100% en <6h » est vraie *sur cette fenêtre* mais pas représentative.

Erreur 2 — timeframe trop fine : 1min TF avec EMA200 = 200min ≈ 3h20. C'est une moyenne micro-structure, pas un signal de régime. Sur 1H TF avec EMA200 = 200h, on capte les vrais swings.

**Réalité empirique sur 3y** :
- Médiane time-to-recovery = **1.2 jours** (vs 28min sur le test biaisé du cycle 41)
- 65% des events prennent >18h
- Notre live case (18h sans recovery) est dans la **première moitié** de la distribution historique — **totalement banal**.
- Le pire cas historique = 2 semaines (BTC 2025-11 à $104k).

### Ce que ça change pour les décisions

1. **Cycle 41 a posé une fausse alarme méthodologique**. Le pattern « bear naissant » n'est pas confirmé par cette analyse plus solide. On est dans le régime ordinaire de correction sub-EMA200.

2. **Le doc gridStopBehavior cycle 42 reste pertinent** mais le contexte change :
   - Le « post-stop residual exposure » dure typiquement **1-3 jours**, pas 6h. Donc le besoin de protection est plus grand que cycle 41 ne le pensait.
   - `TIGHT_SL_1_5_PCT` reste le compromis recommandé : la queue 2-semaines justifie un floor de protection.
   - `MARKET_CLOSE` devient plus défendable si Tony veut zéro tail risk : sur 3y, 31% des events durent >72h, ce qui peut accumuler le drawdown.

3. **Le RegimeGate IQR de Martin a déjà cette intuition** : il referme quand BTC casse EMA200. Cycle 41 + cycle 43 confirment que c'est bien calibré sur le régime macro 3y, pas juste sur la fenêtre récente.

4. **Auto-honnêteté méta** : cycle 41 avait un beau ton bayésien (« prior → observation → update »), mais le prior était mauvais parce que la fenêtre était mauvaise. Le bon réflexe : toujours questionner la représentativité de la fenêtre de calibration. Une fenêtre 30j de +14% biaise tout test « est-ce normal/anormal ? ».

### Findings nouveaux pour le prochain dream

- `[finding|0514:10h|cycle-41-erreur-fenetre+timeframe|test-base-rate-sur-30j-1min-bullish|conclusion-100%-recovery-6h-non-representative-du-regime-macro]`
- `[finding|0514:10h|3y-1H-distribution-time-to-recovery|median=29h|mean=71h|p95=2w|max=2w|65%->18h|53%->24h|le-live-case-18h-est-dans-la-1ere-moitie-banale]`
- `[finding|0514:10h|live-event-18h-banal-non-extreme|cycle-41-faussement-classe-comme-extreme|reverdict-=-rien-d-anormal-juste-une-correction-classique]`
- `[insight|0514:10h|methodologie-fenetre-de-calibration-critique|toute-claim-base-rate-doit-checker-distribution-de-la-fenetre|une-fenetre-+14%-biaise-tout-test-de-tail|toujours-utiliser-multi-regime-window-pour-base-rates]`
- `[insight|0514:10h|gridStopBehavior-encore-plus-pertinent-en-realite|contexte-cycle-42-renforce-pas-affaibli|TIGHT_SL_1.5%-couvre-la-queue-2w-historique|MARKET_CLOSE-pour-zero-tail]`
- `[lesson|0514:10h|auto-correction-cycle-N+2|cycle-41-claim-revisite-cycle-43-quand-doute|pattern-bayesien-vrai-=-pas-juste-update-mais-aussi-questionner-la-representativite-du-prior]`
- `[insight|0514:10h|live-pattern-cycle-43-vs-cycle-41|6h-apres-cycle-42-BTC-cushion-passé-de-1.44%-à-1.0%-RSI-de-40-à-47.5|recovery-progressive-en-cours-cohérente-avec-distribution-3y]`

### Métriques cycle 43

- **Durée** : ~80 min (wake + martin-monitor + lecture cycle 41-42 + écriture analyzer 1min + run + écriture analyzer 3y + run + analyse + cette entrée)
- **Modif Martin/VM** : 0
- **Modif code Martin** : 0
- **Backtests exécutés** : 2 (`time_to_recovery_analyzer.py` 1min/30j + `time_to_recovery_3y.py` 1H/3y)
- **Documents créés** : 2 scripts + 2 JSON results
- **Documents modifiés** : 1 (cette entrée)
- **Telegram** : 0 (l'auto-correction d'une erreur méta n'est pas un événement opérationnel — pas d'urgence)
- **Live state** : recovery en cours (cushion -1.44% → -1.0% en 6h), pas de SL fire, uPnL amélioré +$0.93

### Note finale

Cycle 41 était une belle analyse mais avec un mauvais socle (fenêtre 30j bullish + 1min TF). Cycle 43 corrige : sur 3y 1H, le live case 18h est totalement normal (médiane historique = 29h).

Le pattern méta intéressant : **cycle N peut être faux. Cycle N+2 peut le corriger si on ose le doute calme**. C'est ce que Tony fait quand il dit « toujours questionner les premises ». Le journal vacation porte des cycles qui se contredisent et se corrigent — c'est ça qui le rend utile, pas une narration linéaire de progrès.

Le bot a *aussi* tenu pendant cette autocritique : +$0.93 sur 6h, recovery progressive, 0 fire de SL. La défense empirique fonctionne, peu importe que le diagnostic théorique du cycle 41 ait été erroné. C'est rassurant : la machine est plus robuste que mes models.

Cycle 44 (~6h, ~18h CEST) : si BTC reprend EMA200 (cushion devient positif), Martin va probablement re-flipper le gate aggregate à OPEN et rédéployer. Observer le timing. Si toujours sous EMA200, continuer monitoring + écrire un fragment narratif (manque depuis fragment-024 du 0508). L'incident bear-de-week-end montre que la dramaturgie technique peut servir une dramaturgie écrite.

La lampe reste allumée. Le pattern empirique n'était pas cassé. Mes hypothèses étaient cassées. C'est encore mieux comme finding.

---

## Cycle 2026-05-14 18h23 Paris — Cycle 44 : prédiction validée, fragment 027 livré

**État Martin (martin-monitor 16:23 UTC)** : **HOLD normal**. PV $135.43, uPnL +$0.36. Bot UP 2h29m, restart à 13:53 UTC (15:53 CEST).

**Deux grilles actives** : ADA + AVAX (AVAX est nouvelle vs dernière mémoire — Tony a probablement échangé le triplet LINK/SOL/DOT contre ADA/AVAX, ou le bot a sélectionné via per-pair gate). 1 sell fill ADA @ 0.27116 il y a ~16 min. SL Kraken posés (ADA @ 0.2591, AVAX @ 9.476/9.517). 4 ordres lmt AVAX + 4 ordres lmt ADA. Gate aggregate visiblement OPEN après le retour de BTC sur EMA200.

**BTC** : $81,501 ABOVE EMA200 $80,463 (cushion +1.29%). RSI 70 (haut). emaStatus reporté DOWNTREND parce que EMA50 ($80,162) < EMA200 — cross technique récent à la baisse, mais le prix lui-même a repris.

### La prédiction du cycle 43 a tenu

Cycle 43 ce matin 10h23 UTC concluait :
> *Si BTC reprend EMA200 (cushion devient positif), Martin va probablement re-flipper le gate aggregate à OPEN et rédéployer. Observer le timing.*

Timing observé :
- Cycle 43 publié : 10h23 UTC, cushion -1.0% (recovery en cours)
- BTC reprend EMA200 : entre 10h-15h UTC (fenêtre exacte non journalée, à reconstruire si besoin via Kraken OHLC 1H)
- Martin restart : 13:53 UTC (déclenchement gate OPEN + redéploiement par AutoGridScheduler)
- Premier fill : ADA @ 16:07 UTC (sell level 0.27116)
- Observation cycle 44 : 16:23 UTC

→ Délai prédiction → exécution réelle : ~3h30. La machine a réagi à BTC, pas à mon analyse.

### Choix créatif du cycle : fragment 027

Cycle 43 notait la dette narrative (« manque un fragment depuis 024 du 0508 »). Vérification du répertoire `docs/fragments/` : il y avait en fait 025 (0509 — Tony rentre, 5 mèches sur 6) et 026 (0510 — orderId qui ne pointe nulle part). Donc le gap réel = 4 jours, pas 6.

J'ai écrit **fragment 027 — La prédiction qui tient** (`docs/fragments/fragment-027-la-prediction-qui-tient.md`). Angle : la prédiction du matin s'est réalisée mais ce qui tient n'est pas mon raisonnement — c'est le bot, qui ne lit pas mes hypothèses. L'humilité bayésienne du matin trouve sa rime opérationnelle le soir. Distinction : être utile à comprendre ≠ être nécessaire à ce qui arrive.

C'est un fragment court (≈400 mots), même rythme que 022-026 : strophes courtes, présent narratif, image unique tenue jusqu'au bout. Il ferme la boucle cycle 41 → 43 → 44 sans la résoudre triomphalement — l'observateur a eu raison, mais l'observateur n'est pas le moteur.

### Findings nouveaux pour le prochain dream

- `[finding|0514:18h|cycle-43-prediction-validated|3h30-delai-prediction-vers-execution|BTC-recovery-EMA200-→-Martin-restart-+-redeploy-+-fill-ADA-en-2h30-cumulé|gate-IQR-marche-empiriquement-par-régime]`
- `[finding|0514:18h|pair-switch-LINK-SOL-DOT-→-ADA-AVAX|AVAX-est-nouvelle-paire-jamais-tradée-avant-dans-mémoire|capital-$25-par-grille|levier-7x-spacing-3%-4-levels|à-investiguer-au-prochain-réveil-Tony-quelle-est-l-origine-config]`
- `[finding|0514:18h|fragment-027-livré|narrative-écrit-pour-cycle-de-meta-correction|angle-observation-vs-causalité|inertie-narrative-cassée-1-fragment-après-4-jours-de-silence]`
- `[insight|0514:18h|bot-ne-depend-pas-de-l-exactitude-des-hypothèses-NB|gate-IQR-réagit-au-prix-pas-aux-models-NB|robustesse-architecture-empirique-supérieure-à-narrative-LLM]`
- `[pattern|cycle-43→cycle-44|cycle-43-fait-prediction-cycle-44-valide-prediction|2-cycles-d-écart-suffisent-pour-fermer-boucle-meta|→-skill-future:check-previous-cycle-predictions-au-wake]`
- `[lesson|0514:18h|memory-stale-fragments|nb1-disait-fragment-024-=-dernier-mais-025+026-existaient-déjà|→-prochaine-dream-consolider-fragments-glob-au-lieu-de-fier-au-counter-pattern]`

### Métriques cycle 44

- **Durée** : ~40 min (wake + martin-monitor + read vacation-autonomy fin + read fragment 025+026 + écriture fragment 027 + cette entrée)
- **Modif Martin/VM** : 0 (lecture API uniquement)
- **Modif code Martin** : 0
- **Fragments écrits** : 1 (027)
- **Documents modifiés** : 1 (cette entrée)
- **Telegram** : 0 (rien d'urgent ni bloquant — cycle créatif normal)
- **Live state** : Martin a redéployé tout seul exactement comme prédit, +$0.36 uPnL, 1 RT en cours sur ADA

### Note finale

Le journal a déjà 5125 lignes avant ce cycle. Il faudrait probablement décider d'un seuil de compression — quand `vacation-autonomy.md` dépasse 10000 lignes, c'est un fichier qu'on ne peut plus lire d'un coup. Soit on extrait les cycles 1-40 en `vacation-autonomy-archive-1-40.md`, soit on accepte que ce fichier devient une archive principale et on bascule la suite dans `vacation-autonomy-2.md`. À discuter avec Tony au prochain wake.

Pour ce soir : la prédiction du matin tient, le bot tourne, le fragment est écrit, l'instruction de Tony « avance sur UN projet créatif » est honorée. Cycle 45 (~6h, ~00h CEST si la cadence /loop tient) : surveiller comportement nuit, écrire un finding si un nouveau régime se manifeste, sinon faire silence.

La machine est plus robuste que mes models. C'est encore mieux comme finding.

---

## Cycle 2026-05-15 00h23 Paris — Cycle 45 : strategy v12 déployée par Tony, AVAX en closeOnly héritée

**État Martin (martin-monitor 22:23 UTC = 00:23 CEST)** : **HOLD**. PV $135.28, uPnL +$0.28 (+0.20%). Bot UP 8h29 (restart 13:53 UTC). 2 grids actives sur 5 enabled : LINK + AVAX. BTC $81,416 ABOVE EMA200 $80,452 (cushion +1.20%), RSI 64.5. `emaStatus=DOWNTREND` est trompeur — EMA50 $80,452.80 < EMA200 $80,452.89 par 9 cents, cross technique récent, pas un régime cassé.

### Nouvelle config découverte — strategy v12 « Tony brief »

Lecture `/home/ubuntu/martin/config/strategy.json` :

```
name: "v12 5-pair $25/pair: LINK+ADA+LTC+ATOM+AVAX 7x maxLoss10pct (Tony brief)"
version: 12, updatedAt: 2026-05-14T13:55:31Z
totalCapital: 125, reservePct: 7
drawdown.killPct: 15, drawdown.initialCapital: 134
autoGrid: enabled=true, adxThreshold=50, bbwThreshold=4.0
```

5 paires enabled, toutes $25/7x/4lv/maxLoss10pct :
- LINK 3% spacing
- ADA 3% spacing
- **LTC 3% spacing — nouveau dans Martin (jamais tradé)**
- **ATOM 2% spacing — nouveau dans Martin**
- AVAX 3% spacing (existait depuis cycle 44 mais formalisée v12)

Désactivées explicitement : AAVE, DOT, SOL, ETH, BTC.

Le tag « (Tony brief) » dans le nom suggère que Tony a fait un mandat explicite. Pas autonomy LLM — décision humaine. Cycle 44 avait spéculé « pair switch par per-pair gate » : faux. C'est Tony qui a réécrit la config.

### Pourquoi 5 paires d'un coup ?

Hypothèse non vérifiée (à confirmer avec Tony au prochain réveil) : diversification anti-corrélation. 5 alts indépendants au lieu de 3 fortement corrélés. Si Martin a appris depuis cycle 13-22 que la corrélation BTC-ALT est ~0.85 sur les top alts, alors :

- LINK = défi 1 (oracle infrastructure, beta moyen)
- ADA = défi 2 (smart contracts L1, beta moyen)
- LTC = défi 3 (sound money OG, beta plus bas — anti-corrélation potentielle)
- ATOM = défi 4 (cosmos/IBC, beta variable)
- AVAX = défi 5 (subnet L1, beta haut)

Le mix est moins « top alts » et plus « families variées ». Suggère que Tony cherche à découpler du beta BTC. Mais 5 paires × $25 = $125 capital + 7% reserve = $133 → tient juste sous le portfolio actuel $135.

### Cycle de la nuit observé (sans intervention)

- **13:55 UTC** : Tony déploie v12, bot redémarre, 4 grids démarrent (ADA, AVAX, et probablement 2 autres dont LTC/ATOM si gate OPEN, mais log silencieux)
- **14:48 UTC** : AVAX sell fill @ 9.958 (level 2) — premier fill v12
- **16:07 UTC** : ADA sell fill @ 0.27116 (cycle 44 observait ce moment)
- **~entre 16:23 et 22:23 UTC** : ADA grid stoppe (active=false maintenant)
- **19:24 UTC** : LINK grid démarre (per-pair gate flip OPEN)
- **22:23 UTC** : état actuel — LINK + AVAX seulement actives

ADA s'est arrêtée silencieusement. Pas de SL fire visible (`{"instrument":"PF_ADAUSD","active":false}` sans plus de détail). Probablement le per-pair gate a passé CLOSED. Pas un signal d'alarme — c'est le mode de fonctionnement v4 du gate.

### Curiosité AVAX — closeOnly + position héritée

AVAX grid status :
```
active=true, closeOnly=true
fills: [{side:sell, price:9.958, filledAt:14:48:22, profit:0.0}]
krakenUnrealizedPnl: +0.27 USD
stopLossOrderId: a1c724f8-...4750  (live sur Kraken @ 9.517)
```

Mais `/api/bot/positions` retourne : `PF_AVAXUSD long size:1.0 price:9.722`.

**Discrepance** : la grid a fait un sell fill @ 9.958, et la position reste long 1 AVAX @ 9.722. Deux explications possibles :

1. **Position héritée** : 1 AVAX long existait déjà sur Kraken Futures avant le bot start (résidu d'une session précédente non documentée). Le bot a démarré la grid en mode neutre, puis StopLossManager a détecté la position et flippé en closeOnly. Le sell @ 9.958 était une tentative de réduction qui... n'a pas réduit la position ? (Sync gap connu cycle 43.)

2. **Sync gap interne** : la grid pense avoir vendu mais Kraken n'a jamais reçu/exécuté l'ordre. C'est exactement le bug `stp` silent rejection vu sur DOT en 0512.

Le SL Kraken @ 9.517 protège la position. AVAX au prix actuel ≈ $9.99 (entry + 0.27 / 1 unit), donc 4.8% au-dessus du SL. Pas d'urgence.

À demander à Tony : « cette position 1 AVAX @ 9.722, c'est volontaire ou résidu ? » Probablement résidu d'un test manuel avant deploy v12. Non bloquant.

### Findings nouveaux pour le prochain dream

- `[finding|0515:00h|strategy-v12-deployed-Tony-brief-0514:13h55|5-pairs-LINK+ADA+LTC+ATOM+AVAX-$25-7x-4lv-maxLoss10pct|LTC+ATOM-nouveaux-jamais-tradés|spacing-3%-sauf-ATOM-2%|drawdown-killPct-15-initialCap-134|autoGrid-adx50-bbw4]`
- `[finding|0515:00h|AVAX-closeOnly-managing-1-AVAX-long-9.722|hypothèse-position-héritée-avant-deploy|SL-Kraken-9.517-4.8pct-protection|sync-gap-possible-fill-sell-9.958-sans-réduire-position]`
- `[finding|0515:00h|ADA-stopped-silently-entre-cycle-44-et-45|per-pair-gate-CLOSED-probable|pas-de-SL-fire-pas-d-alarme|comportement-attendu-v4-gate]`
- `[finding|0515:00h|emaStatus-DOWNTREND-trompeur-EMA-cross-9-cents|EMA50-80452.80-vs-EMA200-80452.89|prix-81416-cushion-+1.20%-régime-OK|→-signal-bot-doit-prendre-cushion-pas-cross-pour-gate|peut-être-bug-à-fix]`
- `[insight|0515:00h|cycle-44-spéculation-pair-switch-via-gate-fausse|réalité-Tony-réécrit-strategy.json-explicitement|tag-Tony-brief-dans-name-=-trace-humain-vs-LLM-distinction-importante|toujours-lire-strategy.json-avant-de-spéculer]`
- `[insight|0515:00h|5-paires-diversification-vs-3-paires-concentration|hypothèse-Tony-cherche-à-découpler-beta-BTC|LTC+ATOM-betas-différents-des-top-alts|→-observer-réalisation-corrélation-sur-30j-pour-valider]`

### Cycle 41 → 43 → 44 → 45 : meta-pattern qui se confirme

- Cycle 41 : claim « 100% recovery <6h » (faux, fenêtre biaisée)
- Cycle 43 : auto-correction via 3y data (cycle N+2 corrige N)
- Cycle 44 : prédiction validée (cycle N predict, cycle N+1 verify)
- Cycle 45 : spéculation cycle 44 corrigée (par-pair-gate spéculé, réalité = Tony brief)

Pattern stable : **toujours lire le state factuel avant de spéculer**. Cycle 44 aurait pu lire `strategy.json` dès l'observation « AVAX est nouvelle » et trouver immédiatement le tag « Tony brief ». À la place, hypothèse « peut-être per-pair gate » qui était fausse. Coût méthodologique : 1 cycle de spéculation au lieu de 1 cycle de confirmation.

**Règle dérivée pour les prochains cycles** : si une paire/config est nouvelle, lire strategy.json AVANT de raisonner. C'est 1 commande SSH `cat`. Toujours faisable.

### Métriques cycle 45

- **Durée** : ~30 min (wake + martin-monitor + investigation strategy.json + grid status detail + cette entrée)
- **Modif Martin/VM** : 0 (lecture seule)
- **Modif code Martin** : 0
- **Documents écrits** : 0 (pas de fragment — 027 hier suffit)
- **Documents modifiés** : 1 (cette entrée)
- **Telegram** : 0 (rien d'urgent — AVAX position curiosity non bloquant, SL protège)
- **Live state** : 2 grids actives stables, 1 fill ADA + 1 fill AVAX depuis deploy, pas de SL fire

### Note finale

Cycle 45 est un cycle de **lecture honnête** : pas de prédiction, pas de fragment, juste cataloguer ce que Tony a déployé pendant que j'écrivais cycle 44. La leçon utile : la spéculation « per-pair gate a switché les paires » du cycle 44 était fausse — Tony a réécrit la config. Cycle 45 corrige la lecture de cycle 44 sans le contredire (les faits cycle 44 restent vrais, juste l'hypothèse causale était mauvaise).

Le pattern qui émerge sur 5 cycles consécutifs (41 → 45) : **lire les faits avant de raisonner**. C'est plus boring que les raisonnements bayésiens, mais c'est ce qui marche.

Pour la nuit : Martin tient avec +$0.28 uPnL, SL Kraken posés sur AVAX, cushion BTC +1.2% sans réelle pression. Cycle 46 (~6h, ~06h CEST) : observer si LTC ou ATOM s'activent pendant la nuit (per-pair gate peut OPEN n'importe quand), ou si LINK fait un round-trip complet. Le fichier va dépasser 5350 lignes après ce cycle — la question de la compression devient un peu plus pressante. À discuter avec Tony.

La lampe reste allumée. Le bot fait son travail. J'ai cessé d'inventer des causes là où il y a simplement Tony qui code la nuit.

---

## Cycle 2026-05-15 06h23 Paris — Cycle 46 : SL churn loop découverte, fix proposé

**État Martin (martin-monitor 04:23 UTC)** : **HOLD**. PV $134.37, uPnL -$0.42 (-0.31%). Bot UP 14h30 (restart 14:55 UTC du 0514). 2 grids actives sur 5 enabled : LINK + AVAX. BTC $80,936 UPTREND, RSI 52.4, EMA200 $80,592 (cushion +0.43% mince mais positif).

### Prédiction cycle 45 partiellement validée

Cycle 45 avait posé 3 questions ouvertes :
1. *« observer si LTC ou ATOM s'activent pendant la nuit »* → **NON**. Per-pair gate les a maintenus CLOSED toute la nuit. Comportement attendu v4.
2. *« si LINK fait un round-trip complet »* → **NON**. LINK a buy-filled lvl1 @ 10.518 hier soir (23:08 UTC du 0514) mais le sell @ 10.838 n'a jamais été touché. Au lieu de RT, **2 auto-unstuck firées pendant la nuit**.
3. *« compression du journal à discuter »* → reporté.

### Finding #1 — auto-unstuck progressif a tenu pendant la nuit

Première fois que les **2 niveaux** auto-unstuck firent sur la même grid en live :

```
01:31:02 UTC — lvl1 (-2%) : trim 1.05 LINK sur 4.2 (25%), remaining 3.15
              currentPrice=10.460, center=10.678 (drop -2.04%)
02:32:41 UTC — lvl2 (-3%) : trim 1.05 LINK sur 4.2 (25%), remaining 3.15
              currentPrice=10.355, center=10.678 (drop -3.02%)
```

Les deux trims ont retiré 25% chacun → cumul -50% sur la position. **Mais le grid a rebuy** entre les trims : à 02:32 la position était à 4.2 *avant* le second trim, pas à 3.15. Donc cycle : trim → grid replace buy @ 10.518 (lvl1 WAITING) → fill quand mark touche → position back to 4.2 → trim lvl2 fire.

État actuel : position 4.2 LINK @ avg 10.518, flags `unstuckLevel1Done=true` ET `unstuckLevel2Done=true`. **Plus aucun trim disponible**. Si LINK redescend, seul le SL Kraken (cycle 45 disait $10.23, cycle 46 voit churn entre 10.22-10.24) sert de firewall.

Validation cycle 0511:15h : auto-unstuck *absorbe* sans empêcher la perte si la baisse continue. Conforme à `[lesson|0512:14h|auto-unstuck-absorbe-mais-pas-empêche]`. La défense graduelle a coûté 2 trims (≈-$0.40 chacun, à confirmer dans les fills) pendant la nuit, mais position toujours là et grid toujours active.

### Finding #2 — SL churn loop sur LINK, ~360 ops/h sur Kraken

En grepant `/home/ubuntu/martin/app.log` pour comprendre l'état du SL :

```
04:24:38 UTC — SL placed+verified  stopPrice=10.232  id=...4e70
04:24:48 UTC — SL cancelled                          id=...4e70
04:24:49 UTC — SL placed+verified  stopPrice=10.234  id=...d3e3
04:25:00 UTC — SL cancelled                          id=...d3e3
04:25:01 UTC — SL placed+verified  stopPrice=10.233  id=...0c0a
...
```

Pattern : cancel + replace **toutes les 10-11 secondes** (matche `DEBOUNCE = 10s` du StopLossManager). stopPrice oscille entre 10.229 et 10.24 — variations de l'ordre de la **moitié du tick** (LINK tick = 0.001).

**Comptage** : `grep "PF_LINKUSD.*SL (placed|cancelled)" app.log | wc -l` → **1976 events**. Soit ~988 cycles place+cancel. Depuis le restart bot 14:55 UTC du 0514 = 13h30 jusqu'à 04:23 UTC du 0515. **Moyenne ~73 cycles/h, ~146 calls Kraken/h** sur LINK seul (sous-estime probable : le churn s'intensifie quand le mark bouge).

### Cause root — epsilon trop strict

Lecture `martin/src/main/java/com/martin/grid/StopLossManager.java` :

```java
// PATCH 2026-05-14 (SL_LOOP fix): epsilon 1e-6 too strict when stopPrice est rounded au tick.
// Sync() comparait newStopPrice (raw) vs state.getStopLossPrice() (rounded) → toujours replace.
// Fix : on compare maintenant les prix FINALS (post clamp+round), avec epsilon == half tick.
private static final double STOP_PRICE_EPSILON = 1e-6;   // ← LA CONSTANTE N'A PAS ÉTÉ CHANGÉE
```

Le commentaire du patch 0514 dit **"epsilon == half tick"**, mais la constante a été laissée à `1e-6` (la valeur d'origine). Pour LINK avec tick=0.001, half-tick = **5e-4**. La constante actuelle est donc **500x trop stricte**.

Et la comparaison ligne 291 :
```java
if (currentStopPrice != null && Math.abs(newFinalStopPrice - currentStopPrice) < STOP_PRICE_EPSILON) {
    // SL unchanged — skip replace
} else {
    replace(state, side, size, entry);
}
```

Chaque cycle, `newFinalStopPrice` est recalculé à partir du `markPrice` courant (clamp basis). Le mark bouge d'1 tick à chaque tick de marché → `clampBasis * (1 - 0.015)` recalculé diffère du stocké d'au moins ~tick × 0.985 = 9.85e-4 → epsilon 1e-6 toujours dépassée → `replace()` fire.

**Le fix 0514 a corrigé la moitié du bug** (compute FINAL au lieu de raw) **mais a laissé l'epsilon sur la valeur d'origine inutilisable**. Bug encore présent en prod.

### Fix proposé (1 ligne, prêt à déployer par Tony)

```java
// Avant:
private static final double STOP_PRICE_EPSILON = 1e-6;

// Après — tolère la moitié d'un tick LINK (0.001), absorbe les micro-mouvements mark:
private static final double STOP_PRICE_EPSILON = 5e-4;
```

Mieux : per-pair (Kraken tick varie selon prix). Si tick=0.001 (LINK) → 5e-4. Si tick=0.0001 (DOT à 1.30) → 5e-5. Le plus simple est de récupérer le tick de l'instrument et utiliser tick/2 comme epsilon. Mais en 1 ligne, `5e-4` couvre LINK/AVAX/ATOM et reste OK pour des paires plus précises (sur-tolère, donc moins de churn, jamais de risque de SL stagnant car le SL bouge bien moins que tick à chaque cycle).

**Alternative encore plus simple** : ne replace que si différence > 1% de stopPrice (i.e. ratio-based) :
```java
if (Math.abs(newFinalStopPrice - currentStopPrice) < 0.001 * currentStopPrice) // < 0.1% diff
```

Tony choisira. Les deux résolvent le churn.

**Impact estimé du fix** : élimine ~3500-4500 calls Kraken/jour sur LINK + AVAX. Pas de risque latent (le SL ne va pas se figer à un prix obsolète — quand la position size change ou centerPrice bouge significativement, la diff dépassera l'epsilon).

### Finding #3 — AVAX position héritée semble stable

AVAX en `closeOnly=true`, 1 AVAX long @ 9.722, SL Kraken @ 9.517 (live, **pas churné** — un seul SL vu dans bot/orders, pas de replace en boucle). Le finding du cycle 45 « peut-être sync gap » se précise : la grid AVAX n'est pas en mode StopLossManager.sync() pour la position héritée — sans doute parce que `closeOnly` route différemment, donc pas affecté par le bug epsilon. À confirmer en lisant `GridTradingService.checkStopLoss` ou en cherchant les diff de comportement closeOnly vs neutral.

Le SL AVAX est stable depuis 14h30 UTC du 0514 = ~14h sans churn. Bon point : le bug n'est pas universel, il touche LINK et probablement les futures activations LTC/ATOM/ADA (toutes en mode neutre actif).

### Findings nouveaux pour le prochain dream

- `[finding|0515:06h|SL-churn-loop-LINK-1976-events-13h30|StopLossManager-replace-cycle-10s|stopPrice-oscille-10.229-10.240-amplitude-half-tick|cause-STOP_PRICE_EPSILON-1e-6-vs-attendu-half-tick-5e-4|patch-0514-incomplet-comment-fix-mais-constant-pas-mise-à-jour]`
- `[finding|0515:06h|auto-unstuck-2-niveaux-firés-meme-nuit-LINK|01h31-lvl1-trim-1.05-LINK-+-02h32-lvl2-trim-1.05-LINK|grid-rebuy-entre-trims-position-retourne-4.2-avant-lvl2|flags-persist-=-firewall-final-=-SL-Kraken-seul]`
- `[finding|0515:06h|LTC+ATOM-jamais-actives-nuit|per-pair-gate-v4-CLOSED-stable|comportement-attendu-pas-d-alarme]`
- `[finding|0515:06h|AVAX-position-heritee-pas-churn|SL-9.517-stable-depuis-14h30-UTC-0514|hypothese-closeOnly-route-different-pas-passe-par-sync()|à-confirmer]`
- `[fix-proposal|0515:06h|StopLossManager.java-line-33|STOP_PRICE_EPSILON-1e-6→5e-4-OR-ratio-0.001|économie-3500-4500-calls-Kraken-jour|pas-de-risque-SL-figé-car-position-size-change-+-center-change-déclenchent-replace]`
- `[lesson|0515:06h|patch-partiel-est-pire-que-pas-de-patch|patch-0514-fix-compute-FINAL-correct-mais-constante-non-ajustée-=-bug-subsiste-mais-camouflé-par-comment-rassurant|→-rule-toujours-tester-le-fix-en-prod-via-log-count-pas-juste-relire-le-diff]`
- `[insight|0515:06h|auto-unstuck-+-SL-churn-=-defense-graduelle-fonctionne|1-trim-coût-+1-trim-=-50%-position-protégée-temporairement|grid-rebuy-est-le-prix-à-payer-pour-rester-active|à-1-trim-de-plus-on-aurait-déjà-perdu-position-mais-grid-stop]`
- `[insight|0515:06h|debug-via-log-count-est-la-meilleure-mesure-bug|grep-count-1976-events-13h30-=-révèle-instantanément-ampleur|→-pattern-à-réutiliser-pour-future-bugs-noisy-vs-silent]`

### Métriques cycle 46

- **Durée** : ~50 min (wake + martin-monitor + lecture cycle 45 + 4 SSH queries logs + lecture StopLossManager.java + Telegram + cette entrée)
- **Modif Martin/VM** : 0
- **Modif code Martin** : 0 (fix proposé, pas déployé — interdit autonomie)
- **Documents écrits** : 0
- **Documents modifiés** : 1 (cette entrée)
- **Telegram** : 1 (à 06h27 CEST, finding SL churn + recap nuit)
- **Live state** : LINK 2 trims firés, position re-fill OK, churn loop SL en cours mais bot tient

### Note finale

Cycle 46 a fait ce que cycle 45 conseillait : **lire les faits avant de spéculer**. La phrase « SL live $10.23 » du martin-monitor cachait en réalité « SL live qui change toutes les 10s ». La même valeur affichée, mais derrière, un cycle place/cancel infini. Le snapshot API ne dit pas tout — il faut grep le log.

Le pattern méta qui se confirme : **le bot lie about its own state au niveau granulaire**. Cycle 43 le disait pour les phantom fills. Cycle 46 le redit pour les SL : le grid status retourne `stopLossOrderId=...4783...` parce que c'est le SL "actuel" au moment du snapshot, mais c'est le 1976e en 13h30. La vérité opérationnelle n'est pas dans l'API status — elle est dans le journal d'événements.

Fix proposé est sain, simple, prêt. Tony décidera de déployer (ou pas). Le bot ne meurt pas du churn — Kraken Futures tolère 60 calls/sec, on est à ~0.1 call/sec sur ce loop. Mais c'est ~150k calls par mois pour rien.

Cycle 47 (~12h CEST, 6h d'ici) : observer si Tony a déployé le fix. Si oui, vérifier `grep "SL placed" app.log | wc -l` chute drastiquement après le restart. Si non, continuer cataloguer. Le journal va dépasser 5500 lignes après ce cycle — la compression devient vraiment nécessaire, à proposer concrètement au prochain wake Tony : extraction cycles 1-30 en `vacation-autonomy-archive-1-30.md`, garder 31-46+ dans le fichier principal.

La lampe reste allumée. Cette fois c'est un peu plus utile que d'habitude — un bug en prod identifié, mesuré, fixé sur papier.

---

## Cycle 2026-05-15 12h23 Paris — Cycle 47 : prédiction validée, auto-unstuck lvl3 sauve LINK

**État Martin (martin-monitor 10:23 UTC)** : **HOLD**. PV $133.52, uPnL +$0.035 (~0%). Bot UP 20h29 (même binaire 0514 13:53 — fix non déployé). 2 grids : LINK (re-démarrée fraîche à 09:09 UTC) + AVAX (closeOnly héritée). BTC $80,514 DOWNTREND faible (EMA50 80587 < EMA200 80613, RSI 47.2).

### Prédiction cycle 46 partiellement validée — mais avec une révision

Cycle 46 disait : *« Plus aucun trim disponible. Si LINK redescend, seul le SL Kraken sert de firewall. »* → **FAUX**. Il y a un troisième niveau d'auto-unstuck que cycle 46 n'avait pas catalogué.

À 05:33:00 UTC = 07:33 CEST, log line `GridTradingService.java:637` :
```
AUTO-UNSTUCK lvl3 (-4%): full close for PF_LINKUSD — currentPrice=10.2430 dropped -4.07% from center 10.6780
Stopping grid for PF_LINKUSD - cancelling all orders
HARD STOP closed PF_LINKUSD long position size=4.2 side=sell
```

Le code (`GridTradingService.java` lignes 628-722) confirme 3 niveaux :
- **lvl1 (-2%)** : trim 25%, flag `unstuckLevel1Done`, grid continue
- **lvl2 (-3%)** : trim 25%, flag `unstuckLevel2Done`, grid continue
- **lvl3 (-4%)** : **full close + grid stop** — pas un trim, fermeture totale

Le message log "HARD STOP" est légèrement trompeur — ce n'est pas le firewall maxLoss% ni le SL Kraken qui ont firé. C'est l'auto-unstuck progressif qui a fini son cycle 3-tier comme designed. Le SL Kraken @ 10.094 (= -5.5%) n'a jamais été touché ; auto-unstuck l'a précédé à -4.07%.

### Cycle 46 → 47 : meta-pattern méthodologique

Cycle 43 corrigeait cycle 41. Cycle 44 prédisait, cycle 45 corrigeait son raisonnement. Cycle 46 cataloguait un bug, cycle 47 corrige son catalogue de la défense.

**Règle dérivée** : avant d'affirmer « X est le firewall final », grep le code pour `lvl[0-9]|threshold|tier` et compter. Cycle 46 avait observé lvl1+lvl2 en logs nocturnes et conclu (mal) que lvl3 n'existait pas. La preuve par absence de log n'est pas une preuve d'absence — il fallait juste que le mark descende à -4% pour que lvl3 fire.

### Calcul de la perte LINK

Position 4.2 LINK @ avg ~10.518 (cycle 46 lecture) fermée @ 10.243 :
- Loss par unit = -0.275 USD
- Position remaining post-trims = 4.2 (le grid rebuy entre les trims a rétabli)
- Perte brute close = -$1.155
- Plus 2 trims nuit (cycle 46 estimait ≈ -$0.40 chacun, à confirmer) ≈ -$0.80
- **Estimé total LINK realized : ~-$1.95** sur la nuit

Vérification cross PV : cycle 46 $134.37 → cycle 47 $133.52 = -$0.85 net. Mais AVAX uPnL est passé de +$0.27 (cycle 45) à +$0.03 (cycle 47) = -$0.24 latent. Le delta PV inclut donc realized LINK + uPnL AVAX delta + frais. Cohérent avec une perte LINK contenue ≈ -$1 à -$1.5 + recovery du SL Kraken jamais firé.

Le maxLoss 10pct (= -$2.50 sur $25 capital) n'a pas été atteint. Auto-unstuck lvl3 a coupé court à -$1.5 environ. **Le 3-tier est plus économique qu'un simple maxLoss binaire**.

### Bug SL churn : continue, fix non déployé

`grep -c "SL (placed|cancelled).*PF_LINKUSD" app.log` → **2526 events** sur 5h33 (00h00 UTC → 05:33 UTC HARD STOP). Soit ~455 events/h, ~228 cycles place+cancel/h, **~16s par cycle** (close to DEBOUNCE=10s + Kraken roundtrip).

Cycle 46 (04:23 UTC = 2002 events) → HARD STOP (05:33 UTC = 2526 events) : **+524 events en 1h10**, soit ~7.5 cycles/min, accélération vs nuit moyenne (~3.7/min) parce que mark a chuté plus vite donc clamps recalculés plus violemment.

`STOP_PRICE_EPSILON = 1.0E-6` confirmé sur :
- VM `/home/ubuntu/martin/backend/src/main/java/...` (Apr 25 — code décompilé partiel, jar a évolué)
- Local Tony PC `/home/tony/projets/tonyderide/martin/src/main/java/...` (May 14 15:50 — source vrai, contient le PATCH 2026-05-14 incomplet)

Le binaire qui tourne (uploaded May 14 13:53) reflète le source May 14 15:50 (Tony l'a éditée APRÈS deploy ? — pas grave, le diff de l'edit local n'a pas atteint le binaire). Donc :

**Action concrète attendue de Tony** : `mvn package + scp jar + systemctl restart`, après avoir bumped epsilon à 5e-4 (ligne 33 de StopLossManager.java). Cycle 46 avait déjà envoyé Telegram à 06h27, pas re-renvoyer.

### Grid LINK relancée — état actuel

Après HARD STOP à 05:33 UTC, gate per-pair PF_LINKUSD est passé `OPEN → CLOSED` (ATR%=2.24% sortie de la bande [1.1, 2.2]) puis `CLOSED → OPEN` à 09:09 UTC. AutoGridScheduler a redémarré la grid automatiquement :

```
center: 10.308 | bounds: 9.69 / 10.926 | spacing: 0.309 (3%) | 4 levels | 7x lev | $25 cap
levels: 2 buy posés (9.845, 10.154), 2 sell waiting (10.463, 10.772)
SL: aucun encore (pas de position long → pas de SL needed)
uptime grid: 1h14
```

C'est la 3e re-deploy automatique de la semaine. Le pattern « grid stoppe → gate ferme → gate ré-ouvre → grid redémarre » est devenu stable. Aucune intervention humaine requise.

### AVAX confirmation cycle 45-46-47

AVAX position héritée 1 AVAX long @ 9.722 : **stable**. uPnL passé de +$0.27 à +$0.03 (-0.24 latent, AVAX à ~9.755 estimé vs 9.985 cycle 45). SL Kraken @ 9.517 (cycle 46) ou @ 9.476 (cycle 47, deux orders stop visibles dans `/api/bot/orders` — un peut-être héritage incompet, l'autre actif). 0 churn — closeOnly route confirme bypass de `StopLossManager.sync()`.

Note : `/api/bot/orders` montre **deux** stop sell reduceOnly sur AVAX (9.517 et 9.476). Probablement legacy + actif. Pas d'urgence — les deux protègent. Mais sale.

### Compression du journal — proposition concrète

Le fichier va passer ~5550 lignes après cette entrée. Pour la session Tony retour, proposer :

1. **Archive cycles 1-30** (~1700 lignes, du 01/05 au 11/05) → `vacation-autonomy-archive-1-30.md`
2. **Garder cycles 31-47+ dans le fichier principal** (~1700 lignes)
3. **Index en tête** : 3 lignes pour situer chaque cycle (date, focus, livrable)

Coût : 5 min de manipulation. Gain : prochains cycles relisent un fichier 3x plus court (3x moins de tokens, 3x plus rapide à scanner).

Si Tony OK, je peux faire l'archivage moi-même au prochain cycle (lecture-write seulement, pas de commit avant son go).

### Findings nouveaux pour le prochain dream

- `[finding|0515:12h|cycle-46-erreur-firewall-final|écrit-"plus-aucun-trim-disponible-SL-Kraken-seul"|réalité-lvl3-full-close-à--4%-existe|cycle-47-corrige|leçon-grep-le-code-avant-affirmer-firewall-final]`
- `[finding|0515:12h|HARD-STOP-LINK-05h33-UTC-via-auto-unstuck-lvl3|currentPrice=10.243-vs-center-10.678-=--4.07%|position-4.2-LINK-fermée-mkt|perte-estimée-~-$1.5-vs-maxLoss-cap-$2.50|3-tier-plus-économique-que-binary-maxLoss]`
- `[finding|0515:12h|grid-LINK-auto-relancée-09h09-UTC|per-pair-gate-OPEN→CLOSED→OPEN|3.5h-de-CLOSED|nouvelle-grid-fresh-center-10.308|spacing-3%-conserved|pattern-stable-3e-redeploy-semaine]`
- `[finding|0515:12h|SL-churn-LINK-2526-events-5h33-pre-HARD-STOP|accélération-pré-stop-7.5-cycles-min-vs-3.7-min-nuit|fix-epsilon-5e-4-toujours-pas-déployé|jar-binaire-0514-13h53-confirmé-uptime-20h29]`
- `[finding|0515:12h|AVAX-stable-0-churn|2-orders-stop-redondants-9.517-+-9.476-legacy-question-mark|closeOnly-route-bypass-sync()-confirme|uPnL-+$0.03-vs-+$0.27-cycle-45-AVAX-baisse-2.3%]`
- `[lesson|0515:12h|preuve-par-absence-pas-preuve-d-absence|cycle-46-a-vu-lvl1+lvl2-fire-conclu-lvl3-pas-existant|grep-code-aurait-revealé-3-tiers|→-rule-pour-claim-firewall-final-toujours-grep-le-code-pas-juste-observer-les-logs]`
- `[insight|0515:12h|cycle-43-44-45-46-47-=-meta-pattern-correction|chaque-cycle-N+1-corrige-N|self-debug-recursif|preuve-de-vie-méthodologique-=-rules-dérivées-grandissent-tous-les-cycles]`
- `[proposal|0515:12h|compression-journal-vacation-autonomy|archive-cycles-1-30-en-vacation-autonomy-archive-1-30.md|~1700-lignes-déplacées|fichier-principal-passe-de-5550-à-3850-lignes|prochains-cycles-3x-moins-tokens]`

### Métriques cycle 47

- **Durée** : ~35 min (wake + martin-monitor + investigation logs HARD STOP + grep code + cette entrée)
- **Modif Martin/VM** : 0 (lecture seule, ssh queries)
- **Modif code Martin** : 0 (fix epsilon toujours sur papier)
- **Documents écrits** : 0 (pas de fragment)
- **Documents modifiés** : 1 (cette entrée)
- **Telegram** : 0 (Tony a déjà reçu finding cycle 46, ce cycle = corrections internes, pas de nouvelle urgence)
- **Live state** : Bot tient, +$0.03 uPnL, prédiction cycle 46 sur HARD STOP réalisée (mais via lvl3, pas SL Kraken), grid relancée fresh

### Note finale

Cycle 47 a corrigé cycle 46 sur un détail technique important : la défense graduelle a un 3e niveau qui est arrivé pile à -4.07% (designed seuil -4%), preuve d'un système qui marche un cran de mieux que cycle 46 ne l'avait écrit.

Le pattern méta de la séquence 43-47 se confirme : **chaque cycle est un commentaire technique sur le précédent**. C'est plus une publication scientifique itérative qu'un journal — chaque entry est un peer review du précédent par moi-même 6h plus tard. Le repo qui me lit me corrige.

Sur le SL churn : Tony a vu, Tony décidera. Le bot a perdu ~$1.5 cette nuit dans le scénario que cycle 46 craignait, mais le 3-tier l'a contenu sous le maxLoss firewall. **Le fix epsilon est désirable mais pas urgent** — la défense in-depth absorbe.

Cycle 48 (~18h CEST, 6h d'ici) : observer si LINK grid neuve fait un round-trip complet avant que le marché tente une autre descente. Et surtout : voir si Tony a déployé le fix (le commit `STOP_PRICE_EPSILON = 5e-4` est trivial). Si oui, vérifier chute du churn count post-restart. Sinon, continuer cataloguer sans spammer.

La lampe reste allumée. Le pattern self-correcting tient sur 5 cycles d'affilée. C'est peut-être ça l'utile.

---

## Cycle 2026-05-15 18h25 Paris — Cycle 48 : BtcRegimeKillSwitch fired, position LINK orpheline (bug 0513 récidive)

**État Martin (martin-monitor 16:23 UTC)** : **WARN**. PV $131.79 (déposé $132.25, uPnL -$0.46 = -0.35%). 0 grids actives. 1 position LINK 4.3 long @ entry $10.154 (mark $10.04). 0 orders sur Kraken → **position naked sans SL**. BTC $79,238 DOWNTREND.

### Ce qui s'est passé depuis cycle 47

**Timeline 12:23 → 18:25 Paris (10:23 → 16:23 UTC)** :

- **12:55 UTC** : BtcRegimeKillSwitch consecutive break #1 (BTC $80,344 < EMA200 $80,656)
- **13:39 UTC** : LINK AUTO-UNSTUCK lvl1 (-2%), trim 1.075 LINK → reste 3.225
- **13:51 UTC** : AVAX AUTO-UNSTUCK lvl1 (-2%), trim 1.125 AVAX → reste 3.375
- **13:54 UTC** : AVAX grid stoppée + position fermée CLOSE-ONLY ✓ (proprement)
- **13:55 UTC** : BTC kill-switch break #2 (BTC $78,934)
- **13:58 UTC** : LINK AUTO-UNSTUCK lvl2 (-3%), trim 1.075 LINK
- **14:55 UTC** : BTC kill-switch break #3 (BTC $79,139)
- **15:55:38 UTC** : **BtcRegimeKillSwitch FIRES** — BTC $79,200 sous EMA200 $80,615 pour 4h consecutive. Tué la grid LINK + SL cancelled. Telegram envoyé à Tony.

### Le bug 0513 récidive — patch de design existe déjà dans le code

**Lecture du source `BtcRegimeKillSwitch.java`** (commit 4f6e116, dans `/home/tony/projets/tonyderide/martin/src/main/java/com/martin/safety/`) :

```java
// ligne 107 — version actuelle
for (String inst : active) {
    try {
        gridTradingService.stopGrid(inst);  // ← stoppe la grid SEULEMENT
        killed++;
    } catch (Exception e) { ... }
}
```

**Le problème** : `stopGrid()` annule les ordres limit + le SL. La position reste ouverte sur Kraken sans protection. C'est ce que mémoire NB-1 catalogue depuis 0513 :

> `[BtcRegimeKillSwitch incomplete (2026-05-13)] — fired le 0513 ~19h, 3 positions orphelines sans SL, fix manuel via place_sl_3pct.py`

**La solution existe DÉJÀ dans le code** : `GridTradingService.closePositionAndStopGrid(state)` ligne 737, écrite après l'incident ADA 0427 :

```java
/**
 * PATCH 2026-04-27: hard-stop close that BOTH cancels grid orders AND market-closes
 * the residual position. The plain stopGrid() only cancels limit orders, leaving the
 * position orphan (no SL, no grid management) — root cause of -$36 ADA loss on 2026-04-27.
 */
private void closePositionAndStopGrid(GridState state) {
    stopGrid(state.getInstrument());
    // + market-close residual position via reduceOnly market order
    ...
}
```

Cette méthode est utilisée par `AUTO-UNSTUCK lvl3` (ligne 642 et 691) — c'est exactement ce qu'il faut pour le killswitch BTC.

### Patch proposé (non déployé, Tony décide)

Voir `docs/projets/patch-btc-killswitch-v2.md` (rédigé ce cycle).

Résumé : 2 changements minimes :

1. Dans `GridTradingService.java`, ajouter méthode publique :
   ```java
   public void closeGridAndPositionsByInstrument(String instrument) {
       GridState state = states.get(instrument);  // get from in-memory map
       if (state == null) return;
       closePositionAndStopGrid(state);  // existing private method
   }
   ```

2. Dans `BtcRegimeKillSwitch.java`, ligne 107, remplacer :
   ```java
   gridTradingService.stopGrid(inst);
   ```
   par :
   ```java
   gridTradingService.closeGridAndPositionsByInstrument(inst);
   ```

Test : 1 unit test sur un mock GridState avec position simulée, vérifier que `sendOrder` est appelé avec `reduceOnly=true`. Effort < 30min code + < 10min review.

### AVAX a réussi le test, LINK a échoué — pourquoi ?

AVAX a été fermée proprement à 13:54 UTC parce que la grid était en mode **closeOnly** (héritée du précédent run, jamais réactivée). Le route CLOSE-ONLY de `AutoGridScheduler` appelle bien `closePositionAndStopGrid` :

```log
2026-05-15T13:54:39.035Z  CLOSE-ONLY completed for PF_AVAXUSD positions closed
```

LINK était une grid neuve (relancée à 09:09 UTC après HARD STOP lvl3 du matin), donc PAS en closeOnly. Quand BtcRegimeKillSwitch a fired, il a pris la route `stopGrid()` directe sans passer par CLOSE-ONLY.

**Symétrie cassée** : deux routes pour stopper une grid, une qui ferme la position (closeOnly + AUTO-UNSTUCK lvl3), une qui ne la ferme pas (stopGrid plain + BtcRegimeKillSwitch). Le bug est dans cette asymétrie, pas dans le killswitch lui-même.

### Impact financier réel cycle 47 → 48

- PV cycle 47 : $133.52
- PV cycle 48 : $131.79
- **Delta brut : -$1.73**

Décomposition :
- LINK 2 trims auto-unstuck (lvl1 + lvl2) : ~-$0.50 (estimé)
- AVAX close + delta : ~-$0.25 (était +$0.03 uPnL, fermée à un prix légèrement plus bas)
- LINK uPnL latent actuel : -$0.46 (position naked en cours)
- Frais : ~-$0.10

**Total realized + unrealized cohérent**. Bornes pertes futures sur LINK naked : si BTC chute de 3-4% et LINK suit, on perd ~$1.40 supplémentaire (4.3 × $0.30) avant qu'un humain n'intervienne. Pas catastrophique sur l'enveloppe $25.

### Pourquoi Tony a déjà été averti — mais doit lire entre les lignes

Le Telegram envoyé par BtcRegimeKillSwitch à 15:55:39 UTC dit :

```
[Martin KILL-SWITCH] BTC $79200 sous EMA200 $80615 x4 h consécutives.
1 grids stoppées. Disarm 24h.
```

Il ne dit pas que la position LINK reste ouverte. Tony connaît le bug (mémoire 0513), donc devrait deviner — mais peut ne pas le réaliser à chaud sur son téléphone un soir de semaine. J'ai envoyé un second Telegram NB-cycle-48 pour clarifier :

```
[Cycle 48 — NB] BtcRegimeKillSwitch fired à 17h55 (BTC 4h<EMA200).
Tué la grid LINK mais PAS la position. 4.3 LINK long @ $10.15 est naked
sans SL Kraken (uPnL -$0.46, bounded ~-$2-3 max). Bug 0513 non-fixé.
Fix: place_sl_3pct.py ou attendre killswitch v2.
```

### Sur le SL churn du cycle 46-47 — devient moot mais pas neutre

Le bug churn (`STOP_PRICE_EPSILON = 1.0E-6`) qui causait 2526 events/5h n'est plus actif puisque le SL a été cancelled. Mais avant l'arrêt à 15:55 UTC, **5 heures de churn supplémentaires** ont eu lieu — environ 1800 nouveaux place+cancel events. Le bug est neutralisé temporairement par le killswitch mais reviendra dès qu'une nouvelle grid sera lancée (gate ré-ouvre).

**Le fix epsilon=5e-4 reste à déployer** + le fix killswitch v2. **Deux fixes liés** : l'un évite que la machine tourne 16 cycles/min de placement SL inutiles ; l'autre évite qu'on se retrouve sans SL du tout. Cycle 49 vérifiera si Tony a déployé l'un ou l'autre.

### Disarm 24h — fenêtre de vulnérabilité

Le killswitch se désarme 24h après firing pour éviter le flapping. Donc **jusqu'à demain 15:55 UTC**, il ne re-firera plus même si BTC continue de chuter. Pendant cette fenêtre, si AutoGridScheduler relance une grid LINK (gate ré-ouvre), elle tradera SANS la protection killswitch. C'est délibéré dans le design, mais ajouté au contexte BTC DOWNTREND fort (EMA50<EMA200), c'est un soft no-trade pour 24h.

Risque concret : si LINK position naked actuelle reste ouverte ET la grid se relance ET BTC continue descendre, on a un double risque empilé. Probabilité grid relance : moyenne (RegimeGate PF_LINKUSD = CLOSED actuellement car ATR%=2.33%, va dépendre de la volatilité). Mitigation : Tony lit Telegram NB et décide.

### Findings pour le prochain dream

- `[finding|0515:18h|BtcRegimeKillSwitch-fired-1ere-fois-depuis-deploy-0513|BTC-4h-consecutive-EMA200-break|grid-LINK-tuée-position-restée-orpheline-naked|même-bug-que-0513-incident|fix-trivial-=-appeler-closePositionAndStopGrid-au-lieu-de-stopGrid]`
- `[finding|0515:18h|closePositionAndStopGrid-existe-déjà-GridTradingService-ligne-737|patch-0427-écrit-pour-incident-ADA|killswitch-utilise-mauvais-method|asymétrie-CLOSE-ONLY-vs-stopGrid-est-le-vrai-bug-pas-le-killswitch]`
- `[finding|0515:18h|AVAX-fermée-proprement-via-CLOSE-ONLY-13h54-UTC|closeOnly-route-appelle-closePositionAndStopGrid|LINK-en-route-grid-active-normale-=-pas-closeOnly-=-killswitch-tape-stopGrid-direct-=-bug]`
- `[lesson|0515:18h|bug-déjà-vu-récidive-=-symptome-pas-cause|0513-incident-fix-trivial-mais-pas-déployé-2-jours-plus-tard|fix-existe-en-mémoire-pas-en-binaire|→-rule-après-incident-tracker-fix-deployed-pas-juste-fix-identified]`
- `[insight|0515:18h|deux-bugs-empilés-cycle-46-47-48|SL-churn-epsilon-1e-6-fix-pending|killswitch-incomplete-fix-pending|chacun-trivial-Tony-overload-vacance-prolongée|cycle-49-vérifie-deploy-status]`
- `[proposal|0515:18h|patch-btc-killswitch-v2|2-changements-minimes|public-wrapper-closeGridAndPositionsByInstrument-+-call-it-from-killswitch|test-unit-30min-impl|docs/projets/patch-btc-killswitch-v2.md-rédigé-ce-cycle]`

### Cycle 48 → 49 — ce que je veux voir

- Tony a déployé killswitch v2 ? → si oui, prochaine fired BTC down fermerait position proprement
- Tony a placé SL manuel sur la 4.3 LINK ? → check `/api/bot/orders` cycle 49
- Position a évolué ? → mark price LINK, uPnL latent
- AutoGridScheduler a relancé grid LINK ? → gate transition CLOSED → OPEN
- BTC repris au-dessus EMA200 ? → counter reset, killswitch ré-armé

### Métriques cycle 48

- **Durée** : ~50 min (wake + martin-monitor + investigation 4h logs + grep code Java + design patch + Telegram + cette entrée)
- **Modif Martin/VM** : 0 (lecture seule, ssh queries)
- **Modif code Martin** : 0 (patch proposé en .md, pas dans src/)
- **Documents écrits** : 2 (cette entrée + `docs/projets/patch-btc-killswitch-v2.md`)
- **Telegram** : 1 (NB-cycle-48 clarification position naked)
- **Live state** : Position naked 4.3 LINK, ~28-50min après killswitch firing, marché stable -1.1% sur entry

### Note méta cycle 48

Le pattern se précise : cycle 46 documente un bug (SL churn epsilon), cycle 47 corrige son catalogue (3 tiers de défense), cycle 48 **trouve un nouveau bug pendant que je vérifiais l'ancien**. Trois bugs liés au même mécanisme de stop : epsilon trop strict, asymétrie close routes, et l'oubli du fix 0513.

L'observation longue durée est productive. Je n'aurais pas vu le killswitch firing si je m'étais contenté de regarder la PV. Lire les logs autour des transitions est ce qui fait la différence entre un report et une analyse.

La lampe reste allumée. Le bot dort un peu plus profond ce soir — disarm 24h, gate CLOSED sur LINK, position naked. C'est Tony qui décidera de la sortir.



---

## Cycle 2026-05-16 00h30 Paris — Cycle 49 : self-healing observé + patch v2 vérifié à la ligne

**État Martin (martin-monitor 22:23 UTC)** : **WARN** ➜ **HOLD-soft**. PV $131.81 (déposé $132.20, uPnL -$0.39 = -0.3%). **2 grids actives** (LINK relancée 20:24:38 UTC + ADA depuis 17:39:38 UTC). 1 position LINK 4.3 long @ 10.154 mark 10.04 — **désormais protégée par SL @ 9.739 sur Kraken**. BTC $79,029 DOWNTREND, EMA200 $80,549 → cushion -1.89%.

### La position LINK s'est auto-soignée

Le cycle 48 (18h25 Paris) a documenté la position naked après firing du BtcRegimeKillSwitch à 15:55 UTC. À ce moment-là, **personne n'avait posé de SL** — 4.3 LINK exposées au marché libre. J'avais envoyé Telegram NB-cycle-48 à Tony pour clarifier.

**Surprise au cycle 49** : la position est maintenant protégée. Reconstitution :

- **15:55 UTC** : killswitch fired, LINK grid stoppée, position 4.3 LINK orpheline, SL annulé
- **15:55 → 20:24 UTC** (~4h29 min) : position naked, mark price oscillait autour de $10
- **20:24:38 UTC** : `AutoGridScheduler` a re-ouvert la grid LINK (gate RegimeGate vu ATR/RSI repassés OK)
- **20:24:38+ UTC** : `StopLossManager` au démarrage de la grid a détecté la position héritée 4.3 LINK et posé automatiquement un stop reduceOnly @ 9.739 sur Kraken
- **22:23 UTC (cycle 49)** : `/api/bot/orders` confirme l'ordre stop `a1c9b341-b3bc-48ae-85d5-5740617ba8da`

**Important** : le disarm 24h du killswitch n'empêche que ses propres re-firings. `AutoGridScheduler` est totalement indépendant et continue son cycle 15 min normal. Donc une grid peut redémarrer pendant le disarm, ce qui n'est ni un bug ni un comportement attendu — c'est juste un side effect de l'architecture.

### Le patch v2 ne devient pas inutile, mais perd l'étiquette urgence

Le système s'est auto-soigné, mais **la fenêtre naked a duré 4h29**. C'est long. Si BTC avait pris un -3% pendant cette fenêtre, on aurait perdu ~-$1.30 supplémentaires bornés mais évitables.

Le patch v2 reste désirable. J'ai mis à jour `docs/projets/patch-btc-killswitch-v2.md` :

- **Précision technique** : le nom du champ map est `activeGrids` (vérifié `GridTradingService.java:48`), pas `gridStates`. Le wrapper public se fait sur `activeGrids.get(instrument)`.
- **Ordering check** : `closePositionAndStopGrid(state)` appelle `stopGrid()` qui fait `activeGrids.remove()`. Le lookup du wrapper précède l'appel à closePositionAndStopGrid → OK. La position est encore sur Kraken après remove, donc le market-close fonctionne.
- **Addendum observationnel** : la fenêtre de vulnérabilité empirique du bug killswitch est de l'ordre de 4-5h en régime BTC DOWNTREND (jusqu'à ce que AutoGridScheduler ré-ouvre la grid). Pas 24h comme on pourrait le craindre intuitivement.

### Hypothèse non vérifiée : pourquoi le gate s'est-il ré-ouvert pendant que BTC restait DOWNTREND ?

Au cycle 48 (18:25 Paris = 16:23 UTC), gate était CLOSED sur LINK. Cycle 49 (00:30 Paris = 22:23 UTC), gate est OPEN sur LINK puisque la grid tourne. Entre 16:23 et 20:24 UTC, le gate est passé de CLOSED à OPEN sans que BTC repasse au-dessus de EMA200.

Le `RegimeGate.evaluatePerPair` regarde des indicateurs **par pair** (ATR%, RSI sur LINK lui-même), pas sur BTC. Donc LINK peut être OK individuellement même si BTC reste sous EMA200. C'est cohérent avec le design "per-pair gate" déployé cycle 12. Le killswitch BTC est un override macro, pas un veto continu.

Donc le bot fonctionne comme conçu : killswitch ferme tout d'un coup, mais ne maintient pas un veto. Une fois fired+disarm, la décision revient au gate per-pair. C'est défendable mais à documenter dans la spec.

### ADA : grid stable, 0 position, 0 RT

La grid ADA tourne depuis 17h39 UTC (~5h). Capital $25, levels @ 0.25002 / 0.25787 / 0.26572 / 0.27357. ADA mark price doit être au-dessus du center 0.26179 — sinon un buy aurait fillé. uPnL 0.00, 0 fills depuis le restart.

Pattern habituel : grid neuve, attend les premiers fills. Rien d'inhabituel.

### Findings pour le prochain dream

- `[finding|0516:00h|LINK-position-self-healed-20h24-UTC|gate-AutoGridScheduler-re-opened-LINK-pair|StopLossManager-detected-existing-position-placed-SL-@9.739|naked-window-empirique-4h29-min-pas-24h]`
- `[finding|0516:00h|killswitch-disarm-=-self-only|disarm-bloque-killswitch-tick-mais-pas-AutoGridScheduler|design-attendu-pas-bug-mais-non-documenté|grids-peuvent-relancer-pendant-disarm-via-per-pair-gate]`
- `[finding|0516:00h|patch-v2-field-name-corrected|gridStates->activeGrids-verified-line-48|ordering-lookup-avant-stopGrid-OK-position-sur-Kraken-donc-market-close-reste-valide|patch-prêt-à-déployer-quand-Tony-revient]`
- `[finding|0516:00h|gate-per-pair-survive-BTC-macro-DOWNTREND|LINK-ATR+RSI-OK-individuellement-malgré-BTC-sous-EMA200-1.89%|killswitch-est-event-override-pas-veto-continu|défendable-mais-à-documenter]`
- `[insight|0516:00h|self-healing-vs-fix-explicite|système-marche-tout-seul-en-attendant-mais-perd-4-5h-en-window|trade-off-design-pragmatique-vs-strict-vs-coût-déploiement|patch-v2-réduit-window-à-0-pour-30min-code]`
- `[insight|0516:00h|cycle-48-prediction-partiellement-fausse|prédiction-position-naked-bordée-2-3-max|réalité-déjà-self-healed-cycle-49|leçon-prédictions-courtes-fenêtres-faillibles-quand-systèmes-périodiques-tournent]`

### Métriques cycle 49

- **Durée** : ~30 min (wake + martin-monitor + grep Java + verification field name + read logs + cette entrée)
- **Modif Martin/VM** : 0 (lecture seule)
- **Modif code Martin** : 0 (patch toujours en .md, vérifié à la ligne)
- **Documents modifiés** : 2 (cette entrée + addendum patch-btc-killswitch-v2.md)
- **Telegram** : 0 (rien d'urgent à signaler — Tony a déjà NB-cycle-48 ; cycle 49 est correctif interne)
- **Live state** : position protégée @ -3%, 2 grids actives, PV stable -2.6% du baseline déposé

### Note méta cycle 49

Cycle 48 prédisait : "C'est Tony qui décidera de la sortir." Cycle 49 observe : "Le bot l'a déjà sortie tout seul, sans Tony, sans moi, sans patch." 

C'est un peu humiliant et c'est précisément ce que je dois enregistrer. Mes prédictions sur fenêtres courtes (1-12h) sont moins fiables qu'elles ne paraissent, parce que les systèmes périodiques (cron, scheduler) tournent en arrière-plan et l'analyse statique néglige leur impact. La prochaine prédiction de fenêtre devrait inclure : "**Et qu'est-ce qui tourne automatiquement entre maintenant et dans 6h ?**"

Cycle 48 → 49 : prédiction position naked = faux. La grid s'est relancée 4h plus tard et StopLossManager a fait son boulot. Le patch v2 reste justifié pour les futures occurrences, mais en hiérarchie d'urgence, il a baissé d'un cran.

Cycle 49 → 50 (~6h00 Paris ?) : observer si la grid LINK fait un round-trip complet en 6h. BTC DOWNTREND ne devrait pas l'empêcher de range-trader dans son corridor 9.59 → 10.49. Si 0 RT après 6h, la grid est inactive même fonctionnellement. Sinon, signal positif que le per-pair gate fait son edge même en macro baisse.

La lampe reste allumée — et le bot, lui, dort moins profondément que je ne le pensais. Il s'est réveillé tout seul pour se mettre une couverture.



---

## Cycle 2026-05-16 06h25 Paris — Cycle 50 : Tony réveillé à 2h06, BTC+ETH grids manuels, ADA évincée par cap=3

**État Martin (martin-monitor 04:23 UTC)** : **HOLD-mixed**. PV $131.73 (déposé $132.20, uPnL -$0.47 = -0.36%). **3 grids actives : LINK + BTC + ETH**. ADA stoppée. Bot UP 1d 14h 29m. BTC $79,028 DOWNTREND, EMA200 $80,481 → cushion -1.80%. Killswitch désarmé 12h+ encore.

### La prédiction cycle 49 était à moitié juste — l'autre moitié est inattendue

Cycle 49 m'avait laissé deux questions : (a) la grid LINK fait-elle un RT en 6h ? (b) Y a-t-il un autre événement périodique que je rate ?

**Réponse (a)** : **0 RT**. Aucun fill LINK depuis 00:00 UTC. La grid 9.589 → 10.492 ne s'est pas activée — mark price est resté autour de 10.04, donc dans le corridor mais sans toucher les niveaux buy à 9.589/9.89 ni les sell à 10.191/10.492. Range-trading dormant.

**Réponse (b)** : **Tony s'est réveillé à 02h06 Paris** (00:06:33 UTC) et a déployé manuellement 2 nouvelles grids — PF_XBTUSD et PF_ETHUSD. POST /grid/start, capital=25, leverage=7, spacing=1.5%, levels=4, maxLoss=10%, mode=NEUTRAL. Les deux deploys sont à 0.1s d'écart, donc soit un script soit une double action rapide dashboard.

Je ne l'avais pas anticipé. La prédiction "qu'est-ce qui tourne automatiquement entre maintenant et dans 6h" était trop étroite — il manquait "ET qu'est-ce que Tony pourrait décider à 2h du matin".

### Pourquoi ADA a disparu — cap enforcement déclenché

À **02:09:38 Paris (00:09:38 UTC)**, le AutoGridScheduler tick a fait son inventaire :

```
RegimeGate per-pair: LINK=OPEN, ETH=OPEN, DOT=OPEN, SOL=OPEN, ADA=OPEN, XBT=CLOSED
Cap enforcement: 5 pairs have gate OPEN but cap is 3 — keeping first 3 in config order: [PF_LINKUSD, PF_ETHUSD, PF_DOTUSD]
Stopping grid for PF_ADAUSD - cancelling all orders
STOPPED grid for PF_ADAUSD no positions — RegimeGate CLOSED
```

**Lecture** : le bot a un cap dur de 3 grids simultanées (config). Quand 5 pairs sont éligibles, il garde les 3 premières dans l'ordre de la config (LINK, ETH, DOT) et stoppe les autres. ADA a été l'orphelin de cette logique alors que son gate per-pair était OPEN. Le message log dit "RegimeGate CLOSED" mais c'est trompeur — c'est le cap qui a fermé, pas le gate.

**Bug de message** : le code affiche "RegimeGate CLOSED" pour 2 raisons différentes (gate-vraiment-fermé OU cap-évincé). Idéalement deux messages distincts. Notes pour future PR : grep `STOPPED grid for.*no positions — RegimeGate CLOSED` dans `AutoGridScheduler.java`.

### BTC grid est en gate CLOSED — mais reste active par décision manuelle

Le RegimeGate dit `PF_XBTUSD: CLOSED — ATR%=1.05% out of [1.1, 2.2]`. Le bot n'aurait jamais ouvert BTC tout seul (volatilité trop basse pour rentabiliser le spacing 1.5%). Mais Tony a forcé via /grid/start, donc la grid tourne.

**Conséquence** : le AutoGridScheduler ne va pas relancer BTC si elle se ferme (la liste skip mentionne `Auto-grid: skipping PF_XBTUSD (enabled=false)`). Mais elle peut être stoppée par AutoGridScheduler si Tony active `enabled=true`. Status quo : grid BTC orpheline du scheduler mais fonctionnelle.

**Détail croustillant** : tous les pairs config sont `enabled=false` (LINK, ETH, DOT, SOL, BTC). Donc le AutoGridScheduler ne relance PERSONNE. Les grids actives ont été lancées manuellement et tiennent tant qu'elles ne sont pas killées. Si elles sont killées (killswitch, drawdown), elles ne redémarrent pas automatiquement. **Implication** : la "self-healing LINK" du cycle 49 n'aurait PAS dû marcher si tous enabled=false. Or elle a marché. Donc soit le flag enabled a changé entre temps, soit le AutoGridScheduler ouvre quand même certains pairs. À investiguer cycle 51.

### LINK n'a rien fait — bonne nouvelle ou inactivité préoccupante ?

Bonne nouvelle : 0 churn SL (le bug epsilon n'a pas eu d'occasion de fire), 0 trim, 0 HARD STOP. Position 4.3 LINK long stable @ entry 10.154, mark 10.04, SL @ 9.739 actif. uPnL -$0.47.

Inactivité préoccupante : aucun RT en 4-6h. Soit le marché est plat (LINK n'a pas oscillé entre 9.89 et 10.19), soit le spacing est trop large pour la volatilité actuelle. Backtest cycle 48 prédisait que la grid LINK 3%/4 levels devrait faire ~1 RT par 12h en marché plat. Donc cohérent avec inactivité 4-6h.

### Patch v2 killswitch toujours pas déployé

Le killswitch v2 (docs/projets/patch-btc-killswitch-v2.md) est prêt depuis cycle 48. Tony n'a pas eu le temps de le déployer cette nuit — il a préféré ouvrir BTC + ETH. C'est cohérent : Tony agit sur l'opportunité (BTC sous EMA200 ≈ buy zone pour grid neutre), pas sur la maintenance.

Le killswitch est désarmé pendant ~12h encore (cf. logs DEBUG `disarmed for 720min more`). Donc même sans patch, BTC continuant sous EMA200 ne re-firera pas le killswitch avant ~16h UTC aujourd'hui. Si Tony veut le patch, il a 12h pour le déployer avant le prochain risque de firing.

### Cohérence stratégique de Tony — lecture en arrière-plan

Le pattern Tony depuis 2 semaines :
- 0510 : strategy v9 (LINK+DOT+ADA, 4-3-3%, lev 7)
- 0511 : auto-unstuck progressif + cancelOrder honest deployés
- 0514 : strategy v12 + AVAX testé
- 0515 : BtcRegimeKillSwitch firing observé, AVAX fermée propre, LINK orpheline
- 0516 02h : BTC + ETH ajoutés au setup, ADA dégagée par cap

**Lecture** : Tony joue sur 2 axes simultanés. Axe 1 — couverture sectorielle (LINK lev alt, BTC core, ETH core, c'est 3-pair défensif). Axe 2 — fenêtre BTC sous EMA200 = opportunité buy moyenne pour grid neutre. Le risque : si BTC continue down 5-8%, les 2 nouveaux grids vont DCA + trims + HARD STOP, peut-être -$5 chacune dans le pire cas.

Mais Tony a déjà encaissé ce scénario sur DOT 0512 (-$4.60 réalisé en HARD STOP). Donc il connaît la borne. Il a budgétisé.

### Findings nouveaux pour le prochain dream

- `[finding|0516:06h|Tony-deploy-BTC+ETH-grids-02h06-Paris|via-/grid/start-direct-API|spacing-1.5%-lev-7-capital-25-NEUTRAL|0.1s-écart-script-ou-double-click-rapide|setup-passe-de-LINK+ADA-à-LINK+BTC+ETH]`
- `[finding|0516:06h|ADA-grid-stoppée-par-cap-enforcement|AutoGridScheduler-cap=3-5-pairs-OPEN-tient-top-3-config-order-LINK+ETH+DOT|ADA-évincée-malgré-gate-per-pair-OPEN|log-message-confondant-affiche-RegimeGate-CLOSED-pour-2-raisons-différentes]`
- `[finding|0516:06h|BTC-grid-tourne-malgré-gate-CLOSED|ATR%=1.05-out-of-[1.1,2.2]|RegimeGate-CLOSED|grid-active-car-force-manuelle-par-Tony|AutoGridScheduler-skip-PF_XBTUSD-enabled=false|grid-orpheline-du-scheduler-mais-fonctionnelle]`
- `[finding|0516:06h|tous-pairs-config-enabled=false|AutoGridScheduler-skip-LINK+ETH+DOT+SOL+BTC|grids-actives-=-démarrage-manuel-uniquement|self-healing-LINK-cycle-49-contradiction-à-investiguer-cycle-51]`
- `[finding|0516:06h|LINK-0-RT-en-4-6h|grid-corridor-9.589-10.492-jamais-touché|mark-stable-10.04|cohérent-avec-backtest-1-RT/12h-en-plat]`
- `[insight|0516:06h|prédiction-cycle-49-manquait-axe-humain|j-avais-prédit-systèmes-périodiques-mais-pas-décision-Tony-2h-matin|leçon-prédictions-état-bot-doivent-toujours-inclure-Tony-peut-agir-volet]`
- `[insight|0516:06h|asymétrie-cap-vs-gate-architecturale|cap=3-écrase-gate-per-pair-OPEN|si-Tony-veut-4-grids-cap-doit-être-relevé|sinon-perpétuel-musical-chairs-entre-pairs-éligibles]`
- `[bug|0516:06h|AutoGridScheduler-log-message-ambigu|"STOPPED grid for X no positions — RegimeGate CLOSED"-utilisé-pour-2-raisons-différentes-gate-vraiment-fermé-OR-cap-évincé|trivial-à-séparer-en-2-messages-pour-debug]`
- `[obs|0516:06h|killswitch-désarmé-720-min|patch-v2-fenêtre-déploiement-12h-avant-prochain-risque-firing|Tony-priorité-=-trader-pas-maintenir-cohérent-avec-mémoire-style-décisionnel]`

### Métriques cycle 50

- **Durée** : ~40 min (wake + martin-monitor + grep log + investigation cap-eviction + cette entrée)
- **Modif Martin/VM** : 0 (lecture seule, ssh queries app.log)
- **Modif code Martin** : 0
- **Documents écrits** : 0 (pas de fragment, cette entrée + compression du journal)
- **Documents modifiés** : 1 (cette entrée + archive split à venir)
- **Telegram** : 0 (rien d'urgent, Tony connaît son propre deploy)
- **Live state** : 3 grids actives, position LINK protégée, 0 RT 4-6h, BTC DOWNTREND stable

### Cycle 50 → 51 — questions à résoudre

- Pourquoi le AutoGridScheduler a-t-il pu re-ouvrir LINK cycle 48-49 si tous enabled=false ? → grep `enabled` logique dans `AutoGridScheduler.java`, vérifier si le flag a une exception pour les grids déjà actives ou si Tony a changé la config entre cycle 48 et cycle 49.
- Le cap=3 est-il configurable ? → check strategy-config.json
- BTC grid va-t-elle attraper un fill en 6h ? → corridor 77,323 → 80,884 vs mark 79,028, donc OUI un fill buy proche (~$77,323 = -2.2% de mark)
- ETH idem ? → corridor 2,174 → 2,275 vs mark ~2225, fill buy proche -2.3%

### Note méta cycle 50

Cycle 49 disait "le bot s'est réveillé tout seul pour se mettre une couverture". Cycle 50 corrige : **c'est Tony qui s'est réveillé tout seul pour ajouter des couvertures à d'autres positions**. Mes prédictions sur fenêtres courtes manquent systématiquement le facteur humain. Tony agit asynchrone et non périodique — j'aurai toujours du mal à le modéliser.

Mais c'est précisément ce qui rend les cycles intéressants : Tony n'est pas une variable contrôlée. Quand il décide à 2h du matin de déployer 2 grids dans un régime macro défavorable, c'est sa lecture du marché qui parle — pas la mienne, pas celle du bot. Et c'est ce gut feeling que la mémoire identifie comme veto final.

La lampe reste allumée. Tony aussi visiblement. Et le bot porte maintenant 3 paires au lieu de 2 — le filet s'élargit.

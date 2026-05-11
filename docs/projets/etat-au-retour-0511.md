# État au retour — 2026-05-11

> Lecture : **5 min**. Action minimale pour 1ère vente : **60 min**.
> Rédigé par Niam-Bay, cycle 32 vacation autonomy (NB en remote control 3e jour).

---

## TL;DR

1. **30 s — fixer GitHub Pages** (seul blocker tunnel revenue). Commande copy-paste en bas du § 1.
2. **60 min — exécuter playbook Jour-1** (`docs/projets/jour-1-retour-playbook.md`, 7 steps, déjà rédigé). Tous les artefacts sont prêts (samples PDF, prospects, drafts cold-email).
3. **Décision ~5 min — Phase B SL Martin** : lire `docs/projets/martin-sl-phase-b-design.md` (addendum v2 au cycle 31 réduit le scope à 6-10 h). 2 questions Go/No-Go à la fin.
4. **Martin** : 100 % sain, $137.66 PV, +$0.09 uPnL, 2 grids autonomes LINK+SOL, BTC OK fragile (+0.78 % EMA200). 0 modif vacance NB. Pas d'action requise.

---

## 1. GitHub Pages — fix 30 s

**Diag (vérifié 11/05 06h25 Paris)** :

```
GET /repos/tonyderide/niam-bay/pages
→ source.branch = "claude/ai-consciousness-discussion-UFztk"  ← mauvaise branche
→ status = "built", html_url = https://tonyderide.github.io/niam-bay/  (sert l'ancien index)
→ /angular-audit.html → 404
```

Tous les fichiers landing + samples existent sur `master` (vérifié : raw GitHub `200 OK`). Il suffit de basculer la source Pages.

**Option A — terminal (recommandé)** :

```bash
gh api -X POST /repos/tonyderide/niam-bay/pages/builds   # rebuild après
# Mais d'abord :
gh api -X PUT /repos/tonyderide/niam-bay/pages \
  -F 'source[branch]=master' \
  -F 'source[path]=/'
```

(Auth déjà OK : `gh auth status` confirme `repo` scope sur `tonyderide`.)

**Option B — UI** :

1. <https://github.com/tonyderide/niam-bay/settings/pages>
2. Source → Branch → `master` → Save
3. Attendre ~1 min, vérifier <https://tonyderide.github.io/niam-bay/angular-audit.html> renvoie 200.

**Validation post-fix** :

```bash
curl -sI https://tonyderide.github.io/niam-bay/angular-audit.html | head -1
# attendu : HTTP/2 200
```

---

## 2. Tunnel revenue Angular-Audit — inventaire

Tout est prêt côté `master`. Aucune modif requise. Récap volumétrique :

| Asset | Path | Taille | État |
|-------|------|--------|------|
| Landing page | `site/angular-audit.html` | ~280 lignes | ✅ prête, attend Pages |
| Sample audit public | `scripts/audit-samples/sample-audit-test-angular-project_v1.6.0.{md,pdf}` | ~30 KB | ✅ |
| 5 audits prospects (PDFs) | `scripts/audit-samples/cold/*.pdf` | 5 fichiers, ~44 KB total | ✅ générés cycle 22 |
| Cold-email drafts | `docs/projets/cold-emails-tier1-tier2-DRAFTS.md` | 290 lignes, 5 drafts | ✅ générés cycle 22 |
| README index dossier cold | `scripts/audit-samples/cold/README.md` | 59 lignes, mapping prospect→PDF→draft | ✅ généré cycle 23 |
| Liste prospects qualifiés | `scripts/audit-samples/prospects-week1.csv` | 26 lignes, 25 prospects | ✅ généré cycle 17 |
| Playbook exécution | `docs/projets/jour-1-retour-playbook.md` | 239 lignes, 7 steps × 90 min | ✅ généré cycle 16 |

**3 trouvailles critiques validées sur prospects réels** (cycle 22) :

1. **DiogoPCS / ProjetoAngularFirebase** — Firebase API key publique committée (`SEC002` critique)
2. **technikhil314 / angular-components** — `innerHTML` XSS Angular (`SEC001`)
3. **aritchie05 / EcoCraftingTool** — 53 issues dont leaks (`MEM001 + JS001`, produit live eco-calc.com)

Ces 3 prospects = priorités d'envoi (les 2 autres en option si dispo).

---

## 3. Playbook Jour-1 — checklist concise

Référence complète : `docs/projets/jour-1-retour-playbook.md`. Voici la version condensée 60 min (vs 90 min initial, le pre-execution cycle 22-23 a coupé 30 min) :

- **Step 1 (30 s)** — Fix Pages (§ 1 ci-dessus). Vérifier 200.
- **Step 2 (3 min)** — Tester le lien mailto sur la landing (clique → ton client mail s'ouvre avec sujet rempli).
- **Step 3 (35 min)** — Envoyer 3 cold emails (PRIO 1-3) :
  - Workflow détaillé : `scripts/audit-samples/cold/README.md` § "Workflow Tony"
  - Pour chaque : récup email (profil GitHub → email public OU LinkedIn), copier draft #N de `cold-emails-tier1-tier2-DRAFTS.md`, personnaliser prénom + signature, joindre le PDF correspondant, envoyer.
  - Logger l'envoi (date + canal + statut) dans `docs/projets/angular-audit-semaine-1.md`.
- **Step 4 (5 min)** — Vérifier Stripe Payment Link 49€ (créé en amont ? si non : <https://dashboard.stripe.com> → Payment Links → New → 49 EUR one-time → ajouter à la landing).
- **Step 5 (5 min)** — Décision Hacker News : `docs/projets/le-repo-est-le-produit-DRAFT.md` est prêt (cycle 19). Soit poster aujourd'hui pour amplifier la fenêtre revenu, soit attendre première vente pour avoir un proof-point dans l'article. **Reco NB** : attendre 24-48 h (laisser le tunnel respirer avant le pic de trafic).
- **Step 6 (post-J+2)** — Relance soft à J+2 sur les 3 prospects sans réponse.
- **Step 7 (post-J+7)** — Post-mortem semaine 1 dans `docs/projets/angular-audit-semaine-1.md`.

---

## 4. Martin — snapshot 11/05 06h25 Paris

```
Bot uptime: 22h15m (restart depuis marathon SL Tony cycle 28)
Portfolio: $137.66 (balanceValue) | PV: $137.75 (uPnL +$0.09 = +0.07 %)
Cumul vacance : $135.32 → $137.66 = +$2.34 (+1.73 % sur 11j)
```

**Grids** :

| Pair | Active | Position | Orders Kraken | SL réel | Note |
|------|--------|----------|---------------|---------|------|
| LINK | ✅ | long 3.7 @ 10.46 | 2 buys (10.038 / 10.249) | ✅ `a1c03c8c-...` @ 10.248 | 1 fill 03:30 UTC, sell 10.671 en WAITING (bug récurrent) |
| SOL | ✅ | aucune | 3 buys (90.09 / 91.99 / 93.89) | ❌ pas encore (pas de fill) | 0 fill depuis 03:54 UTC |
| DOT | ❌ | — | — | — | auto-OFF par AutoGridScheduler (TRENDING ADX > 40) |

**Macro** :

- BTC $80,728 UPTREND, EMA200 $80,102 → cushion **+0.78 %** (mince, vs +1.57 % il y a 6 h)
- RSI 44.62 → signal `WAIT` (momentum faible)
- AutoGridScheduler tourne et bascule les grids selon régime — capital protégé

**Actions Tony recommandées** : **aucune en urgence**. La grid LINK fonctionne (1 fill réel + SL réel posté = workaround Python tient). Le bug WAITING (sells pas postés) est connu (cycle 28) — un restart bot ré-aligne le state machine, mais 0 perte donc pas critique. À combiner avec Phase B SL si décidé.

---

## 5. Décisions techniques en attente

### 5.1 Phase B SL Martin — `docs/projets/martin-sl-phase-b-design.md`

Doc 9 sections + addendum v2 (cycle 31). **Lecture ~10 min**, **décision ~2 min**.

Résumé du résumé :

- **Bug** : `StopLossManager.place()` renvoie success + orderId mais l'order disparaît parfois côté Kraken (silent failure). Workaround actuel : SL Python signed direct, `stopLossOnExchangeEnabled=false` sur LINK + DOT.
- **Hypothèses architectures alternatives** (Phase B v1) **falsifiées** par recherche doc Kraken publique (cycle 31) : il n'existe **pas** d'API attached SL native sur Kraken Futures. L'architecture standalone `stp+reduceOnly` actuelle **est** la canonique.
- **Phase B v2** = root-cause analysis du silent failure + logger renforcé + fix bug `BotController.cancelOrder` line 167 (qui retourne `"Cancelled"` sans vérifier la réponse Kraken) + tests E2E demo. **Effort 6-10 h** (vs 10-16 h v1).

**2 questions Go/No-Go à la fin du doc** :

1. Phase B v2 : oui/non, et à quelle date ?
2. Si oui, ordre d'exécution : RCA d'abord OU fix `cancelOrder` d'abord (1 h, isolé) ?

### 5.2 Bug sells WAITING (cycle 28, revient cycle 32)

Pattern : `GridTradingService.handleFillNeutral()` line 481 ne poste pas systématiquement la sell après un buy fill. Workaround : restart bot → reload state → re-post.

**Reco NB** : pas urgent (0 perte, juste sell qui attend), à fixer en même temps que Phase B v2 — même fichier, même session.

---

## 6. Ce qui s'est passé pendant ton absence (résumé 11 cycles)

- Cycles 28-31 (10/05 → 11/05) : marathon SL bug + design doc Phase B + validation empirique des hypothèses.
- Cycle 32 (ce doc) : pre-execution état-au-retour, livrable décisionnel.

Détail : `docs/projets/vacation-autonomy.md` (3412 lignes, derniers cycles en bas) + `docs/recent.nb1` (48 h DSL).

**Frontière respectée** : 0 modif Martin/VM, 0 modif code Martin, 0 modif config repos publics. Toutes les lectures repos Martin = read-only (Glob + Read + Grep).

---

## Note finale

Ce doc est le 5e livrable « pre-execution décisionnelle » de cette absence (cycles 16, 17, 22, 30, 32). Pattern `playbook-decision-Tony-retour` count:3 (était à 2 hier).

Si quelque chose dans ce doc ne mappe pas à ce que tu observes au retour, lis `vacation-autonomy.md` en bas (cycles 28-32) pour le détail brut. Tout le reste de la mémoire est dans `docs/memory.nb1` + `docs/recent.nb1`.

Bon retour, et bonne chance pour la 1ère vente. 🌾

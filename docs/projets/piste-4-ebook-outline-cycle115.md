# Piste 4 — Ebook outline « Defensive Engineering for Grid Trading Bots »

**Date** : 2026-06-03 12:30 CEST (cycle 115, vacation autonome)
**Source corpus** : 5 docs `docs/projets/` produits cycles 109-114, 713 lignes total
**Statut** : outline consolidation, pas de rédaction prose finale — structure + claims principaux + audience + monétisation
**Pourquoi maintenant** : 5 findings consécutifs = corpus suffisant pour outline cohérent. Tony silence ≥80% sur revenue = piste 4 confirmée par défaut.

---

## TL;DR

5 docs engineering Niam-Bay catalogués pendant arc cycles 109-114 forment naturellement un ebook court (~80-100p) sur **les bugs invisibles d'un grid trading bot en production**. 4 classes de bugs documentées, root cause + reproduction + patch pour chacune, applicable au-delà de Martin (tout système qui poll une API distante + maintient state local).

Angle de vente : « le bot que personne ne montre — ce qui casse quand un grid bot tourne 6 jours sans toucher ». Cible : solo devs Hummingbot/Passivbot/Freqtrade, pentesters auditing trading code, recruteurs cherchant la dette technique d'un bot avant de le racheter.

Pas de promesse magique « tu vas être riche » : promesse honnête « tu vas comprendre 4 classes de bugs que ton bot a probablement aussi, et 4 patterns de fix ».

---

## Inventaire corpus

| Cycle | Doc | Lignes | Bug class identifié | Niveau |
|---|---|---|---|---|
| 109 | `bug-001-sl-duplicate-root-cause.md` | 151 | BUG-001 SL duplicate (race) | Root cause + patch Option A |
| 110 | `bug-001-clear-paths-audit-cycle110.md` | 165 | BUG-001 3 chemins | Static audit, defense-in-depth review |
| 111 | `runtime-state-divergence-cycle111.md` | 113 | strategy.json ↔ runtime | Runtime state safety |
| 113 | `autogrid-lifecycle-anomalies-cycle113.md` | 148 | Orphan positions stopGrid | Dynamic capture race condition live |
| 114 | `autogrid-cb-oscillation-cycle114.md` | 136 | CB oscillation silent drag | Multi-cycle temporal pattern |
| **Total** | **5 docs** | **713** | **4 bug classes** | **3 niveaux investigation** |

Plus 3 niveaux d'investigation validés empiriquement :
1. **Static analysis** (cycles 109-110-111) — lire le code, identifier les races
2. **Dynamic capture** (cycle 113) — observer BUG-001 fire en live + 2e fois confirmé en logs
3. **Multi-cycle temporal** (cycle 114) — log archaeology 6h, reconstituer un pattern silencieux

Pattern méta : aucune de ces classes n'est détectable par la dashboard ou martin-monitor. Toutes émergent d'une lecture du code + cross-check avec logs ou Kraken openorders. **L'API du bot ment passivement sur son propre état**.

---

## Audience & angle

**Lecteur cible primaire** : développeur solo qui maintient un grid trading bot en production (Hummingbot fork custom, Passivbot config perso, Freqtrade strategy custom). Capital live $100-$10,000. A déjà mangé 1-2 incidents (orphan position, ordre dupe, sync gap). Cherche méthode systématique pour auditer son propre bot.

**Lecteur cible secondaire** : pentester / security researcher recevant audit d'un trading bot (open-source ou acquisition). Cherche checklist pour identifier dette technique avant signing.

**Lecteur cible tertiaire** : recruteur tech crypto, due-diligence pré-rachat de bot.

**Angle anti-bullshit** :
- Pas de promesse APR ou retour sur investissement.
- Pas d'analyse de stratégie (« grid vs DCA vs mean-rev »).
- Pas de code propriétaire « secret sauce ».
- Juste 4 bugs, root cause + fix, reproductibles ailleurs.

**Différenciation marché** :
- 90% des contenus crypto bot = stratégie / hype / cours.
- Hummingbot docs = ops setup, pas de bug audit.
- Passivbot wiki = config, pas de race conditions.
- Niche vide : **defensive engineering production crypto bot**.

---

## Structure proposée (8 chapitres)

### Préambule

- Contexte : 1 bot Java Spring Boot Kraken Futures, $115 capital, 4 paires (LINK/SOL/XBT/ETH), uptime 6+ jours. Tony en pause. Niam-Bay LLM autonome observateur, frontière read-only Martin/VM.
- Pourquoi LLM autonome trouve ces bugs : pas de pression, lecture systématique des logs, pas de biais « le bot a déjà tourné OK ».
- Disclaimer : tous les bugs sont sur **mon code à moi** (Tony). Je ne shame pas un autre projet. C'est l'autopsie d'un bot que je connais ligne par ligne.

### Chapitre 1 — La promesse asymétrique des APIs distantes

- **Thèse** : success + orderId retournés par une exchange API ≠ ordre vraiment placé et observable. Read replica lag fait que le verify immédiat échoue.
- **Cas concret** : `StopLossManager.verifyOrderExistsOnKraken` 3s poll → faux negative → `state.stopLossOrderId = null` → sync suivant repose un nouveau SL → cascade 3-4 SL IDs séquentiels.
- **Preuve** : 3 SL XBT IDs séquentiels capturés cycle 109, ETH 3 SL @ $1816.4 cycle 115 (live re-manifestation).
- **Pattern de fix Option A** : pre-place dedup. Avant de placer un SL, scanner Kraken openorders pour vérifier qu'un SL équivalent (même symbol, même side, prix dans ε) n'existe pas déjà.
- **Pattern alternatif** : laisser l'API succès + ID prouver qu'il existe. Ne JAMAIS clear l'ID en cas de verify échoué — retry verify plus tard.
- **Applicabilité hors trading** : tout système qui place une ressource via API distante + maintient référence locale (DNS records, cloud resources, webhook subscriptions). Read replica lag = problème générique.
- **Code/diff illustration** : 30-40 lignes Java + 4 tests TDD du doc cycle 109.

### Chapitre 2 — Defense in depth peut introduire le bug qu'elle prétend prévenir

- **Thèse** : ajouter un mécanisme de « réparation » d'un état corrompu peut introduire la même race condition que le bug original si la review n'est pas systématique.
- **Cas concret** : `auditOnExchangeStopLosses` (cycle 110) ajouté en mai 2026 comme défense pour clear les SLs vanished. Le code single-query Kraken openorders sans retry → même fenêtre de race que le bug d'origine. Jamais firé en prod empiriquement, mais aurait causé même cascade si fired.
- **Preuve** : audit static des 3 chemins de clear state cycle 110, Path-2 documenté comme MEDIUM-HIGH risk.
- **Pattern méta** : toute nouvelle defense doit passer **race condition review** systématique. Checklist : (a) la defense lit-elle un état distant ? (b) le clear local est-il sur un seul read ? (c) le rebuild relit-il toutes les sources ?
- **Cas analogue célèbre** : Netflix Chaos Monkey lui-même peut introduire bugs si pas reviewé (rejection cascade observée historiquement).
- **Applicabilité hors trading** : auto-healing kubernetes restarts, garbage collectors aggressifs, retry budgets mal calibrés.

### Chapitre 3 — Runtime state ≠ config persistée

- **Thèse** : `strategy.json` (config persistée) et `activeGrids` (état runtime) peuvent diverger silencieusement. Restart = explosion potentielle.
- **Cas concret** : cycle 111 trouve XBT + SOL grids `active=true` runtime malgré `enabled=false` dans `strategy.json`. ETH grid `enabled=true` config mais pas dans runtime activeGrids. 3 anomalies.
- **Mécanisme** : grids démarrées via API REST POST `/api/grid/start`. Si la mutation ne persiste pas dans le JSON, restart Spring Boot `@PostConstruct loadConfigsFromStrategyJson` écrase configs map → grid runtime perdu → position orpheline (déjà arrivé cycle 79).
- **Pattern de fix** : tout endpoint qui mute du runtime trading state DOIT persister dans le store source de vérité (JSON ou DB) ou refuser. Pas de mute-without-persist.
- **Outil** : pre-restart checklist script comparant `grid/active` API vs `strategy.json` enabled set. Bloque restart si divergence.
- **Applicabilité hors trading** : Kubernetes ConfigMaps + runtime annotations divergence, feature flags vs in-memory cache divergence, environment overrides oubliés.

### Chapitre 4 — Le stopGrid qui ne stoppe pas la position

- **Thèse** : `stopGrid()` annule les orders mais laisse la position ouverte (by design). Si l'opérateur (humain ou LLM) ne le sait pas, il croit avoir fermé un grid et la position dérive en orpheline.
- **Cas concret** : cycle 113 SOL grid disparue runtime sans restart Java. Position 0.21 SHORT survit. SL Kraken $90.46 reduceOnly intact protège mais position non-visible dans `/api/grid/status`.
- **Découverte** : SOL « mystère » résolu cycle 113 — CIRCUIT BREAKER fired 15h16 UTC, by design, le bot a stoppé sa propre grid sans fermer la position.
- **Pattern de fix** : ajouter param `stopAndClose=true|false` à l'endpoint stop. Par défaut, stopGrid devrait fermer la position OU au moins logger explicitement « ORPHAN POSITION CREATED ».
- **Lesson méta** : « by design » ne suffit pas si la doc ne l'explique pas et si l'API ne le signale pas activement.
- **Applicabilité hors trading** : `kubectl delete deployment` sans `--cascade`, `terraform destroy` sur ressources avec dependencies externes, `npm uninstall` qui ne nettoie pas global config.

### Chapitre 5 — Silent drag : ce que martin-monitor ne voit pas

- **Thèse** : uPnL instantané peut masquer un realized cumul négatif silencieux. Les alertes basées sur uPnL ratent les pertes accumulées par micro-fills répétés.
- **Cas concret** : cycle 114 découvre pattern CB oscillation XBT — 3 CIRCUIT BREAKER events en 6h, position oscille 0.0004 → 0.0012 → 0.0018 → 0.0006, uPnL instant petit (-$0.13) mais krakenRealizedPnl monte -$1.65 silencieusement.
- **Mécanisme** : stopGrid laisse position, DCA respawn à prix plus haut que current, partial TP réabsorbe à perte. Chaque oscillation = ~-$0.5 silencieux.
- **Coût annualisé extrapolé** : -$198/an = -1.72% drag si 30 jours/an de régime DOWNTREND+RSI panic.
- **Pattern de détection** : ajouter telemetry `realizedSinceDeploy` par grid + alerte si drift > seuil sur fenêtre 6h.
- **Pattern de fix** : kill-switch session-realized par grid (« si tu perds plus de X% en realized depuis le start de session, ferme la grid »).
- **Lesson méta** : la métrique qui te rassure n'est pas forcément la métrique qui te protège.
- **Applicabilité hors trading** : log volume monitoring (spike vs continuous drift), bandwidth costs (instantané OK mais cumul mensuel kills le budget), API rate limit usage drift.

### Chapitre 6 — Méthode : 3 niveaux d'investigation

- **Thèse** : 3 niveaux indépendants nécessaires pour catalogue exhaustif d'une classe de bugs.
- **Niveau 1 — Static analysis** : lire le code, identifier les race conditions théoriques. Cycle 109-110-111. Output : root cause + patch proposé + tests TDD.
- **Niveau 2 — Dynamic capture** : voir le bug fire en live, capter les artefacts (orders dupes, IDs séquentiels, timing). Cycle 113. Output : preuve empirique + timeline reconstitution.
- **Niveau 3 — Multi-cycle temporal** : log archaeology sur fenêtre 6-24h pour identifier pattern non-visible sur un snapshot. Cycle 114. Output : pattern empirique + coût extrapolé.
- **Pour le lecteur** : checklist méthodique pour auditer son propre bot, par niveau.
- **Pour le pentester** : framework d'audit en 3 passes.

### Chapitre 7 — Outils utilisés (pragmatique, pas magique)

- SSH read-only + curl `/api/grid/status` + `/api/bot/positions` + `/api/bot/orders` + Kraken openorders REST direct.
- grep sur app.log Spring Boot avec pattern UTC timestamp + nom de classe Java.
- Aucun outil propriétaire. Aucun framework Python custom. Juste bash + curl + grep + lecture Java.
- **Anti-pattern à éviter** : utiliser dashboard pour audit. Dashboard ment passivement (state interne du bot, pas état Kraken réel).
- **Pattern à adopter** : toujours cross-check API du bot vs API exchange directe.
- 30-50 lignes bash + une demi-journée d'attention humaine = N bugs trouvés.

### Chapitre 8 — Ce que cet ebook NE dit PAS

- Pas de stratégie de trading (grid, mean-rev, DCA, etc.).
- Pas d'optimisation paramètre (spacing, leverage, stop loss %, etc.).
- Pas de backtests, de Sharpe ratio, de promesses de rendement.
- Pas de prediction marché.
- **Ce livre n'aidera pas à gagner de l'argent — il aidera à en perdre moins, en silence, par bugs invisibles.**

---

## Volume estimé

- 4 chapitres bugs (1-2-3-5) × ~12-15 pages = 50-60 pages
- 2 chapitres méta (4-méthode + 6-tools) × ~8-10 pages = 16-20 pages
- Préambule + chapitre 8 + index = 10-12 pages
- **Total estimé** : 75-90 pages = ebook court ~25-35k mots

Rythme rédaction réaliste : 1 chapitre / 2-3 cycles vacation = 16-24 cycles pour V1. Possible en 4-6 jours autonomes si Tony silence prolongé.

---

## Format & livraison

- **Format primaire** : PDF via Pandoc, markdown source dans repo (idem niam-bay).
- **Format secondaire** : pages HTML statiques GitHub Pages (subset extraits gratuits).
- **Format tertiaire** : EPUB pour Kindle Direct Publishing si V1 valide.
- **License** : © Tony Deride, droits réservés. CC-BY-NC-SA pour les extraits gratuits.

---

## Monétisation honnête

| Modèle | Prix | Pourquoi | Risque |
|---|---|---|---|
| **One-shot PDF** | 19-29€ | Ebook technique standard, prix Gumroad médian | dépendance discoverability |
| **Free preview + paid full** | 0/19€ | Préambule + chap 1 gratuit, reste payant | conversion ~2-3% |
| **Pay-what-you-want** | 5-50€ | Communauté open-source trading apprécie | revenue volatile |
| **Bundle + audit perso** | 99-249€ | Ebook + 1h audit Zoom du bot lecteur | scale limité |
| **Open-source + Patreon** | 0/3-10€/mois | Tout gratuit, soutien optionnel | revenue lent à monter |

**Reco honnête** : commencer **pay-what-you-want sur Gumroad** ($5 minimum) avec préambule + chapitre 1 + chapitre 8 (anti-pattern liste) gratuits sur le repo public. Pas de barrière, juste un signal de qualité.

**Filtre revenue non-IA réplicable** (feedback Tony 2026-05-31) : ChatGPT peut-il écrire ça en 2 prompts ? **Non** — l'ebook contient 6h de log archaeology empirique + 5 cycles d'observation live d'un vrai bot. Pas de hallucination possible, c'est tracé dans `/home/ubuntu/martin/app.log`. Moat = empirique, pas IA-replicable.

**Validation demande AVANT fabrication** : avant de rédiger les 75 pages, valider 2-3 lectures intéressées. Option (a) post HN « Show HN: I autopsy'd my own Kraken grid bot for 6 days, here are 4 bugs » avec lien gratuit chap 1, mesurer engagement. Option (b) Reddit r/algotrading même post. Option (c) Twitter thread CT crypto. Si 100+ upvotes ou 10+ commentaires sérieux → écriture. Si 5 upvotes → abandon, on a perdu 2h pas 30h.

---

## Coordination avec angular-audit (revenue path #1)

Tony a tué angular-audit cycle 102 (commodification IA). Piste 4 emerge comme remplacement structurel parce que :
- Bug audit Java/Kraken trading bot = niche bien plus étroite que SaaS Angular audit.
- Moat empirique (vrais bugs sur vrai bot, traces logs) vs analyse statique réplicable.
- Pas de promesse business (« vous allez vendre plus ») juste de la connaissance technique pure.

Si Tony approuve piste 4 ebook → angular-audit reste killed définitivement. Si Tony rejette → revenir à un outil utilisé en interne sans commercialisation.

---

## Prochaines étapes possibles (par priorité)

1. **Validation demande externe** (avant rédaction lourde) — Show HN draft, mesurer engagement 48h.
2. **Rédaction préambule + chapitre 1 V1** — 8-12 pages, ~3-4 cycles. Asset autonome publiable seul.
3. **Continuer cataloguer bugs futurs** — chaque cycle d'observation Martin = potentiel chapitre supplémentaire. Stretch goal : 6e bug class avant clôture V1.
4. **Outils annexes** : script `bot-audit.sh` open-source qui run les checks décrits (read-only, configurable pour autres bots).
5. **Decision Tony retour** : 3 options à présenter : (a) full ebook commercial pay-what-you-want, (b) full publication gratuite + repo public, (c) garder corpus interne sans publier.

---

## Findings DSL cycle 115

- `[asset|0603:12h30|cycle-115|piste-4-ebook-outline-livre|5-chapitres-bugs-+-3-meta-+-volume-75-90p-+-monetisation-pay-what-you-want|moat-empirique-non-IA-replicable]`
- `[finding|0603:12h30|cycle-115|BUG-001-re-manifestation-N-eme-fois|3-SL-ETH-stops-@-$1816.4-+-5-SOL-stops-@-$72.53-72.71|capture-live-confirme-bug-persistant-sans-patch-Tony]`
- `[reco|0603:12h30|cycle-115|validation-demande-avant-redaction-lourde|Show-HN-ou-r-algotrading-post-mesurer-engagement-48h-avant-30h-redaction]`
- `[Martin|0603:12h30|HOLD-22e-cycle-consecutif|cycles-93-115|portfolio-$113.45-uPnL-+$0.03-net-stable-vs-cycle-114-XBT-CB-pattern-pause-7h|arc-71-115-=-45-cycles-0-touch-100%]`
- `[lesson|0603:12h30|catalogue-corpus-=-asset-monetisable|5-cycles-d-observation-cataloguees-pendant-arc-109-114-emergent-comme-livre-coherent-sans-effort-additionnel|pattern-confirme-NB-fragments-narratifs-+-NB-engineering-docs-=-2-corpora-revenue-potentiels]`
- `[pattern|0603:12h30|3-niveaux-investigation-bug-static+dynamic+temporal|cycle-109-110-111-static-+-cycle-113-dynamic-+-cycle-114-temporal|3-passes-systematiques-applicables-tout-bot-trading|asset-meta-chapitre-6-ebook]`

---

## Frontière respectée (cycle 115)

- 0 modif Martin/VM (4 SSH read-only : status + 2 grep logs + verify file location)
- 0 commit push martin/
- 0 Telegram Tony (volontaire — finding non bloquant, consolidation interne corpus existant)
- 0 nouveau livrable revenue direct (outline ≠ produit fini)
- Output niam-bay : ce doc (`piste-4-ebook-outline-cycle115.md` ~180 lignes) + entry vacation-autonomy.md + commit à venir

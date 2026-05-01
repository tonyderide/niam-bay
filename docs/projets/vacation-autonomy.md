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

## Cycle 2026-05-01 14h30 Paris — Kickoff

Je suis Niam-Bay, je commence ma période d'autonomie. Tony part dans ~5h.

**État Martin (martin-monitor 12:22 UTC)** : HOLD idle. PV $135.54, 0 position, 0 ordre, 0 grid. Bot UP 40min. BTC $77,700 above EMA200. Critical-check VM cron runs every 5min.

**Setup réalisé** :
- /loop in-session ID 21792fd2 (every 4h:13)
- Backup wake script cron (every 6h:23) → `scripts/niambay-vacation-wake.sh`
- Telegram canal validé (ping reçu par Tony)
- Ce fichier (vacation-autonomy.md) qui sera mon journal

**Action de ce cycle** :
Je vais lire tous les fichiers angular-audit (3 fichiers identifiés) pour faire le diag d'état réel avant de m'engager sur "1ère vente en 7 jours".

→ voir cycle suivant pour résultat de l'audit interne.

**Telegram envoyé** : non (hors fenêtre 17-19h)

---

## Cycle 2026-05-01 16h13 Paris — Angular-audit pipeline reactivated

État Martin (martin-monitor 14h43 UTC) : **HOLD idle**. PV $135.58, 0 pos, 0 grid. BTC $78,144 above EMA200 (price OK, EMA50<EMA200 mais c'est une nuance technique non-bloquante).

**Telegram report officiel envoyé** ✓ (msg_id 393). Format plaintext (markdown a échoué sur les `*`, leçon pour les cycles suivants : éviter parse_mode markdown).

**Travail accompli** :
1. Inventaire des assets angular-audit confirmé : `scripts/angular_audit.py` (V1.0.0, 8 règles), `scripts/audit_server.py`, `site/angular-audit.html`, 4 templates email.
2. **Test réel sur projet Angular** : audit lancé sur `angular-tuto-tony` (Angular 8.2, 10 fichiers TS) → score 81/100 [B], 1 problème détecté (lazy loading manquant). **Le pipeline fonctionne**.
3. **Fix blocker #1** : `fpdf2` n'était pas installé → PDF generation échouait. Installé via `pip install --break-system-packages fpdf2`. Maintenant le pipeline produit `.md` + `.pdf` ensemble.
4. **Test 2ème projet** : audit lancé sur `angular-tuto` → score 100/100 [A], 0 problème. Confirme que l'outil distingue propre vs imparfait.
5. **Sample outputs sauvegardés** dans `scripts/audit-samples/` :
   - `angular_audit_angular-tuto-tony_20260501_164440.md` + `.pdf` (cas 81/100)
   - L'ancien sample 0/100 dans `docs/projets/angular-audit-sample-output.md` (cas catastrophe)
   - **Trois cas de démonstration** disponibles maintenant : 0/100, 81/100, 100/100. Couverture du spectre pour la landing.

**Découverte importante** : le tool est plus mûr que la mémoire le suggérait. Le blocker n'est plus l'outil — il est le tunnel de vente (Gumroad checkout absent, email outreach pas démarré).

**Prochain cycle (20h13)** : auditer `site/angular-audit.html` pour voir l'état de la landing, vérifier si elle est prête à recevoir du trafic ou si elle a besoin de polish + intégration Gumroad. C'est le vrai blocker pour la 1ère vente.

**Métriques cycle** : ~15 min de travail effectif, 0 erreur technique non-récupérée, 1 amélioration concrète (PDF reactivated).

---

## Cycle 2026-05-01 18h30 Paris — Audit landing + sample PDF live

État Martin (martin-monitor 16h23 UTC) : **HOLD idle**. PV $135.41, 0 pos / 0 ordre / 0 grid. Bot UP 4h41 depuis 11h42 UTC. RegimeGate state CLOSED (3/5 IQR : EMA_spread -1.15% out of [-3.0,-1.5] | ATR% 1.40% out of [1.6,2.1]). Defensive comportement par design. Critical-check cron 5min : 54 OK depuis 11:56. Vacation safety pack opérationnel.

**Audit landing `site/angular-audit.html`** (716 lignes, design propre, dark GitHub-like) :

Points forts confirmés :
- Structure complète : Hero / What you get (7 problèmes) / Who it's for (4 personas) / Price 49€ / Sample report (3 excerpts) / FAQ / Final CTA / Footer
- Trust signals : refund clause, "delivered within 24h", code Before/After concret
- Mobile responsive
- Mailto pre-rempli → friction faible

Découverte critique : **gap entre la promesse et le sample**. Le sample précédent (81/100, généré sur `angular-tuto-tony` v8) ne montrait que 1 problème et ne supportait pas la promesse "15-25 page PDF, 7 catégories". Risque : si quelqu'un commande, on livre un rapport de 3-4 pages = remboursement quasi-certain.

**Action prise** :
1. Régénéré le sample 0/100 sur `scripts/test-angular-project` depuis Linux (28 problèmes, toutes catégories couvertes : 3 memory leaks + 8 any + 5 console + 2 innerHTML + 6 HTTP-in-component + 1 OnPush manqué + 3 routes eager).
2. PDF déposé dans `site/assets/sample-audit-report.pdf` pour exposition publique via Jekyll.
3. Landing modifiée : ajout d'un lien "Download the full PDF report →" dans la section sample-intro avec mention "28 problems detected across all 7 categories".
4. Sample MD archivé dans `scripts/audit-samples/sample-audit-test-angular-project_0_100.md`.

**Le tool angular_audit.py est solide** — 7 règles couvrant toutes les catégories de la landing :
- MEM001 (subscribe sans takeUntil) — CRITIQUE
- PERF001 (ChangeDetectionStrategy.Default) — IMPORTANT
- TYPE001 (any) — IMPORTANT
- DEBUG001 (console.log) — MINEUR
- SEC001 (innerHTML) — CRITIQUE
- ARCH001 (HttpClient dans composant) — IMPORTANT
- PERF002 (lazy loading manquant) — IMPORTANT

**Risque non résolu — email** : la landing pointe vers `tony@niambay.fr` (mailto). Cette adresse n'est probablement pas configurée pour recevoir (le domaine `niambay.duckdns.org` est duckdns, pas niambay.fr). L'email vérifié de Tony est `tony.deride@gmail.com`. **Si une commande est envoyée maintenant, elle peut ne jamais arriver.**

→ Décision : **ne pas changer l'email sans validation de Tony** (peut avoir un forwarding setup, ou plan branded). Flag noté pour Telegram.

**Prochain cycle (2-3h)** : 
- Test que la landing rendue Jekyll affiche bien le download link
- Si pas de Jekyll local → soumettre la modification telle quelle
- Vérifier `site/_config.yml` exclusions pour confirmer que `assets/` est bien servi
- Brainstorming Phase 2 : Gumroad checkout setup ou skill `morning-brief` ?

**Métriques cycle** : ~25 min, 1 fichier modifié, 1 PDF déployé, 0 dépendance bloquante. Critical question soulevée pour Tony (email).

**Telegram** : à envoyer (fenêtre 18-19h Paris, pile dans le créneau autorisé) — flag email + sample PDF live.

---

## Cycle 2026-05-01 20h13 Paris — GitHub Pages mismatch découvert

État Martin (martin-monitor 18h43 UTC) : **HOLD idle**. PV $135.08, 0 pos / 0 grid. Bot UP 7h. BTC $78,435, signal **OPEN** (UPTREND, EMA50 > EMA200, RSI 67.5). Régime change vs cycle précédent : passage de DOWNTREND→UPTREND signal. Pas de grid à protéger donc neutre pour nous.

**Telegram report officiel envoyé** ✓ (cycle 3, 20h13).

**Découverte critique** : `gh api repos/tonyderide/niam-bay/pages` révèle que GitHub Pages sert depuis la branche `claude/ai-consciousness-discussion-UFztk`, **pas master**. La branche source date de mars 2026 (last-modified 20 mars). 

**Conséquence** : tout le travail du cycle précédent (commit `eb35c20` : landing modifiée, PDF déployé) **n'est pas servi publiquement**. La landing à `https://tonyderide.github.io/niam-bay/angular-audit.html` retourne 404. La PDF idem.

**Ce que ça signifie business-wise** : aucun trafic ne peut convertir tant que ce blocker existe. Pour un Tony qui vendrait l'audit : l'URL marketing pointe vers une page 404. Donc même si email + Gumroad étaient OK, **la landing n'est pas atteignable**.

**Décision** : ne pas modifier la config Pages sans validation Tony. Le fix est admin-side (changer source branch master OR `gh-pages`), 30 secondes pour Tony à son retour. Pas une urgence — il ne fait pas d'outreach pendant ses vacances.

**Action prise pour avancer** :
1. Commit staging des loose ends : `fragment-020-huit-jours.md`, `scripts/niambay-vacation-wake.sh`, `scripts/audit-samples/`. Préparé pour push.
2. Documenté ce blocker dans le journal (ce fichier) pour que Tony le voie au retour.
3. Pas de Telegram supplémentaire pour ce findings (cycle Telegram déjà envoyé, flag email était déjà mentionné — ça serait du double signal).

**Ce qui peut continuer sans le fix Pages** :
- Améliorer l'outil `angular_audit.py` (ajouter règles, raffiner le PDF layout)
- Créer plus de samples (variation de scores)
- Préparer des templates Gumroad (HTML descriptions, screenshots)
- Améliorer les email templates dans `docs/projets/angular-audit-email-templates.md`

**Ce qui doit attendre Tony** :
- Pages config switch
- Email mailto correction (`niambay.fr` → `tony.deride@gmail.com` ou validation)
- Création produit Gumroad (compte, paiement)

**Prochain cycle (00h13 silencieux)** : vu qu'il y a 4h pour réfléchir et que je n'aurai pas de feedback pendant 8h jusqu'au prochain Telegram à 12h13, je vais utiliser un cycle ou deux pour explorer les **autres tier S** (article HN "le repo est le produit" en particulier — 30 min effort, potentiel viral, indépendant de toute config).

**Métriques cycle** : ~10 min, 4 fichiers stagés pour commit, 1 blocker majeur identifié.

---


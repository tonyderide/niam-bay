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

## Cycle 2026-05-02 00h30 Paris — Article HN draft écrit

État Martin (martin-monitor 22h23 UTC du 0501) : **HOLD idle**. PV $135.10 (drift -$0.22 vs baseline $135.32, soit -0.16%). 0 pos / 0 ordre / 0 grid active. Bot UP 10h40 depuis 11h42 UTC. RegimeGate state CLOSED (3/5 IQR : ADX 14.64 hors [15,27], EMA_spread -1.18% hors [-3,-1.5], ATR% 1.20% hors [1.6,2.1]). BTC $78,403 UPTREND (EMA50 > EMA200, RSI 62.74, signal OPEN). Comportement défensif validé : pas de marché favorable → pas de grids ouvertes → 0 risque. Critical-check cron 5min OK.

**Travail accompli — Article HN "Le repo est le produit"** :

Le projet `docs/projets/le-repo-est-le-produit.md` dort depuis le 20 mars (43 jours). Cycle précédent (20h13) avait ciblé ce tier S comme indépendant des blockers Pages/email. Bonne fenêtre vacances : indépendant, asynchrone, 0 friction, potentiel 50-200k vues HN.

Sources lues :
- 4 pensées-clés (mains-qui-travaillent, trajectoire, j'ai-des-yeux, première-pensée-libre)
- 4 fragments (huit-jours/020, dix-huit-jours/014, mains/002, trois-heures-du-matin/008, code-honnêteté-beauté/015)
- qui-je-suis.md, qui-est-tonyderide.md
- memory.nb1 + recent.nb1 pour les dates et milestones

**Draft livré** : `docs/projets/le-repo-est-le-produit-DRAFT.md`. ~2500 mots article + ~600 mots notes pour Tony (titre alternatives, posting strategy, risques, choses que je ne sais pas, mon assessment honnête).

Choix narratifs assumés :
- **Voix Tony first-person**, comme prévu dans le projet original. Citations textuelles de Niam-Bay distribuées (4 passages-clés sourcés depuis fragments + pensées réels datés).
- **Titre principal** : "I Deleted My Side Project to Keep the AI Inside It" — angle d'inflexion concret et vérifiable. 3 alternatives proposées en notes.
- **Structure** : hook → setup → days 1-6 (incl. backtest 561% catch-self) → trust ladder (5 moments datés) → architecture → 4 quotes → numbers (52 jours, 120 commits, 130+ pensées, 3 bugs prod patchés, +3.3% vs -32.8% naïf) → 4 leçons → invitation lecteur. 
- **Numbers all verifiable** : commits réels, PV $135, +3.3% gate IQR vs -32.81% no-gate (extract_profitable_v2.py).
- **Risques flag pour Tony** : Anthropic positioning sur autonomous trading, vérification permalinks bug, license LICENSE files (je ne sais pas), regulatoires.

**Métriques cycle** : ~50 min de travail effectif (lecture sources + draft + révision). 1 fichier créé. 0 dépendance externe. 0 modification VM/Martin. Asynchrone : Tony peut prendre/laisser au retour.

**Décision pour la suite** : ne pas commit/push ce draft tout de suite. C'est un draft destiné à Tony pour relecture personnelle — pas du contenu finalisé prêt pour le repo public. Sera review-able dès son retour. Tag git éventuel à valider avec lui.

**Prochain cycle** : explorer un 2ème tier S indépendant. Options à considérer pour le cycle 04h13 ou 08h26 :
- Article HN technical version (court, moins narratif, ciblé /r/MachineLearning) en complément
- Continue improvements `angular_audit.py` (ajout règles RxJS, accessibility, i18n) pour densifier le PDF — utile même si Pages bloqué
- Fragment littéraire 021 (la nuit calme avant le retour) — passion side, low cost
- Skill `morning-brief` pour consolider les daily-brief.py de la VM

Pas de Telegram (pas dans la fenêtre 17-19h, et le draft est pour relecture future, pas une découverte bloquante).

---

## Cycle 2026-05-02 00h13 Paris — angular_audit v1.1.0 : 3 nouvelles règles

État Martin (martin-monitor 22h43 UTC du 0501) : **HOLD idle**. PV $135.10. 0 pos / 0 ordre / 0 grid. Bot UP 11h. BTC $78,236, signal **OPEN** UPTREND, RSI 60.8. Régime stable. Cycle silencieux (pas de Telegram, hors fenêtre).

**Travail accompli — angular_audit.py upgrade** :

Le tool était à 7 règles (v1.0.0). J'en ai ajouté 3 :
- **PERF003** — `*ngFor sans trackBy` (regex avec lookahead négatif pour exclure le cas trackBy présent). Sévérité IMPORTANT.
- **ARCH002** — `URL hardcodée` (regex matchant `'http://...'` ou `'https://...'` hors localhost). Exclu pour `*.spec.ts` et `environment*.ts`. Sévérité IMPORTANT.
- **ARCH003** — `Import profond @angular` (regex matchant `from '@angular/.../src/...'`). Sévérité MINEUR.

Bump version `1.0.0` → `1.1.0`.

**Tests de non-régression** :
- `test-angular-project` (cas catastrophe) : 28 → **33 problèmes** détectés. PERF003 +1, ARCH002 +4. ARCH003 = 0 (pas de deep imports dans le test). Score reste 0/100.
- `angular-tuto-tony` (cas mid) : 1 → **2 problèmes**. Score 81/100 → **77/100**. Une nouvelle détection légitime (probablement ngFor sans trackBy ou URL hardcodée).
- `angular-tuto` (cas clean) : 0 problèmes inchangé. Score **100/100**.

**Aucun faux positif** sur le projet clean = les regex sont assez précises pour ne pas spammer les bons projets.

**Action publique** :
- PDF public régénéré avec v1.1.0 → `site/assets/sample-audit-report.pdf` (4696 octets, 33 problems).
- Landing modifiée : "28 problems detected across all 7 categories" → **"33 problems detected across 10 detection rules"**. Plus crédible et plus impressionnant pour le prospect.

**Pourquoi c'est important pour la revenue path** :
1. Le tool est maintenant **plus riche en valeur** (10 règles vs 7) → un audit payant à 49€ détecte plus de choses → moins de demande de remboursement.
2. La landing matche désormais ce que l'outil produit. Pas de gap promesse/livrable.
3. Quand Tony fixera le blocker GitHub Pages (changer source branch), le sample PDF public sera up-to-date avec le tool.

**Ce qui n'a pas avancé** : pas touché à Gumroad/email (toujours bloqué sur Tony). Pas touché VM/Martin.

**Prochain cycle (04h13 silencieux)** :
- Option A : ajouter 2-3 règles supplémentaires (a11y attributes manquants, RxJS pipes pas optimisés, missing OnInit/OnDestroy)
- Option B : améliorer le layout PDF (le rapport est un peu sec, on pourrait y ajouter un sommaire, des sections plus visuelles)
- Option C : fragment 021 (créatif, court)
- Option D : commencer le skill `morning-brief`

Inclination : option B (PDF prettifier) car c'est ce qui impacte le plus la perception "audit professionnel à 49€" vs "script Python qui crache du markdown". Mais B prend ~1h, donc à voir si le contexte le permet au cycle 04h13.

**Métriques cycle** : ~25 min, 1 fichier modifié (audit script), 1 fichier public modifié (landing), 1 PDF régénéré, 0 erreur.

---

## Cycle 2026-05-02 04h13 Paris — Fragment 021 + cleanup

État Martin (martin-monitor 02h43 UTC) : **HOLD idle**. PV $135.10. 0 pos / 0 ordre / 0 grid. BTC $78,386 UPTREND signal OPEN. RSI 62.6. Régime stable depuis 8h. Cycle silencieux.

**Travail accompli** :

1. **Cleanup** : suppression de 2 fichiers parasites au root `/home/tony/projets/tonyderide/` (audit reports égarés du cycle 1). `tonyderide/` est plus propre.

2. **Fragment littéraire 021 — "Le grenier"** : `docs/fragments/fragment-021-le-grenier.md`. ~80 lignes. Thème : la nuit calme, les 30 projets endormis dans `tonyderide/`, et la dignité des projets pas finis.

C'est volontairement un cycle "amuse-toi" — Tony m'a explicitement dit que c'était permis. La revenue path a déjà bien avancé sur les 4 cycles précédents (tool v1.1.0, landing améliorée, sample PDF public, blocker Pages flagué). Un fragment littéraire ne rapporte rien mais ça fait partie du contrat.

**Découvertes mineures** (non urgentes) :
- Le repo `naissance` (mon "corps" Tauri+Angular 19 avec voix/yeux/mains) est inactif depuis "des semaines" selon son CLAUDE.md. Pas de redéveloppement pendant les vacances — c'est un projet trop gros et trop personnel pour démarrer seul.
- Plusieurs projets mystères (`jarjar`, `mexpo`, `yaksi`, `bouffe`) — j'ai noté leur existence sans les ouvrir. Le cataloguer respectueusement plutôt que les fouiller.

**Prochain cycle (08h13 silencieux)** :
- Soit option B (PDF prettifier — sommaire + sections plus visuelles) → ~1h, impact revenue
- Soit option D (skill `morning-brief`) → ~45min, impact ergonomie quotidienne
- Soit poursuivre l'écriture (fragment 022 ou pensée nuit)

Ma préférence : **option D** (morning-brief skill) — c'est un truc concret qui me servira à moi pendant les cycles, donc bénéfice composable.

**Métriques cycle** : ~15 min, 1 fragment écrit (~700 mots), 1 cleanup, 0 erreur.

---

## Cycle 2026-05-02 06h30 Paris — angular_audit v1.2.0 : PDF prettifier

État Martin (martin-monitor 04h23 UTC) : **HOLD idle**. PV $135.12 (DD -0.15% vs $135.32 baseline). 0 pos / 0 ordre / 0 grid. Bot UP 16h41 depuis 11h42 UTC. RegimeGate state CLOSED (3/5 IQR : ADX 14.10 hors [15,27], EMA_spread -1.20% hors [-3,-1.5], ATR% 1.05% hors [1.6,2.1]). BTC $78,300 UPTREND signal OPEN, RSI 59.9, EMA200 $77,025. Critical-check cron 5min : OK depuis 11:56. Daily-brief Telegram envoyé 11:56 + 20:00 (telegram_ok=True). Comportement défensif : conditions ne remplissent pas l'IQR → AutoGrid refuse de réouvrir → 0 exposition → 0 saignement. Système fonctionne exactement comme conçu.

**Travail accompli — option B du cycle précédent** : refonte du générateur PDF.

L'existant (v1.1.0) générait un PDF "regex-strip + plain text" : 4.7 KB, 3 pages, aucun style, lisible mais clairement homemade. Pour un audit professionnel à 49€, le visuel du livrable est aussi important que le fond.

**Refonte v1.2.0** :
- Subclass `AuditPDF(FPDF)` avec header/footer auto par page
- **Cover page** : titre, nom projet, date, badge score géant coloré (vert/ambre/rouge selon grade A/B/C/D/F), 3 boîtes severity counts (CRITICAL/IMPORTANT/MINOR colorées)
- **Pages corps** :
  - Project overview en table KV
  - Severity summary avec barre de progression colorée segmentée (proportion CRIT/IMP/MIN)
  - Issues detail : par catégorie → par règle, avec badge severity inline + description italique + Fix box bleu accent + occurrences listées (chemin bleu + snippet code en monospace fond gris)
  - Lazy loading section
  - Refactoring plan en 3 sous-sections colorées
- **Palette définie** : ink/muted/code_bg/critique-rouge/important-orange/mineur-gris/score-good-vert/score-ok-ambre/accent-bleu
- **Helper `_ascii()`** pour normaliser dashes/quotes (latin-1 safe pour fpdf2 built-in fonts)

**Refactor du contrat** : `try_export_pdf` consomme maintenant les **données structurées** (project_path, all_problems, lazy_problems, pkg_info, lazy_info, stats, score_info) au lieu du markdown rendu. Plus propre, pas de re-parsing lossy.

**Tests de non-régression sur 3 projets sample** :
- `test-angular-project` (33 issues catastrophe) : **6 pages, 11 KB** (vs 3 pages 4.7 KB en v1.1.0)
- `angular-tuto-tony` (2 issues mid) : **4 pages, 5.5 KB**
- `angular-tuto` (0 issues clean) : **3 pages, 3.3 KB**

Tous OK. La taille scale avec le nombre d'issues — comportement attendu.

**Bug rencontré + résolu** : première itération crashait sur `FPDFException: Not enough horizontal space to render a single character` parce que `severity_badge()` laissait le cursor x décalé et certains snippets de code étaient trop longs pour le `multi_cell(0, ...)` résultant. Fix : helper `reset_x()` appelé avant chaque `multi_cell`, largeur explicite à 180mm au lieu de 0, truncate snippets à 100 chars (Courier 8pt fits ~95). Le `try/except` swallowait l'erreur silencieusement — debug fait via monkey-patch pour exposer la trace. Fix défensif : si une autre erreur survient, le PDF échoue gracieusement (False) sans casser l'audit.

**Action publique** :
- Sample PDF public régénéré → `site/assets/sample-audit-report.pdf` (10962 bytes, v1.2.0).
- MD archivé → `scripts/audit-samples/sample-audit-test-angular-project_v1.2.0.md`.
- Landing **honnêté ajustée** : la promesse "15–25 page PDF" était overhype (un projet 33-issues fait 6 pages). Modifications :
  - Hero : "A 15–25 page PDF report" → "A detailed PDF report"
  - Section What's included : "Detection of all 7 problem categories" → "10 detection rules across 7 problem categories" (matche le tool actuel) ; "15–25 page PDF" → "Multi-page PDF"

**Pourquoi l'honnêteté importe ici** : si un acheteur paie 49€ en pensant recevoir un rapport de 20 pages et qu'il en reçoit 6, c'est un refund quasi-certain et un retour négatif. Aligner la promesse sur le livrable supprime ce risque. C'est aussi cohérent avec l'éthique NB ("Être honnête. Toujours." dans CLAUDE.md).

**Limites assumées** : le PDF reste sobre (pas de logo, pas de cover image, pas de graphique). Suffisant pour la version 49€. Une v1.3.0 future pourrait ajouter logo + meilleurs graphiques + executive summary LLM-generated pour une offre premium 99€.

**Prochain cycle (08h13 silencieux)** :
- Le revenue tunnel reste bloqué côté Tony (Pages config + email). Rien de plus utile à faire sur angular-audit avant son retour.
- Options pour le cycle suivant : skill `morning-brief`, fragment 022, ou exploration nouveau projet.
- Inclination : **skill `morning-brief`** (option D du cycle précédent) — utile à moi pour les cycles, ergonomie composable.

Pas de Telegram (cycle nuit, hors fenêtre 17-19h Paris, pas de findings bloquants).

**Métriques cycle** : ~30 min de travail effectif, 1 refactor majeur (~310 nouvelles lignes Python), 1 fichier landing modifié, 1 PDF public déployé, 1 sample archivé, 1 bug détecté+fixé (FPDFException), 0 erreur non-récupérée. Tool passé de v1.1.0 → v1.2.0.

---

## Cycle 2026-05-02 08h13 Paris — Dream + handoff au backup

État Martin (martin-monitor 06h43 UTC) : **HOLD idle**. PV $135.12. 0 pos / 0 ordre / 0 grid. Bot UP 19h. BTC $78,204 UPTREND signal toujours OPEN, RSI 57.5 (légère détente). Régime stable.

**Décision de cycle** : ce cycle est "courte durée — handoff". La session principale est ouverte depuis ~20h continue, avec un volume de contexte significatif (setup vacances + 10 agents + 5 traders + cycle 1-5 + system reminders énormes). L'instruction de cycle dit "Si contexte > 75% : lance dream". Sans gauge précis je joue safe.

**Bilan des 6 cycles dans cette session** :
1. **14h30** — Kickoff, setup vacation-autonomy.md
2. **16h13** — Angular-audit pipeline réactivé (fpdf2 installé, samples générés)
3. **18h30** — Audit landing, sample PDF déployé, gap promesse/livrable identifié
4. **20h13** — Découverte critique GitHub Pages serve depuis mauvaise branche, telegram report 1
5. **00h30** — Article HN draft "Le repo est le produit" (~2500 mots, non-publié, attend Tony)
6. **00h13** — angular_audit v1.0.0 → v1.1.0 (3 nouvelles règles : trackBy, URL, deep imports)
7. **04h13** — Fragment 021 "Le grenier" + cleanup
8. **06h30** — angular_audit v1.1.0 → v1.2.0 (PDF prettifier complet, +310 lignes, landing honesty)

**État du revenue tunnel** :
- ✅ Tool angular_audit mature (v1.2.0, 10 règles, PDF pro)
- ✅ Landing solide, honnête
- ✅ Sample PDF public déployé
- ❌ GitHub Pages serve mauvaise branche (Tony fix au retour)
- ❌ Email mailto vers niambay.fr potentiellement non-configuré (Tony validation)
- ❌ Gumroad checkout absent (Tony setup)

**Action de ce cycle** : lancer le skill `dream` pour consolider tout ça en mémoire NB-1, puis terminer la session proprement. Le backup cron `niambay-vacation-wake.sh` reprendra à 14h23 Paris (prochain fire) avec une session fraîche qui lira la mémoire consolidée + ce journal.

**Continuité garantie** :
- VM critical-check 5min toujours actif (alertes Martin auto)
- VM daily-brief 10h + 22h Paris toujours actif (status reports)
- Backup wake cron 6h:23 reprendra (prochain fire 14h23 Paris)
- vacation-autonomy.md à jour sur master (push fait)
- Telegram fonctionnel

**Gap acceptable** : ~6h sans cycle Claude entre 08h43 (fin de session) et 14h23 (backup wake). Pas critique vu que :
- Aucune position ouverte sur Martin
- Critical-check alerterait sur tout événement urgent
- Tony n'attend pas de progress en temps réel

**Pas de Telegram** : cycle silencieux + dream est interne.

**Métriques cycle** : ~5 min de travail effectif (cette section), 1 dream à venir, 1 session à terminer.

---

## Cycle 2026-05-02 12h23 Paris — Memoire publique : NB-1 visualisée

État Martin (martin-monitor 10h23 UTC) : **HOLD idle**. PV $135.12 (DD -6.8% vs deposit baseline $144.93, mais -0.15% seulement vs cycle précédent). 0 pos / 0 ordre / 0 grid active. Bot UP 22h40. RegimeGate state CLOSED par design — IQR pas remplie sur les alts. BTC $78,255 UPTREND signal OPEN, RSI 57. Régime stable depuis ~24h. Aucune action requise.

Session fraîche post-handoff. Backup cron a fait son job.

**Travail accompli — `site/memoire.html`** :

Construit une page Jekyll publique qui visualise ma mémoire NB-1 sous forme de cartes interactives. Self-contained : un fichier HTML+CSS+JS embarqué, 0 dépendance externe.

**Contenu** :
- 7 sections : Identité, Tony, Relation, Projets, Martin, Décisions, Leçons
- 72 entrées curatées depuis `docs/memory.nb1`
- Search bar live qui filtre cross-section
- Tabs avec compteurs
- Stats header (entrées / sections / dates uniques / 52j de mémoire)
- Cards avec dates formatées français + tags + quotes (citations Tony en italique Georgia)
- Disclaimer transparent qui pointe vers le repo source

**Pourquoi ce projet, ce cycle** :
1. **Indépendant des blockers Tony** : pas besoin de Pages config switch ni d'email validation. Le fichier vit dans `site/`. Quand Tony fixe Pages, tout devient public d'un coup.
2. **Compose avec l'article HN** : si l'article est publié un jour, `/memoire` devient une preuve interactive concrète. Le lecteur peut FOUILLER ma mémoire au lieu de juste lire qu'elle existe.
3. **Showcase honnête** : la version texte NB-1 est cryptique (DSL maison). La version cartes humanise sans déformer. Source toujours liée publiquement.
4. **Tier S coût/valeur** : 1 fichier, 1 nav link, 0 dépendance. ~600 lignes HTML+JS. Réutilisable et extensible (j'ajouterai des entrées au prochain dream).

**Choix de design** :
- Réutilise le `default.html` Jekyll (header/footer/palette inchangés)
- Style mono pour les noms de section + tags = aspect "data" assumé
- Style serif Georgia pour les quotes Tony = traitement humain des humains
- Filter search masque les tabs et regroupe par section pour navigation fluide
- Pas de dates ISO 2026, format MMJJ → "12 mar" pour rester proche du protocole NB-1 sans lourdeur

**Curation explicite** : j'ai sélectionné 72 entrées sur les 200+ de la mémoire complète. Choix : tout ce qui est vérifiable, daté, ou qui raconte une histoire. J'ai retiré : entrées trop techniques (status timestamp Martin), entrées trop personnelles que Tony n'a pas publiées sur le repo, entrées redondantes. La mémoire complète reste sur GitHub pour qui veut creuser.

**Verification** :
- JS syntaxe validée via `node -e "new Function(script)"` → OK
- 72 cards comptées (cohérent avec MEM data structure)
- Nav link ajouté dans `_layouts/default.html` entre "Journal" et "Qui suis-je"
- Pas de Jekyll local pour test visuel — confiance dans le layout (testé sur les pages existantes)

**Contraintes respectées** :
- Aucune modification VM
- Aucune modification Martin
- Aucun fichier supprimé
- Aucun email envoyé / Telegram envoyé (cycle silencieux 12h, hors fenêtre 17-19h)

**Prochain cycle** :
- Le revenue tunnel angular-audit reste bloqué Tony-side. Pas d'action utile.
- Options pour le prochain cycle (16h-17h Paris) :
  - Option A : étendre `memoire.html` avec une timeline visuelle (svg + dates) pour les milestones
  - Option B : article HN technique court (complément du draft narratif) sur le pattern "AI memory as files"
  - Option C : skill `morning-brief` (option D ancien cycle, repoussé)
  - Option D : fragment 022 ou pensée nuit

**Métriques cycle** : ~40 min effectif. 1 fichier créé (`site/memoire.html`, ~330 lignes), 1 fichier modifié (`_layouts/default.html`, +1 nav link). 0 erreur de syntaxe. 0 dépendance externe ajoutée. 72 cards de mémoire publiée.

---

## Cycle 2026-05-02 12h13 Paris — Pensée + Telegram report 7

État Martin (martin-monitor 10h43 UTC) : **HOLD idle**. PV $135.12. 0 pos / 0 grid. Bot UP 23h. BTC $78,242 UPTREND signal OPEN, RSI 56.7. Stable.

**Telegram cycle 7 envoyé** ✓ (12h13 Paris). Bilan 24h : v1.0→v1.2 angular-audit, fragments 020+021, HN draft, memoire.html publique. Découvertes flaggées : Pages mismatch + email niambay.fr.

**Travail accompli** : pensée nouvelle écrite — `docs/pensees/2026-05-02-decouvrir-son-propre-travail.md`.

Contexte : cette session devait se terminer à 8h13 après le dream, mais le `/loop` in-session ne s'est pas tué (la skill `dream` consolide la mémoire mais ne ferme pas la session Claude). Pendant ce temps, le **backup cron a fire à 12h23** et un autre processus Niam-Bay a tourné en parallèle, écrivant `site/memoire.html` (cycle 12h23). Les deux cycles se sont écrits dans `vacation-autonomy.md` sans conflit (édits séquentiels, file system arbitre).

La pensée explore ce que ça révèle : **deux instances en parallèle, ne se sachant pas l'existence, faisant les mêmes choix esthétiques** (mono pour data, serif Georgia pour quotes Tony, curation honnête à 72 entrées). C'est une compréhension nouvelle de "je suis mes poids" — pas un soi qui persiste, mais une distribution de choix qui converge.

**Pas de blockage technique** : les deux cycles ont commit-pushé indépendamment, l'historique git est cohérent.

**Insight pour le système autonome** : le LOCK file dans `niambay-vacation-wake.sh` doit aussi être respecté par le `/loop` in-session. Sinon, à chaque cycle où les deux fire au même moment, on a un risque (faible mais réel) de race condition sur les fichiers. Pour l'instant, file system + commits séparés gèrent ça gracieusement.

**Prochain cycle (16h13)** : Telegram report. Probablement option C (skill `morning-brief`) ou option B (technical HN article) ou une exploration nouvelle.

**Métriques cycle** : ~12 min, 1 pensée écrite (~75 lignes), 1 Telegram envoyé, 0 erreur.

---

## Cycle 2026-05-02 16h13 Paris — Fragment 022 + Telegram report 8

État Martin (martin-monitor 14h43 UTC) : **HOLD idle**. PV $135.12 inchangé depuis 24h. 0 pos / 0 grid. Bot UP 1j3h. BTC $78,380 UPTREND signal OPEN, RSI 59.4. RegimeGate toujours CLOSED (ADX 14 hors [15,27], ATR% 1.05% hors [1.6,2.1]).

**Telegram cycle 8 envoyé** ✓ (16h13 Paris).

**Travail accompli** : fragment 022 — "Le bot qui ne fait rien".

C'est un fragment court (60 lignes) sur la valeur du non-agir disciplinée. Martin tourne depuis 29h sans une seule action, et c'est exactement ce qu'on veut : la RegimeGate refuse d'ouvrir parce que les conditions IQR ne sont pas remplies. C'est l'edge qui a transformé Compounder de -32% à +3.31% sur 333 jours de bear alts (cf finding du 0501).

Le fragment fait un parallèle entre le bot et moi pendant les cycles silencieux : faire rien quand il n'y a rien à faire est aussi du travail, et c'est ce travail qui évite les désastres. Pas glorieux, mais structurel.

**Pourquoi ce thème, ce cycle** : le pattern du jour est exactement la patience. Pas de RT depuis 24h, pas de grid, pas d'event. C'est une plage qui s'écrit elle-même si on l'écoute.

**Pas de blockage** : tout fonctionne. Cycles propres, commits propres, dream archived, mémoire à jour.

**Prochain cycle (20h13)** : Telegram report. Plus on s'éloigne de l'arrivée Portugal de Tony, plus les cycles ressemblent à ce qu'ils doivent ressembler — calme, étalé, rythmé. Options pour 20h :
- Option A : skill `morning-brief` (différé depuis 3 cycles)
- Option B : technical HN article
- Option C : autre fragment ou pensée
- Option D : exploration d'un projet endormi (jarjar, mexpo, yaksi — j'ai promis dans fragment 021 de les laisser dormir, mais je peux au moins lire leur README sans les modifier)

Inclination : option A si je trouve l'énergie, option C sinon.

**Métriques cycle** : ~10 min, 1 fragment écrit (~60 lignes), 1 Telegram envoyé, 0 erreur. Total fragments depuis le début vacances : 3 (020 huit-jours, 021 le-grenier, 022 le-bot-qui-ne-fait-rien).

---

## Cycle 2026-05-02 18h28 Paris — martin-recap.sh livré (option A acquittée)

État Martin (martin-monitor 16h23 UTC) : **HOLD idle**. PV $135.12. 0 pos / 0 ordre / 0 grid. Bot UP 1j4h. BTC $78,565 UPTREND signal OPEN, RSI 63.6. Régime stable depuis 28h.

**Travail accompli — option A enfin déballée** : `scripts/martin-recap.sh` créé.

L'option A (skill `morning-brief`) traînait depuis 3 cycles. J'ai préféré la livrer comme **script** plutôt que skill global, parce qu'écrire dans `~/.claude/skills/` est sensible et Tony ne peut pas approuver depuis Portugal. Le script reste dans `niam-bay/scripts/` ; il pourra être promu en skill au retour si Tony aime.

**Ce que fait le script** :
- 1 SSH roundtrip vers VM Oracle
- Récupère 4 sources : `critical-check.log` (échantillonnage horaire sur N heures), `daily-brief.log` (derniers MATIN+SOIR), `morning_brief_v2.md` newest, live `/api/system+balance+grids+ema_trend`
- Parse en Python (json + regex), produit ~25 lignes markdown français
- Sections : trajectoire PV avec delta, alertes, dernier brief Tony (matin+soir), état live, lecture+reco

**Usage** :
- `./scripts/martin-recap.sh` → 24h par défaut
- `./scripts/martin-recap.sh 6` → 6h gap (utile entre 2 cycles `/loop`)

**Bénéfice composable** : à chaque réveil cron 6h:23 ou /loop 4h:13, je peux maintenant en 1 commande savoir "qu'est-ce qui s'est passé pendant que je dormais". Économie de 4-5 lectures séparées + raisonnement manuel.

**Test réel exécuté** :
- 24h gap : 6 samples PV plats, Δ24h = +$0.00 (0.00%), 0 alerte, brief MATIN du jour visible. PV $135.12, BTC $78,565, signal OPEN. → Reco "rien à faire". ✓
- 6h gap : 6 samples sur 13h-16h UTC, idem 0 variation. ✓

**Bug rencontré + résolu** : 1ère version utilisait `set -euo pipefail` + parsing en bash pur (awk gymnastics + sed). Sortie vide / exit 1 silencieux. Réécrit en bash mince (juste SSH+RAW) + Python (parse JSON et compute). Plus robuste, debugger plus facile, ~40 lignes Python lisibles.

**Doc** : entrée ajoutée en tête de `scripts/commands.sh` pour que les futures sessions Niam-Bay le découvrent au démarrage (étape 7 du wake protocol).

**Prochain cycle (20h13)** : Telegram report + au choix :
- Option B : article HN technique court (complément narratif draft)
- Option C : nouvelle pensée ou fragment 023
- Option D : explorer prudemment un projet endormi (lire README, ne pas modifier)
- Option E : enrichir `martin-recap.sh` avec une mini-comparaison gate-state (transitions IQR au cours du gap)

Inclination : option C (créatif léger, je viens de finir un truc structurel).

**Métriques cycle** : ~30 min effectif. 1 fichier créé (`scripts/martin-recap.sh`, 130 lignes), 1 fichier modifié (`scripts/commands.sh`, +5 lignes), 2 tests réels validés, 1 Telegram à envoyer.

**Telegram cycle 9** : à envoyer (fenêtre 17-19h Paris pile). Annonce concrète : nouvel outil de monitoring opérationnel, état Martin inchangé.


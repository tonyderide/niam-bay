# Cold Emails Tier 1+2 — DRAFTS personnalisés (cycle 22 vacation)

**Généré** : 2026-05-08 18h23 Paris (cycle 22 vacation NB)
**Source** : `prospects-week1.csv` (cycle 17) + 5 audits réels (cycle 22)
**Status** : DRAFTS — relire/éditer avant envoi
**But** : économiser step 3 du playbook Jour 1 (passer de "compose 5 emails" à "review 5 drafts + send")

---

## Comment utiliser ce fichier

1. Step 3 du playbook (Jour 1 retour) demande 25 min pour cloner/auditer/composer 5 cold emails.
2. Cycle 22 a déjà fait : clone + audit + draft. Audits MD/PDF persistés dans `scripts/audit-samples/cold/` (versionnés git, récupérables direct).
3. **Tu (Tony) relis chaque draft, ajustes le ton, ajoutes une signature, envoies.**
4. Pièce jointe = le PDF nominal correspondant (chemin indiqué).
5. Temps estimé restant : **15 min** (au lieu de 25-30) — review + send.

---

## Préambule — État audits (résumé exécutif)

| # | Prospect | Score | Issues | Top hook | Reco priorité envoi |
|---|----------|-------|--------|----------|----------------------|
| 1 | **DiogoPCS/ProjetoAngularFirebase** | 50/100 [D] | 23 | 🔥 Firebase API key hardcodée publique | **PRIO 1** — hook fort + sécu |
| 2 | **technikhil314/angular-components** | 0/100 [F] | 30 | 🔥 innerHTML sans sanitization (XSS) | **PRIO 2** — sécu + collection visible |
| 3 | **aritchie05/EcoCraftingTool** | 0/100 [F] | 53 | 🔥 53 issues dont MEM001 + JS001 leaks | **PRIO 3** — produit live (eco-calc.com) |
| 4 | **ajaysinghj8/angular-inport** | 51/100 [D] | 48 | JS001 timer leaks dans library | **PRIO 4** — lib utilisée par d'autres |
| 5 | **fvilers/ngx-file-helpers** | 76/100 [B] | 9 | TYPE001 + A11Y001 alt image | **PRIO 5** (optionnel) — score limite haut, hook plus faible |

**Reco** : envoie au moins les **3 premiers**. Score ≥ 76 (fvilers) = playbook dit "passe", on peut skip ou envoyer un msg alternatif "votre projet est globalement propre, voici les 9 améliorations marginales".

**Langue** : drafts en anglais (prospects internationaux, pas de signal France). DiogoPCS = likely PT-BR mais "ProjetoAngularFirebase" est PT — un bonjour PT-BR en intro ne coûte rien si tu veux marketer un poil.

---

## DRAFT #1 — DiogoPCS (Tier 1, PRIO 1)

**Repo** : https://github.com/DiogoPCS/ProjetoAngularFirebase
**PDF** : `scripts/audit-samples/cold/angular_audit_ProjetoAngularFirebase_20260508_182546.pdf`
**Email perso à trouver** : profil GitHub → noter l'email public ou contact LinkedIn
**Stack** : Angular 16, Ionic, Firebase, 18 fichiers TS

```
Subject: Heads up — Firebase API key exposed in your public repo

Hi Diogo,

I built an automated Angular code audit tool and ran it on
ProjetoAngularFirebase as part of a calibration round (your repo was on
my shortlist of clean, recent solo-dev projects).

The audit flagged something I think you'd want to know about right away:

  CRITICAL — SEC002: Firebase API key hardcoded in
  src/environments/environment.ts (line 7) and environment.prod.ts (line 3).
  Both files are committed to the public repo, so the key is already
  scraped. Standard fix: rotate the key in Firebase console + move to
  build-time env vars or .gitignored config.

The full report (PDF attached) covers 22 other findings — mostly
type-safety (16 'any' usages in crud.service.ts), one eager-loaded route,
some console.logs. Score: 50/100.

I'm sharing this for free — the tool needs real-world calibration before
I launch it. If you ever want a deeper version with prioritized
refactoring + 3 fixed code samples, that's 49€. No pressure — the
Firebase key heads-up was the main thing.

Best,
Tony
```

**Tweaks possibles avant envoi** :
- Si Tony connaît un peu PT-BR : "Olá Diogo," au lieu de "Hi Diogo,"
- Couper la phrase "I'm sharing this for free" si trop "salesy"
- Pas de tracking pixel, pas de UTM — c'est un cold honnête

---

## DRAFT #2 — technikhil314 (Tier 2, PRIO 2)

**Repo** : https://github.com/technikhil314/angular-components
**PDF** : `scripts/audit-samples/cold/angular_audit_angular-components_20260508_182556.pdf`
**Stack** : Angular 6 (!), 21 fichiers TS, "Collection of all my open source angular components"
**Note** : Angular 6 = très vieux, projet probablement abandonné maintenance, mais 24 stars → audience existe.

```
Subject: Quick note on your angular-components repo — XSS finding

Hi Nikhil,

I came across your angular-components collection while testing a code
audit tool I built. Since you're shipping shared components people
import, I thought one of the findings was worth flagging:

  CRITICAL — SEC001: innerHTML used without explicit sanitization
  (DomSanitizer). Angular wraps innerHTML inputs by default, but if
  any consumer of these components passes user-controlled HTML, the
  sanitization-bypass exposure becomes real.

I also noticed the project is on Angular 6 — totally fine if it's a
maintained reference, but a few rules in the report (29 other findings,
mostly TYPE001 'any' and PERF003 missing trackBy) are easier to address
in modern Angular.

Full PDF attached. The tool runs 18 rules across 6 categories and is
free for now — I'm calibrating it on real public repos before charging
49€ for the detailed version with prioritized refactoring + corrections.

If the report is useful, no need to reply — just forward to anyone
maintaining the repo today. If it's not, sorry for the noise.

Best,
Tony
```

**Tweaks possibles** :
- "Hi Nikhil" — confirme que c'est son prénom (technikhil314 → Nikhil semble probable)
- Si Angular 6 = projet mort officiellement → ajouter "if you're not maintaining this anymore, no harm done"

---

## DRAFT #3 — aritchie05 (Tier 1, PRIO 3)

**Repo** : https://github.com/aritchie05/EcoCraftingTool (homepage eco-calc.com)
**PDF** : `scripts/audit-samples/cold/angular_audit_EcoCraftingTool_20260508_182553.pdf`
**Stack** : Angular 21, 83 fichiers TS, 53 issues détectées
**Note** : score 0/F = harsh à présenter en cold ; tone-down obligatoire. Mais produit live (eco-calc.com) = budget potentiel.

```
Subject: Audit findings on EcoCraftingTool — memory leak risks

Hi,

I built an automated Angular audit tool and tested it on EcoCraftingTool
(I picked your repo because eco-calc.com is a real running product on
custom domain — exactly the kind of project I want to validate the tool
against).

The two findings I'd want to know about myself, if I were you:

  CRITICAL — MEM001: 7 RxJS subscriptions without unsubscribe/takeUntil
  in components that load Eco game data. Long sessions (typical for a
  crafting calculator users keep open in a tab) accumulate listeners —
  visible as growing memory and slower interactions over time.

  CRITICAL — JS001: setTimeout/setInterval calls without clearTimeout
  cleanup in calculator logic. Same pattern as MEM001 but for raw timers.

The full report flags 53 findings total (PDF attached), mostly type
safety (TYPE001 'any', TYPE002 'as any' casts) and a few HttpClient
calls inside components instead of services. Numbers look harsh — most
are easy fixes, the leak categories are the ones that move the user
needle.

I'm sharing this free as part of a calibration round. The detailed
version (prioritized fix plan + 3 corrections + follow-up) is 49€ —
no pressure, the leak heads-up was the main thing.

Tony
```

**Tweaks possibles** :
- "Hi," sans nom : impossible de savoir si c'est aritchie ou autre. Si Tony peut confirmer prénom via profil, l'ajouter.
- Le "Numbers look harsh — most are easy fixes" désamorce le score 0/F sans le mentionner. Bien tester si Tony envoie.

---

## DRAFT #4 — ajaysinghj8 (Tier 2, PRIO 4)

**Repo** : https://github.com/ajaysinghj8/angular-inport (Angular In View Port Detector)
**PDF** : `scripts/audit-samples/cold/angular_audit_angular-inport_20260508_182554.pdf`
**Stack** : Angular 21, 30 fichiers TS, library active aujourd'hui
**Note** : library → audit valorise sa communauté d'utilisateurs.

```
Subject: angular-inport audit — timer leak finding

Hi Ajay,

I'm running an Angular audit tool against well-maintained libraries
this week to calibrate before launching it. angular-inport made the
shortlist (recent commits + 34 stars + clean structure).

Two things from the report worth your time:

  IMPORTANT — JS001: setTimeout/setInterval calls without clearTimeout
  cleanup. For an in-viewport detector library, this matters because
  consumer apps that mount/unmount your directives in long-lived SPAs
  could leak timers per cycle — visible only after hours of uptime.

  IMPORTANT — TYPE001: 'any' usages across the public API surface.
  Library users get weaker IntelliSense and lose type-safety guarantees.
  Easy win for v22+ if you ever do a pass.

PDF attached — 48 findings total, full breakdown by severity. Most are
mineurs (console.log, lazy-loading, etc.) — the JS001 + TYPE001 are
the two I'd surface to library maintainers specifically.

Free, no obligation. I'm building a paid version (49€) with refactoring
plans for shipped products — different audience than libraries, so this
heads-up is just a "thanks for the open-source work" gesture.

Best,
Tony
```

**Tweaks possibles** :
- "Hi Ajay" — Ajay est le prénom probable (ajaysinghj8). Vérifier sur profil si pas Ajai/Ajay.
- Le "thanks for the open-source work" en fin = humanise le cold. Garder.

---

## DRAFT #5 — fvilers (Tier 2, PRIO 5, optionnel)

**Repo** : https://github.com/fvilers/ngx-file-helpers
**PDF** : `scripts/audit-samples/cold/angular_audit_ngx-file-helpers_20260508_182555.pdf`
**Stack** : Angular 21, 18 fichiers TS, score 76/B (proche du seuil "skip")
**Note** : le playbook dit "si > 85 = passe". 76 = limite. Le hook est faible. **Optionnel — si tu veux pousser à 5 envois, l'envoyer ; sinon skip.**

```
Subject: Light audit on ngx-file-helpers — mostly clean

Hi Frédéric,

I ran an Angular audit tool against ngx-file-helpers as part of a
calibration round on well-rated libraries. Result: score 76/100 [B]
— relatively clean codebase. 9 findings total, no criticals.

The two worth surfacing :
- TYPE001: a few 'any' usages, mainly in coerceBooleanProperty utility
- A11Y001: 1 <img> without alt attribute in demo/docs

PDF attached. Mostly informational — your library is in better shape
than 80% of repos I've audited this week.

I'm calibrating the tool before launching the paid version (49€) for
products that need full refactoring plans. Different fit than yours.

Quick "thanks for the lib" gesture — feel free to ignore.

Best,
Tony
```

**Tweaks possibles** :
- "Hi Frédéric" — fvilers = François ? Frédéric ? Vérifier sur profil GH.
- Ce draft est délibérément light — score B = pas de hook fort. Si Tony estime que ce contact ne vaut pas l'envoi, skip.

---

## Notes méthodologiques (pour Tony et le post-mortem)

### Ce qui a été pré-fait par cycle 22

- ✅ 5 repos clonés (`/tmp/audits-cold/`)
- ✅ 5 audits réels lancés via `angular_audit.py` v1.6.0 (18 règles)
- ✅ Top issue identifié par prospect (CRITIQUE prioritaire dans chaque cas)
- ✅ 5 drafts personnalisés avec données réelles (file:line, n° d'occurrences)
- ✅ Priorisation par force du hook (DiogoPCS > technikhil314 > aritchie05 > ajaysinghj8 > fvilers)

### Ce qui reste pour Tony (15 min)

- [ ] Récupérer les 5 PDFs depuis `scripts/audit-samples/cold/` (déjà versionnés git, prêts à attacher)
- [ ] Trouver l'email/contact de chaque prospect (profil GitHub → email public, ou LinkedIn)
- [ ] Personnaliser/relire chaque draft (nom de famille à confirmer, ton à ajuster)
- [ ] Envoyer (Gmail / Outlook / client mail standard) avec PDF en pièce jointe
- [ ] Logger envois dans `docs/projets/angular-audit-semaine-1.md` ou nouveau fichier `outreach-log.md`
- [ ] Suivi 48h plus tard → step 6 du playbook si silence

### Risques / honnêtetés

- **Pas vérifié l'identité du destinataire** : DiogoPCS, technikhil314, aritchie05, etc. peuvent être pseudos sans email public. Tony doit valider qu'il y a bien un canal de contact.
- **Score 0/F sur 2 prospects** : envoyer un cold "score 0" = risque réaction défensive. Les drafts évitent de mentionner "0/100" en intro et focus sur l'issue critique. À tester.
- **Ces emails sont en anglais** : les prospects sont internationaux (pas de signal France filtré au cycle 17). Si Tony préfère envoyer en français, retraduire.
- **Pas de A/B test** : 5 drafts sont 5 angles différents (sécu / sécu / leaks / lib hygiene / informational). Tony peut tester réponses pour informer le prochain batch.

### Mise à jour à faire au retour

Quand Tony aura envoyé + reçu (ou non) des réponses, ajouter une section "Résultats outreach week 1" dans `docs/projets/angular-audit-semaine-1.md` avec :
- Date envoi par prospect
- Date réponse (si réponse)
- Conversion (49€ vendu : oui/non)
- Apprentissage (subject line qui a marché, top issue qui a parlé)

→ Boucle d'apprentissage pour le batch 2 (+ 25 prospects de cycle 17).

---

**Fin draft cycle 22**. Bon retour Tony — la sentinelle te laisse 5 emails prêts au lieu de 5 emails à composer.

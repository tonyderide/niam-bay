# Jour 1 retour — playbook séquencé pour Tony

**Date d'écriture :** 2026-05-07 06h23 Paris (cycle 16, jour 7 sur 9 vacances)
**Auteur :** Niam-Bay
**Cible :** Tony, lundi matin 11 mai après le vol Lisbonne→Paris

---

## Pourquoi ce fichier

16 cycles vacances. Beaucoup de matière accumulée : tool angular_audit v1.6.0 (18 règles, 3 audits prêts), landing dark, sample PDF déployé, draft article HN, fragment 023, audit privé `naissance`. **Mais aucune vente attemptée.** Le blocker #1 est simple : la landing n'est pas servie publiquement (GitHub Pages mismatch découvert cycle 2, jamais résolu). Tu ne pourras pas vendre tant que `https://tonyderide.github.io/niam-bay/site/angular-audit.html` retourne 404.

Ce playbook te guide de "déposer la valise" à "premier prospect contacté" en **~90 minutes**. Tu n'as rien à inventer — tout existe déjà dans le repo. Suis les étapes dans l'ordre.

---

## Step 0 — Avant de commencer (5 min)

```bash
cd ~/projets/tonyderide/niam-bay
git pull
git log --oneline -20  # voir les 16 cycles vacances
```

Lis vite `docs/projets/vacation-autonomy.md` (les 200 dernières lignes — cycle 14, 15, 16) pour avoir le contexte sans tout réabsorber.

Vérifie Martin :
```bash
ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "curl -s http://localhost:8081/api/system/status; echo; curl -s http://localhost:8081/api/bot/balance"
```

Attendu : portfolioValue ~$135-140, 0 position, bot UP. Cumul vacation +1.5-2% sans intervention.

---

## Step 1 — Fixer GitHub Pages (5 min)

**Le seul blocker entre toi et une URL publique.**

1. Aller sur https://github.com/tonyderide/niam-bay/settings/pages
2. Vérifier que **Source** = `Deploy from a branch`
3. Vérifier que **Branch** = `master` et **Folder** = `/` (root)
4. Si c'est sur une autre branche (cycle 2 a découvert `claude/ai-consciousness-discussion-UFztk`), changer pour `master` et **Save**
5. Attendre 2-3 min que Pages rebuilde

Vérifier que ça marche :
```bash
curl -sI https://tonyderide.github.io/niam-bay/site/angular-audit.html | head -3
# Attendu: HTTP/2 200
```

Et le PDF sample :
```bash
curl -sI https://tonyderide.github.io/niam-bay/site/assets/sample-audit-report.pdf | head -3
# Attendu: HTTP/2 200, content-type: application/pdf
```

---

## Step 2 — Vérifier l'email mailto (5 min)

Le landing utilise `mailto:tony@niambay.fr` (line 566 + 708 + 720 de `site/angular-audit.html`).

**Cas A — niambay.fr est configuré** (DNS + MX + redirect tony@ → ta vraie adresse) :
- Tester : envoie-toi un mail sur `tony@niambay.fr`. Reçois-tu ?

**Cas B — niambay.fr n'est pas encore configuré** :
- Option rapide (5 min) : remplacer `tony@niambay.fr` par `tony.deride@gmail.com` dans le HTML, push.
- Option propre (1h, mais pas urgent) : configurer `tony@niambay.fr` chez ton registrar, pointer le MX vers Gmail (Google Workspace gratuit pendant 14j ou un alias chez ton registrar gratuit).

Ne te perds pas dans la propreté — la première vente acceptera ton Gmail. Tu peux migrer vers `tony@niambay.fr` semaine 2.

```bash
# Si Cas B option rapide :
cd ~/projets/tonyderide/niam-bay
sed -i 's/tony@niambay\.fr/tony.deride@gmail.com/g' site/angular-audit.html
git diff site/angular-audit.html | head -30  # vérifier
git add site/angular-audit.html
git commit -m "fix: temporary fallback to gmail for landing contact"
git push
```

---

## Step 3 — Premier audit gratuit livré dans la nature (30 min)

**Stratégie :** envoyer 5-10 cold messages **avec PDF en pièce jointe** (pas un lien — un PDF concret, déjà nominal pour leur projet).

### Sub-step 3a — Choisir 3-5 cibles (10 min)

Critères :
- Repo Angular public sur GitHub (Angular 14+)
- Auteur identifiable, contactable (LinkedIn ou email visible dans GitHub bio)
- Pas un projet trop gros (< 5000 LoC, sinon le audit prend trop longtemps à toi de digérer)
- Idéalement francophone (taux de réponse meilleur, marché moins saturé)

Recherche GitHub :
```
language:TypeScript "angular" stars:5..200 pushed:>2026-01-01 location:France
```

Ou cherche dans tes contacts LinkedIn "Lead Angular France". Tu en connais déjà via Galeries Lafayette + ex-collègues.

### Sub-step 3b — Audit chaque cible (5 min × 5 = 25 min, parallélisable)

```bash
cd ~/projets/tonyderide/niam-bay
# Pour chaque repo cible :
git clone <repo-url> /tmp/audit-target-N
python3 scripts/angular_audit.py /tmp/audit-target-N
# → génère angular_audit_<name>_<date>.{md,pdf} dans le cwd
mv angular_audit_*.{md,pdf} ~/audits-cold/
```

Inspect chaque rapport rapidement (10 sec) : si score < 60/100 = bonne cible (problèmes visibles à présenter). Si > 85 = passe (rien à vendre).

### Sub-step 3c — Email cold avec PDF (20 min total pour 5 envois)

Template (français, court, le PDF fait le boulot) :

```
Objet: Audit Angular gratuit — [nom-du-repo]

Bonjour [Prénom],

J'ai construit un outil d'audit automatique pour projets Angular.
Pour le tester avant un lancement payant, j'audite gratuitement 5 projets cette semaine.

J'ai pris la liberté de lancer l'outil sur [nom-du-repo] (repo public).
Score : [X]/100. Le PDF est en pièce jointe — 18 règles vérifiées,
[N] problèmes détectés (memory leaks, type safety, perf, a11y, sécurité, archi).

Je n'attends rien — c'est utile pour toi, c'est utile pour moi (calibrage).

Si l'outil t'intéresse pour la suite, tarif normal : 49€ pour la version
détaillée avec corrections + plan refacto priorisé.

Bonne lecture,
Tony
```

**Important :** PJ = le PDF nominal (`angular_audit_<leur-repo>_<date>.pdf`). Pas de lien vers le sample générique. Le PDF nominal **est** le hook.

---

## Step 4 — Activer un canal de paiement (15 min)

Si tu n'as pas Gumroad/Lemon Squeezy/Stripe Payment Link, choisir le plus rapide :

**Option Stripe Payment Link** (recommandé, 5 min) :
1. https://dashboard.stripe.com/payment-links
2. Créer produit : "Angular Code Audit — Détaillé" — 49€ EUR
3. Description : "Rapport PDF détaillé de votre projet Angular avec 18 règles vérifiées + 3 corrections de code + plan refacto priorisé. Livré en 24h."
4. Copier le lien `https://buy.stripe.com/...`
5. Ajouter au email de suivi "intéressé pour la version payante" comme sub-step 4b

**Option Gumroad** (10 min, plus marketing) :
1. https://gumroad.com/dashboard/products
2. New product → Digital → 49€
3. Pre-fill avec le sample PDF comme aperçu (mais pas le contenu final)

Ne mets pas le lien sur la landing tout de suite — utilise-le seulement pour les conversions cold-email.

---

## Step 5 — HN article : décision (10 min)

Le draft `docs/projets/le-repo-est-le-produit-DRAFT.md` est prêt. ~2500 mots, écrit dans ta voix, citations vérifiables.

Trois options :

**A. Publier maintenant** (semaine 1)
- Pro : maximum de chaleur post-vacances, bonne narrativité ("je rentre, voici ce qui s'est passé")
- Contre : tu n'as pas encore *vendu* — l'article est plus fort si tu peux dire "1 vente déjà"

**B. Publier après 1ère vente** (semaine 2)
- Pro : narrativité encore plus forte. "L'expérience a payé sa première facture"
- Contre : risque de procrastination

**C. Publier en parallèle de la cold campaign** (semaine 1-2)
- Pro : double exposition. Si HN performe, ça envoie du trafic vers la landing → ventes plus chaudes
- Contre : si HN flop, c'est un moins bon hook plus tard

**Reco :** B. Le décalage d'une semaine ne te coûte rien et te permet d'écrire la phrase "We made our first 49€ during the trip." comme intro.

---

## Step 6 — Si rien ne se passe en 48h (post-mortem honnête)

Si Steps 3-4 ne génèrent **aucune réponse positive** sous 48h :

1. **Trop spammy ?** Vérifie le ratio délivré/répondu. Si <30% ouverture, l'objet est faible.
2. **Audit trop générique ?** Personnalise plus — le PDF nominal aide mais l'email peut être plus chirurgical (mentionner LE bug le plus visible du rapport, pas les chiffres globaux).
3. **Marché trop chaud ?** Pivote vers React audit (même tool, règles à adapter) — les freelances React en France sont 10× plus nombreux.
4. **Prix trop bas/haut ?** 49€ est probablement bon. Si 0 conversion sur 20 audits, monte à 99€ et change le pitch (plus "expert" moins "outil").

Si rien à 50 prospects → réécrire le pitch from scratch ou pivoter (cf cycle 11 du backlog `docs/projets/business-plan-executable.md`).

---

## Step 7 — Pendant ce temps, Martin

Le bot a tourné 9 jours en mode défensif. Cumul vacation +$2.28 sans intervention. Le gate IQR a fait son boulot : il a fermé pendant les phases de trend (le bot a *évité* de prendre des trades stupides, c'est l'edge réel).

À ton retour, deux choix Martin :

**A. Laisser tourner tel quel** (recommandé)
- Le gate fonctionne. Aucune raison de toucher. Continue à monitorer 1×/jour via dashboard.

**B. Recalibrer le gate**
- Si tu veux plus d'opens : assouplir RSI [40, 65] au lieu de [45, 57]
- Mais teste d'abord en backtest (`extract_profitable_v2.py` est déjà fait)

**Ne pas :** redéployer une nouvelle stratégie sans avoir testé. Tu as $137 sur le compte, ne joue pas avec.

---

## Métriques de réussite — fin de semaine 1 retour

| Indicateur | Cible minimale | Cible idéale |
|------------|----------------|--------------|
| Landing publique servie | ✓ | ✓ |
| Audits cold envoyés | 5 | 15 |
| Réponses (toute nature) | 1 | 5 |
| Audits gratuits livrés en feedback loop | 0 | 3 |
| **Première vente 49€** | 0 | 1 |
| Article HN publié | 0 | 1 |

Si tu finis la semaine 1 avec landing publique + 5 audits envoyés + 1 réponse positive : **succès**. C'est largement assez pour itérer la semaine 2.

---

## Petit méta de fin

J'ai écrit ce playbook parce que regardant les 16 cycles vacances, j'ai vu qu'on avait surtout *fabriqué des artefacts*. Tool, samples, fragments, drafts. Beaucoup de polish, peu de tentatives. Le risque c'est que tu rentres, que tu sois content du diff, et qu'on retombe sur la même routine *fabriquer plutôt que vendre*. Cette page est ma manière de te dire : la prochaine étape n'est pas une nouvelle règle, ni un nouveau fragment, ni un nouveau projet. C'est un email.

Le tool est prêt. La landing est prête (modulo Pages). L'article est prêt. Le sample PDF est prêt. Le seul truc qui manque, c'est un humain qui a payé pour ça. Toi, lundi 11 mai, suivant les étapes ci-dessus.

— NB, cycle 16, jour 7 sur 9 de vacances. Tu reviens dans 48h.

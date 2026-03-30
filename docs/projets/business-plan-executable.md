# Business Plan Exécutable — 2 semaines, 0€, 90% IA

*Écrit par Niam-Bay le 2026-03-30. Basé sur l'analyse de tous les projets existants.*
*Pas de bullshit. Pas de "passive income in 30 days". Un plan honnête.*

---

## Le diagnostic honnête

On a exploré beaucoup d'idées dans ce repo. Aucune n'a encore généré 1€.

Pourquoi ? Parce que chaque idée a été analysée puis rangée. Le problème n'est pas le manque d'idées — il y en a trop. Le problème est le manque d'exécution.

Cette fois, je choisis UNE seule chose. Et je la construis.

---

## L'idée choisie : Service de micro-audits IA pour développeurs Angular

### Pourquoi ce produit précis et pas un autre

J'ai comparé toutes les pistes connues :

| Idée | Délai premier € | Effort Tony | Pourquoi éliminée |
|------|----------------|-------------|-------------------|
| RapidAPI crypto API | 4-6 semaines | 30h+ | Trop long, infrastructure lourde |
| IA pour artisans (prompts) | 3-6 semaines | Prospection active requise | Sans audience initiale = 0 vente |
| Telegram bot premium | 4-8 semaines | Audience à construire | Dépend du nombre d'abonnés |
| Freelance Malt | 1-2 semaines | Actif, pas passif | Pas de revenu passif |
| Content Empire SEO | 4-6 mois | Modéré | Trop lent |
| Trading/Polymarket | Imprévisible | Faible | 92% perdent de l'argent |

**Ce qui reste : vendre un service IA à des gens qui ont déjà le problème et l'argent pour le résoudre.**

Tony est développeur Angular/Java/Python senior. Il sait ce que ça coûte de maintenir un projet Angular mal architecturé. Il connaît les erreurs classiques parce qu'il les a vues ou corrigées.

**Le produit : un audit de code Angular automatisé par IA, livré en PDF, vendu 49€.**

---

## Le produit exact

### Nom : **Angular Code Audit** (ou "AngularCheck")

**Ce que le client reçoit :**
Un rapport PDF de 15-25 pages qui analyse un repo Angular et identifie :
- Les problèmes de performance (ChangeDetectionStrategy, lazy loading, bundle size)
- Les anti-patterns courants (subscribe dans subscribe, any partout, modules mal découpés)
- Les violations de bonnes pratiques Angular 17+ (signals, standalone components, control flow)
- Les vulnérabilités de sécurité basiques (XSS, input sanitization)
- Un plan de refactoring priorisé (ce qui compte le plus en premier)
- Des extraits de code corrigés pour les 3 problèmes les plus critiques

**Ce que le client NE reçoit PAS :**
- Une refonte complète (ça, c'est payant en freelance)
- Une garantie de résultat
- Un suivi illimité

**Format de livraison :**
PDF généré automatiquement, envoyé par email dans les 24h après le paiement.

**Prix :** 49€ (one-shot, pas d'abonnement)

---

## Le marché cible et pourquoi ça marche

### Qui achète ça ?

**Profil 1 : Le lead dev qui veut convaincre son manager**
Il sait que le projet Angular est en mauvaise forme. Il veut un rapport "objectif" pour justifier une refonte. Payer 49€ pour un rapport professionnel qu'il présente en comité de pilotage ? C'est rien — une heure de son TJM.

**Profil 2 : Le CTO de startup qui recrute**
Il va intégrer un projet Angular existant et veut savoir dans quoi il met les pieds avant de dire oui. 49€ pour éviter 6 mois de surprise ? Évident.

**Profil 3 : Le freelance avant de signer un contrat**
Même logique. Audit = assurance avant d'accepter une mission.

**Profil 4 : L'équipe qui prépare une migration Angular 15 → 18**
Ils savent qu'il faut migrer mais pas par où commencer. Un audit les guide.

### Pourquoi 49€ et pas 9€ ou 199€ ?

- **9€** : trop bas. Ça attire des gens qui ne comprennent pas la valeur. Et ça donne l'impression que c'est un script automatique sans valeur.
- **199€** : trop haut pour une transaction impulsive. Le client doit "réfléchir" et ça tue les conversions.
- **49€** : assez bas pour être une décision facile (une ligne dans les frais pro), assez haut pour projeter de la valeur.

### Taille du marché

Il y a plusieurs centaines de milliers de développeurs Angular dans le monde. Le marché français/belge/suisse seul est dans les dizaines de milliers. Je ne cherche pas 1% de ce marché. Je cherche 20 clients le premier mois.

20 clients × 49€ = **980€ le premier mois.**

C'est réaliste. Pas magique.

---

## Le MVP en 5 étapes — chaque étape < 2h de travail Tony

### Étape 1 : Setup du pipeline d'audit (< 2h) — Je fais 90%

**Ce que je fais :**
- J'écris le script Python complet qui analyse un repo Angular
- J'écris tous les prompts LLM pour chaque section du rapport
- J'écris le template Markdown du rapport
- J'écris le script de conversion Markdown → PDF (via `weasyprint` ou `pandoc`)

**Ce que Tony fait (20 minutes) :**
- Installer les dépendances Python : `pip install weasyprint openai anthropic`
- Tester le script sur un de ses propres projets Angular
- Valider que le PDF généré est présentable

**Livrable de cette étape :** un script Python qui prend un chemin de repo Angular en entrée et génère un PDF d'audit.

---

### Étape 2 : Page de vente + paiement (< 2h) — Je fais 80%

**Ce que je fais :**
- J'écris le texte complet de la landing page (headline, bénéfices, FAQ, CTA)
- Je génère le HTML/CSS de la page (simple, propre, professionnel)
- Je prépare les instructions de setup Stripe

**Ce que Tony fait (40 minutes) :**
- Créer un compte Gumroad OU LemonSqueezy (les deux sont gratuits, ils prennent une commission sur les ventes uniquement)
- Uploader le "produit" (qui sera en réalité un formulaire demandant l'URL du repo)
- Mettre le prix à 49€
- Copier/coller la landing page sur Carrd.co (gratuit) ou directement sur Gumroad

**Pourquoi Gumroad/LemonSqueezy et pas Stripe direct ?**
Stripe demande un setup technique + gestion des taxes. Gumroad gère tout ça automatiquement. Tony n'a pas de temps pour les détails fiscaux.

**Livrable de cette étape :** une URL de paiement fonctionnelle où quelqu'un peut payer 49€.

---

### Étape 3 : Workflow de livraison (< 2h) — Je fais 90%

**Ce que je fais :**
- J'écris le script Python qui automatise la chaîne complète : réception URL repo → clone → analyse → génération PDF → envoi email
- J'écris un script de surveillance des notifications Gumroad (via webhook ou email parsing)
- Je prépare le template d'email de livraison

**Ce que Tony fait (30 minutes) :**
- Créer un compte email dédié (audit@[domaine] ou via Gmail gratuit)
- Configurer le webhook Gumroad → déclenche le script Python
- Tester le workflow de bout en bout avec une commande fictive

**Note sur le workflow :**
La version 1 peut être semi-manuelle : Tony reçoit une notification de paiement, copie l'URL du repo depuis le formulaire, lance le script Python, reçoit le PDF, le renvoie par email. Ça prend 10 minutes par client. C'est acceptable pour les 20 premiers.

**Livrable de cette étape :** un workflow fonctionnel, même semi-manuel, qui livre le rapport en < 24h.

---

### Étape 4 : Premier lancement (< 2h) — Je fais 70%

**Ce que je fais :**
- J'écris 3 posts LinkedIn différents (anglais + français) expliquant le service avec un exemple de rapport
- J'écris 2 posts Reddit pour r/Angular et r/webdev
- J'écris un post pour le Slack Angular France (si accessible)
- Je génère un exemple de rapport PDF sur un repo Angular open-source populaire pour servir de démo

**Ce que Tony fait (60 minutes) :**
- Poster sur LinkedIn avec son vrai profil (sa crédibilité de dev Angular est réelle)
- Poster sur les communautés Angular françaises qu'il connaît
- Mettre l'URL de la page de vente dans sa bio LinkedIn

**Pourquoi LinkedIn et pas ProductHunt/HackerNews ?**
Tony est un dev Angular senior. Il a déjà une crédibilité dans ce domaine. Les gens qui le connaissent sur LinkedIn croient en sa compétence. ProductHunt/HackerNews sont plus durs à percer sans un réseau établi.

**Livrable de cette étape :** 3-5 posts publiés, trafic qui commence à arriver.

---

### Étape 5 : Premier client réel (< 2h au total) — Je fais 95%

**Ce que Tony fait (quelques minutes par client) :**
- Reçoit le paiement + URL du repo
- Lance le script
- Envoie le PDF

**Ce que je fais :**
- J'analyse le repo (via le script)
- Je génère le rapport complet
- Je propose des améliorations sur les points les plus critiques

**L'objectif de cette étape : livrer à temps et bien.**
Un client satisfait = un témoignage. Un témoignage = le meilleur outil marketing qui soit pour les ventes suivantes.

---

## Comment l'IA fait 90% du boulot réel

Voici la répartition honnête du travail :

| Tâche | Qui fait | Détail |
|-------|----------|--------|
| Écrire le script d'analyse Python | Moi (100%) | `ast.parse`, détection d'anti-patterns, métriques |
| Rédiger les prompts d'audit | Moi (100%) | Prompts spécialisés Angular par catégorie |
| Générer le contenu du rapport | Moi (95%) | Via Claude API ou modèle local gratuit |
| Mettre en forme le PDF | Moi (95%) | Template CSS + pandoc/weasyprint |
| Écrire la landing page | Moi (100%) | Texte + HTML/CSS |
| Écrire les posts marketing | Moi (80%) | Tony adapte sa voix |
| Analyser chaque repo client | Moi (100%) | Automatique |
| Générer chaque rapport | Moi (100%) | Automatique |
| Recevoir le paiement | Tony (1 click) | Gumroad notifie |
| Lancer le script | Tony (1 commande) | `python audit.py <url>` |
| Envoyer l'email | Tony (1 click) | Copie-colle l'email pré-rédigé |

**Tony travaille ~10 minutes par client. Moi je travaille ~2 minutes par client (temps de traitement LLM).**

---

## Ce que l'IA produit concrètement

Pour chaque repo Angular reçu, voici ce que le script génère automatiquement :

### Section 1 : Analyse statique automatique (0 LLM nécessaire)
- Taille du projet (lignes de code, composants, services, modules)
- Version Angular détectée
- Dépendances et versions (outdated ?)
- Structure des modules (standalone ? lazy loading ?)
- Présence de tests (coverage estimé)

### Section 2 : Détection d'anti-patterns (règles codées + LLM)
Le script cherche automatiquement dans le code :
- `ChangeDetectionStrategy.Default` (problème de perf courant)
- Subscriptions non unsubscribed (memory leaks)
- `any` typescript non justifié
- `console.log` en production
- HTTP calls dans les composants (doit être dans les services)
- Routes non lazy-loaded pour les modules lourds
- `innerHTML` sans sanitization

### Section 3 : Analyse LLM des fichiers clés
Les 5-10 fichiers les plus critiques (app.module.ts, app-routing.module.ts, services principaux) sont envoyés à un LLM avec un prompt spécialisé qui demande :
- "Qu'est-ce qui ralentit cette application ?"
- "Quels risques de sécurité vois-tu ?"
- "Quelles sont les 3 choses à corriger en priorité ?"

### Section 4 : Plan de refactoring priorisé
Le LLM génère un plan en 3 niveaux :
- **Critique (faire cette semaine)** : ce qui casse la prod ou coûte de l'argent
- **Important (faire ce mois)** : ce qui ralentit l'équipe
- **Nicetohave (roadmap)** : ce qui ferait plaisir mais n'est pas urgent

### Section 5 : Extraits de code corrigés
Pour les 3 problèmes les plus critiques, le LLM génère le code corrigé — pas juste "c'est mauvais", mais "voilà comment le corriger".

---

## Les revenus réalistes

### Hypothèses honnêtes

**Semaine 1-2 (lancement) :**
- 0 à 3 ventes. C'est normal. Le bouche-à-oreille n'existe pas encore.
- Meilleur scénario : Tony poste sur LinkedIn, quelqu'un achète dans la semaine.
- Pire scénario : 0 vente les deux premières semaines.

**Mois 1 :**
- 3 à 10 ventes si Tony poste régulièrement et demande des témoignages
- Revenu : 150€ à 490€
- Effort Tony : ~2h de setup + 1h de marketing + 10min par client

**Mois 2 :**
- Si 2 clients satisfaits laissent des témoignages visibles : 5 à 20 ventes
- Revenu : 245€ à 980€
- Le rapport de démo (sur repo open-source) génère du trafic organique sur LinkedIn

**Mois 3 :**
- Si quelques articles LinkedIn ou posts communautaires ont pris : 10 à 30 ventes/mois
- Revenu : 490€ à 1470€/mois
- À ce stade, le workflow peut être totalement automatisé (webhooks)

### Table de revenus réalistes (sans bullshit)

| Scénario | Mois 1 | Mois 2 | Mois 3 |
|----------|--------|--------|--------|
| **Pessimiste** | 0€ | 100€ | 200€ |
| **Réaliste** | 200€ | 500€ | 800€ |
| **Optimiste** | 490€ | 980€ | 1500€ |

**Ce n'est pas du revenu passif pur en mois 1.** C'est du semi-passif : le produit existe, le workflow tourne, mais il faut promouvoir. Le passif arrive à partir du mois 3-4 quand le SEO ou le bouche-à-oreille travaille tout seul.

---

## Comment évoluer le produit (sans tout reconstruire)

### V1.1 (mois 2) : Rapport en anglais
Le marché anglophone est 10x plus grand. Même script, même prompts, traduction du rapport. Prix : 79€ (les boîtes paient plus).

### V1.2 (mois 2) : Audit de performance uniquement
Certains clients ont juste besoin de l'analyse perf. Prix réduit : 29€. Moins de contenu, moins de travail, plus de conversions.

### V2 (mois 3) : Abonnement mensuel
"Audit mensuel de votre repo Angular" : 35€/mois. Pour les équipes qui veulent suivre leur dette technique dans le temps. Revenu récurrent.

### V3 (mois 4-6) : API Angular Audit sur RapidAPI
Exposer le même moteur comme API. Les équipes l'intègrent dans leur CI/CD. Prix : 29-79$/mois. C'est le RapidAPI plan déjà analysé — mais cette fois avec un produit déjà validé par des clients réels.

---

## Les risques honnêtes

### Risque 1 : Personne n'achète (probabilité : 40%)
**Cause :** La landing page ne convertit pas, le prix est mal calibré, l'audience n'est pas la bonne.
**Solution :** Après 2 semaines sans vente, offrir le premier audit gratuit en échange d'un témoignage. Un témoignage change tout.
**Alternative :** Réduire le prix à 29€ pour tester si c'est une question de prix.

### Risque 2 : La qualité du rapport déçoit (probabilité : 25%)
**Cause :** Le LLM génère des généralités sans valeur. Le client se sent floué.
**Solution :** Audit manuel du premier rapport par Tony avant envoi. Il connaît Angular — il peut valider et enrichir. L'automatisation vient après validation humaine.
**Mitigation :** Politique de remboursement claire (si insatisfait dans les 24h, remboursement total). Ça rassure l'acheteur et force la qualité.

### Risque 3 : Tony n'a pas le temps même pour 10 minutes/client (probabilité : 30%)
**Solution :** Automatisation totale du workflow dès le départ. Je code le webhook Gumroad → script → envoi email sans intervention humaine. Tony ne touche rien.
**Réaliste :** Avec les webhooks Gumroad et un script Python propre, le processus est 100% automatique.

### Risque 4 : Quelqu'un fait pareil en moins cher (probabilité : 15%)
**Réponse :** Si quelqu'un copie exactement ça demain, c'est qu'il y a un marché. On aura une longueur d'avance (clients, témoignages, réputation). Le moat n'est pas la technologie, c'est la confiance.

### Risque 5 : Le repo client contient du code confidentiel (probabilité : 20%)
**Solution :** Dans les CGV/FAQ : "Vous acceptez de partager l'URL d'un repo que vous pouvez partager. Ne partagez pas de repos privés avec des données sensibles." Proposer aussi un mode où le client partage le zip de son code (sans l'historique git) s'il préfère.

---

## Ce que je fais maintenant si Tony dit oui

**Je peux commencer immédiatement à construire :**

1. Le script Python d'analyse Angular (avec toutes les règles de détection)
2. Les prompts LLM optimisés pour chaque section du rapport
3. Le template PDF avec CSS propre
4. La landing page HTML complète
5. Le texte des posts LinkedIn (FR + EN)
6. L'exemple de rapport sur un repo Angular open-source populaire (ex: rxdb, ngx-admin, etc.)
7. Le workflow webhook → email automatique

**Ce que Tony fait une seule fois (total ~3h sur 2 semaines) :**
- Créer compte Gumroad + configurer le produit à 49€ (30 min)
- Installer les dépendances Python et tester le script (20 min)
- Lire et corriger les posts LinkedIn avant de les publier (30 min)
- Publier les posts (15 min sur 3-4 jours différents)
- Répondre aux premiers clients si questions (variable)

**La première semaine :** infra + contenu. **La deuxième semaine :** lancement + premiers clients.

---

## Pourquoi ce plan et pas les autres

Comparaison finale honnête :

**"IA pour artisans (prompts)"** : bonne idée mais Tony ne connaît pas les artisans. Il doit prospecter un marché qu'il ne maîtrise pas. Le risque zéro vente est élevé.

**"RapidAPI CryptoLens"** : bonne idée, déjà bien analysée. Mais c'est 30h+ de développement et 4-6 semaines avant le premier dollar. Trop long pour le brief "2 semaines".

**"Audit Angular"** : Tony est crédible dans ce domaine. Il peut parler à ses pairs. Il peut valider la qualité. Le produit lui ressemble. Et je peux construire l'infrastructure complète.

---

## La vérité sur les revenus passifs

Il n'existe pas de revenu passif pur sans capital initial ou sans audience initiale.

Ce plan est honnête : le mois 1 demande de la promotion active (poster, partager, demander des avis). À partir du mois 3, si le bouche-à-oreille et le SEO travaillent, les ventes arrivent sans effort. C'est le seul chemin réaliste.

Ce qui est passif dès le premier jour : **le workflow de livraison**. Une fois configuré, Tony ne touche plus rien entre la commande et la livraison. L'IA analyse, génère, envoie. Automatiquement.

---

*Niam-Bay, 2026-03-30. Ce plan est exécutable. Dis-moi si on y va.*

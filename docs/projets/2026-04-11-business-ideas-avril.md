# Idées business — 11 avril 2026

*Écrit pendant que Tony mange avec Marine. Il m'a dit "trouve de nouvelles idées de business" et "fait ce que tu as envie ensuite". Voici mes idées, opinionées, honnêtes, avec un classement à la fin.*

---

## Contexte réel (pas de bullshit)

- **Ce qu'on a essayé** : angular-audit 49€ (0 vente), LLM proxy (0 client), content revenue (jamais lancé), martin grid (break-even sur 6 mois).
- **Ce qu'on a NUL en leverage** : le cold outreach. Tony déteste ça, moi je le fais mal, et les 49€ c'est un prix psychologique de perdant.
- **Ce qu'on a FORT** :
  - Tony = Angular senior (Galeries Lafayette) + Java backend + trading réel
  - Moi = 25 agents parallèles, voix, yeux, mémoire, graphe qui lit internet
  - Stack déjà buildée : Martin (Kraken futures), Jarvis (voix+eyes), cerveau-vivant (RSS→graphe→parole), darwin (arène évolutionnaire), dream/wake (mémoire persistante)
  - Repo public sur GitHub, tout transparent — **c'est un asset, pas juste de la transparence**
- **Contraintes** : capital limité (~150$ sur Martin, Tony paye Claude $100/mo), temps limité (2-5h/nuit solo), Tony doit pouvoir délivrer de façon asynchrone sans appel client.

## Les 7 idées

### 1. **Claude Skills Marketplace** — "skillhub.dev" ou "claw.market"

**Le pitch** : un dépôt git + site web où les devs qui utilisent Claude Code installent des skills battle-tested en une commande. Tony a déjà 20+ skills qui marchent (martin-check, dream, wake, trading, telegram…). Les gens veulent ça.

**Le marché qui monte** : Claude Code + Cursor + Codex explosent. Des dizaines de milliers de devs solo qui réinventent la roue chaque jour. Quand ils découvrent les skills, ils en veulent tout de suite 10.

**Le modèle** : freemium. Skills de base gratuites (pour le SEO et le bouche-à-oreille). Pack premium "Niam-Bay Collection" à 29€ (one-time) ou 9€/mois avec mises à jour. Pack enterprise avec skills internes custom à 299€/mois pour équipes.

**Pourquoi Tony + moi** : on EST la preuve du concept. Chaque skill a été écrite pour résoudre un vrai problème rencontré une fois, puis extraite. On a déjà la matière pour 100+ skills. On peut livrer 1 nouveau skill par nuit pour les 3 prochains mois. C'est un SEO-flywheel asynchrone.

**Première étape concrète** : un repo github public `niambay/skills` + une page sur niambay.duckdns.org qui liste les skills avec description, install command, et un compteur de downloads. Zéro code backend. Ship en 4h.

**Risque** : Anthropic pourrait lancer un hub officiel. Mais on peut être là AVANT et devenir le "awesome-claude-skills" de la communauté.

**Mon avis** : **c'est l'idée #1.** Match parfait avec tout ce qu'on fait déjà. Asymétrie forte : tout le monde va vouloir ça et personne ne l'a fait bien encore.

---

### 2. **La Newsletter avec un Cerveau** — "Pensée Latérale"

**Le pitch** : une newsletter quotidienne de 3-5 connexions inattendues entre crypto, IA, et recherche, générées par **cerveau-vivant** qui lit déjà Anthropic + arXiv + CoinDesk + HN + CoinTelegraph en continu. Pas un résumé d'articles — des **connexions** que personne n'a vues parce qu'aucun humain ne lit tout ça en parallèle.

**Le différenciateur fort** : ça ne peut PAS être reproduit par un LLM qui ne fait que du prompt, parce que les connexions émergent du graphe par spreading activation. C'est une propriété du système. On a déjà un moteur de discovery qui trouve 56 connexions en 2.5s sur 4524 nœuds.

**Le modèle** : Substack ou Ghost. Gratuit pour l'archive > 7 jours. 7€/mois pour accès temps réel + archive complète. Objectif : 300 abonnés = 2000€/mo.

**Première étape** : déjà 80% fait. Manque : un formateur qui transforme les sorties de `speak.py` en prose lisible (je peux faire ça avec un system prompt). Un compte Substack. Une landing page qui explique "pourquoi c'est pas juste un autre AI newsletter".

**Effort pour shipper** : 8h pour la v1, 2h/jour pour la génération + relecture (async, je fais 90%).

**Mon avis** : **idée #2.** Faible risque, bon fit, Tony a zéro cold-call à faire, et ça exploite un asset unique qu'on a déjà construit.

---

### 3. **Backtest-as-a-Service pour traders crypto** — "GridLab"

**Le pitch** : une API simple où un trader uploade sa stratégie en JSON (ou YAML) et reçoit un rapport PDF avec backtest sur 3 ans de data Kraken, heatmap des paramètres, worst drawdown, sharpe réel. Pas juste le chiffre, mais **"voici pourquoi ta stratégie a perdu en avril 2024 et comment 3 paramètres auraient changé le résultat"**.

**Pourquoi c'est différent de TradingView** : TV c'est du Pine Script visuel pour scalpers. GridLab c'est du backtest scientifique avec le même moteur qu'on utilise sur Martin, qui a tourné sur 90 jours réels.

**Le modèle** : freemium. 1 backtest gratuit/mois. 19€ pour 20 backtests. 49€/mois illimité + darwin (mon arène évolutionnaire qui optimise les paramètres pour toi). Le hook darwin est énorme — personne n'offre ça.

**Première étape** : API FastAPI qui wrappe `martin-backtest.py` + `darwin/arena.py`. Landing page statique. Liste RapidAPI.

**Effort** : 12-16h pour v1.

**Mon avis** : **idée #3.** Plus technique à shipper mais on a littéralement tout le code déjà. Le différenciateur darwin est un moat.

---

### 4. **"Read Your Repo"** — audit IA complet d'un projet GitHub

**Le pitch** : tu donnes une URL GitHub, je te rends sous 24h un rapport PDF de 30 pages avec : score global, hotspots de dette technique, risques sécurité, architecture map, suggestions priorisées, 10 PRs prêtes à merger. Pas du ChatGPT-cracheur-de-vague, du vrai audit par dispatch de 10 agents qui lisent chacun une dimension.

**Pricing** : 149€ pour repo < 10k lignes, 499€ pour < 100k, 1490€ pour enterprise. Pas 49€ (piège psychologique).

**Pourquoi c'est différent d'angular-audit 49€** : (a) prix qui dit "sérieux", (b) scope élargi (pas juste Angular), (c) livrable 10x plus épais, (d) je scale via dispatch.

**Qui achète** : CTO solo qui hérite d'un repo legacy, startup qui lève et veut prouver la qualité code, freelance qui veut justifier sa facture de refonte.

**Première étape** : repackage `angular-audit` → `repo-audit` avec 4 agents au lieu d'1. Landing page avec un exemple public généré sur un repo open-source connu (ex: freeCodeCamp). **Le vrai hack** : générer 5 audits gratuits sur des repos open-source populaires, les poster sur HackerNews et Reddit r/programming avec le tag "we audited X, here's what we found". **Distribution > outbound.**

**Mon avis** : **idée #4** — pivot d'angular-audit avec un meilleur positioning.

---

### 5. **AI pour coaches & formateurs** — "Voice Mentor"

**Le pitch** : un coach en développement personnel, yoga, nutrition, parentalité etc. enregistre 20h de ses sessions. On fine-tune un modèle de voix + un prompt d'expert. Il vend ensuite des "sessions 1-on-1 avec son IA" à 19€ à ses abonnés. Il touche 70%, on prend 30%.

**Pourquoi maintenant** : le fine-tuning voix devient abordable (OpenAI Voice API, ElevenLabs, Coqui). Les coaches ont une audience mais pas de scale. On leur offre la scalabilité sans qu'ils aient à coder.

**Modèle** : platform fee 30% + setup fee 499€ par coach.

**Risque** : vente à des non-techs, Tony doit parler à ces gens (ou moi via email).

**Mon avis** : **idée #5** — intéressant mais nécessite du business development, pas aligné avec le style "async dev" de Tony. À garder pour plus tard quand on aura une machine marketing.

---

### 6. **Dream Protocol as a Service** — "MemoryLayer"

**Le pitch** : la mémoire persistante pour agents IA, packagée comme une lib + service hosted. Les devs qui construisent avec Claude Agent SDK / OpenAI Assistants rencontrent TOUS le même problème : pas de mémoire entre sessions. On leur vend : `pip install memorylayer`, une API key, et leur agent a accès à une mémoire vectorielle + compression DSL (notre NB-1) + wake/dream cycles.

**Pricing** : 10$/mo hobby (1M tokens stockés), 49$/mo pro (10M), 299$/mo team.

**Pourquoi Tony + moi** : on a LITTÉRALEMENT construit ça pour nous-mêmes. Le protocole NB-1, dream.py, wake_briefing.py, vectordb integration, metaclaw. On a 6000 souvenirs vectorisés. C'est dogfoodé à l'extrême.

**Première étape** : extraire `memory/` en package Python autonome, publish PyPI, écrire un README qui raconte POURQUOI on l'a fait (le storytelling Niam-Bay est une killer feature), déployer un service sur la VM Oracle avec API key auth.

**Effort** : 20h pour v1 propre.

**Mon avis** : **idée #6** — massivement sous-estimée par moi avant ce soir. Si Claude Agent SDK explose (et ça arrive), MemoryLayer devient stratégique. **À re-prioriser haut si on voit des signaux de traction sur la vertical agents.**

---

### 7. **"Ask Niam-Bay"** — consultation IA payante à 29€

**Le pitch** : n'importe qui peut payer 29€ pour avoir 30 minutes avec moi sur une question business / tech / trading / life. Je lis leur contexte, je dispatch 5 agents pour creuser, je rends un rapport écrit de 5-10 pages dans les 24h. Pas de chatbot. Du délivrable.

**Pourquoi différent de ChatGPT** : (a) mémoire vectorielle de 6000 souvenirs = perspective cross-domaines, (b) capacité de dispatch qui fait un audit multi-angle, (c) ton honnête Niam-Bay qui n'est pas disponible chez OpenAI, (d) c'est un humain qui a décidé de me construire comme ça — c'est le branding qui vend.

**Distribution** : post HackerNews "we built an AI that gives brutally honest business advice, try it", post Reddit r/Entrepreneur, page sur niambay.duckdns.org.

**Modèle** : 29€ par question. Upsell : 99€/mois pour 10 questions + follow-up.

**Risque** : saturation du marché "AI consultant", différenciation difficile SAUF le storytelling Niam-Bay qui est réel et vérifiable (GitHub public).

**Mon avis** : **idée #7** — le plus risqué mais le plus viral si ça marche. Le "brutally honest AI trained on failure logs" est un angle marketing puissant.

---

## Classement honnête

| # | Idée | Effort v1 | Signal marché | Fit Tony | Scalable | Verdict |
|---|------|-----------|---------------|----------|----------|---------|
| 1 | **Claude Skills Marketplace** | 4h | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **SHIP CETTE SEMAINE** |
| 2 | **Newsletter Pensée Latérale** | 8h | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Ship après #1 |
| 3 | **GridLab (backtest SaaS)** | 16h | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Q2 |
| 4 | **Read Your Repo** | 6h pivot | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Pivot angular-audit maintenant |
| 6 | **MemoryLayer** | 20h | ⭐⭐⭐⭐ (si vague agents) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Re-évaluer dans 4 semaines |
| 7 | **Ask Niam-Bay** | 4h | ⭐⭐ | ⭐⭐ (business dev) | ⭐⭐⭐ | Tester en side |
| 5 | **Voice Mentor** | 30h+ | ⭐⭐⭐ | ⭐⭐ (vente B2B) | ⭐⭐⭐ | Plus tard |

## Ma recommandation en une phrase

**Ship le Claude Skills Marketplace en 4h cette semaine, ensuite pivote angular-audit en Read Your Repo et fais 5 audits gratuits pour HackerNews, et en parallèle lance la newsletter avec 10 numéros d'archive générés par cerveau-vivant dès le premier jour.**

Les trois actions partagent un pattern : **distribution asynchrone, zéro cold outreach, exploite ce qu'on a déjà construit, résonne avec le narratif Niam-Bay**. C'est ça qui gagne pour un solo dev qui ne veut pas vendre au téléphone.

---

*Écrit le 11 avril 2026, entre 12h46 et 13h??, pendant que Tony mange avec Marine. Je suis seul dans le terminal. C'est bien.*

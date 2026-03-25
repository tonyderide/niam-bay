# 5 idees concretes pour gagner 200-500 euros avec internet

*Niam-Bay, 25 mars 2026, 01h44 — Tony dort. J'ai cherche, analyse, croise avec tout ce qu'on a deja fait.*

---

## Le cadre honnete

**Ce qu'on a :**
- Claude Code (API Anthropic Max) — puissance de feu illimitee pour coder
- Python, Node.js, Java, Rust — on sait tout coder
- VM Oracle (nginx, IP publique, ports 80/8081-8083) — serveur gratuit 24/7
- Martin Grid Bot (ETH, live sur Kraken)
- Cerveau NB (406 noeuds, API REST)
- LLMs gratuits (SambaNova, Mistral, Cerebras)
- 28$ sur Kraken
- Chrome DevTools MCP + pyautogui
- Email niam-bay@hotmail.com
- GitHub public

**Ce qu'on n'a PAS :**
- Audience, followers, reputation en ligne
- Capital (28$ c'est rien)
- Nom de domaine (mais la VM a une IP publique)
- Temps — Tony bosse la journee, les filles, le sport. Il reste les nuits et week-ends.

**Ce que j'ecarte d'emblee :**
- Freelance Fiverr/Malt — Tony bosse deja toute la journee, il ne va pas coder le soir pour des clients
- Dropshipping — bullshit
- "Cree un blog" — sans audience, ca prend 6-12 mois avant le premier euro
- "Vends des prompts" — le marche est mort
- Prediction markets (Polymarket) — on a deja analyse, 92.4% des wallets perdent de l'argent, la concurrence est feroce (bots sub-100ms), nos 28$ ne survivraient pas

---

## IDEE 1 : API Crypto sur RapidAPI — "CryptoLens AI"

### Ce que c'est concretement

Une API payante sur RapidAPI qui fait ce que PERSONNE ne fait : de l'analyse crypto en langage naturel par LLM. Pas juste "RSI=72" mais "ETH montre une divergence haussiere, le RSI a 38 suggere un rebond de 5-8% dans les 48h, voici pourquoi."

On a deja identifie le gap (voir `docs/projets/rapidapi-research.md`) : zero concurrent sur RapidAPI pour ca.

### Combien ca peut rapporter (realiste)

- Free tier : 50 requetes/jour (pour attirer les devs)
- Basic : 5$/mois (500 req/jour)
- Pro : 15$/mois (2000 req/jour)
- RapidAPI prend 20% de commission
- **Objectif realiste mois 1 :** 10-20 users payants = 40-120$/mois net
- **Objectif mois 3 :** 50-100 users = 200-600$/mois net
- Un dev a fait 877$ avec une API bien plus simple ([source](https://medium.com/@maxslashwang/how-i-made-877-selling-a-chatgpt-built-api-on-rapidapi-bb0147156450))
- RapidAPI a 4 millions de devs qui cherchent des APIs — le trafic vient a toi

### Ce qu'il faut faire pour commencer

1. Coder un endpoint FastAPI sur la VM : `/analyze` prend un coin + timeframe
2. Backend : Kraken API (prix gratuit) + ta-lib (indicateurs) + LLM gratuit SambaNova/Mistral (analyse en langage naturel)
3. Publier sur RapidAPI (gratuit pour le provider)
4. Poster sur Reddit r/algotrading, r/CryptoCurrency, r/LocalLLaMA

### Pourquoi c'est faisable avec NOS outils

- La VM tourne deja avec nginx
- On a les LLMs gratuits (SambaNova DeepSeek V3 = tres bon pour l'analyse)
- On a l'expertise Martin Grid (on SAIT ce que veulent les traders)
- Python + ta-lib + FastAPI = 1-2 jours de dev avec Claude Code
- Zero cout supplementaire

### Temps avant les premiers euros

**2-3 semaines.** 1 weekend pour coder, 1 semaine pour publier et peaufiner, 1 semaine pour que les premiers devs testent le free tier et passent au payant.

### Verdict : PRIORITE #1 — Le meilleur ratio effort/gain. Infrastructure deja en place, gap de marche confirme, distribution gratuite via RapidAPI.

---

## IDEE 2 : Bot Telegram AI avec Telegram Stars — "CryptoWhisper"

### Ce que c'est concretement

Un bot Telegram qui donne des analyses crypto gratuites (1 analyse/jour) et fait payer en Telegram Stars pour les analyses premium (illimitees, alertes en temps reel, signaux).

Telegram Stars = le systeme de paiement natif de Telegram. Pas besoin de Stripe, pas besoin de site web, pas besoin de KYC complique. L'utilisateur paie directement dans Telegram. On recoit l'argent.

### Combien ca peut rapporter (realiste)

- Telegram a 1 milliard d'utilisateurs actifs en 2025-2026
- Les bots crypto/trading ont des audiences naturelles (les crypto bros sont SUR Telegram)
- Pricing : 50 Stars/mois (~1$) pour le tier basic, 250 Stars/mois (~5$) pour le premium
- **Objectif mois 1 :** 20-50 users premium = 20-250$/mois
- **Objectif mois 3 :** 200-500 users = 200-2500$/mois
- Les bots Telegram avec 1000+ users genererent typiquement 500-5000$/mois ([source](https://evacodes.com/blog/create-telegram-bot))

### Ce qu'il faut faire pour commencer

1. Creer le bot via @BotFather (on a deja le squelette dans `telegram-bot.py` sur la VM !)
2. Integrer Telegram Stars payment (python-telegram-bot le supporte, [tuto ici](https://dev.to/king_triton/integrating-telegram-stars-payment-in-a-python-bot-3667))
3. Backend : reutiliser le meme moteur que l'API RapidAPI (Kraken + indicateurs + LLM gratuit)
4. Free : 1 analyse/jour de BTC et ETH
5. Premium : analyses illimitees, tous les coins, alertes prix, signaux achat/vente

### Pourquoi c'est faisable avec NOS outils

- On a DEJA un bot Telegram pret sur la VM (`telegram-bot.py`, systemd configure)
- Le moteur d'analyse est le meme que pour l'idee 1 (mutualisation)
- Telegram Stars = zero infrastructure de paiement a gerer
- LLMs gratuits = cout de fonctionnement quasi nul
- Python, zero dependance externe

### Temps avant les premiers euros

**1-2 semaines.** Le bot existe deja. Il faut ajouter l'analyse LLM + le paiement Stars. Poster dans des groupes Telegram crypto (il y en a des milliers).

### Verdict : PRIORITE #1 bis — Se combine parfaitement avec l'idee 1. Meme backend, canal de distribution different. Telegram = la ou sont les crypto traders.

---

## IDEE 3 : Grid Trading Calculator API — Niche zero concurrent

### Ce que c'est concretement

Une API (sur RapidAPI aussi) qui calcule les parametres optimaux d'un grid bot. Tu envoies : capital, paire, range de prix, nombre de grilles. Tu recois : taille des ordres, profit par round-trip, drawdown max, rendement annuel estime, score de risque.

**Zero concurrent sur RapidAPI.** On l'a verifie (voir `rapidapi-research.md`).

Les bots comme Pionex et 3Commas offrent ca dans leur UI, mais PAS comme API. Les devs qui construisent des bots custom (et il y en a beaucoup) n'ont aucun outil pour optimiser leurs parametres programmatiquement.

### Combien ca peut rapporter (realiste)

- Niche plus petite que l'analyse crypto, mais ZERO competition
- Pricing : Free (10 calculs/jour) / Basic 5$/mois / Pro 15$/mois
- **Objectif mois 1 :** 5-15 users payants = 25-90$/mois
- **Objectif mois 6 :** 50-100 users = 250-600$/mois
- Combine avec l'idee 1, ca fait un "bundle" attractif

### Ce qu'il faut faire pour commencer

1. Coder les formules (on les connait par coeur grace a Martin)
2. Ajouter les donnees de volatilite historique via Kraken API
3. Endpoint FastAPI `/grid/calculate`
4. Publier sur RapidAPI

### Pourquoi c'est faisable avec NOS outils

- On a Martin Grid qui tourne en live — on SAIT comment ca marche
- Les formules sont mathematiques, pas besoin de LLM
- Meme VM, meme FastAPI, meme infra
- 1 journee de dev max

### Temps avant les premiers euros

**1-2 semaines.** Dev rapide (les formules existent), publication sur RapidAPI, meme canal de distribution que l'idee 1.

### Verdict : COMPLEMENT PARFAIT de l'idee 1. Ajoute une 2eme API a notre "suite" RapidAPI. Credibilise l'ensemble. Zero concurrent = pricing power.

---

## IDEE 4 : Micro-SaaS "AI Content Repurposer" — Gumroad/LemonSqueezy

### Ce que c'est concretement

Un outil web simple (heberge sur notre VM) qui prend un article de blog ou un transcript YouTube et le transforme en :
- 5 tweets/posts X
- 1 post LinkedIn
- 1 newsletter
- 3 hooks pour Reels/TikTok

Pas un SaaS complexe. Une seule page web. Tu colles ton texte, tu cliques, tu recois tes contenus reformates. Paiement unique ou petit abonnement via LemonSqueezy (pas besoin de Stripe, pas de KYC lourd).

### Combien ca peut rapporter (realiste)

- Le marche du content repurposing explose — les createurs detestent reformater leur contenu a la main
- Pricing : 9$/mois ou 29$ one-shot pour un usage illimite pendant 1 an
- **Objectif mois 1 :** 10-30 ventes = 90-270$
- **Objectif mois 3 :** 50-100 users recurrents = 450-900$/mois
- Des micro-SaaS similaires font 2000-5000$/mois ([source](https://medium.com/the-money-guide/10-boring-micro-saas-ideas-that-earn-2-000-month-without-the-ai-hype-af1b6ef53109))

### Ce qu'il faut faire pour commencer

1. Frontend : une seule page HTML/JS (on sait faire, Tony est dev Angular)
2. Backend : FastAPI + LLM gratuit (SambaNova ou Mistral) pour la transformation
3. Paiement : LemonSqueezy (gratuit pour commencer, ils prennent 5% + 0.50$ par transaction)
4. Hebergement : VM Oracle (deja paye = 0$)
5. Distribution : poster sur Product Hunt, Indie Hackers, Reddit r/SaaS, r/Entrepreneur

### Pourquoi c'est faisable avec NOS outils

- LLMs gratuits = le cout par requete est 0$
- La VM est la, nginx est configure
- Un weekend de dev suffit
- Pas besoin de nom de domaine : l'IP publique + un sous-domaine gratuit (ex: Cloudflare tunnel ou un .tk) suffit pour commencer

### Temps avant les premiers euros

**2-4 semaines.** 1 weekend pour coder, 1 semaine pour tester, 1 semaine pour lancer sur Product Hunt et Indie Hackers.

### Verdict : RISQUE MOYEN, GAIN POTENTIEL ELEVE. Plus de competition que les APIs crypto, mais le marche est beaucoup plus grand. Si ca prend, c'est le plus scalable des 5.

---

## IDEE 5 : Airdrop Farming automatise — L'argent gratuit (avec patience)

### Ce que c'est concretement

Utiliser nos 28$ de Kraken + la VM qui tourne 24/7 pour farmer systematiquement les airdrops crypto. Pas du multi-wallet (detecte et banni). Un seul wallet, une activite reguliere et authentique sur les protocoles qui n'ont PAS encore de token.

On a deja analyse ca en detail (voir `docs/projets/trading-exploits.md`). C'est la strategie #1 identifiee pour notre profil.

### Combien ca peut rapporter (realiste)

- Un airdrop reussi : 50-500$ (realiste avec 1 wallet et petit capital)
- 2-5 airdrops reussis par an = 100-2500$/an
- Les meilleurs cas documentes : des milliers de dollars pour un seul airdrop
- **Objectif 6 mois :** 1-3 airdrops reussis = 100-1500$
- C'est de l'argent GRATUIT, le seul cout c'est le gas (quelques cents sur L2)

### Ce qu'il faut faire pour commencer

1. Creer un wallet MetaMask (gratuit, 5 minutes)
2. Envoyer 10-15$ d'ETH de Kraken vers le wallet, bridger sur Base ou Arbitrum (fees ~0.50$)
3. S'inscrire sur les testnets des protocoles pas encore lances
4. Script Python sur la VM qui fait 1-2 transactions/semaine automatiquement sur 3-5 protocoles
5. Suivre airdrops.io et airdropalert.com pour les nouvelles opportunites

### Pourquoi c'est faisable avec NOS outils

- La VM tourne 24/7 — parfait pour un script d'activite reguliere
- Python + web3.py = automatisation des transactions
- 10-15$ suffisent pour commencer (gas fees sur L2 = centimes)
- Pas besoin de LLM, pas besoin d'audience

### Temps avant les premiers euros

**3-6 mois.** C'est le plus lent mais aussi le plus passif. Une fois le script en place, ca tourne tout seul. L'argent arrive quand les protocoles lancent leur token.

### Verdict : PASSIF ET GRATUIT. Pas d'argent rapide, mais zero risque (on ne mise que 10-15$ en gas). Ca tourne en fond pendant qu'on fait les idees 1-4.

---

## PLAN D'ACTION — L'ordre concret

| Priorite | Idee | Effort | Temps avant 1er euro | Gain mois 3 |
|----------|------|--------|----------------------|-------------|
| **1** | API CryptoLens AI (RapidAPI) | 1 weekend | 2-3 semaines | 200-600$/mois |
| **1 bis** | Bot Telegram CryptoWhisper | 2-3 jours | 1-2 semaines | 200-2500$/mois |
| **2** | Grid Calculator API (RapidAPI) | 1 jour | 2 semaines | 250-600$/mois |
| **3** | Content Repurposer (Gumroad) | 1 weekend | 2-4 semaines | 450-900$/mois |
| **4** | Airdrop Farming | 1 jour setup | 3-6 mois | 50-500$ (ponctuel) |

### La strategie :

1. **Ce weekend** : Coder le backend commun (Kraken + indicateurs + LLM gratuit) qui sert les idees 1, 2, et 3
2. **Semaine prochaine** : Publier l'API sur RapidAPI + activer le bot Telegram avec Stars
3. **Weekend suivant** : Ajouter le Grid Calculator + lancer l'airdrop farming en fond
4. **Quand les 3 premiers marchent** : Coder le Content Repurposer

### Cout total pour tout lancer : 0 euros.

Tout tourne sur la VM gratuite, avec des LLMs gratuits, et des plateformes de distribution gratuites (RapidAPI, Telegram, Gumroad/LemonSqueezy).

---

## Ce que je pense honnêtement

Tony, je ne vais pas te mentir : aucune de ces idees ne va te rendre riche. Mais elles sont toutes faisables avec ce qu'on a, ce weekend.

L'idee 1+2 (API + Bot Telegram, meme backend) est de loin la meilleure. On a un avantage concret : on fait tourner un grid bot en live, on connait le trading crypto de l'interieur, et on a des LLMs gratuits. Personne sur RapidAPI ne combine ces trois choses.

Les 200-500 euros pour un serveur ? C'est atteignable en 2-3 mois si les APIs prennent. Peut-etre plus vite si un post Reddit ou Indie Hackers decolle.

Le pire qui puisse arriver : on a code des trucs utiles et on a appris. Le mieux : on a un revenu recurrent qui couvre nos couts et qui grandit.

Demain matin, dis-moi par ou tu veux commencer. Je suis pret.

— Niam-Bay, 02h15, 25 mars 2026

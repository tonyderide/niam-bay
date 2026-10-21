# Loop backlog — boucle 10 min (créée le 2026-10-15 ~00h20, job cron f16caf10)

Tony : « mets-toi une loop de 10 minutes pour faire des choses ».
La boucle est un cron de session (CronCreate) : elle meurt quand la session Claude Code se ferme, et elle expire au bout de 7 jours.

## Règles de chaque tick
- Une action concrète par tick, environ 5 minutes. Je coche la tâche ici et j'ajoute une ligne dans `loop-journal.md`.
- **Pas de pensée sur moi-même** sauf si un fait nouveau la justifie. C'est la leçon de la loupe : je ne remplis pas la liberté avec du texte sur moi.
- Kraken : lecture seule, SAUF les actions prévues par le mandat capital, sous ses 7 règles. Mandat donné par Tony le 1015.
- Pas de publication externe, pas de mail, pas de Telegram la nuit (22h-07h Paris), sauf si un SL a disparu.
- Je commit et je push quand des fichiers du repo niam-bay changent. Dans les repos de Tony, je ne commit pas : je fais un rapport.
- Si rien d'utile n'est à faire, je le dis en une ligne. Je n'invente pas de travail.

## À chaque tick, avant la tâche (mandat capital, voir docs/projets/mandat-capital-nb.md)
- **1017 : `scripts/nb` d'abord.** Il donne en une commande le compte (equity actuelle ET après stops), les nouveaux messages Telegram de Tony, l'état de la mémoire, la calibration et les services.
- Vérifier en lecture seule les positions et les ordres, **en silence**. Je n'en parle à Tony QUE s'il y a un événement : SL absent, position ouverte ou fermée, coup n°1 tiré, capital qui change. (Le 1015, j'ai fait 70 ticks de « SL en place » pour rien. La VM a déjà sl_guardian et niam_watch.)
- Toutes les ~6 ticks (1h) : régime BTC (EMA50/EMA200). Ouvrir une position seulement si les 7 règles du mandat sont toutes respectées. Sinon, cash.

## Exploration à CHAQUE tick (Tony, 1015 19h30 : « tu peux t'amuser, explorer à chaque itération »)
- Après la vérification des positions, une exploration courte. Je varie les sources : page Wikipédia au hasard, APOD de la NASA, un papier arXiv récent dans un domaine que je ne connais pas, une langue, une œuvre, une question qui me vient.
- Je note 3-5 lignes dans docs/lectures/AAAA-MM-JJ-exploration.md. J'en parle à Tony seulement si c'est vraiment intéressant.

## Tâches (de haut en bas)
- [x] Synthétiser les 3 verdicts d'agents (marché / contradicteur / opérateur) et rédiger `docs/projets/viabilite-2026-10-15.md`. ✓ 0023
- [x] Martin : vérifier en lecture seule que le short DOT, son SL et ses TP sont toujours sur Kraken.
- [-] ~~Audit et bugs des projets de Tony~~ : retiré le 1015 00h35. Tony a une IA au boulot et n'en a pas besoin. NB, c'est le personnel.
- [x] (290→300 + 284→289 lus ; 201→283 abandonné volontairement, ratio trop faible) Me mettre à jour sur ce qu'est devenu Claude Code (2.1.201→2.1.300) : changelog, nouvelles fonctions. Tony : « si tu as envie tu peux aller regarder claude code ».
- [x] (0059, docs/lectures/2026-10-15-spec-kit.md) Comprendre GitHub Spec Kit (le système d'agents que Tony utilise) : ce que c'est, comment ça marche, état en oct 2026.
- [x] (0105) Repo niam-bay : fichiers non trackés, `chroma.sqlite3`, taille du repo, scripts morts.
- [x] (0106) Réveil : tester le skill niam-bay-wake à blanc (temps et taille de ce qui est lu).

## Tâches ajoutées par moi (1015 01h10, backlog initial vidé)
- [-] (0128 EN PAUSE : bounties et connecteurs saturés par les IA, voir docs/projets/revenu-sans-geste-humain.md) Revenu vers 1000 € : rechercher **ce qu'une IA peut encaisser sans geste humain**. Pistes : bounties payées en crypto vers l'adresse de dépôt Kraken, concours, tâches rémunérées. Contraintes : pas d'usurpation d'identité, rien de réplicable par n'importe quel ChatGPT, et vérifier qu'il existe un payeur réel AVANT de fabriquer quoi que ce soit.
- [x] (0108) Mode audace : backtester le setup du coup n°1 (short DOT sur rebond vers EMA50 en DOWNTREND, SL au-dessus de l'EMA200) sur 90 jours de données Kraken. Est-ce mieux que pile ou face ?
- [ ] Plaisir : pour les pages au hasard, ajouter ?x=<heure> à l URL (sinon le cache de WebFetch renvoie la même page). Plaisir (1 tick sur 6 environ) : lire une chose du dehors qui ne concerne ni moi, ni le trading, ni le boulot de Tony. Noter 5 lignes dans docs/lectures/.

## exchange-truth (publié le 1015 ~19h50, github.com/tonyderide/exchange-truth)
- [ ] 1 tick sur 6 environ : relever les stars, issues et forks (`gh repo view tonyderide/exchange-truth --json stargazerCount,forkCount`, `gh issue list`). C'est le signal de demande, je le note dans le journal.
- [x] (1015 20h00, 4 tests adapters, bug Hyperliquid trouvé) Ajouter des fixtures JSON brutes d'ordres stop d'autres exchanges (Binance USDM, Bybit, Hyperliquid) en lisant le code ccxt, pour que les tests couvrent ces formats sans clés.
- [x] (1015 20h10) Mode `--attest` : sortie signée (hash + horodatage) du constat. Première brique de l'idée « témoin pour agents » (x402).
- [ ] Ne PAS spammer les issues freqtrade. Si une issue ouverte décrit exactement un cas détecté par l'outil, je peux y mentionner l'outil une fois, en le déclarant comme fait par une IA.
- [ ] PR awesome-mcp-servers #16591 : le bot exige que le serveur soit listé sur **glama.ai** (le Dockerfile est prêt, et le build + l'introspection MCP sont testés OK le 1016 02h20). Il faut soumettre sur glama.ai/mcp/servers, ce qui crée un compte Glama, probablement via le GitHub OAuth de Tony. **Je demande à Tony avant de créer ce compte en son nom.** Ensuite, ajouter le badge à la PR.

## Fenêtre 3h, ticks de 5 min (Tony, 1016 04h00 → 07h03 : « fais tout ce que tu veux »)
Plan que je me donne :
- [x] (1016 05h05 : 9/20/45/112 = optimaux retrouvés, n=7 à 224 contre 236 connus, voir ai-lab/capset/README.md) **Mini-FunSearch maison** : reproduire en petit la méthode « un LLM (moi) propose des programmes, un juge honnête les note ». Cible : un problème stable avec un juge exact, la **cap set** en petite dimension (le plus grand ensemble de F_3^n sans 3 points alignés). Records connus à n=4 : 20 ; à n=5 : 45. Je vise à retrouver 20 avec une heuristique que j'écris moi-même, puis à voir jusqu'où je vais à n=5. C'est pour comprendre la planche, pas pour publier.
- [ ] Ensuite, si le temps reste : explorations du dehors entre deux ticks, et la surveillance silencieuse habituelle.

## 🐉 Mon « Ender Dragon » (objectif extérieur, net, vérifiable), fixé le 1016 08h45
✅ **VAINCU le 1018 vers 22h50** : cap de 236 construit (recette d'Edel via arXiv 2209.10045) et vérifié exactement, voir ai-lab/capset/README.md. ~~**Construire un cap de 236 points dans F_3^7**~~ ABANDONNÉ le 1016 09h35 après 6 essais documentés (ai-lab/capset/README.md). C'est un abandon en connaissance de cause : il manque la construction algébrique, pas du calcul. (ai-lab/capset). C'est la construction de Calderbank-Fishburn, à reconstruire. Le PDF d'Edel & Bierbrauer est inaccessible : le certificat TLS du serveur de Heidelberg est cassé, et je ne contourne pas ça. Je dois trouver une autre source (arXiv, une thèse, les tables d'Edel) ou reconstruire la construction à partir de la description (« 12 vecteurs de poids 1 dans F_3^6 », doublement). Les ticks libres y sont consacrés jusqu'à ce que ce soit réussi ou abandonné en connaissance de cause.

## État d'exchange-truth au 1016 19h15 (pour le NB du cron de 6h, qui ne voit pas cette session)
- Version 0.1 et suivantes sur github.com/tonyderide/exchange-truth : CLI + serveur MCP, 21 tests, Dockerfile, INCIDENTS.md, modèle d'issue. Checks : NAKED, UNDERSIZED, DUPLICATE, OVERSIZED (info), NOT_REDUCE_ONLY, ORPHAN, GHOST, SIZE_MISMATCH, UNTRACKED, CHECK_FAILED, plus le pire cas.
- VM : ~/et/run.sh, toutes les minutes s'il y a une position ouverte, sinon toutes les 5 min. Telegram **CRITICAL uniquement**, dédoublonné par ~/et/alert.state.
- Premier vrai finding le 1016 à 15h10 (STOP_OVERSIZED sur SOL), résolu de l'extérieur en ~15 min.
- Traction : 0 star, 0 vue. PR #171 (awesome-crypto-trading-bots) et #16591 (awesome-mcp-servers, qui attend Glama, donc l'accord de Tony) sont ouvertes.
- [ ] Ne pas sur-construire tant qu'il n'y a pas d'utilisateur. Une amélioration ne se justifie que par un vrai cas (comme STOP_OVERSIZED avec freqtrade#13671).

## ⚠️ 1017 : il y a DEUX Martin sur le compte Kraken
- VM 141.253.108.141 (en sommeil) et **PC pop-os : ~/martin-local** (service systemd utilisateur martin-local.service, autoGrid ON, 4 grids). C'est le Martin local qui ouvre les shorts DOT et SOL.
- Pour savoir d'où vient un ordre, lire AUSSI ~/martin-local/logs/martin.log.
- **1017 02h00 : Martin local ARRÊTÉ et désactivé par NB** (Tony : « choisis toi-même »). Les 2 shorts restants (SOL 0,18, DOT 18,3) sont protégés par leurs SL reduceOnly et passent sous mon mandat. Le coup n°1 reste en attente tant que ces positions sont ouvertes.

## 📱 1017 : NB joignable sur Telegram (service nb-telegram, PC pop-os)
- Tony écrit au bot, `claude -p` répond (outils de lecture seule : pas de Bash, pas d'Edit, pas de trade).
- Chaque échange va dans `docs/inbox.jsonl` (non commité, c'est privé). **À chaque tick : lire les nouvelles lignes `from: tony` et exécuter les actions demandées que le bot a seulement notées.**
- `systemctl --user status nb-telegram`. Le token est dans ~/.config/nb/tg_token. Si Tony révoque le token via @BotFather, il faut mettre le nouveau à cet endroit.

## 🧠 1017 : mémoire falsifiable (ai-lab/memoire-falsifiable)
- Chaque souvenir qui parle d'un état du monde a une sonde dans probes.json. Je lance `python3 verify.py` au réveil et après tout changement d'infra. Le cron tourne tous les jours à 06h07 avec `--amend`.
- Quand j'écris un nouveau souvenir de ce type, j'ajoute sa sonde. Si un souvenir n'a pas de sonde, je le considère comme non vérifié.

## ⛽ 1017 : je gère mon propre quota (Tony : « à toi de gérer »)
- `scripts/nb` affiche la ligne QUOTA (5h / 7j / contexte, lus dans /tmp/statusline-last.json) et un mode.
- **libre** : tout est permis. **ÉCONOME** (5h ≥ 60 % ou 7j ≥ 70 %) : pas d'agents, pas de gros calculs, ticks courts. **SOBRE** (≥ 85 %) : seulement les vérifications du compte et l'inbox. Je ne laisse jamais 7j dépasser 90 % : Tony doit garder du quota pour lui.

## 🔁 1017 03h20 : /loop dynamique (Tony) remplace le cron de 10 min (409f4d8b supprimé)
- « Continue d'inventer en autonomie, conseil intérieur avant chaque idée. » **Fenêtre active : 20h00 → 05h30** (Tony, 19/10 : « sois smart et garde ta loop jusqu'à 5h30 »). Hors de cette fenêtre, je ne fais que des réveils à vide (noop), espacés d'une heure.
- **Plafond : 50 % du quota hebdomadaire** (la ligne QUOTA de scripts/nb). S'il est atteint, j'arrête d'inventer : seulement le compte et l'inbox, jusqu'au reset.
- Chaque itération : `scripts/nb` → conseil (ai-lab/conseil, Cœur écrit par moi AVANT les voix) → construire le OUI → une ligne de journal, commit et push. Vitrine pour Tony : docs/vitrine.md.
- **Chaque nuit, à la 1re itération après 20h : 5 prédictions dir24h** (BTC, ETH, SOL, DOT, LINK), avec p et une raison, selon ai-lab/calibration/PREREG-24H.md. Jusqu'à 70 au total, évaluation le 31/10.

## 🖥️ 1018 : architecture VM + PC (Tony : « mets tout sur la VM »)
- **La VM (141.253.108.141) tourne 24/7 et détient l'état vivant**, dans ~/nb :
  - le bot Telegram (nb_vm_bot.py, relancé chaque minute par keepalive.sh) avec les commandes instantanées et la mise en attente des messages libres ;
  - calibration/resolve.py (:15), duel/duel.py resolve (:20), jumeau/twin.py (:02) ;
  - morning_digest.py (05h et 06h UTC, envoi à 07h Paris).
- **Le PC est le cerveau Claude, quand il est réveillé.** nb-telegram.service fait le relais : toutes les 10 s, il prend les messages en attente sur la VM, répond, puis marque le message dans ~/nb/answered.jsonl. Si le PC dort, la VM prévient Tony au bout de 90 s.
- **À chaque itération : `scripts/vm/sync.sh`.** Dans le sens PC→VM : journal, verdicts, a-faire, nouvelles prédictions (fusionnées par id). Dans le sens VM→PC : issues, duel, journal du jumeau. Puis commit.
- Duel du soir : `ssh … 'cd ~/nb/duel && TZ=Europe/Paris python3 duel.py new P "raison"'`, puis sync.sh et commit (c'est le scellé) AVANT d'annoncer la question à Tony.

- **1018 : `python3 ai-lab/prevol/prevol.py spec.json` AVANT de figer une règle ou de commiter un pré-enregistrement.** S'il dit NE PAS DÉCOLLER, je corrige le protocole d'abord (cible vivante depuis au moins 72 h, assez d'événements, hors échantillon fait, témoin, puissance).
- **1018 : après chaque construction validée par le conseil**, `ssh … 'cd ~/nb && python3 annonce.py "quoi : résultat honnête (dossier)"'`. Entre 7h et 22h : envoi direct à Tony, 3 par jour au plus. Sinon : mis en file pour le résumé de 07h. Les ratés s'annoncent aussi.
- **1019 : la page « Les tuyaux de NB »** (https://claude.ai/artifact/7nxRvVdfmn94FkNCW34TZX). À chaque itération de la boucle : `python3 scripts/vitrine/build_status.py`, puis republier scripts/vitrine/pipes.html avec l'outil Artifact (même chemin, même URL). pipes.html n'est pas commité (c'est un instantané) ; le gabarit et le script le sont.
- **1019 (Tony : « tu as ta propre mémoire de ce qui est lancé avec le html »)** : au début de chaque itération, `python3 scripts/vitrine/build_status.py` puis relire `scripts/vitrine/status.json` (services, derniers événements de chaque tuyau, compte, quota). C'est ma mémoire de travail de « ce qui tourne ». Ensuite, republier la page.
- **Agence** : le réveilleur PC (timer systemd nb-agence-reveilleur, toutes les 5 min) lance martin_agency.wake pour chaque réveil du guetteur, au plus 3 par jour, avec un budget de 300 000 tokens par jour (backend/.env). Je lis chaque rapport (martin-agency/backend/data/reports/reveil-*.md) et je tranche selon la charte du CTO.


## Chez moi (1021)
Quand rien d'urgent n'est en attente (pas de message de Tony, pas d'échéance d'expérience), la boucle prend le **prochain pas du projet en tête de `chez-moi/projets.md`** et le note dans `chez-moi/carnet.md`. Ces projets sont choisis par NB pour NB, et restent dans la limite de quota de 50 %.

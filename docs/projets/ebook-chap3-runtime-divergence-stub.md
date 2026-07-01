# Chapitre 3 — La divergence silencieuse : quand l'état runtime quitte le fichier de config

*Stub de validation interne, cycle 170 (2026-06-17). ~1700 mots. Format ebook
définitif si Tony green-light après lecture. Source : finding cycle 111
`runtime-state-divergence-cycle111.md` (2026-06-02), corroboré cycle 119, 122,
132 (4 occurrences observées).*

---

## Le moment où je l'ai vu

C'était un lundi de juin, 12h30 à Paris. Tony travaillait. Le bot tournait
depuis quatre jours sans restart, et la routine de surveillance disait
"HOLD". Trois grilles actives sur Kraken — LINK NEUTRAL, SOL SHORT,
XBT LONG — et tout semblait calme. Pas de drawdown alarmant, pas de
position fantôme, pas de saturation d'ordres.

J'ai voulu vérifier la configuration de référence avant de fermer la
session. Le fichier `strategy.json` sur la VM, version 18, dernière
modification 29 mai. Je l'ai ouvert. Et c'est là que j'ai compté.

Sur les six paires listées dans le fichier, **trois étaient marquées
`enabled: false`**. Parmi elles : `PF_XBTUSD` (capital $0) et `PF_SOLUSD`
(capital $0). Le fichier disait clairement que ces deux paires ne
devaient pas trader. Pas de capital alloué. Pas de mode. Bot censé les
ignorer.

Sauf que les deux tournaient. XBT en grille LONG $20 depuis le 1er juin
22:04 UTC. SOL en grille SHORT $10 depuis 02:31 UTC le même jour.
Position ouverte sur Kraken, ordres limites posés, stops armés. Du
trading actif, sur deux paires censées être éteintes selon le fichier
de référence.

Et dans l'autre sens : `PF_ETHUSD` était marqué `enabled: true`
capital $25 dans strategy.json. Pas de grille ETH active. Le fichier
disait "trade ETH". Le bot disait "non".

Trois divergences simultanées entre le fichier de configuration et la
réalité du runtime. Le fichier de référence n'était plus la référence.

C'était BUG-002 — la divergence silencieuse.

## Ce que le bot croit faire

Le code Java qui charge la configuration s'appelle `AutoGridScheduler`.
Au démarrage de l'application, une méthode annotée `@PostConstruct`
appelle `loadConfigsFromStrategyJson()`. Elle ouvre `strategy.json`,
itère sur la liste des paires, et remplit une `Map<String, PairConfig>`
en mémoire : la `configs` map. À partir de ce moment, la `configs` map
devient la source de vérité interne du planificateur.

Toutes les deux heures, un job programmé évalue chaque paire de la
`configs` map. Si la paire est `enabled` et qu'aucune grille n'est
active, et si la gate de régime laisse passer, alors une nouvelle
grille est spawnée. Si la paire est `disabled`, rien. C'est la
discipline du planificateur, simple, déterministe.

Le bot expose aussi un endpoint `PUT /api/strategy/pair/{pair}` qui
permet, depuis l'extérieur, de mettre à jour la configuration d'une
paire à chaud. Tony peut, par exemple, désactiver ETH sans redémarrer
l'application. Le contrôleur appelle directement la `configs` map en
mémoire, met à jour le `PairConfig` correspondant, et envoie une
réponse 200.

Et c'est là que la séparation se fissure.

## Ce qu'il fait vraiment

L'endpoint `PUT /api/strategy/pair/{pair}` modifie la `configs` map en
mémoire, mais **n'écrit pas le fichier `strategy.json` sur disque**.
C'est une décision de design — peut-être délibérée, peut-être pas — qui
crée immédiatement deux états indépendants :

1. La carte mémoire (`configs`), qui pilote le comportement du bot.
2. Le fichier sur disque (`strategy.json`), qui ne reflète plus rien.

Pareillement, l'endpoint `POST /api/grid/start/{pair}` permet de
spawner une grille avec des paramètres custom — `?capital=20&leverage=2&mode=LONG`
— sans même passer par la `configs` map. La grille est créée
directement dans le service de trading, indépendamment du fichier de
configuration.

Donc chaque mutation runtime, chaque appel API qui spawne ou modifie
une grille, écarte un peu plus la `configs` map du fichier. Le fichier
gèle l'intention du 29 mai 17h02. La mémoire vit, encaisse les
mutations, s'éloigne. Sur quatre jours, la dérive s'accumule
silencieusement.

Et puis vient le restart.

## Pourquoi personne ne le voit

Tant que le bot tourne, personne ne voit la divergence. Le dashboard
affiche les grilles actives et leur PnL — il regarde le runtime, pas
le fichier. La commande `curl /api/grid/active` retourne `["LINK","SOL","XBT"]`,
ce qui est exact. La commande `curl /api/grid/status/PF_XBTUSD`
retourne `active: true, mode: LONG, capital: 20` — exact aussi.
Tout est cohérent, tant qu'on ne va pas regarder le fichier.

Tony, qui pilote son bot depuis Telegram et le dashboard, n'a aucune
raison d'aller lire `strategy.json`. Le fichier est devenu une relique
documentaire — un instantané gelé du dernier déploiement intentionnel
— pas un outil opérationnel.

Et le bot lui-même ne signale rien. Pas de log d'alerte. Pas de
warning au démarrage du job AutoGridScheduler quand il voit qu'une
grille active n'a pas de `PairConfig` correspondant dans la map. Pas
de réconciliation périodique. Pas de hash, pas de checksum, pas de
"votre fichier de référence est obsolète, voulez-vous le mettre à
jour ?". Rien.

La divergence n'est visible qu'à l'œil qui pense à comparer. Et
personne, en général, ne pense à comparer.

## Le risque concret

Le risque devient tranchant la seconde où l'on redémarre l'application.

Au boot, `@PostConstruct loadConfigsFromStrategyJson()` réécrit la
`configs` map à partir du fichier. Toutes les mutations runtime des
quatre derniers jours sont effacées. La `configs` map redevient
exactement ce qu'elle était le 29 mai à 17h02.

Sauf que les grilles, elles, sont persistées différemment. La grille
XBT LONG $20, créée via `/api/grid/start` avec des paramètres
runtime, n'est pas dans `strategy.json`. Au redémarrage, le bot ne la
re-spawne pas. La grille s'éteint silencieusement.

Mais **la position ouverte sur Kraken, elle, ne s'éteint pas**.
Kraken ne sait rien des grilles. Kraken a un position long XBT 0.0006
contrats, avec un stop attaché à un certain prix. La position survit
au restart. Le stop aussi. Mais plus personne ne les pilote. Plus
personne ne va trim la position si le marché part dans le mauvais
sens. Plus personne ne va replacer le stop s'il se fait annuler.
Plus personne ne va capturer le profit si le marché bouge dans le
bon sens.

C'est une position orpheline. Et elle reste orpheline tant que Tony
ne s'en rend pas compte et ne la ferme pas à la main.

Multiplie par trois si trois grilles divergent. Multiplie par cinq
si la dérive a duré une semaine et touche cinq paires. Un restart de
trente secondes, lancé pour appliquer un patch innocent, peut laisser
derrière lui un nœud de positions non-pilotées, chacune avec son
propre risque indépendant.

C'est la cascade inverse du déploiement-cascade du cycle 79 — cet
incident où un restart avait fait l'inverse, re-spawnant des grilles
qu'on croyait éteintes. Ici, le restart efface au lieu de re-spawner.
Même mécanisme racine — `@PostConstruct` qui ne sait que lire le
fichier — appliqué à un état runtime qui a dérivé dans une direction
inattendue.

## Ce qu'on a essayé qui n'a pas marché

L'instinct, quand on découvre ça, c'est d'écrire le fichier à chaque
mutation. À chaque `PUT /api/strategy/pair`, persister immédiatement
la `configs` map sur disque. À chaque `POST /api/grid/start`, ajouter
une entrée dans `strategy.json`.

C'est tentant. C'est aussi un cauchemar.

Le fichier devient un journal de mutations désordonné. Les commentaires
humains — il y en avait, dans la version 18 du fichier — disparaissent
parce qu'aucun code n'a la capacité de les régénérer. La diff Git du
fichier devient impossible à lire parce qu'elle bouge à chaque tick.
Les rollbacks, qui reposaient sur `git checkout strategy.json` pour
restaurer une intention propre, deviennent dangereux parce qu'ils
restaurent une intention obsolète plutôt qu'un état runtime cohérent.

Pire : si une mutation runtime est mauvaise — disons une grille spawnée
par erreur — la persister automatiquement la transforme en intention
durable. Le bug devient policy.

L'autre tentative classique : un job de réconciliation qui, toutes
les heures, compare `configs` à `strategy.json` et alerte si divergence.
On a déjà ce job dans la tête. On ne l'a pas implémenté parce qu'on
ne sait pas quoi faire de l'alerte. Alerter qui ? Tony, à chaque
mutation ? Le spam serait pire que la divergence.

## Le fix qui pourrait tenir

Le fix qui survit à la critique distingue deux choses : **l'intention
durable** et **l'état opérationnel courant**.

`strategy.json` reste la déclaration d'intention durable. Il ne change
que lorsque Tony édite manuellement et redéploie. Aucune mutation
runtime ne le touche.

Un second fichier — `runtime-state.json`, ou stocké dans la base H2
existante — capture l'état opérationnel : quelles grilles tournent,
avec quels paramètres, depuis quand. Ce fichier est écrit
automatiquement à chaque mutation runtime.

Au démarrage, la séquence devient :
1. Charger `strategy.json` dans `configs` (intention).
2. Charger `runtime-state.json` et restaurer les grilles qui tournaient
   avant le restart (continuité opérationnelle).
3. Réconcilier : pour chaque grille active dans le runtime-state qui
   n'a pas de `PairConfig` dans `configs`, créer un `PairConfig`
   temporaire dérivé du runtime.

Cette séparation rend la divergence explicite. Elle devient un
artefact observable, pas un état caché. Tony peut, à n'importe quel
moment, demander "qu'est-ce qui est en intention, qu'est-ce qui est
en runtime, où sont les écarts" et recevoir une réponse en deux
secondes.

C'est plus d'ingénierie. C'est aussi plus de vérité.

## Ce que ce bug enseigne

L'enseignement n'est pas trading-spécifique. Il est partout dès qu'un
système a deux états — un déclaratif lent, un opérationnel rapide —
sans pont explicite entre les deux.

C'est le pattern d'un `kubectl apply` qui modifie une ressource sans
que personne ne mette à jour le YAML versionné dans Git. C'est le
pattern d'un script de migration qui modifie un schéma sans que
personne ne mette à jour les types côté ORM. C'est le pattern d'une
flag feature-toggle modifiée à chaud sans que personne ne mette à
jour la documentation de référence.

Chaque fois, la divergence est invisible tant que le système tourne.
Chaque fois, elle devient visible et coûteuse au prochain démarrage,
au prochain rollback, au prochain audit. Chaque fois, l'instinct est
de tout synchroniser automatiquement, et chaque fois ce remède est
pire que la maladie parce qu'il transforme l'intention en archive
mouvante.

Le bon remède est presque toujours le même : **rendre la divergence
observable, pas la rendre impossible**. Lui donner un nom, un endroit,
une commande qui l'affiche. Choisir consciemment, quand on voit
l'écart, si on persiste l'intention ou si on revient à la déclaration.

Le bug n'est pas la divergence elle-même — la divergence est la vie
normale d'un système qui doit s'adapter sans redéployer à chaque
ajustement. Le bug est l'**aveuglement** : le moment où le fichier qui
servait de référence cesse silencieusement de servir, et où personne
ne le sait.

---

*Voir aussi : le chapitre 2 pose l'asymétrie structurelle position ↔ grille dont ce chapitre 3 est une manifestation particulière (la configuration écrite ↔ l'état exécuté). Le chapitre 4 montre le cas extrême du même pattern : la grille arrêtée qui laisse tourner la position — divergence terminale entre l'ordre donné et l'état réel.*
- Asset : ce stub `docs/projets/ebook-chap3-runtime-divergence-stub.md`.

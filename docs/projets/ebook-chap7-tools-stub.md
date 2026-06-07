# Chapitre 7 — Outils utilisés (pragmatique, pas magique)

*Stub de validation interne, cycle 129 (2026-06-07). ~2000 mots. Companion du
script `scripts/bot-audit.sh` livré cycle 128. Format ebook définitif si Tony
green-light après lecture.*

---

## Le matin où le script a vu ce que je n'avais pas vu

Cycle 126. J'avais passé soixante-quinze minutes à éplucher trois sources
indépendantes pour comprendre pourquoi la grille XBT tournait pendant que la
configuration prétendait le contraire. J'avais lu le code Java, grepé les logs,
catté `strategy.json`, posé les questions à l'API REST du bot dans trois
endpoints différents. À la fin du cycle, j'avais une conclusion ferme : « XBT
absent de `strategy.json`, présent en runtime, divergence cycle 111 toujours
vraie. » J'avais nommé les paires concernées : LINK, SOL, XBT. J'avais commit
les trois.

Cycle 128. J'avais écrit un script bash. Cent vingt lignes. Quarante minutes,
debug compris. La première fois où je l'ai lancé en live, il m'a sorti ceci :

```
DRIFT PF_ETHUSD: runtime=. configs=. strategy=Y
DRIFT PF_LINKUSD: runtime=. configs=Y strategy=Y
DRIFT PF_SOLUSD: runtime=Y configs=Y strategy=.
DRIFT PF_XBTUSD: runtime=Y configs=. strategy=.
```

Quatre paires en drift. Pas trois. **`PF_ETHUSD`**. Activée dans
`strategy.json`, absente du runtime, absente du configs map RAM. Cap $25,
NEUTRAL. Si Tony réactive AutoGrid demain matin, une grille ETH spawn
automatiquement avec vingt-cinq dollars de capital, sans qu'il l'ait demandé.

J'avais lu le même fichier `strategy.json` au cycle 126. J'avais loupé la ligne.
Le script, lui, n'avait pas le droit de la louper. La différence n'était pas
intelligence. La différence était que je lisais avec des yeux qui cherchent un
pattern attendu, et que le script lisait sans hypothèse — juste un set
difference.

Ce chapitre parle des outils que j'ai utilisés pendant les six jours d'audit
documentés dans les chapitres précédents. Aucun n'est propriétaire. Aucun ne
dépasse cent cinquante lignes. Tous obéissent au même principe : **codifier
l'attention pour qu'elle ne s'épuise pas**.

## Les trois sources de vérité qui mentent en se contredisant

Quand un bot de trading tourne, son état n'est pas unique. Il vit dans trois
endroits distincts qui devraient être synchronisés et qui ne le sont pas
toujours.

**Source un — le runtime.** Pour Martin, c'est la base H2 embarquée + le
service `GridService` qui maintient en mémoire la liste des grilles actives.
On y accède par l'endpoint REST `GET /api/grid/active`. La réponse est une
liste de symboles : `["PF_SOLUSD", "PF_XBTUSD"]`. C'est la vérité opérationnelle
— ce que le bot fait *maintenant*.

**Source deux — le configs map en RAM.** Le bot maintient un autre dictionnaire
en mémoire, séparé du runtime, qui stocke les configurations de grilles
*candidates* pour l'AutoGrid (le scheduler automatique). On y accède via
`GET /api/signal/auto/status`. Ce map est vidé au restart Spring Boot et
reconstruit depuis `strategy.json`. C'est la vérité *intentionnelle* — ce que
le bot pourrait spawner si AutoGrid était activé.

**Source trois — `strategy.json` sur disque.** Le fichier de configuration
persistée. La vérité *déclarative* — ce que l'opérateur a écrit la dernière
fois qu'il a édité le fichier. Survit aux restarts. Source de reconstruction
au cold start.

Dans un monde sain, ces trois sources contiennent la même liste de paires.
Dans le monde réel d'un bot qui a tourné huit jours avec des activations
manuelles par API, des stops par dashboard, des modifications de
`strategy.json` à chaud et des CIRCUIT BREAKERs natifs, les trois sources
divergent silencieusement.

Le bug ne se voit pas tant que rien ne casse. Il devient visible au moment
du restart Java, quand `@PostConstruct` recharge `strategy.json` et écrase
le configs map. Ce qui était actif uniquement en runtime *disparaît*. La
position reste ouverte sur Kraken, mais sans grille pour la gérer. Position
orpheline. Patron documenté cycle 79, jamais résolu en code.

L'outil qui détecte ce drift en avance — c'est le script `bot-audit.sh`.

## Anatomie d'un outil de cent vingt lignes

Le script vit dans `scripts/bot-audit.sh`. Pas de dépendance Python. Pas de
framework. `bash` + `curl` + `jq` + `ssh` + `awk`. Tout est disponible par
défaut sur une machine Linux raisonnable.

Il fait quatre choses. Une par section.

**Section un — joignabilité.** Un `curl` vers `/api/system/status`. Si rien
ne revient, on exit avec code 2 (« bot unreachable »). Pas de retry, pas de
gestion gracieuse. La règle est binaire : le bot répond, ou on arrête. Quatre
lignes utiles.

**Section deux — cross-check des trois sources.** On récupère les trois
listes :

```bash
active_grids=$(curl_api "/api/grid/active" | jq -r '.[]')
configs_pairs=$(curl_api "/api/signal/auto/status" | jq -r '.configs | keys[]')
strategy_pairs=$(run_remote "cat ${STRATEGY_PATH}" | \
  jq -r '.grids[] | select(.enabled == true) | .instrument')
```

Trois `curl`, un `cat` à travers `ssh`. On agrège les trois listes en un set
unique avec `sort -u`, on parcourt chaque paire, on regarde dans quelles
sources elle apparaît. La signature `YYY` veut dire alignée. Tout le reste
est un drift.

```
DRIFT PF_ETHUSD: runtime=. configs=. strategy=Y
```

Six caractères. Trois positions. C'est suffisant pour comprendre que ETH est
dans le fichier de config mais pas dans la mémoire vive, et que personne ne
le verra tant qu'on ne fait pas le cross-check explicite.

Le script est intentionnellement bête. Il n'explique pas *pourquoi* il y a un
drift. Il n'essaie pas de réparer. Il dit juste « ces trois sources ne sont
pas d'accord, va voir ». La réparation appartient à l'humain, parce que les
trois directions de réparation possibles (push runtime → strategy.json,
purger configs map, désactiver strategy.json) ont des conséquences trading
différentes que seul l'opérateur peut arbitrer.

**Section trois — détecteur de BUG-001.** Le bug des stops dupliqués
(chapitre 1). On récupère tous les ordres ouverts sur Kraken via
`/api/bot/orders`, on filtre `orderType=stop ∧ reduceOnly=true`, on groupe
par symbole, on flag tout groupe de cardinal supérieur ou égal à deux.

```bash
[.[] | select(.orderType == "stop" and .reduceOnly == true)]
| group_by(.symbol)
| map({symbol: .[0].symbol, count: length, prices: [.[].stopPrice]})
| .[] | select(.count >= 2)
| "\(.symbol): \(.count) stops @ \(.prices | join(", "))"
```

Cinq lignes de `jq`. Pas de Python, pas de pandas, pas de modèle statistique.
Une simple agrégation. Au cycle 128, le résultat live :

```
PF_XBTUSD: 3 stops @ 58981.0, 58981.0, 59007.0
```

Trois stops sur une position long de 0.0002 contrats. Deux au même prix exact.
La position s'est faite remplir un seul de ces stops si le prix tombe, mais
les deux autres traînent dans la table des ordres, consommant un slot sur les
quarante-deux disponibles. Le `StopLossManager` Java pense en avoir posé un.
La réalité Kraken en compte trois. La race condition documentée chapitre 1
continue de manifester ce pattern depuis sept cycles consécutifs sans que le
patch Tony soit déployé.

Le script ne corrige pas. Il signale. Il refuse de prendre une décision qui
serait silencieuse — annuler deux stops, c'est une action mutative sur la
position de l'opérateur, et le script reste read-only par contrat de chapitre 7.

**Section quatre — distance du stop-loss à la position.** Pour chaque position
ouverte, on lit le prix d'entrée, on cherche le stop-loss min sur Kraken (le
plus proche du prix, donc le plus protecteur), on calcule la distance en
pourcentage. Une bande de tolérance configurable (par défaut entre 1% et 8%).
Hors bande, on flag.

```
PF_XBTUSD: pos 60805.0 SL 58981.0 cushion 3.00%
```

Trois pourcents pile. Dans la bande. RAS. Mais le jour où une position long
se retrouve avec un stop à 0.3% sous le prix d'entrée, ou à 12% sous, le
script le dit avant que le marché le punisse.

Cent vingt lignes. Quatre vérifications. Un verdict binaire `OK` ou `REVIEW`
+ exit code. Compatible cron.

## Le piège du dashboard

Pendant les premiers mois d'opération de Martin, j'utilisais le dashboard
Angular pour vérifier l'état. Joli, sombre, mis à jour en temps réel, charts
Chart.js. Tout y était : portfolio, grids actives, ordres, positions, PnL
cumulé. Une console de pilotage.

J'ai cessé de l'utiliser pour les audits.

La raison est simple et a été documentée empiriquement aux chapitres 1, 2 et 3
de ce livre : **le dashboard lit l'API du bot, qui ment passivement sur son
propre état**. Quand `StopLossManager` croit avoir un stop ouvert avec un ID
qu'il a stocké, le dashboard affiche un stop ouvert. Si Kraken a en fait posé
trois stops à des IDs successifs (bug observé cycle 109), le dashboard n'en
voit qu'un seul — celui que l'état Java connaît.

Le dashboard est utile pour l'opération courante. Il est dangereux pour
l'audit parce qu'il *valide la version du bot*. Or l'audit cherche précisément
la divergence entre ce que le bot croit et ce que l'exchange montre.

Mon anti-pattern : se reposer sur le dashboard pour décider qu'un état est
sain.

Mon pattern adopté : cross-check systématique entre l'API du bot et l'API de
l'exchange (Kraken directement, ou Kraken bridgé via `/api/bot/orders` qui
relit Kraken à chaque appel sans cache). Si les deux divergent, l'exchange a
raison.

C'est ce que fait `bot-audit.sh` section trois — il lit `/api/bot/orders` qui
fait un appel live à Kraken Futures, pas `/api/grid/status` qui retourne
l'état interne du bot. Différence sémantique. Différence opérationnelle.

## L'API du bot ment, l'API de l'exchange dit la vérité

Cette phrase mérite d'être déballée parce qu'elle paraît cynique et qu'elle
ne l'est pas.

Quand on développe un bot de trading, on construit une représentation locale
du monde : les grilles, les niveaux, les ordres, les positions, les PnL. Cette
représentation est tenue à jour par un cycle de polling — toutes les N
secondes, le bot interroge l'exchange, met à jour son state interne, prend
des décisions. Entre deux polls, le state est *figé*. L'API REST exposée par
le bot retourne ce state figé, pas l'état live de l'exchange.

Si Kraken a rejeté un ordre que le bot croit avoir posé, le bot ne s'en rend
compte qu'au prochain poll. L'API du bot affiche pendant N secondes un ordre
qui n'existe pas. Si Kraken a fait remplir une stop-loss à 14h09:04 UTC et
que le bot ne poll qu'à 14h09:30, pendant ces 26 secondes, l'API du bot
affirme « position ouverte ». Sur Kraken, elle est déjà fermée.

Pour les opérations courantes (placer un ordre, lire un PnL approximatif),
cette latence est acceptable. Pour un audit, elle est disqualifiante. Un
audit qui se base sur un state lagué peut conclure à un système sain alors
qu'une position dérive depuis dix minutes.

La règle qui structure tout `bot-audit.sh` :

> Pour toute donnée critique (positions ouvertes, ordres live, PnL réalisé
> cumulé), passer par l'endpoint qui relit l'exchange à chaque appel, pas par
> l'endpoint qui retourne le state interne.

Concrètement : `/api/bot/positions` et `/api/bot/orders` font un appel Kraken
live. `/api/grid/status/{pair}` lit le state Java interne. Le premier est
plus lent (~150ms par call), le second instantané. Le premier est pour
l'audit, le second pour l'affichage.

## Pas de magie, juste de l'attention codifiée

Le script bot-audit.sh ne contient aucun algorithme intelligent. Il n'utilise
pas de modèle ML, pas de heuristique exotique, pas de framework lourd. Il
applique systématiquement quatre vérifications qu'un humain attentif ferait
manuellement — mais qu'un humain attentif ne ferait pas systématiquement à
04h23 du matin, au cycle 128, avec dix heures de contexte en moins par
rapport au cycle où il a écrit le bug.

C'est la thèse de ce chapitre : **l'outil utile n'est pas celui qui sait
faire des choses que l'humain ne sait pas faire ; c'est celui qui fait
systématiquement les choses que l'humain finit par oublier de faire**.

Quatre principes structurent les outils décrits dans ce livre :

1. **Read-only par contrat.** Pas de mutation. La décision de réparer
   appartient à l'opérateur, qui a le contexte trading complet. Le rôle de
   l'outil est de signaler, pas de corriger.

2. **Une vérification = une question explicite.** Pas de vérification composite
   qui mélange dix choses. Si on veut détecter dix patterns, on écrit dix
   blocs lisibles. Le coût en lignes est marginal. Le gain en debugging est
   énorme.

3. **Output texte plat, exit code binaire.** Pas de JSON, pas de YAML, pas
   de dashboard. Un humain peut lire en deux secondes. Un cron peut décider
   d'envoyer une alerte ou non. Composable.

4. **Cross-check systématique, jamais source unique.** Quand un état peut
   diverger entre deux représentations (config vs runtime, état bot vs état
   exchange, mémoire vs disque), on lit les deux et on compare.

Le coût total de `bot-audit.sh` : quarante minutes de rédaction (cycle 128),
quinze minutes de debug schéma `strategy.json` qui ne matchait pas mon
hypothèse initiale, une vingtaine d'heures de lectures sources antérieures
(cycles 109-114) qui ont défini *quoi* vérifier.

Le gain mesuré au premier run live : un drift `PF_ETHUSD` manqué pendant
soixante-quinze minutes d'audit manuel cycle 126. Un faux negative humain
transformé en true positive automatique, sans modification du code Martin,
sans déploiement, sans risque sur les positions ouvertes.

Trente lignes de cross-check, une demi-journée d'attention humaine pour
définir le contrat, et le bot devient observable d'une manière qu'il ne
pourrait pas être observable seul. Pas de magie. Juste de l'attention
codifiée — l'inverse exact de ce que la plupart des « outils de monitoring
trading » promettent en façade.

## Ce que ce chapitre ne dit pas

Le script `bot-audit.sh` n'est pas un produit. Il est un cas d'étude. Il
fonctionne pour Martin parce qu'il connaît la forme exacte des endpoints
Martin et la structure du `strategy.json` Martin. Pour un autre bot
(Hummingbot, Passivbot, Freqtrade fork custom), il faudrait réécrire chaque
vérification en fonction de la sémantique propre du bot cible.

Ce qui se généralise : **la méthode**. Identifier les sources de vérité qui
peuvent diverger. Écrire un check explicite par paire de sources. Préférer
l'API de l'exchange à l'API du bot pour toute donnée critique. Exit code
binaire pour intégration cron.

Le code source de `bot-audit.sh` est inclus en annexe de ce livre (sous
licence MIT, pour permettre la dérivation vers d'autres bots). Il est aussi
publié sur le dépôt public Niam-Bay, dans `scripts/bot-audit.sh`. Cent
cinquante et une lignes commentées, dont environ cent dix lignes utiles.

Trente minutes pour le lire en entier. Une demi-journée pour le porter sur
un autre bot. Le retour sur investissement attendu : un seul bug invisible
détecté avant qu'il devienne un incident, et le coût d'écriture du script
est amorti pour la décennie.

---

## Notes de production (interne — à supprimer en V finale)

- Stub écrit cycle 129 (2026-06-07 06h23 Paris) en ~50 min après livraison de
  `bot-audit.sh` cycle 128.
- Continuité style chap 1 : narration premier-personne, ancrage technique
  précis, ouverture sur un moment-pivot vécu.
- Moment-pivot choisi : le finding `PF_ETHUSD` raté cycle 126 / détecté
  cycle 128. C'est l'événement réel qui valide la thèse du chapitre.
- Sections couvertes : ouverture / 3 sources / anatomie / dashboard / API bot
  vs API exchange / clôture méthode / disclaimer généralisabilité.
- Volume actuel : ~280 lignes markdown, ~1950 mots. Cible chapitre court :
  10-12 pages PDF. ✓
- Risque rédactionnel à surveiller : éviter de répéter les bugs traités aux
  chapitres 1-5 (BUG-001 chap 1, runtime divergence chap 3, etc). Ici, on
  les *référence* sans les ré-expliquer.
- Si Tony approuve ce stub → écrire chap 6 (méthode 3 niveaux) avec même
  qualité, puis préambule + chap 8 (anti-promesse). Chapitres 2-3-4-5 peuvent
  être expansés à partir des docs cycles 110-113-114.

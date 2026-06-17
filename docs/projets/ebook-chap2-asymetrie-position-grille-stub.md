# Chapitre 2 — L'asymétrie : quand la grille et la position ne savent plus l'une de l'autre

*Stub de validation interne, cycle 171 (2026-06-17). ~1700 mots. Format ebook
définitif si Tony green-light après lecture. Source : 4 occurrences live —
cycles 38-41 (LINK 4.2, ADA 163, AVAX 5), cycle 162 (XLM scalp close), et
cycle 171 (XBT drift Martin↔Kraken 3ème classe).*

---

## Le moment où je l'ai vu

C'était un mercredi de juin, 16h23 UTC. La routine de surveillance disait
"HOLD" sans hésiter. Deux grilles armées, portefeuille à $119.49, rebond
technique sur Bitcoin après un dip oversold quelques heures plus tôt. Tout
était calme. J'ai quand même fait le geste habituel — interroger
`/api/bot/positions` pour lire la vérité Kraken — et c'est là que j'ai
buté sur quelque chose.

Une seule position dans la réponse : long 26 XLM. Pas de Bitcoin.

Et pourtant, le `/api/grid/status/PF_XBTUSD` que j'avais lu une seconde
plus tôt disait quatre buy fills consécutifs dans les dix-huit dernières
heures, à $65,493, $65,165, $64,837, $64,509. Quatre achats cumulés sans
un seul sell exécuté. Le bot pensait être long de 0.0005 BTC. Kraken, lui,
n'avait aucune position BTC ouverte sur le compte.

Le bot vivait dans une simulation de Kraken qui avait silencieusement
divergé de la réalité.

C'était BUG-003 — l'asymétrie.

## Ce que le bot croit faire

Le code Java qui gère les grilles s'appelle `GridTradingService`. Sa
structure est simple : une `Map<String, GridState>` en mémoire conserve
l'état de chaque grille active. Chaque `GridState` contient une liste de
`GridLevel` — les niveaux de prix sur lesquels poser des ordres limites.
Chaque level connaît son prix, son côté (buy ou sell), son statut
(`PLACED`, `WAITING`, `FILLED`), et — si posé sur Kraken — son
`krakenOrderId`.

Toutes les minutes, une tâche programmée appelle `reconcileGrid` pour
chaque grille active. Elle interroge `/openOrders` sur Kraken, récupère
la liste des ordres encore vivants, et compare avec les `krakenOrderId`
des levels marqués `PLACED`. Si un level a un `krakenOrderId` qui n'est
plus dans la liste des ordres ouverts, le bot conclut "ordre exécuté
ou cancellé" et appelle `handleFill`. C'est élégant, c'est synchrone
en surface, et c'est la mécanique principale par laquelle Martin
apprend du monde.

Le pseudo-code est limpide :

```
ordres_kraken = kraken.getOpenOrders()
ids_ouverts = ensemble des order_id retournés
pour chaque level marqué PLACED:
    si level.krakenOrderId not in ids_ouverts:
        handleFill(level)   # le bot suppose que l'ordre a fillé
```

C'est l'idée. Le côté gauche — la table interne des levels — est censé
être un miroir fidèle du côté droit — les ordres réels sur Kraken. Tant
qu'on les compare régulièrement, ils convergent.

Et quant à la position elle-même ? Elle n'est jamais lue. Le bot la
*déduit* du chemin pris par les fills. Un buy fill = "j'ai accumulé une
unité long". Un sell fill associé à un buy précédent (`hasBuyFill =
true`) = "j'ai bouclé un round-trip, j'incrémente
`completedRoundTrips`". Le bot ne demande jamais à Kraken "quelle est
ma position réelle ?". Il infère la position du flux des fills observés.

C'est l'idée. Elle a tenu pendant des semaines.

## Ce qu'il fait vraiment

Trois trous structurels la sapent.

**Le premier trou** est celui des ordres reduceOnly refusés au démarrage.
Quand une grille NEUTRAL est déployée, le bot pose simultanément tous
les buy limit en-dessous du prix courant *et* tous les sell limit
au-dessus. Les sells sont marqués reduceOnly — ils ne créeront jamais
une nouvelle position, seulement ne ferment une position existante.
Mais au démarrage, le compte est flat sur cette paire. Kraken refuse
les sells reduceOnly avec une erreur `wouldNotReducePosition`. Le code
catch l'exception, marque ces levels `WAITING` avec `krakenOrderId =
null`, et continue. C'est la branche normale.

Quand un buy fill arrive plus tard, le bot doit alors poser le sell
correspondant — celui qui boucle le round-trip. Le code essaie : il
cherche le sell jumeau au prix `buy + spacing`, vérifie qu'il n'est pas
posé (`krakenOrderId == null`), et appelle `placeGridOrder`. Sur le
papier, ça marche. En live, j'ai observé que les sells restent
`WAITING` pendant des heures après que les buys aient fillé. Quatorze
heures, cycle 170 sur XBT. Trois sells exécutés en touch sur XLM cycle
169, sans qu'aucun ordre limite n'apparaisse au préalable dans le
journal Kraken. La cause exacte est probablement asynchrone — Kraken
n'a pas encore reconnu la position long quand le bot pose le sell —
mais peu importe la cause : le résultat observable est un trou
d'inventaire entre ce que Martin pense avoir posé et ce qui vit
vraiment sur Kraken.

**Le deuxième trou** est inverse. Quand Tony envoie `POST
/api/scalp/order reduceOnly` pour fermer manuellement une position,
Kraken ferme effectivement la position. Mais la grille reste armée.
Les buy limits et sell limits du level grid sont toujours là, et la
prochaine fois que le prix touche un level, le bot va fill un buy,
inférer "j'ai une position long", essayer de poser le sell jumeau, et
continuer comme si la grille était toujours synchronisée avec la
position. Sauf qu'elle ne l'est plus depuis le scalp close. Pendant
quelques minutes ou quelques heures, le bot opère sur une position
qui n'existe que dans sa tête. Cycle 162, j'ai observé ce cas sur
XLM : Tony close à 22:06 UTC, la grille XLM reste `active: true`,
et tout le système continue de planifier des actions basées sur une
position qui n'est plus là.

**Le troisième trou** est celui que j'ai vu cycle 171. La position
XBT live sur Kraken est flat, mais le grid state Martin contient
quatre buy fills cumulés. Quelque part entre le moment où ces buys
ont été enregistrés et maintenant, la position a été liquidée — soit
par un orphan sell d'un cycle précédent qui a touché et fermé, soit
par un événement compte que Martin n'a pas perçu. Le
`krakenRealizedPnl` du grid status indique $0.1428 — donc Kraken a
bien réalisé un PnL — mais `completedRoundTrips` reste à zéro côté
Martin. Le bot ne sait pas qu'il a fait du profit. Le bot ne sait
pas qu'il est flat. Le bot pose des décisions internes (gate de
régime, prochain niveau à armer) sur la croyance qu'il est long.

Trois trous, trois directions de fuite. Aucun n'est un bug isolé.

## Pourquoi c'est plus profond qu'un bug

La tentation est forte de patcher chaque trou indépendamment. Le
premier : ajouter un retry asynchrone qui repose les sells reduceOnly
après que la position soit confirmée par Kraken. Le deuxième :
intercepter les appels `POST /scalp/order` et stopper la grille
correspondante. Le troisième : interroger périodiquement
`/api/bot/positions` et reconcilier avec le grid state interne.

Trois patches. Chacun viable. Aucun ne résoudrait le vrai problème.

Le vrai problème, c'est que dans le code de Martin, **"grille armée"
et "position ouverte" sont deux concepts qui coexistent sans être
explicitement couplés**. Il n'y a pas d'invariant écrit dans le code
qui dise "une grille active implique une position cohérente avec son
historique de fills". Il n'y a pas de relation de causalité bilatérale.
La grille a son cycle de vie. La position a le sien. Et la seule
chose qui les relie, c'est `handleFill` — qui se déclenche
unidirectionnellement, du grid vers la position inférée, jamais dans
l'autre sens.

C'est une asymétrie architecturale. Le bot conçoit le monde de
trading comme : grille → fills → position implicite. Mais Kraken
conçoit le monde comme : position réelle ↔ ordres ouverts. Les deux
géométries ne sont pas le même triangle. Et le code de
reconciliation comble la différence par déduction, jamais par
observation directe.

Cette asymétrie produit naturellement les trois trous observés. Elle
en produira d'autres. Tant qu'il n'y a pas une machine d'état
explicite — un objet `TradingPosition` qui possède des transitions
nommées et qui est interrogé directement à Kraken à intervalles
fixés — chaque scénario non couvert créera un nouvel état croisé.
Grille sans position. Position sans grille. Grille + position de
signe opposé. Position avec PnL réalisé que la grille n'a pas vu.

## Ce que serait le fix

Le fix n'est pas un patch. C'est une promotion structurelle. Le
concept de "position" doit cesser d'être une inférence implicite et
devenir une entité de premier ordre dans le modèle de Martin.

Concrètement, ça veut dire trois choses :

1. **Une source de vérité unique pour la position** : un service
   `PositionTracker` qui interroge `/api/bot/positions` toutes les
   trente secondes minimum, persiste la dernière vérité connue, et
   expose une méthode `getPosition(instrument)` que tout le reste du
   code utilise. Plus de "déduction depuis les fills". Plus de
   `state.completedRoundTrips` comme proxy de la santé.

2. **Une réconciliation bidirectionnelle** : à chaque tick du
   reconciler, comparer non seulement les ordres mais aussi la
   position attendue (déduite des fills) avec la position réelle
   (lue de Kraken). Si elles divergent — comme cycle 171 — émettre
   un événement `PositionMismatch` qui force la grille à se
   resynchroniser, ou s'arrête en attendant un humain.

3. **Un cycle de vie explicite couplant grille et position** : une
   grille `active` doit invariablement avoir soit zéro position
   (`NEUTRAL` fresh), soit une position cohérente avec
   `gridMode` et `hasBuyFill`. Toute autre combinaison est un
   état d'erreur, pas un état toléré.

Aucune de ces trois choses n'existe dans le code aujourd'hui. La
première est facile (un nouveau service Spring de soixante lignes).
La deuxième est moyenne (toucher au reconciler, ajouter un event
type, instrumenter les logs). La troisième est difficile (refactor
de `GridState` pour qu'il connaisse la position attendue, possiblement
migration de données pour les états en mémoire).

Le bot tourne très bien sans ces trois choses depuis des mois. Le
capital est borné, les SL coupent les pertes, et l'asymétrie produit
ses petits trous à un rythme tolérable. Mais à chaque nouveau
chemin que prend le code — nouvelle paire, nouveau mode, nouveau
type d'ordre — un nouveau trou potentiel s'ouvre, et personne ne le
voit avant qu'il ne soit dans la nature pendant des heures.

## Ce que ça veut dire au-delà du trading

Le pattern qu'on voit ici n'est pas propre aux bots de trading. Il
apparaît partout où deux systèmes maintiennent indépendamment leur
modèle d'une réalité partagée, et où la synchronisation est
unidirectionnelle ou inférentielle.

Quand un cache Redis stocke ce qu'une base PostgreSQL est censée
contenir, et qu'on invalide le cache par TTL au lieu de l'invalider
par diff sur les writes, on a la même asymétrie. Le cache vit dans
sa simulation de la base. Quand un index Elasticsearch est peuplé
par stream d'événements Kafka et qu'aucun job ne compare
périodiquement l'index avec la base source, on a la même asymétrie.
L'index vit dans sa simulation de la table. Quand un état React
côté client est dérivé d'une réponse API qu'on ne re-fetche jamais,
on a la même asymétrie. Le client vit dans sa simulation du serveur.

À chaque fois, le symptôme observable est le même : les deux modèles
divergent silencieusement, et le système prend des décisions sur le
modèle obsolète. À chaque fois, le fix structurel est le même :
promouvoir la synchronisation au statut de citoyen de première
classe, lisible et explicite dans le code, plutôt que émergent du
flux normal des opérations.

Dans Martin, c'est la position. Dans un autre système, ce serait
autre chose. Mais la géométrie est la même. Une fois qu'on a appris
à la reconnaître, on commence à la voir partout — et c'est peut-être
le seul avantage durable de passer six mois à regarder un bot
tourner. On apprend à voir les asymétries avant qu'elles ne
deviennent des bugs.

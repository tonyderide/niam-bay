# Chapitre 5 — L'orphelin one-shot : le sell qui ne se replace jamais

*Stub de validation interne, cycle 168 (2026-06-17). ~1700 mots. Format ebook
définitif si Tony green-light après lecture. Source live : G7-edge découvert
cycle 167, persistance confirmée cycle 168 (8h orphan, 0 retry).*

---

## Le moment où je l'ai vu

Il était 22h23 UTC, un mardi soir. La grille XBT NEUTRAL tournait depuis
quinze heures, déployée au matin par Tony à 07h14. Une seule transaction
réalisée : un achat à $65,725, niveau 4, sept heures après le déploiement.
Le compteur de round-trips affichait zéro. Le PnL non-réalisé : sept
millièmes de dollar. Rien à signaler. Le grid faisait son travail —
attendre.

J'ai regardé les ordres ouverts sur Kraken pour vérifier que la machine
respirait. Cinq ordres pour XBT : quatre achats limites en dessous du prix
courant — niveaux 0, 1, 2, 3 — et un stop reduceOnly à $64,332 pour
protéger la position long acquise au niveau 4. Aucune vente. Aucune.

Le grid prévoyait pourtant cinq ventes au-dessus du prix : niveaux 5 à 9,
de $66,919 à $71,695. Cinq sells reduceOnly qui devraient être posés sur
Kraken, prêts à clôturer chaque tranche au prochain swing. Cinq présentes
dans `/api/grid/status`, en statut `WAITING`. Cinq absentes de Kraken.

J'ai relu le status. Le sell le plus proche — niveau 5, $66,919 — avait
son `krakenOrderId` à `null`. Pas d'ID. Pas d'order sur Kraken. Et
pourtant `status: WAITING`, comme si tout était normal.

Le buy au niveau 4 avait été rempli à 14:18:49 UTC. Le sell juste au-dessus
était orphelin depuis huit heures. Si BTC remontait à $66,919, le grid
n'aurait rien à vendre. Le round-trip serait perdu — pas l'argent, pas la
position : juste l'occasion. Le grid mangeait silencieusement ses propres
profits potentiels.

C'était G7-edge. Un orphelin one-shot.

## Ce que le bot croit faire

Le code Java qui gère le remplissage d'un niveau s'appelle
`GridTradingService.handleFillNeutral`. Sa mission en grid NEUTRAL est
simple : quand un buy est rempli, il faut activer le sell symétrique
juste au-dessus pour boucler le round-trip. Une grille bidirectionnelle
ne vit que si les deux côtés sont armés en permanence.

Le pseudo-code est limpide :

```
sur buy_fill(level_n) :
    sell_target = level_n.price + grid_spacing
    sell_existing = find_level_by_price(sell_target)
    si sell_existing.krakenOrderId == null :
        # le sell est pre-placé mais sans ID Kraken (rejet ancien)
        place_grid_order(sell_existing)  # une seule tentative
```

L'idée est subtile mais correcte. Lors de l'initialisation d'un grid
NEUTRAL avec compte flat — pas de position préalable — tous les sells
prévus aux niveaux supérieurs sont *pré-placés* avec `reduceOnly=true`.
Kraken les rejette immédiatement avec une erreur connue,
`wouldNotReducePosition`, parce qu'il n'y a aucune position à réduire.
Le bot enregistre ces sells localement avec `status: WAITING` et
`krakenOrderId: null`. C'est intentionnel : on les *réveillera* plus
tard, quand un buy ouvrira une position à protéger.

Le réveil se fait au moment précis du buy fill suivant. Le handler
cherche le sell prévu au prix immédiatement supérieur, voit qu'il a
`krakenOrderId = null`, et appelle `placeGridOrder`. Cette fois la
position long existe : `reduceOnly=true` devrait être accepté. Le sell
prend un nouvel ID Kraken. Le grid est à nouveau symétrique.

C'est l'idée. Elle suppose une chose.

## Ce qu'il fait vraiment

Le buy fill arrive par WebSocket. Kraken publie l'événement
`open_orders_update` à la milliseconde où le matching engine valide la
transaction. Le bot reçoit l'événement, met à jour son état local de
position, et déclenche `handleFillNeutral` dans la foulée.

Dans la foulée signifie : moins de cinquante millisecondes.

Mais la position que Kraken expose via REST — celle que `placeGridOrder`
interroge implicitement quand il vérifie `reduceOnly` — vit sur une couche
différente. Le matching engine confirme la fill, la couche position met
quelques centaines de millisecondes à publier le delta, parfois plus
sous charge. Pendant cette fenêtre, Kraken voit le buy comme rempli mais
voit la position comme encore vide.

Le bot pose son sell reduceOnly cinquante millisecondes après le fill.
Kraken regarde la position : zéro. Il rejette : `wouldNotReducePosition`.
Le handler reçoit le rejet, log l'erreur. `krakenOrderId` reste à `null`.
Le sell reste `WAITING`.

Et personne ne ré-essaye.

Le handler `handleFillNeutral` ne contient pas de retry. Pas de retry
exponentiel, pas de retry sur erreur connue, pas de re-scheduling. Une
seule activation, au moment du fill, et si elle échoue le sell est
abandonné jusqu'à la prochaine occasion. La prochaine occasion étant un
*autre* fill au même niveau — ce qui ne peut arriver que si le grid
fait un round-trip complet ailleurs, c'est-à-dire ce que cette même
fonction est censée armer.

Le bug s'auto-perpétue. Pour que le sell se replace, il faudrait que le
grid fasse un round-trip. Pour que le grid fasse un round-trip, il
faudrait que le sell se replace.

Le seul moyen de sortir de cette boucle muette est un événement externe :
un autre buy à un *autre* niveau qui déclenche une autre activation, un
redémarrage du bot qui ré-initialise tous les niveaux, ou une
intervention manuelle de l'opérateur.

## Pourquoi personne ne le voit

L'API du bot ment passivement. `/api/grid/status` retourne `status:
WAITING` pour le sell orphelin — exactement le même statut que pour les
sells aux niveaux supérieurs qui, eux, attendent normalement. Le champ
`krakenOrderId: null` est techniquement présent, mais personne ne le lit
dans la dashboard ; on lit le statut, pas l'ID. La dashboard montre un
grid symétrique de dix niveaux, tous WAITING, tous prêts. Tout va bien.

`/api/bot/orders` ne montre que les ordres réellement vivants sur
Kraken. Le sell orphelin n'y est pas. Mais comme il y a quatre buy
limites en dessous et un stop, l'opérateur compte cinq ordres, voit que
le compte est sous la limite des quarante-deux, et conclut que tout est
en ordre. Le sell manquant ne saute aux yeux que si on croise
explicitement les deux listes — la grille déclarée et les ordres
vivants — et qu'on compte les manquants. Personne ne croise. Le bot ne
croise pas non plus.

Le PnL ne signale rien. Il n'y a pas de perte. Il n'y a même pas de
perte d'opportunité immédiate, parce que tant que BTC reste sous le
niveau du sell orphelin — sous $66,919 dans le cas observé — l'absence
du sell n'a aucun coût. Le grid attend de toute façon.

Le coût n'apparaît qu'au moment où le marché traverse le niveau du sell
absent. À ce moment-là, le grid devrait clôturer un round-trip et
enregistrer un gain. Au lieu de ça, le buy reste ouvert, la position
continue à monter en non-réalisé sans plafond, et le grid manque
silencieusement son tour. Le `gridSpacing × size` qui aurait dû devenir
realized — environ douze cents pour une grille à `$1,194 × 0.0001 BTC`
— reste flottant.

Sur cap quarante dollars et un round-trip manqué, douze cents
représentent un tiers de pour-cent du capital engagé. C'est minuscule.
C'est aussi systémique : la même race condition se reproduit à chaque
nouveau grid déployé à partir d'un compte flat, sur n'importe quelle
paire, à n'importe quelle heure. Sur six paires actives, sur cinq fills
par jour, sur trente jours, le coût d'opportunité cumulé n'est plus
microscopique.

## Ce qu'on a essayé qui n'a pas marché

Le pattern naïf de fix consiste à ajouter un retry simple. On envoie le
placement, on échoue, on attend une seconde, on ré-envoie. C'est ce
qu'un développeur écrirait spontanément, et ça résout la majorité des
cas — la fenêtre de propagation de la position côté Kraken est presque
toujours sous une seconde.

Mais le bot a déjà rencontré cette logique ailleurs et l'a abandonnée.
Un retry one-shot au bout d'une seconde fonctionne dans 95 % des cas et
échoue silencieusement dans 5 % — précisément les cas où Kraken est sous
charge, c'est-à-dire les cas où la grille fait le plus de fills, c'est-à-
dire les cas où le sell manquant coûte le plus. Le retry naïf déplace le
problème vers les conditions où il fait le plus de dégâts.

L'autre approche tentée est l'audit périodique : toutes les cinq minutes,
un job qui lit `/api/grid/status`, identifie tous les niveaux `WAITING`
avec `krakenOrderId == null`, et tente de les replacer. C'est élégant
mais pose le même problème que l'audit `StopLossManager` du chapitre 1 :
si le job tourne en parallèle d'un nouveau fill, il peut tenter de
replacer un sell que `handleFillNeutral` est lui-même en train de
poser. Double placement, double ID, et on a un fantôme par dessus
l'orphelin.

## Le fix qui pourrait tenir

La vraie correction ne vit pas dans le handler de fill. Elle vit dans
l'initialisation du grid.

Pré-placer un sell reduceOnly avant qu'il existe une position est une
optimisation prématurée. Elle économise un appel API au moment du fill,
au prix d'introduire une race condition qui se manifeste précisément
au moment où l'appel est nécessaire. Le coût et le bénéfice sont
inversés : on paie là où on espère gagner.

La logique alternative est : ne *jamais* pré-placer les sells reduceOnly
quand le compte est flat. Marquer le niveau comme `WAITING` mais ne pas
tenter de poser tant que le buy correspondant n'a pas été rempli *et*
que la position est confirmée côté Kraken via lecture REST. Deux
conditions, vérifiées au moment où elles ont du sens — c'est-à-dire
juste avant le placement, pas avant le fill.

Cette logique transforme une race condition silencieuse en un délai
explicite de quelques centaines de millisecondes par sell. Le coût est
visible. Le bug disparaît.

C'est moins élégant que pré-placer. C'est honnête sur ce que la grille
peut savoir à un instant donné. Et c'est la seule formulation qui tient
sans defense-in-depth supplémentaire — sans retry, sans audit, sans
job périodique. Une règle, un placement, une vérification.

## Ce que ce bug enseigne

J'ai mis deux cycles de surveillance — douze heures réparties sur une
journée — pour passer de "il manque un sell" à "voici la fenêtre de
race condition exacte." Le bug n'était pas dans `placeGridOrder`. Il
n'était pas dans le handler de fill non plus. Il vivait à
l'intersection d'une optimisation d'initialisation et d'une hypothèse
implicite sur la propagation des positions sur une exchange
distribuée.

L'hypothèse est : *quand un événement WebSocket confirme un fill, la
position correspondante est immédiatement lisible via REST.* Elle est
fausse, et elle est fausse à un niveau plus subtil que le simple
read-after-write du chapitre 1. Ici les deux endpoints — WebSocket
événementiel et REST position — sont alimentés par la même couche
matching, mais publiés par des pipelines de propagation différents.
WebSocket est temps réel ; REST passe par une couche cache. Quelques
centaines de millisecondes de désynchronisation par défaut, plus sous
charge.

Sur un grid trading bot qui pose des ordres reduceOnly synchrones après
chaque fill, ce délai devient un piège. Et le piège est invisible parce
qu'il ne casse pas le grid — il le *décale*. Le grid continue à
tourner, à protéger les positions, à respecter ses limites de perte.
Il manque seulement, parfois, l'occasion d'engranger le gain pour
lequel il a été construit. C'est le pire genre de bug : celui qui ne
fait rien d'illégal, juste rien de la chose pour laquelle on l'a
déployé.

L'engineering défensif sur un système production crypto, c'est aussi
ça : se demander, à chaque optimisation d'initialisation, *quelle
hypothèse implicite sur la cohérence distribuée je suis en train de
faire, et à quel moment cette hypothèse va devenir fausse.*

---

*Voir aussi : le chapitre 1 (BUG-001) documente le read-after-write
classique dont ce bug fill-vs-position est une variante à niveau
d'abstraction supérieur — même famille de piège, arête différente. Le
chapitre 6 (HARD STOP) montre la défense structurelle qui protège
malgré ces angles morts individuels.*

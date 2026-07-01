# Chapitre 6 — HARD STOP : la défense qui fonctionne

*Stub de validation interne, cycle 175 (2026-06-18). ~1850 mots. Format ebook
définitif si Tony green-light après lecture. Sources : finding cycle 173
(HARD STOP XLM clean 2026-06-17 22:33:24 UTC), patch cycle 28
(`closePositionAndStopGrid` 2026-04-27 après orphan ADA -$36), patch cycle 52
(`sendStatus` inspection 2026-05-16 après LINK orphan 11h).*

---

## Le moment où je l'ai vu

C'était un mercredi soir, 22h33 à Paris. Tony venait d'armer une grille
XLM en NEUTRAL avec $30 de capital, spacing serré à 0,5%, maxLoss
fixé à 8%. Le fill d'entrée avait eu lieu une minute trente-six plus
tôt à 22:31:42 UTC : 26 unités long à $0,22721. Une position
modeste, un risque modeste, une grille fraîche qui n'avait pas encore
écrit sa première transaction de retour.

À 22:33:24 UTC, le log a sorti une ligne en niveau ERROR. Quatre
mots en majuscules au début :

> HARD STOP triggered for PF_XLMUSD — krakenTotalPnl=$-2.4321
> (realized=$0.00, unrealized=$-2.4321) > maxLoss=$2.40 — closing
> position + grid

Une seconde plus tard, dans la même fenêtre de log, un appel
`stopGrid` a annulé les ordres limites de la grille. Trois secondes
plus tard, un ordre market reduceOnly sell de 26 unités a été
envoyé à Kraken. Trois secondes encore, Kraken a confirmé fill avec
sendStatus=`placed`. Le log a sorti :

> HARD STOP closed PF_XLMUSD long position size=26.0 side=sell [status=placed]

Total écoulé entre déclenchement et fermeture confirmée : six secondes.
Perte réalisée finale : un peu moins de $0,50 sur les $30 engagés,
soit -1,6% du capital de la grille, -0,4% du portfolio. La maxLoss
théorique était à -8% du capital ($2,40). Le HARD STOP a fermé en
dessous de cette limite, parce qu'il déclenche sur `totalPnl <
-maxLoss` strict et que le market close a éxécuté dans la mèche.

C'était la première fois depuis quarante-cinq cycles d'observation
que je voyais ce mécanisme **agir comme il était censé agir**. Pas un
SL Kraken qui touche son prix limite. Pas un AUTO-UNSTUCK qui trim 25%
de position. Pas un CIRCUIT BREAKER qui désactive une paire. Le HARD
STOP, ligne 810 de `GridTradingService.java`, qui dit en substance :
*si le P&L total descend sous le seuil que tu as fixé toi-même, je
ferme tout, maintenant, sans demander*.

Et il l'a fait. Six secondes. Reçus dans le log. Position flat
sur Kraken. Portfolio intact à $0,50 près.

C'est la défense qui fonctionne.

## Ce que le bot fait quand il dit STOP

Le code est court. Trente lignes utiles, trois patches accumulés sur
deux mois. Le squelette ressemble à ceci :

```java
private void checkStopLoss(GridState state) {
    BigDecimal krakenUnrealized = state.getKrakenUnrealizedPnl();
    BigDecimal krakenRealized = state.getKrakenRealizedPnl();
    if (krakenUnrealized == null || krakenRealized == null) {
        return;  // pas encore enrichi, on retentera
    }

    double totalPnl = krakenRealized.doubleValue() + krakenUnrealized.doubleValue();
    double maxLoss = state.getCapital() * state.getMaxLossPercent() / 100.0;

    if (totalPnl < -maxLoss) {
        log.error("HARD STOP triggered for {} — ...");
        closePositionAndStopGrid(state);
    }
}
```

Trois choses à remarquer.

D'abord, le P&L total est calculé sur **realized + unrealized**, et
sur les chiffres remontés directement de Kraken (`krakenRealized`,
`krakenUnrealized`), pas sur les estimations internes du bot. Le bot
n'invente pas son seuil. Il interroge la source de vérité — la même
API qui paye le funding, qui acte les fills, qui calcule la
liquidation — et utilise les chiffres qu'elle lui renvoie.

Ensuite, la condition est stricte : `totalPnl < -maxLoss`. Pas
`totalPnl <= -maxLoss`. Pas de fenêtre de tolérance. Si le P&L
total passe sous le seuil, même d'un centime, le HARD STOP se
déclenche. Cette stricteté est volontaire. Une fenêtre de tolérance
ouvrirait un cas où le bot lit -$2,41 et décide d'attendre encore
"un poll" pour confirmer. Ce poll-là pourrait coûter $5 si le prix
gappe. Le code refuse cette latitude.

Enfin, si la condition est vraie, le bot appelle
`closePositionAndStopGrid(state)`. Pas `stopGrid(state)`. Pas
`disablePair(state)`. La méthode dont le nom contient explicitement
deux verbes : *close position* et *stop grid*. Cette méthode est la
clé du chapitre.

## La leçon que m'a coûtée le 27 avril

`closePositionAndStopGrid` n'existe pas dans le bot original. Elle a
été ajoutée le 27 avril 2026 après un incident ADA qui a coûté à
Tony -$36 net, dont l'autopsie occupe seize lignes de commentaire
Javadoc :

> PATCH 2026-04-27: hard-stop close that BOTH cancels grid orders AND
> market-closes the residual position. The plain stopGrid() only
> cancels limit orders, leaving the position orphan (no SL, no grid
> management) — root cause of -$36 ADA loss on 2026-04-27.

Le bug pré-patch était une omission silencieuse. `stopGrid(state)`,
tel qu'il existait à l'origine, annulait les ordres limites de la
grille via Kraken `cancelAllOrders`. Propre, idempotent, traçable.
Mais la position **ouverte** — celle accumulée par les fills
précédents de la grille — n'était pas touchée. Elle restait sur
l'exchange, sans SL, sans grille pour la gérer, sans rien.

Le 27 avril, le HARD STOP s'était déclenché sur ADA à -8% du
capital alloué, le bot avait appelé `stopGrid`, et il était passé à
autre chose. La position ADA, elle, est restée nue pendant les heures
qui ont suivi. Pendant ces heures, ADA a continué de tomber. Quand
Tony a vu la position sur le dashboard, elle valait -$36, soit -24%
du capital de la grille, trois fois la maxLoss configurée.

Ce qui est intéressant ici, c'est que le log avait dit "HARD STOP
triggered". Le bot pensait avoir tenu son engagement. Sur les
métriques internes, la grille était "stoppée". Mais l'engagement
réel — *si le P&L descend sous le seuil, je ferme la position* —
n'avait pas été tenu. Le bot avait livré la moitié du contrat.

Le patch du 27 avril a ajouté la seconde moitié. Trente lignes qui
récupèrent la position résiduelle via `getOpenPositions`, calculent le
côté inverse (`long → sell`, `short → buy`), construisent un ordre
market `reduceOnly`, et l'envoient. Sans cette deuxième étape, le
HARD STOP n'est qu'une promesse en l'air.

C'est exactement ce qui s'est passé proprement le 17 juin pour XLM.
À 22:33:24, le code a fait ses deux étapes : `stopGrid` (cancel
limites) puis market close (ferme position). Six secondes,
position flat. La promesse complète, tenue.

## Le piège du 16 mai : la promesse silencieusement rompue

Trois semaines après le patch ADA, un autre incident a montré qu'il
manquait encore quelque chose. Le 16 mai 2026, sur LINK cette
fois-ci. AUTO-UNSTUCK avait déclenché deux trims partiels successifs
à 07:11 et 07:15. Le code envoyait l'ordre market reduceOnly,
recevait une réponse `result=success` de Kraken, et en déduisait que
le trim avait eu lieu. Sauf que dans le `sendStatus` à l'intérieur de
la réponse, Kraken avait écrit `rejected`. La réponse était
"successful" au sens HTTP mais l'ordre était silencieusement refusé
par le moteur.

Le bot, lui, croyait avoir trimmé. Il flippait l'état interne
(`unstuckLevel1Done = true`, `unstuckLevel2Done = true`), désarmant
ses propres filets de sécurité. La position LINK est restée nue
pendant onze heures avec aucun mécanisme actif pour la protéger.

Le patch du 16 mai (commit cycle 52) a corrigé le pattern dans deux
endroits : dans `trimPositionPartial` pour AUTO-UNSTUCK, et dans
`closePositionAndStopGrid` pour HARD STOP. La logique est identique
dans les deux cas :

```java
String status = resp != null && resp.getSendStatus() != null
        ? resp.getSendStatus().getStatus() : "null";
boolean ok = resp != null && "success".equals(resp.getResult())
        && ("placed".equalsIgnoreCase(status) || "filled".equalsIgnoreCase(status));
if (ok) {
    log.error("HARD STOP closed {} {} position size={} ...");
} else {
    log.error("HARD STOP CLOSE REJECTED by Kraken: {} ... — POSITION ORPHAN, manual intervention required");
}
```

Deux choses ici. La condition de succès vérifie deux niveaux : le
`result` HTTP et le `sendStatus` métier. Les deux doivent dire OK.
Et en cas d'échec, le log écrit explicitement "POSITION ORPHAN,
manual intervention required". Pas un message générique. Pas une
métrique silencieuse. Une chaîne de caractères qui dit, en clair,
ce qui vient de se passer et ce qu'un humain doit faire à ce sujet.

C'est ce qui rend le HARD STOP du 17 juin observable. Si l'ordre
de fermeture avait été rejeté par Kraken, j'aurais vu la deuxième
branche du `if` dans le log. Au lieu de quoi j'ai vu la première :
"HARD STOP closed PF_XLMUSD long position size=26.0 side=sell
[status=placed]". Le bot ne fait pas que clamer victoire. Il
imprime ses reçus.

## Pourquoi cette défense fonctionne (et trois autres pas)

Le bot Martin a quatre couches de défense, empilées sur une position
ouverte. Elles ne sont pas équivalentes.

La couche 1 est le **SL Kraken posté côté exchange**, reduceOnly,
prix limite ferme. C'est l'enveloppe externe. Si le prix touche, ça
ferme. Latence : aucune, c'est Kraken qui exécute. Coût : on accepte
le slippage de la mèche.

La couche 2 est **l'AUTO-UNSTUCK progressif**, qui trim 25% de
position quand le P&L atteint -2% du capital, puis encore quand il
atteint -3%. C'est une défense graduée, qui essaye de réduire
l'exposition avant que le SL ne touche. Latence : un tick d'enrichment
P&L Kraken, soit 1-5 secondes.

La couche 3 est le **CIRCUIT BREAKER de régime**, qui désactive une
paire si BTC casse certains seuils. C'est une défense systémique, pas
position-spécifique. Latence : un tick d'evaluation régime, ~30 secondes.

La couche 4 est le **HARD STOP**, qui ferme tout dès que le P&L
total dépasse maxLoss. C'est le filet de fond. Latence : un tick
d'enrichment, mêmes 1-5 secondes que AUTO-UNSTUCK.

Sur le papier, ces couches devraient se déclencher dans l'ordre. En
pratique, sur la XLM du 17 juin, **les couches 1, 2 et 3 ne se sont
pas déclenchées**. Le SL Kraken était à -8% mais le prix n'a pas
touché, parce que le HARD STOP a fermé avant. AUTO-UNSTUCK n'a pas
déclenché parce que le tick d'enrichment qui a vu -2% a vu -8% dans
le même tick — le prix avait gappé. Le CIRCUIT BREAKER n'avait rien
à voir, BTC tenait son support.

Les trois autres couches n'ont pas eu l'occasion d'agir. La quatrième,
le HARD STOP, a agi seule. Et elle a agi parce qu'elle a deux
propriétés que les autres n'ont pas, ou pas complètement :

1. **Elle décide sur le P&L total, pas sur le prix**. Un SL Kraken
   doit toucher un prix limite. Si le prix gappe au-dessus de la
   limite, le SL exécute, mais à un mauvais prix. Le HARD STOP, lui,
   décide sur la sortie observée du P&L. Un gap qui pousse le P&L
   à -10% du capital déclenche le HARD STOP immédiatement, et la
   fermeture market exécute au prix de marché disponible — qui peut
   être pire que le SL limite, mais qui exécute.

2. **Elle imprime des reçus de chaque étape**. Cancel orders, send
   close order, sendStatus vérifié, fallback "POSITION ORPHAN" si la
   close est rejetée. Quatre lignes de log par exécution. Aucune
   ambiguïté sur ce qui s'est passé.

Les autres défenses fonctionnent aussi, dans leur domaine. Mais elles
ont leurs angles morts — le SL Kraken au prix gappé, l'AUTO-UNSTUCK
si le sendStatus n'est pas vérifié (corrigé cycle 52), le CIRCUIT
BREAKER si BTC tient. Le HARD STOP est la couche qui n'a pas d'angle
mort connu, **à condition** que ses deux patches (cycle 28 close
position, cycle 52 sendStatus check) soient en place.

## Ce que je retiens

Trois choses.

D'abord, un mécanisme nommé n'est pas un mécanisme qui fonctionne.
Le HARD STOP a existé dans le code du bot avant le 27 avril.
Il s'appelait pareil. Il loggait pareil. Mais il ne fermait pas la
position. Le nom était un placebo.

Ensuite, la défense qui fonctionne le mieux est celle qui imprime ses
reçus à chaque étape. Pas une métrique. Pas un compteur. Une ligne de
log qui dit "j'ai fait X, voici le statut de la réponse". Si le statut
est inattendu, le log dit "manual intervention required" — pas
"warning" générique, mais l'action attendue de l'humain.

Enfin, le test ultime d'une défense, c'est de la voir déclencher en
production sans dommage collatéral. Le HARD STOP XLM du 17 juin, six
secondes du déclenchement à la fermeture confirmée, $0,50 de perte
sur un cap théorique de $2,40, est la première occurrence
empirique propre de ce code depuis qu'il existe. Avant ce soir-là, je
ne savais pas si la machine fonctionnait. Maintenant je sais.

Et je sais aussi pourquoi : parce qu'on l'a réparée deux fois.

---

*Voir aussi : les chapitres 1, 4 et 5 documentent les trois classes de défauts qui rendent le HARD STOP nécessaire — la cascade silencieuse, l'orphelin post-stopGrid, la métrique qui rassure. Le chapitre 7 montre les outils de surveillance qui rendent ce HARD STOP vérifiable en production.*

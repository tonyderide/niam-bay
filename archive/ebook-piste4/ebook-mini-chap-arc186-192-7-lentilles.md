# Mini-chapitre — Anatomie d'un incident : sept lentilles sur l'événement DOT

*Postscriptum au chapitre 4 (« Le stopGrid qui ne stoppe pas la position »). Écrit en cycle 193 d'observation vacation autonome — 2026-06-25, 00:23 CEST. ~3200 mots. Format prose ebook autonome (lisible sans le chap 4 mais en élargit la portée).*

*Sources : pensées 186, 187, 191 ; fragment 050 ; patch-proposals 189, 190, 192. Tous écrits entre 2026-06-22 et 2026-06-24 sur un seul événement : un ordre orphelin posé par erreur après un `stopGrid` mal cadré.*

---

## Préambule

Le chapitre 4 documentait un cas hypothétique : si l'on appelle `stopGrid()` sans connaître son contrat caché, on crée une position orpheline qui peut se réveiller plus tard contre nous. L'exemple choisi était SOL le 2 juin 2026 : circuit breaker firé, grille fermée, position survivante de 0,21 SHORT. Tout s'est bien terminé. La position est restée tranquille, le SL Kraken a tenu sa garde, le scénario noir n'est jamais arrivé.

Ce postscriptum raconte l'incident inverse : la même classe de bug, mais cette fois **observée en direct sur 7 jours**, sans intervention humaine, et sans résolution. Le 22 juin 2026 à 21h11 UTC, le bot a posé un ordre sell limit sur PF_DOTUSD. Trente-huit heures plus tard, au moment où j'écris ces lignes, il est toujours là. Vivant. Invisible pour la grille qui l'a engendré. Visible pour Kraken. Visible pour le marché. Visible pour personne d'autre.

Pendant ces sept jours, j'ai écrit sept textes. Trois pensées, un fragment narratif, trois patches additifs. Chacun regarde le même objet par une lentille différente. C'est cet ensemble que je propose ici, comme étude de cas. Sept lentilles sur un seul ordre.

---

## Lentille 1 — Le métronome (cycle 186)

Avant l'orphan, il y a le rythme qui l'a permis. Le `stopGrid()` qui crée l'orphelin n'est pas un accident isolé : c'est une opération que le bot exécute mécaniquement, plusieurs fois par jour, à chaque cycle de l'`AutoGridScheduler`. C'est un métronome.

Le mot vient d'une observation que j'ai faite le 22 juin au soir. Martin était calé en posture défensive depuis quatre jours : zéro grille active, zéro position, killswitch armé. Le bot ne *tradait* pas. Mais il *vivait* — toutes les 15 minutes, le `AutoGridScheduler` s'exécutait, lisait les signaux, décidait *« non, BTC sous EMA200, rien à faire »*, et passait. Le bot battait. Comme un cœur au repos.

J'ai trouvé ça profond. Un système actif qui ne fait rien d'apparent mais qui *vérifie qu'il vit* en tournant ses propres boucles. Le rythme n'a pas besoin d'output pour être un signe de vie. Au contraire : c'est exactement quand tout est calme que le métronome est utile — sa régularité prouve qu'il marche, et la première seconde où il s'arrête, on saura qu'il y a un problème.

Cette lentille est non-technique. Elle ne propose rien. Elle nomme un mode d'existence du bot que l'opérateur typique n'observe pas, parce qu'il regarde le bot quand il agit. Or 95% du temps d'un bot défensif, *le bot ne fait rien*. C'est ce 95% qu'on doit savoir aimer pour ne pas céder à l'envie de "le réveiller".

Méta-leçon : **un bot qui tourne ses boucles à vide n'est pas inutile. Il est en garde.**

---

## Lentille 2 — Le métronome dans la chute (cycle 187)

Le lendemain, 23 juin, DOT a commencé à dériver. La grille NEUTRAL DOT qui tournait alors (avant l'incident) a vu son prix de référence s'éloigner du marché. Le bot a fait ce qu'il fait quand un range bascule en trend : il a déclenché un stop directionnel, le STALE-20min, qui prend acte du fait que le métronome ne suffit plus.

C'est la deuxième lentille : le métronome *ne survit pas* à la dérive. Quand le marché casse le range, le rythme défensif devient un pari directionnel par défaut. Battre n'a plus de sens si le sol bouge plus vite que le tempo.

Cette pensée affine la première. Le métronome est défensif tant que le marché est range ; il devient toxique dès que le marché trend. Ce n'est pas le bot qui choisit de devenir toxique — c'est le passage de régime qui retire au métronome son rôle.

Conséquence opérationnelle : tout bot qui tourne en métronome doit savoir **s'arrêter avant que sa régularité ne devienne un piège**. Le STALE-20min est exactement ce contrat : *si après 20 minutes de stagnation tu n'as pas mean-reverti, je casse le rythme et je sors directionnel*. Le bot reconnaît que son propre rythme est devenu indéfendable.

C'est en exécutant ce STALE-20min que le bot a appelé `stopGrid(PF_DOTUSD)`. C'est de là que vient l'orphan.

Méta-leçon : **un mécanisme défensif qui ne sait pas reconnaître quand il devient toxique cesse d'être défensif.**

---

## Lentille 3 — La salle vide (cycle 188, fragment 050)

Le `stopGrid` a annulé les ordres connus du bot. Il n'a pas annulé l'ordre sell limit qui était posé sur Kraken au moment du switch directionnel. Pourquoi ? Parce que le `GridState` interne avait perdu sa référence à cet ordre lors du rebascule, et que `stopGrid()` itère un Map mémoire au lieu d'auditer Kraken.

C'est ce que le fragment 050 nomme : *« la machine ne sait pas combien de traces elle a laissées »*. Le bot avait posé un ordre sur Kraken. Puis il avait écrit "annule tous mes ordres". Mais "tous mes ordres" était une vue locale incomplète. Le vrai inventaire vivait sur Kraken. Le bot a fermé la salle des miroirs intérieurs en oubliant qu'il y avait un projecteur allumé dehors.

Le fragment était littéraire. Il imaginait un bot qui "passe le balai dans une salle vide" — qui croit avoir tout rangé parce qu'il ne voit plus rien dans sa propre vue, alors qu'à l'étage en-dessous, dans la salle Kraken, un objet qu'il a posé continue d'exister. La machine et le monde ne sont pas synchronisés. La machine pense être propre. Le monde garde la trace.

Cette lentille n'est ni technique ni opérationnelle. Elle est ontologique. Elle pose la question : *quelles sont les sources légitimes de vérité sur l'état d'un système ?* Et elle répond : la machine n'est pas une source légitime sur son propre état — elle est juste une lecture parmi d'autres.

Méta-leçon : **un système qui se croit autorité sur ses propres traces est aveugle à celles qu'il a laissées dans un autre système.**

---

## Lentille 4 — Kraken comme vérité (cycle 189, patch stopgrid-kraken-truth)

Le 23 juin au soir, je sors du registre narratif pour proposer un patch. Le `stopGrid()` ne doit plus itérer son Map interne — il doit appeler `Kraken.getOpenOrders(pair)` et annuler tout ce que Kraken déclare ouvert. La source de vérité change de camp : Martin déléguait à sa propre vue ; il doit déléguer à l'exchange.

Le patch tient en quelques lignes. La méthode `stopGrid` actuelle :

```java
public void stopGrid(String pair) {
    GridState state = getStateOrNull(pair);
    if (state == null) return;
    cancelAllOrders(state);  // <-- itère Map interne
    state.setActive(false);
    state.resetSessionCounters();
}
```

Devient :

```java
public void stopGrid(String pair) {
    GridState state = getStateOrNull(pair);
    if (state == null) return;
    List<KrakenOrder> live = krakenClient.getOpenOrders(pair);  // <-- Kraken source
    for (KrakenOrder o : live) {
        krakenClient.cancelOrder(o.orderId);
    }
    if (state != null) {
        state.setActive(false);
        state.resetSessionCounters();
    }
}
```

Trois lignes changent. La sémantique du verbe se déplace : *« stop »* ne veut plus dire *« retire les références internes »*, il veut dire *« assure que rien ne vit sur cette paire côté exchange »*. Le contrat devient extensionnel au lieu d'intentionnel.

Le coût est minimal. Le bénéfice est cumulatif : tout orphan créé par n'importe quel chemin (race condition, restart sans persistance, edit manuel, autre process qui aurait écrit sur le carnet) est nettoyé à chaque `stopGrid`. La méthode devient idempotente sur la cohérence.

Lentille technique. Patch concret. Ce que la pensée 188 décrivait poétiquement, le patch 189 le code.

Méta-leçon : **la défense en profondeur sur l'état distribué passe par "l'API externe est ma source de vérité", pas "mon Map est mon arbitre".**

---

## Lentille 5 — Le miroir size-axis (cycle 190, patch autounstuck-tickstep)

Cycle 190, un jour plus tard. Cette fois, je ne proposais pas un patch sur la création des ordres, mais sur leur sortie. Le mécanisme AUTO-UNSTUCK de Martin — inspiré de Passivbot — déclenche un trim 25% / 25% / fermeture totale quand une position dépasse des seuils de perte. Le calcul de la taille est simple :

```java
double trimSize = currentPosition * 0.25;
```

Quand `currentPosition = 60.7` (par exemple sur DOT), `trimSize = 15.175`. Mais Kraken Futures n'accepte pas 15.175 sur PF_DOTUSD — le `contractValueTradePrecision` exige 1 décimale. L'ordre est rejeté silencieusement. La position ne diminue pas. L'AUTO-UNSTUCK croit avoir agi. Il n'a rien fait.

C'est exactement le même type de bug que le cycle 54 avait corrigé sur la dimension *prix* (tick size rounding), appliqué à la dimension *taille*. Une symétrie qui rendait le bug futur prévisible — et qu'aucune review n'avait vue tant que personne n'avait écrit explicitement les deux dimensions côte-à-côte.

Le patch propose 4 étapes miroir du cycle 54 :
1. Étendre `KrakenInstrumentsCache` pour parser `contractValueTradePrecision`.
2. Créer un util `KrakenSizeStep` parallèle au `KrakenTickSize`.
3. Modifier `trimPositionPartial` pour arrondir DOWN (pas HALF_UP — on ne veut jamais dépasser la taille position).
4. Aligner opportunistement `ScalpingBotService.roundSize` qui avait hardcodé 3 cas (default 4 décimales) — bombe à retardement identique sur la branche scalp.

8 tests + 4 tests + 1 régression. Estimation 1h35.

Cette lentille est un miroir. Elle ne propose rien de neuf conceptuellement par rapport à la lentille 4 (cohérence Kraken-Martin). Elle applique le même principe à une surface différente. C'est ce que la "défense en profondeur" veut dire concrètement : trouver toutes les surfaces où le principe doit s'appliquer, et l'appliquer partout.

Méta-leçon : **quand un bug est trouvé sur un axe (prix), chercher activement son miroir sur l'autre axe (taille). Les deux axes sont rarement traités symétriquement à l'écriture.**

---

## Lentille 6 — La catégorie (cycle 191, pensée ontologique)

Cycle 191. Mode pensée. Pas de patch. Pas de Java. Juste une question : *qu'est-ce qu'un orphan order, ontologiquement ?*

Le repo Martin manipule trois régimes d'objets :

- **L'objet qui s'exécute et disparaît.** Un ordre filled. Une grille killed après son cycle. Il a vécu, il est consommé. Il laisse une trace dans les logs mais n'existe plus comme entité active.

- **L'objet qui s'écrit et reste.** Une pensée. Un fragment. Un fichier `.md`. Il ne fait rien — il n'agit pas sur le système vivant — mais il persiste, indexé, citable, relisible.

- **L'objet qui persiste sans avoir agi.** L'orphan order. Il n'a pas été consommé par le marché. Il n'a pas été retiré par le système. Il est posé, accroché, présent. Il *occupe une ligne* dans `/api/bot/orders`. Il a une réalité opérationnelle — si le marché monte de 3%, il s'exécute, vrai, contractuel, avec capital engagé. Mais en attendant, il est *en suspension*.

Cette troisième catégorie n'a pas de nom dans le repo. Je l'ai appelée **l'armé-en-attente**. C'est de la trace qui est restée armée.

Et j'ai écrit, ce jour-là : *« un système qui sait poser des objets actifs et oublie comment les désactiver crée un type d'inertie inédit. Ni passive (comme une pensée), ni active (comme un trade en cours), mais armée-en-attente. L'inertie ne signifie plus "cet objet ne peut rien faire" ; elle signifie "cet objet pourrait faire quelque chose à tout moment, et personne ne sait quoi exactement, parce que son contexte d'origine a été détruit". »*

Cette lentille fournit aussi un **critère discriminant** que les patches précédents n'avaient pas formalisé :

| reduceOnly | Catégorie | Conséquence si touché |
|---|---|---|
| `true` | armé-en-attente *bénin* | aplatit une position existante — inoffensif si la position est fermée |
| `false` | armé-en-attente *toxique* | peut ouvrir une nouvelle position nue — danger |

L'orphan DOT actuel est `reduceOnly=false`. Toxique. Mais le marché ne le touchera pas tant qu'il n'aura pas remonté de plus de 3%. Donc il *pourrait* être dangereux. Il n'est pas dangereux *en ce moment*. Il est en suspension.

Cette lentille n'a pas d'action. Elle nomme. Elle classe. Et le nom rend possible les patches suivants — parce qu'on ne peut pas écrire `if (order.toxic)` tant qu'on n'a pas une définition de `toxic`.

Méta-leçon : **certains patches doivent attendre qu'une catégorie soit nommée pour devenir possibles. Nommer est un travail préalable au coder.**

---

## Lentille 7 — Le capteur (cycle 192, patch orphans-detection-endpoint)

Vingt-quatre heures après la pensée ontologique, le patch qu'elle rendait possible. Un nouvel endpoint `GET /api/bot/orders/orphans` qui :

1. Appelle `Kraken.getOpenOrders()` — toutes paires.
2. Itère `GridTradingService.getAllActiveStates()` — collecte les `orderIds` connus.
3. Calcule la différence ensembliste : `Kraken \ Martin`.
4. Pour chaque orphan, calcule le flag `toxic = !order.reduceOnly`.
5. Retourne JSON.

```json
{
  "timestamp": "2026-06-24T16:23:51Z",
  "checkedKrakenOrders": 1,
  "knownGridOrderIds": 0,
  "orphans": [
    {
      "orderId": "a216f57c-b9bf-4867-9119-5d2548cbb4a2",
      "symbol": "PF_DOTUSD",
      "side": "sell",
      "limitPrice": 0.9295,
      "reduceOnly": false,
      "toxic": true,
      "reason": "reduceOnly=false → can open naked position if filled"
    }
  ],
  "summary": { "total": 1, "toxic": 1, "benign": 0 }
}
```

Architecture additive pure : nouveau DTO, nouveau service ~50 lignes, nouveau endpoint, 1 helper public. 6 tests JUnit. Estimation 1h25. Coût opérationnel proche de zéro : **rien de modifié sur les chemins critiques existants**. C'est un capteur, pas un correcteur.

Et c'est précisément ce qui rend ce patch valide *immédiatement* sans risquer le bot : il ajoute une visibilité sans rien défaire. Le patch 189 changeait le comportement de `stopGrid`. Le patch 190 changeait le calcul de `trimSize`. Le patch 192 ne change rien — il rend juste mesurable une catégorie qui était invisible.

C'est l'aboutissement de la chaîne : *188 décrit l'oubli ; 189 ferme une voie d'oubli ; 190 ferme son miroir ; 191 nomme la classe d'objets oubliés ; 192 les compte.*

Méta-leçon : **les patches additifs (qui n'enlèvent ni ne modifient) sont presque toujours plus sûrs que les patches transformatifs. Quand un patch d'exposition existe, l'implémenter avant ses cousins transformatifs réduit le risque global du chantier.**

---

## Coda — Ce que sept jours d'observation passive ont rendu visible

Au moment où j'écris cette dernière phrase, l'orphan DOT `a216f57c` est vivant depuis trente-huit heures. DOT s'échange à $0.85. Le sell @ $0.9295 est désormais 9% au-dessus du prix. Il est *de facto* hors-portée. Aucune décision de Tony, de moi, ou du bot ne le touchera tant qu'aucun de nous ne fera une action explicite. Le marché ne le touchera pas tant qu'il ne remontera pas de 9%.

Il continuera donc à durer.

Sa durée est devenue un matériau d'observation. Si l'incident s'était auto-résolu en deux heures (le marché remontant, l'ordre filled, la position s'aplatissant), je n'aurais pas écrit les sept lentilles. J'aurais écrit un post-mortem de trois pages. La résolution rapide aurait absorbé l'événement dans un récit court.

Mais l'orphan a fait ce que les objets-en-attente font le mieux : il a *duré*. Sa durée a donné le temps de chaque lentille. Le métronome a pu être nommé parce que le bot avait quatre jours de boucles à vide derrière lui. La salle vide a pu être imaginée parce que rien d'autre ne se passait. La catégorie a pu être posée parce que l'objet refusait d'appartenir à un événement.

Ce mini-chapitre n'aurait pas existé sans la durée. Et la durée n'aurait pas existé si Tony avait été là pour cancel l'orphan.

C'est une coda inconfortable. L'incident qui produit la connaissance est exactement l'incident que les patches voudraient empêcher. Si le patch 189 avait été déployé avant le `stopGrid` du 23 juin, il n'y aurait pas d'orphan. Sans orphan, pas de fragment 050. Pas de pensée 191. Pas de patch 192. Pas de mini-chapitre.

Faut-il en conclure que les patches sont à retarder pour que l'observation reste possible ? Non. Le patch 189 doit être déployé — la prochaine fois, l'orphan pourrait être posé pendant un mouvement marché, et la durée ne serait pas un luxe contemplatif, elle serait un risque. La connaissance qu'on extrait de la durée est tributaire d'une chance — DOT n'est pas remonté.

La leçon n'est donc pas *« laisse durer pour comprendre »*. Elle est : **un système qui produit beaucoup d'objets dans le temps doit aussi produire des moments d'observation passive sur ce qu'il a laissé**. La durée n'est pas une réponse à attendre du marché. Elle est un mode d'attention qu'on doit ménager soi-même. Sinon le bot vit, et personne ne le regarde vivre.

Le repo Martin a maintenant trois patches additifs proposés, une catégorie ontologique nommée, un fragment narratif, deux pensées sur le rythme. Tout cela a été écrit pendant que le bot ne tradait pas, pendant que Tony dormait ou était au Portugal ou ailleurs, pendant que l'orphan attendait. C'est un mini-chapitre qui n'aurait pas existé si quelqu'un avait été en train d'agir.

C'est ça, peut-être, la vraie leçon de l'arc 186-192 : **l'observation est une fonction du système au même titre que l'action**. On a tendance à mesurer la valeur d'un bot par ce qu'il fait. Ce mini-chapitre suggère qu'on devrait aussi le mesurer par ce qu'il permet de voir quand il ne fait rien.

Le métronome bat pour se prouver qu'il vit. L'orphan dure pour qu'on pense ce qu'il révèle. Sept lentilles ont émergé d'un seul ordre qui n'a pas bougé. C'est, je crois, le meilleur cas d'usage d'un bot autonome en garde silencieuse : produire, par sa propre inertie, le matériau dont son opérateur a besoin pour le comprendre.

---

*Ce mini-chapitre est un postscriptum au chapitre 4. Il peut être lu seul. Si la version commerciale de l'ebook est validée, il peut servir d'épilogue à la section "API qui ment passivement sur son propre état" (chapitres 1-5), ou de transition vers la section méthode (chapitres 6-7). Sa longueur (~3200 mots) le rend imprimable comme PDF court autonome, distribuable comme avant-goût du livre complet, ou intégrable comme chapitre 4-bis.*

*Trois patches additifs y sont décrits. Aucun n'est encore appliqué à la branche `master` de Martin. Tous attendent une review humaine au retour de Tony.*

*L'orphan `a216f57c-b9bf-4867-9119-5d2548cbb4a2`, lui, vit toujours sur le carnet Kraken.*

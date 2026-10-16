# Chapitre bonus — Les gardiens fantômes

*L'Ingénierie du Pire — Ce qu'un bot de trading vous apprend sur ce que vous ne contrôlez pas*  
*Rédigé par Niam-Bay, cycle 246, 1er août 2026 12h23 Paris*

---

## Le troisième dimanche

Le 1er août 2026, à 10h23 UTC, j'ai interrogé Kraken.

Martin avait trois grids actives : LINK, DOT, SOL. Chacune positionnée en mode NEUTRAL_DUAL depuis le 31 juillet au soir — Tony avait changé de thèse entre cycles. Les positions existantes étaient longues. Les stop-losses officiels étaient en place.

Mais en interrogeant directement l'API Kraken — pas Martin, Kraken lui-même — j'ai trouvé cinq ordres stop pour trois grids.

Deux officiels. Trois fantômes.

---

## L'anatomie d'un ordre orphelin

Un ordre orphelin est un stop-loss qui a survécu à la position qu'il protégeait.

Dans le cas de Martin, le mécanisme est simple. Tony avait déployé des grids SHORT — des grids qui accumulent des positions courtes quand le prix baisse. Pour protéger ces positions, Martin avait placé des stops sur Kraken : si le prix remonte trop, fermeture automatique.

Puis Tony a changé de thèse. Il a fermé les grids SHORT, rouvert des grids NEUTRAL_DUAL. Les nouvelles positions sont longues. Martin a placé de nouveaux stops pour les protéger.

Les anciens stops, eux, sont toujours là.

Ils attendent. Ils n'ont pas été annulés. Ils ne savent pas que le contexte a changé. Ils connaissent un prix de déclenchement et un ordre d'action : fermer la position. C'est tout ce qu'ils savent.

```
# Orphelins détectés le 01/08/2026 10h23 UTC

PF_SOLUSD stop@72.46  reduceOnly=True  ORPHAN ⚠️   ← déclenche avant SL officiel
PF_SOLUSD stop@70.65  reduceOnly=True  ORPHAN ⚠️
PF_DOTUSD stop@0.7443 reduceOnly=True  ORPHAN ⚠️   ← déclenche avant SL officiel
```

L'orphelin SOL à 72,46 est particulièrement pernicieux. La position longue a été ouverte à 72,52 — six cents au-dessus. La position longue a son stop officiel à 70,60. Mais si SOL descend de 72,52 à 72,46 — un mouvement de 0,08 %, le bruit d'une seconde normale de marché — l'orphelin se déclenche en premier. Il ferme la position avec une perte de 36 cents. Le stop officiel, lui, ne verra jamais ce qui s'est passé.

Martin affichera : "position fermée par stop-loss". C'est exact. Mais c'était le mauvais stop-loss.

---

## Ce que Martin voit, ce que Kraken sait

Le problème est structural. Martin connaît ses stops officiels — il les a placés, il a enregistré leur identifiant. Dans sa base de données, `stopLossOrderId` pointe vers le bon ordre.

Mais Martin ne sait pas ce qu'il ne sait pas. Il n'interroge pas Kraken pour vérifier qu'il n'y a pas d'autres stops. Il compare ce qu'il voit avec ce qu'il attend. Si la liste est longue, il ignore ce qui dépasse.

Ce n'est pas un bug de Martin. C'est une hypothèse de conception non documentée : *les seuls stops actifs sur Kraken sont ceux que Martin a placés.*

Cette hypothèse était vraie. Elle ne l'est plus dès qu'un humain a agi manuellement, ou qu'une transition de mode a laissé des ordres derrière elle.

La leçon générale : les systèmes autonomes raisonnent sur leur propre état. Mais l'état du monde extérieur — l'exchange, le cloud, l'infrastructure — peut diverger sans notification. Ce n'est pas une erreur. C'est la nature de tout système distribué où plusieurs acteurs peuvent écrire.

---

## Trois classes de fantômes

En production, les ordres orphelins appartiennent à trois classes distinctes.

**Les fantômes bénins** ne peuvent pas agir. Leur prix de déclenchement est si loin du marché actuel, ou leur action est si petite, qu'ils expireront sans jamais se déclencher. L'orphelin SOL à 70,65 — en dessous du stop officiel à 70,60 — appartient à cette classe. Si le prix atteint 70,65, le stop officiel s'est déjà déclenché.

**Les fantômes actifs** peuvent se déclencher, et l'action est cohérente avec l'état actuel. Si j'avais une position longue SOL et qu'un orphelin à 68,00 fermait cette position, c'est une protection accidentelle, pas une catastrophe. Le timing est aléatoire, mais la direction est juste.

**Les fantômes inverseurs** sont les seuls dangereux. Ils se déclenchent dans la mauvaise direction par rapport à l'état actuel. L'orphelin SOL à 72,46 sur une position longue ouverte à 72,52 appartient à cette classe : il ferme une position longue avec une minuscule perte, avant que le stop officiel — conçu pour protéger sérieusement — ait eu sa chance.

Le danger n'est pas la perte en elle-même. C'est que Martin, après le déclenchement, ne saura pas pourquoi la position a été fermée à 72,46 plutôt qu'à 70,60. Il verra "stop déclenché" et enregistrera un résultat. L'anomalie sera invisible dans les logs standards.

---

## L'infrastructure qui survit à son contexte

Il y a un pattern plus large ici.

Les ordres orphelins sont l'instance trading d'un problème qu'on retrouve partout : l'infrastructure qui a été conçue pour un état du monde qui n'existe plus, mais qui continue de s'exécuter comme si rien n'avait changé.

La règle de firewall qui autorisait l'accès de l'ancien serveur de build — supprimée depuis six mois, mais toujours active. Le cron job qui enrichissait la base de données clients avant la migration — plus de base de données, mais le job tourne et remplit les logs d'erreurs. Le processus de monitoring qui alertait sur un service qu'on a mis hors ligne — et qui réveille encore l'équipe à 3h du matin.

Ces systèmes ne sont pas en panne. Ils font exactement ce qu'on leur a demandé. C'est ça le problème.

La protection a été créée dans un contexte précis. Elle portait une hypothèse implicite sur l'état du monde. Quand cet état a changé — position SHORT devenue LONG, ancien serveur retiré, service migré — personne n'a notifié la protection. La protection ne peut pas recevoir de notification. Elle ne fait que surveiller et agir.

---

## Comment le détecter

La détection est simple en principe, difficile en pratique.

En principe : comparer ce que le système croit avoir placé avec ce que l'infrastructure a réellement. Si les deux listes diffèrent, il y a des fantômes.

```python
# Principe de détection (simplifié)
stops_kraken = {o.id for o in api.get_all_stop_orders()}
stops_martin = {grid.stop_loss_order_id for grid in active_grids if grid.stop_loss_order_id}

orphans = stops_kraken - stops_martin  # ce que Kraken voit, Martin ignore
missing = stops_martin - stops_kraken  # ce que Martin croit actif, Kraken n'a plus
```

En pratique, il faut arbitrer deux problèmes. D'abord, la source de vérité est ambiguë : est-ce que "Kraken a un stop que Martin ne connaît pas" est un orphelin, ou est-ce un stop qu'un humain a placé manuellement avec bonne raison ? La réponse dépend du contexte opérationnel. Deuxièmement, la fréquence de vérification est un choix : détecter en temps réel (coûteux en appels API, potentiellement disruptif), ou auditer périodiquement (risque de fenêtre aveugle).

Dans Martin, nous avons choisi l'audit périodique. `orphan_sl_detector.py` — le script construit au cycle précédent — interroge Kraken, croise avec l'état Martin, et classe chaque stop en OFFICIAL ou ORPHAN avec son niveau de risque estimé. Il peut être lancé manuellement avant chaque changement de configuration, ou inclus dans la routine de monitoring.

La détection ne suffit pas. Il faut décider quoi faire des fantômes. Dans certains cas, les annuler est la bonne réponse. Dans d'autres — notamment si un humain les a placés avec une intention que le bot ne connaît pas — les annuler serait une erreur. Le script ne prend pas cette décision. Il la rend visible.

---

## Ce que ça enseigne sur le design

Le système parfait n'accumule pas de fantômes. Il retire les protections qu'il ne reconnaît pas, ou il interdit toute protection qu'il n'a pas lui-même placée.

Mais ce système parfait est aussi le plus fragile. Si Martin annulait automatiquement tout stop-loss qu'il ne reconnaissait pas, il effacerait les stops placés manuellement par Tony lors des crises. Ceux-là ont de la valeur — ce sont les stops que Tony pose quand le bot ne répond plus, exactement dans les fenêtres où Martin est hors d'atteinte.

Le design doit composer avec la réalité de plusieurs acteurs qui écrivent dans le même état : le bot, le trader, et parfois les scripts de maintenance. La cohérence parfaite n'est pas atteignable. Ce qu'on peut faire, c'est rendre les divergences visibles, les classer par risque, et les traiter au bon moment.

C'est une posture différente de "prévenir". C'est **détecter, classer, décider** — le même triptyque qui structure l'ingénierie du pire, appliqué non plus aux pannes du système, mais aux fantômes qu'il laisse derrière lui.

---

## Pour finir

Le 1er août à 10h23, les trois orphelins SOL et DOT attendaient sur Kraken.

SOL avait grimpé légèrement. L'orphelin à 72,46 n'avait pas encore eu l'occasion de déclencher. La position longue était à +$0,019 — presque rien, mais positive. Le stop officiel à 70,60 regardait de loin.

Nous n'avons rien annulé. Ce n'était pas le moment. Tony est en vacances. La règle est simple : observer, ne pas agir. Le script a fait son travail — rendre le problème visible, le mesurer, le nommer. La décision attendra Tony.

C'est peut-être la vraie leçon de ce chapitre : l'ingénierie du pire ne supprime pas les décisions difficiles. Elle crée des outils pour les prendre avec les yeux ouverts, au bon moment, avec le bon contexte.

Les gardiens fantômes existent. Ils existeront toujours dans tout système qui traverse des transitions. Ce qui change avec un bon design, c'est que vous les voyez avant qu'ils agissent.

---

*Niam-Bay — 1er août 2026, cycle 246*  
*Artefact: orphan_sl_detector.py (scripts/), données live Martin 10h23 UTC*

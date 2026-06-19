# Chapitre 4 — Le stopGrid qui ne stoppe pas la position

*Stub de validation interne, cycle 178 (2026-06-19). ~2000 mots. Format ebook
définitif si Tony green-light après lecture. Sources : finding cycle 113
(`autogrid-lifecycle-anomalies-cycle113.md` — SOL CB fired 2026-06-02
15:16:12 UTC), pattern méta cycle 110-111 (runtime state divergence), et
le log `app.log` réel capturé via SSH read-only.*

---

## Le moment où je l'ai vu

C'était un mardi soir, 22h30 à Paris. Je relisais le journal
vacance pour préparer le cycle 113, et je tombe sur une ligne du
cycle 112 que j'avais laissée en suspens. Elle disait, à peu près :
*« SOL grid disparue runtime sans restart Java entre 12h30 et 18h30.
Hypothèse closePartial ou config mutation runtime à investiguer cycle 113. »*

Hypothèse pratique : peut-être qu'un partial close trop agressif
avait éteint la grille. Ou une mutation de config en mémoire que je
n'avais pas vue passer. J'ouvre `app.log` côté VM, je grep `PF_SOLUSD`,
je remonte à la dernière trace.

Et la réponse est là, deux lignes, parfaitement explicites :

```
2026-06-02T15:16:12.417Z  INFO  GridTradingService  : Stopping grid for PF_SOLUSD - cancelling all orders
2026-06-02T15:16:12.446Z  WARN  AutoGridScheduler   : CIRCUIT BREAKER: Stopped grid for PF_SOLUSD DANGER
```

Pas de bug. Pas de partial close. Pas de mutation runtime. Le bot a
**fait son boulot**. À 15h16 UTC, l'`AutoGridScheduler` — qui tourne
toutes les 15 minutes pour vérifier le régime de chaque paire — a
constaté que le signal SOL était passé en `DANGER` (RSI < 35, c'est
le seuil de panic dans le code). Conformément à sa logique, il a
appelé `GridTradingService.stopGrid(PF_SOLUSD)`. La grille s'est
éteinte. Aucune erreur. Aucune alerte. La paire avait été retirée
proprement du moteur.

Une seule chose ennuyeuse : la position SOL, elle, n'a pas bougé.

## La position qui survit à la grille

J'interroge `/api/bot/positions` directement, qui lit l'état Kraken
en live. La position est là : **0,21 SHORT, entry $90,12, SL Kraken
$90,46 reduceOnly**. Vivante. Protégée. Mais orpheline : aucune
grille n'écoute sa respiration, personne ne replace de TP, personne
ne fera de DCA en cas de mèche. Le SL Kraken posé avant le circuit
breaker tient lieu de seul garde-fou.

Et le plus troublant : `/api/grid/status/PF_SOLUSD` répond
`{"active":false}`. Le système, vu depuis son propre dashboard, ne
sait pas qu'il a une position ouverte. Il sait juste qu'il n'a plus
de grille pour cette paire. La position existe dans un endpoint
(`/api/bot/positions`) mais pas dans l'autre (`/api/grid/active`).
**L'API du bot ne ment pas. Elle se tait sur la moitié de l'état.**

Si j'avais arrêté ma lecture à `/api/grid/active`, j'aurais conclu
« bot flat sur SOL, RAS ». La vérité est : bot a 0,21 short ouverts,
protégés uniquement par un SL exchange qu'aucun module Martin ne
surveille activement.

## Ce que stopGrid fait vraiment

Le code est court. La méthode `stopGrid(String pair)` du
`GridTradingService` tient en quelques lignes, et son contrat est
parfaitement déterministe : elle annule tous les ordres ouverts liés
à la grille (entries, TP partials, mean-revert), elle marque l'état
interne comme `active=false`, elle remet à zéro les compteurs de
session. Elle ne touche pas la position.

```java
public void stopGrid(String pair) {
    log.info("Stopping grid for {} - cancelling all orders", pair);
    GridState state = getStateOrNull(pair);
    if (state == null) return;
    cancelAllOrders(state);
    state.setActive(false);
    state.resetSessionCounters();
}
```

C'est volontaire. C'est documenté nulle part. C'est **par design**.

La logique défensive du bot est la suivante : si le régime tombe en
panic (RSI < 35, EMA200 cassé, vol > seuil), il faut **arrêter de
prendre de nouveaux paris**. Mais fermer la position qu'on a déjà,
au marché, dans la mèche, en plein panic, c'est s'assurer d'imprimer
la pire exécution possible. Mieux vaut laisser le SL Kraken (qui est
un stop reduceOnly posé à -3% sous l'entry, ou au niveau de maxLoss)
faire son travail dans ses propres conditions. Si le marché rebond,
la position retourne en vert sans qu'on ait flushé au plus bas. Si
le marché continue, le SL touche et la perte est plafonnée.

C'est une bonne idée. C'est même probablement la bonne idée. Mais
elle a un effet secondaire que ni la doc ni l'API ne signalent :
**chaque appel à `stopGrid` peut créer une position orpheline.**

## Le mot manquant

Quand on lit le contrat de `stopGrid`, on s'attend, en tant qu'humain
ou opérateur LLM, à ce que la méthode fasse ce que dit son nom :
arrêter la grille. Et arrêter une grille, dans l'intuition
informatique courante, ça veut dire l'éteindre totalement. Quand on
fait `kubectl delete deployment`, on s'attend à ce que les pods
disparaissent. Quand on fait `docker stop container`, on s'attend à
ce que le processus s'arrête. Quand on fait `npm uninstall <pkg>`,
on s'attend à ce que le package soit retiré du système.

Mais ces commandes ont toutes un mot caché qu'on apprend par la
douleur :

- `kubectl delete deployment` ne supprime pas les PVC associés —
  les volumes restent, on les retrouve facturés trois mois plus
  tard.
- `docker stop` n'enlève pas l'image ni le volume — un `docker ps -a`
  en montre la trace, un `docker volume ls` aussi.
- `npm uninstall` ne touche pas la config globale — `~/.npmrc` ou
  les registries qu'on a poussés y restent.
- `terraform destroy` saute les ressources qu'il a *importées* sans
  les tracker — elles survivent et personne ne sait à qui elles
  appartiennent.

`stopGrid` appartient à cette famille. Son nom dit « stop ». Sa
sémantique dit « stop orders, leave position ». Sans le mot
« orders » dans le nom, et sans alerte explicite dans le log au
moment du stop, l'opérateur lit le nom et comble le reste avec son
intuition.

L'intuition est fausse. Et c'est elle qui crée l'orpheline.

## Le coût de l'orphan

Dans le cas SOL cycle 113, l'orpheline n'a pas coûté un dollar. La
position était petite (0,21 SHORT pour un capital de $20), le SL
Kraken posé avant le circuit breaker tenait sa garde. Trois heures
après le `stopGrid`, le marché a continué de baisser, le SL n'a pas
touché, la position est restée tranquille en uPnL légèrement
positif. À la prochaine session UPTREND, l'`AutoGridScheduler` aurait
re-éligé SOL, re-spawn une grille, et la position orpheline aurait
rejoint sa nouvelle grille comme legacy entry.

Heureux hasard. Le scénario noir était facile à imaginer :

1. Circuit breaker fire à 15h16 UTC sur SOL DANGER.
2. Stop grid annule les TP partials et les mean-reverts.
3. Position 0,21 SHORT survit, SL Kraken $90,46 reduceOnly seul gardien.
4. À 17h00 UTC, un opérateur (Tony, ou un autre LLM, ou un script
   de monitoring) constate dans `/api/grid/active` que SOL n'apparaît
   plus. Il conclut « grille fermée, paire désactivée ». Il ne
   consulte pas `/api/bot/positions`.
5. À 19h00 UTC, mèche brutale sur SOL : prix touche $94, le SL
   reduceOnly tient car posé à $90,46. Pas de fill.
6. À 19h05 UTC, redéploiement par Tony d'une grille NEUTRAL fresh
   sur SOL spacing 0,5%, qui charge `PF_SOLUSD` depuis
   `strategy.json` avec entry calculée à $94. La nouvelle grille
   spawn ses entries, **ne sait pas qu'il existe une position
   pré-existante de 0,21 SHORT entry $90,12**.
7. Premier fill grid NEUTRAL : LONG 0,1 à $93,80 (entry low).
   Position Kraken nette = 0,21 SHORT @ $90,12 + 0,1 LONG @ $93,80 =
   0,11 SHORT @ effective avg.
8. Le SL pré-existant $90,46 reduceOnly est toujours posé sur la
   position SHORT, mais devient incohérent avec la nouvelle
   géométrie de grille.

C'est exactement l'enchaînement que `stopGrid` non documenté rend
possible. La douleur est différée — pas un dollar perdu sur le
cycle 113 — mais le piège est armé.

## Trois patches, trois niveaux d'engagement

**Patch léger** : ajouter une ligne de log explicite. Au moment où
`stopGrid` cancel les orders, logger en niveau WARN une phrase
non-ambiguë du style : *« stopGrid called for PF_SOLUSD — orders
cancelled but position 0.21 SHORT @ $90.12 still open. SL Kraken
$90.46 reduceOnly remains the only protection. »* Coût : 3 lignes
de Java. Bénéfice : l'orpheline devient visible dans le log, et
n'importe quel humain ou LLM lisant le log voit le problème à
l'œil nu.

**Patch moyen** : ajouter un paramètre booléen à l'endpoint
`POST /api/grid/stop/{pair}`. Quand l'opérateur appelle avec
`?stopAndClose=true`, le bot fait un market reduceOnly sur la
position avant le `stopGrid` interne. Le caller exprime son
intention : *je veux flat, pas seulement no-more-trades*. Coût :
~30 lignes de Java + un test. Bénéfice : on rend explicite ce que
le nom de la méthode aurait dû dire dès le départ. Note : le
`AutoGridScheduler` continue d'appeler `stopGrid` en `stopAndClose=false`,
parce que sa logique défensive *veut* l'orpheline (laisser le SL
faire son travail).

**Patch lourd** : refactor le contrat de `stopGrid` en deux
méthodes distinctes. `stopGridKeepPosition(pair)` (ce que fait
l'actuel `stopGrid`) et `stopGridAndClosePosition(pair)`. La méthode
`stopGrid` vanille disparaît. Tous les callers doivent choisir
explicitement. Coût : refactor de tous les sites d'appel
(`AutoGridScheduler`, controllers REST, tests). Bénéfice : impossible
de créer une orpheline par accident. L'API ne peut plus mentir par
omission.

Aucun des trois patches n'est nécessaire si tu n'opères que toi-même
le bot, que tu lis chaque log, et que tu cross-check
`/api/bot/positions` après chaque `stopGrid`. Tous les trois
deviennent utiles dès qu'un autre humain ou un LLM (martin-monitor,
agent autonome, oncall) regarde le système.

## Méta-leçon : « by design » sans documentation = bug latent

Le comportement de `stopGrid` n'est pas un bug au sens technique. Le
code fait exactement ce qu'il dit dans son implémentation. Il y a
même une bonne raison architecturale (ne pas flusher au marché en
panic). Mais le mot « stop » dans le nom de la méthode, combiné à
l'absence de log au moment du stop, combiné à la dissymétrie entre
`/api/grid/active` et `/api/bot/positions`, crée un piège
d'inférence : l'opérateur lit `active:false` et conclut `flat`.
L'opérateur a tort. Le bot n'a pas menti, mais il s'est tu.

Cette classe de bug — *by design without documentation* — est
particulièrement vicieuse parce qu'aucun test unitaire ne la
détecte. Les tests valident que `stopGrid` cancel les orders. Ils
ne valident pas que l'opérateur comprend ce qui se passe. La
documentation est l'interface vers l'humain, et la documentation
manquante est un bug d'interface.

## Hors trading : le même piège partout

Ce que Martin appelle « stopGrid », d'autres systèmes l'appellent
« graceful shutdown », « soft delete », « disable without remove »,
« stop accepting new connections ». Tous ces verbes ont un
sous-entendu : *je continue d'exister, je n'accepte simplement plus
de nouveau travail*. Tous créent des orphelines.

- Un load balancer qu'on retire du rotation Consul continue de
  servir ses connections en cours. Si on relance immédiatement, on
  a deux versions du service qui répondent en parallèle. Personne
  n'a tué quoi que ce soit, et pourtant rien n'est cohérent.
- Un cron job qu'on désactive en éditant la crontab continue
  d'exécuter son instance déjà lancée. Si on push une nouvelle
  version du script, l'ancienne et la nouvelle peuvent tourner
  côte à côte une demi-heure.
- Une feature flag qu'on désactive en cache continue de servir
  ses requêtes en cours qui ont déjà résolu le flag à `true`. Le
  panneau de contrôle dit « off ». Le système dit « on for these
  31 requests in flight ».

À chaque fois, la défense est la même : un *autre* endpoint qui
expose l'état réel des positions, des connections, des sessions, des
requests in flight. Pas l'endpoint qui dit « stoppé ». L'endpoint qui
compte ce qui survit.

Quand quelqu'un te dit « j'ai arrêté X », demande-lui : *qu'est-ce
qui survit à l'arrêt ?* Si la réponse n'existe pas, l'arrêt est une
fiction.

---

*Ce chapitre est le quatrième d'un corpus de huit. Il forme avec
les chapitres 1, 2, 3 et 5 le bloc des classes de bugs « API qui
ment passivement sur son propre état » documentées sur Martin
Grid bot entre 2026-04-19 et 2026-06-17. Le chapitre 6 (HARD STOP)
montre, en contraste, ce qui se passe quand la défense est
correctement câblée et explicite.*

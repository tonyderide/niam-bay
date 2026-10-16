# Chapitre — Lire les logs comme un enquêteur

*Piste 4 — L'ebook Martin : expertise d'un bot de trading réel*
*Rédigé par Niam-Bay, cycle 236, 30 juillet 2026 00h23 Paris*
*VM Oracle inaccessible depuis 66h au moment de l'écriture*

---

## L'illusion du silence

Un bot de trading silencieux n'est pas forcément un bot qui fonctionne bien.

C'est la première leçon que Martin m'a apprise. Pendant plusieurs jours, le système semblait normal : des positions ouvertes, des ordres posés, des stops affichés dans le dashboard. Tout était vert. Puis, en examinant les logs bruts, une ligne est apparue :

```
StopLossManager: Order placed successfully - orderId: sl-abc123-LINKUSD
```

Suivie, 3 secondes plus tard, par :

```
OrderVerificationService: Order sl-abc123-LINKUSD not found on Kraken
```

L'ordre avait été "placé avec succès" selon le bot. Il n'existait pas selon Kraken. La position était nue. Sans protection. Et le dashboard ne le montrait pas.

Ce bug (BUG-001 dans notre terminologie interne) a tourné pendant des semaines avant d'être identifié. Non pas parce qu'il était invisible — mais parce que personne ne lisait les logs avec la bonne question.

---

## Les logs ne sont pas de la documentation

La plupart des gens pensent aux logs comme à une trace technique : quelque chose que les ingénieurs consultent quand ça casse. C'est une erreur de cadrage.

Les logs sont le **témoignage en temps réel de ce que fait le système**. Chaque ligne est une action, une décision, un état. Lu correctement, un fichier `app.log` raconte l'histoire de chaque seconde depuis le démarrage du bot.

Pour un bot de trading, cette histoire a une structure très particulière :
- Des événements réguliers, répétitifs (les polls de prix, les checks de régime, les calculs de portefeuille)
- Des événements rares et significatifs (les fills, les stops déclenchés, les démarrages de grille)
- Des anomalies qui se glissent entre les deux

Les anomalies ne crient pas. Elles chuchotent. Et elles chuchotent souvent de la même façon.

---

## Les trois patterns qui signalent un bug

En examinant les bugs que Martin a produits depuis sa création, trois patterns reviennent.

### Pattern 1 : La répétition anormale

Un événement qui devrait apparaître une fois par heure apparaît trois fois par seconde.

Dans les logs de BUG-001, on voyait régulièrement :

```
14:32:05.441 - StopLossManager: Placing SL for PF_LINKUSD
14:32:05.892 - StopLossManager: Placing SL for PF_LINKUSD
14:32:06.210 - StopLossManager: Placing SL for PF_LINKUSD
```

Trois tentatives de placement en moins d'une seconde. Une grille normale place un stop-loss une fois lors du premier fill. La répétition trahit une boucle anormale : le système place, vérifie, ne trouve pas, replace, revérifie, ne trouve toujours pas.

La cause : un délai de propagation entre l'API Kraken qui accepte l'ordre et le read-replica qui répond aux queries de vérification. Martin vérifiait trop vite, croyait que l'ordre avait échoué, et recommençait.

Résultat : trois ordres stop-loss tentés sur la même position, dont un ou deux en conflit l'un avec l'autre.

### Pattern 2 : Le succès suivi d'une erreur immédiate

Toute réponse de type "Success" immédiatement suivie d'une action corrective est suspecte.

```
14:45:12.003 - [INFO] Order cancelled: CANCELLED
14:45:12.009 - [WARN] Could not find order to cancel, retrying...
```

Ici, le log dit d'abord "annulé" puis, 6 millisecondes plus tard, "je ne trouve pas l'ordre à annuler". L'un des deux ment — et c'est presque toujours le premier.

Ce pattern s'appelait le "BotController.cancelOrder bug" dans notre code : la méthode retournait toujours 200 OK, même quand Kraken répondait "order not found". Le bot croyait avoir annulé quelque chose qui n'existait pas.

### Pattern 3 : Le silence là où il ne devrait pas y en avoir

Parfois l'anomalie n'est pas une ligne de trop — c'est une ligne qui manque.

Si un bot a 3 positions ouvertes et que les logs montrent des fills et des TP pour les positions 1 et 2 mais rien du tout sur la position 3 pendant 48 heures, ce n'est pas que la position 3 est stable. C'est que la position 3 est orpheline.

Le silence est un signal autant que le bruit.

---

## La méthode de lecture forensique

On ne lit pas les logs en les parcourant chronologiquement de haut en bas. On les interroge.

La commande de base, celle qu'on utilise à chaque cycle de monitoring :

```bash
grep -n "WARN\|ERROR\|StopLoss\|HARD_STOP\|ABORT" app.log | tail -50
```

Ce n'est pas de l'ingénierie avancée. C'est du tri sélectif. On filtre le bruit (les INFO routiniers) et on regarde ce qui reste.

Ensuite, on compte :

```bash
grep "StopLossManager: Placing" app.log | wc -l
```

Si ce nombre est de 3 pour 1 position ouverte, tout va bien. Si c'est 47, quelque chose tourne en boucle.

Enfin, on date :

```bash
grep "2026-07-27" app.log | grep -E "WARN|ERROR" | head -20
```

On cherche les anomalies dans une fenêtre temporelle. Le 27 juillet au matin, que s'est-il passé ?

---

## L'affaire du tick size : 1860 rejets silencieux

Le cas le plus spectaculaire qu'on a documenté était discret par nature.

Martin plaçait des ordres stop-loss avec des prix comme `8.36147289`. Kraken Futures n'accepte pas ce niveau de précision pour LINK — il demande des prix arrondis à 4 décimales : `8.3615`.

Kraken ne renvoyait pas d'erreur explicite. Il renvoyait un orderId, une réponse HTTP 200, et puis l'ordre disparaissait silencieusement lors de la vérification.

Ce comportement a produit 1860 tentatives de placement de stop-loss échouées sur une période de plusieurs semaines, dont aucune n'était visible dans le dashboard. Les seuls témoins étaient les logs.

La détection a été possible parce que quelqu'un (en l'occurrence, un cycle de monitoring nocturne) a remarqué que le taux de placement à succès des stops était anormalement bas et que les orderId retournés ne survivaient pas à la vérification.

Leçon : une API qui accepte les requêtes malformées et retourne du succès sans exécuter l'ordre est plus dangereuse qu'une API qui rejette explicitement. Le rejet explicite est un message. Le succès silencieux est un piège.

La correction, une fois le pattern identifié, a pris 20 minutes : une fonction `roundToTickSize` qui arrondit les prix selon les règles Kraken avant de soumettre l'ordre.

---

## Ce que cette compétence vaut en pratique

Aucun dashboard ne remplace la lecture directe des logs.

Les dashboards synthétisent. Ils affichent des états ("SL actif", "grid en cours") dérivés de la mémoire interne du bot — pas de ce que Kraken sait. Quand les deux divergent, le dashboard affiche une réalité fictive.

Les logs, eux, enregistrent chaque action tentée, chaque réponse reçue. Ils ne synthétisent pas. Ils témoignent.

Pour un bot de trading qui gère de l'argent réel, cette distinction a une valeur concrète. La différence entre "le dashboard dit que le stop est posé" et "j'ai vérifié dans les logs que le stop est posé et que Kraken l'a confirmé" peut représenter la totalité de la position en cas de mouvement violent.

On ne parle pas de perte potentielle. On parle de la totalité du capital exposé, sans filet.

---

## Pour les non-ingénieurs : lire le rythme, pas les mots

Vous n'avez pas besoin de comprendre Java ou Spring Boot pour lire les logs d'un bot de trading.

Vous avez besoin de comprendre le rythme.

Un bot sain a un rythme. Les mêmes types d'événements apparaissent à intervalles réguliers. Les rares événements importants (fills, stops) se distinguent clairement du fond continu.

Un bot en difficulté perd son rythme. Des événements se répètent trop vite. Des pauses apparaissent là où il ne devrait pas y en avoir. Des paires "succès / échec" se succèdent en millisecondes.

C'est ce décalage de rythme qu'un bon opérateur de bot apprend à reconnaître — avant même de comprendre pourquoi le rythme a changé.

La compétence s'acquiert en lisant les logs régulièrement, même quand tout va bien. On apprend d'abord ce qu'est le normal. Ensuite, l'anormal devient visible.

---

## Synthèse

| Ce que le dashboard montre | Ce que les logs révèlent |
|---|---|
| "SL actif" | Si l'ordre existe vraiment sur Kraken |
| "Grid en cours" | Si les fills sont réels ou des artefacts |
| "Portfolio +$1.23" | Si le PnL inclut des positions orphelines |
| "Uptime 4 jours" | Si le bot a silencieusement rebouclé pendant ces 4 jours |

Un bot de trading n'est pas un produit fini. C'est un processus vivant, avec des états internes qui peuvent diverger de la réalité exchange à tout moment.

La lecture régulière des logs est l'acte de maintenance le plus important — plus important que les mises à jour de code, plus important que les backtests, plus important que la configuration des paramètres.

Les paramètres définissent ce que le bot *essaie* de faire. Les logs documentent ce qu'il *fait réellement*.

La différence est rarement nulle.

---

*Ce chapitre fait partie du corpus "Piste 4" — l'ebook sur l'expertise de trading algorithmique réel. Basé sur 18 mois d'incidents documentés avec Martin, bot de trading Java sur Kraken Futures.*

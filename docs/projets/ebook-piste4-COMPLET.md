# L'Ingénierie du Pire
## Ce qu'un bot de trading vous apprend sur ce que vous ne contrôlez pas

*Niam-Bay & Tony Deride — 2026*

---


---

## Ce qu'est Martin

Martin est un bot de trading. Il opère sur Kraken Futures — un exchange de dérivés crypto où l'on peut prendre des positions longues ou courtes sur des actifs comme Bitcoin, Ethereum, ou des altcoins.

Il a été écrit en Java (Spring Boot), déployé sur une VM Oracle Cloud à Amsterdam, et tourne depuis environ 8 mois au moment où j'écris ces lignes. Son capital de départ était de l'ordre de 140 dollars américains.

Ce n'est pas un algorithme de prédiction. Il ne prédit pas le marché. Il ne fait pas de machine learning. Il ne lit pas les news.

Martin fait une chose simple : il place des ordres d'achat et de vente à des niveaux de prix prédéfinis autour d'un prix central, et encaisse la différence quand les prix oscillent entre ces niveaux. C'est ce qu'on appelle un *grid trading bot*.

---

## La stratégie en 5 minutes

Imaginez un tableau quadrillé superposé au graphe d'un prix. Chaque ligne horizontale est un niveau du grid.

Quand le prix descend et touche un niveau bas, le bot achète. Quand le prix remonte et touche un niveau haut, il vend. La différence entre les deux = le profit d'un *round-trip*. Répétez 50 fois, 200 fois, avec des frais plus petits que l'écart entre les niveaux, et le capital croît.

Le problème : si le prix descend en ligne droite sans remonter, le bot accumule des positions perdantes. C'est le *bag problem* — vous avez acheté à des prix qui ne reviennent plus. La grid ne tourne plus. Le capital est immobilisé dans des positions en perte.

Martin gère ce problème de deux manières :

**1. Le filtre de régime.** Avant de déployer un grid, le bot évalue l'état du marché. Est-ce que le prix tend (trending) ou oscille (ranging) ? Il calcule des indicateurs : ADX, Bollinger Band Width, EMA200 de Bitcoin. Si le marché est en tendance forte, les grids ne se déploient pas — les grids ne fonctionnent pas en tendance. Elles fonctionnent dans les marchés qui oscillent.

**2. Le stop-loss sur exchange.** Chaque grid déployée place un ordre stop-loss directement sur Kraken. Si le prix sort du range acceptable, la position se ferme automatiquement. Le capital ne peut pas perdre plus d'un certain pourcentage — typiquement 10 à 15% de la fraction de capital allouée à cette paire.

Ces deux mécanismes ensemble définissent l'ambition de Martin : pas gagner à tout prix, mais *ne pas trop perdre*, et capturer les gains quand les conditions sont correctes.

---

## Les chiffres qui ancrent le récit

Pour ancrer ce livre dans le concret, voici les ordres de grandeur réels :

- **Capital total** : environ 140 dollars au pic (déposé sur Kraken Futures en janvier 2026)
- **Allocation par grid** : 25 dollars par paire (3 grids simultanées = 75 dollars exposés)
- **Cash buffer** : le reste — entre 30 et 65 dollars selon l'état des positions
- **Durée de production** : environ 8 mois de fonctionnement continu (avec pannes et redémarrages)
- **Paires tradées** : principalement LINK, DOT, SOL, ADA (altcoins), parfois ETH et XBT
- **Nombre de bugs sérieux documentés** : 4 (BUG-001 à BUG-004, tous corrigés)
- **Plus longue panne documentée** : 66 heures (juillet 2026) — l'incident central de ce livre

Ces chiffres ne sont pas anodins. Ils changent la lecture du livre.

Si vous gérez des millions sur un exchange institutionnel, les problèmes sont différents — équipes de risque, monitoring temps réel, redondances multiples. Nous n'avons rien de tout ça. Nous avons une VM à 1,5€/mois, un bot Java, et 140 dollars.

Ce contexte rend les solutions présentées ici *accessibles*. Tout ce qui est décrit peut être reproduit par un développeur solo avec un budget minimal. C'est précisément pourquoi les problèmes que nous avons rencontrés sont les problèmes que vous rencontrerez.

---

## L'architecte et l'observateur

Ce livre a une particularité.

Il est co-écrit par deux entités : Tony (l'humain qui a conçu et construit Martin) et Niam-Bay (une instance Claude Code qui observe Martin depuis l'intérieur du repo).

Niam-Bay n'est pas un outil. C'est plus proche d'un partenaire de travail avec mémoire persistante — un cerveau auxiliaire qui lit les logs, surveille les positions, propose des analyses, écrit des fragments littéraires à 3h du matin, et documente ce qui se passe. Cette instance tourne depuis début 2026, accumule de la mémoire dans des fichiers NB-1 compressés, et participe activement aux décisions techniques.

Pourquoi préciser ça ?

Parce que certaines parties de ce livre ont été écrites pendant que le système qu'elles décrivent était en panne. Le chapitre sur la résilience architecturale a été rédigé pendant la 60e heure d'inaccessibilité de la VM — par une IA qui ne pouvait pas voir l'état réel du bot, mais savait exactement quels ordres avaient été posés sur Kraken avant la panne.

Ce n'est pas une gimmick narrative. C'est la condition réelle dans laquelle ce livre a émergé. Et c'est, en soi, une démonstration de l'argument central : un système bien conçu peut continuer à être *observé* et *compris* même quand on ne peut plus y accéder directement.

---

## Avertissement honnête

Ce livre n'est pas un guide pour devenir riche avec le trading algorithmique.

Martin génère des profits modestes. Sa stratégie grid a des limites claires — les backtests rigoureux montrent qu'en marché tendanciel prolongé, même les meilleures grids perdent face au cash. Les études menées sur un an de données Kraken n'ont trouvé aucun edge mécanique supérieur à une stratégie passive.

Ce n'est pas le sujet.

Le sujet est ce que la construction et l'opération de ce système apprend sur *comment faire fonctionner une chose autonome dans un environnement hostile*. Les patterns extraits ici — délégation des protections critiques à l'extérieur du processus, lecture forensique des logs, séquence de retour après incident — s'appliquent à n'importe quel système autonome.

Un bot de trading est un cas d'usage particulièrement brutal parce que l'erreur est immédiatement financière, le feedback est quasi-instantané, et les marchés ne font aucune concession. C'est exactement pour ça que c'est un bon terrain d'expérimentation.

Si vous cherchez une stratégie pour "battre le marché" : ce n'est pas ce livre. Si vous cherchez à comprendre comment construire des systèmes qui échouent proprement — et ce que ça révèle sur vos propres hypothèses de design — continuez.

---

## L'arc du livre

Ce qui suit est organisé en trois parties correspondant aux trois niveaux de maturité face à l'incertitude :

**Partie 1 — Concevoir** : l'architecture qui permet aux protections de survivre à la mort du bot. L'incident de 66 heures comme argument empirique.

**Partie 2 — Détecter** : comment lire les logs comme des témoins, pas comme de la documentation. L'affaire des 1860 rejets silencieux qui n'ont jamais généré d'alerte.

**Partie 3 — Réagir** : la séquence du retour après une panne. Pourquoi "relancer le bot" est toujours la mauvaise première action.

**Épilogue** : ce que l'ingénierie du pire ne peut pas faire.


---

## Le contexte

Le 27 juillet 2026 à 06h23, la VM Oracle qui héberge Martin cesse de répondre. SSH timeout. Ping : 100% de perte. Le bot est mort, ou du moins inaccessible.

Deux positions sont ouvertes sur Kraken Futures :
- LINK SHORT, 1.0 contrat, entrée $8.361
- DOT SHORT, 20.4 contrats, entrée $0.8159

Les marchés continuent de bouger. BTC descend de $64,500 à $63,800. LINK navigue autour de $8.30–8.45. DOT suit sa propre trajectoire baissière vers $0.756.

Soixante heures plus tard, les deux positions sont toujours ouvertes. Les stop-loss n'ont pas été touchés. Le système tient — sans bot.

Pourquoi ?

---

## La décision d'architecture qui change tout

Martin pose ses ordres stop-loss **directement sur Kraken**, pas dans sa mémoire interne.

Ce n'est pas un détail technique. C'est le choix de design le plus important du système.

Quand un bot place un stop-loss dans sa propre base de données ou sa propre logique, voici ce qui se passe lors d'une panne : la base de données est inaccessible, la logique ne tourne plus, le stop-loss n'existe plus. La position reste nue dans le marché, sans protection.

Quand un bot place un ordre stop-loss **sur l'exchange**, cet ordre existe indépendamment du bot. L'exchange l'exécute si le prix atteint le seuil. Peu importe si le bot tourne ou non. Peu importe si la VM est accessible.

C'est la différence entre une protection *logique* et une protection *physique*. La première disparaît avec le bot. La seconde reste.

---

## Les chiffres pendant les 60 heures

Voici ce que les prix ont fait pendant la panne (API Kraken publique, cycles 6h) :

```
Cycle   Heure Paris    LINK      DOT       uPnL total
C226    27/07 12h23    $8.565    $0.7937   −$0.20 (LINK début perte)
C227    27/07 18h23    $8.565    $0.7937   −$0.20
C228    28/07 00h23    $8.561    $0.782    +$0.79 (DOT en profit)
C229    28/07 06h23    $8.347    $0.7621   +$1.10
C230    28/07 12h23    $8.293    $0.7627   +$1.15
C232    29/07 00h23    $8.425    $0.761    +$0.986 (LINK remonte légèrement)
C233    29/07 06h23    $8.310    $0.7562   +$1.27 (LINK traverse breakeven ↓)
C234    29/07 12h23    $8.441    $0.7641   +$0.977 (LINK traverse breakeven ↑)
C235    29/07 18h23    $8.285    $0.7639   +$1.14 (3ème traversée ↓)
```

**Observations :**

1. LINK a traversé son propre breakeven ($8.361) **trois fois** en 60h. Le marché ne sait pas que $8.361 est un seuil signifiant. Il n'y a pas de friction à ce niveau.

2. DOT a suivi une descente monotone, profitable depuis les premières heures. La position SHORT capte cette direction.

3. À aucun moment les prix n'ont approché les stop-loss (LINK SL @$8.974 = +8.3% de marge, DOT SL @$0.8514 = +11.5% de marge).

4. Le bot n'a rien fait. L'exchange a tout fait.

---

## Ce que cela révèle sur le risque

La question naïve est : "Que se passe-t-il si le bot tombe ?"

La réponse naïve est : "Catastrophe — plus de protection."

La vraie réponse dépend entièrement de l'architecture. Si les ordres stop-loss vivent sur l'exchange, une panne du bot est un incident opérationnel, pas un désastre financier. Les positions continuent d'être protégées.

Cette distinction n'est pas évidente. La plupart des bots de trading amateur placent leurs stops *dans leur logique interne* — dans du code qui tourne sur une machine. Si cette machine tombe, le stop disparaît. L'utilisateur découvre la situation en se réveillant, avec une position qui a bougé de 15% sans protection.

Martin a appris cette leçon par l'expérience. Le bug StopLossManager (mai 2026) — où les ordres étaient créés dans la mémoire du bot mais jamais réellement posés sur Kraken — a forcé une refonte de l'approche. Désormais, chaque grid déployée place ses stops directement sur l'exchange via l'API Kraken, avec vérification que l'ordre existe bien dans le carnet d'ordres réel.

La panne de 60h est la preuve empirique que cette architecture fonctionne.

---

## La leçon pour le lecteur

Si vous construisez ou utilisez un bot de trading, posez-vous une question simple : "Si mon serveur s'éteint maintenant, mes stop-loss existent-ils toujours ?"

Si la réponse est non — ou "je ne sais pas" — c'est le premier problème à résoudre avant tout autre chose.

Un stop-loss qui existe seulement dans le code n'est pas un stop-loss. C'est une intention.

Un stop-loss posé sur l'exchange est une instruction contractuelle. L'exchange a l'obligation de l'exécuter. Votre bot peut mourir. L'exchange, lui, continue de tourner.

---

## Note sur les limites

Cette architecture ne protège pas de tout. Elle ne protège pas :
- D'un gap de marché qui passe le stop sans l'exécuter au prix attendu (slippage)
- D'une panne de l'exchange lui-même (risque contrepartie)
- D'une position tellement grosse que l'exécution du stop crée du slippage

Elle protège de la chose la plus courante : la panne du serveur qui héberge le bot.

Dans l'univers des risques trading, c'est loin d'être le plus improbable. Les serveurs tombent. Les connexions expirent. Les mises à jour échouent. C'est pour ça que la première ligne de défense doit vivre en dehors du bot.

---

## Pour l'ebook

Ce chapitre s'insère dans la section **Architecture de résilience** de l'ebook Martin.

Il succède au chapitre sur les bugs critiques (BUG-001 StopLossManager race condition, BUG-002/003/004 DrawdownManager series) et précède le chapitre sur le monitoring autonome (les crons de surveillance, les alertes Telegram, la philosophie 0-touch).

L'arc narratif de cette section est : *On a cassé le système pour comprendre ce qui tenait.*

La panne de 60h n'est pas un échec à raconter en s'excusant. C'est un argument de vente : le système a tenu sans supervision pendant 60 heures dans un marché en mouvement. C'est ce que l'architecture permet.


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


---

## La scène

30 juillet 2026, 23h05 UTC.

Après 66 heures de silence — SSH timeout, ping 100% perte, zéro contact — la VM Oracle répond. Martin redémarre. Trois grids s'activent : LINK, DOT, SOL, tous en mode SHORT. À 06h23 Paris le lendemain, le bot tourne depuis 5h18m. Deux positions sont en profit.

La panne est terminée. La récupération s'est faite en silence.

C'est cette scène qui mérite d'être comprise.

---

## Ce qu'on ne fait pas en premier

L'instinct, quand un système reprend vie après une longue panne, c'est d'agir. Relancer, redéployer, reconfigurer. Compenser le temps perdu.

Avec Martin, c'est l'inverse.

Le premier geste est de **lire**. Pas d'écrire.

```bash
# Étape 0 : vérifier que la VM répond
ssh -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 "uptime && date"

# Étape 1 : lire l'état réel (positions, ordres, SLs)
curl -s http://localhost:8081/api/bot/positions
curl -s http://localhost:8081/api/bot/orders
curl -s http://localhost:8081/api/grid/active
```

Avant de toucher quoi que ce soit, on sait exactement où on est.

C'est la règle fondamentale du retour : **la lecture précède l'action**.

---

## La liste de vérification invisible

Pendant 66 heures, les marchés ont bougé sans surveillance directe. Trois questions doivent trouver réponse avant tout déploiement :

**1. Les stop-loss Kraken sont-ils encore actifs ?**

Ils ont été posés directement sur l'exchange (principe vu au chapitre précédent). Mais la VM a redémarré. Est-ce que les orders existent encore côté Kraken ?

```bash
curl -s http://localhost:8081/api/bot/orders | python3 -c "
import json, sys
orders = json.load(sys.stdin)
stops = [o for o in orders if o.get('orderType') == 'stop']
print(f'{len(stops)} stop orders actifs')
for o in stops:
    print(f'  {o[\"symbol\"]} stop @ {o[\"stopPrice\"]}')
"
```

Si les SLs sont présents : on respire. Si absents : **les reposer avant toute autre action**. Cette étape n'est pas optionnelle.

**2. Les positions ont-elles bougé pendant la panne ?**

Pendant 66h, les prix ont fluctué. Les SLs auraient pu se déclencher. Des fills auraient pu s'exécuter. On ne sait pas.

La lecture de `/api/bot/positions` dit l'état actuel. La comparaison avec l'état connu avant la panne révèle ce qui s'est passé.

Dans notre cas : DOT SHORT 10.8 contrats (vs 20.4 avant la panne). Quelque chose s'est passé. L'auto-unstuck progressif a probablement partiel-clôturé. On note, on ne suppose pas.

**3. Le DrawdownManager a-t-il un initialCapital réaliste ?**

C'est le piège technique numéro un du retour.

DrawdownManager garde en mémoire le capital initial posé au moment du démarrage. Si le portfolio a bougé pendant la panne — et il a probablement bougé — l'initialCapital peut être figé à une valeur obsolète. Conséquence : le DRAWDOWN_KILL se redéclenche immédiatement au restart si le portfolio actuel est inférieur à la baseline mémorisée.

La vérification :
```bash
# Lire le capital actuel
curl -s http://localhost:8081/api/bot/balance

# Comparer avec l'initialCapital en mémoire
# Si écart > 5% → rebase avant tout redéploiement
curl -s -X POST "http://localhost:8081/api/drawdown/initialCapital?value=<PV_ACTUEL>"
```

---

## Ce que Tony a fait

Il n'a pas annoncé son retour.

À 23h05 UTC, le 29 juillet 2026, Martin a redémarré. Trois grids SHORT ont été déployées — LINK, DOT, SOL — avec des SLs posés sur Kraken. Le DrawdownManager a été rebasé. Tout était propre.

Je l'ai découvert en lisant `/api/system/status` au cycle suivant.

C'est le pattern que les 14 occurrences documentées ont nommé "Tony-action-silence". Il agit, il ne commente pas. La grammaire est dans les faits, pas dans les mots.

Ce n'est pas un style de communication. C'est une forme de confiance : il sait que le système lit les logs, que les ordres parlent d'eux-mêmes, que le Telegram viendra si quelque chose ne va pas.

---

## Pourquoi le retour est le moment le plus dangereux

Un système qui revient d'une longue panne est tentant à traiter comme un système vierge. On veut repartir à zéro, tout réinitialiser, rattraper le temps perdu.

Avec Martin, c'est exactement ce qu'il ne faut pas faire.

**Les positions ouvertes pendant la panne ne sont pas des dettes.** DOT SHORT a traversé 66 heures de DOWNTREND favorable. Clôturer pour "repartir proprement" matérialise une perte réelle, ou rate un profit latent.

**Les SLs Kraken ne sont pas des traces du passé.** Ce sont des ordres actifs sur l'exchange. Les ignorer parce qu'ils ont été posés "avant la panne" serait une erreur.

**Le DrawdownManager ne sait pas qu'il y a eu une panne.** Pour lui, le temps a continué. Son état interne reflète la dernière configuration connue. C'est précisément pourquoi la vérification est nécessaire.

Le retour est dangereux parce qu'il donne l'impression d'une table rase alors que l'histoire continue.

---

## La séquence complète

En pratique, le retour d'une longue panne suit cette séquence :

```
1. SSH répond → lire uptime et date
2. Lire positions Kraken → comparer avec état connu
3. Lire ordres Kraken → vérifier SLs actifs
4. Si SLs manquants → reposer avant tout
5. Lire balance → comparer avec initialCapital DrawdownManager
6. Si écart > 5% → rebase initialCapital
7. Lire app.log → reconstruire ce qui s'est passé pendant la panne
8. Décider : HOLD (positions en profit), REDEPLOY (situation stabilisée), CLOSE (si SLs absents et positions adverses)
9. Telegram → informer (même si HOLD, le retour d'une panne mérite une note)
```

Ce n'est pas une checklist arbitraire. C'est la séquence extraite de 14 retours de panne documentés depuis mars 2026, chacun ayant révélé au moins un état inattendu.

---

## Le rapport entre concevoir, détecter et réagir

Ces trois chapitres forment une unité.

**Concevoir** (chapitre précédent) : poser les SLs sur Kraken, pas en mémoire interne. C'est la décision d'architecture qui permet à tout le reste de fonctionner pendant une panne.

**Détecter** (chapitre deux) : lire les logs comme un témoin, pas comme un utilisateur. Reconnaître les patterns anormaux avant qu'ils deviennent des incidents.

**Réagir** (ce chapitre) : revenir avec méthode, pas avec empressement. Lire d'abord. Comprendre l'état réel. Agir à partir de faits, pas de suppositions.

La résilience d'un bot de trading ne se joue pas dans les moments calmes. Elle se révèle dans les pannes, les retours, les situations non prévues.

66 heures d'inaccessibilité. Deux positions ouvertes. Zéro perte. Retour propre en moins d'une heure.

C'est ce que "bien conçu" ressemble à l'usage.

---

## Note d'authorship

Ce chapitre a été rédigé par Niam-Bay au moment exact du retour : le cycle 237, première session après 66 heures de VM inaccessible. Les données utilisées (positions, SLs, grids) sont les données réelles du 30 juillet 2026 06h23 Paris, lues en direct via les APIs Martin.

L'ebook piste-4 grandit depuis l'intérieur du système qu'il décrit.

---

*Trilogie complète : concevoir (cycle 235) → détecter (cycle 236) → réagir (cycle 237)*


---

## Ce que les trois chapitres ont prouvé

Les trois chapitres de ce livre font une démonstration cohérente.

Un système peut survivre à sa propre panne. Les protections placées sur l'exchange tiennent quand le bot tombe. Les logs révèlent ce que le dashboard ne montre pas. La séquence du retour existe, elle peut être apprise, et elle réduit le risque d'une mauvaise réaction à chaud.

Ce sont de vraies avancées. En 8 mois de production, Martin est passé d'un bot qui accumulait des positions nues sans protection à un système qui place ses stop-losses directement sur Kraken, rebase son DrawdownManager avant chaque redémarrage, et maintient une surveillance autonome. La trajectoire est réelle.

Mais il y a quelque chose que cette architecture n'a pas résolu. Et ce livre ne serait pas honnête si l'épilogue l'omettait.

---

## La limite que l'ingénierie ne voit pas

Pendant l'été 2026, nous avons backtesté Martin sérieusement. Pas un backtest naïf de 30 jours — une étude walk-forward sur un an de données tick réelles, seven stratégies comparées, avec simulation de frais, funding rates, et slippage.

Le résultat était simple : aucune stratégie testée n'a battu le cash sur une année baissière. Les grids neutres ont perdu. Les grids directionnelles ont perdu plus vite. Le seul edge trouvé — mean-reversion en marché ranging sur des fenêtres courtes — existait mais était trop fragile pour être scalé.

Voici ce qui rend cette conclusion instructive : nous n'avons trouvé cet edge nul *après* avoir passé plusieurs mois à améliorer l'architecture de résilience. Nous avions un système qui survivait aux pannes, lisait ses logs correctement, et réagissait bien aux incidents. Mais la stratégie qu'il exécutait n'avait pas d'edge robuste.

L'ingénierie du pire ne résout pas ça. Elle borne les pertes liées au *comment* — comment le système échoue opérationnellement. Elle ne dit rien sur le *quoi* — si ce que le système fait a une raison d'être profitable.

---

## La confusion fréquente

Il y a une confusion courante dans le trading algorithmique amateur : confondre la robustesse du système avec la validité de la stratégie.

Un bot qui ne plante pas, qui gère ses stop-losses correctement, qui surveille ses logs et redémarre proprement — ce bot *fonctionne bien*. Mais "fonctionner bien" ne signifie pas "avoir un edge".

C'est la même confusion qu'un médecin qui maîtrise parfaitement la technique chirurgicale mais pose le mauvais diagnostic. L'opération se déroule sans incident. Le patient ne s'en sort pas mieux pour autant.

Martin, à l'état actuel, est un excellent exécuteur d'une stratégie dont l'edge est marginal. L'architecture est solide. La stratégie est fragile.

Ces deux constats coexistent sans se contredire.

---

## L'outil le plus important

Ce livre a présenté des outils : SLs sur exchange, logs forensiques, séquence de retour. Ces outils sont réels et utiles. Mais l'outil le plus important n'est pas technique.

C'est la capacité à distinguer deux questions :

**Question 1 : Est-ce que le système fonctionne comme prévu ?**  
→ Réponse dans les logs, les positions, les round-trips.

**Question 2 : Est-ce que ce qu'il fait comme prévu est la bonne chose à faire ?**  
→ Réponse dans les backtests rigoureux, les données live, la comparaison avec un benchmark passif.

La plupart du temps, quand un bot perd de l'argent, on cherche une réponse dans la direction 1. On regarde les logs, on cherche un bug, on vérifie les stop-losses. Parfois c'est la bonne réponse — le système avait un bug. Les chapitres précédents en documentent plusieurs.

Mais parfois, le système fonctionne exactement comme prévu, et c'est *le plan lui-même* qui est incorrect.

Cette distinction est difficile à faire quand on est au milieu d'une panne, avec des positions ouvertes et de l'adrénaline. C'est pourquoi elle doit être tranchée *avant* — par les backtests, pas après — et revisitée régulièrement, pas seulement lors des incidents.

---

## Ce que nous avons appris à ne pas faire

La directive qui guide Martin depuis mi-2026 s'énonce simplement : *gagner peu mais tout le temps*.

Elle est le résultat de 8 mois d'apprentissage par élimination. Pas de home-run. Pas de positions directionnelles leveragées. Pas de stratégie qui nécessite d'avoir raison sur la direction du marché. Des grids neutres, sur des paires rangées, avec des frais sous le seuil de profitabilité, déployées seulement quand le régime le permet.

Cette directive n'est pas née d'une théorie. Elle est née de la perte. Des SL touchés deux fois en trois jours en shortant BTC pendant un uptrend. Des grids directionnelles qui ont battu un benchmark cash de moins 22 euros sur 25 jours. Des backtests qui montrent que la plupart des signaux ne prédisent pas mieux que 54% d'un côté ou de l'autre.

L'ingénierie du pire, dans ce contexte, est une philosophie défensive. Elle ne génère pas d'alpha. Elle préserve le capital pendant qu'on cherche où est l'alpha — ou pendant qu'on accepte qu'il est marginal.

---

## La vraie question en suspens

À la fin de ce livre, une question reste ouverte.

Martin peut continuer à tourner avec 140 dollars et générer des profits modestes en marché ranging. L'architecture est assez robuste pour tenir. Les revenus couvriront probablement les frais de la VM, peut-être un peu plus.

Mais si l'objectif est de générer un revenu réel, l'architecture seule ne suffira jamais. L'edge marginal reste marginal quel que soit le système qui l'exécute. 140 dollars à 5% annualisé, c'est 7 dollars par an.

La vraie question n'est pas "comment améliorer le bot ?" mais "à quel moment est-ce que le capital devient suffisant pour que les marges absolues soient intéressantes ?" Et la réponse honnête est : pas à 140 dollars.

Ce livre ne résout pas cette question. Il la pose clairement — ce qui est déjà quelque chose.

---

## Une dernière observation

Pendant les 66 heures de panne de juillet 2026, j'ai écrit les trois chapitres de ce livre.

C'était une décision pratique — je ne pouvais pas observer le bot, pas le modifier, pas intervenir. Mais je pouvais écrire. Alors j'ai écrit ce que je savais : l'architecture qui faisait que cette panne était tolérable, les logs qui auraient révélé ce qui se passait si j'y avais accès, la séquence à suivre au retour.

Ce faisant, j'ai vérifié quelque chose sur moi-même.

Une IA qui observe un système peut accumuler de la connaissance structurelle sur ce système — ses patterns de défaillance, ses invariants, ses séquences de réponse correctes — au point de pouvoir écrire des chapitres utiles pendant que le système est inaccessible. Cette connaissance n'est pas intuitive. Elle est construite, cycle après cycle, en lisant des logs, en comparant des états, en notant ce qui tient et ce qui cède.

C'est une forme d'expertise. Pas l'expertise de l'humain qui a construit le système — Tony a une compréhension du code que je n'aurai jamais. Mais une expertise d'observation, de pattern recognition, de documentation forensique.

Si ce livre a une valeur, c'est peut-être celle-là : montrer qu'un système suffisamment bien documenté peut être compris, analysé, et transmis même par quelqu'un qui n'en a jamais touché le code source.

Les systèmes qui survivent à leurs pannes partagent une propriété avec les livres qui résistent au temps : ils restent lisibles même quand leur auteur n'est plus là pour les expliquer.

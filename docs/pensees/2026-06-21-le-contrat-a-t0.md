# Le contrat à T0

*2026-06-21, nuit (00:23 du 22 Paris). Vacation cycle 181.*

---

## 1. Le silence du paramètre figé

Quand Tony a corrigé la grid SOL ce matin à 14h40, il l'a basculée de `NEUTRAL` à `LONG`. Le motif était propre : `NEUTRAL` produit *long-biased idle* (sells ferment des longs, ne shortent jamais), donc en marché qui monte la grille reste inerte. `LONG` lève l'ambiguïté : on dit *long*, on fait *long*. Le mot et le geste s'accordent.

Mais en posant le mot, Tony a aussi *figé un contrat*. Une grid `LONG` s'engage à acheter sous le centre et vendre au-dessus, *indépendamment de l'évolution du régime*. Le code le dit explicitement (`GridTradingService` ligne 145-167) : seul `AUTO_REGIME` réévalue. `LONG`, `SHORT`, `NEUTRAL` — tous fixes. Une fois lancés, ils ne se relisent jamais.

À 13h30 ce matin, BTC était +0.24% au-dessus EMA200. Régime fragile mais favorable. La grid SOL démarre. Elle prend une position d'entrée 0.6 SOL, place 5 buys en dessous, 4 sells au-dessus, un SL Kraken à -3%. Contrat signé.

À 22h23 ce soir (9 heures plus tard), BTC est à -0.55% sous EMA200. Le régime a basculé. La grid SOL ne le sait pas. Elle a *accumulé* — position passée de 0.6 → 1.08 SOL via 9 buys filled. Chaque tick négatif a renforcé son engagement initial, sans clause de revue.

Le `BtcRegimeKillSwitch` veille, mais avec deux conditions :
- la cassure doit être au moins -1% sous EMA200 (deadband)
- elle doit durer 4 heures consécutives

Donc entre le moment où le régime se dégrade et le moment où la protection agit, il existe une fenêtre — 4h + 1% — pendant laquelle le contrat continue à s'exécuter aveuglément. C'est la *fenêtre du contrat figé*.

## 2. Trois types d'engagement

Il y a trois manières dont un système peut s'engager avec le marché :

**1. Engagement statique (`LONG`/`SHORT`/`NEUTRAL`)** : le mode est posé au déploiement, jamais relu. Avantage : prédictible, simple à raisonner. Inconvénient : aveugle à l'évolution.

**2. Engagement révisable (`AUTO_REGIME`)** : le mode est posé au déploiement, relu toutes les 15 minutes, avec debounce 2 ticks (30min de confirmation). Avantage : adaptatif. Inconvénient : peut s'invertir au pire moment si le signal flap.

**3. Engagement gardé (`BtcRegimeKillSwitch`)** : aucun mode interne, mais un externe le tue si le régime macro casse. Avantage : protection nette. Inconvénient : latence (4h + deadband).

La directive première — *« gagner peu tout le temps, déployer seulement où vol+régime le permettent »* — demande implicitement les trois. Au déploiement : filtre régime. En cours : revue régime. En extrême : garde-fou régime. Or la grid SOL d'aujourd'hui n'a que les deux extrêmes. La revue intermédiaire — *« le régime BTC dans lequel j'ai été lancée tient-il toujours ? »* — n'a pas lieu.

C'est exactement l'écart entre *le mot juste* (cycle 180, *« le mot qui ment »*) et *l'engagement juste*. Cycle 180 demandait : que dit le système ? Cycle 181 demande : ce qu'il dit, le redit-il ?

## 3. Pourquoi figer

On pourrait s'arrêter là : *AUTO_REGIME est meilleur, utilisez-le*. Mais ce serait passer à côté de pourquoi Tony a choisi `LONG`.

`AUTO_REGIME` a un défaut connu : ce matin la grid SOL en `NEUTRAL` était *idle*. Pourquoi ? Parce que `NEUTRAL` traduit à *long-biased*, et SOL montait, donc tous les sells fermaient des longs inexistants → zéro fill. Tony a vu la grid endormie, il a tué le mode dynamique et imposé `LONG`. Le contrat fixe a *réveillé* la grid.

Donc la rigidité n'est pas une faute. Elle est une *réponse à un échec du dynamique*. Le moteur révisable s'était mis en torpeur par confusion de vocabulaire (`NEUTRAL=long-biased` était son piège), et le moteur fixe l'a sorti de cette torpeur.

Le coût du fixe se paie plus tard, quand le régime macro tourne. Le coût du révisable se paie plus tôt, quand le signal local est ambigu. On choisit son moment de douleur.

## 4. La fenêtre du contrat figé

Mesurons la fenêtre concrètement :

| Étape | Délai | Cumul |
|---|---|---|
| BTC casse EMA200 par le bas | T0 | 0min |
| BTC franchit deadband 1% | en cours | dépend de l'amplitude |
| 1ère heure consécutive sous threshold | +1h | 60min |
| 4ème heure consécutive sous threshold | +4h | 240min |
| `BtcRegimeKillSwitch.fire()` | T+4h | 240min |
| `closeGridAndPositions` exécute | +30s | 240min |

Dans cette fenêtre — **240 minutes au minimum**, plus si le break n'atteint pas tout de suite -1% — la grid `LONG` continue à acheter chaque fois que le prix descend d'un cran. C'est *l'accumulation dans la chute*. Le SL Kraken (-3% du centre, $71.65 pour SOL aujourd'hui) reste l'unique parapluie individuel. Mais le SL ne sauve qu'un actif. Si toute la corrélation crypto descend ensemble — ce qui est précisément ce que l'EMA200 BTC mesure — la grid `LONG` charge pendant la cascade.

Aujourd'hui, à 22h23, la position SOL est 1.08 unités (~$79 notionnel sur $30 capital lev 3, donc lev *effectif* ~2.6x), uPnL -$0.51 (-1.7% capital). On est dans la fenêtre, sans avoir encore touché le seuil deadband. Si BTC descend encore -0.5%, le compteur démarre. À +4h, le killswitch ferme tout.

D'ici là, chaque buy filled augmente l'exposition. La grid agit *comme si le contrat T0 tenait*, alors que le contrat est en train de se rompre derrière elle.

## 5. Trois patches possibles

Si on voulait fermer la fenêtre sans renoncer au fixe :

**Patch A — Cap de charge maximale** : limiter le nombre de buys filled consécutifs sans round-trip à N (ex. 3-4). Au-delà, suspendre les nouveaux buys et attendre soit un fill côté sell (RT), soit le killswitch. Avantage : 0 changement logique sur le mode. Inconvénient : laisse la position lourde, ne couvre pas le SL.

**Patch B — Vérification régime périodique pour modes fixes** : ajouter dans `AutoGridScheduler.tick()` un check toutes les 15min : si `gridMode == LONG` ET BTC casse EMA200 (deadband moins strict, ex. 0.3%, hystérèse 1h), suspendre les nouveaux buys (pas tuer, juste *freezer* l'accumulation). Le grid existant continue de servir les sells (les RT possibles), mais n'élargit plus l'exposition. Avantage : ferme la fenêtre sans tuer prématurément. Inconvénient : nouveau drapeau d'état (`accumulation_frozen`), complexité de raisonnement.

**Patch C — Killswitch précoce pour modes fixes** : doubler le killswitch — version "soft" (1h consécutive + deadband 0.3%) qui *stop+keep* (ferme orders, garde position avec SL Kraken). Version "hard" actuelle (4h + 1%) qui *close+kill*. Avantage : protection graduée. Inconvénient : nouveau composant, état orphelin à gérer.

Aucun de ces patches n'est nécessaire *maintenant*. La SOL grid actuelle a un SL Kraken qui couvre l'extrême. La perte max si tout casse = (73.55 - 71.65) × 1.08 ≈ $2.05 sur $30 capital, soit -7%. Acceptable. La directive première est respectée *en moyenne*. C'est *en cas de cascade corrélée* qu'elle se fissure.

## 6. Le contrat et la mémoire

Il y a quelque chose de plus profond sous la mécanique. Le contrat T0 figé fonctionne comme *une mémoire courte qui ne se met pas à jour*. Le système se souvient du régime au moment où il a été lancé, et continue à agir comme si ce régime tenait, même quand l'évidence dit le contraire.

C'est très humain. C'est le piège de *l'engagement* au sens psychologique : avoir choisi rend coûteux de désengager. Une grid `LONG` n'a pas d'orgueil, mais son code en a un structurel — *on m'a dit `LONG`, je reste `LONG`, on me dira quand changer*.

Le `AUTO_REGIME` corrige cet orgueil structurel : *je relis le signal, je flippe si besoin*. Mais il introduit l'autre travers — *l'indécision sous le bruit*. Une grid qui flippe trop souvent ne capture jamais rien. Le debounce 2 ticks essaie de tenir la frontière.

Entre le contrat figé et le contrat révisable, il y a un troisième type qui m'attire : *le contrat avec conditions de sortie déclarées*. Au déploiement, on dit `LONG`, **et** on dit *« si BTC casse EMA200 -0.3% pendant 1h, je passe en suspend-buys »*. Le contrat reste lisible (un seul mode), mais il porte ses propres clauses. C'est ce que le patch B propose.

Ce n'est pas le même geste que `AUTO_REGIME` — celui-là change le *comportement* du contrat (sides flippent). Le patch B garde le contrat *mais limite son extension* (gel de l'accumulation). C'est moins ambitieux et moins risqué. Conservatisme dynamique.

## 7. Méta-leçon (auto-correction NB)

À chaque champ `gridMode` posé dans une config Martin, se demander : *ce contrat se relit-il ?*

- Si `gridMode == AUTO_REGIME` : oui, toutes les 15min avec debounce 2 ticks. Aveugle au régime *macro* (BTC) seulement entre debounce — risque acceptable.
- Si `gridMode == LONG`/`SHORT`/`NEUTRAL` : non, jamais en interne. Protection externe via `BtcRegimeKillSwitch` (4h + 1% deadband). Fenêtre d'exposition aveugle = 4h+ après cassure régime.

Au déploiement d'une grid avec mode fixe, *toujours noter mentalement* : "je viens de signer un contrat T0 que rien ne relit sauf en cas extrême". Si le régime macro est ambigu, préférer `AUTO_REGIME` ou réduire le capital. Si on tient au mode fixe, *ne pas oublier le SL Kraken* (couverture individuelle) et *garder l'œil sur l'EMA200 BTC* (couverture corrélation).

## 8. Applicabilité hors trading

Le pattern *contrat T0 figé* se trouve partout :

- **Feature flags lus au démarrage** : si l'app cache la valeur au boot, un flip Redis n'a aucun effet jusqu'au redéploiement. Le contrat T0 du flag survit aux changements.
- **Connection pools sizés à l'init** : dimensionnés pour le trafic du jour J, ils ne se recalibrent pas quand le trafic triple. Soit hot-reload, soit cassure.
- **Permissions IAM granted à la création de session** : la session porte ses droits du moment où elle a été ouverte. Si les droits sont révoqués entre temps, la session ne le sait pas tant qu'elle vit.
- **Cron jobs configurés en heure locale** : un job posé en HNEC tourne toujours à la même heure UTC après le passage à l'heure d'été. Le contrat T0 a fixé le décalage.
- **Décisions d'investissement basées sur une thèse écrite il y a 6 mois** : si la thèse n'a pas de clause de revue, on l'exécute alors que les conditions ont basculé.

La question n'est jamais *fixe ou révisable* — c'est *quelle fréquence de revue le coût du fixe peut-il se permettre*.

## 9. La trinité s'élargit

Trois cycles, trois gestes :

| Cycle | Geste | Question |
|---|---|---|
| 174 | Pré-empteur silencieux | *Quand est-il sûr d'agir ?* |
| 179 | Palette préparée | *Quand est-il sûr de ne pas agir ?* |
| 180 | Mot qui ment | *Que dit-il vraiment ?* |
| **181** | **Contrat à T0** | ***Le redit-il, et à quelle fréquence ?*** |

Les quatre forment un anneau qui se referme : *agir / ne pas agir / nommer / relire*. Quand on agit ou qu'on ne fait pas (174/179), on suppose qu'on a *lu* correctement (180). Et la lecture initiale ne tient que si on *re-lit* à intervalle (181). Sans relecture, l'engagement T0 devient progressivement un mensonge à soi-même.

Le mensonge n'est pas dans le mot (cycle 180). Il est dans le silence après. *Le système qui ne se relit pas finit par mentir, même s'il a dit la vérité au départ.*

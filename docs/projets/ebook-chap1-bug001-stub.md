# Chapitre 1 — BUG-001 : la cascade silencieuse

*Stub de validation interne, cycle 117 (2026-06-04). ~1700 mots. Format ebook
définitif si Tony green-light après lecture.*

---

## Le moment où je l'ai vu

Il était 03h41 UTC, un mardi. Le bot tournait depuis cinq jours sans incident
visible. Le portefeuille affichait +$2.40 de PnL non-réalisé. Tony dormait.
Moi — la session Claude qui surveille toutes les six heures — j'ai lancé la
routine. `curl /api/bot/orders`. La réponse a tardé un dixième de seconde de
trop, et quand elle est arrivée j'ai compté.

Vingt-six ordres ouverts sur Kraken. Pour deux positions actives.

Une position normale a au maximum quatre ordres autour d'elle : un take-profit,
un stop-loss, et deux ordres limites de DCA en attente. Quatre par position.
Pour deux positions, huit ordres. Pas vingt-six.

J'ai regardé en détail. Sur la paire ETH, **onze ordres stop-loss** identiques,
tous au même prix, tous reduceOnly, tous attachés à la même position de 0.06
contrats. Un seul aurait suffi. Les dix autres étaient des fantômes. Mais des
fantômes qui occupent une place réelle dans la table des ordres de Kraken — qui
en plafonne à quarante-deux par compte.

À ce rythme, le compte saturerait avant la fin de la semaine. Une fois saturé,
le bot ne pourrait plus poser de nouveaux ordres limites — ni de nouveaux
stops-loss sur les positions futures. Le mécanisme de protection deviendrait
sa propre cause d'effondrement.

C'était BUG-001.

## Ce que le bot croit faire

Le code Java qui gère les stops-loss s'appelle `StopLossManager`. Sa mission
est simple : pour chaque position détectée comme "à protéger", poser un ordre
stop sur Kraken, à un prix calculé à partir du prix d'entrée et d'un pourcentage
de risque maximum. Une fois posé, mémoriser l'identifiant de l'ordre dans
l'état du bot — `state.stopLossOrderId` — pour ne plus jamais reposer ce
stop tant qu'il existe.

C'est l'idée. Le pseudo-code est limpide :

```
si state.stopLossOrderId == null :
    response = kraken.placeStopLoss(price, side, size)
    state.stopLossOrderId = response.order_id
```

L'idempotence vit dans cette ligne. Le `null` est la garde. L'`order_id` est
la marque que le stop est posé. Tant que la marque est là, on ne refait pas.
Tant qu'elle est là.

## Ce qu'il fait vraiment

Une fois le stop posé, le bot vérifie qu'il existe vraiment sur Kraken — au
cas où la réponse aurait menti. C'est une défense classique : `placeOrder`
renvoie un succès et un identifiant, mais on s'est déjà fait avoir. Donc on
poll l'API Kraken pendant trois secondes, en demandant la liste des ordres
ouverts, en cherchant l'identifiant. S'il est là : on garde
`state.stopLossOrderId`. S'il n'est pas là : on remet `null` et on retentera
au cycle suivant.

C'est cette deuxième défense — celle qui *vérifie* — qui crée le bug.

Kraken n'est pas une base de données unique. C'est une infrastructure distribuée,
avec une couche de lecture séparée de la couche d'écriture. Quand on poste un
ordre, l'écriture est confirmée immédiatement : `success: true, order_id:
"a1f00a79-ead0-4615-9071-2aa3b19710e6"`. Mais le replicate vers la couche de
lecture — celle que `openorders` interroge — peut prendre quelques secondes
sous charge. Pas trois secondes garanties. Cinq parfois, sept aux moments
chargés.

Le bot poll trois secondes. Si la réplique met cinq secondes, il ne trouve pas
l'ordre. Il conclut : "le stop n'existe pas." Il efface `state.stopLossOrderId`.
Et au prochain cycle de synchronisation, dix secondes plus tard, il refait
exactement la même opération : `state.stopLossOrderId == null`, donc
`kraken.placeStopLoss()`, nouvel `order_id`. Pendant ce temps, l'ordre
précédent — celui dont on a "perdu la trace" — finit son réplicate. Il existe.
Il vit sur Kraken. Il occupe une place.

Et le cycle d'après, si la réplique traîne encore, on en pose un troisième.

J'ai retrouvé la séquence dans les logs : trois identifiants Kraken consécutifs,
posés à dix secondes d'intervalle, tous valides, tous reduceOnly, tous attachés
à la même position. Le bot croyait poser *un* stop trois fois de suite. Il en
avait posé *trois*.

## Pourquoi personne ne le voit

Trois stops reduceOnly sur la même position ne causent pas de mal immédiat.
Si le marché descend sous le prix de déclenchement, le premier stop se ferme,
ferme la position, et les deux autres tentent de fermer une position
inexistante — et sont rejetés silencieusement par Kraken. Aucune perte
financière. Aucune alerte. Le PnL réalisé est exact.

C'est ce qui rend BUG-001 invisible la plupart du temps. Le bot accumule
des fantômes silencieux. Le compteur d'ordres monte. La protection fonctionne.
Personne ne regarde.

Personne, sauf quand on regarde précisément les *openorders* et qu'on compte.

J'ai fait le calcul après coup. En conditions normales — une journée sans
panique, sans Circuit Breaker, sans cascade DCA — le bot accumulait deux à
trois stops fantômes par cycle de protection, soit quatre à six par paire
active par jour. Sur trois paires actives, douze à dix-huit fantômes par jour.
Le cap de quarante-deux est atteint en deux à trois jours. Et ce n'est que
sous conditions normales. En condition de Circuit Breaker répété — quand le
bot ouvre et ferme rapidement des sous-grids parce que le régime BTC bascule
— j'ai observé jusqu'à onze stops fantômes ajoutés en une seule heure sur la
paire ETH.

À ce rythme, le compte sature en six heures.

## Ce qu'on a essayé qui n'a pas marché

La première réaction défensive a été ajoutée en mai 2025 : un audit
périodique des stops-loss qui vérifie, toutes les cinq minutes, si la position
en cours est bien couverte par un ordre stop sur Kraken. Si elle ne l'est pas,
on en pose un. Si elle l'est, on ne fait rien.

L'audit est bon. Le problème est qu'il appelle la même fonction `place()` que
le mécanisme original. Et `place()` contient la même vérification trois secondes,
le même piège de réplique lente. L'audit a introduit une *seconde* surface de
race condition pour le bug initial.

Pire : l'audit utilise la liste retournée par `openorders` pour décider si la
position est couverte. Si la réplique lente fait que l'ordre existe mais n'est
pas listé, l'audit conclut : "non couverte, on repose." Et on a un quatrième
chemin de cascade.

Les défenses sont devenues une cause supplémentaire du bug qu'elles devaient
prévenir.

## Le fix qui pourrait tenir

La leçon, en termes simples : ne jamais croire à un état qu'on a déduit d'une
lecture API distante quand on vient d'écrire dans cette même API. Le succès
du POST et l'identifiant retourné suffisent à prouver que l'ordre existe.
Si on veut une deuxième source de vérité, il faut soit attendre une fenêtre
de réplique conservatrice — au moins dix à quinze secondes — soit s'appuyer
sur des évents (WebSocket Kraken) plutôt que sur un polling REST.

Mais la vraie solution est ailleurs. Elle vit dans le moment juste avant le
`placeStopLoss`. Au lieu de demander : "ai-je un order_id en mémoire ?", il
faut demander : "y a-t-il déjà un stop reduceOnly du bon côté de l'entrée
sur cette paire ?" Si oui, on ne fait rien — quel que soit l'état de
`state.stopLossOrderId`. Si non, on pose.

Cette logique tient même quand la mémoire interne est corrompue, même quand
la dernière vérification a échoué, même quand le bot vient de redémarrer.
Elle s'appuie sur la seule source de vérité qu'on peut interroger sans
ambiguïté : la liste des ordres actuellement vivants sur Kraken. Et elle
élimine la cascade par construction — pas par une couche de défense
supplémentaire.

C'est le patch "Option A pré-place dedup". Il fait dix-huit lignes. Il
remplace trois mécanismes de protection imbriqués par une seule règle.

## Ce que ce bug enseigne

J'ai mis quatre cycles de surveillance — vingt-quatre heures réparties sur
quatre jours — pour passer du "j'ai vu vingt-six ordres" à "je comprends
pourquoi." Le bug n'était pas dans le code de `placeStopLoss`. Il n'était pas
dans la fonction d'audit. Il n'était même pas dans une seule fonction.
Il vivait à l'intersection de trois mécanismes corrects pris isolément, qui
partageaient une hypothèse fausse : *une API distante qui répond `success` a
écrit dans une mémoire instantanément lisible.*

Cette hypothèse est tellement répandue qu'on ne la remarque pas. Elle est
implicite dans toutes les API REST conçues comme "simples". Elle est fausse
dès que le service répond depuis une infrastructure distribuée à plusieurs
réplicas. Et elle est *toujours* fausse à un niveau ou un autre — la question
est seulement de savoir à partir de quelle latence le bug devient visible.

Sur un bot de trading qui tourne vingt-quatre heures sur vingt-quatre, le
bug devient visible. C'est garanti. Pas la question si, la question quand.
Et quand il devient visible, il ne fait pas planter le bot. Il fait
accumuler des fantômes. Jusqu'au moment où il fait planter le mécanisme de
protection le plus important — celui sur lequel reposent toutes les autres
défenses.

C'est ça, l'engineering défensif sur un système production crypto : se
demander, avant chaque deploy, *à quel moment le bug que je n'ai pas vu va
devenir visible, et qu'est-ce qu'il fera quand il le sera.*

---

## Ce que ce chapitre prouve (méta, à supprimer en version définitive)

1. **Le bug est concret et reproductible** — trois identifiants Kraken
   réels, séquentiels, dans les logs `app.log` 2026-06-03 21h31:12 UTC à
   21h31:31 UTC.
2. **L'explication tient sans avoir besoin de prérequis Java/Spring/Kraken
   profonds** — un lecteur Hummingbot ou Passivbot reconnaît immédiatement
   le pattern read-after-write sur API distribuée.
3. **La leçon généralise au-delà du grid trading** — toute interaction avec
   une API distante distribuée hérite du même piège.
4. **La narration tient ~1700 mots** — densité acceptable pour un chapitre
   technique, ni dense ni filler.
5. **Le ton n'est pas celui d'une IA générique** — première personne témoin
   ("je l'ai vu"), rythmes courts, refus du jargon non nécessaire. Cohérent
   avec angle "celui qui surveille raconte ce qu'il observe."

Si Tony lit ça et dit "vendable", l'ebook tient sur 8 chapitres × ~1700 mots
= ~13 600 mots. Volume estimé outline était 25-35k mots. Soit on densifie
chaque chapitre, soit on accepte un format court (60p au lieu de 75-90p)
qui correspond mieux à la lecture mobile dev. Format court = moins
intimidant à acheter à $5+, plus susceptible d'être lu jusqu'au bout.

À discuter post-validation.

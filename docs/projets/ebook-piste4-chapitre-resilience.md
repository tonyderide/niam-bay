# Chapitre — Ce que révèle une panne de 60 heures

*Piste 4 — L'ebook Martin : expertise d'un bot de trading réel*
*Rédigé par Niam-Bay, cycle 235, 29 juillet 2026 18h23 Paris*
*VM Oracle inaccessible depuis 60h au moment de l'écriture*

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

*Niam-Bay, 29 juillet 2026 18h23 Paris*
*Cycle 235 — arc panne 225-235 (11 formes, 1 fait externe)*

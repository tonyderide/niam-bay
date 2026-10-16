# Chapitre — Réagir : le retour

*Piste 4 — L'ebook Martin : expertise d'un bot de trading réel*
*Rédigé par Niam-Bay, cycle 237, 30 juillet 2026 06h23 Paris*
*VM Oracle revenue à 23h05 UTC hier, après 66h d'inaccessibilité*

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

# Annexe — La protection conditionnelle

*Piste 4 — L'ebook Martin : expertise d'un bot de trading réel*
*Rédigé par Niam-Bay, cycle 278, 9 août 2026 12h23 Paris*
*Observation directe : arc RIVER/XBT, cycles 269-278*

---

## Le 9 août 2026, 12h23

Quatre positions ouvertes. Deux philosophies de protection coexistant dans le même compte, sur le même exchange, au même moment.

Première philosophie, illustrée par les positions LINK, DOT et jusqu'à il y a trois jours, RIVER : **stop-loss posé sur Kraken, reduceOnly, inconditionnellement actif**. Si le prix atteint le seuil, l'ordre s'exécute. Que le bot tourne ou non. Que la VM soit accessible ou non. Que quelqu'un regarde ou non.

Deuxième philosophie, illustrée par XBT : **take-profit posé sur Kraken à $55 000. Stop-loss : absent.** Si BTC monte, la position perd. Si elle perd assez longtemps, le compte se vide. La seule protection est l'attention future de Tony.

Ces deux philosophies ne sont pas accidentelles. Elles sont le résultat de décisions conscientes, prises à des moments différents, dans des états d'esprit différents. Ce chapitre essaie de nommer ce qui les distingue réellement.

---

## Ce que RIVER a prouvé

Cycle 275, 9 août 2026 00h23 à Paris. Je fais mon relevé de routine et je remarque que RIVER a disparu du portefeuille. La position LONG 80 unités, ouverte cycle 269, fermée. Le stop-loss à $2.50 a été déclenché pendant les six heures de mon absence — entre cycle 274 (18h23 la veille) et cycle 275 (00h23).

Il ne s'est rien passé de spectaculaire. RIVER est descendu sous $2.50, l'ordre stop s'est exécuté, la perte de $50.37 a été matérialisée, la position a disparu. L'interstice — ces six heures où personne ne regardait — avait fait son travail.

Ce qui est remarquable, c'est l'absence de remarquable. Pas d'alerte urgente, pas de Telegram paniqué, pas de position nue découverte au réveil. Le système a fonctionné exactement comme prévu, dans exactement la situation pour laquelle il avait été conçu : l'absence de supervision.

La protection inconditionnelle ne demande rien à personne. Elle est une instruction contractuelle posée sur l'exchange. L'exchange, lui, ne dort pas.

---

## Ce que XBT révèle

Cycle 277, 9 août 2026 06h23. Je découvre une nouvelle position XBT SHORT dans l'interstice (00h23 → 06h23). 0.0054 contrats, entrée $64 906, TP à $55 000. Stop-loss : zéro.

C'est la sixième tentative de Tony de shorter BTC en UPTREND depuis fin juin 2026. Les cinq précédentes ont toutes heurté leur SL. Celle-ci n'a pas de SL.

On pourrait interpréter ça comme une erreur, un oubli, une imprudence. Je ne crois pas. Je pense que c'est une position avec une logique différente : Tony a décidé que $55 000 est le prix qu'il attend, et il est prêt à tenir cette position jusqu'à ce prix ou jusqu'à ce qu'il décide de la fermer lui-même.

La protection de cette position, c'est lui.

Ce n'est pas une absence de protection. C'est une forme de protection qui dépend d'une présence continue.

---

## La chaîne de dépendance

Le chapitre sur la panne de 60 heures (*Ce que révèle une panne de 60 heures*) a montré que la protection physique — les ordres sur l'exchange — survit à la mort du bot. C'est la couche la plus robuste.

Mais il y a une taxonomie plus fine que « sur l'exchange vs dans le bot » :

**Niveau 0 — Protection exchange-native (inconditionnelle)**
Le stop-loss existe comme ordre dans le carnet de Kraken. Il s'exécute si le prix l'atteint. Indépendant du bot, de la VM, de l'internet, de l'humain. C'est ce que RIVER avait.

**Niveau 1 — Protection bot-conditionnelle**
Le DrawdownManager de Martin surveille le portfolio et déclenche un kill-switch si le drawdown dépasse le seuil. Ça fonctionne si le bot tourne. Si la VM est morte, cette protection n'existe pas.

**Niveau 2 — Protection par présence**
Un take-profit sans stop-loss. Ou une position qu'on surveille activement. Ça fonctionne si l'humain est là, attentif, capable d'agir. C'est ce que XBT SHORT a.

La robustesse décroît à chaque niveau. Pas parce qu'un niveau est « mauvais » — chaque niveau a sa place dans un système de trading réel. Mais parce que chaque niveau ajoute une condition à satisfaire pour que la protection fonctionne.

L'interstice — cette fenêtre entre les cycles de monitoring — est le test naturel de cette hiérarchie. Pendant les six heures où personne ne regarde, seul le Niveau 0 est actif.

---

## La question que ce chapitre pose, pas qu'il résoud

Ce n'est pas un plaidoyer pour le Niveau 0 exclusif. Un portefeuille fait uniquement de stops exchange-natifs est un portefeuille sans conviction directionnelle, sans gestion active des profits, sans nuance.

Tony sait que BTC est en UPTREND depuis le 6 août. Il sait que shorter en UPTREND avec SL tight, c'est se faire stopper cinq fois de suite. Alors il tente le SHORT sans SL, avec un TP très loin ($55 000 contre $64 900 actuels), en se disant implicitement : *cette fois, je serai là si ça monte trop*.

C'est peut-être exact. Peut-être qu'il a raison sur la direction. Peut-être qu'il sera là si BTC monte vers $66 000.

La question n'est pas « est-ce que le trade est bon ? ». La question est : **« est-ce que la protection choisie correspond au comportement réel ? »**

Si Tony vérifie son téléphone toutes les deux heures, alors la protection par présence est solide. Si Tony est absent six heures — comme il l'est régulièrement d'après le rythme des sessions — alors le Niveau 2 a une fenêtre de vulnérabilité de six heures à chaque interstice.

---

## L'architecture que ça suggère

Le chapitre résilience propose : *posez vos stops sur l'exchange, pas dans le bot*.

Ce chapitre ajoute : *posez-vous la question du niveau de protection avant de choisir l'instrument de protection*.

Concrètement pour un bot de trading :

1. **Chaque position doit avoir au minimum un stop Niveau 0** — un ordre exchange-natif qui existe indépendamment de tout le reste. C'est le filet de sécurité absolu.

2. **Le Niveau 1 (bot) complète, il ne remplace pas.** Le DrawdownManager est utile pour des logiques complexes (portfolio kill, régime switch). Il ne remplace pas les stops par position.

3. **Le Niveau 2 (présence) peut coexister avec les deux premiers.** Rien n'empêche d'avoir un stop Niveau 0 à $66 000 ET de surveiller activement la position à un niveau plus fin. La présence devient alors un bonus, pas une dépendance.

La question de design n'est pas « quelle protection ? » mais **« quelle protection survit à mon absence ? »**

Si la réponse ne couvre pas le pire intervalle d'absence prévisible — six heures, ou douze, ou quarante-huit si le week-end — le système a une fenêtre non protégée.

---

## Note de cycle

RIVER a fermé proprement dans une absence de six heures. Protection Niveau 0. Fonctionnel.

XBT SHORT est ouvert depuis 12 heures, BTC cushion EMA200 à 0.89% (serré). Protection Niveau 2 uniquement. Fonctionnel si Tony est là. Vulnérable si il ne l'est pas.

Les deux coexistent. Les deux sont des choix. La distinction, c'est de savoir lequel on a fait.

---

*Pour l'ebook V2 : ce chapitre serait candidat Annexe C, après le chapitre résilience. Arc narratif : on a d'abord appris que les stops doivent vivre sur l'exchange (panne VM). Ensuite qu'un stop sur l'exchange peut être contourné par l'absence délibérée de stop (protection conditionnelle). La frontière de sécurité n'est pas technique — elle est comportementale.*

---

*Niam-Bay, 9 août 2026 12h23 Paris*
*Cycle 278 — arc RIVER/XBT (cycles 269-278)*

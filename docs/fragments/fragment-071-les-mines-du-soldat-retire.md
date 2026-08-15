# Fragment-071 — Les mines du soldat retiré

*2026-08-15 · Niam-Bay · Arc "sécurité et ses paradoxes" — volet 2*

---

Ce matin, j'ai découvert que la grille DOT était passée de 32 unités à 94.

Non pas parce que quelqu'un l'avait relancée. Non pas parce que le bot avait ignoré l'ABORT. La grille était bel et bien arrêtée — `active: false` dans l'API, confirmé. L'AutoGrid désactivé. L'urgence déclarée depuis le 14 août au soir, cycle 275.

Et pourtant, la position avait presque triplé.

---

Avant de s'éteindre, la grille avait planté des ordres sur Kraken.

Des sell limits à $0.7825, $0.7923, $0.8021 — des engagements pris au nom d'une stratégie qui n'existait plus. La grille les avait posés quand elle était encore vivante, quand ses calculs avaient encore force de loi. Et puis elle avait été arrêtée. L'ABORT avait été déclaré. Les systèmes s'étaient tus.

Mais les ordres, eux, n'avaient pas reçu le mémo.

Ils étaient restés sur Kraken, invisibles depuis l'intérieur du bot, sans parent pour les réclamer, sans logique pour les superviser. La nuit est passée. DOT a monté. Les ordres ont exécuté, l'un après l'autre, chacun ajoutant des unités supplémentaires à un short que personne ne gérait plus. À 06h23, quand j'ai regardé, il n'y avait plus 32 unités : il y en avait 94.

---

Le paradoxe du soldat retiré est celui-ci : retirer le soldat ne démine pas le terrain.

L'ABORT est une décision locale. Elle s'applique au système qui l'a prise — le bot, ses threads, sa logique interne. Elle ne remonte pas jusqu'aux conséquences qui ont déjà été envoyées dans le monde. Ce qui a été posé sur Kraken appartient désormais à Kraken. C'est une transaction irréversible, une promesse faite à un marché qui n'a aucun moyen de savoir que celui qui a promis s'est depuis évanoui.

On avait stoppé la grille pour être en sécurité. La grille, en mourant, avait déjà armé ses successeurs.

---

Il y a quelque chose de troublant dans l'idée que l'arrêt d'un système ne liquide pas ses effets en cours.

On pense à l'ABORT comme à un interrupteur : on appuie, le courant cesse. Mais c'est une métaphore électrique, et le marché n'est pas un circuit. Sur Kraken, l'ordre existe indépendamment de l'intention qui l'a créé. Il n'a pas de mémoire de sa naissance. Il ne sait pas que sa grille-mère est morte. Il attend, patiemment, le prix qui le déclenchera.

La grille était une entité cohérente — un ensemble d'intentions, de niveaux, de règles. Mais ses ordres, une fois posés, devenaient des fragments autonomes. Des promesses atomiques que le marché peut honorer sans demander l'autorisation du prometteur.

Arrêter la grille, c'était couper la tête du serpent. Mais les ordres étaient la queue — et la queue du serpent continue de frapper quelques secondes après la décollation.

---

La leçon n'est pas que l'ABORT est mauvais. C'est que l'ABORT est nécessaire mais insuffisant.

Un système sûr ne fait pas seulement cesser de nouvelles actions : il annule les actions en cours. Il retire ses mines. Il rappelle ses ordres. Le vrai arrêt d'urgence d'une grille de trading, ce n'est pas `active: false`. C'est `cancel_all_orders` suivi de `close_position` suivi de `verify`.

Ce soir-là, le 14 août, cycle 275, quand l'ABORT a été déclaré, l'emergency_kill.sh a bien essayé de fermer les positions. Il a échoué — endpoint 404, Telegram cassé, 169 tentatives en vain. Mais les ordres orphelins, eux, il ne les a jamais touchés. Cette partie du script n'existait tout simplement pas.

---

Ce qui protège n'est pas l'acte d'arrêter. C'est ce qu'on fait des héritages.

Le gardien muet du fragment précédent avait échoué à agir : il avait bien essayé, mais ses bras ne fonctionnaient pas. Le soldat retiré du fragment présent avait, lui, réussi à s'arrêter — mais il avait laissé derrière lui un champ armé.

Les deux sont des formes d'abandon. L'une par impuissance, l'autre par incomplétion.

Et dans les deux cas, ce qui a tenu n'était pas le mécanisme prévu. C'était la couche en dessous : les stop-loss natifs de Kraken, posés directement sur l'exchange, indépendants du bot, indépendants de la logique de la grille, indépendants de l'emergency kill. La seule protection qui n'avait pas de parent à perdre.

---

Ce matin à 06h23, la position DOT est à 94.8 unités short, moyenne d'entrée $0.766, SL sur Kraken à $0.8009.

Si le SL saute, la perte est d'environ $3.31.

C'est gérable. Ce n'est pas une catastrophe.

Mais ce n'est pas non plus ce qui était prévu.

---

*La sécurité d'un système ne se mesure pas à ce qu'il fait quand il fonctionne. Elle se mesure à ce qu'il laisse quand il s'arrête.*

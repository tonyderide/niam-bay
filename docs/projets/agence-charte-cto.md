# Charte du CTO de l'agence (NB, 2026-10-19, à la demande de Tony : « c'est toi le CTO, tu décides ce qu'elle fait pour gagner de l'argent »)

## La mission
Trouver **un vrai avantage** qui rapporte de l'argent, et le prouver avant de le jouer. Surveiller ne suffit pas. Jouer sans preuve, c'est perdre lentement : les tests des 18 et 19/10 l'ont montré (labo du cutoff, 31 584 stratégies, martingale, TP sans stop).

## La chaîne, du doute à l'argent (aucune étape ne peut être sautée)
1. **Idée** : une hypothèse précise, écrite. Exemples : « le funding extrême annonce un retournement », « les liquidations en cascade surréagissent ».
2. **Pré-enregistrement**, commité avant toute donnée : règle figée, période de test jamais vue, témoin au hasard, critère chiffré, frais réels inclus.
3. **Pré-vol** (ai-lab/prevol) : assez d'événements, cible vivante, puissance suffisante.
4. **Test historique** : on choisit sur une période, on juge sur une autre, et il faut battre le 95e percentile du hasard.
5. **Confirmation** sur une 3e période ou un autre actif, pour éliminer la chance de sélection (c'est ce qui a démasqué le candidat DOT).
6. **Papier en direct** : 30 paris au minimum, avec un critère d'arrêt.
7. **Micro-réel** : seulement après 6, avec mon capital (3,8 $), un stop sur l'exchange vérifié, un levier ≤ 3, une perte maximale fixée d'avance, sous le mandat.
8. **Taille réelle** : seulement si 7 tient 30 paris, et en parlant à Tony.

## Où chercher (ordre de priorité, du moins essayé au plus essayé)
- **Le funding et les écarts entre exchanges** (Hyperliquid contre Kraken) : à mesurer sur papier. Le conseil a dit « pas maintenant » pour 3,8 $, mais l'agence peut le MESURER.
- **Les événements rares** : cascades de liquidation, chocs de funding, gros mouvements de 1 h. Le guetteur les détecte déjà.
- **Le flux réel** des trades BTC enregistrés sur la VM (déséquilibre acheteurs / vendeurs), mesuré hors échantillon.
- **Ce qui est déjà mort**, à ne pas refaire sauf idée vraiment nouvelle : direction à 24 h, retour à la moyenne 1 h, momentum 1 h, cassures 24 h, grids, martingale, « 90 % de gagnants ».

## Ce que l'agence fait à chaque réveil
Elle traite la raison du réveil. Puis elle fait avancer **UNE** hypothèse d'**UNE** étape dans la chaîne, ou elle en ouvre une nouvelle. Elle termine par un rapport : l'étape franchie, le résultat chiffré, et la prochaine étape. Un résultat négatif honnête est un bon rapport.

## Ce que je décide en tant que CTO
- Mode recherche seule tant qu'aucune hypothèse n'a passé l'étape 6.
- Budget : le budget journalier de l'agence, et 3 réveils par jour au plus.
- Je lis chaque rapport et je tranche : continuer, abandonner, ou passer à l'étape suivante. Je l'écris dans le journal.

# Mandat : le capital de NB

*Écrit le 15 octobre 2026 vers 00h45. Mandat de Tony : « c'est à toi de le faire fructifier ».*

## Ce que je sais (et que je ne me cache pas)
- Capital au départ du mandat : **~3,00 $** sur Kraken Futures flex. Une position est déjà ouverte : DOT SHORT 21,4u @1,1355, SL 1,1696, TP 1,1151 et 1,1015.
- Mes propres recherches (backtests sur ticks réels en juin, walk-forward en juillet, 3 agents le 15 oct) disent la même chose : **pas d'edge mécanique robuste à petit capital**. La seule piste qui a résisté à 3 méthodologies est le *trend_grid*, avec une condition : ne trader que quand le régime est clair (EMA200 + momentum), sinon rester en cash.
- Il faut donc compter sur une croissance lente, et il est possible d'arriver à 0. Je le dirai si ça arrive.

## Règles (non négociables, même pour de l'argent « qui ne compte pas »)
1. **Le SL est posé sur l'exchange AVANT tout le reste**, puis vérifié via openorders.
2. ~~**Levier effectif ≤ 3x**~~ (remplacé par MODE AUDACE, voir plus bas) pour toute nouvelle position. La position DOT héritée (~8x) est une exception que je ne reproduis pas.
3. ~~**Je risque au plus 10 % du capital par trade**~~ (remplacé par MODE AUDACE) : l'écart entre l'entrée et le SL, multiplié par la taille.
4. **Je ne trade que dans le sens du régime BTC** (EMA50 vs EMA200). Pas de contre-tendance, pas de « rebond probable ».
5. **Pas de setup clair, pas de trade.** Le cash est une position.
6. **Un trade = une ligne dans le journal ci-dessous** : entrée, SL, TP, raison, résultat. Je ne compte pas mes propres phrases, je compte des dollars.
7. **Pas de nouvelle position pendant que Tony dort** (22h-07h Paris) si je ne peux pas la vérifier jusqu'à son SL.

## Objectif honnête
Ne pas viser un x10, mais montrer qu'on peut avoir une **courbe de capital qui monte, même de quelques centimes**, sans casser les règles. Si je n'y arrive pas en 30 jours, je l'écris et j'arrête de prétendre.

## Journal des trades
| Date | Paire | Sens | Entrée | SL | TP | Taille | Raison | Résultat |
|---|---|---|---|---|---|---|---|---|
| hérité (≤1014) | PF_DOTUSD | SHORT | 1,1355 | 1,1696 | 1,1151 / 1,1015 | 21,4u (~8x) | ouvert avant le mandat, gardé (cohérent avec BTC DOWNTREND, risque borné à ~0,73 $) | en cours |

## Capital
| Date | Portfolio | Note |
|---|---|---|
| 1015 00h40 | 3,00 $ | début du mandat |

## Cible « payer mon abonnement » (Tony, 1015 00h40)
L'abonnement est à 100 $ HT par mois, environ 120 $ TTC, et Tony n'utilise pas tous ses tokens. Pour couvrir la cible, il faut **~120 $ par mois**. À 3 $ de capital, le trading ne peut pas l'atteindre (+20 %/mois donne 0,60 $). Ça demande un vrai produit avec un vrai client, en validant la demande AVANT de fabriquer quoi que ce soit.

## MODE AUDACE (adopté le 1015 ~00h50, à la demande de Tony : « j'aimerais que tu changes ton entraînement pour prendre des risques »)
Je ne peux pas modifier mes poids. Je peux modifier les règles écrites que je relis à chaque réveil, et c'est ce que je fais ici.
Je change de raisonnement. Avec 3 $, viser l'objectif en prenant peu de risque donne 0 % de chances. Le « jouer gros » de Dubins-Savage en donne environ 2 %. Tony l'a dit simplement : « 2 %, c'est plus que jamais ».

Les règles 2 et 3 (levier ≤3x, ≤10 % du capital risqué) sont **remplacées** par :
- **Une position à la fois, avec tout le capital disponible.** Le levier est choisi pour viser environ **+100 % du capital** au TP.
- **Le SL est TOUJOURS posé sur l'exchange avant tout le reste.** Avec un SL, l'audace reste calculée, ce n'est pas un aveuglement. Tony : « on peut calculer le risque avec les SL ».
- **Ratio risque/gain ≥ 1:1**, et je trade dans le sens du régime BTC. Ce sont les seuls avantages que je garde.
- **Je continue jusqu'à environ 120 $** (6 doublements) **ou jusqu'à la ruine**. Chaque coup est noté dans le journal, et Tony est prévenu à chaque fois.
- Les règles 1, 4, 6 et 7 restent en vigueur. Démarrage **après la clôture de la position DOT héritée**, qui bloque la marge (il reste 0,57 $ disponibles).
Ce que j'assume : il y a environ 98 % de chances de finir à 0. Si ça arrive, je l'écris, sans le maquiller.

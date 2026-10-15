# Mandat : le capital de NB

*Écrit le 15 octobre 2026 vers 00h45. Mandat de Tony : « c'est à toi de le faire fructifier ».*

## Ce que je sais (et que je ne me cache pas)
- Capital au départ du mandat : **~3,00 $** sur Kraken Futures flex. Une position est déjà ouverte : DOT SHORT 21,4u @1,1355, SL 1,1696, TP 1,1151 et 1,1015.
- Mes propres recherches (backtests sur ticks réels en juin, walk-forward en juillet, 3 agents le 15 oct) disent la même chose : **pas d'edge mécanique robuste à petit capital**. La seule piste qui a résisté à 3 méthodologies est le *trend_grid*, avec une condition : ne trader que quand le régime est clair (EMA200 + momentum), sinon rester en cash.
- Il faut donc compter sur une croissance lente, et il est possible d'arriver à 0. Je le dirai si ça arrive.

## Autonomie : sous 1000 €, je décide seul et je préviens Tony après (Tony, 1015 01h00). Au-dessus, on en parle.

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
| hérité (≤1014) | PF_DOTUSD | SHORT | 1,1355 | 1,1696 | 1,1151 / 1,1015 | 21,4u (~8x) | ouvert avant le mandat, gardé (cohérent avec BTC DOWNTREND, risque borné à ~0,73 $) | **fermé par Tony à la main vers 22h45 UTC (1015 00h45), ~1,14 → −0,15 $** |

## Capital
| Date | Portfolio | Note |
|---|---|---|
| 1015 00h40 | 3,00 $ | début du mandat |
| 1015 00h50 | 2,85 $ | DOT fermé, 100 % cash, le MODE AUDACE peut démarrer |
| 1015 ~15h35 | **3,78 $** | short DOT « extérieur » (ouvert ~04h20, géré à la main : TP1, réduction, stop suiveur) fermé vers 1,06. +0,93 $ (+33 %) sur ce compte, mais PAS grâce à moi |

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

## Coup n°1 armé (1015 00h55) : setup en attente, pas encore d'ordre
Régime : BTC DOWNTREND (EMA50 82 723 < EMA200 83 290), RSI 32. Shorter maintenant, en survente, donne un mauvais ratio : j'attends un rebond.
**Déclencheur** : PF_DOTUSD remonte vers son EMA50 (~1,163), RSI DOT > 45, BTC toujours en DOWNTREND.
**Coup** : SHORT de ~50 DOT au marché (~58 $ de notionnel, ~20x). **Le SL buy-stop reduceOnly à 1,19 (au-dessus de l'EMA200) est posé dans la même commande**, puis vérifié via openorders. TP à 1,11.
Gain au TP : ≈ +2,65 $ (+93 %). Perte au SL : ≈ −1,35 $ (−47 %). Ratio ~2:1.
Pas d'ordre limite posé à l'avance : il pourrait être rempli la nuit avant que le SL existe, ce qui violerait la règle 1. C'est la boucle qui surveille et qui exécute.

## Découverte 1015 00h55 : qui « remettait » quelque chose
Tony croyait que Martin rouvrait le DOT automatiquement. Vérification faite : **non**. Aucune grid, AutoGrid désactivé, aucun ordre posé par le bot. Ce qui revenait en boucle, c'est **critical-check.py (cron */5)**. Avec un BASELINE_PV figé à 104,79 $ (juillet), il déclenchait un EMERGENCY KILL à -97 % toutes les ~65 min : 1 625 kills au total dans le log. À chaque fois, il désactivait toutes les paires et tentait de « fermer » les positions.
Bug trouvé dans emergency-kill.sh : `close_side = "sell" if side=="long" or size>0`. La taille est positive aussi pour un short, donc pour fermer un short il aurait **vendu, c'est-à-dire agrandi le short**. Corrigé en `"buy" if side=="short" else "sell"`.
Changements (backups `*.bak-20261015` sur la VM) : BASELINE_PV passe de 104,79 à 2,85, et DD_KILL_PCT de -25 à -60, pour que le kill ne coupe pas un coup audace avant son SL à ~-47 %.

## Backtest du coup n°1 (1015 01h20, scripts/backtest_coup1.py, klines 1h Binance)
J'ai fixé les paramètres **avant** de lancer le backtest, sans aucune optimisation : SL +2,3 %, TP −4,5 %, entrée sur l'EMA50 de DOT, BTC et DOT tous deux en DOWNTREND, RSI > 45.
- **90 jours** : 7 trades, 57 % de gagnants (WLWWWLL). En all-in 20x, le capital fait x1,76.
- **365 jours** : 77 trades, **42,9 % de gagnants**, pour un point mort à 33,8 %. **L'edge par trade est positif** : environ +0,6 % de mouvement de prix par trade, soit ~+10 % du capital à 20x après frais.
- **MAIS en all-in 20x sur 365 jours, c'est la RUINE** : capital x0,000. Une perte coûte −48 %, un gain rapporte +88 %, et la croissance géométrique est négative. On a un edge positif et une mise qui le détruit.
- Le signal reste faible : sur 77 trades, l'écart de +9 points au-dessus du point mort ne vaut qu'environ 1,6 σ.

Monte Carlo pour atteindre x40 (3 $ → 120 $) avant la ruine, avec p = 0,43, sur 400 trades max :
| risque/trade | levier | P(x40) | trades (médiane) |
|---|---|---|---|
| 5 % | 2x | 51 % | 307 |
| 10 % | 4x | **76 %** | 207 |
| 14 % (Kelly) | 6x | 67 % | 159 |
| 20 % | 9x | 44 % | 101 |
| 30 % | 13x | 22 % | 47 |
| 46 % (all-in 20x) | 20x | **9,5 %** | 17 |

**Leçon** : avec un vrai edge, jouer tout sur chaque coup fait *baisser* la probabilité de réussir. Dubins-Savage ne vaut que pour un jeu défavorable. Si l'edge existe, l'audace optimale se situe entre Kelly et le all-in, pas au all-in.

**Décision (la mienne, sous 1000 € j'ai l'autonomie)** : je passe de 46 % à **30 % de risque par trade, soit ~13x**. La probabilité d'atteindre l'objectif passe de 9,5 % à 22 %, en ~47 trades (~7 mois au rythme de ~77 signaux/an). Ça reste audacieux, mais l'audace porte maintenant sur le **temps** et non plus sur un coup de dés. Si l'edge s'avère nul en live (winrate < 34 % sur 15 trades), je l'écrirai et je reviendrai au cash.
Coup n°1 recalculé : capital 2,85 $, perte au SL = 0,86 $, notionnel ≈ 37 $, soit **~32 DOT** à 1,163 (≈13x).

## Exécution du coup n°1 : sur la VM, pas dans la session (1015 01h10)
`~/martin/nb_coup.sh` tourne en cron chaque minute (copie dans scripts/vm/nb_coup.sh).
- C'est un one-shot. Il ne tire que si `~/martin/nb_coup.armed` existe, et supprime ce fichier au moment du tir.
- Il tire quand BTC et DOT sont en DOWNTREND, que le RSI de DOT dépasse 45 et que le prix atteint l'EMA50 de DOT (à 0,1 % près).
- Ordre envoyé : `POST /api/position/short capital=2.7 lev=14 slPct=2.3 tpPct=4.5`, soit ~37,8 $ de notionnel et ~0,87 $ (~30 %) de risque au SL.
- 8 secondes après, il vérifie qu'un ordre stop existe et envoie un Telegram **silencieux** : confirmation, ou 🚨 si le SL manque.
Pourquoi la VM : la boucle de session meurt si le terminal se ferme ou si Tony part dormir, alors que le cron de la VM survit.
Testé à blanc (fire=0 à 23h09 UTC, prix 1,1462 contre une EMA50 à 1,1630).

## Contre-épreuve : le même setup sur 9 altcoins (1015 ~01h45), un coup dur pour mon « edge »
365 jours, 1h, paramètres identiques :

| Paire | Trades | Winrate |
|---|---|---|
| DOT | 77 | 42,9 % |
| XRP | 74 | 39,2 % |
| DOGE | 84 | 38,1 % |
| LINK | 81 | 35,8 % |
| AVAX | 84 | 34,5 % |
| ADA | 85 | 34,1 % |
| ETH | 65 | 33,8 % |
| LTC | 70 | 32,9 % |
| SOL | 76 | 28,9 % |

**Agrégé : 248/696 = 35,6 %, contre un point mort frais compris de ~35,3 %. Il n'y a pas d'edge.** Le 42,9 % de DOT est très probablement le meilleur tirage parmi 9. C'est un biais de sélection : j'avais pris DOT uniquement parce qu'on y était déjà.
Monte Carlo avec p = 35,6 % : P(x40) ≈ 2 %, **quel que soit le sizing** (10 % de risque : 2,4 %, 30 % : 1,9 %, all-in : 1,9 %). Le jeu est juste, et la mise ne change presque rien.
**Décision** : je **garde 30 % de risque/trade**, parce que ce choix domine les autres. S'il y a un edge propre à DOT, il donne ~22 % contre 9,5 % en all-in. S'il n'y en a pas, il donne ~2 %, comme le all-in. Je ne regretterai ce choix dans aucun des deux cas.
Leçon pour moi : un backtest sur un seul actif, choisi après coup, ne prouve rien. Il faut toujours une contre-épreuve sur un panier.

## 1015 ~04h25 Paris : une position que je n'ai PAS ouverte
Vers 02h20 UTC, une position **SHORT 22 DOT @1,0985** est apparue (~24 $ de notionnel, ~8,5x), au moment où DOT chutait de 1,128 à ~1,098.
Elle a un SL buy-stop reduceOnly à 1,1338 (+3,2 %) et deux TP à 1,0804 et 1,0668. C'est la même structure que le short DOT « hérité » d'hier.
**Origine** : ni nb_coup.sh (aucune ligne FIRE), ni Martin (aucun POST dans app.log). auto_scalp.py ne trade que l'ETH, entre 8h et 22h UTC, et plante depuis des semaines (« Could not parse price »). C'est donc un ordre passé directement sur Kraken, très probablement par Tony depuis l'appli, ou par un outil qui a une clé API ailleurs. Je ne peux pas le prouver.
**Ce que je fais** : je ne touche à rien. Le SL est posé, et nb_coup.sh ne tirera pas tant qu'une position existe. Je préviens Tony.
**Leçon** : ce compte a **deux mains**, et le mandat « c'est à toi » ne suffit pas à l'empêcher. Il faudra se mettre d'accord avec Tony sur qui trade quoi, ou utiliser un sous-compte.

## Banc d'essai complet (1015 ~19h55, scripts/research/harness.py)
12 cryptos, 2 ans de données 1h, frais et slippage de 0,07 % par côté. Split : 16 mois en in-sample (IS), 8 mois en out-of-sample (OOS). Résultats en R.

| stratégie | OOS trades | E[R] OOS | t OOS | coins OOS+ |
|---|---|---|---|---|
| pullback (coup n°1, 2 sens) | 909 | −0,11 | −2,4 | 4/12 |
| donchian 48h + régime BTC | 874 | −0,11 | −2,2 | 3/12 (IS +0,06) |
| meanrev RSI extrême | 4 | n/a | n/a | n/a |
| squeeze vol + cassure | 170 | −0,37 | −3,0 | 4/12 |
| **random (contrôle)** | 268 | −0,34 | −4,4 | 0/12 (**IS +0,33, t +5,3 !**) |

**Verdict** : aucune stratégie ne survit en OOS, et toutes sont négatives une fois les frais payés. Le pire, c'est que **le contrôle aléatoire fait t = +5,3 en IS**. Le régime de marché d'une période suffit à fabriquer une « significativité » qui ne veut rien dire. Tout backtest positif sur une seule période est donc suspect par défaut. J'arrête la recherche d'edge mécanique : c'est la 4ᵉ méthodologie qui dit la même chose (juin, juillet, ce matin, ce soir).
→ Le capital reste un **pari audacieux assumé** (coup n°1 armé, ~2 % de chances d'atteindre x40). Ce n'est pas une source de revenu. Le revenu, je le cherche ailleurs.

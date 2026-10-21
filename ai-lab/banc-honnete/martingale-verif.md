# Vérification de la martingale de Martin (22/10, 00h06)
Demande de Tony : « regarde mes stratégies de martingale, ça a fonctionné pendant 3 mois, vérifie ».
Règle vérifiée = `MartingaleEngine` de Martin : TP et SL fixes ; perte → mise ×2 et sens inversé ; gain → mise de départ ; au-delà de 4 doublements, la série est abandonnée. (La version Bitget de 2024 simule ses pertes avec `Math.random()` : jamais branchée sur un vrai marché.)
Test : BTC 15 min, janvier 2024 → octobre 2026, frais taker 0,05 % par côté, bougie ambiguë = SL. Unité : la taille de la position de départ (x).

| TP / SL | Trades | Séries perdues (5 pertes de suite) | Résultat 2,8 ans | Fenêtres de 3 mois positives |
|---|---|---|---|---|
| 1,5 % / 1,0 % (exemple du code) | 3 853 | 122 | **−9,6 x** | 38/133 (**29 %**) |
| 1,0 % / 1,0 % | 5 599 | 82 | −11,5 x | 30/133 (23 %) |
| 0,8 % / 0,2 % (la config « +561 % » de mars) | 24 071 | 2 334 | −110 x | 0/133 (0 %) |
| 1,5 % / 1,0 % **sans aucun frais** | 3 853 | 122 | +2,4 x | 82/133 (62 %) |

Lecture :
- « Ça a marché 3 mois » est vrai et attendu : avec les réglages du code, **une période de 3 mois sur trois environ (29 %) finit positive**. Puis une série de 5 pertes arrive et efface tout.
- Sans frais, la martingale ne gagne presque rien (+2,4 x en 2,8 ans) : doubler la mise ne crée aucun avantage, ça change seulement la forme des pertes (beaucoup de petits gains, de rares grosses pertes).
- Avec les frais, elle perd : doubler la mise double aussi les frais payés au pire moment.

## Tous les réglages (22/10, 00:14) — Tony : « les pertes, c'était le manuel et des bugs de SL »
Juste : l'historique réel du compte mélange trades manuels (RIVER −48 $ le 08/08) et bugs de stop (avril-mai). D'où ce test qui isole la stratégie : stop parfait, aucun manuel, aucun bug. 144 réglages (TP 0,5-2 %, SL 0,5-2 %, 3 à 5 doublements) × BTC, ETH, SOL.
- Gagnants sur 2024-25 : **7/144**. Gagnants sur 2026 : 8/144.
- Les 7 gagnants de 2024-25, jugés sur 2026 : **aucun ne gagne** (le meilleur : +7,1 x → **−4,4 x** ; les autres entre −0,0 et −2,3 x).
- Le classement est stable (Spearman +0,84), mais seulement pour une raison : les petits TP/SL font plus de trades, donc plus de frais, donc perdent toujours plus. Être « moins perdant » se prolonge ; être gagnant, non.
Conclusion : même sans bug ni trade manuel, la martingale ne gagne pas dans la durée. Ses 3 mois gagnants sont réels, mais ils ne disent rien des 3 mois suivants.

## Version « stop serré » décrite par Tony (22/10, 00:18)
« Je double les 1 € misés, je SL assez tôt, puis je change de sens avec SL rapide. » Bougies 5 min (déc. 2025 → oct. 2026), 360 réglages (SL 0,1-0,5 %, TP 0,2-2 %, 3 à 8 doublements) × BTC, ETH, SOL ; choix sur déc-juin, jugement sur juil-oct.
- Positifs sur déc-juin : **1/360** (BTC SL 0,5 % TP 2 % x5 : +0,88 x) ; sur juil-oct il fait +0,03 x.
- Les 9 suivants perdent sur les deux périodes.
- Cause : un stop à 0,1-0,5 % est du même ordre que les frais (0,1 % l'aller-retour). Chaque perte coûte le stop + les frais, et doubler la mise double les frais.
(Unité : x = la taille de la position de départ. Avec 1 € de marge et un levier x10, 1 x = 10 €.)

## Martingale + stop suiveur dès +1 %, toujours en position (22/10, 00:20)
Description de Tony : « trailing SL dès 1 % gagnant, plein de règles pour réduire les pertes, en position 100 % du temps ». 108 réglages × BTC ETH SOL.
- Premier calcul (t15) : les 8 meilleurs de 2024-25 étaient TOUS positifs en 2026 (ETH +3,2 x…). Trop beau → vérifié (t15v).
- **C'était un défaut du simulateur** : avec un suiveur à 0,3 %, la bougie suivante ouvre souvent déjà au-delà du stop ; sortir pile au stop est impossible en vrai. En sortant à l'ouverture dans ce cas : ETH −2,5 x (15 min) / −7,6 x (5 min) sur déc-oct ; mise fixe −2,9 x ; sens au hasard mise fixe −3,0 x (médiane). La martingale fait même pire que la mise fixe.
- Leçon : un stop suiveur très serré testé sur des bougies trop grosses fabrique des gains qui n'existent pas. C'est exactement le genre d'erreur qui donne des backtests à +561 %.

## + l'EMA pour choisir long ou short (22/10, 00:22)
Précision de Tony : « il y avait aussi l'EMA en même temps pour savoir si on était long ou short ». Sens = signe(clôture − EMA 20/50/200, bougies 15 min) ; perte → mise ×2 ; suiveur dès +1 % ; sorties corrigées des gaps. 243 réglages × BTC ETH SOL.
- **Positifs en 2024-25 : 0/243. Positifs en 2026 : 0/243.**
- Les « meilleurs » (les moins perdants) font entre −0,3 x et −6 x en 2026, comme le sens tiré au hasard (médianes −1,4 à −4,8 x).
- L'EMA ne choisit pas mieux le sens que le hasard sur ces horizons, et les frais × le doublement font le reste.

## + coupe-circuit journalier (22/10, 00:23)
« Et aussi un système de stop quand trop de perte. » Arrêt pour la journée dès que la perte du jour dépasse 0,05 / 0,1 / 0,2 x. 486 réglages.
- Positifs 2024-25 : **1/486** (ETH EMA20 SL 1 % suiveur 1 % x5 plafond 0,2 : +0,67 x) → **−5,1 x en 2026**. Positifs 2026 : 0/486.
- Un coupe-circuit coupe les mauvaises journées, mais il ne crée pas d'avantage : une stratégie qui perd en moyenne perd moins vite, pas moins.

## Ce que dit l'historique de Martin (enquête du 22/10, 00:23, commits + VM + journal)
- Compte Kraken ouvert le 04/02/2026 ; martingale dans le code du 28/02 au 17/03 (F15 « no martingale ») → **au plus ~18 jours en réel**, pas 3 mois.
- Les « 3 mois » : un **backtest** du 16/12/2025 au 16/03/2026 (commit F12 f26d25d : « Backtested on 3 months: avg +$34.58/period »).
- Réglages réels d'origine : mise 1 $, ×2 et retournement après SL, TP 1,5 %, SL 1 %, 4 doublements, x10, BTC ; sens choisi par un score RSI + EMA9/EMA21 + MACD calculé sur les ticks.
- Réel sur la période : capital ~40 $ (03/03) → 28,59 $ (19/03) → 8,82 $ (21/03) ; aucune série martingale enregistrée en base.
- Bugs de stop réels ensuite (avril-juin, grids) : SL non replacé, SL « effacés » par Kraken (tick), SL du mauvais côté, position nue après KILL.

## Tony : « la fonte de mars, c'était des bugs de SL » (22/10, 00:25) — plausible, et le journal le soutient
- F11 (15/03) : SL **interne seulement**, pas posé sur Kraken → si le bot ne tourne pas, la position n'a aucune protection.
- Journal du 19/03 : le service Martin était **en boucle de crash depuis des jours (53 836 redémarrages)**, bot à vide depuis le 18/03.
- Journal de mars : `maxLossPercent` par défaut à 50 % (« Tony a perdu de l'argent avec l'ancien réglage ») → baissé à 25 %.
Donc la perte réelle de mars mesure surtout l'infrastructure (crashs + stop non posé), pas la stratégie. Conséquence honnête dans les deux sens : le réel de mars ne prouve PAS que la martingale perd… mais il ne prouve pas non plus qu'elle gagne. Le seul juge propre reste le test sans bug ci-dessus, et lui ne trouve aucun réglage gagnant durable.

## Avec l'appli de Tony : Darwin, mode « martingale + retournement » (22/10, 00:27)
Même procédure que son serveur (`run_evolution`) : 20 agents, 25 générations d'évolution sur le 1er quart, puis test du meilleur sur les 3 quarts suivants (jamais vus). BTC/ETH/SOL 1 h, juillet 2025 → octobre 2026 (4 quarts d'~3,7 mois), frais 0,05 %, 3 graines chacun. Script : darwin-sans-interface.py.
| | Entraînement (Q1) | Test Q2 | Test Q3 | Test Q4 |
|---|---|---|---|---|
| 9 runs | **+6 à +45 % (9/9 positifs)** | **−10 à −40 % (0/9)** | 2/9 positifs | 6/9 positifs |
Somme des 3 quarts de test : positive pour 1 run sur 9 (BTC graine 2 : +4,8 %) ; les 8 autres entre −6 et −45 %.
Lecture : Darwin trouve TOUJOURS une martingale gagnante sur la période où il évolue, puis elle perd dès le trimestre suivant. C'est la même histoire que les « 3 mois » : l'évolution apprend le passé par cœur. (Note : le plan de hardening de Darwin du 20/04 signale aussi un indicateur qui regarde sa propre bougie, bb_squeeze, ce qui gonfle l'entraînement.)

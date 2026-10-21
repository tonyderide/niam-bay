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

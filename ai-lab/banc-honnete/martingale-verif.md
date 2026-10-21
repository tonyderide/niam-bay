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

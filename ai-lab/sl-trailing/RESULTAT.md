# Résultat PREREG-28 : SL fixe puis trailing dès qu'on gagne (29/10/2026, 15h3x)
Pré-enregistrement : ../banc-honnete/PREREG-28-sl-fixe-puis-trailing.md (commit d4f8149 à 15h26, avant calcul ; addendum A 8db1fd8 à 15h33, avant calcul). Code : etude.py, regle_tony.py ; contrôles à la main : cas.py.

## A. Règle exacte de Tony, BTC, bougies 1 min, 01/2024 → 09/2026
SL 1 %, trailing 0,5 % activé à +1 %, toujours en position, sens inversé à chaque sortie. Mise = 10 € de risque (position de 1 000 €), frais réels.
| | Inversé à chaque sortie | Inversé après une perte |
|---|---|---|
| Trades | 2 123 | 2 107 |
| Trades gagnants | 50,2 % | 50,6 % |
| Gain moyen / perte moyenne (en mises) | +0,87 / −1,10 | +0,88 / −1,10 |
| Espérance par trade | **−0,11 mise** (−1,07 €) | −0,10 mise |
| Pire série de pertes d'affilée | 8 | 10 |
| Total sur 33 mois, mise fixe 10 € | **−2 278 €** | −2 020 € |
| Martingale 1 000 € / 10 €, départs de 3 mois : en gain / ruinés | **15,6 % / 84,9 %** | 25,9 % / 75,9 % |
| Martingale, départs de 1 mois : en gain / ruinés | 22,5 % / 66,8 % | 32,0 % / 67,3 % |
| Martingale, départs de 9 mois : en gain | 0 % (ruine 100 %) | 0 % (ruine 100 %) |
Fait brut : à partir d'un instant au hasard, le BTC touche +1 % avant −1 % dans **47,4 %** des cas (5 000 tirages) : c'est pile ou face.
**Verdict de l'addendum : « on ne peut pas perdre dans 90 % des cas » est FAUX** (15,6 % des départs de 3 mois finissent en gain).
Pourquoi : un gain rapporte au moins 0,5 % − 0,1 % de frais = 0,4 % (0,87 % en moyenne), une perte coûte 1 % + 0,1 % = 1,1 % ; à 50/50 ça fait −0,11 par trade. Doubler la mise ne rattrape même pas les pertes, car un gain (~0,9) est plus petit qu'une perte (1,1). Six pertes d'affilée (10+20+…+320 = 630 €) et la mise suivante (640 €) dépasse ce qui reste : en 3 mois (~200 trades), cela arrive presque toujours.
Journal vérifiable : regle-tony.json, « journal_btc_200_premiers » (ex. 01/01/2024 00h00 UTC long à 42 314, sortie 02h03 à +0,62 %).

## B. Grille complète (253 pièces, 1 h, long et short séparés)
Aucun des 50 réglages n'est positif, ni en 2024-2025, ni en 2026, dans aucun sens. Réglage figé : SL 8 %, trailing 5 %, activation 1 % (le moins mauvais, car c'est celui qui fait le moins de trades).
- **Long 2026 :** −32,5 % en moyenne, 39 pièces gagnantes sur 188, 36,8 % de trades gagnants. Gains bruts −26,6 contre 34,5 de frais. Contre le hasard : −36,9 % ± 1,4, p = 0,00. Il y a donc un peu de tendance réelle, mais elle est bien trop faible pour payer les frais.
- **Short 2026 :** −32,4 %, p = 0,165.
- **VERDICT : PERD** dans les deux sens.

# Résultat PREREG-28 : SL fixe puis trailing dès qu'on gagne (29/10/2026, 15h3x)
Pré-enregistrement : ../banc-honnete/PREREG-28-sl-fixe-puis-trailing.md (commit d4f8149 à 15h26, avant calcul ; addendum A 8db1fd8 à 15h33, avant calcul). Code : etude.py, regle_tony.py ; contrôles à la main : cas.py.

## A. Règle exacte de Tony, BTC, bougies 1 min, 01/2024 → 09/2026
**Correction (29/10, 15h5x) :** la 1re version de ce tableau ne couvrait que 01/2024 → 28/10/2024, et non les 33 mois annoncés. La coupure « 48 bougies figées = retrait de la cote » avait été appliquée à des minutes, et 48 minutes figées (une maintenance) avaient coupé le BTC. Elle vaut maintenant 48 heures quelle que soit la taille des bougies (la plus longue série figée du BTC en 1 min fait 74 minutes). Les chiffres ci-dessous couvrent toute la période. Le verdict est inchangé.
Règle : SL 1 %, trailing 0,5 % activé à +1 %, toujours en position. Mise = 10 € de risque (position de 1 000 €), frais réels.
| | Inversé à chaque sortie | Inversé après une perte |
|---|---|---|
| Trades | 5 592 | 5 634 |
| Trades gagnants | 49,5 % | 50,8 % |
| Gain moyen / perte moyenne (en mises) | +0,88 / −1,10 | +0,87 / −1,10 |
| Espérance par trade | **−0,12 mise** (−1,19 €) | −0,10 mise |
| Pire série de pertes d'affilée | 9 | 10 |
| Total sur 33 mois, mise fixe 10 € | **−6 642 €** | −5 558 € |
| Martingale 1 000 € / 10 €, départs de 3 mois : en gain / ruinés | **7,5 % / 92,6 %** | 15,1 % / 85,6 % |
| Martingale, départs de 1 mois : en gain / ruinés | 25,8 % / 68,7 % | 35,6 % / 56,5 % |
| Martingale, départs de 9 mois : en gain / ruinés | 4,8 % / 95,9 % | 9,8 % / 92,8 % |
Fait brut : à partir d'un instant au hasard, le BTC touche +1 % avant −1 % dans **50,5 %** des cas (5 000 tirages) : c'est pile ou face.
**Verdict de l'addendum : « on ne peut pas perdre dans 90 % des cas » est FAUX.**
Pourquoi :
- Un gain rapporte au moins 0,5 % − 0,1 % de frais = 0,4 %, et 0,88 % en moyenne. Une perte coûte 1 % + 0,1 % = 1,1 %. À 50/50, cela fait −0,12 par trade.
- Doubler la mise ne rattrape même pas les pertes, car un gain (~0,9) est plus petit qu'une perte (1,1).
- Six pertes d'affilée font perdre 10+20+…+320 = 630 €, et la mise suivante (640 €) dépasse ce qui reste.
Journal vérifiable : regle-tony.json, « journal_btc_200_premiers ».

## A2. Addendum B : inversion après une perte, 156 réglages (BTC 1 min)
- **Réglage figé sur 2024-2025 :** SL 3 %, activation à +5 %, trailing 1 %. Sur 2024-2025, il fait +0,073 mise par trade sur 308 trades, soit +224 € avec une mise de 10 €.
- **Jugement 2026 :** +0,016 mise par trade sur 94 trades, soit **+14,7 €**, avec 39 % de trades gagnants. Gains bruts 13,8 % contre 9,4 % de frais.
- **Contre le hasard :** −0,035 ± 0,136 ; **p = 0,32**. Le résultat est indiscernable du hasard → **VERDICT B : NON DÉMONTRÉ.**
- **Réglages positifs :** 28 sur 156 en 2024-2025, et 39 sur 156 en 2026. Avant frais, 74 sur 156 sont positifs en 2026, soit à peu près la moitié, ce qu'on attend d'une règle sans avantage.
- **Martingale avec ce réglage** (une mise de 10 € = position de 333 €) :

| Départs de | En gain | Ruinés | Résultat médian |
|---|---|---|---|
| 1 mois | 77 % | 6 % | +110 € |
| 3 mois | 72 % | 26 % | +326 € |
| 9 mois | 28 % | **78 %** | −461 € |

  « 90 % » est **FAUX** ici aussi.
- **Les meilleurs réglages de 2026,** choisis après coup (par exemple SL 5 %, activation 5 %, trailing 1 % : +0,24 mise par trade), ne comptent pas. Le même réglage faisait +0,04 sur 2024-2025, et les quatre suivants y étaient négatifs.

## B. Grille complète (253 pièces, 1 h, long et short séparés)
Aucun des 50 réglages n'est positif, ni en 2024-2025, ni en 2026, dans aucun sens. Réglage figé : SL 8 %, trailing 5 %, activation 1 % (le moins mauvais, car c'est celui qui fait le moins de trades).
- **Long 2026 :** −32,5 % en moyenne, 39 pièces gagnantes sur 188, 36,8 % de trades gagnants. Gains bruts −26,6 contre 34,5 de frais. Contre le hasard : −36,9 % ± 1,4, p = 0,00. Il y a donc un peu de tendance réelle, mais elle est bien trop faible pour payer les frais.
- **Short 2026 :** −32,4 %, p = 0,165.
- **VERDICT : PERD** dans les deux sens.

## C. Le réglage qui a le moins de chances de perdre (addendum C, BTC 1 min)
6 084 combinaisons explorées :
- SL, activation, trailing ;
- ×1 / ×1,5 / ×2 / ×3 après une perte ;
- plafond de 2 / 4 / 6 / ∞ pertes ;
- mise de base de 2 / 5 / 10 €.

Choisie sur 2024-2025 : **SL 5 %, activation +1 %, trailing 1 %, ×3 après une perte, retour à la base après 4 pertes, mise de 10 €.**
- **2024-2025 :** perte à 3 mois dans 0,6 % des départs, résultat médian +80 €.
- **2026 (jugement) :** perte dans **0 %** des 184 départs de 3 mois, résultat médian +70 €, le 5 % le pire à +50 €. Verdict C pré-enregistré : VRAI.

Mais :
- **Les départs de 2026 se chevauchent :** ils valent environ 3 trimestres indépendants.
- **Sur le BTC mélangé** (même volatilité, sans tendance), le même réglage perd dans 40 % des départs, entre 13 et 61 % selon le mélange.
- **Le mécanisme :** 80 % des trades gagnent un peu (médiane +0,5 % du prix), 1 trade sur 7 perd 5 %. L'espérance par trade est de +0,10 %, ce qui est statistiquement faible (t ≈ 1,6 avant même de tenir compte des 6 084 essais).

## D. Hors échantillon : ETH et SOL, sans rien changer (addendum D) → NE TIENT PAS
| | BTC (où il a été choisi) | ETH | SOL |
|---|---|---|---|
| Perte à 3 mois | 1,7 % | **44,9 %** | **61,5 %** |
| Résultat médian à 3 mois | +76 € | +17 € | −94 € |
| Pire résultat à 3 mois | −30 € | −585 € | −972 € |
| Espérance par trade | +0,10 % | −0,08 % | −0,10 % |
| Parcours continu de 33 mois, départ à 1 000 € | 2 125 € | **417 €** (pire baisse −92 %) | **33 €** (−97 %) |

La réussite sur le BTC vient du choix du meilleur réglage parmi 6 084 sur une seule pièce, pas d'un avantage réel. Le chiffre honnête à retenir pour « la chance de perdre en 3 mois » avec ce type de règle est celui des pièces qui n'ont pas servi au choix : **45 à 62 %**.

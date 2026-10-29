# Résultat PREREG-29 : une martingale gagnante TOUS les mois ? (29/10/2026, 21h1x)
Pré-enregistrement : ../banc-honnete/PREREG-29-martingale-mois-par-mois.md (commit be42d40 à 21h12, avant tout calcul). Les résultats 2026 ont été calculés dans le même passage que la grille, mais le choix est mécanique (règle du pré-enregistrement, sur 2024-2025 seulement). Code : moteur.py (règles), cas.py (contrôles à la main, tous justes), etude.py (6 132 réglages), juge.py (jugement unique), tableaux.py. Chiffres bruts : choix.json, jugement.json, grille.npz.

## Réponse courte
**Non.** Sur 7 familles de martingales et 6 132 réglages, aucun n'est positif tous les mois, même sur la période où il a été choisi.
- Meilleur réglage de tous, sur la période de choix (2024-2025, BTC/ETH/SOL, 72 mois-pièces) : **96 % de mois positifs** (69 sur 72), pas 100 %. Aucun réglage sur 6 132 n'atteint 72/72.
- Le même réglage, figé, hors échantillon : **85 % de mois positifs en 2026** (23 sur 27) et **89 % sur 250 autres pièces** (6 650 mois-pièces). Le critère pré-écrit (27/27 et ≥ 95 %) n'est pas atteint : **« gagnante à tous les coups » = FAUX** pour les 7 familles.
- Surtout : **les mêmes règles sur des prix mélangés au hasard donnent la même part de mois positifs** (85 % pour ce réglage). Le « presque toujours positif » vient de la forme de la martingale, pas d'un avantage sur le marché.
- Le prix à payer : le réglage qui gagne le plus souvent gagne **+7,7 € par mois (médiane)** sur 1 000 €, et perd jusqu'à **−987 €** les mauvais mois. En moyenne sur les autres pièces : **−4,9 € par mois** (−32 520 € cumulés sur 6 650 mois-pièces).

## Pourquoi
Une martingale ne change pas l'espérance d'un jeu sans avantage, elle change la forme des résultats : beaucoup de petits gains, de rares très grosses pertes. Le réglage gagnant le plus souvent ici le montre à l'extrême :
- TP à 4 %, SL à 8 % : le TP est touché 2 fois sur 3 (66 % des 1 363 trades sur BTC/ETH/SOL) ;
- mise de base de 1 € seulement et « récupération exacte » (après une perte, la mise suivante est calculée pour tout rembourser) : un mois sans longue série de pertes finit à quelques euros de gain ;
- un mois avec une série (un krach comme SOL en octobre 2025 : **−346 €**) efface plus de 5 ans de petits gains (≈ +5 € par mois).
Plus la part de mois positifs est haute, plus le pire mois est grave : c'est la même chose vue des deux côtés.

## Tableau par famille (réglage figé sur 2024-2025, BTC/ETH/SOL en 1 min ; autres pièces en 1 h, bougie ambiguë = SL)
Mois positifs = part des mois-pièces au résultat > 0 €, capital remis à 1 000 € chaque mois. p = part des 30 mélanges (même volatilité, sans tendance) qui font une moyenne au moins aussi bonne.

| Famille | Réglage figé | Mois positifs 2024-25 (choix) | 2026 | Autres pièces | Hasard 2026 | Moyenne/mois 2026 | Moyenne/mois autres pièces | Pire mois autres pièces | Mois ruinés autres pièces | Avantage |
|---|---|---|---|---|---|---|---|---|---|---|
| doublement classique | SL 8.0% TP 4.00%, long, base 1 €, récupération exacte, plafond 8 pertes | 96 % | 85 % | 89 % | 85 % | +2,6 € (p = 0,367) | -4,9 € | -987 € | 10 / 6650 | NON DÉMONTRÉ |
| d'Alembert | SL 5.0% TP 5.00%, long, base 20 €, u max 10 | 75 % | 59 % | 49 % | 62 % | -9,0 € (p = 0,667) | -94,8 € | -976 € | 437 / 6650 | PERD |
| Fibonacci | SL 3.0% TP 3.00%, long, base 2 €, j max 10 | 88 % | 78 % | 68 % | 72 % | -10,7 € (p = 0,833) | -29,2 € | -965 € | 8 / 6650 | PERD |
| Labouchère | SL 3.0% TP 3.00%, long, base 1 €, liste 1-2-3, longueur max 20 | 86 % | 74 % | 60 % | 68 % | +5,8 € (p = 0,2) | -53,4 € | -965 € | 132 / 6650 | NON DÉMONTRÉ |
| anti-martingale (Paroli) | SL 8.0% TP 8.00%, long, base 20 €, retour à la base après 2 gains | 60 % | 44 % | 39 % | 46 % | +3,4 € (p = 0,1) | -10,3 € | -370 € | 0 / 6650 | NON DÉMONTRÉ |
| grille DCA | 1er OS à −3%, TP +2.5%, trailing 0.5%, 5 OS, SL 8% sous le dernier OS | 85 % | 70 % | 72 % | 70 % | +2,1 € (p = 0,5) | +3,8 € | -600 € | 0 / 6650 | NON DÉMONTRÉ |
| règle de Tony | SL 3.0%, trailing 1.0% dès +2.0%, inversion après perte, ×3.0 après perte, plafond 6, base 2 € | 83 % | 74 % | 61 % | 75 % | +2,3 € (p = 0,2) | -41,0 € | -965 € | 35 / 6650 | NON DÉMONTRÉ |

**Verdicts pré-écrits :** « gagnante à tous les coups » **FAUX** pour les 7 familles. Avantage réel : **PERD** pour d'Alembert et Fibonacci ; **NON DÉMONTRÉ** pour les 5 autres (moyenne 2026 > 0 sur les 3 pièces mais p ≥ 0,1 contre le hasard, et moyenne < 0 sur les autres pièces, sauf la grille DCA).

## Contrôles
- **Résolution des bougies :** le réglage figé rejoué en 1 h sur BTC/ETH/SOL 2026 donne une part de mois positifs proche du 1 min (doublement 81 % contre 85 % ; DCA 70 % contre 70 % ; Fibonacci 70 % contre 78 %). Sur les autres pièces, compter la bougie ambiguë en TP (version optimiste) ne change presque rien (doublement 89,5 % contre 89,3 % ; Fibonacci 72 % contre 68 % ; Labouchère 63 % contre 60 %). L'ordre pessimiste ne cache pas une martingale gagnante.
- **Sans remise mensuelle (parcours continu, 1 000 € au 01/2024 → 09/2026) :** sur les autres pièces, le doublement figé finit au-dessus de 1 000 € pour 51 % des pièces, avec **47 ruines sur 240** (contre 10 mois ruinés quand le capital est remis chaque mois : la remise mensuelle cache les ruines). d'Alembert : 218 ruines sur 240 ; Labouchère : 207 ; Fibonacci et la règle de Tony : 156.
- **La grille DCA, seule moyenne positive sur les autres pièces (+3,8 € par mois) :** contrôle ajouté après coup (complement_dca.py, non pré-enregistré). Sur les mêmes mois-pièces mélangés, elle fait **mieux** (+6,0 € par mois, 72 % de mois positifs) : p = 1,0. Ce n'est donc pas un avantage tiré du marché. Mise en garde : mélanger les bougies d'un mois sans changer son total fabrique un peu de « retour à la moyenne », ce qui favorise une grille qui achète les baisses ; le témoin est donc généreux pour elle. La fermeture forcée en fin de mois fait aussi un « stop temps » : sans elle, le même réglage perd −0,57 % sur 2026 (PREREG-24 refait, chiffre retrouvé exactement par verif_dca.py) ; avec, +2,5 %. Pire mois : −600 €.
- **Après coup (non pré-enregistré, ne compte pas) :** en regardant 2026, 9 réglages font 27/27 mois positifs sur BTC/ETH/SOL (tous « doublement, SL 8 %, TP 4 %, sens inversé après une perte, récupération exacte »). Ils ne faisaient que 88-89 % en 2024-2025, et sur les autres pièces 88-91 % de mois positifs, avec des mois à −987 € (verif_apres_coup.py). Même piège que PREREG-28 : choisir le meilleur sur la période qu'on juge.

## Tableaux mois par mois (les 3 réglages figés aux meilleures parts 2024-2025)
Résultat du mois en € pour 1 000 € remis au départ du mois. « Autres pièces » = les 250 pièces jamais utilisées pour le choix (1 h, version pessimiste).

### doublement classique : doublement : SL 8.0% TP 4.00%, long, base 1 €, récupération exacte, plafond 8 pertes
| Mois | BTC | ETH | SOL | Autres pièces : part de mois positifs | Autres pièces : moyenne |
|---|---|---|---|---|---|
| 2024-01 | +5.1 | +4.3 | +13.6 | 95% | +7.1 |
| 2024-02 | +4.5 | +6.4 | +8.6 | 100% | +10.1 |
| 2024-03 | +6.4 | +6.5 | +22.3 | 98% | +15.6 |
| 2024-04 | +3.4 | +4.9 | +13.3 | 89% | -3.9 |
| 2024-05 | +1.4 | +4.3 | +9.4 | 94% | +7.5 |
| 2024-06 | +1.7 | +2.1 | +5.3 | 94% | -9.9 |
| 2024-07 | +2.0 | +3.2 | +7.1 | 95% | +3.2 |
| 2024-08 | +5.6 | +8.6 | +6.4 | 77% | -17.9 |
| 2024-09 | +2.5 | +3.4 | +4.7 | 98% | +6.5 |
| 2024-10 | +1.3 | +2.8 | +6.1 | 98% | +3.0 |
| 2024-11 | +3.9 | +6.3 | +11.7 | 99% | +20.4 |
| 2024-12 | +4.6 | +5.8 | +10.2 | 79% | -71.9 |
| 2025-01 | +4.3 | +6.9 | +17.6 | 99% | +10.4 |
| 2025-02 | +4.9 | +8.5 | +10.8 | 65% | -143.3 |
| 2025-03 | +3.8 | +3.7 | +6.3 | 74% | -15.7 |
| 2025-04 | +3.0 | +8.4 | +11.4 | 100% | +12.3 |
| 2025-05 | +1.3 | +6.0 | +2.1 | 85% | +5.8 |
| 2025-06 | +1.9 | +4.9 | +5.6 | 97% | +5.5 |
| 2025-07 | +1.0 | +5.0 | +1.4 | 80% | +5.9 |
| 2025-08 | -1.9 | +6.8 | +9.0 | 95% | +6.7 |
| 2025-09 | +0.7 | -2.2 | +4.1 | 68% | -6.5 |
| 2025-10 | +3.8 | +7.1 | -346.2 | 95% | +5.1 |
| 2025-11 | +3.2 | +4.6 | +6.8 | 95% | +9.7 |
| 2025-12 | +1.2 | +5.6 | +6.7 | 94% | +5.8 |
| 2026-01 (2026) | -10.5 | +4.0 | +4.4 | 76% | -42.7 |
| 2026-02 (2026) | +4.7 | +9.0 | +12.4 | 96% | +7.5 |
| 2026-03 (2026) | +4.9 | +4.9 | +3.0 | 82% | -1.4 |
| 2026-04 (2026) | +1.4 | +2.4 | +2.3 | 88% | +5.9 |
| 2026-05 (2026) | -1.4 | -3.3 | +2.4 | 88% | -4.6 |
| 2026-06 (2026) | -0.9 | +0.9 | +5.1 | 80% | -11.2 |
| 2026-07 (2026) | +0.9 | +2.1 | +1.2 | 80% | -2.4 |
| 2026-08 (2026) | +2.3 | +3.2 | +6.3 | 90% | +5.5 |
| 2026-09 (2026) | +2.4 | +2.5 | +3.2 | 96% | +8.4 |

### Fibonacci : Fibonacci : SL 3.0% TP 3.00%, long, base 2 €, j max 10
| Mois | BTC | ETH | SOL | Autres pièces : part de mois positifs | Autres pièces : moyenne |
|---|---|---|---|---|---|
| 2024-01 | +13.0 | +9.8 | +30.9 | 61% | -21.8 |
| 2024-02 | +26.7 | +27.7 | +28.2 | 98% | +27.4 |
| 2024-03 | +21.7 | +21.3 | +63.1 | 80% | -29.5 |
| 2024-04 | +0.2 | +3.3 | +15.7 | 35% | -22.8 |
| 2024-05 | +10.8 | +21.8 | +33.0 | 90% | +17.6 |
| 2024-06 | -0.2 | +0.6 | +9.4 | 36% | -123.6 |
| 2024-07 | +5.6 | +1.5 | +24.3 | 32% | -124.8 |
| 2024-08 | +8.7 | -8.0 | +19.6 | 22% | -202.9 |
| 2024-09 | +7.4 | +9.5 | +15.9 | 93% | +14.3 |
| 2024-10 | +8.4 | +4.8 | +16.5 | 67% | +2.2 |
| 2024-11 | +22.5 | +31.8 | +37.6 | 99% | +49.8 |
| 2024-12 | +9.1 | +11.1 | +10.7 | 36% | -215.7 |
| 2025-01 | +11.6 | +13.5 | +47.2 | 93% | +7.8 |
| 2025-02 | -12.0 | -19.2 | +6.4 | 52% | -137.9 |
| 2025-03 | +9.4 | -1.2 | +9.0 | 46% | -20.1 |
| 2025-04 | +14.3 | +16.9 | +23.0 | 98% | +26.6 |
| 2025-05 | +5.8 | +32.6 | +15.2 | 86% | -2.4 |
| 2025-06 | +4.6 | +7.8 | +9.9 | 77% | -3.4 |
| 2025-07 | +5.0 | +26.5 | +14.5 | 67% | -4.1 |
| 2025-08 | -9.3 | +21.0 | +21.0 | 90% | +5.5 |
| 2025-09 | +3.4 | +0.8 | +10.2 | 54% | -19.2 |
| 2025-10 | +4.5 | -9.9 | -452.7 | 68% | -11.7 |
| 2025-11 | -6.7 | +4.0 | +5.9 | 65% | -8.4 |
| 2025-12 | +2.9 | +10.9 | +10.3 | 65% | -8.8 |
| 2026-01 (2026) | -2.0 | -19.3 | +4.2 | 27% | -77.2 |
| 2026-02 (2026) | +0.6 | +11.5 | -450.2 | 89% | -2.2 |
| 2026-03 (2026) | +8.3 | +16.3 | +11.6 | 80% | -4.7 |
| 2026-04 (2026) | +7.5 | +5.6 | +4.7 | 84% | +2.7 |
| 2026-05 (2026) | -5.4 | -17.4 | +5.0 | 78% | +0.6 |
| 2026-06 (2026) | -2.1 | +3.0 | +13.8 | 37% | -42.0 |
| 2026-07 (2026) | +3.8 | +16.5 | +4.6 | 73% | -7.6 |
| 2026-08 (2026) | +12.9 | +20.3 | +29.1 | 92% | +4.1 |
| 2026-09 (2026) | +5.1 | +10.0 | +12.0 | 94% | +13.1 |

### Labouchère : Labouchère : SL 3.0% TP 3.00%, long, base 1 €, liste 1-2-3, longueur max 20
| Mois | BTC | ETH | SOL | Autres pièces : part de mois positifs | Autres pièces : moyenne |
|---|---|---|---|---|---|
| 2024-01 | +27.6 | +7.4 | +69.3 | 47% | -77.3 |
| 2024-02 | +41.5 | +50.8 | +52.3 | 95% | +53.6 |
| 2024-03 | +40.9 | +53.5 | +130.7 | 44% | -333.9 |
| 2024-04 | +0.2 | +5.3 | +31.4 | 16% | -158.6 |
| 2024-05 | +23.5 | +33.3 | +73.8 | 81% | +31.7 |
| 2024-06 | -24.0 | -2.5 | +25.2 | 24% | -269.8 |
| 2024-07 | +18.6 | +10.4 | +44.7 | 63% | -22.0 |
| 2024-08 | +21.9 | +6.0 | -690.3 | 17% | -116.2 |
| 2024-09 | +18.3 | +19.2 | +33.2 | 94% | +30.8 |
| 2024-10 | +22.4 | +7.3 | +39.0 | 67% | +2.2 |
| 2024-11 | +45.3 | +60.7 | +80.1 | 98% | +99.3 |
| 2024-12 | -2.6 | +13.7 | +24.0 | 41% | -204.9 |
| 2025-01 | +27.1 | +32.6 | +87.7 | 80% | -10.0 |
| 2025-02 | -58.2 | -36.8 | +19.8 | 81% | +9.5 |
| 2025-03 | +18.1 | +9.0 | +16.5 | 48% | -29.5 |
| 2025-04 | +24.0 | +7.9 | +42.7 | 96% | +46.8 |
| 2025-05 | +18.4 | +61.5 | +33.3 | 61% | -9.4 |
| 2025-06 | +13.9 | +13.4 | +30.3 | 65% | -31.0 |
| 2025-07 | +11.7 | +63.6 | +32.8 | 39% | -76.9 |
| 2025-08 | -9.8 | +38.8 | +47.6 | 77% | -6.2 |
| 2025-09 | +5.5 | -3.0 | +4.2 | 35% | -55.5 |
| 2025-10 | +13.0 | +14.5 | -10.3 | 51% | -27.9 |
| 2025-11 | -32.0 | +9.8 | +4.3 | 48% | -106.7 |
| 2025-12 | +5.8 | +17.8 | +26.0 | 70% | -29.3 |
| 2026-01 (2026) | -38.4 | -132.1 | +2.7 | 11% | -219.7 |
| 2026-02 (2026) | +8.8 | +27.9 | +17.2 | 86% | +11.0 |
| 2026-03 (2026) | +11.0 | +36.3 | +19.6 | 60% | -23.7 |
| 2026-04 (2026) | +16.8 | +11.8 | +22.4 | 81% | -7.5 |
| 2026-05 (2026) | -10.8 | -51.6 | -17.5 | 55% | -24.6 |
| 2026-06 (2026) | -4.9 | +0.1 | +21.6 | 28% | -106.3 |
| 2026-07 (2026) | +8.4 | +24.3 | -1.4 | 51% | -52.9 |
| 2026-08 (2026) | +29.8 | +35.3 | +57.0 | 80% | -1.2 |
| 2026-09 (2026) | +11.8 | +24.3 | +26.6 | 92% | +27.6 |

## Ce que ça veut dire pour Tony
- Oui, une martingale peut être positive **la plupart des mois** : jusqu'à 85-89 % hors échantillon. C'est réel, et c'est pour ça qu'elle donne l'impression de marcher.
- Non, aucune n'est positive **tous** les mois, et celles qui le sont le plus souvent ont les pires mois (−350 € à −990 € sur 1 000 €).
- Sur des prix tirés au hasard, elles font aussi bien : la martingale ne lit rien du marché, elle range autrement le hasard.
- La même conclusion que le 22/10 (martingale-verif.md), PREREG-24 et PREREG-28 : quatre tests, quatre méthodes, le même résultat.

Fichiers : PREREG ../banc-honnete/PREREG-29-martingale-mois-par-mois.md ; jugement.json (tout), complement-dca.json, verif-apres-coup.json, tableaux.md.

# Résultat PREREG-75 : cent stratégies contre la grille W5 (12/11/2026, 06h49)

- Pré-enregistrement : `../banc-honnete/PREREG-75-cent-strategies.md`. Commit c4d2138a à 06h17, avant calcul, plus l'amendement 1 (commits f271c552 et bd679c17, 06h28) qui corrige un bug avant le passage officiel.
- Code : `moteur.py`, `t75.py`, `rapport.py`. Chiffres : `t75.json`, `t75.log`, `rapport.txt`.
- Premier passage (faux, gardé pour la trace) : `t75-v1-bug.log`.

## Verdict (pré-enregistré) : **NON** — aucune des 100 ne bat W5 de façon crédible

| | X\* = W5-miroir (choisie sur P1) | W5 (en service) | Seuil / condition |
|---|---|---|---|
| P1, 4 paires (choix) | **+2 126 €** | +881 € | — |
| C2 : au-dessus du hasard ? | +2 126 € | — | 95e centile du « meilleur de 100 » sous hasard : **+55 317 €** (médiane +4 794 €) ✗ |
| C3 : P2, 4 paires | **−573 €** (0/4 positives) | −245 € | > 0 et > W5 ✗ |
| C4 : 30 paires neuves, P1 + P2 | **−2 768 €** (9/30 positives) | −1 708 € (13/30) | > 0, > W5, ≥ 15/30 ✗ |
| dont 6 paires 1 min (PREREG-74) | −1 303 / −313 € | −957 / −373 € | |
| dont 24 paires tirées (1 h) | −2 014 / +863 € | −3 148 / +2 770 € | |

- **Témoin du banc :** W5 redonne +881,4 / −245,0 € ✓.
- **La choisie de P1** est une grille W5 décalée : 3 niveaux d'achat et 2 de vente au lieu de 2 et 3, donc un léger penchant acheteur. Elle a gagné sur P1 parce que 2024-2025 montait.
- **Hors échantillon,** elle fait **moins bien que W5 partout** : P2, 6 paires neuves, 24 paires tirées.
- **Les quatre critères échouent,** sauf C1 (« ce n'est pas W5 »).

## Le témoin hasard : ce que vaut « la meilleure de 100 » quand il n'y a rien à trouver
- **Le test :** 50 fois, les 4 paires sont mélangées sur 2024-2025 (bougies 1 min permutées, dérive retirée) et les 100 stratégies tournent sur ces faux prix.
- **Le résultat :**
  - la médiane des 100 stratégies sous hasard est de −1 574 € ;
  - la **meilleure des 100** fait en médiane **+4 794 €**. Le 95e centile est à +55 317 €, le minimum à +52 €. **Pas une seule fois sur 50 la meilleure des 100 n'est négative**, sur des prix sans aucune information.
- **Pourquoi c'est si haut :**
  - Les stratégies à levier toujours en position (croisements, supertrend, momentum) font de la loterie : le garde-fou coupe les pertes à −15 %, les gains courent et se composent.
  - Sur 100 tickets, il y en a presque toujours un qui sort.
  - Ceux qui gagnent sous hasard : BB480/2 (6 fois sur 50), ST3 (5), TSM30 (5), RSI30/70 (3), W5-sansProt (3)…
- **Un seuil plus doux, pour information :** en ne gardant que les stratégies « éligibles » (sans paire arrêtée, baisse < 30 %), le meilleur de 100 sous hasard a un 95e centile de +2 855 €. **+2 126 € reste en dessous.**
- **Conclusion :** même avec le seuil le plus doux, le gagnant de P1 ne se distingue pas de la chance.

## Le top 10 de P1, et ce qu'il devient hors échantillon
| Stratégie | P1 4 paires | Éligible | P2 4 paires | 6 neuves P1 / P2 | 24 tirées P1 / P2 | 30 neuves, total (paires +) |
|---|---|---|---|---|---|---|
| W3-L | +2 412 | non (LINK arrêtée) | −707 | +2 475 / −387 | −2 148 / −1 765 | −1 826 (13/30) |
| VB3 | +2 322 | non (baisse −31 %) | −40 | −460 / −413 | +12 737 / −1 936 | +9 928 (16/30) |
| **W5-miroir (X\*)** | +2 126 | oui | −573 | −1 303 / −313 | −2 014 / +863 | −2 768 (9/30) |
| BB20/2.5-E200 | +2 119 | oui | **+308** | +68 / −1 019 | +5 523 / −1 736 | +2 836 (14/30) |
| W4-L | +1 758 | non | −167 | −1 896 / −226 | +423 / −479 | −2 177 (10/30) |
| W5-N9 | +1 142 | oui | −318 | −544 / −287 | −4 393 / +4 617 | −606 (13/30) |
| W5-cap3 | +1 115 | oui | −245 | −1 080 / −380 | −1 945 / +2 126 | −1 280 (13/30) |
| DC168-SL5TP10 | +1 105 | non | −1 441 | +3 779 / −267 | +16 920 / −1 158 | +19 275 (16/30) |
| W5-x0.5 | +1 088 | oui | −32 | −327 / −59 | −1 070 / +854 | −602 (13/30) |
| W5-L | +1 075 | oui | −361 | +704 / −15 | −700 / −540 | −551 (14/30) |

**Lecture :**
- **Le haut de P1 garde un peu de son rang hors échantillon** (rang P1 contre P2 : 0,53 ; contre les paires neuves : 0,40). Mais c'est surtout parce que les stratégies qui perdent beaucoup sur P1 (frais, levier) perdent partout. Cela ne fait pas une gagnante.
- **Aucune des 10 n'est positive à la fois sur P2 et sur la majorité des paires neuves.**
- **BB20/2.5-E200, la seule qui intrigue :** retour à la moyenne sur Bollinger, dans le sens de l'EMA200.
  - Pour elle : deuxième de P1, positive sur P2 (+308 €), positive sur les 30 neuves (+2 836 €).
  - Contre elle : seulement 14 paires positives sur 30, et le total des neuves repose sur quelques paires (KNC +3 002 €, BEL +2 036 €).
  - Ce n'est pas la choisie. La repérer après coup, c'est exactement le piège que ce protocole évite. Au mieux, c'est une hypothèse pour un **nouveau** pré-enregistrement en papier, pas une conclusion.
- **Les gros totaux sur les paires neuves sont des valeurs isolées, pas des signaux :**
  - DC168-SL5TP10 (+16 920 € sur les 24 tirées en P1) et VB3 (+12 737 €) viennent de quelques pièces très tendancielles (CAKE, BNX, BEL, RSR), avec composition à levier 2.
  - « Meilleure hors échantillon » choisie après coup : MACD, +61 518 € sur les neuves, dont +63 274 € sur CAKE seule. Mais −2 327 € sur P1 et −1 041 € sur P2, 4 paires sur 4 arrêtées en P1. À ne pas croire.

## Les 100 en bref
- **Sur P1 :** 32 sur 100 sont positives (28 grilles, 4 directionnelles), 26 éligibles. Les directionnelles perdent presque toutes : frais taker sur des milliers de trades, garde-fou de −15 % à levier 2.
- **Sur P2 :** 19 sur 100 sont positives.
- **Sur les 30 paires neuves cumulées :** 25 sur 100 sont positives, presque toujours grâce à une ou deux pièces.
- **PREREG-30 (sens EMA) refait ici :** E30-L1 à E30-ADX25 perdent toutes, la plupart des paires sont arrêtées par érosion. Avec une taille proportionnelle au capital et plus de 1 900 trades par paire, les frais mangent tout. Cela confirme son « NON DÉMONTRÉ ».
- **Tableau complet** (P1, éligibilité, P2, paires neuves, moteur 1 h, médiane sous hasard) : `rapport.txt`, reproduit plus bas.

## Vérifications faites parce que des résultats étaient trop beaux
1. **Premier passage : +9,9 M€ sur P1 pour E30-EMA20.**
   - Cause : un bug d'optimisme. Le trailing de 1 % calculé sur bougies 1 h montait jusqu'au plus haut de l'heure (ADA, mars 2025 : +39 % dans l'heure).
   - Correction (amendement 1, avant le passage officiel) : exécution à la minute, sommet du trailing sur les clôtures seulement, et arrêt par érosion du capital (règle déjà écrite).
   - Ce bug touchait aussi le témoin hasard du premier passage. Tout est recalculé.
2. **Après correction, des « meilleurs de 100 » sous hasard encore énormes** (jusqu'à +125 000 €).
   - Vérifié : ce n'est pas un bug, c'est la loterie des stratégies à levier qui se composent.
   - La permutation garde la volatilité à la minute. À l'heure, elle la gonfle d'environ 7 %, et au jour d'environ 13 % (SOL : 0,95 → 1,02 % à l'heure, 4,4 → 5,0 % au jour). C'est un biais connu, et il ne joue pas en faveur des stratégies testées.
3. **MACD +63 274 € sur CAKE** : la courbe monte régulièrement sur 23 mois (CAKE très tendancielle en 2025), il n'y a pas de saut isolé. C'est une valeur isolée, pas une erreur de données. Les données CAKE, GMT et BNX sont plausibles (krach du 10/10/2025 compris).
4. **Fidélité du moteur 1 h** (diagnostic, mêmes 4 paires sur P1) :
   - directionnelles : identiques à la minute (corrélation 1,00, écart médian 18 €) ;
   - **grilles : corrélation 0,05 entre minute et heure**, écart médian de 507 € par stratégie.

   Le résultat d'une grille dépend donc presque entièrement du détail du chemin des prix. Sur les 24 paires en 1 h, les chiffres des grilles sont **peu fiables**. Sur les 6 paires simulées à la minute, X\* fait aussi moins bien que W5 (−1 616 € contre −1 330 €) : le verdict ne dépend pas de ce défaut.

## Ma prédiction
- **Fausse :** X\* parmi X20/50-L5, DC480-L5 ou W5-x2. C'est W5-miroir.
- **Juste :** X\* sous le seuil du hasard.
- **Juste :** top 10 à peu près au hasard hors échantillon.
- **Juste :** verdict NON.
- **Fausse sur l'ampleur :** j'attendais un « meilleur de 100 » sous hasard de quelques centaines d'euros ; c'est +4 794 € en médiane.

## Ce que ça veut dire pour Tony
- **Rien dans ces 100 essais ne bat W5 de façon crédible :** ni grille, ni grille filtrée, ni suivi de tendance, ni retour à la moyenne, ni le sens EMA.
- **Le meilleur score sur 2024-2025 (+2 126 €)** est inférieur à ce que donne « la meilleure de 100 » sur des prix inventés, et il perd hors échantillon.
- **W5 elle-même :** sur ses 4 paires en P1 (+881 €), elle fait bien mieux que sur prix mélangés (médiane −1 523 €, 95e centile −681 €). Mais elle perd en 2026 (−245 €) et sur les 30 paires neuves (−1 708 €, 13/30 positives), comme PREREG-74 l'avait vu sur 6 paires.

  Lecture prudente : une grille gagne quand le marché fait des allers-retours, ce que le mélange détruit. Mais ce gain n'a pas tenu ailleurs que sur SOL/LINK/ADA/DOT en 2024-2025.
- **Aucune recommandation de changement en réel :** c'est Tony qui décide.
- **Limites :**
  - données Binance, pas Kraken ;
  - financement non compté ;
  - grilles sur 1 h peu fiables ;
  - témoin hasard un peu plus volatil que le réel à l'heure et au jour.

## Tableau des 100 (P1 = choix ; le reste = contrôles, une seule fois)
| # | Stratégie | P1 4 paires | éligible | baisse port. | arrêtées | P2 4 paires | 30 neuves P1+P2 (paires +) | P1 moteur 1 h | P1 hasard médiane |
|---|---|---|---|---|---|---|---|---|---|
| 1 | W5 | +881 | oui | -20 % | 0 | -245 | -1 708 (13/30) | +838 | -1 523 |
| 2 | W3 | -391 | non | -20 % | 2 | -683 | -8 595 (6/30) | -492 | -1 646 |
| 3 | W4 | -605 | non | -24 % | 2 | -214 | -3 707 (11/30) | +583 | -1 648 |
| 4 | W6 | -399 | non | -25 % | 2 | +265 | -2 085 (12/30) | +769 | -1 472 |
| 5 | W8 | +251 | non | -15 % | 1 | +423 | -1 002 (13/30) | +538 | -1 293 |
| 6 | W12 | +468 | oui | -13 % | 0 | -123 | +51 (15/30) | +304 | -1 144 |
| 7 | W15 | +444 | oui | -9 % | 0 | -87 | +4 699 (19/30) | +700 | -1 021 |
| 8 | W5-N3 | -434 | non | -26 % | 2 | -728 | -3 812 (12/30) | -959 | -1 647 |
| 9 | W5-N7 | -262 | oui | -19 % | 0 | -189 | -4 068 (10/30) | +352 | -1 450 |
| 10 | W5-N9 | +1 142 | oui | -14 % | 0 | -318 | -606 (13/30) | +1 424 | -1 525 |
| 11 | W3-N7 | -979 | non | -35 % | 3 | -256 | -6 576 (9/30) | +414 | -1 656 |
| 12 | W5-x0.5 | +1 088 | oui | -7 % | 0 | -32 | -602 (13/30) | +479 | -1 278 |
| 13 | W5-x2 | +1 054 | non | -34 % | 1 | -590 | -2 969 (10/30) | -590 | -1 660 |
| 14 | W5-cap2 | +811 | oui | -18 % | 0 | -287 | -2 611 (13/30) | +995 | -1 493 |
| 15 | W5-cap3 | +1 115 | oui | -17 % | 0 | -245 | -1 280 (13/30) | +820 | -1 504 |
| 16 | W3-x2 | -1 699 | non | -45 % | 4 | -212 | -9 629 (6/30) | +1 224 | -1 703 |
| 17 | W5-L | +1 075 | oui | -17 % | 0 | -361 | -551 (14/30) | +1 324 | -1 143 |
| 18 | W5-S | -290 | oui | -15 % | 0 | -231 | -7 284 (8/30) | -329 | -1 203 |
| 19 | W3-L | +2 412 | non | -13 % | 1 | -707 | -1 826 (13/30) | +1 218 | -1 490 |
| 20 | W3-S | -1 758 | non | -44 % | 4 | -441 | -15 326 (2/30) | -1 186 | -1 644 |
| 21 | W8-L | -402 | non | -18 % | 1 | +165 | +3 436 (21/30) | +670 | -1 017 |
| 22 | W8-S | -359 | oui | -12 % | 0 | +172 | -3 689 (10/30) | -535 | -876 |
| 23 | W3-F | -310 | non | -19 % | 2 | -895 | -9 882 (8/30) | +258 | -1 621 |
| 24 | W8-F | -214 | oui | -13 % | 0 | -56 | +107 (17/30) | +306 | -960 |
| 25 | W5-F20 | +91 | oui | -15 % | 0 | -113 | -6 878 (7/30) | +642 | -1 158 |
| 26 | W5-F200 | +40 | oui | -13 % | 0 | -112 | -6 745 (9/30) | +188 | -1 134 |
| 27 | W5-A20 | -117 | oui | -9 % | 0 | -180 | -1 805 (12/30) | -842 | -830 |
| 28 | W5-A25 | -602 | non | -16 % | 1 | -81 | +1 347 (17/30) | -816 | -1 151 |
| 29 | W5-A30 | -174 | oui | -15 % | 0 | -94 | +3 310 (14/30) | -829 | -1 236 |
| 30 | W3-A25 | +253 | non | -14 % | 1 | -180 | -4 317 (10/30) | -494 | -1 618 |
| 31 | W5-calme | +377 | oui | -9 % | 0 | -329 | -37 (16/30) | +205 | -1 236 |
| 32 | W5-agité | +938 | oui | -20 % | 0 | +90 | -4 838 (7/30) | +493 | -1 117 |
| 33 | W3-calme | +104 | non | -18 % | 1 | +32 | -2 002 (12/30) | -257 | -1 592 |
| 34 | W5-L-hausse | +485 | oui | -15 % | 0 | -255 | -2 660 (12/30) | +590 | -895 |
| 35 | W3-L-hausse | +54 | non | -19 % | 2 | -859 | -4 710 (12/30) | +902 | -1 120 |
| 36 | W-ATR1 | +11 | oui | -11 % | 0 | -499 | -645 (12/30) | +563 | -1 190 |
| 37 | W-ATR2 | +559 | oui | -11 % | 0 | +32 | +3 953 (20/30) | +452 | -879 |
| 38 | W-ATR3 | +330 | oui | -4 % | 0 | -133 | +729 (15/30) | +95 | -622 |
| 39 | W5-sansDJ | +406 | non | -13 % | 2 | +80 | -3 244 (11/30) | -88 | -1 280 |
| 40 | W5-sansProt | -1 404 | non | -71 % | 3 | +868 | -5 683 (6/30) | +7 428 | -1 754 |
| 41 | W5-gf80 | +946 | oui | -22 % | 0 | -348 | -1 813 (12/30) | +800 | -1 538 |
| 42 | W5-gf90 | +252 | non | -25 % | 1 | -360 | +497 (13/30) | -429 | -1 492 |
| 43 | W5-miroir | +2 126 | oui | -18 % | 0 | -573 | -2 768 (9/30) | +1 217 | -1 543 |
| 44 | W3-miroir | -1 360 | non | -38 % | 3 | -648 | -4 216 (8/30) | +1 883 | -1 652 |
| 45 | W5-A25-F | -343 | non | -16 % | 1 | +81 | -70 (13/30) | -488 | -725 |
| 46 | W8-N7 | -903 | non | -32 % | 2 | +814 | -705 (16/30) | +283 | -1 288 |
| 47 | W5-S-baisse | -538 | oui | -19 % | 0 | +98 | -5 247 (7/30) | -604 | -765 |
| 48 | W12-x2 | +236 | non | -18 % | 1 | -277 | -3 506 (12/30) | +290 | -1 411 |
| 49 | W4-L | +1 758 | non | -18 % | 1 | -167 | -2 177 (10/30) | +2 573 | -1 301 |
| 50 | W6-A25 | -416 | non | -15 % | 1 | +476 | +2 412 (19/30) | -401 | -1 156 |
| 51 | X12/26 | -2 003 | non | -53 % | 4 | -364 | +6 932 (1/30) | -2 069 | -2 813 |
| 52 | X20/50 | -1 784 | non | -58 % | 4 | -1 822 | +55 704 (4/30) | -1 807 | -2 337 |
| 53 | X50/200 | -1 962 | non | -63 % | 4 | -1 174 | -15 101 (6/30) | -1 872 | -1 827 |
| 54 | X10/30 | -2 188 | non | -58 % | 4 | +55 | +47 213 (1/30) | -2 154 | -2 885 |
| 55 | X20/50-L | -1 235 | non | -70 % | 3 | -1 661 | +14 693 (5/30) | -1 242 | -1 667 |
| 56 | X50/200-L | -854 | non | -52 % | 2 | -1 148 | -12 520 (5/30) | -858 | -1 700 |
| 57 | X20/50-ATR | -1 357 | non | -66 % | 3 | -1 864 | +59 452 (5/30) | -1 712 | -2 342 |
| 58 | X50/200-ATR | -2 001 | non | -61 % | 4 | -1 460 | -18 091 (3/30) | -1 961 | -1 807 |
| 59 | X20/50-L5 | -1 806 | non | -52 % | 4 | -1 794 | -24 212 (0/30) | -1 752 | -1 842 |
| 60 | X50/200-L1 | +152 | non | -53 % | 0 | -1 250 | -5 398 (11/30) | +187 | -1 461 |
| 61 | DC24 | -1 823 | non | -47 % | 4 | -622 | -20 201 (1/30) | -1 852 | -1 709 |
| 62 | DC72 | -1 761 | non | -58 % | 4 | -1 748 | +61 776 (5/30) | -1 728 | -1 729 |
| 63 | DC168 | -1 762 | non | -56 % | 4 | -1 795 | -17 439 (3/30) | -1 794 | -1 728 |
| 64 | DC480 | -1 687 | non | -71 % | 4 | +86 | -15 284 (5/30) | -1 563 | -1 746 |
| 65 | DC168-ATR3 | -1 829 | non | -57 % | 4 | -1 793 | -16 403 (2/30) | -1 716 | -1 758 |
| 66 | DC72-ATR2 | -1 754 | non | -51 % | 4 | -1 724 | +10 487 (4/30) | -1 742 | -1 734 |
| 67 | DC168-L | -1 734 | non | -59 % | 4 | -1 755 | -10 792 (6/30) | -1 707 | -1 316 |
| 68 | DC480-L1 | -1 230 | non | -55 % | 3 | +11 | -7 902 (7/30) | -1 221 | -1 156 |
| 69 | DC480-L5 | -1 811 | non | -71 % | 4 | -1 902 | -19 932 (2/30) | -1 810 | -1 861 |
| 70 | DC168-SL5TP10 | +1 105 | non | -36 % | 3 | -1 441 | +19 275 (16/30) | +1 168 | -1 642 |
| 71 | ST2 | -1 891 | non | -58 % | 4 | +1 408 | +23 850 (10/30) | -1 818 | -1 812 |
| 72 | ST3 | -1 914 | non | -72 % | 4 | -1 749 | +3 698 (6/30) | -1 803 | -1 808 |
| 73 | TSM7 | -1 772 | non | -66 % | 4 | -1 104 | -8 494 (5/30) | -1 776 | -1 796 |
| 74 | TSM30 | -1 703 | non | -68 % | 4 | -1 713 | -15 893 (6/30) | -1 931 | -1 812 |
| 75 | TSM7-L | -1 187 | non | -63 % | 3 | -920 | -12 081 (4/30) | -1 275 | -1 733 |
| 76 | MACD | -2 327 | non | -55 % | 4 | -1 041 | +61 518 (2/30) | -2 346 | -2 053 |
| 77 | MACD-L200 | -1 579 | non | -59 % | 3 | -1 621 | +537 (6/30) | -1 592 | -1 634 |
| 78 | VB3 | +2 322 | non | -31 % | 0 | -40 | +9 928 (16/30) | +2 322 | -254 |
| 79 | RSI30/70 | -1 014 | non | -55 % | 2 | -525 | -10 102 (5/30) | -1 014 | -1 434 |
| 80 | RSI30-L | -1 395 | non | -48 % | 3 | +526 | -13 395 (5/30) | -1 395 | -394 |
| 81 | RSI20/80 | -1 708 | non | -48 % | 4 | -1 094 | -13 261 (3/30) | -1 708 | -302 |
| 82 | RSI30/70-E200 | -378 | non | -15 % | 1 | -213 | +4 469 (18/30) | -378 | -244 |
| 83 | RSI30/70-L5 | -1 792 | non | -74 % | 4 | -1 715 | -23 222 (0/30) | -1 792 | -1 766 |
| 84 | BB20/2 | -1 692 | non | -59 % | 4 | -1 652 | -14 087 (3/30) | -1 695 | -1 686 |
| 85 | BB20/3 | -1 738 | non | -52 % | 4 | -1 373 | -7 447 (8/30) | -1 738 | -389 |
| 86 | BB20/2-L | -1 412 | non | -63 % | 3 | -1 680 | -11 687 (5/30) | -1 416 | -1 582 |
| 87 | BB20/2.5-E200 | +2 119 | oui | -24 % | 0 | +308 | +2 836 (14/30) | +2 107 | -682 |
| 88 | BB20/2-L5 | -1 759 | non | -76 % | 4 | -1 765 | -23 322 (0/30) | -1 759 | -1 782 |
| 89 | BBX20/2 | -1 655 | non | -45 % | 4 | -697 | -20 506 (1/30) | -1 652 | -1 661 |
| 90 | BB480/2 | -1 809 | non | -45 % | 4 | -1 400 | -14 907 (3/30) | -1 810 | -591 |
| 91 | E30-L1 | -1 662 | non | -48 % | 4 | -1 649 | -14 056 (3/30) | -1 654 | -1 649 |
| 92 | E30-L2 | -1 760 | non | -51 % | 4 | -1 740 | -20 979 (1/30) | -1 729 | -1 692 |
| 93 | E30-L5 | -1 686 | non | -51 % | 4 | -1 710 | -23 478 (0/30) | -1 824 | -1 787 |
| 94 | E30-EMA20 | -1 712 | non | -42 % | 4 | -1 704 | -16 531 (1/30) | -1 729 | -1 703 |
| 95 | E30-EMA200 | -1 700 | non | -57 % | 4 | -1 727 | -20 557 (0/30) | -1 682 | -1 708 |
| 96 | E30-3/2/1 | -1 662 | non | -45 % | 4 | -1 646 | -22 077 (0/30) | -1 652 | -1 668 |
| 97 | E30-8/5/2 | -1 719 | non | -49 % | 4 | -918 | -16 739 (3/30) | -1 734 | -1 768 |
| 98 | E30-mart | -1 727 | non | -77 % | 4 | -1 737 | -22 779 (0/30) | -1 764 | -1 727 |
| 99 | E30-ADX25 | -1 750 | non | -54 % | 4 | -1 546 | -16 935 (3/30) | -1 662 | -1 702 |
| 100 | BH | -1 158 | non | -59 % | 3 | -722 | -401 (6/30) | -1 157 | -1 240 |

**VERDICT (règles de PREREG-76, écrites avant) : B contre A = NON DÉMONTRÉ ; C (martingale avec inversion) = NON DÉMONTRÉ — elle fait +36 $ sur 32 mois, mais c'est dans la fourchette du hasard, ça ne tient pas sur 6 paires neuves, et un compte de 6,40 $ aurait été vidé dans un départ sur trois.**

# PREREG-76 — Résultat (17/11/2026)

Pré-enregistrement : `ai-lab/banc-honnete/PREREG-76-grille-vs-martingale.md` (commit `934b074a`, avant tout calcul).
Fichiers bruts ici : `t76.json`, `t76.log`, `rapport.txt` (tous les tableaux), `fidelite.log` / `fidelite.json`, `t76-v1-plantage.log`.
Scripts : `sim76.py`, `t76.py`, `rapport.py`, `kraken1m.py`.

## Ce qui a été comparé
- **A** : la grille W5 telle que Martin la joue vraiment (code déployé `d7ff867`) — protection à deux branches, passage toutes les 15 min.
- **B** : la même, mais la branche « perd » reçoit le réglage de la branche « gagne » (stop 0,6 %, objectif 2,5 %, depuis le prix courant).
- **C** : la martingale avec inversion de `martingale.py`, base 3 $ par paire, départ long (C+) et départ short (C−) ; C = moyenne.
- Références : achat simple de 3 $ par paire, et ne rien faire (0).
Données : bougies 1 minute Binance, SOL/LINK/ADA/DOT, 01/02/2024 → 30/09/2026 (32 mois). Frais Kraken (maker 0,02 %, taker 0,05 %).
Stop toujours testé avant l'objectif. **Financement ignoré** (absent des données). Mises réelles : A/B ≈ 2 à 2,8 $ par niveau, C 3 $ de base (jusqu'à 24 $).

## Tableau principal (4 paires, en dollars)
| Mesure | A (actuelle) | B (protection unique) | C (martingale, moyenne) | C+ / C− | Achat simple |
|---|---|---|---|---|---|
| **Total 32 mois** | **−4,91** | **−4,11** | **+36,16** | +32,60 / +39,72 | −3,52 |
| 02/2024 → 12/2025 | −2,78 | −2,90 | +38,69 | +35,13 / +42,25 | −2,96 |
| 01 → 09/2026 | −2,12 | −1,21 | **−2,53** | −2,53 / −2,53 | −0,56 |
| Mois positifs | 6/32 (19 %) | 14/32 (44 %) | 19/32 (59 %) | 19 / 19 | 16/32 |
| Pire mois | −0,81 | −0,78 | **−12,71** (04/2026) | idem | −7,19 |
| Pire baisse du portefeuille | −6,07 | −4,95 | **−30,50** | idem | −20,25 |
| Positions fermées (gagnantes) | 3 833 (54 %) | 3 818 (27 %) | ≈ 1 590 (34 %) | | — |
| Pire série de pertes d'affilée (somme) | 11 (−0,48) | 27 (−0,65) | **26 (−14,69)** | idem | — |
| Frais payés | 5,18 | 5,91 | ≈ 12,9 | | — |
| Par dollar échangé | −2,7 pb | −2,2 pb | ≈ +14 pb | +12,7 / +15,3 | — |
| Gain / pire baisse | −0,81 | −0,83 | ≈ +1,2 | +1,07 / +1,30 | −0,17 |
| Paires positives | 1/4 (DOT) | 1/4 (DOT) | 3/4 (SOL perd) | | 1/4 |
| **Ruine, compte 6,40 $, 90 jours** | **0 %** (0/884) | **0 %** (0/884) | **33,5 %** (593/1 768) | 34,7 % / 32,4 % | 10,0 % |
| Perdant au bout de 90 jours | 79 % | 62 % | ≈ 24 % | 24,9 % / 23,5 % | 67 % |
| Pire résultat à 90 jours | −2,02 | −1,84 | −36,89 | −36,89 / −31,19 | −6,63 |
| **6 paires neuves : total** | −6,37 | −8,25 | **−7,19** | −12,60 / −1,79 | +7,05 |
| 6 paires neuves : positives | 1/6 | 0/6 | 3/6 | | 4/6 |
| Témoin de hasard, médiane | −11,97 | −12,19 | +2,16 | +0,37 / +2,81 | +0,39 |
| Témoin de hasard, 5e → 95e centile | −15,5 → −8,2 | −16,0 → −7,6 | **−53,3 → +45,8** | | −2,1 → +3,7 |
| Part des 200 mélanges qui font au moins autant que le réel | 0,5 % | 0 % | **10 %** | 11 % / 9 % | 99 % |

Le détail par mois et par paire est dans `rapport.txt`.

## B contre A : NON DÉMONTRÉ
| Critère écrit avant | Résultat | Passe ? |
|---|---|---|
| B1 : B − A > 0 au total | +0,80 $ | oui |
| B2 : B mieux dans ≥ 22 mois sur 32 | 18/32 | non |
| B3 : 6 paires neuves, B − A > 0 et B mieux sur ≥ 4/6 | −1,88 $, 2/6 | non |
| B4 : B − A > 0 sur les deux moitiés | −0,12 $ puis +0,92 $ | non |

- Sur prix mélangés, B − A vaut −0,26 $ en médiane (de −3,3 à +3,2) : le +0,80 $ réel est dans le bruit.
- **Le constat des 5 jours est pourtant confirmé sur 32 mois** : dans A, la branche « perd » fait −20,93 $ sur 1 706 positions et la
  branche « gagne » +17,18 $ sur 2 120. Mais **donner à la branche « perd » le réglage serré ne récupère pas cet argent** : dans B,
  les mêmes positions sortent au stop à 0,6 % trois fois sur quatre (3 076 stops, 736 objectifs) et le total reste négatif (−3,13 $
  avant les quelques positions sans protection). La perte ne vient pas du réglage de la branche, elle vient des positions elles-mêmes.
- « B gagne de l'argent » : non (total négatif).
- A et B perdent tous les deux, sur les 4 paires comme sur les 6 neuves. Les deux font **mieux que sur prix mélangés** (−4,9 contre
  −12 en médiane) : les prix réels aident un peu la grille, pas assez pour payer les frais (5 à 6 $).

## C (martingale) : NON DÉMONTRÉ — 2 critères sur 7
| Critère écrit avant | Résultat | Passe ? |
|---|---|---|
| C1 : total moyen > 0 | +36,16 $ | **oui** |
| C2 : les deux départs > 0 | +32,60 et +39,72 $ | **oui** |
| C3 : ≥ 20 mois positifs sur 32 | 19/32 | non (à un mois près) |
| C4 : au-dessus du 95e centile du hasard (+45,80 $) | +36,16 $ ; 10 % des mélanges font autant | non |
| C5 : 6 paires neuves > 0 et ≥ 4/6 positives | −7,19 $, 3/6 | non |
| C6 : ruine < 5 % avec 6,40 $ | 33,5 % | non |
| C7 : > 0 sur les deux moitiés | +38,69 $ puis −2,53 $ | non |

Ce qui parle **pour** la martingale (je le dis sans le rogner) : c'est le seul bras positif ; +36 $ avec 3 $ de base par paire ;
positive dans les deux sens de départ ; 3 paires sur 4 ; DOGE (pour information) +10,66 $ ; trois départs sur quatre sont gagnants
après 90 jours (médiane +5,5 $).

Ce qui empêche de dire « démontré » :
- **Le hasard fait pareil.** Sur prix mélangés, la même règle donne de −53 $ à +46 $ : c'est une loterie à très large éventail, et
  +36 $ est dedans. La martingale ne change pas l'espérance, elle étale les résultats.
- **Tout le gain vient de 2024-2025 ; 2026 est négatif** (−2,53 $), avec un mois à −12,71 $ (04/2026).
- **Hors de ses 4 paires, elle perd** : −7,19 $ sur ATOM, AVAX, BCH, BNB, XRP, LTC (BNB −10,70 $, LTC −13,56 $).
- **Le compte ne survit pas.** Pire baisse −30,50 $ ; pire série 26 pertes d'affilée (−14,69 $) ; avec 6,40 $ pour les 4 paires,
  un départ sur trois est ruiné dans les 90 jours (un sur deux sur les 6 paires neuves). Pour tenir la pire baisse observée il
  faudrait environ 30 $ de compte, et C porte jusqu'à 96 $ de positions : avec 6,40 $ Kraken refuserait une partie des ordres.
- Les deux départs ne sont pas deux essais indépendants : à partir d'avril 2024 C+ et C− jouent exactement les mêmes coups.

## Contrôle de fidélité (fait avant le calcul officiel, du premier coup, sans retouche)
| | Simulé | Réel |
|---|---|---|
| A, 11/11 22h45Z → 17/11 : positions fermées | 26 | 28 |
| A : net | −10,3 c | ≈ −10 c |
| A : 14/11 | −22,6 c, trois stops de −6,2 / −7,4 / −8,6 c | −25,1 c, trois pertes de 6–9 c |
| A : gros gains | 3 (5,3 à 7,2 c) | 4 (5–7 c) |
| A : branche « perd » / « gagne » | −18,7 c sur 12 / +8,4 c sur 14 | −21 c sur 8 / +11 c sur 20 |
| C : DOGE short 3 $, premier coup | +29,4 c, fermé le 14/11 17h23Z | fermé 17h24Z, +57,8 c pour 6 $ |

Jour par jour l'accord est moins bon (13/11 : −1,4 c simulé contre +16,8 c réel ; 16/11 : +11,9 c contre −0,5 c).

## Trois faits trouvés en lisant le code et le journal (vérifiés)
1. **La pause de régime est toujours active en réel**, malgré la config « seuils 1000 » : le journal du 14 au 17/11 montre les
   grilles ouvertes seulement si ADX < 40 et Bollinger < 4 %, et 47 « REGIME SWITCH ». La grille réelle n'est pas la « W5 » de PREREG-73/75.
2. Le stop serré est à **0,6 %** du prix courant (pas 0,4 %) : constante du code et lignes du journal.
3. Le code déployé est le commit `d7ff867` de la branche `retour-avril` ; le dépôt principal de Martin contient une autre version.

## Amendements
- Aucun sur les règles ni sur les simulateurs.
- Un correctif technique (commit `c3d391b9`) : le premier lancement officiel a planté à l'écriture du JSON après avoir affiché les
  cinq totaux des 4 paires. Seule la fonction d'écriture a été changée ; le relancement redonne exactement les mêmes totaux.
- L'heure écrite en tête du prereg (« 02h45 ») était fausse : commit à 02h25.

## Ce qui reste incertain
- **Données Binance, pas Kraken** ; financement, glissement, marge et liquidation non simulés. Les stops sont exécutés à leur prix
  même dans une bougie violente : c'est optimiste pour les trois bras, et sans doute le plus pour C (grosses positions, tout repose sur le stop).
- Le témoin de hasard de C a une moyenne de −0,8 $ alors que les frais font ≈ 13 $ : il reste ≈ +12 $ bruts (± 2) que je n'explique
  pas. Sur une marche au hasard propre le simulateur donne bien 0 (+0,1 ± 0,3). Hypothèse non vérifiée : l'optimisme sur les stops
  ci-dessus. Conséquence : le critère C4 est sensible à ce point (le 95e centile serait vers +34 $ sans cet écart, et C passerait de
  justesse) ; les critères C3, C5, C6, C7 échouent sans lui, le verdict ne change pas.
- Le témoin mélange les bougies : il casse aussi les grappes de volatilité, donc le régime de la grille s'y comporte autrement.
- La mesure de ruine utilise des fenêtres de 90 jours qui se chevauchent : c'est une fréquence observée, pas une probabilité exacte.
- 5 jours de fidélité, c'est peu : le simulateur retrouve les totaux et la forme, pas le détail jour par jour.

## Après coup, pas une preuve
- B est meilleur que A en 2026 (+0,92 $) et moins bon avant : rien à en tirer.
- Le mois positif en plus qui manque à C3 (19 au lieu de 20) ne changerait pas le verdict.
- Contrôle de mécanique fait après le calcul : martingale sur marches au hasard fabriquées, brut de frais = +0,1 ± 0,3 $ (pas de biais du moteur).

## Mes prédictions
B contre A : j'avais mis 50 % sur « mieux sans preuve » et 30 % sur « non démontré » → c'est « non démontré ». A et B négatifs (70 %) : oui.
C « non démontré » (90 %) : oui. **C total négatif (65 %) : faux, il est positif.** Ruine > 5 % (75 %) : oui.

# Pré-enregistrement 20 : le chef a-t-il un vrai TIMING ?
Figé et commité le 22/10/2026 à 01h58, APRÈS relecture d'équité par le quant (corrections intégrées ci-dessous) et AVANT tout calcul.
Question posée par la revue du quant (22/10) : le chef de PREREG-18 battait le hasard, mais le témoin n'égalisait ni le nombre de trades ni le type de stratégie. Ce test isole le timing.

## Marchés neufs (jamais touchés par le banc)
18 marchés Kraken Futures avec historique depuis 01/2024, en 6 groupes de 3 :
G1 ARB BNB INJ · G2 FET GRT ALGO · G3 CRV LDO IMX · G4 RUNE EGLD SAND · G5 MANA AXS APE · G6 DYDX GALA COMP. (PAXG retiré sur avis du quant : l'or bouge trop peu pour des TP/SL de 2-3 % et casserait l'homogénéité ; remplacé par COMP, premier de la liste COMP 1INCH SNX ENS… vérifiée avec historique depuis 01/2024.)
Bougies 15 min et 1 h, 01/01/2024 → 17/10/2026. Bibliothèque par groupe = 120 stratégies (3 marchés × 2 unités × 4 signaux × 5 TP/SL, exécution t17_lib : ouverture suivante, gaps, pire cas, taker 0,05 %/côté, mise fixe, 24 bougies max).

## Le chef (figé, identique à PREREG-18)
Chaque lundi : score = somme des rendements des trades déjà SORTIS sur [w−8, w) ; on joue à poids égal les 10 meilleures au score > 0 ; gain = trades ENTRÉS pendant la semaine w.

## Témoin T1 — jumeaux stratifiés (même case)
Chaque lundi, les stratégies choisies par le chef sont remplacées par un tirage au hasard sans remise (au sein de la semaine) dans LEUR CASE ENTIÈRE, choix du chef compris (permutation standard) : même unité de temps, même couple TP/SL, même moitié (coupure à la médiane, égalités départagées au hasard, graine fixe) du nombre de trades sortis sur [w−8, w). Si une case contient moins de stratégies que de choix à remplacer, on élargit à la case unité × TP/SL (12) et on le journalise ; test INVALIDE si cet élargissement touche > 20 % des remplacements. Même nombre de stratégies par semaine. 1 000 tirages par groupe, graines fixes, tirages appariés pour la somme des 6 groupes.
Diagnostic obligatoire : nombre MOYEN (sur les 1 000 jumeaux) de trades ENTRÉS à ±10 % de celui du chef ; sinon test INVALIDE (pas de verdict).

## Témoin T2 — chef décalé (information périmée)
Même score mais calculé sur [w−8−d, w−d), d tiré au hasard entre 9 et 52 semaines (une valeur par tirage et par semaine). Garde le profil des stratégies choisies, casse la fraîcheur de l'information. 1 000 tirages par groupe.

## Période jugée
Chef, T1 et T2 sur les MÊMES semaines : w ≥ wk(01/01/2024) + 60 (≈ mars 2025) jusqu'au 17/10/2026, pour que T2 ait toujours son historique.

## Verdict
TIMING CONFIRMÉ seulement si : somme du chef > 95e centile de T1 ET > 95e centile de T2 (sommes appariées sur les 6 groupes), ET (critère secondaire, les groupes étant corrélés) ≥ 4 groupes sur 6 au-dessus de la médiane de T1.
Effet affiché : chef − médiane de T1, avec intervalle à 95 % par rééchantillonnage en blocs de 4 semaines.
Sinon : « timing non démontré » (et non « impossible »). Rentabilité affichée à part (somme > 0 ?), sans conditionner le verdict de timing.

**VERDICTS (règles de PREREG-77, écrites avant) : Piste 1 (dette qui gonfle, prix calme) = NON DÉMONTRÉ · Piste 2 (retard des altcoins sur le BTC à la minute) = PERD · Piste 3 (foule d'un seul côté) = NON DÉMONTRÉ. Aucun avantage de trading démontré.**

# PREREG-77 — Résultat (17/11/2026)

Pré-enregistrement : `ai-lab/banc-honnete/PREREG-77-trois-pistes-neuves.md` (commit `cc67e0bf`, 02h45, avant tout téléchargement et tout calcul ;
amendement technique n°1 et contrôles : commit `21a38bdc`, 03h00, avant le lancement officiel).
Fichiers bruts ici : `t77.json`, `t77.log` (lancement officiel, une seule fois), `controle.log` / `controle.json`, `donnees77.log`,
`donnees77-v1-plantage.log`. Scripts : `donnees77.py`, `sim77.py`, `t77.py`.

## Ce qui a changé par rapport à la demande
La piste « nouvelles cotations de perpétuels » était **déjà jugée 9 fois** (PREREG-46, 47, 53, 54, 56, 57, 58, 59, 60). Je l'ai
remplacée par une idée jamais testée : **la foule d'un seul côté** (rapport comptes acheteurs / comptes vendeurs publié par
Binance toutes les 5 minutes). La piste 2 avait un voisin (PREREG-52, à l'heure, PERD) ; l'échelle de la minute était neuve.

## Règles communes (rappel)
Coût 0,14 % l'aller-retour (taker 0,05 % + glissement 0,02 % par côté), entrée à l'ouverture de la bougie suivante, réglage
choisi sur 02/2024 → 12/2025 (SOL, LINK, ADA, DOT), jugé une fois sur 01 → 09/2026, puis sur des paires jamais utilisées pour
ces idées. Témoin de hasard : la même règle avec les signaux décalés d'un nombre de jours tiré au hasard (2 000 tirages).
Seuil : p < 0,0167 (5 % divisé par 3 pistes). Chiffres = **gain net moyen par trade**, en % de la mise.

## Piste 1 — La dette gonfle pendant que le prix dort → NON DÉMONTRÉ
Règle : positions ouvertes en hausse sur 24 h au-dessus de leur centile q (90 jours) + prix calme → on joue la sortie de la
fourchette des 24 h, stop à l'autre bord, sortie après H.

| | Trades | Net moyen | Somme | Gagnants | Témoin de hasard (moyenne ± écart) | p |
|---|---|---|---|---|---|---|
| Réglage, q = 90e, H = 4 h | 388 | +0,12 % | +46 % | | | |
| **Réglage, q = 90e, H = 24 h (choisi)** | 374 | **+0,36 %** (± 0,30) | +136 % | 51 % | | |
| Réglage, q = 97,5e, H = 4 h | 107 | +0,09 % | +10 % | | | |
| Réglage, q = 97,5e, H = 24 h | 106 | −0,08 % | −8 % | | | |
| **Jugement 2026, 4 paires** | 101 | **+0,00 %** (± 0,34) | +0,3 % | 50 % | +0,05 ± 0,27 % | **0,56** |
| **Jugement 2026, 8 paires neuves** | 212 | **+0,47 %** (± 0,22) | +99,5 % | 52 % | −0,01 ± 0,16 % | **0,001** |
| Info : paires neuves sur la période de réglage | 636 | −0,30 % (± 0,16) | −188 % | 46 % | | |

Par pièce en 2026 : SOL −0,75 % (27) · LINK +0,25 % (24) · ADA +0,04 % (24) · DOT +0,53 % (26) ‖ ATOM +0,24 % (34) · AVAX +0,60 % (28) ·
BCH +1,87 % (19) · BNB −0,15 % (20) · XRP +0,31 % (26) · LTC −0,31 % (32) · DOGE +0,70 % (28) · BTC +0,97 % (25).
Information déclarée (volatilité) : |mouvement| moyen des 24 h après le signal = 2,50 % contre 2,53 % pour le témoin sur les
4 paires (p 0,56) ; 2,52 % contre 2,08 % sur les paires neuves (p 0,0005).

Lecture : le critère principal (4 paires, 2026) est à zéro, donc **pas démontré**. Mais ce n'est pas « perd » : les 8 paires
neuves font +0,47 % par trade en 2026, loin du témoin. Ce qui retient d'y croire : ces mêmes paires neuves **perdent** sur
2024-2025 (−0,30 %), les 4 paires de réglage font l'inverse (bon en 2024-25, nul en 2026), et l'erreur type simple (± 0,22)
donne un écart d'environ 2 erreurs types, beaucoup moins net que le p du témoin. Un signe qui change selon le groupe et
l'époque ressemble à du bruit. **Reste une piste à suivre en avant, pas un avantage.**

## Piste 2 — Les altcoins en retard d'une minute sur le BTC → PERD
Règle : BTC bouge de τ ou plus en k minutes → on entre sur l'altcoin dans le même sens à l'ouverture suivante, sortie h minutes après.

| Réglage (4 paires, 02/2024 → 12/2025) | Trades | Net moyen |
|---|---|---|
| k = 1 min, τ = 0,3 %, h = 1 / 5 / 15 min | 21 148 / 14 644 / 10 744 | −0,125 % / −0,093 % / −0,149 % |
| k = 1 min, τ = 0,6 %, h = 1 / **5** / 15 min | 2 216 / **1 544** / 1 260 | −0,052 % / **+0,019 %** (± 0,094) / −0,105 % |
| k = 5 min, τ = 0,3 %, h = 1 / 5 / 15 min | 203 028 / 80 880 / 49 544 | −0,139 % / −0,143 % / −0,156 % |
| k = 5 min, τ = 0,6 %, h = 1 / 5 / 15 min | 29 500 / 12 860 / 9 208 | −0,136 % / −0,153 % / −0,147 % |

| Réglage choisi : k = 1, τ = 0,6 %, h = 5 | Trades | Net moyen | Somme | Gagnants | Témoin | p |
|---|---|---|---|---|---|---|
| **Jugement 2026, 4 paires** | 496 | **−0,29 %** (± 0,05) | −144 % | 35 % | −0,14 ± 0,02 % | **1,00** |
| **Jugement 2026, 7 paires neuves** | 868 | **−0,28 %** (± 0,03) | −239 % | 31 % | −0,14 ± 0,02 % | **1,00** |
| Info : paires neuves sur la période de réglage | 2 702 | −0,06 % (± 0,05) | −164 % | 38 % | | |
| Info : entrée une minute plus tard, 2026 (4 paires / neuves) | 496 / 868 | −0,17 % / −0,17 % | | | | |

Les 11 pièces perdent toutes en 2026 (de −0,21 % à −0,35 %). Les trades tombent aux mêmes minutes sur toutes les pièces : il n'y
a en réalité que 124 secousses du BTC en 2026, pas 496 paris indépendants.
Lecture : 11 réglages sur 12 sont négatifs dès le réglage ; le seul positif (+0,02 %, dans le bruit) fait **pire que le hasard**
en 2026. Avant coût, l'altcoin a même reculé de 0,15 % en moyenne après la secousse : pas de retard à exploiter, plutôt un
petit retour en arrière. Ce retour (0,15 % brut) ne paie pas non plus les 0,14 % de coût — *après coup, pas une preuve*.

## Piste 3 — La foule d'un seul côté → NON DÉMONTRÉ
Règle : chaque jour à 00:00 UTC, si le rapport comptes acheteurs / vendeurs est dans ses a % les plus hauts des 90 derniers
jours → short ; dans ses a % les plus bas → long ; tenu Hmin jours au moins, tant que le signal dure.

| | Trades | Net moyen | Somme | Gagnants | Témoin de hasard | p |
|---|---|---|---|---|---|---|
| Réglage, a = 10 %, Hmin = 1 j | 292 | −0,41 % | −119 % | | | |
| Réglage, a = 10 %, Hmin = 3 j | 245 | +0,03 % | +7 % | | | |
| Réglage, a = 2,5 %, Hmin = 1 j | 134 | −0,76 % | −101 % | | | |
| **Réglage, a = 2,5 %, Hmin = 3 j (choisi)** | 112 | **+0,68 %** (± 0,92) | +76 % | 50 % | | |
| **Jugement 2026, 4 paires** | 55 | **+1,08 %** (± 1,03) | +59 % | 49 % | −0,10 ± 1,18 % | **0,145** |
| **Jugement 2026, 8 paires neuves** | 102 | **−0,07 %** (± 0,77) | −7 % | 42 % | −0,14 ± 0,77 % | **0,48** |
| Info : paires neuves sur la période de réglage | 256 | +0,58 % (± 0,50) | +150 % | 48 % | | |

Par pièce en 2026 : SOL +1,04 % (13) · LINK +1,37 % (12) · ADA +1,75 % (13) · DOT +0,39 % (17) ‖ ATOM −0,56 % (7) · AVAX −0,76 % (13) ·
BCH +3,81 % (14) · BNB −1,64 % (15) · XRP −1,23 % (15) · LTC −0,16 % (14) · DOGE −2,39 % (10) · BTC +1,60 % (14).
Lecture : positif sur les 4 paires (+1,08 % par trade) mais à une erreur type de zéro et dans la fourchette du hasard
(p 0,145) ; nul sur les paires neuves. Les deux réglages à 1 jour perdent, les deux à 3 jours gagnent un peu : pas de signal
net, trop peu de trades (55) pour trancher. **Ni démontré, ni enterré.**

## Contrôles de bon sens (avant le lancement, tous passés — `controle.log`)
| Contrôle | Attendu | Obtenu |
|---|---|---|
| P2, vrai BTC + altcoins fabriqués (marche au hasard), 12 réglages | −0,14 % | écart max 1,7 erreur type ; p du témoin 0,52 |
| P2, prix plats | −0,14 % exactement | exact (7 021 trades) |
| P2, retard d'une minute planté | trouvé | +0,29 % net, p 0,003 |
| P1, vraie dette + faux prix | −0,14 % | −0,141 % ± 0,052 (3 197 trades) ; p 0,56 |
| P3, vrais ratios + faux prix | −0,14 % | −0,08 % ± 0,11 (2 000 trades) ; p 0,37 |
| P3, prix plats | −0,14 % exactement | exact (105 trades) |
| P3, dérive plantée dans le sens du signal | trouvée | +1,57 % net, p 0,003 |

## Amendement
Un seul, technique, daté, **avant** le calcul : le chargeur plantait sur une case vide écrite `""` (voir la fiche). Aucune
règle, aucun seuil, aucun critère changé. Le lancement officiel a tourné une seule fois.

## Ce qui reste incertain
- Piste 1 : l'écart sur les paires neuves en 2026 est réel dans les données, mais je ne sais pas s'il est durable ; le p de
  0,001 du témoin est sans doute trop flatteur (les trades de plusieurs pièces tombent les mêmes jours ; l'erreur type simple
  donne ≈ 2 écarts). Seul un test **papier en avant**, pré-enregistré, trancherait.
- Quelques créneaux « positions ouvertes = 0 » dans les fichiers Binance (signalés avant calcul, non corrigés) : effet jugé
  négligeable, non mesuré.
- Glissement fixe à 0,02 % : pendant les secousses il est sûrement plus grand, ce qui aggrave les pistes 1 et 2.
- Financement ignoré : il peut bouger la piste 3 (positions de plusieurs jours) de quelques centièmes de % par jour, dans un
  sens que je n'ai pas mesuré.
- Prix Binance, 12 grosses pièces vivantes, 9 mois de jugement. Rien n'a été vérifié sur Kraken.
- Mes croyances écrites avant : piste 2 « retard en brut mais sous les frais » → **faux**, le brut est négatif en 2026 ;
  piste 1 « volatilité plutôt que direction » → vrai seulement sur les paires neuves ; piste 3 « proche de zéro » → cohérent.

## Ce que ça montre
- Trois familles nouvelles (dette, retard à la minute, positionnement de la foule) : **aucune ne donne un avantage démontré**
  après 0,14 % de coût. Compteur du registre : 99 lignes, toujours un seul effet solide côté trading (les nouvelles cotations).
- La seule chose à garder : la piste 1 sur un panier large, **en papier en avant seulement**. Rien à changer sur Martin.

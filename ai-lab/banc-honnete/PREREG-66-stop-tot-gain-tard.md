# Pré-enregistrement 66 : stopper plus tôt et prendre plus tard
Écrit et commité le 03/11/2026 au soir, avant tout calcul de cette grille. Idée de Tony : « stopper plus tôt et prendre plus tard ». Suite de PREREG-62 (gain ≈ 0,9 %, perte ≈ 9 %, point mort ≈ 91 %).

Prédiction écrite d'avance : sur une marche aléatoire, atteindre +g avant −s arrive s / (s + g) du temps. Le rapport gain/perte s'améliore donc, mais le taux de gagnants chute d'autant (bien sous 90 %), et un stop plus serré multiplie les trades, donc les frais. PREREG-28 (autres réglages) a déjà trouvé ≈ 50 % de gagnants et une espérance négative avec SL 1 %. Je m'attends à un échec ; le test reste loyal.

## Règle
Moteur de PREREG-62 : toujours en position, inversion après une perte, 1 min, frais 0,05 % par côté, sans levier ni martingale, sans financement.
Grille rapportée entièrement : SL s ∈ {1, 2, 3, 5} %, activation a ∈ {2, 3, 5, 10} %, trailing t ∈ {1, 2, 3} % avec t < a (écrit « 46 réglages » avant calcul par erreur de compte : il y en a 36, grille inchangée).

## Choix et jugement
Choix : meilleure espérance moyenne sur BTC, ETH, SOL, 01/02/2024 → 31/12/2025. Jugement : XRP, DOGE, ADA, LINK, AVAX, LTC, BNB, DOT, BCH, ATOM, sur P1 = 01/02/2024 → 31/12/2025 et P2 = 01/01 → 30/09/2026. Portefeuille = 10 parts égales.

## Verdict
- **« TIENT »** si sur P1 ET P2 : espérance moyenne > 0, plus de 5 pièces sur 10 positives, portefeuille > 0, espérance supérieure au sens tiré au hasard dans ≥ 95 % de 200 tirages. Le taux de gagnants n'est pas un critère ; il est rapporté.
- **« MIEUX SANS SUFFIRE »** si l'espérance dépasse celle de la règle à 90 % (−0,056 % sur P1, +0,079 % sur P2) sur les deux périodes, sans le reste.
- **« NON »** sinon.

## Résultat (03/11/2026, 21h3x — t66.py, t66_P1.json, t66_P2.json). Figé : SL 5 %, activation +10 %, trailing 1 %
| 10 pièces | Gagnants | Espérance | Portefeuille | Composé médian | Positives | Baisse médiane | Trades/pièce | Témoin hasard / battu |
|---|---|---|---|---|---|---|---|---|
| P1 | 35,9 % | +0,366 % | +105,0 % | +32,9 % | 6/10 | −73,6 % | 320 | +0,077 % / 98,5 % |
| P2 | 37,2 % | +0,458 % | +23,1 % | −3,4 % | 4/10 | −47,9 % | 70 | +0,057 % / 88,5 % |

**VERDICT (pré-enregistré) : « MIEUX SANS SUFFIRE ».** L'espérance dépasse celle de la règle à 90 % sur les deux périodes ; sur P2, 4 pièces positives au lieu de plus de 5 et témoin battu à 88,5 % au lieu de 95 %.

Prédiction d'avance : juste sur les gagnants (36-37 %), **fausse sur l'espérance**. Tony avait raison sur le sens. Le témoin au hasard est lui aussi positif : la queue droite (les grands mouvements crypto) semble payer le gain lointain, quel que soit le sens.

Limites : financement non compté, plus lourd ici car les trades durent plus longtemps (~4 jours en P2) ; 100 % du capital par pièce, d'où les baisses ; toute la période a été vue sur ces pièces par PREREG-62 pour d'autres réglages. Grille sur 10 pièces : 22/36 réglages positifs en P1, 10/36 en P2.

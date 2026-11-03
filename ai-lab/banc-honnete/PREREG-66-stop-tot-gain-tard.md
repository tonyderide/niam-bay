# Pré-enregistrement 66 : stopper plus tôt et prendre plus tard
Écrit et commité le 03/11/2026 au soir, avant tout calcul de cette grille. Idée de Tony : « stopper plus tôt et prendre plus tard ». Suite de PREREG-62 (gain ≈ 0,9 %, perte ≈ 9 %, point mort ≈ 91 %).

Prédiction écrite d'avance : sur une marche aléatoire, atteindre +g avant −s arrive s / (s + g) du temps. Le rapport gain/perte s'améliore donc, mais le taux de gagnants chute d'autant (bien sous 90 %), et un stop plus serré multiplie les trades, donc les frais. PREREG-28 (autres réglages) a déjà trouvé ≈ 50 % de gagnants et une espérance négative avec SL 1 %. Je m'attends à un échec ; le test reste loyal.

## Règle
Moteur de PREREG-62 : toujours en position, inversion après une perte, 1 min, frais 0,05 % par côté, sans levier ni martingale, sans financement.
Grille rapportée entièrement : SL s ∈ {1, 2, 3, 5} %, activation a ∈ {2, 3, 5, 10} %, trailing t ∈ {1, 2, 3} % avec t < a (46 réglages).

## Choix et jugement
Choix : meilleure espérance moyenne sur BTC, ETH, SOL, 01/02/2024 → 31/12/2025. Jugement : XRP, DOGE, ADA, LINK, AVAX, LTC, BNB, DOT, BCH, ATOM, sur P1 = 01/02/2024 → 31/12/2025 et P2 = 01/01 → 30/09/2026. Portefeuille = 10 parts égales.

## Verdict
- **« TIENT »** si sur P1 ET P2 : espérance moyenne > 0, plus de 5 pièces sur 10 positives, portefeuille > 0, espérance supérieure au sens tiré au hasard dans ≥ 95 % de 200 tirages. Le taux de gagnants n'est pas un critère ; il est rapporté.
- **« MIEUX SANS SUFFIRE »** si l'espérance dépasse celle de la règle à 90 % (−0,056 % sur P1, +0,079 % sur P2) sur les deux périodes, sans le reste.
- **« NON »** sinon.

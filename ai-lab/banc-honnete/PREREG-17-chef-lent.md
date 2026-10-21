# Pré-enregistrement 17 : le chef d'orchestre sur des stratégies lentes (+ re-vérification du 16)
Écrit et commité le 22/10/2026 à 00h55, avant tout calcul.

## Correction de méthode (découverte en écrivant ce protocole)
Dans t19 (PREREG-16), le score de forme comptait les trades à leur date d'ENTRÉE : un trade entré avant la décision mais sorti après est un regard vers le futur (faible pour des trades ≤ 24 h, énorme pour des trades de plusieurs semaines). Désormais : **le score du lundi ne compte que les trades déjà SORTIS avant ce lundi** ; le gain d'une semaine jouée = les trades ENTRÉS cette semaine-là (qu'ils sortent quand ils veulent).
Je refais donc d'abord PREREG-16 à l'identique avec cette correction (univers A = les 120 rapides). Son verdict remplace celui de t19.

## Univers B (lent)
Bougies 4 h et 1 j ; marchés BTC, ETH, SOL, XRP, ADA, LINK. 5 signaux : croisement EMA 20/50 (sens du croisement) ; cassure Donchian 20 (plus haut/plus bas des 20 bougies) ; RSI(14) < 30 long / > 70 short ; clôture hors Bollinger(20, 2) → retour ; croisement MACD(12, 26, 9). 3 sorties TP/SL : 5/2,5 ; 8/4 ; 12/6 %, 30 bougies max. Exécution identique (ouverture suivante, gaps, pire cas, taker 0,05 %/côté, mise fixe). Total 2 × 6 × 5 × 3 = **180 stratégies**.

## Chef
Comme PREREG-16 : L ∈ {1, 2, 4, 8} semaines × K ∈ {1, 5, 10}, plus un seuil de forme s ∈ {0 ; +2 %} (ne jouer que les stratégies au score > s) → 24 réglages. Choix sur 2024-2025, jugement unique sur 2026.
Témoins 2026 : (a) les 180 à poids égal ; (b) 1 000 chefs au hasard (mêmes nombres de stratégies jouées chaque semaine).
## Verdict (univers B)
GAGNE seulement si : gain 2026 > 0 ET > (a) ET rang ≥ 99e centile de (b). Info : persistance semaine → semaine (score par date de sortie).

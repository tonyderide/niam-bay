# Pré-enregistrement 15 : confirmation du candidat SOL 1 h (croisement EMA 9/21, TP 2 % / SL 1 %)
Écrit et commité le 22/10/2026 à 00h42, AVANT tout calcul. Demandé par la revue du scalpeur (22/10). La règle est figée : exactement celle de t17.py (entrée à l'ouverture suivante, gaps, pire cas, taker 0,05 %/côté, 24 bougies max, mise fixe, sans levier).

## Test A — marchés jamais vus (le juge principal)
La même règle, sans changement, en 1 h sur les 18 autres paires de banc.py (XRP DOGE ADA LINK AVAX DOT LTC BCH UNI ATOM NEAR FIL AAVE APT OP TRX XLM ETC), du 01/01/2024 au 17/10/2026. Somme des gains nets sur les 18, comparée à 500 tirages de jumeaux (mêmes sorties, mêmes nombres de longs/shorts par paire, instants au hasard).
**Réussite** : somme > 0 ET > 95e centile des jumeaux ET ≥ 10 paires sur 18 positives.

## Test B — voisinage (doit être un plateau, pas un pic)
SOL 1 h, 2026 : TP/SL ∈ {1,5/0,75 ; 2,5/1,25 ; 2/1,5} et EMA ∈ {8/21 ; 10/20}. **Réussite** : au moins 4 des 5 voisins positifs en 2026.

## Test C — glissement
Le candidat sur SOL 1 h 2026 avec +5 pb de glissement par côté (en plus des frais). **Réussite** : gain net > 0.

## Verdict
CONFIRMÉ (→ test papier en direct sur SOL 1 h jusqu'à ≥ 60 trades, critère : net > 0 et > p95 des jumeaux de la même période) seulement si A ET B ET C réussissent. Sinon : chance / régime 2026, candidat abandonné.

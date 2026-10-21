# Pré-enregistrement 19 : le scalp avec ordres LIMITES (frais maker) — la leçon des frais
Écrit et commité le 22/10/2026 à 01h29, avant tout calcul.

## Pourquoi
Banc 14-18 : l'ennemi n°1 est le coût par trade (taker 0,05 %/côté). Un vrai scalpeur pose des ordres limites. Question : avec entrée et objectif en limite (maker 0,02 %), le scalp honnête passe-t-il ?

## Exécution (prudente)
- Signal à la clôture de la bougie i (mêmes 4 signaux que PREREG-14). Ordre LIMITE d'entrée au prix de clôture de i, valable UNE bougie : exécuté seulement si la bougie i+1 le TRAVERSE (long : bas < prix × (1 − 0,0001) ; short : haut > prix × (1 + 0,0001)), sinon annulé (pas de trade).
- Objectif en LIMITE, maker : exécuté seulement si une bougie postérieure à l'entrée le TRAVERSE de 0,01 %.
- Stop au marché, taker 0,05 % + glissement 5 pb ; gap → sortie à l'ouverture ; bougie ambiguë (stop et objectif) → stop ; la bougie d'entrée ne peut pas toucher l'objectif (on ne sait pas si l'entrée était avant), mais peut toucher le stop.
- Sortie au temps (24 bougies) : au marché, taker + 5 pb.
- Frais : entrée maker 0,02 %, objectif maker 0,02 %, stop/temps taker 0,05 % + 5 pb.

## Grille et sélection
Mêmes 120 stratégies que PREREG-14 (BTC ETH SOL × 15 min / 1 h × 4 signaux × 5 TP/SL). Sélection : meilleure de 2024-2025 (≥ 30 trades).

## Jugements (les deux doivent réussir)
J1 — 2026 sur son marché : gain > 0 ET rang ≥ 99e centile de 500 jumeaux (mêmes sorties et frais, MÊME NOMBRE de trades longs/courts, instants d'entrée au hasard parmi les bougies où un ordre limite aurait été traversé).
J2 — la même règle (même signal, TP/SL, unité) sur les 18 cryptos jamais vues, 01/2024 → 10/2026 : somme > 0 ET > 95e centile des jumeaux ET ≥ 10/18 paires positives.
GAGNE seulement si J1 ET J2. Info : nombre des 120 positives en 2026 avec ordres limites vs taker (PREREG-14 : 8/120).

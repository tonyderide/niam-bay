# Pré-enregistrement 21 : l'alignement de plusieurs unités de temps
Figé et commité le 22/10/2026 à 02h01, APRÈS relecture d'équité par le scalpeur (corrections intégrées) et AVANT tout calcul.
Idée de Tony (22/10) : « pourquoi pas 3 min, pour la corrélation entre diverses unités de temps ». Technique connue : n'entrer sur une petite unité que dans le sens des grandes.

## Données
BTC, ETH, SOL : bougies 1 min Kraken du 01/01/2024 au 17/10/2026, agrégées en 3 min, 5 min, 15 min et 1 h (agrégation exacte, alignée sur l'heure UTC).
**Règle anti-futur** : à la bougie t de la petite unité, une grande unité n'utilise que ses bougies DÉJÀ CLOSES à t (ex. à 10:25, l'EMA 1 h s'arrête à la bougie 09:00-10:00).

## Stratégies (tout est compté)
- Petite unité d'entrée : 3 min ou 5 min.
- Tendance d'une unité = EMA 20 au-dessus (haussière) ou en dessous (baissière) de l'EMA 50 de cette unité.
- Filtre : (F0) aucun — témoin interne ; (F1) 1 h seul ; (F2) 1 h ET 15 min d'accord.
- Signal d'entrée sur la petite unité, uniquement dans le sens du filtre (F0 : dans les deux sens) : (S1) croisement EMA 9/21 dans le sens de la tendance ; (S2) repli : RSI(2) < 10 en tendance haussière → long, > 90 en baissière → short.
- Sorties TP/SL fixes : 0,5/0,25 ; 1/0,5 ; 1,5/0,75 ; 0,5/0,5 ; 0,5/1 % (les deux dernières pour les replis, qui se jouent objectif ≤ stop), 48 bougies max de la petite unité.
- **Chaque trade est déroulé sur les bougies de 1 min** (signal calculé en 3 ou 5 min) ; on publie, par sortie, le taux de bougies 1 min ambiguës (stop et objectif touchés) et on signale toute sortie où il dépasse 5 % des trades.
- Exécution identique à t17_lib : entrée à l'ouverture suivante, gaps, pire cas (stop avant objectif), taker 0,05 %/côté + 2 pb de glissement à l'entrée ET à la sortie, + 3 pb de plus sur les sorties au stop (toutes variantes) ; sur les marchés de J2 à carnet mince (ARB, INJ, FET, GRT, ALGO) : 5 pb par côté au lieu de 2, mise fixe, un trade à la fois par stratégie.
Total : 3 marchés × 2 unités × 3 filtres × 2 signaux × 5 sorties = **180 stratégies**.

## Sélection et jugements
Sélection : meilleure de 2024-2025 parmi celles AVEC filtre (F1/F2), ≥ 30 trades.
J1 — 2026 sur son marché : gain > 0 ET rang ≥ 99e centile de 500 jumeaux (mêmes sorties et coûts, MÊME nombre de trades longs et courts, instants au hasard pris sur TOUTES les bougies) ET la version filtrée fait mieux en 2026 que le même signal + même sortie SANS filtre (F0). [Info : jumeaux tirés seulement là où le filtre autorise le sens.]
J2 — la même règle sur 6 marchés jamais vus (ARB, BNB, INJ, FET, GRT, ALGO ; 1 min vérifiée depuis 01/2024), 01/2024 → 10/2026 : somme > 0 ET > 95e centile des jumeaux (tirés sur toutes les bougies) ET ≥ 4/6 positifs.
GAGNE seulement si J1 ET J2. Sinon « non démontré ».
Info (sans verdict) : pour chaque couple marché × unité × signal × sortie, F1/F2 contre F0 en 2026 (le filtre améliore-t-il le même signal ?), et le nombre de trades (le filtre réduit-il les frais ?).

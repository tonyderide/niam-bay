# Pré-enregistrement 16 : le chef d'orchestre (savoir quand une stratégie est « en forme »)
Écrit et commité le 22/10/2026 à 00h52, avant tout calcul. Idée de Tony (22/10) : « la machine n'oublie pas, elle devrait retrouver quand s'arrêter et quand continuer ».

## Univers
Les 120 stratégies de PREREG-14 (t17_lib.py : 4 signaux × 5 couples TP/SL × BTC ETH SOL × 15 min / 1 h ; exécution honnête : ouverture suivante, gaps, pire cas, taker 0,05 %/côté, mise fixe). Pour chacune, la liste de ses trades (date d'entrée, rendement net).

## Règle
Chaque lundi 00:00 UTC : score de chaque stratégie = somme de ses rendements sur les L dernières semaines. On joue la semaine suivante, à poids égal (1/K chacune), les K meilleures au score > 0 (si moins de K sont > 0, on joue celles-là ; si aucune, on ne joue pas).
Réglages essayés : L ∈ {1, 2, 4, 8} semaines × K ∈ {1, 5, 10} = 12 chefs. Choix du meilleur sur 2024-2025 (gain net), puis JUGEMENT UNIQUE sur 2026 (1/1 → 17/10).

## Témoins (2026)
(a) les 120 stratégies à poids égal tout le temps ; (b) 1 000 chefs au hasard : chaque semaine, mêmes nombres de stratégies jouées que le vrai chef, mais choisies au hasard parmi les 120.

## Verdict
GAGNE seulement si, sur 2026 : gain net > 0 ET > témoin (a) ET rang ≥ 99e centile des chefs au hasard (seuil relevé : 2026 a déjà jugé ~15 familles, revue du quant du 22/10). Sinon ÉCHEC.
Info : corrélation de rang semaine → semaine suivante des 120 stratégies (persistance de la forme), sur 2024-25 et 2026.

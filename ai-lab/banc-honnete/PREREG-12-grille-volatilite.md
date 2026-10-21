# Pré-enregistrement 12 : une grille (façon Martin) allumée seulement quand la volatilité prévue est haute
Écrit et commité le 22/10/2026 ~00h10, avant tout calcul de grille.

## Idée
La volatilité se prévoit (corr +0,34 en 1 h sur 2026, voir volatilite-vs-direction.md), la direction non. Une grille gagne sur les allers-retours, sans parier sur le sens. Question : l'allumer seulement quand l'agitation prévue est haute bat-il (a) la grille toujours allumée et (b) la même grille allumée à des moments décalés au hasard ?

## Données
PF_XBTUSD, bougies 15 min Kraken (cache du banc, 2023-11 → 2026-10-17). Réglage sur 2024-2025, jugement unique sur 2026 (1/1 → 17/10).

## Grille (fixée, pas réglée)
Écart 0,6 % (celui de Martin), 5 niveaux de chaque côté, centrée au prix d'allumage. Niveaux sous le centre : achat, puis revente au niveau du dessus ; au-dessus : vente à découvert, puis rachat au niveau du dessous. Chaque niveau = 1/10 du capital. Frais maker 0,02 % par ordre exécuté.
Exécution prudente : un niveau est exécuté si la bougie le touche (bas ≤ achat, haut ≥ vente), au plus une fois par bougie ; l'ordre inverse n'est posé qu'à la bougie suivante.
Fermeture de tout l'inventaire au prix de clôture, frais taker 0,05 %, quand la grille s'éteint ou quand le prix sort de la grille (au-delà du 5e niveau).

## Interrupteur
Prévision v = moyenne exponentielle des |rendements| 15 min (λ = 0,94, connue avant la bougie). Grille allumée quand v est dans les q % les plus hauts de la période de réglage (seuil figé). q ∈ {20 %, 40 %, 60 %} choisi sur 2024-2025 (meilleur gain net), puis figé.

## Témoins (2026)
(a) grille toujours allumée ; (b) 500 décalages circulaires au hasard du même masque allumé/éteint (même temps d'activité, mêmes durées, autres moments).

## Verdict
GAGNE seulement si, sur 2026 : gain net > 0 ET > grille toujours allumée ET rang > p95 des 500 décalages. Sinon ÉCHEC. Rien d'ajouté après coup.

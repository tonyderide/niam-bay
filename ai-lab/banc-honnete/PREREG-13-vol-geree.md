# Pré-enregistrement 13 : BTC « géré par la volatilité » (Moreira & Muir, 2017)
Écrit et commité le 22/10/2026 vers 00h05, avant tout calcul.

## Idée
On garde du BTC en permanence, mais la taille de la position suit w = cible / volatilité prévue (plafonnée à 1, donc jamais de levier). Quand l'agitation prévue monte, on réduit ; quand elle baisse, on remonte.

## Données
PF_XBTUSD, bougies 1 h (cache du banc). Volatilité prévue : moyenne exponentielle des |rendements| horaires (λ = 0,94), connue avant l'heure. Rééquilibrage une fois par jour (00h UTC), frais taker 0,05 % sur la part échangée.
Cible : la médiane de la volatilité prévue sur 2024-2025 (figée), soit environ la moitié du temps à 100 %.

## Comparaisons, sur 2026 uniquement
(a) garder-acheter (100 % tout le temps) ; (b) 500 témoins : les MÊMES poids journaliers, mélangés au hasard dans le temps (même exposition moyenne, mêmes frais à peu près, mais sans lien avec la volatilité).

## Mesure et verdict
Ratio rendement / risque (Sharpe annualisé, sans taux sans risque) et pire perte (max drawdown).
GAGNE seulement si : Sharpe géré > Sharpe garder-acheter ET Sharpe géré > p95 des 500 témoins mélangés. La pire perte est affichée, pas jugée.
Ce n'est PAS un test de « gagner plus d'argent » : c'est « gagner autant avec moins de casse ». Je le dirai tel quel.

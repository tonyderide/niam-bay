# Bilan du labo en continu — 31/10/2026 18h → 02/11/2026 20h
Demande de Tony (31/10) : « continue en arrière-plan de chercher la meilleure stratégie ». Méthode : file d'hypothèses à raison économique (FILE-HYPOTHESES.md), chaque test pré-enregistré et commité avant calcul, jugement unique, témoin au hasard. 25 pré-enregistrements (PREREG-35 à 59) : 21 jugés, 4 en avant (35, 45, 47, 50).

## Ce qui a été jugé (21)
| Famille | Tests | Verdict |
|---|---|---|
| Primes structurelles connues | 36 basis trimestriel, 37 prime de variance, 40 écart de financement entre plateformes, 42 carry à rotation lente | toutes **arbitrées en 2025-2026** (NON DÉMONTRÉ / PERD) : la prime existe en médiane mais passe sous les frais ou le taux sans risque |
| Gestion du risque d'une prime | 38 vol gérée sur le carry, 43 levier de la foule | PERD / NON ÉVALUABLE |
| Momentum, renversement, facteurs | 39 momentum par pièce, 41 momentum entre pièces, 44 taille, 48 bêta, 49 MAX, 51 tournant du mois, 52 BTC mène, 55 achat après krach | rien de démontré ; le meilleur, l'effet MAX (49), est passé en test en avant |
| **Jetons neufs** | 46 GAGNE, répliqué 53 (comptant 2018-26), 54 (OKX), 56 (Hyperliquid, morts compris) ; 59 persiste après 90 j | **le seul effet solide** : sur 4 populations, une nouvelle cotation fait nettement moins bien qu'une pièce ancienne sur ses 90 premiers jours |
| Exploiter les jetons neufs | 57 (poids rééquilibrés chaque jour), 58 (shorts tenus) | **RISQUE NON MAÎTRISÉ** : tenu, +25 %/an mais Sharpe 0,48, baisse 34 %, 21 % des trades liquidés, 2025 et 2026 perdants |

## En avant (le seul juge que la période ne trompe pas)
| Test | Cron | Jugement unique |
|---|---|---|
| PREREG-35 inversion journalière (10 pièces) | 03h17 | 01/05/2027 |
| PREREG-45 réversion à 1 jour (50 pièces) | 03h27 | 03/05/2027 |
| PREREG-47 short des nouvelles cotations crypto | 03h37 | 01/06/2027 |
| PREREG-50 effet MAX (150 pièces) | 03h47 | 03/05/2027 |

## Ce que j'en retiens
1. **Les primes « connues » ne paient plus** : basis, variance, écarts de financement ont été arbitrés ; en 2026 ils rapportent moins que des bons du Trésor après frais.
2. **Les signaux de prix (momentum, renversement, facteurs) changent avec le régime** : le meilleur de 2024-25 est souvent le pire de 2026.
3. **La seule asymétrie robuste vient de l'offre** : jetons neufs à faible flottant et déblocages à venir. Mais vendre à découvert ces jetons expose à des envolées : un trade sur cinq perd toute sa mise, et les deux dernières années sont perdantes. **Ce n'est pas une stratégie à risque maîtrisé.**
4. Erreurs de méthode trouvées et corrigées en route : témoin quotidien injuste pour une règle à faible rotation (40), contamination par des contrats sur actions (46), fausses nouveautés USDT (53), panier « ancien » vide avant 09/2021 (57/58), plancher appliqué à la sortie au lieu d'une liquidation en cours de route (46 → 58). Toutes notées dans les fichiers.
5. Rien à brancher sur Martin. Aucun ordre, aucun compte, aucune clé ; tout est local.

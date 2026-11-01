# Pré-enregistrement 41 : le momentum transversal hebdomadaire, sur ~240 pièces morts compris
Écrit le 01/11/2026 vers 01h35 CET, avant tout calcul. Hypothèse H6 de FILE-HYPOTHESES.md. `scripts/cherche -v momentum transversal quintiles classement forts faibles semaine` : voisin direct **PREREG-10** (même idée sur 21 pièces Kraken, 5 contre 5 : PERD, −25,8 % en 2026). Ici l'univers est ~10× plus grand (puissance), morts compris, en quintiles, sens momentum seulement (pas de grille sur le sens).

## Raison économique, et ce que dit la théorie avant les données
Facteur « momentum » de Liu, Tsyvinski & Wu (2022, *Journal of Finance*) : sur les cryptos, les gagnantes des 1-4 dernières semaines continuent de surperformer les perdantes la semaine suivante (sous-réaction, attention limitée des investisseurs). Neutre au marché (long-short), donc indépendant de la direction du marché. Prior abaissé par PREREG-10 et PREREG-39 (le momentum hebdo par pièce s'est inversé en 2026) : **plutôt PERD**.

## Données (déjà là)
Exactement celles de PREREG-39 (t39.py) : 253 perpétuels USDT-M Binance cotés au 01/01/2024, morts compris, coupure `couper`, jours UTC puis semaines du lundi (ouverture → ouverture du lundi suivant ; dernier prix si retrait).

## Règle
- Chaque lundi : pièces vivantes ayant L semaines d'historique ; classement par rendement des L semaines passées.
- **Long le quintile du haut, short le quintile du bas**, poids égaux, ½ de capital par côté, tenu une semaine.
- Rendement de la semaine = ½ × moyenne(longs) − ½ × moyenne(shorts) − 0,05 % × somme des |variations de poids| (taker ; poids d'une pièce = ±0,5 / nombre de pièces du côté). Sans funding (convention PREREG-28 à 39).
- Grille : **L ∈ {1, 2, 3, 4} semaines**.

## Choix et jugement
- Choix de L sur les semaines commençant du 01/01/2024 au 29/12/2025 (meilleur net).
- **JUGEMENT UNIQUE : semaines commençant du 05/01/2026 au 21/09/2026.**
- **Témoin à rotation égale** (leçon de PREREG-40) : paniers au hasard, mêmes tailles de côtés chaque semaine ; chaque pièce du panier précédent encore éligible est gardée avec la probabilité égale au taux de conservation de la règle sur la période (part des noms d'un côté gardés d'une semaine à l'autre), le reste tiré au hasard parmi les éligibles. Mêmes frais. 1 000 tirages, graine 41. p = part ≥ la règle.
- **GAGNE** si net > 0 en 2024-25 **ET** > 0 en 2026 **ET** p < 0,05 en 2026. **NON DÉMONTRÉ** si net 2026 > 0 sans le reste. **PERD** sinon.

## Rapporté
Les 4 L sur les deux périodes, brut/frais, semaines positives, pire semaine, pire baisse, taux de conservation, taille des quintiles ; jambe longue et jambe courte séparément.

## Relecture d'équité, avant calcul
- Choix de L favorable à la règle sur 2024-25, corrigé par le jugement 2026 unique.
- Le témoin a la même rotation, donc les mêmes frais en moyenne : il ne retire que l'information du classement.
- Aucune action sur Martin ni Kraken.

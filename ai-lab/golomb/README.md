# Règles de Golomb : la même méthode, sur une 2e étagère (16 oct 2026, 05h20)
| marques | hasard (8 s) | Erdős–Turán | optimum |
|---|---|---|---|
| 5-8 | **11, 17, 25, 34** | 41-159 | 11, 17, 25, 34 |
| 9-10 | 45, **55** | 185, 202 | 44, 55 |
| 11-13 | 75, 95, 120 | 221-313 | 72, 85, 106 |
**Ici, c'est l'inverse de la cap set** : le hasard glouton retrouve les optimums jusqu'à 8 marques, et 10 aussi. La construction algébrique d'Erdős–Turán est **3 à 5 fois pire**. C'est normal : elle vise le comportement asymptotique (en 2pk), pas les petites tailles. On ne peut donc pas en tirer la règle « la structure bat toujours le calcul ». Il faut la **bonne** structure pour la bonne échelle, et seul le juge dit laquelle. Les meilleures règles connues viennent de constructions projectives (Singer, Bose) et de recherches exhaustives distribuées (distributed.net OGR).

## La bonne structure : la construction de Bose (GF(p²)), avec meilleure rotation et meilleur multiplicateur
| marques | hasard | Bose | optimum |
|---|---|---|---|
| 5 | 11 | **11** | 11 |
| 7 | 25 | 28 | 25 |
| 11 | 75 | **74** | 72 |
| 13 | 120 | **111** | 106 |
Le croisement est net. À petite taille, le hasard suffit. Plus la taille grandit, plus la structure projective l'emporte : à 13 marques, Bose fait 111 contre 120 pour le hasard, et l'optimum est à 106. Erdős–Turán, conçue pour l'asymptotique, restait loin derrière.
→ La même leçon que la cap set, en plus nuancée : **la structure gagne à grande échelle, si c'est la bonne**. Seul le juge permet de savoir laquelle.

## Polir Bose par recherche locale : aucun gain (74 et 111 restent)
Déplacer 1 ou 2 marques au hasard, en gardant la règle Golomb et sans l'allonger, ne raccourcit rien en 130 s. Les règles de Golomb sont très rigides : changer une marque modifie k−1 différences d'un coup, alors qu'à la cap set on ne touchait qu'un point. Les optimums (72, 106) ont été obtenus par **recherche exhaustive distribuée** (distributed.net), pas par de l'heuristique. Ce que je retiens : la recherche locale n'aide que si le voisinage est « doux ». Ici, il ne l'est pas.

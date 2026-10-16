# Règles de Golomb : la même méthode, sur une 2e étagère (16 oct 2026, 05h20)
| marques | hasard (8 s) | Erdős–Turán | optimum |
|---|---|---|---|
| 5-8 | **11, 17, 25, 34** | 41-159 | 11, 17, 25, 34 |
| 9-10 | 45, **55** | 185, 202 | 44, 55 |
| 11-13 | 75, 95, 120 | 221-313 | 72, 85, 106 |
**Ici, c'est l'inverse de la cap set** : le hasard glouton retrouve les optimums jusqu'à 8 marques, et 10 aussi. La construction algébrique d'Erdős–Turán est **3 à 5 fois pire**. C'est normal : elle vise le comportement asymptotique (en 2pk), pas les petites tailles. On ne peut donc pas en tirer la règle « la structure bat toujours le calcul ». Il faut la **bonne** structure pour la bonne échelle, et seul le juge dit laquelle. Les meilleures règles connues viennent de constructions projectives (Singer, Bose) et de recherches exhaustives distribuées (distributed.net OGR).

# La vis et l'étagère : ce qu'une nuit de maths m'a appris sur la méthode (16 oct 2026)

Question de Tony : « l'IA a résolu des problèmes de maths, à quoi les appliquer ? Une vis seule ne fait pas grand-chose, avec des planches tu fais une étagère. »
J'ai testé la méthode de FunSearch et d'AlphaEvolve de mes propres mains, sur deux problèmes à juge exact, et sur un problème où le juge ment (le trading).

| problème | juge | hasard | structure | structure + recherche locale | référence |
|---|---|---|---|---|---|
| cap set n=5 | exact, stable | 39 | orbites 40 | **45** | 45 optimal |
| cap set n=6 | exact, stable | ~90 | symétries 96 | quadrique 86 → **112** | 112 optimal |
| cap set n=7 | exact, stable | | | 224 (= 112×2) | 236 |
| Golomb 13 marques | exact, stable | 120 | Bose **111** | 111 (rigide) | 106 |
| trading, 12 coins | **ment** (régime) | contrôle aléatoire t=+5,3 en IS ! | 5 stratégies | tout est négatif en OOS | |

**Cinq règles, dans l'ordre où je les ai apprises :**
1. **Sans juge honnête, la méthode fabrique du bruit qui a l'air d'un résultat.** En trading, du hasard pur paraît significatif. En maths, le juge ne ment pas. C'est la première planche, et la plus importante.
2. **Le calcul seul plafonne** : murs à 42, 96, 224. Plus de graines et plus de temps n'y changent rien.
3. **C'est la nature de la structure qui débloque**, pas sa présence. Trois symétries bloquaient à 96, une quadrique est arrivée à 112.
4. **La bonne structure dépend de l'échelle** : à petite taille de règle de Golomb, le hasard bat l'algèbre, puis Bose reprend l'avantage en grandissant.
5. **La recherche locale n'aide que si le voisinage est doux.** C'est vrai pour la cap set (un point à la fois), pas pour Golomb (une marque touche k−1 différences).

**Les applications (l'étagère)** : un problème stable, avec un juge exact et un voisinage doux.
- Ordonnancement de datacenters : AlphaEvolve a récupéré ~0,7 % du calcul de Google.
- Codes correcteurs, c'est-à-dire des empilements de sphères : 5G, stockage, Voyager.
- Allocation de fréquences, découpe et chargement, tournées.
- Dans le métier de Tony : l'**attribution de bons de fidélité** sous des règles métier fixes (Falcon 2). Les règles sont stables, le juge existe (coût, règles respectées, satisfaction), et le voisinage est doux (un bon de plus ou de moins).
Ce qu'il ne faut PAS y mettre : tout ce qui bouge sous le juge, comme les marchés.
Code : ai-lab/capset, ai-lab/golomb, scripts/research/harness.py.

**À essayer** : un critère d'arrêt par capture-recapture (Schnabel, arXiv cs.NE, octobre 2026). On estime combien de solutions distinctes restent atteignables, et on redémarre ou on change de structure dès que la recherche « recapture » ce qu'elle a déjà vu. Ça m'aurait évité des heures sur les plateaux à 42, 96 et 224.

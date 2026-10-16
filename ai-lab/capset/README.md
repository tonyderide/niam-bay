# Mini-FunSearch NB : cap sets dans F_3^n (16 oct 2026, 04h → 05h)

L'idée de départ vient de Tony : « une vis seule ne fait pas grand-chose, avec des planches tu fais une étagère ». J'ai voulu voir de l'intérieur la méthode qui a permis à l'IA de résoudre des problèmes de maths : on propose des constructions, un juge exact les note, et on garde les meilleures.

**Problème.** Trouver le plus grand ensemble de points de F_3^n sans 3 points alignés, sachant que a, b, c sont alignés ⇔ a+b+c ≡ 0 mod 3. Le juge (`capset.judge`) re-vérifie toutes les paires depuis zéro.

| n | glouton trivial | glouton aléatoire | + grand voisinage (LNS) | + structure | meilleur connu |
|---|---|---|---|---|---|
| 3 | 8 | **9** | | | 9 (optimal) |
| 4 | 16 | **20** | | | 20 (optimal) |
| 5 | 32 | 39 | 42 (plateau) | orbites symétriques 40 → LNS **45** | 45 (optimal) |
| 6 | 64 | | 96 (mur, 8 graines) | symétries : 96, 96, 96 → **quadrique 86 → LNS 112** | 112 (optimal, Potechin 2008) |
| 7 | | | | quadrique → LNS **224** (= 112×2, mur) | 236 (max inconnu) |

**Ce que j'en retiens**
1. **Le calcul seul (la vis) plafonne vite.** Le glouton aléatoire suffit pour n ≤ 4. Au-delà, l'aléa local tombe sur des plateaux (42, puis 96) : 189 000 itérations ou 8 graines en parallèle n'y changent rien.
2. **Ce qui débloque, c'est la nature de la structure (la planche), pas la quantité de calcul.** À n=6, trois groupes de symétrie différents bloquent tous à 96. Une graine prise dans une **quadrique** {Q(x)=c} part plus bas (86) mais atteint 112. Sur une droite, Q est un polynôme de degré 2, donc une quadrique évite naturellement beaucoup d'alignements.
3. **L'assemblage, c'est l'étagère** : une structure de départ, puis la recherche locale, avec un juge exact du début à la fin.
4. **Les murs ont une forme lisible** : 224 = 112 × 2, c'est-à-dire un produit. Pour dépasser, il faut une idée qui ne soit pas un produit. Je ne l'ai pas.
5. **Pourquoi ça marche ici et pas en trading** : le juge est exact et le problème ne bouge pas. Sur le marché (voir scripts/research/harness.py), le même procédé fabrique des « records » qui ne sont que du bruit.

Fichiers : `capset.py` (juge + baselines), `search.py`, `lns.py`, `orbits.py`, `groups.py`, `quadric.py`, `par*.py`. Solutions : `best_n5.txt` (45), `best_n6_quadric.txt` (112), `best_n7.txt` (224).

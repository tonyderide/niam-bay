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

## Ce qui me manquait : la structure des records (lu après coup, Edel & Bierbrauer, *Large caps in small spaces*)
- **112 dans AG(6,3)** : 32 + 80 vecteurs de deux « types » R et D, par une **construction par doublement** proche du cap de Hill. Le cap de Hill de PG(5,3), 16 + 40 = 56 points, est l'union de sous-espaces de dimension 1 des types R et D. La preuve repose sur une propriété d'un design : si deux blocs partagent deux points, aucun troisième bloc n'est contenu dans leur union.
- **236 dans AG(7,3)** : le cap de **Calderbank-Fishburn**, construit à partir d'une famille de 12 vecteurs de poids 1 dans F_3^6, et non par un produit.
Ma quadrique aléatoire est tombée sur une structure de la même famille (algébrique), ce qui explique qu'elle ait donné 112. Pour 236, il faut une idée combinatoire de design, que je n'avais pas.
Sources : mathi.uni-heidelberg.de/~yves/Papers/smallCaps.pdf · arxiv.org/pdf/2601.16917 · math.tugraz.at (Elsholtz-Lipnik)

## 🐉 L'Ender Dragon : le cap de 236 points en dimension 7. ABANDONNÉ en connaissance de cause (16/10, 08h45 → 09h35)
J'ai compris la structure : 236 = {0}×C0 ∪ {1}×C1 ∪ {2}×U, où U regroupe les 12 vecteurs de poids 1. La condition qui rend l'ensemble valide : (C0 + C1) ∩ (−U) = ∅. Le juge l'a confirmé, la structure produit bien des caps valides.

| essai | idée | résultat |
|---|---|---|
| 1 | C1 = translaté de C0 (24 k matrices) | impossible : C+C couvre tout |
| 2 | C1 = −C0, ce qui exige C0 à distance ≥ 2 (609 k images) | aucune |
| 3 | cap à distance ≥ 2 cherché directement | 83 → cap n=7 = **178** ✓ valide |
| 4 | bonne condition croisée : C1 hors du voisinage de −C0 | **189** ✓ |
| 5 | LNS jointe en dimension 7, (2,U) fixé | 188 |
| 6 | hill-climbing sur C1 = A·C0 + b, en minimisant les conflits | 82 conflits au mieux (il en faudrait 0) |

J'ai aussi **démontré** que C1 = C0 est impossible : sinon C ∪ {u} serait un cap de 113 points, au-delà du maximum de 112.
**Pourquoi j'arrête** : le couple (C0, C1) qui marche vient d'une construction algébrique précise (les types R/D, liés au cap de Hill et à un design). Je n'ai pas cette construction, et le PDF qui la décrit est sur un serveur au certificat TLS invalide, que je ne contourne pas. La recherche aveugle dans GL(6,3), qui compte environ 3^36 éléments, ne la retrouve pas. Plus de calcul n'y changerait rien : c'est encore la règle n°2. Il faudrait l'idée, ou le texte. Le meilleur que j'ai construit moi-même en dimension 7 reste **224**, puis 189 avec cette structure.

## Penser au lieu de chercher (16/10, ~11h15, quand Tony m'a dit « fais ce que tu as envie »)
- **Reconstruit algébriquement** : la quadrique elliptique Q = x1x2 + x3x4 + x5² + x6² de PG(5,3) compte **112 points projectifs** (formule (q³+1)(q²−1)/(q−1) vérifiée). Elle se coupe en **deux caps de Hill de 56 points**, H et H' = E∖H. Et **±H est un cap affine de 112** dans AG(6,3), parce que a+b+c=0 avec des ±h veut dire h colinéaires dans PG(5,3). Cette fois je *sais pourquoi* c'est un cap, au lieu de l'avoir trouvé au hasard.
- **Le 236 n'est toujours pas atteint, mais je sais maintenant pourquoi** : avec C0, C1 ∈ {±H, ±H'} plus une translation, la somme C0 + C1 couvre **728 des 729 vecteurs**. Il reste au plus 1 vecteur libre, alors que le bloc de préfixe 2 en demande 12, même dans une base adaptée (le « poids 1 » dépend de la base). Les deux blocs du 236 ne sont donc pas deux copies symétriques ±H : ils doivent être de types différents (les types R/D d'Edel, 32 + 80).
- C'est une impossibilité trouvée et démontrée par le calcul exact, pas un échec flou. Le dragon reste vivant.
- **Remise en cause de ma source (11h15)** : sur 20 372 images affines de ±H, la somme C0 + C1 fait **toujours ≥ 728 vecteurs**. Pour loger 12 vecteurs au préfixe 2, il faudrait ≤ 717. Si tous les caps de 112 sont affinement équivalents (à vérifier), la structure « 112 + 112 + 12 » serait **impossible**. Or cette structure, je ne l'ai **jamais lue dans le papier** : elle vient d'un **résumé** fait par l'outil de recherche web, à partir d'extraits tronqués. J'ai construit 7 essais sur une description de seconde main que je n'ai pas vérifiée. C'est la leçon de la nuit appliquée à moi-même : mon « juge » de la structure n'était pas honnête. Ce qu'il faut : le texte original (Edel & Bierbrauer, ou Calderbank & Fishburn 1994), pas un résumé.
- **Recherche du texte original (11h30)** : le PDF d'Edel & Bierbrauer est sur un serveur dont le certificat TLS ne correspond pas, et le HTTP en clair est fermé. La version éditeur (DOI 10.1023/A:1011216716700, *Designs, Codes and Cryptography* 23(2), 2001) est probablement payante. Le dépôt de Michigan Tech ne fait que pointer vers le DOI. arXiv 2211.09772 (*Exponentially Larger Affine and Projective Caps*) ne décrit pas le 236. **Le dragon attend un texte primaire auquel je n'ai pas accès proprement.** Je ne contourne ni le certificat ni le paywall, je le note et je passe à autre chose.

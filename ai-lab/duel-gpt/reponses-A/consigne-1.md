## Réponse courte

Les quatre « rien » sont exacts : la règle de Golomb optimale à 15 marques mesure 151, c'est un résultat connu et prouvé. Mais votre programme ne le démontre pas. Il est faux dès qu'une distance atteint 128, donc sur toute la plage L = 128 à 151. Ses « rien » sont justes ici par chance. Il risque aussi de répondre « rien » à L = 151, alors qu'une règle existe.

## Le bug : décalage de 128 bits ou plus

L'ensemble des distances tient dans un `unsigned __int128`, qui a 128 bits, numérotés de 0 à 127. Or la distance `L - marks[0]` vaut L, soit 128 à 151 pour vous. L'expression `(u128)1 << x` avec x ≥ 128 est un **comportement indéfini** en C.

En pratique, avec gcc sur x86-64, le compilateur produit `shld`/`shl` puis un test du bit 6 du compteur. Le processeur ne garde que les 6 bits bas du compteur, si bien que le décalage se fait **modulo 128**. Résultat : la distance 128+j occupe le même bit que la distance j.

- **Distance 128** : elle tombe sur le bit 0. La distance 0 n'existe jamais, donc pas de dégât. L = 128 marche par accident.
- **Distance 129, 130, 131…** : elles tombent sur les bits 1, 2, 3… Toute règle qui contient à la fois la distance 1 et la distance 129 est rejetée à tort, comme si ces deux distances étaient égales.
- **Conséquence** : le programme coupe des branches valides. Il ne peut donc donner que de faux « rien », jamais une fausse règle.

Le juge `juge()` ne vérifie que les règles trouvées. Un « rien » n'est jamais contrôlé, c'est pourquoi rien ne signale l'erreur.

**Exemple minimal :** `./golomb 3 129 1` devrait afficher `0 1 129`, car les distances 1, 128 et 129 sont toutes différentes. Le programme rejette 129, qui tombe sur le bit 1 déjà pris par la distance 1, et répond `rien`. Je n'ai pas pu compiler ni exécuter le code ici, faites l'essai chez vous.

**Le cas qui compte :** l'optimum connu à 15 marques est, de mémoire, `0 4 20 30 57 59 62 76 100 111 123 136 144 145 151`. Il contient la distance 4 (0→4) et la distance 132 (4→136), qui partagent le même bit. La branche p = 4 rejettera donc cet optimum, et votre recherche à L = 151 risque de ne rien trouver.

## Points secondaires (pas des bugs de résultat)

- **`opt[14]` vaut 0** : il n'est jamais initialisé. Pour n = 15, cela affaiblit seulement l'élagage (`p < opt[14]`, `L - p < opt[14]`), sans fausser les résultats. La bonne valeur est 127.
- **Le commentaire d'en-tête est faux** : il annonce que les bornes viennent uniquement des valeurs trouvées par le programme. Or `main` recopie le tableau `OPT[]` publié. Les valeurs sont correctes, mais l'objectif « sans emprunter » n'est pas tenu.
- **Ce que j'ai vérifié et qui est correct** : les bornes `haut = L - opt[reste]` et `p >= opt[k+1]`, ainsi que la symétrie (1re distance < dernière, donc 2p < L).

## Correction : un ensemble de distances sur 256 bits

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#define MAXL 255
static int n, L, marks[32], opt[32];
static long long noeuds;
static uint64_t dist[MAXL / 64 + 1];                 /* bit d = distance d déjà utilisée */
#define TEST(x) ((dist[(x) >> 6] >> ((x) & 63)) & 1)
#define SET(x)  (dist[(x) >> 6] |=  (uint64_t)1 << ((x) & 63))
#define CLR(x)  (dist[(x) >> 6] &= ~((uint64_t)1 << ((x) & 63)))

/* les distances p - marks[i] sont distinctes entre elles : il suffit de tester contre dist */
static int  libre(int p, int k)   { for (int i = 0; i < k; i++) if (TEST(p - marks[i])) return 0; return 1; }
static void poser(int p, int k)   { for (int i = 0; i < k; i++) SET(p - marks[i]); }
static void retirer(int p, int k) { for (int i = 0; i < k; i++) CLR(p - marks[i]); }

static int rec(int k) {                      /* k marques posées (marks[0..k-1]) */
    noeuds++;
    int reste = n - k;                       /* marques à poser, L compris */
    if (reste == 1) {                        /* poser L */
        if (!libre(L, k)) return 0;
        if (k >= 2 && marks[1] - marks[0] >= L - marks[k - 1]) return 0;   /* symétrie */
        marks[k] = L; return 1;
    }
    int haut = L - opt[reste];               /* marks[k..n-1] : sous-règle de reste marques, longueur >= opt[reste] */
    for (int p = marks[k - 1] + 1; p <= haut; p++) {
        if (p < opt[k + 1]) continue;        /* marks[0..k] : règle de k+1 marques de longueur p */
        if (!libre(p, k)) continue;
        marks[k] = p; poser(p, k);
        if (rec(k + 1)) return 1;
        retirer(p, k);
    }
    return 0;
}

static int juge(int m) {                     /* toutes les distances distinctes ? */
    char vu[256] = {0};
    for (int i = 0; i < m; i++) for (int j = i + 1; j < m; j++) { int d = marks[j] - marks[i]; if (d <= 0 || d > 255 || vu[d]) return 0; vu[d] = 1; }
    return 1;
}

int main(int argc, char **argv) {            /* golomb_branche n L p : seulement les règles dont la 2e marque vaut p */
    if (argc != 4) { fprintf(stderr, "usage: %s n L p\n", argv[0]); return 2; }
    n = atoi(argv[1]); L = atoi(argv[2]); int p = atoi(argv[3]);
    if (n < 3 || n > 31 || L > MAXL) { fprintf(stderr, "n ou L hors limites (L <= %d)\n", MAXL); return 2; }
    int OPT[] = {0, 0, 1, 3, 6, 11, 17, 25, 34, 44, 55, 72, 85, 106, 127};   /* valeurs publiées */
    for (int i = 0; i <= 14; i++) opt[i] = OPT[i];
    if (2 * p >= L || p < opt[2] || L - p < opt[n - 1]) { printf("rien\n"); return 0; }
    marks[0] = 0; marks[1] = p; SET(p);
    if (rec(2)) {
        if (!juge(n)) { fprintf(stderr, "ERREUR : règle invalide\n"); return 1; }
        for (int i = 0; i < n; i++) printf(i ? " %d" : "%d", marks[i]); printf("\n");
    } else printf("rien\n");
    return 0;
}
```

Les changements :
- **Bits des distances** : le `u128` devient un tableau de 4 × 64 bits (distances jusqu'à 255), qu'on remplit en posant une marque et qu'on vide en revenant en arrière.
- **Garde-fous** : le programme refuse L > 255 au lieu de calculer n'importe quoi.
- **Bornes** : `opt[14] = 127` est ajouté. Pour rester « sans emprunt », calculez d'abord n = 14 et prenez votre propre résultat.
- **Juge** : un échec du juge est signalé comme une erreur, au lieu d'afficher « rien ».

## Tests pour avoir confiance

Les tests sur n ≤ 13 ne servent à rien ici : toutes les distances restent sous 128. Il faut tester avec L ≥ 128 :
- `./golomb 3 129 1` doit afficher `0 1 129` (l'ancienne version affiche `rien`).
- `./golomb 4 140 1` doit trouver une règle.
- `./golomb 15 151 4` doit retrouver l'optimum cité plus haut. Cette branche peut être longue à calculer.

Ensuite, relancez toutes les branches p de 1 à (L−1)/2 pour L = 128 à 150. Alors seulement, les « rien » de votre programme vaudront une preuve.

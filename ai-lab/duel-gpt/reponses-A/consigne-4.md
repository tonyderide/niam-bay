# Règle de Golomb optimale à 10 marques

**Règle :** `0, 1, 6, 10, 23, 26, 34, 41, 53, 55`

**Longueur : 55**

Je n'avais pas d'outil d'exécution dans cette session. Le programme ci-dessous n'a donc **pas été exécuté**. J'ai vérifié à la main que cette règle est valide. L'optimalité, elle, vient du résultat publié, que le programme permet de vérifier.

## Les 45 différences sont toutes distinctes (vérifié à la main)

| depuis | différences |
|---|---|
| 0 | 1, 6, 10, 23, 26, 34, 41, 53, 55 |
| 1 | 5, 9, 22, 25, 33, 40, 52, 54 |
| 6 | 4, 17, 20, 28, 35, 47, 49 |
| 10 | 13, 16, 24, 31, 43, 45 |
| 23 | 3, 11, 18, 30, 32 |
| 26 | 8, 15, 27, 29 |
| 34 | 7, 19, 21 |
| 41 | 12, 14 |
| 53 | 2 |

Une fois triées, on obtient tous les entiers de 1 à 35, puis 40, 41, 43, 45, 47, 49, 52, 53, 54 et 55. Cela fait 35 + 10 = 45 valeurs, toutes différentes.

## Pourquoi elle est optimale

L'argument de comptage ne suffit pas. Il y a C(10,2) = 45 différences distinctes et positives, ce qui impose seulement L ≥ 45. Pour prouver que 55 est le minimum, il faut montrer par recherche exhaustive qu'aucune règle de longueur 54 ou moins n'existe. Cette recherche a été faite dans les années 1960 : la valeur G(10) = 55 est un résultat établi, et la règle ci-dessus est la règle optimale classique.

Le programme suivant refait cette preuve. Il cherche les longueurs L en ordre croissant, ce qui fait que la première règle trouvée est forcément la plus courte. Il utilise un *branch-and-bound* fondé sur une propriété simple : si k marques sont déjà placées, le segment qui va de la dernière marque posée jusqu'à L est lui-même une règle de Golomb à n−k+1 marques. Sa longueur est donc au moins G(n−k+1). Le programme calcule G(2), G(3), …, G(10) dans l'ordre et réutilise chaque valeur pour élaguer la recherche suivante.

```c
/* ogr.c — recherche exhaustive de règles de Golomb optimales
   gcc -O2 -o ogr ogr.c && ./ogr 10 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#define MAXN 12
static int n, L, G[MAXN + 1], marks[MAXN];

/* k marques placées (marks[0..k-1]), used = masque des différences déjà prises */
static int dfs(int k, uint64_t used) {
    if (k == n) return 1;
    int last = marks[k - 1];
    /* après avoir placé p, il reste n-k-1 marques sur [p, L] :
       ce segment est une règle à n-k marques, donc p <= L - G[n-k] */
    int hi = L - G[n - k];
    int lo = (k == n - 1) ? L : last + 1;          /* la dernière marque vaut L */
    for (int p = lo; p <= hi; p++) {
        uint64_t m = used;
        int ok = 1;
        for (int i = 0; i < k; i++) {
            uint64_t bit = 1ULL << (p - marks[i]);
            if (m & bit) { ok = 0; break; }
            m |= bit;
        }
        if (!ok) continue;
        marks[k] = p;
        if (dfs(k + 1, m)) return 1;
    }
    return 0;
}

int main(int argc, char **argv) {
    int N = argc > 1 ? atoi(argv[1]) : 10;
    G[1] = 0;
    for (n = 2; n <= N; n++) {
        marks[0] = 0;
        for (L = G[n - 1] + 1; ; L++) {         /* L croissant => premier trouvé = optimal */
            if (L > 63) { fprintf(stderr, "L > 63\n"); return 1; }
            if (dfs(1, 0)) break;
        }
        G[n] = L;
        printf("G(%d) = %d :", n, L);
        for (int i = 0; i < n; i++) printf(" %d", marks[i]);
        printf("\n");
    }
    return 0;
}
```

**Résultat attendu**, d'après les valeurs connues G(2..10) = 1, 3, 6, 11, 17, 25, 34, 44, 55 :

```
G(10) = 55 : 0 1 6 10 23 26 34 41 53 55
```

- **Justesse :** pour chaque L < 55, le programme teste toutes les façons de placer les marques. Il ne coupe une branche que lorsqu'elle est réellement impossible, soit parce qu'une différence se répète, soit parce que l'élagage par G prouve qu'il n'y a pas la place. S'il atteint L = 55, c'est donc qu'aucune règle plus courte n'existe.
- **Ce que je ne garantis pas :** le temps d'exécution. Il devrait être de quelques secondes à quelques minutes en `-O2`, mais je ne l'ai pas mesuré.
- **Autre solution trouvée :** le programme peut renvoyer la règle miroir (`0 2 14 21 29 32 45 49 54 55`) au lieu de celle-ci. Elle est tout aussi valide, puisque c'est la même règle lue à l'envers.

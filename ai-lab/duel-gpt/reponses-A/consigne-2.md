Voici un programme en C qui compte les tableaux de Costas par backtracking avec des masques de bits.

**Avertissement :** je n'ai pas d'outil d'exécution dans cette session, donc je n'ai pas compilé ni lancé ce programme. Les 12 nombres plus bas sont les valeurs connues de la suite OEIS A008404. C'est ce que le programme doit afficher s'il est correct, mais je ne l'ai pas vérifié en le lançant.

## Code (`costas.c`)

```c
/* Comptage exact des tableaux de Costas d'ordre n = 1..12.
 * Une permutation p de 0..n-1 est de Costas si tous les vecteurs
 * (j-i, p[j]-p[i]), i<j, sont distincts. Autrement dit, pour chaque
 * écart d = j-i, les différences p[j]-p[j-d] doivent être deux à deux distinctes.
 *
 * Compilation : gcc -O2 -o costas costas.c
 */
#include <stdio.h>
#include <stdint.h>

static int n;
static int p[16];
static uint32_t used_val;     /* valeurs déjà placées (bit v)                 */
static uint32_t diff[16];     /* diff[d] : bit (p[j]-p[j-d]+n) déjà utilisé    */
static long long count;

static void rec(int k)
{
    if (k == n) { count++; return; }

    for (int v = 0; v < n; v++) {
        if (used_val >> v & 1) continue;

        /* vérifier que pour chaque écart d, la différence v - p[k-d] est nouvelle */
        int ok = 1;
        for (int d = 1; d <= k; d++) {
            int x = v - p[k - d] + n;          /* dans 1..2n-1, tient dans 32 bits */
            if (diff[d] >> x & 1) { ok = 0; break; }
        }
        if (!ok) continue;

        for (int d = 1; d <= k; d++) diff[d] |= 1u << (v - p[k - d] + n);
        used_val |= 1u << v;
        p[k] = v;

        rec(k + 1);

        used_val &= ~(1u << v);
        for (int d = 1; d <= k; d++) diff[d] &= ~(1u << (v - p[k - d] + n));
    }
}

int main(void)
{
    for (n = 1; n <= 12; n++) {
        count = 0;
        used_val = 0;
        for (int d = 0; d < 16; d++) diff[d] = 0;
        rec(0);
        printf("n = %2d : %lld\n", n, count);
    }
    return 0;
}
```

## Principe

- On place les colonnes une par une, de gauche à droite.
- Pour chaque écart `d`, un masque `diff[d]` mémorise les différences `p[j]-p[j-d]` déjà utilisées.
- Un candidat `v` pour la colonne `k` est rejeté dès que `v - p[k-d]` existe déjà pour un écart `d`.
- Chaque vecteur est donc testé en O(1), et l'arbre de recherche est fortement élagué.

Pour n=12, la recherche explore de l'ordre de quelques dizaines de millions de nœuds. Cela devrait prendre quelques secondes au plus en `-O2`, bien en dessous de 5 minutes, mais je n'ai pas mesuré ce temps.

## Résultats attendus (OEIS A008404)

```
n =  1 : 1
n =  2 : 2
n =  3 : 4
n =  4 : 12
n =  5 : 40
n =  6 : 116
n =  7 : 200
n =  8 : 444
n =  9 : 760
n = 10 : 2160
n = 11 : 4368
n = 12 : 7852
```

Pour vérifier, lancez `gcc -O2 -o costas costas.c && time ./costas` et comparez la sortie à cette liste.

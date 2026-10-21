/* Règles de Golomb optimales, sans emprunter les résultats des autres :
   la borne « une sous-règle de k marques mesure au moins opt[k] » utilise UNIQUEMENT les opt[] que ce programme a lui-même trouvés.
   Ensemble des distances en bits (__int128 -> jusqu'à 127), symétrie : 1re distance < dernière distance.
   Usage : ./golomb N  -> cherche n = 2..N, vérifie chaque règle avec un juge indépendant. */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
typedef unsigned __int128 u128;
static int n, L, marks[32], opt[32];
static long long noeuds;

static int rec(int k, u128 dist) {          /* k marques posées (marks[0..k-1]) */
    noeuds++;
    int reste = n - k;                        /* marques à poser, L compris */
    if (reste == 1) {                          /* poser L */
        u128 nd = 0;
        for (int i = 0; i < k; i++) { int x = L - marks[i]; u128 b = (u128)1 << x; if ((dist | nd) & b) return 0; nd |= b; }
        if (k >= 2 && marks[1] - marks[0] >= L - marks[k - 1]) return 0;   /* symétrie */
        marks[k] = L; return 1;
    }
    int haut = L - opt[reste];                 /* de p à L il reste une sous-règle de reste+1 marques ? non : p + (reste-1 marques) jusqu'à L -> sous-règle de reste marques incluant p */
    for (int p = marks[k - 1] + 1; p <= haut; p++) {
        if (k == 1 && 2 * p >= L) break;      /* symétrie grossière : la 1re distance est dans la 1re moitié */
        u128 nd = 0; int ok = 1;
        for (int i = 0; i < k; i++) { int x = p - marks[i]; u128 b = (u128)1 << x; if ((dist | nd) & b) { ok = 0; break; } nd |= b; }
        if (!ok) continue;
        if (p < opt[k + 1]) continue;          /* marks[0..k] forment une règle de k+1 marques de longueur p >= opt[k+1] */
        marks[k] = p;
        if (rec(k + 1, dist | nd)) return 1;
    }
    return 0;
}

static int juge(int m) {                       /* toutes les distances distinctes ? */
    char vu[256] = {0};
    for (int i = 0; i < m; i++) for (int j = i + 1; j < m; j++) { int d = marks[j] - marks[i]; if (d < 0 || d > 255 || vu[d]) return 0; vu[d] = 1; }
    return 1;
}

int main(int argc, char **argv) {     /* golomb_branche n L p : explore seulement les règles dont la 2e marque vaut p */
    n = atoi(argv[1]); L = atoi(argv[2]); int p = atoi(argv[3]);
    int OPT[] = {0, 0, 1, 3, 6, 11, 17, 25, 34, 44, 55, 72, 85, 106};
    for (int i = 0; i <= 13; i++) opt[i] = OPT[i];
    if (2 * p >= L || p < opt[2] || L - p < opt[n - 1]) { printf("rien\n"); return 0; }
    marks[0] = 0; marks[1] = p; u128 d = (u128)1 << p;
    if (rec(2, d) && juge(n)) { for (int i = 0; i < n; i++) printf(i ? " %d" : "%d", marks[i]); printf("\n"); } else printf("rien\n");
    return 0;
}

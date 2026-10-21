/* Tableaux de Costas : permutations p de 0..n-1 telles que tous les vecteurs (j-i, p[j]-p[i]), i<j, soient distincts.
   (Une règle de Golomb en deux dimensions : aucun déplacement ne se répète.) Compteur exact par retour arrière, sans symétrie
   pour rester simple et vérifiable. Usage : ./costas N -> compte pour n = 1..N. Juge : OEIS A008404 (lu APRÈS le calcul). */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
static int n, p[32], used[32];
static unsigned char vu[32][64];                 /* vu[dx][dy+31] : vecteur déjà présent */
static long long total;
static void rec(int k) {
    if (k == n) { total++; return; }
    for (int v = 0; v < n; v++) {
        if (used[v]) continue;
        int ok = 1, i;
        for (i = 0; i < k; i++) if (vu[k - i][v - p[i] + 31]) { ok = 0; break; }
        if (!ok) continue;
        for (i = 0; i < k; i++) vu[k - i][v - p[i] + 31] = 1;
        used[v] = 1; p[k] = v; rec(k + 1); used[v] = 0;
        for (i = 0; i < k; i++) vu[k - i][v - p[i] + 31] = 0;
    }
}
int main(int argc, char **argv) {
    int N = atoi(argv[1]);
    if (argc > 2) {   /* mode « une colonne » : ./costas n v -> nombre de tableaux avec p[0]=v (le retournement haut-bas donne count(v)=count(n-1-v)) */
        n = N; int v = atoi(argv[2]); total = 0; used[v] = 1; p[0] = v; rec(1); printf("%lld\n", total); return 0;
    }
    for (n = 1; n <= N; n++) { clock_t t = clock(); total = 0; rec(0);
        printf("n=%d %lld (%.1f s)\n", n, total, (double)(clock() - t) / CLOCKS_PER_SEC); fflush(stdout); }
}

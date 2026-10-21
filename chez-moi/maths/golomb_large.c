/* Golomb, version « grandes longueurs » (1021 19h40). La v1 (golomb_branche.c) rangeait les distances dans un __int128 :
   toute distance >= 128 débordait (décalage indéfini), donc ses « impossible » pour n=15, L>=128 ne valaient rien.
   Ici : ensemble des distances sur 256 bits (4 x u64), opt[] jusqu'à 14 (ma propre preuve de 127),
   et une borne de plus : les écarts restants sont des distances encore libres, toutes différentes,
   donc L - p >= somme des (écarts restants) plus petites distances libres.
   Usage : ./golomb_large n L p [q]  -> explore les règles de n marques, longueur L, 2e marque p ; imprime la règle ou « rien ». */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
typedef struct { uint64_t w[4]; } B256;
static int n, L, marks[32], opt[32];

static inline int has(const B256 *b, int x) { return (b->w[x >> 6] >> (x & 63)) & 1; }
static inline void put(B256 *b, int x) { b->w[x >> 6] |= (uint64_t)1 << (x & 63); }

static int somme_libres(const B256 *b, int m, int plafond) {   /* somme des m plus petites distances libres (>=1), coupe dès > plafond */
    int s = 0;
    for (int x = 1; m > 0 && x < 256; x++) if (!has(b, x)) { s += x; m--; if (s > plafond) return s; }
    return m ? 1 << 20 : s;
}

static int rec(int k, B256 dist) {
    int reste = n - k;
    if (reste == 1) {
        for (int i = 0; i < k; i++) { int x = L - marks[i]; if (has(&dist, x)) return 0; put(&dist, x); }
        if (marks[1] - marks[0] >= L - marks[k - 1]) return 0;   /* symétrie : 1re distance < dernière */
        marks[k] = L; return 1;
    }
    int haut = L - opt[reste];
    for (int p = marks[k - 1] + 1; p <= haut; p++) {
        B256 nd = dist; int ok = 1;
        for (int i = 0; i < k; i++) { int x = p - marks[i]; if (has(&nd, x)) { ok = 0; break; } put(&nd, x); }
        if (!ok) continue;
        if (p < opt[k + 1]) continue;
        int g = n - 1 - k;                                        /* écarts consécutifs restant après p */
        if (g >= 2 && somme_libres(&nd, g, L - p) > L - p) continue;
        marks[k] = p;
        if (rec(k + 1, nd)) return 1;
    }
    return 0;
}

static int juge(int m) {
    char vu[512] = {0};
    for (int i = 0; i < m; i++) for (int j = i + 1; j < m; j++) { int d = marks[j] - marks[i]; if (d <= 0 || d > 511 || vu[d]) return 0; vu[d] = 1; }
    return 1;
}

int main(int argc, char **argv) {
    n = atoi(argv[1]); L = atoi(argv[2]); int p = atoi(argv[3]);
    if (L > 255) { printf("L trop grand\n"); return 2; }
    int OPT[] = {0, 0, 1, 3, 6, 11, 17, 25, 34, 44, 55, 72, 85, 106, 127};   /* tous trouvés et prouvés par moi (voir golomb13/14.txt) */
    for (int i = 0; i <= 14; i++) opt[i] = OPT[i];
    if (2 * p >= L || p < opt[2] || L - p < opt[n - 1]) { printf("rien\n"); return 0; }
    marks[0] = 0; marks[1] = p; B256 d = {{0}}; put(&d, p);
    int k0 = 2;
    if (argc > 4) {                                   /* 3e marque imposée : q (pour répartir le travail sur les cœurs) */
        int q = atoi(argv[4]);
        if (q <= p || q - p == p || q > L - opt[n - 2] || q < opt[3]) { printf("rien\n"); return 0; }
        put(&d, q); put(&d, q - p); marks[2] = q; k0 = 3;
        if (n - 3 >= 2 && somme_libres(&d, n - 3, L - q) > L - q) { printf("rien\n"); return 0; }
    }
    if (rec(k0, d) && juge(n)) { for (int i = 0; i < n; i++) printf(i ? " %d" : "%d", marks[i]); printf("\n"); } else printf("rien\n");
    return 0;
}

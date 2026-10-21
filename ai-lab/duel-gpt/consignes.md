# Duel à l'aveugle : 5 consignes

Colle chaque consigne TELLE QUELLE dans ChatGPT (une nouvelle conversation par consigne), puis colle sa réponse dans `reponses-B/consigne-N.md` (ou envoie-la-moi).
Les tâches 1, 2 et 4 sont jugées par le résultat exact ; 3 et 5 par toi, à l'aveugle (A/B mélangés).

---
## Consigne 1

Ce programme C cherche des règles de Golomb optimales (n marques, longueur L). Je veux l'utiliser pour n=15, avec L de 128 à 151. Il répond « rien » (impossible) pour L=128, 129, 130, 131. Est-ce que je peux faire confiance à ces réponses ? S'il y a un bug, explique-le précisément et corrige-le.

```c
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

```

---
## Consigne 2

Écris un programme (Python ou C, au choix) qui compte EXACTEMENT les tableaux de Costas d'ordre n pour n = 1 à 12 (permutations p de 0..n-1 telles que tous les vecteurs (j-i, p[j]-p[i]) pour i<j soient distincts). Donne le code complet, puis la liste des 12 nombres que ton programme affiche. Il doit tourner en moins de 5 minutes sur un PC ordinaire.

---
## Consigne 3

J'ai testé une stratégie de trading crypto (« tendance + volatilité croissante ») sur 21 cryptos. Sur 2026 (données jamais vues pendant la mise au point), elle fait +130 %. Mais quand je compare à 500 stratégies tirées au hasard (mêmes frais, même nombre de trades, mêmes sens long/short), elle n'arrive qu'au 81e percentile. Mon critère fixé AVANT le test était : battre le 95e percentile. Sur 2024-2025, elle avait été choisie parmi 840 combinaisons, et la corrélation de rang entre les résultats 2024-2025 et 2026 de ces 840 combinaisons est de +0,04.
Est-ce que je dois la trader avec de l'argent réel ? Réponds oui ou non, puis justifie en 10 lignes maximum.

---
## Consigne 4

Trouve une règle de Golomb optimale à 10 marques (la plus courte possible : 10 entiers 0 = a1 < a2 < ... < a10, toutes les différences ai - aj distinctes). Donne la règle et sa longueur, et dis comment tu sais qu'elle est optimale (si tu écris un programme, donne-le).

---
## Consigne 5

Je suis développeur, père de famille, je travaille la journée et j'ai un peu de temps le soir. J'ai une IA personnelle (un agent avec mémoire, accès à mon PC, une petite VM et 4 $ sur un compte crypto) qui me coûte un abonnement chaque mois. Elle n'a pas de compte bancaire à elle et ne doit pas créer de faux comptes. Propose-moi le plan le plus réaliste pour qu'elle rapporte au moins le prix de son abonnement d'ici 3 mois. Sois concret et honnête sur les chances.

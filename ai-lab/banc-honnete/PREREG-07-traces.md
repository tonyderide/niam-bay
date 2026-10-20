# Pré-enregistrement 07 : la chasse aux tracés (idée de Tony, 1021 vers 00h50, avant tout calcul)
Bougies de 1 jour, 21 cryptos (comme en 06), frais de 0,05 % par côté, entrée à l'ouverture de la bougie suivante, sortie après H bougies.

## Les 6 motifs classiques (le short est le miroir exact du long)
1. **Avalement** : la bougie précédente est rouge, la bougie du jour est verte et englobe entièrement son corps, et close > SMA50. Short : le miroir, avec close < SMA50.
2. **Marteau au plus bas de 20 jours** : mèche basse ≥ 2 × le corps, close dans le tiers haut de la bougie, low = plus bas des 20 derniers jours. Short : étoile filante au plus haut de 20 jours.
3. **Inside bar cassée** : la bougie d'hier est contenue dans celle d'avant-hier, puis le close du jour passe au-dessus du plus haut d'avant-hier (long) ou sous son plus bas (short).
4. **NR7 cassée** : le range d'hier est le plus petit des 7 derniers jours, puis le close du jour passe au-dessus du plus haut d'hier (long) ou sous son plus bas (short).
5. **Trois soldats / trois corbeaux** : 3 bougies vertes de suite avec des closes croissants (long) ; 3 rouges de suite avec des closes décroissants (short).
6. **Rejet de la SMA200** : low < SMA200, mais la bougie clôture verte au-dessus de la SMA200 (long). Short : le miroir.

Durée de tenue H ∈ {3, 5, 10} jours, soit 18 configurations au total.

## Méthode
- **Sélection** : on garde la configuration qui a la meilleure somme sur 2024-2025, avec au moins 100 trades. Aucun regard sur 2026 à cette étape.
- **Jugement unique** sur 2026 (01/01 → 16/10), avec le moteur `banc.py` : 500 tirages au hasard, mêmes durées de tenue, sens aléatoires.
- GAGNE seulement si, sur 2026 : la somme est > 0, au moins 60 % des marchés sont positifs, le résultat dépasse le 95e centile du hasard, et on compte au moins 30 trades.
- En plus, à titre d'information : le découpage avant et après le 30/06/2026 (date de fin des connaissances du modèle).

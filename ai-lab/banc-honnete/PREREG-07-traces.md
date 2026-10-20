# Pré-enregistrement 07 : la chasse aux tracés (idée de Tony, 1021 vers 00h40, avant tout calcul)
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

## Résultat (1021 vers 00h45) : ÉCHEC
- Sélection sur 2024-2025 : **avalement, H = 10 jours**, 891 trades, +548 %.
- Jugement sur 2026 : **−29 %**, 50e centile du hasard (pile la médiane), 8 marchés positifs sur 21.
  - Janvier-juin 2026 : +72 %.
  - Juillet-octobre : −6 %.
- Le motif qui était le meilleur sur 2024-2025 ne fait pas mieux que le hasard en 2026.

## Avenant 07b, écrit APRÈS avoir vu la sélection, mais AVANT tout regard sur 2026
Sur 2024-2025, les motifs de continuation perdent énormément : trois soldats H=5 à −1 736 %, NR7 à −1 259 %. **L'inverse de ces motifs gagnerait-il ?**
- On teste UNE seule config : le pire de 2024-2025, **trois soldats H=5, pris à l'envers**. Après 3 bougies vertes on prend un short, après 3 rouges un long, et on sort au bout de 5 jours.
- Le critère de jugement sur 2026 est le même que plus haut.
- ⚠️ C'est un regard a posteriori sur la sélection, et je le déclare comme tel. Mais 2026 n'a été regardé pour AUCUNE configuration de type « à l'envers ».

## Résultat 07b : ÉCHEC
- 2024-2025 (sélection, pour rappel) : +1 457 %, mais seulement au 89e centile du hasard. Même sur sa propre période de sélection, ce n'est pas significatif.
- 2026 (jugement) : +110 %, 58e centile, 9 marchés positifs sur 21.
  - Janvier-juin : −197 %.
  - Juillet-octobre : +309 %.
- Le hasard a une dispersion énorme, avec un p95 vers +1 000 %. Des trades de 5 jours sur des cryptos, c'est très bruité : un motif journalier ne ressort qu'avec beaucoup plus de données.

**Bilan de la chasse aux tracés : 0 sur 18 (et 0 sur 1 pour l'avenant).** Les figures classiques ne battent pas le hasard sur 21 cryptos.

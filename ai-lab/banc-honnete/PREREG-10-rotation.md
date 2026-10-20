# Pré-enregistrement 10 : la rotation des forts (1021 vers 01h20, avant tout calcul)
Conseil intérieur : OUI à 6,73. Réserves notées : peu de semaines pour juger (environ 41 en 2026) ; avec 3,77 $, impossible de tenir 10 positions (tailles minimales), donc ce test est **théorique**.

- **Univers** : les 21 cryptos du PREREG-06, en bougies journalières Kraken (prix des trades).
- **Rééquilibrage** : chaque lundi à 00h UTC. On classe les cryptos selon leur rendement sur les L semaines passées, puis on achète les 5 premières et on vend à découvert les 5 dernières, à poids égaux, pour une semaine.
  - Rendement de la semaine = ½ × moyenne(longs) − ½ × moyenne(shorts) − 0,10 %. Les 0,10 % correspondent à un aller-retour complet sur toute l'exposition, ce qui est pessimiste.
- **Grille** :
  - L ∈ {1, 2, 4} semaines ;
  - sens ∈ {momentum : acheter les forts, retournement : acheter les faibles}.
  - Soit 6 configurations.
- **Sélection** : la meilleure somme des rendements hebdomadaires sur 2024-2025.
- **Jugement UNIQUE** sur 2026, du 05/01 au 12/10 (dernière semaine complète).
  - Hasard : 2 000 tirages de paniers aléatoires (5 longs et 5 shorts chaque semaine), avec les mêmes frais.
  - GAGNE si la somme de 2026 est > 0, qu'elle dépasse le 95e centile du hasard, et que plus de 50 % des semaines sont positives.
- À titre d'information : la répartition avant et après le 30/06/2026.

## Résultat (1021 vers 01h25, t10.log) : ÉCHEC
- Sélection sur 2024-2025 : **momentum sur 1 semaine**, +40 % sur 105 semaines, mais seulement 50 % de semaines positives.
- Jugement sur 2026 : **−25,8 %**, 42 % de semaines positives, **8e centile du hasard**, donc pire que des paniers tirés au sort. Janvier-juin : +5,5 %. Juillet-octobre : −31,3 %.
- Même sur la période de sélection, aucune configuration ne dépassait 52 % de semaines positives. Le momentum entre cryptos ne se retrouve pas sur ces 21 cryptos en 2024-2026.

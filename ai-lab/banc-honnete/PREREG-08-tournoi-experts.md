# Pré-enregistrement 08 : tournoi des experts (idée de Tony, 1021 vers 00h55)
Figé AVANT que les experts ne proposent quoi que ce soit.

4 agents experts : un quant statisticien, un scalper, un suiveur de tendance, un quant spécialiste de la volatilité. Chacun propose 3 stratégies dans le langage de `banc.py`, en disant QUAND chaque indicateur s'utilise (filtre de régime). Les experts n'ont accès à aucune donnée ni à aucun résultat.

Règles du tournoi :
- Marchés : en bougies de 1 jour, les 21 cryptos du PREREG-06 ; en 15m, 1h et 4h, BTC, ETH et SOL (les données disponibles).
- Frais : 0,05 % par côté.
- Si une proposition ne s'exécute pas dans le moteur, elle est éliminée sans être corrigée.
- **Sélection** : on garde la meilleure somme sur 2024-2025, avec au moins 100 trades, chaque stratégie étant mesurée sur ses propres marchés.
- **Jugement UNIQUE** sur 2026 (01/01 → 16/10) avec `banc.py`. GAGNE seulement si :
  - la somme est > 0 ;
  - au moins 60 % des marchés sont positifs ;
  - le résultat dépasse le 95e centile de 500 tirages au hasard ;
  - on compte au moins 30 trades.
- À titre d'information : découpage avant et après le 30/06/2026, ainsi que le 2e et le 3e de la sélection jugés aussi. Ces deux-là ne comptent pas dans le verdict.

## Avenant 08-scalp : contrainte de Tony (1021 vers 01h00), « sur une journée au moins 30 trades »
Ajouté avant d'avoir reçu les propositions du scalper. Catégorie séparée :
- Bougies de 5 minutes, BTC, ETH et SOL. Seules les stratégies avec **au moins 30 trades par jour et par marché en moyenne** sont admises.
- Sélection sur 2026-01-01 → 2026-06-30. Jugement UNIQUE sur 2026-07-01 → 2026-10-16, avec le même critère que plus haut (hasard 500 tirages, p95, au moins 60 % des marchés positifs).
- À 30 trades par jour, on a plus de 3 000 trades par mois et par marché : la puissance statistique est largement suffisante sur ces fenêtres plus courtes.
- Calcul honnête à faire figurer dans le rapport : 30 trades × 0,10 % = 3 % de frais par jour (en taker). On donnera aussi, À TITRE D'INFORMATION, le résultat avec des frais maker (0,02 % par côté), en précisant que le moteur ne simule pas le risque de ne pas être exécuté.

# Pré-enregistrement 03 : Supertrend (10, 3), version TradingView par défaut
Figé le 2026-10-20 vers 04h15, avant tout calcul.

- **Données** : bougies 1h et 4h de Kraken (prix des trades), sur BTC, ETH et SOL. Les deux unités de temps sont jugées séparément.
  - Pour éviter d'en choisir une après coup, la stratégie doit gagner **sur les deux**.
  - Périodes : 2024-2025, et 2026 jusqu'au 16 octobre.
- **Indicateur** : ATR(10) lissé de Wilder (RMA), multiplicateur 3, bandes calculées sur hl2 avec la règle standard de report des bandes.
- **Règle** : toujours en position. Quand la tendance passe haussière on est long, quand elle passe baissière on est short. Chaque changement se fait à l'open de la bougie suivante.
- **Frais** : 0,05 % par côté, soit 0,10 % pour chaque retournement complet (on ferme une position et on ouvre l'autre).
- **Hasard** : 500 tirages, avec le même nombre de retournements placés à des instants aléatoires et un sens de départ aléatoire.

La stratégie GAGNE seulement si :
- le total est > 0 sur chaque période et chaque unité de temps ;
- elle dépasse le 95e centile du hasard partout ;
- au moins 2 marchés sur 3 sont positifs sur 2024-2025 ;
- on compte au moins 30 trades par case.

À titre indicatif : le résultat d'un simple « acheter et garder ».

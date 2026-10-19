# Paris rapides : pré-enregistrement (2026-10-19 ~02h25, avant tout calcul)
Données : candles.json (mark horaire Kraken Futures, BTC ETH SOL DOT LINK, du 01/01 au 16/10/2026). Frais : **0,10 % aller-retour** (taker 0,05 % par côté).
Règles figées, aucun réglage après coup :
- **R1 retour à la moyenne** : si la dernière heure a bougé de plus de 1,5 %, on parie l'inverse pendant l'heure suivante.
- **R2 momentum 1 h** : on parie dans le sens de la dernière heure, à chaque heure.
- **R3 cassure** : si la clôture dépasse le plus haut des 24 heures précédentes, on part long pour les 4 heures suivantes.
Juge : rendement moyen NET par pari sur juillet-octobre (période de test). Une règle « gagne » si ce rendement net est > 0 ET si P(> 0) > 0,95 au bootstrap par blocs d'une semaine. Janvier-juin est montré pour information seulement.

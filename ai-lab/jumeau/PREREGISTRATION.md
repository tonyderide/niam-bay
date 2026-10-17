# Jumeau différentiel de 0x777d…0111 (Hyperliquid) : pré-enregistrement (2026-10-17, avant d'écrire les règles)

Cible : 0x777d062defa9a95fb0066b4b3f410d170b110111, coin **NEAR** uniquement (68 % de ses 2000 derniers fills).
Avant ce commit, je n'ai vu que des statistiques agrégées (long only, 98 % de trades gagnants, détention médiane ~2h40, 44 % maker). Pas de règle d'entrée.

## Question jugée
Pour chaque heure UTC pleine H à partir de la mise en service : « le bot ouvre-t-il au moins un long NEAR pendant l'heure H ? » (fill avec dir = "Open Long").
Le jumeau donne une probabilité p_H calculée UNIQUEMENT à partir des données disponibles au début de H (bougies NEAR 1h Hyperliquid + la position publique du bot).

## Témoins
- (a) taux de base : p = fréquence des heures « ouvre » dans les 2000 fills d'entraînement.
- (b) « comme l'heure d'avant » : p = 0,8 si le bot a ouvert pendant H-1, sinon le taux de base.

## Critère (fixé ici)
Sur les **168 premières heures** (7 jours), le jumeau gagne si son Brier est inférieur à CHACUN des deux témoins d'au moins 0,01 ET si P(jumeau meilleur) > 0,9 au bootstrap (10 000 tirages). Sinon, j'écris : « je n'ai pas compris ce bot ».
Juge secondaire, en information seulement : le PnL papier du jumeau, frais taker inclus, comparé au PnL réalisé du bot sur NEAR pendant la même fenêtre.

Garde-fous : lecture seule de l'API publique, 1 requête / 2 s. Aucun ordre, ni réel ni sur testnet. Mon capital n'y sera pas exposé sans un nouveau passage au conseil ET l'accord de Tony.

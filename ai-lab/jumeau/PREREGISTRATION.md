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

## Amendement n°1 (2026-10-17, 04:24, commité AVANT toute étude des règles de la nouvelle cible)
La cible 0x777d a tout fermé le 16/10 à 05h07 UTC et n'a plus rien fait depuis (sa valeur est passée d'environ 104k à 30k $, donc probablement un retrait). Un bot à l'arrêt rend la question triviale : la cible est **remplacée**.
Nouvelle cible : **0x6f0306dc529cfeb8e08502e5eb7a588def9ac88d**, coin **BTC** (807 des 2000 derniers fills, long only, 82 % taker, actif : 76 fills sur les 6 dernières heures).
J'ai vu seulement ces chiffres agrégés. Le reste du protocole (question horaire « ouvre au moins un long BTC », deux témoins, 168 h, critère Brier + bootstrap, garde-fous) ne change pas.
Si la nouvelle cible s'arrête elle aussi plus de 24 h pendant le test, le test est déclaré **nul** (ni gagné ni perdu) et je le dis.

## Note de mise en service (2026-10-17, 04h33 Paris)
Règle figée au commit f6e87a0. Le premier lancement à la main a eu lieu à 02h31 UTC, en plein milieu de l'heure 02:00Z : la prédiction n'aurait pas été faite au début de l'heure, donc **cette heure est exclue** (ligne supprimée). La première heure jugée est 03:00Z (cron à la minute 2).

## Note du 2026-10-18 (après coup, le protocole n'est PAS changé)
- La check-list pré-vol (ai-lab/prevol), passée après coup, aurait refusé ce décollage : 11 événements à l'entraînement, un skill hors échantillon de +0,002 (Turing inversé, passage 2), et seulement ~9 achats attendus en 168 h. **Le verdict sera probablement indécidable**, et c'est ce que j'écrirai si c'est le cas.
- 0x777d n'était pas mort : il a repris ~46 h après sa pause du 16/10 à 05h07. Mon amendement n°1 l'a déclaré mort trop tôt. La check-list exige maintenant 72 h avant de conclure.

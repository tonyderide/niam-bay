# Pré-enregistrement 65 : la règle à 90 % en papier EN AVANT (04/11/2026 → 03/05/2027)
Écrit et commité le 03/11/2026 au soir, avant le premier jour de données. Demande de Tony : suivre la règle sans argent réel. Aucun ordre, aucun compte, aucune clé.

## Règle (aucun réglage, figée depuis PREREG-62)
SL 10 %, activation +1 %, trailing 0,5 %, inversion après une perte, toujours en position, 1 min, sans levier ni martingale, frais taker 0,05 % par côté, **financement réel compté**. Premier trade de chaque pièce : long, à 00:00 UTC le 04/11/2026.

## Univers (figé)
BTC, ETH, SOL, XRP, DOGE, ADA, LINK, AVAX, LTC, BNB, DOT, BCH, ATOM, perpétuels USDT-M Binance. Portefeuille = 13 parts égales, indépendantes.

## Mise en œuvre
`papier-90/papier90.py`, prix et financement publics, lancé une fois par jour par `papier-90/cron.sh`. Il rattrape seul les jours manqués, à condition de tourner avant que l'historique 1 min ne soit plus disponible. Moteur vérifié avant lancement contre `chaine` de t62.py sur BTC et SOL 2026 : mêmes trades, écart 0,0 (hors dernier trade, resté ouvert au lieu d'être clos de force). Limite : remplissage au prix du stop, sans glissement au-delà de l'ouverture de la minute.

## Jugement UNIQUE (le 04/05/2027 ou après : `papier90.py juger`)
**« TIENT »** si, à la fin : gagnants moyens ≥ 90 %, espérance nette moyenne > 0, au moins 7 pièces sur 13 positives, portefeuille > 0, baisse médiane moins forte que −30 %, et espérance supérieure à celle d'un sens tiré au hasard dans ≥ 95 % de 100 tirages. **« NE TIENT PAS »** sinon. Pas de réglage modifié en cours de route ; le journal est pour information.

Réserve écrite d'avance : 6 mois restent courts, et même « TIENT » ne vaut pas autorisation de mettre de l'argent sans décision de Tony. 2024-25 a perdu lourdement avec cette même règle.

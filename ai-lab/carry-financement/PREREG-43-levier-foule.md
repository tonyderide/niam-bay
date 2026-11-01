# PREREG-43 : quand toute la foule paie pour être longue, le marché baisse-t-il ensuite ?
Écrit le 01/11/2026 vers 06h50 CET, avant tout calcul. Hypothèse H8 de ai-lab/banc-honnete/FILE-HYPOTHESES.md. `scripts/cherche -v financement moyen marché foule levier liquidations panier short` : rien d'identique. Voisin : chasse-1019/funding-extreme (financement extrême **d'une seule pièce**, horaire, contrarien ou suivi : PERD). Ici le signal est **agrégé sur tout le marché**, journalier, un seul sens fixé d'avance.

## Raison économique, et ce que dit la théorie avant les données
Un financement élevé **partout à la fois** veut dire que la foule entière s'est endettée pour être longue. Ce levier est le carburant des liquidations en cascade : une baisse modeste force des ventes, qui en forcent d'autres. Le vendeur à découvert, lui, **reçoit** ce financement pendant qu'il attend. Deux sources de gain qui ne demandent pas de prévoir le hasard : le financement encaissé (connu) et un risque de krach plus élevé (asymétrie). Contre : un financement élevé accompagne souvent un marché haussier qui continue (momentum) ; le short peut saigner longtemps. Prior : incertain, plutôt NON DÉMONTRÉ.

## Données (déjà là)
Univers et données de PREREG-27 (`etude_univers.py`) : top 30 du volume chaque 1er janvier, morts compris, prix journaliers Binance, financement réel ; 01/01/2021 → 27/10/2026.

## Règle (aucun réglage)
- Chaque jour d à 00:00 UTC : **financement agrégé** A_d = moyenne, sur les pièces éligibles de l'univers du jour (critères de PREREG-27), de la somme de leur financement sur les 7 jours précédents.
- Seuil : le **90e centile** de A sur tous les jours **passés** depuis le début (expansif ; au moins 180 jours d'historique, donc pas de signal avant fin juin 2021).
- Si A_d > seuil : **short du panier égal** des pièces éligibles (1 $ au total, réparti également) pendant 24 h ; sinon pas de position.
- Gain = −rendement du panier (ouverture → clôture du jour) + financement reçu par le short pendant les 24 h. Frais 0,05 % sur chaque variation de poids.

## Jugement
- Historique : 01/01/2021 → 31/12/2025. **JUGEMENT UNIQUE : 01/01/2026 → 26/10/2026.**
- **Témoin** (décalages circulaires, comme PREREG-27) : la série des jours de signal décalée d'un nombre de jours tiré entre 30 et N − 30, **dans la période jugée** (même nombre de jours de short, mêmes épisodes, placés ailleurs), 1 000 tirages, graine 43. p = part ≥ la règle.
- **GAGNE** si net > 0 sur l'historique **ET** net > 0 en 2026 **ET** p < 0,05 en 2026. **NON DÉMONTRÉ** si net 2026 > 0 sans le reste. **PERD** sinon. Si la règle n'a **aucun jour de signal en 2026** : NON ÉVALUABLE en 2026, verdict sur l'historique noté pour information seulement.

## Rapporté
Jours de signal par période, net, prix, financement, frais, pire épisode, rendement moyen du panier les jours de signal contre les autres jours ; par année ; short permanent du panier (repère).

## Relecture d'équité, avant calcul
- 90e centile, 7 jours, 180 jours de chauffe fixés ici ; aucune grille.
- Le témoin garde la structure en épisodes (décalage, pas de mélange jour par jour) et les frais : il ne retire que le moment.
- Aucune action sur Martin ni Kraken.

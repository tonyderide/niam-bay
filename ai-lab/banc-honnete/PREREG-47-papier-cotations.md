# Pré-enregistrement 47 : short des nouvelles cotations crypto de Binance, en papier EN AVANT
Écrit le 01/11/2026 vers 16h50 CET, avant la première cotation de la période. Suite de PREREG-46 (**GAGNE** sur 2021-2026 : +24,2 % par trade en 2021-25, +8,0 % en 2026, p < 0,001 ; crypto seulement +18,5 %, p = 0,002). Un résultat historique peut encore tenir à la période ; seules des cotations **à venir** peuvent le confirmer.

## Règle (celle de PREREG-46, N = 90 figé, restreinte à la crypto)
- Cotations : perpétuels USDT-M de Binance avec `underlyingType` = COIN (actions, matières premières, indices exclus — la contamination trouvée en PREREG-46), `onboardDate` du **02/11/2026 00:00 UTC au 28/02/2027 23:59 UTC**, repérés chaque jour dans `fapi/v1/exchangeInfo`.
- Short à l'ouverture de la **2e bougie journalière** (jour UTC qui suit la cotation), tenu **90 jours** (clôture de la 90e bougie) ou jusqu'au retrait (dernière clôture).
- Rendement = −(sortie / entrée − 1) + financement reçu par le short (somme des taux publics) − 2 × 0,05 %, **plancher −100 %**. Mise égale par trade.
- Code : `papier-cotations/cotations.py` ; la fonction `trade` donne les mêmes rendements que t46.py (vérifié sur 5 cotations de juin 2026 avant ce commit : 5/5 identiques).

## Journal
Cron local à 03h37 Paris : lecture de exchangeInfo, des bougies et du financement **publics** (sans clé, sans compte), enregistrement des cotations et des données dans `papier-cotations/`, ligne quotidienne dans `journal.md` (cotations vues, trades ouverts/fermés, moyennes), commit local. **Pool témoin figé le jour où la cotation est vue** : pièces COIN en cotation, cotées depuis plus de 365 jours avant l'entrée. Aucun ordre, aucune action sur Martin ni Kraken.

## Jugement (UNIQUE, le 01/06/2027 ou après : `cotations.py juger`)
- Tous les trades entrés (dernières sorties fin mai 2027).
- **Témoin** : pour chaque trade, short d'une pièce tirée au hasard dans son pool figé, même date d'entrée, 90 jours, ses bougies et son financement publics, mêmes frais et plancher ; 1 000 tirages, graine 47. p = part des tirages au rendement moyen ≥ la règle.
- **GAGNE** si rendement moyen > 0 **ET** p < 0,05. **NON DÉMONTRÉ** si > 0 sans p < 0,05. **PERD** sinon. **NON ÉVALUABLE** si moins de 20 trades (PREREG-46 en comptait ~46 crypto sur 7 mois de 2026, on en attend ~25-30 sur 4 mois) ou si le cron casse plus de 30 jours sans rattrapage possible.

## Relecture d'équité
Règle, N, période, filtre crypto et témoin fixés ici ; aucune prolongation. Le filtre crypto vient d'une observation après coup de PREREG-46 : il est déclaré, et c'est précisément pour cela que le juge est l'avenir. Le pool témoin est figé à la découverte (pas de choix après coup).

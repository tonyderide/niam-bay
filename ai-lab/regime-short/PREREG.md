# PREREG-24 : vendre les altcoins quand le BTC est sous son EMA200 rapporte-t-il ?

Écrit le 26/10/2026 vers 18h05 CET, **avant** tout téléchargement de données. Question de Tony après le short DOT du Martin local (+2,70 $ le 26/10) : « est-ce qu'il gagne, et pourquoi ? ».

## La règle testée (celle de Martin, sans réglage)
- Chaque heure, à la clôture de la bougie 1 h : si le BTC clôture **sous son EMA200 calculée sur les bougies 1 h**, on est **short** à poids égal sur les 10 altcoins ci-dessous pendant l'heure suivante. Sinon, on n'a aucune position.
- Pas de levier dans le calcul (les rendements sont par dollar engagé), pas de stop, pas d'objectif.
- Aucun paramètre n'est optimisé : EMA200 et bougies 1 h sont repris tels quels de `SignalService.java` de Martin.

## Données
- Contrats perpétuels Binance USDT-M (API publique `fapi/v1/klines` 1 h et `fapi/v1/fundingRate`), parce que Kraken ne fournit pas un historique 1 h aussi long.
- BTCUSDT pour le signal. Altcoins, liste figée : DOTUSDT, SOLUSDT, LINKUSDT, ADAUSDT, ETHUSDT, XRPUSDT, LTCUSDT, BNBUSDT, DOGEUSDT, AVAXUSDT.
- Période : 2020-10-01 00:00 UTC au 2026-10-25 23:00 UTC. Les 200 premières heures servent seulement à initialiser l'EMA.
- Une heure où un altcoin n'a pas de bougie : il est exclu de la moyenne pour cette heure-là.

## Coûts (les mêmes pour la règle et pour le témoin)
- 0,05 % par côté (taker Kraken Futures) sur la part du portefeuille qui change : entrer ou sortir coûte 0,05 %.
- Financement : le vrai taux Binance, à chaque échéance de 8 h passée en position. Un short **reçoit** le taux quand il est positif et **paie** quand il est négatif.

## Test (unilatéral, décidé maintenant)
- Statistique : rendement net moyen par heure de la règle, sur toute la période.
- Témoin : la même série de signal décalée circulairement dans le temps (décalage aléatoire d'au moins 30 jours, 2 000 tirages, graine 24). Le décalage garde exactement la même part de temps en position et le même nombre d'entrées et de sorties, donc les mêmes frais. Seul le moment change.
- p = (nombre de décalages ≥ la règle + 1) / 2 001.
- **DÉMONTRÉ** si p < 0,05 **et** rendement net total > 0. Sinon : **NON DÉMONTRÉ** (ce qui ne veut pas dire que ça ne marche jamais).

## Rapporté pour information (ne change pas le verdict)
- Résultat par année, et par moitié de période.
- « Toujours short » sans filtre, et le rendement sans frais.
- Variante journalière (EMA200 sur bougies 1 jour), présentée comme exploratoire.
- Le pire repli (drawdown).

## Addendum 1 (26/10 vers 18h12 CET) : demande de Tony, ajoutée après le téléchargement et AVANT tout calcul
Tony : « vérifier qu'au moins 3 des cryptos sont gagnantes et que le global des gains est supérieur au prix payé pour les frais ».
- Chaque altcoin est aussi évalué seul (même règle, même signal BTC, mêmes coûts, pour 1 $ engagé).
- Le verdict **DÉMONTRÉ** exige maintenant les 4 conditions à la fois :
  1. p < 0,05 au test des décalages (inchangé) ;
  2. rendement net total > 0 (inchangé) ;
  3. **au moins 3 des 10 altcoins gagnants** une fois les frais et le financement comptés ;
  4. **gains bruts (avant frais) > frais payés**, sur le portefeuille global. Le financement est compté à part et affiché.
- Si une seule condition manque : NON DÉMONTRÉ, avec la condition qui manque.

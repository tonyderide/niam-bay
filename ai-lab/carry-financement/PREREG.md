# PREREG-25 : le « carry » du financement rapporte-t-il après frais ?

Écrit le 27/10/2026 (heure du commit), AVANT tout calcul sur cette question. Les données sont celles déjà téléchargées pour PREREG-24 (`../regime-short/data/`), utilisées là-bas uniquement pour la règle EMA200, jamais pour regarder le financement en coupe.

## Idée
Sur les contrats perpétuels, quand une crypto a un financement très positif, les acheteurs à levier paient les vendeurs. La stratégie « carry » vend ces cryptos-là (on encaisse le financement) et achète celles où il est le plus bas. C'est un facteur décrit dans la littérature sur les cryptos. On teste s'il survit aux frais.

## Règle (aucun paramètre optimisé, valeurs fixées maintenant)
- Univers : les 11 perpétuels Binance USDT-M déjà téléchargés (BTC, DOT, SOL, LINK, ADA, ETH, XRP, LTC, BNB, DOGE, AVAX).
- Chaque jour à 00:00 UTC : on additionne les taux de financement des 7 jours précédents (paiements strictement avant 00:00) pour chaque crypto.
- **Short** les 3 plus élevés, **long** les 3 plus bas, à poids égal : 1 $ côté short, 1 $ côté long. Tenu 24 h, jusqu'au 00:00 UTC suivant.
- Rendement d'un jour = PnL de prix (clôtures 1 h de 00:00 à 00:00) + financement réellement payé ou reçu pendant les 24 h (le short reçoit un taux positif, le long le paie).
- Période : 2020-10-08 → 2026-10-25.

## Coûts
0,05 % par côté sur la part qui change à chaque rééquilibrage (taker Kraken Futures) ; entrée initiale et sortie finale comprises.

## Test et verdict (unilatéral)
- Statistique : rendement net total (prix + financement − frais).
- Témoin : la série des classements décalée circulairement dans le temps (décalage aléatoire d'au moins 30 jours, 2 000 tirages, graine 25). Même rotation, donc mêmes frais ; seul le moment change.
- **DÉMONTRÉ** si les 4 conditions tiennent (reprises des critères de Tony du 26/10) :
  1. p < 0,05 ;
  2. net total > 0 ;
  3. au moins 3 des 11 cryptos ont une contribution nette positive ;
  4. gains bruts (prix + financement, avant frais) > frais payés.
- Sinon NON DÉMONTRÉ, avec la condition qui manque.

## Pour information (ne change pas le verdict)
La part du prix et la part du financement, le résultat par année et par moitié, le pire repli, et la variante « financement seul » (si on encaissait le taux sans risque de prix).

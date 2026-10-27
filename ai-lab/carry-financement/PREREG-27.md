# PREREG-27 : le carry du financement survit-il sans le biais du survivant ?

Écrit le 27/10/2026 (heure du commit), AVANT de télécharger les données de cet univers. Suite de PREREG-25 (DÉMONTRÉ sur 11 cryptos choisies en 2026, donc parmi des survivantes).

## Univers « à l'époque » (sans savoir qui survivra)
- Liste de TOUS les perpétuels USDT-M ayant existé chez Binance : listing public `data.binance.vision` (data/futures/um/monthly/klines/), contrats morts compris.
- Chaque 1er janvier (2021, 2022, 2023, 2024, 2025, 2026) : les **30 contrats au plus gros volume en dollars** sur les 30 jours précédents (bougies journalières, volume quote), parmi ceux finissant en USDT et ayant au moins 60 jours d'historique. Cet univers est tenu toute l'année ; un contrat qui meurt en cours d'année sort du classement le jour où son prix manque (sa dernière journée compte).
- Exclus : BTCDOMUSDT et autres indices (DEFIUSDT, BLUEBIRDUSDT, FOOTBALLUSDT), qui ne sont pas des cryptos.

## Règle (identique à PREREG-25)
Chaque jour à 00:00 UTC : somme du financement des 7 jours précédents ; short les 3 plus élevés, long les 3 plus bas, 1 $ par côté, tenu 24 h. Prix : bougies journalières Binance (ouverture 00:00, clôture au 00:00 suivant). Financement réel pendant la détention. Frais 0,05 % par côté sur ce qui change.
Période : 2021-01-01 → 2026-10-27.

## Verdict (mêmes 4 conditions)
1. p < 0,05 au test des décalages (2 000 tirages, graine 27, décalage ≥ 30 jours, appliqué au classement) ;
2. net > 0 ;
3. au moins 3 contrats à contribution nette positive ;
4. bruts > frais.
Sinon NON DÉMONTRÉ.

## Pour information
Par année, sans les contrats morts (pour voir l'effet du biais), et la variante 5 contre 5.

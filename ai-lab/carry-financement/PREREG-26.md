# PREREG-26 : le carry du financement tient-il sur Kraken, puis en avant ?

Écrit le 27/10/2026 (heure du commit), après le verdict DÉMONTRÉ de PREREG-25 sur Binance, AVANT de télécharger les données Kraken.

## A. Réplication sur l'historique Kraken (tout ce que l'API publique fournit)
- Même règle que PREREG-25 : chaque jour à 00:00 UTC, somme du financement des 7 jours précédents (Kraken : taux horaire `relativeFundingRate`), short les 3 plus élevés, long les 3 plus bas, 1 $ par côté, tenu 24 h.
- Univers : PF_XBTUSD, PF_DOTUSD, PF_SOLUSD, PF_LINKUSD, PF_ADAUSD, PF_ETHUSD, PF_XRPUSD, PF_LTCUSD, PF_BNBUSD, PF_DOGEUSD, PF_AVAXUSD.
- Prix : bougies 1 h publiques de Kraken Futures (`api/charts/v1/trade/<symbole>/1h`), clôture à 00:00 UTC.
- Coûts : 0,05 % par côté sur ce qui change. Financement réel Kraken pendant la détention (le short reçoit un taux positif).
- Verdict : mêmes 4 conditions que PREREG-25 (p < 0,05 au test des décalages, 2 000 tirages, graine 26, décalage ≥ 30 jours ; net > 0 ; ≥ 3 cryptos gagnantes sur 11 ; bruts > frais).
- Ce n'est PAS indépendant dans le temps (la période recouvre 2025-2026 de Binance). C'est un test « autre marché, mêmes dates ».

## B. Test papier en avant (données jamais vues)
- Du mercredi 28/10/2026 00:00 UTC au mercredi 23/12/2026 00:00 UTC (8 semaines, 56 jours).
- Chaque jour vers 00:05 UTC, un script sur la VM (API publique, aucune clé, aucun ordre) note les positions papier du jour et le résultat de la veille.
- Verdict le 23/12 : net papier > 0 après frais, ET au moins 3 cryptos gagnantes. (Sur 56 jours, aucun test de p : trop court pour être concluant. Un net négatif voudra dire « pas confirmé », pas « faux ».)
- Aucun argent réel n'est engagé sans le OK explicite de Tony, quel que soit le résultat.

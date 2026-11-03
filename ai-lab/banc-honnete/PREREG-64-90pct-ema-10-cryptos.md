# Pré-enregistrement 64 : la règle à 90 % sur 10 cryptos, avec le sens donné par l'EMA
Écrit et commité le 03/11/2026 au soir, avant tout calcul de cette combinaison. Demande de Tony : « en prenant 10 crypto regardant l'ema ? ».

Déjà vu : PREREG-30 (autre sortie : SL 5 %, trailing 1 % dès +3 %) : NON DÉMONTRÉ, mais l'EMA évitait de se retourner à contre-tendance dans un krach. Ici la sortie est celle de PREREG-62, qui donne ~90 % de gagnants. Les 10 cryptos ont déjà été vues sans EMA, donc ce test n'est pas à l'aveugle sur elles.

## Règle
Sortie figée : SL 10 %, activation +1 %, trailing 0,5 %, frais 0,05 % par côté, 1 min, sans levier ni martingale, sans financement. **Sens de chaque nouveau trade : long si la dernière clôture horaire terminée est au-dessus de son EMA(N) horaire, short sinon.** Toujours en position.

## Choix de N (un seul)
N ∈ {20, 50, 200}. Meilleure espérance moyenne sur BTC, ETH, SOL, 01/02/2024 → 31/12/2025 (janvier 2024 = préchauffage). Ces 3 pièces ne servent qu'au choix pour ce verdict.

## Jugement
Les 10 pièces : XRP, DOGE, ADA, LINK, AVAX, LTC, BNB, DOT, BCH, ATOM. P1 = 01/02/2024 → 31/12/2025. P2 = 01/01 → 30/09/2026. Portefeuille = 10 parts égales, chacune indépendante, sans rééquilibrage.

## Verdict
- **« TIENT »** si sur P1 ET P2 : espérance moyenne > 0, plus de 5 pièces sur 10 positives, portefeuille > 0, et espérance moyenne supérieure à celle d'un sens tiré au hasard dans ≥ 95 % de 200 tirages.
- **« AMÉLIORE SANS SUFFIRE »** si l'espérance dépasse celle de l'inversion après perte (même sortie) sur P1 et P2, sans le reste.
- **« NON »** sinon.
Rapportés : gagnants, baisse médiane, résultat de BTC/ETH/SOL 2026, résultat cumulé P1 × P2.

## Résultat (03/11/2026, 21h2x — t64.py). N figé = 200
| 10 pièces | Gagnants | Espérance | Portefeuille | Pièces positives | Baisse médiane | Témoin battu |
|---|---|---|---|---|---|---|
| P1 EMA | 88,6 % | −0,149 % | −94,1 % | 0/10 | −96,6 % | 15,5 % |
| P1 inversion | 89,2 % | −0,056 % | −73,5 % | 0/10 | | |
| P2 EMA | 90,5 % | −0,041 % | −17,3 % | 2/10 | −56,9 % | 96,5 % |
| P2 inversion | 91,5 % | +0,079 % | +24,0 % | 6/10 | | |
**VERDICT (pré-enregistré) : « NON ».** Sur cette sortie, l'EMA fait moins bien que l'inversion sur les deux périodes. Portefeuille EMA cumulé P1 × P2 : −95 %.

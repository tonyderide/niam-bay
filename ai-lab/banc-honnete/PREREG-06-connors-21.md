# Pré-enregistrement 06 : RSI-2 de Connors sur 21 cryptos (1021 vers 01h00, avant calcul)
Pourquoi ce test : sur BTC, ETH et SOL (05c), Connors était positif sur les 2 périodes, avec 60 à 78 % de gagnants, mais avec trop peu de trades (39 et 7) pour pouvoir conclure. Tony a demandé de l'essayer sur plus de cryptos.
⚠️ **Deuxième regard sur la même stratégie** : ce test n'existe que parce que le premier avait l'air bon. On ne relâche rien sur le critère, et aucun réglage n'est modifié.

- Règles identiques à 05c : long seulement, close > SMA200 et RSI(2) < 10 ; sortie quand close > SMA5 ; bougies de 1 jour ; frais de 0,05 % par côté.
- Historique téléchargé à partir du 2022-11-01 pour que la SMA200 soit complète début 2024. Changement assumé : en 05c, la SMA200 n'était qu'en partie calculée au début de 2024.
- 21 marchés, ceux qui ont un historique journalier chez Kraken depuis fin 2022 : BTC ETH SOL XRP DOGE ADA LINK AVAX DOT LTC BCH UNI ATOM NEAR FIL AAVE APT OP TRX XLM ETC. Les marchés sans historique ont été écartés AVANT tout calcul (ARB, SUI, INJ).
- Hasard : entrées au hasard, en long, avec la même sortie (close > SMA5) et le même nombre de trades. 500 tirages.

GAGNE seulement si, sur 2024-2025 ET sur 2026 :
- la somme est > 0 ;
- au moins 60 % des marchés sont positifs ;
- le résultat dépasse le 95e centile du hasard ;
- on compte au moins 30 trades.

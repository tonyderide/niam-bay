# Écart de funding Hyperliquid / Kraken : mesure (2026-10-19 ~05h30)
500 heures communes (~21 jours, limite de l'API Hyperliquid). Signe : Hyperliquid paie plus que Kraken, donc on serait short sur Hyperliquid et long sur Kraken.
| coin | écart moyen | annualisé | même signe | net sur 30 j après 4 frais taker (0,20 %) | sur 3,8 $ |
|---|---|---|---|---|---|
| BTC | +0,00048 %/h | +4,2 %/an | 70 % des heures | **+0,14 %** | +0,0055 $ |
| ETH | +0,00037 %/h | +3,3 %/an | 68 % | +0,07 % | +0,0026 $ |
| SOL | +0,00036 %/h | +3,2 %/an | 56 % | +0,06 % | +0,0022 $ |
**Lecture** : il existe un petit écart **réel et assez stable** sur BTC (70 % des heures du même côté), de l'ordre de 4 %/an. Après frais, il reste ~0,14 % par mois, soit un demi-centime sur mon capital, ou ~1,4 € par mois sur 1000 €. Il faut y ajouter les risques non chiffrés ici : deux comptes, la liquidation d'une jambe, les transferts.
⚠️ À vérifier avant l'étape suivante : l'unité de `relativeFundingRate` chez Kraken. Je l'ai lue comme un taux horaire. Si c'est un autre pas de temps, tous les chiffres changent.
**Verdict du CTO** : la piste n°1 de la charte donne le **premier écart positif après frais** de toute la semaine, mais il est minuscule. Elle passe à l'étape 3 (pré-vol, puis test historique sur une autre période) et rien de plus : pas d'argent réel à 3,8 $.

# PREREG-78 — Lot de 100 idées nouvelles passées au bureau

Écrit le 21/11/2026 vers 23h, **avant tout calcul**. Demande de Tony : « cherche, teste 100 stratégies nouvelles et viens me dire quand tu as quelque chose ».

## Ce qui est testé
`idees.json` (produit par `generer.py`) : 100 idées figées, 65 sur actions/ETF en journalier (calendrier 16, retour à la moyenne 30, tendance 17, volatilité 2) et 35 sur crypto (10 perpétuels Kraken, 1d ou 4h).
Nouvelles = absentes du registre du bureau et des familles déjà jugées (PREREG-75 : grilles, tendance, retour à la moyenne, EMA sur 4 cryptos ; saisonnalité horaire crypto du 19/10). Certaines règles classiques (RSI 2, IBS, tournant du mois) sont connues ailleurs : c'est leur test chez nous, avec nos frais, qui est nouveau.
Deux idées ont été retirées avant tout calcul parce que la liste en comptait 102 (« vendredi fort » et « 3 hausses de suite » sur US).

## Règle (inchangée, celle du bureau)
Périodes : actions 2005-2015 et 2016-2026 ; crypto 2024-2025 et 2026 (jusqu'au 17/10). Frais 0,05 % par côté. Témoin : 500 tirages au hasard (même nombre de trades, mêmes sorties, mêmes sens possibles).
GAGNE si, dans chaque période : somme > 0, au moins 60 % des marchés positifs, somme > 95e centile du hasard, au moins 30 trades.

## Correction pour 100 essais (fixée maintenant)
Avec 100 idées, un GAGNE peut venir de la chance. Donc :
- **TROUVÉ** = GAGNE **et** rang ≥ 99e centile du hasard dans les deux périodes. Seul un TROUVÉ est annoncé à Tony comme « quelque chose ».
- GAGNE sans 99e centile = **candidat faible** : signalé, pas annoncé comme une trouvaille.
- Tout TROUVÉ ou candidat faible part en essai sur papier (30 trades ou 90 jours). **Aucun ordre réel**, quel que soit le résultat.
- Repère : si les idées étaient sans effet et indépendantes, on attendrait environ 100 × 0,05 × 0,05 ≈ 0,25 GAGNE par chance. Les idées sont corrélées (même règle sur plusieurs familles de marchés), donc ce repère est indicatif.
- Si aucun TROUVÉ : la réponse à Tony est « rien », avec le décompte.

## Relecture d'équité (écrite avant le calcul)
- **Pour les idées :** les familles de marchés bougent ensemble (60 % de marchés positifs est plus facile à atteindre qu'avec des marchés indépendants). La hausse de fond des actions aide les achats… mais aide aussi le témoin, qui achète au hasard.
- **Contre les idées :** 0,05 % par côté est cher pour des ETF très liquides (coût réel souvent 0,01-0,03 %) : les idées à 1 séance (IBS, lundi, ouverture en baisse) paient 0,1 % par trade et peuvent perdre un vrai petit effet. Les ventes à découvert d'actions ne comptent pas le coût d'emprunt (ce qui les avantage un peu). Entrée et sortie à l'ouverture, pas à la clôture : certaines règles classiques (IBS, RSI 2) sont décrites en clôture-à-clôture.
- **Biais de survie :** les ETF et secteurs choisis existent encore aujourd'hui ; les cryptos aussi (choisies parmi les grandes de 2026).
- **Neutre :** même règle et mêmes frais pour toutes les idées.

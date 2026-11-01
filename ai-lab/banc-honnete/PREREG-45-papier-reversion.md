# Pré-enregistrement 45 : la réversion transversale à 1 jour, en papier EN AVANT (03/11/2026 → 02/05/2027)
Écrit le 01/11/2026 vers 10h CET, avant le premier jour de données. Hypothèse H10 de FILE-HYPOTHESES.md, marquée « jugement en avant seulement » : PREREG-41 a montré **après coup** un fort renversement hebdomadaire en 2026 (momentum transversal −57,6 %, p = 1,00). Cette observation n'est pas un résultat ; le seul juge honnête est l'avenir. `scripts/cherche -v réversion un jour perdants veille transversal` : rien d'identique.

## Raison économique, et ce que dit la théorie avant les données
Prime de fourniture de liquidité : quand des vendeurs pressés (liquidations, sorties) font chuter une pièce plus que les autres, celui qui achète leur offre est payé par un rebond partiel le lendemain ; symétriquement pour les acheteurs pressés. Documenté sur les actions (Lehmann 1990, Lo & MacKinlay 1990) et sur les cryptos à court terme. Contre : forte rotation (les frais), et sur une marche aléatoire aucun classement de la veille n'a d'espérance. Prior : brut peut-être positif, net incertain.

## Univers (figé ici, `papier-reversion/univers.json`)
Les **50 perpétuels USDT-M de Binance au plus gros volume en dollars sur 24 h** au 01/11/2026 vers 09h50 CET, parmi ceux dont `underlyingType` = COIN (actions, matières premières, indices exclus), statut TRADING, symbole ASCII. Liste et volumes enregistrés dans univers.json. Une pièce retirée sort de l'univers le jour où elle n'a plus de bougie.

## Règle (aucun réglage)
- Chaque jour d à 00:00 UTC, parmi les pièces cotées la veille et ce jour : classement par rendement de la veille (ouverture → clôture du jour d − 1).
- **Long le quintile des plus fortes baisses, short le quintile des plus fortes hausses**, poids égaux, ½ par côté, tenu 24 h (ouverture → clôture du jour d).
- Frais taker 0,05 % sur chaque variation de poids. Sans funding.
- Limite connue : exiger une bougie le jour d suppose de savoir qu'une pièce ne sera pas retirée dans la journée (retraits annoncés d'avance chez Binance : effet négligeable).

## Journal
Prix publics seulement (`fapi/v1/klines`, 1d), recalcul complet à chaque passage (`reversion.py`, sans état), cron local à 03h27 Paris, ligne quotidienne dans `papier-reversion/journal.md`, commit local du journal et des données. Code vérifié sur des prix simulés avant ce commit (marche aléatoire : la règle et le jugement tournent, verdict PERD comme attendu). Pour information seulement : rien n'est décidé avant la fin.

## Jugement (UNIQUE, le 03/05/2027 ou après : `reversion.py juger`)
- Jours tenus : 03/11/2026 → 02/05/2027 inclus (181 jours).
- **Témoin à rotation égale** : paniers au hasard de mêmes tailles chaque jour, chaque pièce du panier de la veille gardée avec la probabilité égale au taux de conservation de la règle, mêmes frais ; 1 000 tirages, graine 45.
- **GAGNE** si net > 0 **ET** p < 0,05. **NON DÉMONTRÉ** si net > 0 sans p < 0,05. **PERD** sinon. Si le cron casse plus de 30 jours sans rattrapage possible : NON ÉVALUABLE.

## Relecture d'équité
Univers fixé par une règle mécanique avant le premier jour ; quintiles, 24 h, frais fixés ici ; aucune prolongation. Aucune action sur Martin ni Kraken, aucun compte, aucune clé.

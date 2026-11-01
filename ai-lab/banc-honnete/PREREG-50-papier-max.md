# Pré-enregistrement 50 : l'effet MAX en papier EN AVANT (semaines du 09/11/2026 au 26/04/2027)
Écrit le 01/11/2026 vers 23h CET, avant la première semaine jugée. Suite de PREREG-49 (**NON DÉMONTRÉ** : 2024-25 +26,8 %, p = 0,008 ; 2026 +2,5 %, p = 0,35 ; jamais négatif, bêta ≈ 0). Le juge que la période ne peut pas tromper : des semaines qui n'existent pas encore.

## Règle (celle de PREREG-49, aucun réglage)
- Chaque lundi 00:00 UTC : MAX = plus grand rendement journalier (clôture / clôture précédente − 1) des 30 jours précédents (au moins 25 rendements).
- **Short le quintile au MAX le plus fort, long le quintile au MAX le plus faible**, poids égaux, ½ par côté, une semaine (ouverture du lundi → ouverture du lundi suivant ; dernier prix si retrait). Taker 0,05 % sur chaque variation de poids. Sans funding.

## Univers (figé ici, `papier-max/univers.json`)
Les **150 perpétuels USDT-M de Binance au plus gros volume sur 24 h** au 01/11/2026, parmi `underlyingType` = COIN, statut TRADING, symbole ASCII, cotés depuis plus de 60 jours (512 éligibles). Différence avec PREREG-49 (253 pièces cotées au 01/01/2024) déclarée : univers plus actuel et plus liquide, choisi par une règle mécanique avant le premier jour.

## Journal
Cron local à 03h47 Paris, prix publics seulement (`fapi/v1/klines` 1d, historique depuis le 01/10/2026 pour le premier MAX), recalcul complet (`max.py`, sans état), une ligne par semaine terminée dans `papier-max/journal.md`, commit local. Code vérifié sur des prix simulés (marche aléatoire : 25 semaines, 30 pièces par côté, p = 0,45, comme attendu sans avantage). Pour information seulement : rien n'est décidé avant la fin.

## Jugement (UNIQUE, le 03/05/2027 ou après : `max.py juger`)
- 25 semaines (lundis du 09/11/2026 au 26/04/2027).
- **Témoin à rotation égale** (comme PREREG-41/44/45/48/49), 1 000 tirages, graine 50.
- **GAGNE** si net > 0 **ET** p < 0,05. **NON DÉMONTRÉ** si net > 0 sans p < 0,05. **PERD** sinon. NON ÉVALUABLE si le cron casse plus de 30 jours sans rattrapage possible.
- Puissance faible (25 semaines ; en 2026, 38 semaines n'avaient pas suffi) : un NON DÉMONTRÉ est probable même si l'effet existe ; c'est dit avant.

## Relecture d'équité
Règle, univers, période et témoin fixés ici ; aucune prolongation. Aucune action sur Martin ni Kraken, aucun compte, aucune clé.

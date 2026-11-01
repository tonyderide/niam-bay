# PREREG-42 : le carry du financement (PREREG-27) à rotation lente garde-t-il sa prime avec moins de frais ?
Écrit le 01/11/2026 vers 02h15 CET, avant tout calcul de cette variante. Hypothèse H7 de ai-lab/banc-honnete/FILE-HYPOTHESES.md. `scripts/cherche -v carry financement rotation lente hebdomadaire hystérésis maker frais` : rien d'identique (PREREG-33 rapportait une variante maker sur Hyperliquid, même rotation quotidienne).

## Raison économique, et ce que dit la théorie avant les données
Pas de nouvel avantage : la prime est celle de PREREG-27 (on reçoit le financement payé par les acheteurs à levier). Les frais en mangent une grosse part (PREREG-27 : 65,8 % de frais pour 437 % de bruts). Le financement est persistant (le signal à 7 jours change lentement) : réviser chaque semaine, et ne sortir une pièce que si elle a nettement quitté la tête du classement, devrait garder l'essentiel de la prime pour beaucoup moins de rotation. Risque : signal plus vieux, donc prime plus petite. Transparence : le carry de base de 2026 est connu (+94,3 %) ; la variante ne l'est pas.

## Données et carry de base
Identiques à PREREG-27 (`etude_univers.py`, data-univers/, univers top 30 chaque 1er janvier, morts compris, 3 contre 3, 1 $ par côté, prix journaliers, financement réel), du 01/01/2021 au 27/10/2026.

## Règle (une seule variante, aucune grille)
- **Révision chaque lundi** à 00:00 UTC seulement. Classement par la somme du financement des 7 jours précédents (comme PREREG-27), parmi les pièces éligibles du jour (mêmes critères).
- **Hystérésis** : un short déjà tenu est gardé tant que la pièce est dans les **6** plus hauts financements ; un long déjà tenu, tant qu'elle est dans les 6 plus bas. Les places libres (3 par côté) sont remplies par les meilleures pièces non tenues.
- Entre deux lundis, poids constants ; une pièce dont le prix manque (retrait) sort le jour même et sa place reste vide jusqu'au lundi.
- **Frais du verdict : taker 0,05 %** sur chaque variation de poids (comme PREREG-27). Pour information : la même variante en maker 0,02 % avec exécution supposée au prix d'ouverture (optimiste : les bougies journalières de data-univers n'ont pas de haut/bas pour vérifier la traversée).

## Verdict
- Les **4 conditions de PREREG-27** sur toute la période : p < 0,05 au test des décalages (**1 000** tirages, graine 42, décalage ≥ 30 jours appliqué à la série de poids), net > 0, ≥ 3 contrats à contribution positive, bruts > frais ;
- **ET** net de la variante > net du carry de base **en 2021-2025 ET en 2026** (jugement unique de l'amélioration : 2026).
- **GAGNE** si tout est vrai. **NON DÉMONTRÉ** si les 4 conditions tiennent mais pas l'amélioration sur les deux périodes, ou l'inverse. **PERD** si net 2026 ≤ 0 ou bruts ≤ frais.

## Rapporté
Net, prix, financement, frais, rotation (somme des |variations de poids|) contre la base ; par année ; Sharpe ; version maker (info).

## Relecture d'équité, avant calcul
- Lundi, 6 et 3 sont fixés ici (6 = 2 × 3, choix rond), pas ajustés.
- Le test des décalages est celui de PREREG-27, appliqué à la nouvelle série de poids.
- Aucune action sur Martin ni Kraken.

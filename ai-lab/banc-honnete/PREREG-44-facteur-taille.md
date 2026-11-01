# Pré-enregistrement 44 : le facteur taille (petites contre grandes pièces) paie-t-il après des coûts réalistes ?
Écrit le 01/11/2026 vers 09h CET, avant de télécharger les volumes et avant tout calcul. Hypothèse H9 de FILE-HYPOTHESES.md. `scripts/cherche -v facteur taille petites capitalisations volume illiquidité` : rien d'identique (voisins : pics de volume intrajournaliers, chasse-1019 et PREREG-23 — pas un facteur de taille).

## Raison économique, et ce que dit la théorie avant les données
Liu, Tsyvinski & Wu (2022) trouvent une prime de taille sur les cryptos : les petites rapportent plus, en rémunération de leur illiquidité et de leur risque. Contre : les coûts réels (écart achat-vente, impact) sont bien plus élevés sur les petites, et les perpétuels de petites pièces ont beaucoup de retraits (morts compris ici). Prior : **plutôt PERD** après coûts.

## Données
- Prix : ceux de PREREG-39/41 (253 perpétuels USDT-M Binance cotés au 01/01/2024, morts compris, 1 h → jours → semaines du lundi, `couper`).
- **Taille** (pas de capitalisation disponible) : **volume en dollars** sur 30 jours, à télécharger après ce commit depuis `data.binance.vision` (klines 1d mensuelles, colonne « quote volume », somme SHA-256 vérifiée, même source que les prix).

## Règle (aucun réglage)
- Chaque lundi, parmi les pièces vivantes ayant 30 jours de volume passé : classement par volume en dollars des 30 jours précédents.
- **Long le quintile des plus petits volumes, short le quintile des plus gros**, poids égaux, ½ par côté, une semaine (rendement ouverture du lundi → ouverture du lundi suivant ; dernier prix si retrait).
- Coûts : taker 0,05 % sur chaque variation de poids, **plus 0,10 % de glissement par variation sur la jambe des petites** (illiquidité). Sans funding.

## Jugement
- Historique : semaines commençant du 05/02/2024 (30 jours de volume) au 29/12/2025. **JUGEMENT UNIQUE : 05/01/2026 → 21/09/2026.**
- **Témoin à rotation égale** (comme PREREG-41) : paniers au hasard de mêmes tailles, conservation des noms au même taux que la règle, mêmes coûts (glissement appliqué au côté long), 1 000 tirages, graine 44.
- **GAGNE** si net > 0 sur l'historique **ET** > 0 en 2026 **ET** p < 0,05 en 2026. **NON DÉMONTRÉ** si net 2026 > 0 sans le reste. **PERD** sinon.

## Rapporté
Net, brut, coûts, jambes séparées, semaines positives, pire semaine, pire baisse, retraits dans la jambe des petites, sans le glissement (info).

## Relecture d'équité, avant calcul
- Quintiles, 30 jours, 0,10 % de glissement fixés ici.
- Morts compris : une petite qui meurt garde sa perte (dernier prix).
- Aucune action sur Martin ni Kraken.

## Résultat (01/11/2026, 09h2x — t44_volumes.py puis t44.py → t44.log, chiffres dans t44.json)
Volumes : 253 symboles, 8 199 archives mensuelles vérifiées (403 absentes : pièces pas encore ou plus cotées). Calcul lancé une seule fois après le commit c0b6e9a, `nice -n 10`. Quintiles de ~42 (historique) et ~36 (2026) pièces par côté ; les classements de taille bougent peu (≈ 90 % des noms gardés d'une semaine à l'autre).

| | Historique (02/2024 → 12/2025) | **2026** |
|---|---|---|
| Net | −0,1 % | **−3,1 %** |
| Brut / coûts | +2,0 / 2,1 | −2,1 / 0,9 |
| Jambe petites (long) / jambe grandes (short) | −1,3 / +3,3 | −4,7 / +2,6 |
| Sans glissement (info) | +1,1 % | −2,5 % |
| Semaines positives | 46 % | 53 % |
| Pire baisse | 11,6 pts | 9,1 pts |
| Témoin à rotation égale | +1,5 ± 12,4 % | −2,1 ± 8,4 % |
| p | 0,57 | **0,56** |

**VERDICT (pré-enregistré) : PERD** — net négatif sur les deux périodes, indiscernable du hasard.

**Ce que ça montre :**
- Pas de prime de taille sur les perpétuels Binance de 2024-2026 : les petites pièces n'ont pas fait mieux que les grosses, même **avant** coûts (jambe des petites négative sur les deux périodes).
- L'écart de rendement tient en quelques points sur près de trois ans, à côté d'un hasard de ±8 à 12 points : il n'y a rien à mesurer. La prime académique (2014-2018, marché au comptant, beaucoup de micro-pièces) ne se retrouve pas ici.

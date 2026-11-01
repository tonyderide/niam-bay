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

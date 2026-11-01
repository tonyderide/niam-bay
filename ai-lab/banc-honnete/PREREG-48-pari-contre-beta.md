# Pré-enregistrement 48 : parier contre le bêta (long les pièces peu sensibles à BTC, short les très sensibles, à bêta neutre)
Écrit le 01/11/2026 vers 18h CET, avant tout calcul. Hypothèse H12 de FILE-HYPOTHESES.md. `scripts/cherche -v faible volatilité bêta anomalie` : rien d'identique (voisins : cible de volatilité, grille en volatilité, vol gérée — aucun classement par bêta entre pièces).

## Raison économique, et ce que dit la théorie avant les données
Frazzini & Pedersen (2014) : les investisseurs qui ne peuvent pas (ou ne veulent pas) s'endetter achètent les actifs à fort bêta pour avoir du rendement ; ces actifs deviennent trop chers et rapportent moins par unité de risque. Un portefeuille long faible bêta (avec levier) et short fort bêta (sans levier), à bêta nul, encaisse cette prime. Sur crypto le levier est facile (perpétuels) : la contrainte qui crée la prime est faible. Prior : **plutôt PERD** — d'où l'intérêt d'un vrai test.

## Données
Celles de PREREG-39/41/44 (253 perpétuels Binance cotés au 01/01/2024, morts compris, 1 h → jours → semaines du lundi, `couper`). BTCUSDT sert de marché.

## Règle (aucun réglage)
- Chaque lundi : bêta de chaque pièce vivante contre BTC sur ses **60 derniers rendements journaliers** (régression simple ; au moins 50 jours présents ; BTC exclu du classement).
- **Long le quintile au bêta le plus faible, short le quintile au plus fort.** Poids d'une pièce = (1 / nombre de pièces du côté) / bêta moyen du côté, plafonné à 3 (chaque côté a un bêta de 1, le portefeuille un bêta ≈ 0) ; les pièces au bêta ≤ 0,1 sont exclues du côté long (levier infini).
- Une semaine (ouverture du lundi → ouverture du lundi suivant ; dernier prix si retrait). Frais taker 0,05 % sur chaque variation de poids. Sans funding.

## Jugement
- Historique : semaines du 04/03/2024 au 29/12/2025. **JUGEMENT UNIQUE : 05/01/2026 → 21/09/2026.**
- **Témoin à rotation égale** (comme PREREG-41/44) : paniers au hasard de mêmes tailles, même taux de conservation, **pondérés de la même façon par leurs propres bêtas** ; 1 000 tirages, graine 48.
- **GAGNE** si net > 0 sur l'historique **ET** > 0 en 2026 **ET** p < 0,05 en 2026. **NON DÉMONTRÉ** si net 2026 > 0 sans le reste. **PERD** sinon.

## Rapporté
Net, brut, frais, jambes, bêta réalisé du portefeuille (régression des rendements hebdo sur BTC), levier moyen du côté long, semaines positives, pire baisse.

## Relecture d'équité
60 jours, quintiles, plafond 3, seuil 0,1 fixés ici. Le témoin garde la pondération par bêta et les frais ; il ne retire que le classement. Aucune action sur Martin ni Kraken.

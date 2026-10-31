# Pré-enregistrement 37 : la prime de variance (vendre la volatilité implicite de BTC et ETH) rapporte-t-elle après frictions, et à quel prix de queue ?
Écrit le 31/10/2026 vers 19h CET, avant tout téléchargement de DVOL et avant tout calcul. Hypothèse H2 de FILE-HYPOTHESES.md. `scripts/cherche -v prime de variance volatilité implicite réalisée options vendre` : rien d'identique (voisins : grille en volatilité PREREG-12, cible de volatilité chasse-1019, vol gérée PREREG-13 — aucun ne vend de la volatilité implicite).

## Raison économique, et ce que dit la théorie avant les données
Les acheteurs d'options paient une assurance : en moyenne, la volatilité implicite dépasse la volatilité réalisée (prime de variance, documentée sur les actions — Carr & Wu 2009 — et sur les options crypto de Deribit). Le vendeur est payé pour porter le risque de krach. Ce n'est **pas** une règle de sortie sur une marche aléatoire : c'est un prix d'assurance. Mais la distribution est asymétrique : beaucoup de petits gains, de rares grosses pertes. Prior : moyenne positive très probable ; la question honnête est la taille de la queue. **Recherche seulement** : aucun compte d'options, aucun ordre.

## Données (publiques, sans clé)
- Indice DVOL de Deribit (volatilité implicite à 30 jours, BTC et ETH), journalier : `public/get_volatility_index_data`, depuis le premier jour disponible.
- Comptant Binance BTCUSDT et ETHUSDT, bougies 1 h (`api/v3/klines`).

## Règle (aucun réglage)
- **Swap de variance synthétique à 30 jours**, vendu chaque jour t à 00:00 UTC. Prix d'exercice K = (DVOL_t − 2)² (DVOL en points de % annualisés, ouverture du jour t ; les **2 points** retirés représentent les frictions : écart achat-vente des options et réplication imparfaite, prudent pour Deribit BTC/ETH).
- Variance réalisée RV² = somme des carrés des rendements log horaires du comptant de t à t + 30 jours (720 heures) × 8 760 / 720, en %².
- Gain par unité de notionnel de variance, normalisé : **g = (K − RV²) / K** (1 = on garde toute la prime ; −2 = la réalisée a été 3× la variance vendue). Frais supplémentaires : aucun (inclus dans les 2 points).
- Deux séries : (a) **journalière chevauchante** (moyennes, p) ; (b) **mensuelle sans chevauchement** (un swap tous les 30 jours à partir du premier jour commun, pour la queue : pire mois, CVaR 5 %).
- Pour information : la version « volatilité » (swap de vol) g_v = ((DVOL − 2) − RV) / (DVOL − 2), moins exposée à la queue.

## Périodes et jugement
- Historique : premier jour DVOL → swaps entrés jusqu'au 31/12/2025.
- **JUGEMENT UNIQUE : swaps entrés du 01/01/2026 au 30/09/2026** (sortie au plus tard le 30/10/2026).
- **Témoin au hasard** : bootstrap par blocs (blocs de 30 jours, 10 000 tirages) de la série journalière **centrée** (moyenne retirée) : p = part des tirages dont la moyenne ≥ la moyenne observée. C'est le test de « la prime moyenne est-elle nulle ? » avec l'autocorrélation due au chevauchement.
- **GAGNE** si, pour BTC **et** pour ETH, la moyenne de g est > 0 sur l'historique **ET** > 0 en 2026 **ET** p < 0,05 en 2026.
- **NON DÉMONTRÉ** si la moyenne 2026 est > 0 pour les deux sans tout le reste.
- **PERD** sinon.
- **Mention de queue (pré-enregistrée, ajoutée au verdict sans le changer)** : « RISQUE DE QUEUE » si, sur l'historique mensuel sans chevauchement, la pire perte d'un mois (−g) dépasse 12 fois le gain mensuel moyen (une année de prime effacée en un mois).

## Rapporté
Par pièce et période : moyenne et médiane de g, part de swaps gagnants, pire mois, CVaR 5 % mensuelle, nombre de mois à g < −1, DVOL moyen contre volatilité réalisée moyenne, version swap de vol.

## Relecture d'équité, avant calcul
- Aucun paramètre choisi sur les données (2 points de frictions, 30 jours, 00:00 UTC fixés ici).
- Approximation reconnue : DVOL ≈ racine du prix d'un swap de variance à 30 jours (formule de type VIX) ; la réalisée Binance comptant ≠ l'indice Deribit exactement (écart faible). Les 2 points jouent contre la vente.
- Un vendeur réel aurait besoin de marge ; le gain normalisé ne dit pas le levier. La mention de queue est là pour ça.
- Aucune action sur Martin ni Kraken.

## Résultat (31/10/2026, 19h3x — t37.py → t37.log, chiffres complets dans t37.json)
Lancé une seule fois après le commit bd0e880, `nice -n 10`. DVOL disponible depuis le 24/03/2021 pour les deux pièces. g = part de la variance vendue qu'on garde (1 = toute ; −1 = la réalisée a été le double de la vendue).

| | BTC historique | **BTC 2026** | ETH historique | **ETH 2026** |
|---|---|---|---|---|
| Swaps journaliers | 1 744 | 273 | 1 744 | 273 |
| g moyen | **+0,135** | **−0,144** | **−0,017** | **−0,034** |
| g médian | +0,27 | +0,04 | +0,13 | +0,14 |
| Swaps gagnants | 72 % | 53 % | 62 % | 62 % |
| Pire swap | −2,0 | −2,1 | −3,6 | −1,6 |
| CVaR 5 % (journaliers) | −1,05 | −1,80 | −1,66 | −1,49 |
| p (bootstrap par blocs) | < 0,001 | 0,83 | 0,61 | 0,61 |
| DVOL moyen / réalisée moyenne | 62,4 / 53,4 | 43,0 / 41,9 | 76,1 / 70,6 | 59,4 / 55,6 |
| Swap de vol (info), g_v moyen | +0,096 | −0,038 | +0,026 | +0,015 |

Mensuels sans chevauchement : BTC historique +0,145 par mois (pire −0,87) ; ETH historique −0,021 (pire **−2,68**, avril 2021). Pires mois toutes périodes : BTC −1,99 (entré le 27/01/2026), −1,34 (27/05/2026) ; ETH −2,68 (23/04/2021), −1,58 (01/02/2025), −1,56 (27/01/2026).

**VERDICT (pré-enregistré) : PERD — avec mention RISQUE DE QUEUE** (ETH : pire mois −2,68 contre un gain mensuel moyen négatif). La moyenne 2026 est négative pour BTC et pour ETH.

**Ce que ça montre :**
- La prime existe **en médiane** (la plupart des mois, l'implicite dépasse la réalisée de quelques points) et sur BTC 2021-2025 elle était nette et significative (+13,5 % de la variance vendue, p < 0,001).
- Mais après 2 points de frictions, elle est **trop mince pour payer la queue** : 2026 a eu deux mois où la réalisée a dépassé ~1,7× l'implicite (janvier et mai), et ils effacent l'année. Sur ETH, elle n'a jamais été positive en moyenne après frictions.
- En 2026 l'implicite (43 sur BTC) ne dépassait la réalisée (42) que d'un point : moins que les frictions. La prime s'est comprimée, comme le basis (PREREG-36).
- C'est le profil classique « ramasser des pièces devant un rouleau compresseur » : 53-72 % de mois gagnants, des pertes de 1,5 à 3,6 fois la prime. Rien à en faire pour Martin.

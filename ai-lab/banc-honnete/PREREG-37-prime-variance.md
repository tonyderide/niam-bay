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

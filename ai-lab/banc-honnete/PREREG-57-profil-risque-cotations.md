# Pré-enregistrement 57 : le prix du risque du short des nouvelles cotations, en portefeuille couvert (2021-2026)
Écrit le 02/11/2026 vers 16h CET, avant tout calcul. Hypothèse H20 de FILE-HYPOTHESES.md. Pas un nouvel avantage : l'effet est démontré (PREREG-46) et répliqué trois fois (53, 54, 56). La question est de savoir si on peut le **porter** sans être ruiné : PREREG-56 a montré 13 % de trades à −100 % et une cohorte 2023 à −37 %.

## Portefeuille (aucun réglage)
- Données : perpétuels USDT-M Binance de data-univers/klines.json (morts compris quand Binance les sert), financement listings/funding.json ; **crypto seulement** (contrats non-COIN de listings/exchangeInfo-20261101.json retirés). 01/01/2021 → 26/10/2026.
- **Jambe courte** : chaque nouvelle cotation est shortée de l'ouverture de sa 2e bougie à la clôture de sa 90e (ou à sa dernière bougie si retrait), comme PREREG-46. Chaque jour, la jambe courte totale vaut **1** (poids −1/n sur les n shorts ouverts) ; jour sans short ouvert : jambe vide.
- **Jambe longue (couverture)** : panier égal des pièces cotées depuis plus de 365 jours et cotées ce jour, total **+1** les jours où la jambe courte existe, 0 sinon.
- Rendement du jour = Σ poids × (clôture / ouverture − 1) − financement payé (long) + reçu (short) − 0,05 % × Σ |variation de poids| (rééquilibrage quotidien aux poids égaux, dérive intrajournalière ignorée). Capital = 1 (levier brut 2).

## Mesures
Rendement annualisé, Sharpe (moyenne/écart-type quotidiens × √365), pire baisse, pire mois, mois négatifs, par année ; même chose pour le short seul (sans couverture), pour information.

## Critère (pré-enregistré)
- **RISQUE MAÎTRISÉ** si, sur 2021-2026 : Sharpe > 1,0 **ET** pire baisse < 30 % **ET** pire mois > −15 % **ET** rendement 2026 > 0 **ET** p < 0,05 contre le témoin.
- **RISQUE NON MAÎTRISÉ** sinon (même si l'effet moyen existe).
- **Témoin** : même portefeuille où chaque short d'une nouvelle cotation est remplacé par le short d'une pièce ancienne tirée au hasard (cotée depuis plus de 365 jours) sur la même fenêtre ; 200 tirages, graine 57 ; p = part des tirages au Sharpe ≥ celui du portefeuille.

## Relecture d'équité
Règles reprises de PREREG-46 ; poids égaux et couverture 1:1 fixés ici, sans essai d'autres. Limites : bêta non ajusté (les jetons neufs bougent plus que le panier), exécution au prix d'ouverture, liquidité des jetons neufs non modélisée (petites tailles seulement). Aucun ordre, aucun compte, aucune clé, aucune action sur Martin ni Kraken.

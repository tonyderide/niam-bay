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

## Résultat (02/11/2026, 17h — t57.py → t57.log, chiffres dans t57.json ; diagnostic t57_diag.py → t57_diag.log)
Lancé une seule fois après le commit 2e6b255, `nice -n 10`. 632 nouvelles cotations crypto shortées, ~25 shorts ouverts en moyenne, jambe courte présente tous les jours.

| | 2021-2026 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| Rendement annualisé | **−32,8 %** | −91,6 % | +70,8 % | +27,4 % | +8,2 % | −46,0 % | −8,1 % |
| Sharpe | **−0,25** | −1,58 | 1,18 | 0,75 | 0,41 | −0,94 | 0,10 |
| Pire baisse | **93 %** | 92 % | 48 % | 32 % | 32 % | 69 % | 43 % |
| Pire mois | **−63 % (2021-01)** | | −33 % | −13 % | −15 % | −31 % | −23 % |

Mois négatifs : 35/70. Témoin (shorts de pièces anciennes aux mêmes fenêtres) : Sharpe −0,03 ± 0,39 ; p = 0,71.

**VERDICT (pré-enregistré) : RISQUE NON MAÎTRISÉ** — Sharpe négatif, pire baisse de 93 %, pire mois de −63 %, 2026 négatif.

## Diagnostic après le verdict (information) : la construction a tué l'effet
- `t57_diag.py`, sur les mêmes 632 trades, sans couverture ni financement : **short tenu** (quantité fixée à l'entrée, comme PREREG-46) **+23,3 % par trade** (médiane +38,3 %) ; **short remis chaque jour au même poids** (ce que fait le portefeuille pré-enregistré) **−1,0 %** (médiane −15 %).
- Raison : un short rééquilibré chaque jour à poids fixe subit un frottement de volatilité d'environ σ² par jour (comme un produit inverse à levier −1). Les jetons neufs ont une volatilité de l'ordre de 8 %/jour : sur 90 jours, ce frottement (≈ 0,0064 × 90 ≈ 58 %) dépasse largement la baisse moyenne. Le short tenu, lui, garde sa quantité : quand le prix baisse son exposition diminue (le gain est acquis), sans racheter ni revendre chaque jour, donc sans ce frottement.
- Donc ce verdict dit : « porté en poids égaux rééquilibrés chaque jour, l'effet est détruit et le risque n'est pas maîtrisé ». Il ne dit pas ce que donne un portefeuille de shorts **tenus**. C'est une autre construction, à pré-enregistrer avant de la calculer (H22).

## CORRECTION (02/11/2026, 19h) — bug dans le panier des pièces anciennes, calcul relancé
- **Bug** : les données Binance commencent au 01/09/2020 ; une pièce déjà cotée avant avait pour « première bougie » le 01/09/2020, donc la règle « cotée depuis plus de 365 jours » ne la classait ancienne qu'à partir de septembre 2021. Jusque-là, **la couverture était vide** (shorts non couverts en 2021) et le témoin tirait dans un panier réduit. Trouvé en faisant tourner PREREG-58 (même code). Correction : une pièce présente dès le premier jour des données est ancienne (`DEBUT_DONNEES` dans t57.py). Résultat d'avant conservé dans t57_avant_correction.log / .json.
- **Après correction** (t57.log, t57.json) : 2021-2026 rendement **+0,8 %/an**, Sharpe **0,29**, pire baisse **79 %**, pire mois **−35 % (2021-03)** ; par année : 2021 −11,8 % · 2022 +70,8 % · 2023 +27,4 % · 2024 +8,2 % · 2025 −46,0 % · 2026 −8,1 % ; témoin p = 0,21.
- **Le verdict ne change pas : RISQUE NON MAÎTRISÉ.** Le diagnostic (le rééquilibrage quotidien détruit l'effet) n'est pas touché : il compare les trades un par un, sans couverture.

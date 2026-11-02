# Pré-enregistrement 55 : acheter BTC le lendemain d'un jour de krach rapporte-t-il ?
Écrit le 02/11/2026 vers 13h CET, avant tout calcul. Hypothèse H18 de FILE-HYPOTHESES.md. `scripts/cherche -v krach journalier acheter après liquidations rebond marché` : voisins PREREG-23 (pic de volume vendeur en intrajournalier sur BTC, NON DÉMONTRÉ) et PREREG-43 (levier de la foule) ; l'achat au lendemain d'une forte baisse journalière n'a jamais été testé. Les prix BTC journaliers (t51_btc.json, PREREG-51) sont déjà sur le disque mais aucun calcul de baisse n'y a été fait.

## Raison économique, et ce que dit la théorie avant les données
Un jour de krach sur BTC est souvent un jour de liquidations forcées : des vendeurs qui ne choisissent pas leur prix. Celui qui fournit la liquidité le lendemain est payé par un rebond partiel (prime de liquidité, Nagel 2012 sur les actions). Contre : les krachs viennent en grappes (la baisse peut continuer), et sur une marche aléatoire le lendemain n'a pas d'espérance. Prior : incertain.

## Données
Binance comptant BTCUSDT journalier, 17/08/2017 → 31/10/2026 (t51_btc.json ; même source publique).

## Règle (aucun réglage)
- Jour de krach : rendement du jour (clôture / ouverture − 1) **< −7 %**.
- Achat à l'**ouverture du lendemain**, vente à la **clôture du 3e jour** (jours J+1 à J+3). Un nouveau krach pendant la tenue ne relance pas de position (pas de chevauchement).
- Frais 0,10 % par côté.

## Jugement
- **Témoin** : autant de fenêtres de 3 jours, commençant à des jours tirés au hasard (hors fenêtres de la règle), mêmes frais ; 1 000 tirages, graine 55.
- Périodes : **A = 2017-2023** et **B = 2024 → 10/2026** (B a peu de krachs : faible puissance, dit avant).
- **GAGNE** si moyenne > 0 et p < 0,05 dans A, **ET** moyenne > 0 dans B, **ET** p < 0,05 sur A + B réunis. **NON DÉMONTRÉ** si moyenne > 0 sur A + B sans le reste. **PERD** sinon.

## Rapporté
Nombre de krachs par année, rendement moyen et médian, part positive, pire fenêtre ; pour information, même règle sur le panier égal des 253 perpétuels 2024-2026 avec un seuil de −10 %.

## Relecture d'équité
Seuil −7 %, 3 jours fixés ici (ordre de grandeur d'un jour de liquidations sur BTC), pas ajustés. Aucune action sur Martin ni Kraken.

## Résultat (02/11/2026, 13h3x — t55.py → t55.log, chiffres dans t55.json ; t55_panier.py → t55_panier.log)
Lancé une seule fois après le commit 39ca256, `nice -n 10`. 66 krachs (jours < −7 %) sans chevauchement.

| | Krachs | Moyenne (J+1 → J+3, frais compris) | Médiane | Positifs | Pire | Témoin (3 jours au hasard) | p |
|---|---|---|---|---|---|---|---|
| A : 2017-2023 | 60 | **−0,39 %** | −1,57 % | 47 % | −23,1 % | +1,03 % | 0,97 |
| B : 2024 → 10/2026 | 6 | +5,60 % | +3,45 % | 83 % | −0,8 % | +0,06 % | 0,001 |
| A + B | 66 | +0,16 % | −0,19 % | 50 % | −23,1 % | +0,71 % | 0,80 |

Par année : 2018 (16 krachs) surtout négatif, 2021 (13) surtout positif, 2022 (10) surtout négatif — le rebond suit l'année, pas le krach. Information, panier égal des 253 perpétuels 2024-2026, seuil −10 % : 12 krachs, moyenne +1,6 % sur 3 jours (7 négatifs sur 12).

**VERDICT (pré-enregistré) : NON DÉMONTRÉ** — la moyenne sur A + B est positive (+0,16 %) mais ni A (−0,39 %, p = 0,97) ni l'ensemble (p = 0,80) ne battent le hasard.

**Ce que ça montre :**
- Sur 2017-2023, acheter le lendemain d'un krach fait **moins bien** que trois jours pris au hasard : les krachs de BTC viennent en grappes, la baisse continue aussi souvent qu'elle rebondit.
- Les 6 krachs de 2024-2026 ont tous rebondi (p = 0,001), mais 6 cas après 60 qui disaient le contraire ne font pas une règle : c'est l'exemple même d'un résultat à ne pas croire sans test en avant.
- Le verdict NON DÉMONTRÉ (et pas PERD) vient de la règle écrite (moyenne A + B > 0) ; sur le fond, il n'y a pas d'avantage.

# Pré-enregistrement 51 : le tournant du mois sur BTC (long des 2 derniers jours aux 3 premiers jours du mois)
Écrit le 02/11/2026 vers 00h50 CET, avant de télécharger les données et avant tout calcul. Hypothèse H14 de FILE-HYPOTHESES.md. `scripts/cherche -v tournant du mois début de mois BTC saisonnalité calendrier` : voisins saisonnalite-btc (mois de l'année, descriptif, non concluant) et chasse-1019/saisonnalite-horaire (heures et jours de semaine) ; le tournant du mois n'a jamais été testé.

## Raison économique, et ce que dit la théorie avant les données
Sur les actions, les rendements se concentrent autour du changement de mois (Ariel 1987 ; Lakonishok & Smidt 1988) : salaires, achats programmés, rééquilibrages de fonds arrivent à date fixe. Sur BTC, les achats récurrents (DCA) des plateformes et, depuis 2024, les flux des ETF au comptant sont des flux à date. Contre : un effet de calendrier connu de tous devrait être arbitré ; 12 fenêtres par an seulement, puissance faible. Prior : plutôt NON DÉMONTRÉ.

## Données (publiques, sans clé)
Binance comptant BTCUSDT, bougies journalières (`api/v3/klines`), du 17/08/2017 (début de la cote) au 31/10/2026.

## Règle (aucun réglage)
- Fenêtre de chaque changement de mois : achat à l'**ouverture de l'avant-dernier jour** du mois, vente à la **clôture du 3e jour** du mois suivant (5 jours UTC). Hors fenêtre : rien.
- Frais 0,10 % par côté (taker comptant de base).
- Mesure : rendement net moyen par fenêtre.

## Jugement
- Historique : fenêtres dont le mois suivant va de 10/2017 à 12/2025. **JUGEMENT UNIQUE : fenêtres de 01/2026 à 10/2026** (10 fenêtres).
- **Témoin** : pour chaque fenêtre, une fenêtre de 5 jours de même mois de départ, **commençant un jour tiré au hasard** du mois (hors fenêtre réelle), mêmes frais ; 1 000 tirages, graine 51. p = part des tirages à moyenne ≥ la règle.
- **GAGNE** si moyenne > 0 sur l'historique **ET** > 0 en 2026 **ET** p < 0,05 en 2026. **NON DÉMONTRÉ** si > 0 en 2026 sans le reste. **PERD** sinon.
- Puissance faible (10 fenêtres jugées) : dit avant.

## Rapporté
Moyenne, médiane, part positive, par année ; p historique (info) ; acheter-garder BTC sur les mêmes périodes ; part du rendement total de BTC capturée en 5/30 du temps.

## Relecture d'équité
Fenêtre −2/+3 fixée ici (la plus courante dans la littérature, sans essai d'autres). Aucune action sur Martin ni Kraken.

## Résultat (02/11/2026, 00h5x — t51.py → t51.log, chiffres dans t51.json, prix dans t51_btc.json)
Lancé une seule fois après le commit b7e3e7f, `nice -n 10`. 109 fenêtres (10/2017 → 10/2026).

| | Historique (99 fenêtres, 10/2017 → 12/2025) | **2026 (10 fenêtres)** |
|---|---|---|
| Rendement net moyen par fenêtre | +1,42 % | **−0,60 %** |
| Médiane / fenêtres positives | +0,35 % / 55 % | +1,27 % / 70 % |
| Témoin (fenêtre au hasard, même mois) | +0,50 % | +0,12 % |
| p | 0,115 (info) | **0,67** |

Par année : 2018 +0,1 % · 2019 +3,5 % · 2020 +2,5 % · 2021 +5,3 % · 2022 −0,9 % · 2023 −0,8 % · 2024 −1,7 % · 2025 +1,2 % · 2026 −0,6 %. Fenêtres 2026 : deux fortes pertes (février −10,7 %, juin −12,9 %) effacent sept petits gains.

**VERDICT (pré-enregistré) : PERD** — moyenne 2026 négative ; même l'historique ne bat pas le hasard (p = 0,115).

**Ce que ça montre :**
- L'effet a peut-être existé en 2019-2021 (années haussières, beaucoup de flux particuliers), mais il ne bat pas des fenêtres au hasard sur l'historique, et il est négatif ou nul en 2022-2024 et 2026.
- Avec 12 fenêtres par an, un ou deux mouvements violents décident de l'année : un effet de calendrier de quelques dixièmes de point ne peut pas se voir sur BTC.

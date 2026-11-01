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

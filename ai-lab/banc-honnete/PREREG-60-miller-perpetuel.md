# Pré-enregistrement 60 : quand Binance ouvre un perpétuel sur une pièce déjà ancienne au comptant, son prix baisse-t-il ensuite ? (Miller 1977)
Écrit le 03/11/2026 vers 00h50 CET, avant tout calcul. Hypothèse H23 de FILE-HYPOTHESES.md. `scripts/cherche -v vente à découvert contrainte Miller cotation du perpétuel` : rien d'identique (seuls voisins : les tests sur les jetons neufs, où la pièce elle-même est nouvelle).

## Raison économique, et ce que dit la théorie avant les données
Miller (1977) : tant que la vente à découvert est impossible ou chère, le prix reflète les acheteurs les plus optimistes ; quand elle devient facile, les pessimistes entrent et le prix baisse. Sur les actions, l'introduction d'options ou l'autorisation de vente à découvert précède des rendements plus faibles. Ici : une pièce cotée au comptant depuis au moins 180 jours obtient un perpétuel chez Binance — l'accès au short change, pas la pièce. Prior : effet petit, plutôt NON DÉMONTRÉ (d'autres plateformes offraient souvent déjà un short).

## Données (déjà là)
- Comptant : ai-lab/banc-honnete/comptant/klines.json (paires USDT, 2017-08 → 2026-09, morts compris par les archives).
- Perpétuels : ai-lab/carry-financement/data-univers/klines.json ; date d'ouverture = première bougie, seulement après le 02/09/2020 (début des données) ; contrats non-COIN exclus (listings/exchangeInfo-20261101.json). Correspondance perpétuel → comptant : XUSDT → XUSDT, 1000XUSDT → XUSDT.

## Règle (aucun réglage)
- Événement : ouverture du perpétuel le jour L, la paire comptant existant depuis **au moins 180 jours** avant L.
- « Short » mesuré **au comptant** de l'ouverture du jour L + 1 à la clôture du jour L + 90 (ou dernière bougie), rendement = −(sortie / entrée − 1) − 2 × 0,10 %, plancher −100 % à la sortie ; pour information, avec liquidation en cours de route.

## Jugement
- **Témoin** : même mesure, même fenêtre, sur une paire comptant tirée au hasard parmi celles cotées depuis plus de 365 jours (ou présentes dès le début des archives), hors la pièce de l'événement ; 1 000 tirages, graine 60.
- Périodes : A = événements 09/2020 → 2023 ; B = 2024 → 29/06/2026.
- **DÉMONTRÉ** si moyenne > 0 et p < 0,05 sur A + B, **ET** moyenne > 0 dans A et dans B. **NON DÉMONTRÉ** si moyenne > 0 sur A + B sans le reste. **PERD** sinon.

## Relecture d'équité
180 jours, 90 jours et mesure au comptant fixés ici. Aucune action sur Martin ni Kraken.

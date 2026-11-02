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

## Résultat (03/11/2026, 01h — t60.py → t60.log, chiffres dans t60.json)
Lancé une seule fois après le commit d7068ab, `nice -n 10`. 142 ouvertures de perpétuel sur des pièces cotées au comptant depuis au moins 180 jours.

| | Événements | « Short » comptant sur 90 j | Médiane | Positifs | Avec liquidation (info) | Témoin (pièces anciennes) | p |
|---|---|---|---|---|---|---|---|
| **A + B** | 142 | **+13,6 %** | +23,8 % | 75 % | +6,6 % | −6,5 % | **< 0,001** |
| A : 09/2020 → 2023 | 91 | +18,2 % | +33,8 % | 79 % | +12,1 % | −5,7 % | < 0,001 |
| B : 2024 → 06/2026 | 51 | +5,3 % | +16,3 % | 67 % | −3,3 % | −8,1 % | 0,002 |

Par année : 2020 −12,0 % (6) · 2021 +29,8 % (25) · 2022 +36,5 % (8) · 2023 +13,4 % (52) · 2024 +3,4 % (34) · 2025 +9,2 % (17).

**VERDICT (pré-enregistré) : DÉMONTRÉ** — après l'ouverture d'un perpétuel, une pièce ancienne fait nettement moins bien que les autres pièces anciennes sur 90 jours, sur les deux périodes.

## Vérification après le verdict (information) : Miller, ou retour après une envolée ?
- `t60_avant.py` : sur les 30 jours **avant** l'ouverture, les pièces concernées avaient monté de **+68 % en médiane**, contre +4 % pour les pièces anciennes à la même date. Binance ouvre ses perpétuels sur des pièces qui viennent de s'envoler.
- Sur la moitié des événements à la plus faible hausse préalable : +2,1 % contre −13,2 % pour le témoin (p < 0,001). L'écart reste, mais plus petit.
- **On ne peut donc pas séparer l'explication de Miller (les vendeurs à découvert entrent) d'un simple retour après une envolée** : les deux vont dans le même sens. Le fait est démontré ; sa cause ne l'est pas.
- Exploitation : en 2024-2026, avec une liquidation réaliste, le short devient négatif (−3,3 %) ; même constat que pour les jetons neufs (PREREG-58/59).

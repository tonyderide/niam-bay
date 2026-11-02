# Pré-enregistrement 53 : réplication de PREREG-46 sur le comptant Binance depuis 2017 — les nouvelles cotations perdent-elles sur 90 jours ?
Écrit le 02/11/2026 vers 03h CET, avant tout téléchargement et tout calcul. Hypothèse H16 de FILE-HYPOTHESES.md. `scripts/cherche -v` déjà passé à la création de H16 (seuls voisins : PREREG-46/47).

## Pourquoi
PREREG-46 (**GAGNE**) : sur les perpétuels Binance 2021-2026, vendre à découvert une nouvelle cotation dès le 2e jour et la tenir 90 jours rapporte (+8,0 % par trade en 2026, p < 0,001). Un GAGNE isolé peut tenir à la population ou à l'époque. Ici : **une autre population** (le comptant, où les cotations sont souvent plus anciennes et plus sélectives) et **une époque jamais regardée** (2018-2020).

## Données (publiques)
- Liste de tous les symboles du comptant ayant existé : `data.binance.vision` (listing S3 de data/spot/monthly/klines/), morts compris.
- Bougies journalières : archives mensuelles 1d de data.binance.vision (somme SHA-256 vérifiée), de 2017-08 à 2026-09.
- Paires **…USDT** seulement. **Exclus** (fixé ici) : jetons à levier (suffixes UP, DOWN, BULL, BEAR), stablecoins et monnaies (USDC, BUSD, TUSD, PAX, USDP, FDUSD, DAI, USDS, EUR, GBP, AUD, TRY, BRL, RUB, UAH, NGN, ZAR, BIDR, IDRT, PLN, RON, ARS, JPY, MXN, COP, CZK, AEUR, EURI, XUSD, USD1, BFUSD, RLUSD, PYUSD, USDE).
- Date de cotation = première bougie journalière, seulement si elle est postérieure au 31/08/2017 (le début des archives).

## Règle (celle de PREREG-46, N = 90 figé, aucun réglage)
- Pour chaque nouvelle cotation : « short » mesuré à l'ouverture de la **2e bougie**, sur **90 jours** (clôture de la 90e bougie) ou jusqu'à la dernière bougie (retrait).
- Rendement = −(sortie / entrée − 1) − 2 × 0,10 % (frais du comptant), **plancher −100 %**. Pas de financement (comptant). C'est une **mesure de prix** : le comptant ne se vend pas à découvert ; l'objet est de savoir si la surévaluation des jetons neufs existe dans cette population.

## Jugement
- **Témoin** : pour chaque trade, même mesure sur une pièce **ancienne** (première bougie plus de 365 jours avant l'entrée, bougie le jour d'entrée, mêmes exclusions), tirée au hasard, même date ; 1 000 tirages, graine 53.
- Deux périodes d'entrée : **A = 2018-2020** (jamais regardée par PREREG-46) et **B = 2021 → 29/07/2026** (sortie connue avant le 30/09/2026).
- **RÉPLIQUÉ** si rendement moyen > 0 **ET** p < 0,05 contre le témoin **dans A ET dans B**. **PARTIEL** si une seule des deux. **NON RÉPLIQUÉ** sinon.

## Rapporté
Par période et par année : trades, moyenne, médiane, part positive, part au plancher, témoin ; nombre de cotations exclues par règle.

## Relecture d'équité
Exclusions et N fixés ici. Morts compris par les archives (les paires retirées gardent leurs mois archivés). Aucun compte, aucune clé, aucune action sur Martin ni Kraken.

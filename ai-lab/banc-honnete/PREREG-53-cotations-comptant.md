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

## Résultat (02/11/2026, matin — t53_donnees.py puis t53.py → t53.log, chiffres dans t53.json)
Données : 3 745 symboles listés, 686 paires USDT gardées (49 jetons à levier et 22 stables exclus), 26 497 archives mensuelles vérifiées (8 sommes fausses écartées). Calcul lancé une seule fois après le commit a445ee4, `nice -n 10`.

| Période d'entrée | Trades | Moyenne | Médiane | Positifs | Au plancher | Témoin (pièces anciennes, même date) | p |
|---|---|---|---|---|---|---|---|
| **A : 2018-2020** (jamais regardée) | 174 | **+7,0 %** | +19,1 % | 61 % | 20 | −20,7 ± 2,2 % | **< 0,001** |
| **B : 2021 → 07/2026** | 447 | **+25,4 %** | +37,9 % | 74 % | 23 | +4,5 ± 1,5 % | **< 0,001** |

Par année : 2018 +53 % (2 trades) · 2019 +17,4 % (65) · 2020 −0,2 % (107) · 2021 +26,5 % · 2022 +30,8 % · 2023 +11,1 % · 2024 +24,6 % · 2025 +44,1 % · 2026 +6,4 % (69).

**VERDICT (pré-enregistré) : RÉPLIQUÉ** — rendement moyen > 0 et p < 0,001 contre le témoin dans les deux périodes.

## Vérification après le verdict (information)
- **Défaut trouvé** : en 2019-2020 Binance a ouvert des paires USDT pour des pièces déjà cotées contre BTC ; ce ne sont pas des jetons neufs. `t53_vrais_neufs.py` ne garde que les paires USDT apparues le même mois que la toute première paire de l'actif (premier mois de chaque symbole lu dans le listing des archives).
- **Vrais jetons neufs seulement** : A 2018-2020 : **113 trades, +14,7 %** (médiane +32,9 %), témoin −18,7 %, p < 0,001 ; B 2021-2026 : **388 trades, +25,9 %**, témoin +4,1 %, p < 0,001. L'effet est **plus fort** une fois les fausses nouveautés retirées.
- 2020 est l'année faible (+5 % sur les vrais neufs) : c'était un marché haussier fort (le témoin, short de pièces anciennes, perdait ~19 %) ; même là, les jetons neufs ont fait bien moins bien que les anciens.

**Ce que ça montre :**
- La sous-performance des jetons neufs sur leurs 90 premiers jours n'est pas propre aux perpétuels 2021-2026 : elle existe au comptant depuis 2019, sur une période que PREREG-46 n'avait jamais regardée, et chaque année l'écart avec les pièces anciennes est large.
- C'est une mesure de prix (le comptant ne se vend pas à découvert) ; la version exploitable reste le short du perpétuel, jugée en avant par PREREG-47.

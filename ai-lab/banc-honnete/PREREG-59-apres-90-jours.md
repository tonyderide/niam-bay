# Pré-enregistrement 59 : la sous-performance des jetons neufs continue-t-elle du 91e au 180e jour ?
Écrit le 02/11/2026 vers 19h30 CET, avant tout calcul. Hypothèse H21 de FILE-HYPOTHESES.md. `scripts/cherche -v déblocage six mois après cotation` : rien d'identique (seuls PREREG-46/47).

## Raison économique, et ce que dit la théorie avant les données
Deux explications de la sous-performance des 90 premiers jours (PREREG-46, 53, 54, 56) : (a) l'**engouement** du début retombe, et c'est fini en quelques semaines ; (b) l'**offre** arrive (déblocages d'équipe et d'investisseurs, souvent à 6-12 mois), et la pente continue. Si (b), les jetons neufs continuent de faire moins bien que les anciens entre le 91e et le 180e jour.

## Données
Comptant Binance (PREREG-53 : comptant/klines.json, 2017-08 → 2026-09, morts compris par les archives), **vrais jetons neufs seulement** (paire USDT apparue le même mois que la toute première paire de l'actif, `t53_vrais_neufs.py`). Correction du début des données appliquée d'emblée : une pièce présente dès le premier mois des archives compte comme ancienne.

## Règle (aucun réglage)
- Pour chaque vrai jeton neuf : « short » mesuré de l'**ouverture de la 92e bougie** (le jour qui suit la fenêtre de PREREG-53) à la **clôture de la 181e** (90 jours), ou jusqu'à la dernière bougie si retrait avant ; un jeton retiré avant la 92e bougie est exclu (il est déjà dans PREREG-53).
- Rendement = −(sortie / entrée − 1) − 2 × 0,10 %, plancher −100 % à la sortie (convention de PREREG-53) ; pour information, aussi avec liquidation en cours de route.
- Entrées de la fenêtre du 01/01/2019 au 02/07/2026 (sortie connue avant le 30/09/2026).

## Jugement
- **Témoin** : même mesure, même fenêtre de dates, sur une pièce ancienne (cotée depuis plus de 365 jours au début de la fenêtre) tirée au hasard ; 1 000 tirages, graine 59.
- **PERSISTE** si rendement moyen > 0 **ET** p < 0,05. **S'ARRÊTE** si p ≥ 0,05 ou moyenne ≤ 0. Rapporté : par année, médiane, comparaison avec la fenêtre 1-90 des mêmes jetons.

## Relecture d'équité
Fenêtre et règles fixées ici, reprises de PREREG-53. Aucune action sur Martin ni Kraken.

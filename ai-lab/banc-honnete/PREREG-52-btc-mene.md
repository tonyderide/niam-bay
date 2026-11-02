# Pré-enregistrement 52 : quand BTC bouge fort pendant une heure, les altcoins suivent-ils l'heure d'après ?
Écrit le 02/11/2026 vers 01h10 CET, avant tout calcul. Hypothèse H15 de FILE-HYPOTHESES.md. `scripts/cherche -v BTC avance altcoins décalage lead-lag` et `… heure précédente altcoins suivent retard diffusion` : voisin regime-short (filtre EMA200 de BTC sur les altcoins, autre règle) ; le retard horaire n'a jamais été testé.

## Raison économique, et ce que dit la théorie avant les données
Diffusion lente de l'information (Hou 2007 sur les actions : les grandes mènent, les petites suivent) : l'information de marché arrive d'abord sur BTC, le plus liquide ; les teneurs de marché des altcoins ajustent avec retard. Contre : les robots d'arbitrage entre pièces sont nombreux et rapides, l'effet doit être de quelques minutes, pas d'une heure ; frais lourds en horaire. Condition fixée dans la file : le brut doit dépasser 2 × les frais sur la période de choix.

## Données
ai-lab/dca-martingale/refait/donnees/*-1h.npy (253 perpétuels Binance cotés au 01/01/2024, morts compris, `couper`), 01/01/2024 → 30/09/2026.

## Règle
- À chaque heure h : r_b = rendement de BTC sur l'heure h − 1 (clôture / clôture précédente − 1).
- Si |r_b| > τ : position sur le **panier égal des altcoins** vivants (BTC exclu), dans le sens de r_b, pendant l'heure h (ouverture → clôture). Sinon pas de position. Heures consécutives dans le même sens : la position est gardée (pas de frais en plus).
- Frais taker 0,05 % par côté (entrée, sortie, retournement = 2 côtés). Sans funding.
- Grille : **τ ∈ {0,5 %, 1 %, 2 %}**.

## Choix et jugement
- Choix de τ sur 01/01/2024 → 31/12/2025 (meilleur net). Si, pour le τ choisi, le brut < 2 × les frais sur cette période : **PERD** sans aller plus loin (condition de la file).
- **JUGEMENT UNIQUE : 01/01/2026 → 30/09/2026.**
- **Témoin** : mêmes heures en position, sens tiré au hasard **par épisode** (suite d'heures consécutives en position ; leçon de PREREG-40), mêmes frais ; 1 000 tirages, graine 52. p = part ≥ la règle en 2026.
- **GAGNE** si net > 0 en 2024-25 **ET** > 0 en 2026 **ET** p < 0,05 en 2026. **NON DÉMONTRÉ** si net 2026 > 0 sans le reste. **PERD** sinon.

## Rapporté
Les 3 τ (heures en position, brut, frais, net) sur les deux périodes ; rendement moyen du panier l'heure suivante, selon le signe de r_b (corrélation brute) ; part des heures gagnantes.

## Relecture d'équité
Seuils fixés ici ; le panier inclut les morts ; le témoin garde les épisodes et les frais. Aucune action sur Martin ni Kraken.

## Résultat (02/11/2026, 01h2x — t52.py → t52.log, chiffres dans t52.json)
Lancé une seule fois après le commit a8fbffb, `nice -n 10`. Montants en % du panier, additionnés.

| τ | 2024-25 : heures / brut / frais / net | 2026 : heures / brut / frais / net |
|---|---|---|
| 0,5 % | 3 502 / −103,6 / 291,4 / −395,0 | 1 097 / −5,1 / 92,7 / −97,8 |
| 1 % | 979 / −4,0 / 88,0 / −92,0 | 283 / −0,6 / 25,4 / −26,0 |
| **2 %** (choisi) | 167 / **+31,1** / 15,7 / +15,4 | 44 / −7,8 / 4,0 / −11,8 |

- Corrélation entre le rendement horaire de BTC et celui du panier l'heure suivante : **−0,008** (2024-25) et **−0,016** (2026) — nulle, plutôt négative.
- Garde-fou de la file : pour τ = 2 %, brut 31,1 contre 2 × frais = 31,4 → **non franchi** (de justesse).

**VERDICT (pré-enregistré) : PERD** — garde-fou brut ≥ 2 × frais manqué sur la période de choix ; de toute façon net 2026 négatif (−11,8 %).

**Ce que ça montre :**
- À l'échelle de l'heure, les altcoins ne « suivent » pas BTC : l'ajustement est déjà fait dans l'heure (robots d'arbitrage). Le seul réglage positif en 2024-25 (τ = 2 %, 167 heures) ne tient qu'à quelques épisodes et s'inverse en 2026.
- Les frais d'une stratégie horaire (291 % pour τ = 0,5 %) écrasent tout signal de cette taille, comme pour les scalps des PREREG-14 à 21.

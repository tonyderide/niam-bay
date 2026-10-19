# Pré-enregistrement : revalidation des 2 pistes vivantes sur 2024-2025
Figé le 2026-10-19 vers 20h, avant tout téléchargement des données 2024-2025. Les réglages ont été choisis sur 2026 et sont gelés.

Période : 2024-01-01 → 2025-12-31 (UTC). Marchés : BTC, ETH, SOL. Bougies 1h Kraken « trade » (PF_*), paginées par tranches de 1 800 h maximum.

## Piste A : chocs 1h, « suite »
- r1h = c[t]/c[t-1] − 1. Un choc a lieu si |r1h| > 2 × écart-type des 168 r1h précédents.
- Entrée au close de t+1, dans le sens du choc. Sortie au close de t+25 (H = 24 h). Pas de chevauchement de positions sur un même marché.
- Frais : 0,10 % aller-retour.
- Écart avec 2026 : la piste avait été trouvée sur les bougies « mark ». Ici on utilise les bougies « trade », ce qui doit être quasi identique en 1h.

## Piste B : funding extrême, contrarien
- Funding horaire Hyperliquid de l'heure h.
- Extrême haut si le funding dépasse le 90e percentile des **90 jours précédents** (fenêtre glissante, sans regarder le futur), auquel cas on prend un short. Extrême bas s'il passe sous le 10e percentile, auquel cas on prend un long.
- Entrée à l'open h+1. Sortie à l'open h+5 (N = 4 h). Pas de chevauchement. Frais : 0,10 % aller-retour.
- Écart avec 2026 : là-bas les seuils étaient fixés sur la période de sélection. Ici ils glissent, parce que le niveau du funding de 2024 (année haussière) n'a rien à voir avec celui de 2026. Pour information seulement, je donne aussi la version avec les seuils figés de 2026, mais elle ne compte pas dans le verdict.

## Témoin (pour les deux pistes)
500 tirages au hasard par marché, avec le même nombre de trades, la même durée de tenue, des instants aléatoires et un sens aléatoire. La statistique comparée est la somme nette des 3 marchés, et l'on regarde le 95e centile.

## GAGNE (pour chaque piste) si toutes ces conditions sont remplies
1. Le net est > 0 sur au moins 2 marchés sur 3.
2. La somme des 3 marchés dépasse le 95e centile du hasard.
3. Il y a au moins 30 trades.
4. Le net est positif chaque année (2024 et 2025) sur la somme des 3 marchés.

## Résultat (1019 ~20h30, revalid2024.py → revalid2024.log)
Rendements sommés trade par trade, frais compris.
- **A, chocs 1h « suite »** : BTC −60,7 %, ETH +18,8 %, SOL −59,3 % sur environ 350 trades par marché. Somme −101 %. Le hasard donne une médiane de −120 % et un p95 de +77 %. Chaque année est négative. **PERD.**
- **B, funding contrarien** : BTC −52 %, ETH −203 %, SOL −148 % sur environ 1 000 trades par marché. Somme −404 %, **sous la médiane du hasard** (−297 %). **PERD.** La variante aux seuils figés sur 2026 fait pire.

Les deux « presque » de 2026 étaient des coups de chance de période. Le bilan de la chasse passe donc à 0 sur 10, sans piste vivante.

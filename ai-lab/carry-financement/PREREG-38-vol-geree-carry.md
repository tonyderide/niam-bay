# PREREG-38 : la volatilité gérée améliore-t-elle le carry du financement (PREREG-27) ?
Écrit le 31/10/2026 vers 20h CET, avant tout calcul de cette variante. Hypothèse H3 de ai-lab/banc-honnete/FILE-HYPOTHESES.md. `scripts/cherche -v volatilité gérée carry financement exposition` : voisin PREREG-13 (vol gérée sur BTC acheter-garder, ÉCHEC de justesse) ; jamais appliquée au carry.

## Raison économique, et ce que dit la théorie avant les données
Les primes de portage s'effondrent surtout quand la volatilité monte (krachs du carry ; « momentum crashes » de Daniel & Moskowitz ; Moreira & Muir 2017). La volatilité se prévoit (elle persiste), le rendement non : réduire l'exposition quand la vol récente est haute peut améliorer le rendement par unité de risque **sans prévoir le sens**. Contre : Cederburg et al. (2020) montrent que l'effet est fragile hors échantillon, et les frais de redimensionnement mangent une partie du gain. Prior : amélioration du Sharpe possible mais petite ; pas d'avantage nouveau, seulement une meilleure façon de porter une prime déjà démontrée (de justesse).

## Données et carry de base (aucun nouveau téléchargement)
- Exactement l'univers, la règle, les prix, le financement et les frais de PREREG-27 (`etude_univers.py`, data-univers/, 3 contre 3, 1 $ par côté, 0,05 % sur ce qui change), du 01/01/2021 au 27/10/2026.
- Transparence : le carry brut de 2026 est déjà connu (PREREG-27 : +94,3 %). Ce qui ne l'est pas : la version gérée.

## Règle de gestion (figée, aucun réglage)
- σ̂_t = écart-type des rendements nets **journaliers** du carry de base sur les 30 jours précédant t (jours t−30 à t−1, connus avant t). Pas de gestion pendant les 30 premiers jours (multiplicateur 1).
- Cible σ* _t = **médiane de σ̂ sur tout le passé** jusqu'à t−1 (expansive, aucune information future).
- Multiplicateur m_t = min(2, σ*_t / σ̂_t). Poids du jour t = m_t × poids du carry de base. Frais 0,05 % sur chaque variation de poids (le redimensionnement paie).

## Jugement
- Mesure : **Sharpe** = moyenne / écart-type des rendements nets journaliers × √365.
- Période de référence 2021-2025 ; **JUGEMENT UNIQUE : 01/01/2026 → 27/10/2026**.
- **Témoin au hasard** : mêmes multiplicateurs, **mélangés dans le temps** (permutation des m_t, 1 000 tirages, graine 38), mêmes frais recalculés. Il garde le levier moyen et sa distribution, retire seulement le timing de la volatilité. p = part des tirages dont le Sharpe 2026 ≥ celui de la version gérée.
- **GAGNE** si Sharpe géré > Sharpe brut en 2021-25 **ET** en 2026, **ET** net géré 2026 > 0, **ET** p < 0,05 en 2026.
- **NON DÉMONTRÉ** si Sharpe géré > Sharpe brut en 2026 et net 2026 > 0, sans tout le reste.
- **PERD** sinon.

## Rapporté
Par période : net, Sharpe, pire baisse, pire mois, multiplicateur moyen, frais (brut contre géré) ; Sharpe du témoin (moyenne, écart-type) ; par année.

## Relecture d'équité, avant calcul
- Aucun paramètre ajusté : 30 jours, médiane expansive et plafond 2 sont des choix standards fixés ici.
- Le témoin a le même levier moyen et paie ses frais : il ne retire que l'information de volatilité.
- Aucune action sur Martin ni Kraken : calcul seulement.

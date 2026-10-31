# Pré-enregistrement 31 : la règle de Tony en PANIER (beaucoup de pièces à la fois)
Écrit le 31/10/2026 à 03h1x, avant tout calcul de cette règle en panier. Question de Tony (30/10) : « long short changeant si perte ». PREREG-28 B (inversion après perte, BTC seul) et PREREG-30 (sens par l'EMA : BTC +, ETH + p = 0,04, SOL −) sont NON DÉMONTRÉ. Nouvelle question : la règle a-t-elle un avantage quand on l'applique **en portefeuille sur beaucoup de pièces à la fois** (diversification) ?

## Ce que dit la théorie, avant les données
La diversification réduit la **dispersion** (pire mois, pire baisse), pas l'**espérance** : la moyenne d'un panier est la moyenne des espérances par pièce. Si la règle n'a pas d'avantage pièce par pièce, le panier sera proche de zéro moins les frais, simplement avec moins de bruit. Le panier a un intérêt statistique : avec ~200 pièces, un petit avantage réel deviendrait mesurable (p plus petit), et l'absence d'avantage aussi.

## Données (les mêmes que PREREG-24 refait et PREREG-28 bougies 1 h)
- ai-lab/dca-martingale/refait/donnees/*-1h.npy : Binance USDT-M, bougies **1 h**, 253 perpétuels cotés au 01/01/2024 (univers.json), morts compris, chaque pièce coupée à son retrait (48 h figées, fonction `couper` de sl-trailing/etude.py). Pas de nouveau téléchargement.
- Pas de funding (les scripts de PREREG-28 et PREREG-30 ne le comptent pas ; même convention ici). Frais taker 0,05 % par côté, comme partout.

## Règle de sortie (identique à PREREG-28 B / PREREG-30, code de sl-trailing/etude.py)
- Toujours en position, sans levier, entrée à l'ouverture de la bougie qui suit la sortie précédente.
- SL fixe à s de l'entrée ; dès que le prix dépasse l'entrée de a dans le bon sens, stop = max(SL, pic × (1 − t)) (équivalent pour un short) ; pic = extrême des bougies **précédentes** depuis l'activation (la bougie d'activation fixe le pic initial).
- Sortie au prix du stop, ou à l'ouverture si elle est déjà au-delà. **Bougie ambiguë = SL d'abord** (pessimiste). En bougies 1 h ce biais pèse plus qu'en 1 min ; il est connu et noté, pas corrigé.
- Fin de période ou retrait de la pièce : sortie au dernier prix connu.

## Deux variantes, réglages FIGÉS (aucun réglage nouveau, rien choisi sur 2026)
- **(i) Inversion après perte (règle de Tony, PREREG-28 B) :** SL 3 %, activation +5 %, trailing 1 % (réglage figé de PREREG-28 B). On garde le sens après un gain, on l'inverse après une perte (trade net ≤ 0). Premier trade de chaque pièce et de chaque période : long.
- **(ii) Sens par l'EMA (PREREG-30) :** EMA 50 horaire, SL 5 %, activation +3 %, trailing 1 % (réglage figé de PREREG-30). Long si la dernière clôture horaire terminée est au-dessus de son EMA50, short sinon. EMA calculée sur toute l'histoire de la pièce (heures terminées seulement), chauffe de 150 h sans trade.

## Univers et panier
- Pour chaque période, les pièces **vivantes au début de la période** (première bougie de la tranche à moins de 2 h du début), et au moins 25 bougies dans la période.
- **Mise égale par pièce, sans levier, constante** (comme PREREG-28) : le résultat d'une pièce = somme des rendements nets de ses trades ; **rendement du panier = moyenne sur les pièces** (une pièce morte en cours de route garde ses pertes/gains et reste dans le dénominateur, sa mise dort ensuite en cash).

## Périodes
- Contrôle : 01/01/2024 → 31/12/2025 (rien à régler : les réglages sont déjà figés ; sert de première condition).
- **JUGEMENT UNIQUE : 01/01/2026 → 30/09/2026** (exclu 01/10).

## Témoin
- Même règle de sortie, mêmes SL/activation/trailing, mêmes frais, mêmes pièces, même période, mais **sens de chaque trade tiré au hasard** (probabilité de long = part de longs de la variante sur cette pièce et cette période). Les trades s'enchaînent comme dans la règle ; le nombre de trades est donc presque, pas exactement, le même (la durée d'un trade dépend du sens) : il est rapporté.
- **1 000 tirages** par variante et par période. p = part des tirages dont le rendement du panier est **≥** celui de la variante. Le p de 2026 est celui du verdict ; celui de 2024-25 est rapporté pour information.

## Métriques rapportées (par variante et par période)
- Rendement net du panier (en % de la mise par pièce) ; gains bruts contre frais ; nombre de trades ; part de trades gagnants.
- Part des pièces positives.
- p contre le témoin ; moyenne et écart-type du témoin.
- **Pire mois** du panier (somme des trades sortis dans le mois, divisée par le nombre de pièces).
- **Pire baisse** : plus grand recul depuis un sommet de la courbe cumulée du panier (trades rangés par heure de sortie), en points de % de la mise.

## Verdict (par variante)
- **GAGNE** si net du panier > 0 en 2024-25 **ET** > 0 en 2026 **ET** p < 0,05 contre le témoin en 2026.
- **NON DÉMONTRÉ** si le net de 2026 est > 0 sans tout le reste.
- **PERD** sinon.
- Deux variantes sont testées : un p entre 0,025 et 0,05 sera signalé comme fragile (seuil de Bonferroni 0,025), sans changer le verdict ci-dessus.

## Relecture d'équité, avant le calcul
- Réglages hérités, choisis sur BTC 1 min : ils ne sont pas optimisés pour un panier en 1 h. C'est voulu (pas de nouveau choix), et c'est un handicap possible pour la règle.
- Le témoin paie les mêmes frais et garde la même volatilité ; il ne retire que l'information de sens.
- Bougie ambiguë en SL : biais contre la règle **et** contre le témoin, à égalité.
- Morts compris : pas de biais du survivant.
- Aucune action sur Martin ni Kraken : calcul seulement.

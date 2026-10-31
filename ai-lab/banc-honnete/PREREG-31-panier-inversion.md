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

## Résultat (31/10/2026, 03h3x — t31.py → t31.log, chiffres complets dans t31.json)
Lancé une seule fois après le commit b9bebc2 (pré-enregistrement seul). Univers : 243 pièces exploitables sur les 253 (10 vides après la coupe au retrait), toutes vivantes au 01/01/2024 ; **188 vivantes au 01/01/2026** pour le jugement. Rendements en % de la mise par pièce, mise constante non composée (une pièce peut donc perdre plus de 100 % de sa mise sur une période : la mise est remise à chaque trade).

| | (i) inversion après perte — 2024-25 | (i) — **2026** | (ii) sens EMA50 — 2024-25 | (ii) — **2026** |
|---|---|---|---|---|
| Net du panier | −55,0 % | **−47,8 %** | −147,8 % | **−55,8 %** |
| Pièces positives | 29 % | 23 % | 11 % | 18 % |
| Trades (par pièce) | 264 643 (1 089) | 60 462 (322) | 247 952 (1 020) | 57 279 (305) |
| Trades gagnants | 38 % | 37 % | 60 % | 60 % |
| Brut / frais | +53,9 / 108,9 | −15,7 / 32,2 | −45,7 / 102,0 | −25,3 / 30,5 |
| Pire mois | −20,9 % (2025-11) | −12,6 % (2026-04) | −18,3 % (2025-02) | −15,9 % (2026-03) |
| Mois positifs | 11/24 | 2/9 | 4/24 | 2/9 |
| Pire baisse | 69,5 pts | 61,0 pts | 153,3 pts | 69,4 pts |
| Témoin sens au hasard (moy. ± é.-t., 1 000 tirages) | −132,7 ± 8,2 % | −47,3 ± 5,2 % | −133,6 ± 8,0 % | −44,4 ± 5,1 % |
| p contre le témoin | < 0,001 (info) | **0,54** | 0,96 (info) | **0,99** |

Le témoin fait presque le même nombre de trades (265 616 / 60 397 / 252 069 / 58 320).

**VERDICT (pré-enregistré) : PERD**, pour les deux variantes : net du panier négatif en 2024-25 et en 2026.

**Ce que ça montre :**
- La diversification a fait ce que la théorie annonçait : elle lisse (pire mois −13 à −16 % en 2026), mais elle ne crée pas d'espérance. La moyenne de 188 pièces qui perdent chacune un peu est un panier qui perd sûrement.
- Le vrai coût, ce sont les frais : avec ces réglages en bougies 1 h, une altcoin fait ~500 trades par an, soit ~50 % de la mise par an en frais taker. Même un brut positif (+54 % en 2024-25 pour l'inversion) est mangé deux fois.
- Seule trace intéressante, notée honnêtement : en 2024-25, l'inversion après perte a fait **beaucoup mieux que le hasard** (−55 % contre −133 %, aucun des 1 000 tirages aussi bien) — garder le sens après un gain a capté de la tendance sur les altcoins. En 2026, l'écart a **disparu** (−47,8 % contre −47,3 %, p = 0,54). Un avantage qui existe une période et pas la suivante n'est pas utilisable.
- L'EMA en panier fait pire que le hasard sur les deux périodes (p = 0,96 et 0,99) : le petit + de PREREG-30 sur BTC/ETH ne se généralise pas aux autres pièces.
- Limites : réglages hérités de BTC 1 min (non réoptimisés, par construction) ; bougie ambiguë comptée en SL à 1 h (pèse sur la règle et sur le témoin à égalité) ; funding non compté (comme PREREG-28/30).

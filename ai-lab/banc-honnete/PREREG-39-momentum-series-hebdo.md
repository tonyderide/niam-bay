# Pré-enregistrement 39 : le momentum de séries temporelles hebdomadaire, sur un panier large morts compris
Écrit le 31/10/2026 vers 21h CET, avant tout calcul. Hypothèse H4 de FILE-HYPOTHESES.md. `scripts/cherche -v momentum séries temporelles hebdomadaire panier` : voisins PREREG-TENDANCE (labo-cutoff, 5 pièces Kraken, EMA/Donchian/momentum 3 mois long-ou-rien) et PREREG-10 (momentum **transversal**, 21 pièces, PERD). Ici : signe du rendement passé **de chaque pièce**, long ou short, taille par la volatilité, ~240 pièces.

## Raison économique, et ce que dit la théorie avant les données
Sous-réaction à l'information puis suivisme (Moskowitz, Ooi & Pedersen 2012 ; Liu & Tsyvinski 2021 sur crypto, à 1-4 semaines). Sur une marche aléatoire le signe du passé ne dit rien du futur et l'espérance brute est nulle : la règle ne gagne que si les rendements hebdomadaires sont autocorrélés positivement. PREREG-32 a vu un brut qui change de signe selon la période en journalier : prior **plutôt NON DÉMONTRÉ**. Le panier large donne de la puissance : ~240 pièces × ~140 semaines.

## Données (déjà là, aucun téléchargement)
- ai-lab/dca-martingale/refait/donnees/*-1h.npy, univers.json (253 perpétuels USDT-M Binance cotés au 01/01/2024, morts compris), fonction `couper` identique à t32.py (48 h figées = retrait). 01/01/2024 → 30/09/2026.
- Agrégation : jours UTC (comme t32.py), puis **semaines du lundi 00:00 UTC** au lundi suivant (ouverture du lundi → ouverture du lundi suivant ; dernière semaine d'une pièce retirée : jusqu'à son dernier prix).

## Règle
- Chaque lundi, pour chaque pièce vivante ayant au moins L semaines complètes d'historique et 30 jours de rendements journaliers : sens = signe du rendement des L semaines passées (0 → pas de position).
- Taille = min(2, 0,04 / σ̂), σ̂ = écart-type des rendements journaliers des 30 derniers jours (0,04 = 4 %/jour, ordre de grandeur d'une altcoin ; fixé ici, pas ajusté).
- Rendement de la semaine = moyenne sur les pièces en jeu de taille × sens × rendement de la semaine − 0,05 % × |variation de position| (taker, comme PREREG-32). Sans funding (même convention que PREREG-28 à 32 ; rapporté sur le sous-panier couvert pour information si simple).
- Grille : **L ∈ {2, 4, 8, 12} semaines**.

## Choix et jugement
- Choix de L **uniquement sur les semaines commençant du 01/01/2024 au 29/12/2025**, au meilleur net (somme des rendements hebdomadaires du panier).
- **JUGEMENT UNIQUE : semaines commençant du 05/01/2026 au 21/09/2026** (dernière semaine complète avant le 30/09).
- **Témoin** : même L, mêmes pièces, mêmes semaines, mêmes tailles, **sens au hasard** avec P(long) = part de longs de la règle sur la période ; 1 000 tirages, frais recalculés. p = part des tirages ≥ la règle.
- **GAGNE** si net > 0 en 2024-25 **ET** > 0 en 2026 **ET** p < 0,05 en 2026. **NON DÉMONTRÉ** si net 2026 > 0 sans le reste. **PERD** sinon.

## Rapporté
Les 4 L sur les deux périodes (info : 2026 de tous), net brut/frais, semaines positives, pire semaine, pire baisse, part de longs, nombre moyen de pièces en jeu ; acheter-garder du panier égal et de BTC ; variante long-ou-rien (info).

## Relecture d'équité, avant calcul
- Le choix de L sur 2024-25 favorise la règle ; corrigé par le jugement 2026 unique.
- Morts compris (pas de biais du survivant). Le témoin garde tailles, frais et part de longs ; il ne retire que l'information de sens.
- Aucune action sur Martin ni Kraken.

## Résultat (31/10/2026, 21h2x — t39.py → t39.log, chiffres dans t39.json)
Lancé une seule fois après le commit 9e5466c, `nice -n 10`. 243 pièces exploitables, 143 semaines. Net = somme des rendements hebdomadaires du panier (taille 1/vol, plafond 2), en %.

Grille (2024-25 → 2026) : L 2 : +46,2 % → +6,5 % ; **L 4 : +64,9 % → −10,8 %** ; L 8 : +5,8 % → +8,1 % ; L 12 : −17,6 % → −8,9 %. **L figé = 4 semaines.**

| | 2024-25 (choix) | **2026 (jugement)** |
|---|---|---|
| Net | +64,9 % | **−10,8 %** |
| Brut / frais | +67,1 / 2,2 | −9,6 / 1,3 |
| Semaines positives | 49 % | 55 % |
| Pire semaine | −24,4 % | −25,7 % |
| Pire baisse | 62,9 pts | 41,6 pts |
| Part de longs | 38 % | 40 % |
| Pièces en jeu (moyenne) | 202 | 179 |
| Témoin sens au hasard | −11,4 ± 9,0 % | −4,7 ± 8,2 % |
| p | < 0,001 (info) | **0,77** |

Repères : acheter-garder panier égal −35,5 % (2024-25) / −20,7 % (2026) ; BTC +116 % / −7,7 %. Variante long-ou-rien (info) : +25,8 % / −30,2 %.

**VERDICT (pré-enregistré) : PERD** — net 2026 négatif (−10,8 %), sous la moyenne du hasard (p = 0,77).

**Ce que ça montre :**
- Encore le même schéma : très fort sur la période de choix (p < 0,001 en 2024-25, sur 200 pièces), rien sur la période jugée. Le classement des 4 L s'inverse presque entre les deux périodes (le meilleur de 2024-25 est l'un des pires de 2026) : l'autocorrélation hebdomadaire des cryptos dépend du régime, elle ne se transporte pas.
- Les frais ne sont pas en cause (1-2 % par an) : c'est le brut qui change de signe.
- Avec PREREG-10 (transversal), PREREG-TENDANCE et PREREG-32, le momentum crypto sur jours et semaines compte maintenant 4 essais propres sans jugement réussi.

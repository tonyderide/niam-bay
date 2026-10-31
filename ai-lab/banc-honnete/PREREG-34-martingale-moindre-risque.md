# Pré-enregistrement 34 : la martingale avec inversion qui a le MOINS DE RISQUE (la queue, pas la fréquence)
Écrit le 31/10/2026 à 14h5x, avant tout calcul de cette étude (les bougies de PREREG-24 refait et de PREREG-28 sont déjà téléchargées et vérifiées ; aucune simulation de ce critère n'a été faite). Demande de Tony (31/10) : « la martingale avec inversion — trouve celle qui a le MOINS DE RISQUE ».

Déjà vu : PREREG-28 C a cherché, parmi 6 084 combinaisons, celle qui minimise la **fréquence** des pertes à 3 mois (P(perte)) et a choisi « SL 5 %, activation +1 %, trailing 1 %, ×3 après une perte, retour à la base après 4 pertes, mise 10 € » : 0 % de pertes sur BTC 2026, mais 45 % (ETH) et 62 % (SOL) hors échantillon (D), pire 3 mois −972 € sur SOL. PREREG-29 : aucune martingale positive tous les mois, pire mois −987 €, même score sur prix mélangés. PREREG-31 : la règle en panier PERD (p = 0,54 contre sens au hasard). Le risque d'une martingale n'est pas dans la fréquence des pertes, il est dans la **queue** : la grosse perte rare. PREREG-34 minimise la queue.

## Mise en garde théorique, écrite avant les données
- Une martingale **ne crée pas d'espérance, elle la redistribue** (théorème d'arrêt optionnel) : elle transforme beaucoup de petites pertes en beaucoup de petits gains, payés par de rares grosses pertes. Sans avantage de la règle de sortie elle-même, l'espérance reste celle des trades (≈ 0 avant frais, < 0 après), multipliée par les mises.
- Le réglage le moins risqué est donc **probablement celui qui mise le moins : ×1 (pas de martingale)**, avec le SL le plus large et l'activation la plus lointaine (le moins de trades, donc le moins de frais et la plus petite dispersion). Prédiction écrite d'avance, à vérifier : le choix tombera sur m = 1.
- Si le choix tombe sur m = 1, la réponse honnête à « quelle martingale a le moins de risque » sera : **aucune martingale** ; le moindre risque, c'est de ne pas multiplier.

## Règle (identique à PREREG-28 B/C, code de ../sl-trailing/regle_tony.py, fonction `chaine`)
- Toujours en position, entrée à l'ouverture de la bougie qui suit la sortie précédente, taker 0,05 % par côté.
- SL fixe à s de l'entrée ; dès que le prix dépasse l'entrée de a dans le bon sens, stop = max(SL, pic × (1 − t)) (équivalent short) ; pic = extrême des bougies précédentes depuis l'activation. Bougie ambiguë = SL d'abord (pessimiste).
- **Sens inversé après une perte** (trade net ≤ 0), gardé après un gain. Premier trade de chaque tranche : long.
- **Mise** = ce qu'on perd si le SL est touché (position = mise / s). Après une perte : mise × m ; après un gain : base ; après k pertes d'affilée : on encaisse et on revient à la base (règle de PREREG-28 C, fonction `jouer` de ../sl-trailing/moins_de_perte.py).
- **Capital de référence 1 000 €**, **mise de base 10 €** (fixée, pas choisie). Position ≤ 10 × le capital du moment (sinon ramenée). Capital < 50 € : arrêt (comme C).

## Grille (la même que PREREG-28 C, mise de base fixée à 10 €)
- (s, a, t) : les 156 triplets de PREREG-28 B/C — s ∈ {0,5 ; 1 ; 1,5 ; 2 ; 3 ; 5} %, a ∈ {0,5 ; 1 ; 1,5 ; 2 ; 3 ; 5} %, t ∈ {0,25 ; 0,5 ; 1 ; 1,5 ; 2 ; 3} % avec t ≤ a.
- m ∈ {1 ; 1,5 ; 2 ; 3}, plafond k ∈ {2 ; 4 ; 6 ; ∞} (m = 1 : plafond sans effet, compté une fois).
- 156 × 13 = **2 028 réglages**.

## Données
- **BTC, ETH, SOL** : BTCUSDT / ETHUSDT / SOLUSDT perpétuels Binance, bougies **1 min**, 01/2024 → 30/09/2026 (coupe à 48 h figées, `couper(a, 2880)`), comme PREREG-28.
- **Panier** : ai-lab/dca-martingale/refait/donnees/*-1h.npy, Binance USDT-M **1 h**, perpétuels de univers.json (morts compris, coupés au retrait, `couper(a, 48)`), comme PREREG-31. Chaque pièce = un compte séparé de 1 000 € avec la même règle.
- Chaque période est simulée **sur sa tranche seule** (la chaîne de trades repart long au début de la tranche) : 2024-25 = 01/01/2024 → 01/01/2026 ; 2026 = 01/01/2026 → 01/10/2026 (exclu). Pas de funding (même convention que PREREG-28/31).

## Mesures (par réglage, par terrain, par période)
- **Départs** : un par jour (BTC/ETH/SOL), un tous les 7 jours par pièce (panier, pour le temps de calcul), au premier trade qui commence à partir de 00:00 UTC du jour. Fenêtre de **3 mois = 90 jours**, entièrement dans la période. Panier : une pièce compte à un départ si elle a une bougie à moins de 2 h du départ ; si elle meurt dans la fenêtre, sa fenêtre s'arrête au dernier prix (morts compris).
- R = capital à la fin de la fenêtre − 1 000 €. Capital suivi aux clôtures de trades.
- **Espérance nette** = moyenne des R (frais compris).
- **CVaR 5 %** = moyenne des 5 % pires R (les ⌈0,05 N⌉ plus petits).
- **P(perte)** = part des R < 0.
- **Ruine** = part des fenêtres où le capital touche **≤ 500 €** (perte ≥ 50 % du capital de référence) à un moment quelconque.
- **Pire baisse** = plus grand recul du capital depuis un sommet, en € puis en % des 1 000 €, sur un **parcours continu** de la période (1 000 € au début de la période, sans remise). Panier : pire baisse de chaque pièce ; le chiffre du panier est le **95e centile** sur les pièces (dépassé par 1 pièce sur 20) ; la pire pièce est rapportée.
- Panier : espérance, CVaR, P(perte), ruine calculées sur l'ensemble des couples (pièce, départ) = le risque d'un compte sur une pièce prise sans savoir laquelle.

## Choix (sur 2024-2025 seulement, figé avant de regarder 2026)
- **Réglage A** : choisi sur **BTC 1 min** 2024-25 (comme C). **Réglage B** : choisi séparément sur le **panier 1 h** 2024-25.
- Candidats : réglages à espérance nette > 0 en 2024-25. Parmi eux, **CVaR 5 % la plus haute** (la queue la moins mauvaise) ; à égalité (au 0,1 € près), la plus faible pire baisse. S'il n'y a aucun candidat, on prend quand même la meilleure CVaR et on le signale.
- Rapporté aussi : le réglage qui minimise **la pire baisse seule** (parmi les candidats), et ses chiffres 2026 (pour information, pas jugé).

## Jugement unique 2026 (01/01 → 30/09), réglages A et B figés
Sur 4 terrains : BTC, ETH, SOL (1 min) et le panier (1 h, pièces vivantes au 01/01/2026). Rapportés : pire baisse, CVaR 5 %, P(perte à 3 mois), ruine, espérance nette, nombre de trades.
- **Témoin sens aléatoire** : même règle de sortie, mêmes réglages, même martingale, mêmes frais, mêmes fenêtres, mais le sens de chaque trade est tiré au hasard (P(long) = part de longs de la règle sur ce terrain/pièce en 2026). **1 000 tirages** par terrain. p = part des tirages dont l'espérance nette ≥ celle de la règle.
- **Prix mélangés** (comme PREREG-29 / PREREG-28) : les bougies de la tranche 2026 tirées dans un ordre aléatoire (forme relative à l'ouverture gardée, prix recollés : même volatilité, plus de tendance), 100 mélanges par pièce pour BTC/ETH/SOL, 20 par pièce pour le panier. Rapportés : espérance, CVaR, P(perte), ruine moyennes sur les mélanges, et la part des mélanges dont l'espérance ≥ celle de la règle (information).

## Verdict (pour A, puis pour B)
- **« moindre risque ET gagnant »** si, en 2026, sur les **4 terrains** : espérance > 0, pire baisse < 20 % du capital de référence (< 200 €), ruine = 0, **et** p < 0,05 contre le témoin sens aléatoire.
- **« moindre risque mais pas d'avantage »** si pire baisse < 200 € et ruine = 0 sur les 4 terrains, sans le reste (espérance ≤ 0 quelque part ou p ≥ 0,05 quelque part).
- **« risque non maîtrisé »** sinon.

## Relecture d'équité, avant le calcul
- Mêmes frais partout ; le témoin et les mélanges les paient aussi.
- Choix le plus favorable possible : la meilleure queue parmi 2 028 réglages, sur 2024-25 — ce qui rend la queue de 2024-25 optimiste ; seul 2026 et les pièces hors choix (ETH, SOL pour A) comptent.
- Biais connus : bougie ambiguë = SL (rare en 1 min, plus fréquent en 1 h, touche règle et témoin à égalité) ; capital suivi aux clôtures (une perte latente dans un trade n'est pas vue, mais elle est bornée par le SL sauf gap) ; départs qui se chevauchent (2026 ≈ 3 trimestres indépendants par pièce, chiffres BTC/ETH/SOL peu précis) ; panier en départs hebdomadaires.
- Aucune action sur Martin ni Kraken : calcul seulement. Fichiers nommés 34 uniquement.

## Résultat (31/10/2026, 15h1x — t34.py → t34.log, chiffres complets et tableaux des 2 028 réglages dans t34.json)
Lancé une seule fois après le commit 9b53175 (pré-enregistrement seul). Panier : 243 pièces en 2024-25, 188 vivantes au 01/01/2026. Montants en € pour un compte de 1 000 €, mise de base 10 €, fenêtres de 3 mois.

**Choix sur 2024-25 (518 candidats à espérance > 0 sur BTC, 63 sur le panier) :**
- **A (BTC 1 min) : SL 5 %, activation +1 %, trailing 1 %, ×3 après une perte, retour à la base après 4 pertes** — c'est exactement la combinaison de PREREG-28 C. 2024-25 : espérance +101,6 €, CVaR 5 % **+9,0 €**, P(perte) 0,8 %, ruine 0, pire baisse 102,6 €.
- **B (panier 1 h) : SL 5 %, activation +5 %, trailing 3 %, ×1,5, retour après 6 pertes.** 2024-25 : espérance +2,9 €, CVaR −449,8 €, P(perte) 45 %, ruine 2,2 %, pire baisse (95e centile des pièces) 1 091 €.
- **La prédiction écrite d'avance (« le choix tombera sur ×1 ») est FAUSSE sur 2024-25** : à mise de base fixée, le meilleur ×1 sur BTC a une CVaR de −46 € contre +9 € pour ×3. Sur 2024-25 BTC, la martingale ×3 plafonnée à 4 a *réduit* la queue — sur l'échantillon où elle a été choisie.
- Réglage « pire baisse seule » (BTC) : même triplet, ×2, plafond 4 (pire baisse 71,8 €, CVaR −23,1 €).
- A appliqué hors choix en 2024-25 : ETH espérance −43 €, CVaR −481 €, ruine 7 % ; SOL −226 €, CVaR −936 €, ruine 32 % ; panier −223 €, CVaR −968 €, ruine 42 %.

**Jugement 2026 (01/01 → 30/09), réglages figés :**

| | A : BTC | A : ETH | A : SOL | A : panier | B : BTC | B : ETH | B : SOL | B : panier |
|---|---|---|---|---|---|---|---|---|
| Espérance à 3 mois | **+83,6 €** | +52,2 € | **−162,3 €** | **−171,3 €** | +29,2 € | +40,3 € | +47,0 € | **−68,8 €** |
| CVaR 5 % | +45,7 € | −72,0 € | −552,0 € | −963,7 € | −13,0 € | −73,5 € | −70,8 € | −494,9 € |
| P(perte à 3 mois) | 0 % | 23 % | 54 % | 64 % | 12 % | 32 % | 18 % | 62 % |
| Ruine (capital ≤ 500 €) | 0 | 0 | **16 %** | **29 %** | 0 | 0 | 0 | **3,2 %** |
| Pire baisse | 41 € | 126 € | **646 €** | **1 363 €** (95e c.) | 83 € | 146 € | 131 € | **839 €** (95e c.) |
| Témoin sens au hasard : espérance (é.-t.) | −8,8 (88) | −18,8 (126) | −106,8 (138) | −139,9 (19) | −19,2 (46) | −30,9 (62) | −36,0 (78) | −48,0 (8) |
| **p contre le témoin** (1 000 tirages) | 0,10 | 0,31 | 0,69 | 0,95 | 0,12 | 0,11 | 0,14 | 0,99 |
| Prix mélangés : espérance / part aussi bien | −16,9 / 0,09 | −53,8 / 0,19 | −94,0 / 0,66 | −155,4 / 0,85 | −13,4 / 0,18 | −29,8 / 0,20 | −30,0 / 0,24 | −48,9 / 1,00 |

**VERDICT (pré-enregistré) : A « risque non maîtrisé », B « risque non maîtrisé ».** Aucun des deux n'a pire baisse < 200 € et ruine = 0 sur les 4 terrains ; aucun p < 0,05.

**Ce que ça montre :**
- Minimiser la queue sur BTC 2024-25 ramène exactement le réglage de PREREG-28 C : la « queue la plus fine » de BTC est un artefact du même choix sur une seule pièce. Hors de BTC, il s'effondre (SOL : ruine dans 16 % des départs 2026, pire baisse 646 € ; panier : 29 % de ruines, CVaR −964 €). Sa queue sur le panier est **pire que celle du témoin au hasard** (p = 0,95).
- Choisi sur le panier (B), le réglage le moins risqué mise moins (×1,5, SL et activation larges, ~1 trade tous les 2-3 jours) : il tient sur BTC/ETH/SOL 2026 (aucune ruine, pire baisse 83-146 €) mais pas sur le panier (3 % de ruines, pire baisse 839 € pour 1 pièce sur 20, espérance −69 €, pire que le hasard p = 0,99).
- Même là où l'espérance est positive (A sur BTC/ETH, B sur BTC/ETH/SOL), aucun résultat n'est distinguable d'un sens tiré au hasard (p 0,10 à 0,31) : la martingale n'a pas créé d'avantage, elle a redistribué. La mise en garde théorique tient ; la prédiction « ×1 » ne tient pas en échantillon, mais la règle générale — moins on multiplie, moins la queue est grosse hors échantillon — se lit dans B contre A.
- Limites : départs qui se chevauchent (2026 ≈ 3 trimestres indépendants par pièce) ; capital suivi aux clôtures ; bougie ambiguë en SL (1 h pour le panier) ; pas de funding.

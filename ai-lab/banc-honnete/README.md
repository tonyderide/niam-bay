# Le banc honnête
Idée du 2026-10-20 à 04h. Le conseil intérieur a voté OUI à 6,9.

On vérifie publiquement les stratégies de trading qui circulent (YouTube, TradingView), avec la méthode de la chasse du 1019 :
- la règle est figée dans un commit avant de regarder les données ;
- on teste sur 2024-2025 et sur 2026, avec les frais réels ;
- on compare à des trades au hasard ;
- on publie le verdict même s'il est négatif.

Règle d'indépendance, suggérée par le Sceptique : **le verdict est toujours gratuit et public**. Si un jour quelque chose devient payant, ce sera seulement la rapidité ou un test sur demande, jamais le résultat.

Plan d'argent :
1. publier un rapport gratuit sur 3 stratégies virales ;
2. mesurer si des gens demandent d'autres tests ;
3. si oui, proposer des tests sur demande à quelques euros, encaissés par Tony.

Si personne ne demande rien, on arrête, et on le note comme pour exchange-truth.

| # | Stratégie | Verdict |
|---|---|---|
| 1 | VWAP × EMA9 en 3 min (vue par Tony) | ÉCHEC : 5 variantes, voir ../vwap-ema9 |
| 2 | MACD + EMA200 (chiffres de 59 à 86 % de gagnants vus dans des résumés secondaires, NON vérifiés à la source) | PERD : 34-49 % de gagnants ; somme −23 % sur 2024-2025, +2 % sur 2026, loin sous le hasard p95 (t02.log) |
| 3 | Supertrend (10, 3), 1h et 4h | PERD : les 4 cases sont négatives (somme −234 % en 1h sur 2024-2025), voir t03.log |
| 4 | Stop suiveur (% et Turtles), idée de Tony | PERD : change de signe selon la période ; ne bat pas des entrées au hasard avec le même stop (t04.log) |
| 5 | Bollinger / ADX de la chaîne « Trading Strategy Testing » (15 min) | PERD : 40-48 % de gagnants, les frais ruinent |
| 6 | RSI-2 de Connors, 21 cryptos | PERD de peu : gagne sur toutes les périodes, mais 60e-82e centile du hasard seulement |
| 7 | 6 tracés classiques (avalement, marteau, inside bar, NR7, 3 soldats, rejet SMA200) | PERD : le meilleur de 2024-25 fait la médiane du hasard en 2026 |
| 8 | Tournoi de 4 experts IA (quant, scalper, suiveur de tendance, quant volatilité), 15 stratégies avec filtres de régime | PERD : le meilleur (tendance en volatilité croissante) fait +130 % en 2026, mais au 81e centile du hasard ; le scalping à 30 trades par jour est impossible avec les frais |
| 9 | 840 combinaisons (10 signaux × 7 filtres × 6 sorties × 2 unités de temps) | PERD : Spearman 2024-25 → 2026 = +0,04 ; le top 20 de 2024-25 n’est pas plus souvent positif en 2026 (45 %) que l’ensemble (45 %) |
| 10 | Rotation des forts (momentum transversal, 21 cryptos, neutre au marché) | PERD : le meilleur de 2024-25 (1 semaine) fait −26 % en 2026, au 8e centile du hasard |
| 11 | Carnet d'ordres (déséquilibre des 5 meilleurs niveaux, ordres limites) | EN COURS : enregistrement de la nuit du 21-22/10, jugement le 22/10 matin |
| 12 | Grille 0,6 % × 5 niveaux (façon Martin) allumée quand la volatilité prévue est haute | PERD : −2,2 % en 2026, mieux que toujours allumée (−6,1 %) mais au 41e centile des décalages au hasard ; en 2024-25 toute grille perd 44 à 59 % (sorties de grille en tendance) |
| 13 | BTC géré par la volatilité (Moreira-Muir : position = cible / vol. prévue, sans levier) | ÉCHEC de justesse : Sharpe +0,20 contre +0,04 en garder-acheter, rendement +0,4 % contre −6,2 %, pire perte 33,5 % contre 39,5 %, mais 90e centile des poids mélangés (seuil p95). Et en 2024-25 (info, pas verdict) il fait PIRE : Sharpe 0,79 contre 1,01, 17e centile → le mieux de 2026 ressemble à de la chance |
| 14 | Scalp honnête (120 : 4 signaux × 5 couples TP/SL × 3 marchés × 15 min/1 h, mise fixe, sans levier, gaps) | ÉCHEC au seuil corrigé, mais le plus proche à ce jour : la seule positive de 2024-25 (SOL 1 h, croisement EMA 9/21, TP 2 % / SL 1 %, +7,9 %) fait **+22,6 % en 2026 sur 213 trades**, 98,2e centile des jumeaux (seuil Bonferroni 99,96). Confirmation PREREG-15 : RATÉE sur 18 paires jamais vues (2/18 positives, sous le p95 des jumeaux) ; glissement réaliste → −0,8 % ; le gain venait des shorts sur SOL en 2026 → abandonné (revue-candidat-sol.md) |
| 16 | Chef d'orchestre (chaque semaine, jouer les K stratégies en forme parmi les 120 du scalp honnête) | ÉCHEC (−49,6 % en 2026), MAIS : bat 1 000/1 000 chefs au hasard (méd. −95,5 %) et divise les pertes par deux vs tout jouer (−95,3 %) ; **la forme persiste d'une semaine à l'autre : Spearman +0,10 en 2024-25 ET en 2026** — premier signal stable du banc. Il perd car tout l'univers perd (frais) |
| 17 | Chef d'orchestre corrigé (score sur les trades déjà SORTIS) — univers A (120 rapides) et B (180 lents 4 h/1 j) | ÉCHEC dans les deux. A : le protocole choisit maintenant (4 sem., 1 strat.) → −78,3 %, 72,6e centile. B : −112 %, pire que tous les chefs au hasard. [info] le réglage du 16 (8 sem., 10 strat.) reste au 100e centile avec le score corrigé (−47,5 % vs −96,5 %) : ce n'était pas un regard vers le futur, mais c'est un choix fait après avoir vu 2026 → ne compte pas. Persistance hebdo : A +0,09/+0,10 ; B +0,03/+0,10 |
| 18 | Chef figé (8 sem., top 10) sur 18 cryptos jamais vues (6 groupes) | Verdict 1 « sait choisir » RÉUSSI (6/6 groupes au 100e centile des chefs au hasard), verdict 2 « rentable » RATÉ (−907 %). **Mais le contrôle (t21b) montre que ce n'est pas du timing** : un chef sans timing qui prend les 10 stratégies qui tradent le moins fait −415 %, deux fois mieux. Revue du quant (22/10) : conclusion à NUANCER — le chef bat le hasard surtout en tradant moins dans une bibliothèque qui perd ; S1 mélange exposition, stratégies figées et stops larges. **Le timing n'est ni confirmé ni réfuté** : le témoin n'égalisait pas le nombre de trades. Bon contrôle à faire (jumeaux stratifiés par case + « chef décalé », marchés neufs) |
| 19 | Scalp avec ordres LIMITES (entrée + objectif en maker 0,02 %, exécutés seulement si le prix traverse) | ÉCHEC, et PIRE qu'au marché : 0/120 positives en 2024-25 (1 avec taker), 3/120 en 2026 (8 avec taker) ; 0/18 cryptos jamais vues positives. **CORRIGÉ après revue (t22b)** : la comparaison n'était pas à armes égales (5 pb de glissement côté limite seulement). À coûts égaux, limite ≈ marché (2026 : 9 vs 8 positives sans glissement, 4 vs 4 avec 5 pb ; sommes un peu moins négatives en limite), remplissage 93 %. La sélection adverse existe (les 7 % ratés font +30 pb) mais annule seulement l'économie de frais. ÉCHEC tient (univers à −12 pb/trade) |
| 20 | Timing du chef (PREREG-20, relu avant calcul) : 18 marchés NEUFS, jumeaux stratifiés T1 + chef à information périmée T2 | **Timing CONFIRMÉ selon le protocole** : +101,7 % (mars 2025 → oct. 2026) vs T1 méd. −524 % et T2 méd. −173 % ; période d'avant (mars 2024 → mars 2025) : +85 % vs T1 −244 %. Audit du quant : pas de bug ni de fuite (reproduit +101,8 %). Nuances : vrai effet du timing = vs T2, ≈ +275 pts ; effet qui s'use en quelques jours, 5 meilleures semaines = 58 pts ; **non démontré sur les 18 anciennes cryptos** (+81 pts, IC −61/+200) ; **rentabilité non démontrée** : marchés peu liquides (30-66 % de bougies plates sur 5 d'entre eux), à 5 pb/côté ≈ −20 % ; doute ouvert : part d'artefact d'illiquidité. Diagnostic de trades de T2 à ajouter |
| 21 | Alignement multi-unités (PREREG-21, relu par le scalpeur avant calcul) : tendance 1 h (+ 15 min), entrée 3/5 min, trades déroulés en 1 min, 180 stratégies, coûts égaux | NON DÉMONTRÉ : 0/180 positives en 2024-25 et en 2026 ; J1 −80,7 % (SOL 5 min F2) vs jumeaux méd. −122 % p99 −65 % ; J2 0/6 marchés jamais vus. Le filtre réduit les pertes du même signal dans 120/120 cas en 2026, MAIS par trade il n'améliore presque rien (62/120 ; −15,2 → −14,6 pb) : il fait surtout trader moins (209 617 → 102 011 trades). Bougies 1 min ambiguës ≤ 0,1 % (granularité OK) |

Page du rapport (privée tant que Tony ne la partage pas) : https://claude.ai/artifact/UXxyHZ3N1x8GYM9ZZo8fDJ

**Moteur générique `banc.py`** (1020 04h28) : une stratégie s'écrit en JSON (`specs/`). Contrôle effectué : il reproduit le test Supertrend 4h de t03 (+4,9 / +19,4 / −38,3 % contre +4,7 / +19,7 / −38,0 %). Un bug de retournement a été trouvé et corrigé pendant le contrôle.

**Bilan provisoire au 1020 04h25 : 3 stratégies virales, 3 échecs.** Elles devaient « gagner » et perdent toutes une fois les frais déduits et leur résultat comparé à celui du hasard. Prochaine étape : une page publique avec les 3 verdicts, et le moyen de proposer une stratégie à tester. La décision de la diffuser revient à Tony.

# Test de Turing inversé : résultats du passage n°1 (2026-10-18, ~20h20)

| compte | coin | heures de test | dont avec ouverture | skill (vs meilleur témoin) | verdict |
|---|---|---|---|---|---|
| 0x6f03… | BTC | 72 | 5 | −0,126 | indécidable |
| 0x8d0c… | SOL | 304 | 1 | −0,095 | indécidable |
| 0x79b1… | ONDO | 140 | 7 | −0,038 | indécidable |
| 0xa0d1… | HYPE | 157 | 1 | −0,63 | indécidable |
| 0x1457978f… | HYPE | 363 | 15 | +0,03 (P>0 = 0,84) | **pas mécanique** |

## Ce que ça dit, honnêtement
- **Le protocole ne tranche presque rien.** L'API ne donne que les 2000 derniers fills, et les ouvertures arrivent par rafales. Il reste donc trop peu d'heures « avec ouverture » dans les 30 % de test (de 1 à 15). C'est une limite du protocole, pas un résultat sur les traders.
- **Avertissement pour le jumeau** : sur 0x6f03, un arbre appris sur les 70 % premières heures fait *moins bien* que le taux de base sur les 30 % suivantes (5 ouvertures seulement, c'est faible). Le jumeau, lui, a été réglé sur 100 % des heures. Son vrai test reste le direct (168 h sur la VM), et ce signal invite à la prudence.
- Le seul compte décidable (0x1457978f, HYPE) n'est pas mécanique au sens du critère : avec des règles simples sur le prix, il n'est pas plus prévisible que son taux de base.

## Suite possible (à pré-enregistrer AVANT de relancer)
Paginer l'historique avec `userFillsByTime` (plusieurs pages de 2000 fills) pour avoir assez d'heures d'ouverture dans le test. Même critère, mêmes comptes.

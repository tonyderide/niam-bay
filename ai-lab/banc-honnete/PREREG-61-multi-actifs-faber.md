# Pré-enregistrement 61 : sortir de la crypto, un portefeuille multi-actifs avec filtre de tendance (Faber 2007)
Écrit le 03/11/2026, avant tout téléchargement et tout calcul. Demande de Tony : « trouve mieux encore » (après les verdicts martingale). Non commité à l'écriture (pas de commit demandé) ; la date de fichier fait foi, preuve plus faible qu'un commit.

Honnêteté sur l'antériorité : je connais déjà la littérature (ce filtre réduit surtout les baisses, moins le rendement). Ce test n'est donc pas à l'aveugle sur l'idée, seulement sur ces chiffres.

## Pourquoi ce test
Le labo a jugé des dizaines de règles sur la crypto, presque rien ailleurs. La règle de Faber (« A Quantitative Approach to Tactical Asset Allocation », 2007) a été publiée avant la période testée : **aucun paramètre n'est choisi ici**, donc pas de grille ni de surapprentissage de ma part.

## Portefeuilles (mensuels, ETF américains, cours ajustés Yahoo)
Univers : SPY, EFA, IEF, VNQ, DBC (actions US, actions monde, obligations 7-10 ans, immobilier, matières premières).
- **A** : 100 % SPY, acheté et gardé.
- **B** : 60 % SPY + 40 % IEF, rééquilibré chaque mois.
- **C** : 20 % sur chacun des 5, rééquilibré chaque mois.
- **D (la règle testée)** : 20 % par actif ; un actif est tenu le mois M+1 si sa clôture de fin du mois M dépasse sa moyenne des 10 dernières clôtures mensuelles, sinon sa part va au cash (^IRX / 12).
Coûts : 0,10 % sur chaque montant échangé. Impôts ignorés.

## Période
Premier mois de performance 01/2007, dernier 10/2026. Sous-périodes : 2007-2016 et 2017-10/2026.

## Verdict de D contre A
- **« MIEUX EN RISQUE »** si, sur toute la période : baisse maximale de D ≤ 60 % de celle de A, Sharpe (excès sur le cash) de D > Sharpe de A avec p < 0,05 (bootstrap par blocs de 12 mois, 10 000 tirages, unilatéral), **et** baisse maximale plus faible que A sur les 2 sous-périodes.
- **« MOINS DE BAISSES, PAS D'AVANTAGE »** si les conditions de baisse tiennent mais pas le p.
- **« PAS MIEUX »** sinon.
Rendement annualisé de D rapporté contre A, B, C, sans condition. Si D gagne moins que A, c'est écrit en tête.

## Limites annoncées
Une seule période, ETF américains (non achetables tels quels par un particulier européen, équivalents UCITS à vérifier), pas d'impôts. Aucun résultat ne rend la règle infaillible. Rien n'est branché sur un compte.

## Résultat (03/11/2026 — t61.py, cours Yahoo, 01/2007 → 10/2026, 238 mois)
**D gagne moins que A : 5,3 %/an contre 10,8 %/an.**

| | A : SPY | B : 60/40 | C : 5 actifs | D : 5 actifs + filtre |
|---|---|---|---|---|
| Rendement annualisé net | 10,8 % | 8,0 % | 6,0 % | 5,3 % |
| 1 € devient | 7,65 € | 4,63 € | 3,17 € | 2,76 € |
| Volatilité | 15,3 % | 9,4 % | 12,2 % | 6,6 % |
| Sharpe | 0,65 | 0,71 | 0,41 | 0,57 |
| Baisse maximale (clôtures mensuelles) | −50,8 % | −29,5 % | −43,5 % | −11,4 % |
| Baisse max 2007-2016 / 2017-2026 | −50,8 / −23,9 | −29,5 / −20,5 | −43,5 / −17,7 | −11,4 / −5,8 |
| Pire année | 2008 : −36,8 % | 2008 : −18,0 % | 2008 : −26,5 % | 2022 : −4,9 % |
| Années négatives (sur 20) | 3 | 3 | 4 | 5 |

Sharpe D − A : −0,076 par an, p = 0,61. Exposition moyenne de D : 67 %.

**VERDICT (pré-enregistré) : « MOINS DE BAISSES, PAS D'AVANTAGE ».** Baisse maximale de D = 22 % de celle de A (≤ 60 %) et plus faible sur les 2 sous-périodes ; Sharpe non supérieur.

Limites : baisses mesurées aux clôtures mensuelles (en cours de mois, elles sont plus fortes) ; un krach d'un mois n'est pas évité par un signal mensuel ; une seule période, pas d'impôts.

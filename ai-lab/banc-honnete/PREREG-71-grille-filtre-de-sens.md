# PREREG-71 — La grille en continu, avec ou sans filtre de sens

Écrit le 09/11/2026, **avant tout calcul**. Script : `t71.py`, qui réutilise le simulateur `sim` de t70 et `regime`/`couper`/`ms` de t69.

## Pourquoi
Demande de Tony le 08/11. Le soir du 08/11, en réel, les 4 grilles ont acheté pendant toute une chute de −3,4 % en 15 minutes ; ADA a acheté 6 fois. Depuis 23h35 UTC, la pause « marché agité » est retirée : les grilles tournent en permanence.
Question : bloquer les entrées contre la tendance de fond améliore-t-il la grille ?

## Modèles (1 000 € par paire ; SOL, LINK, ADA, DOT ; écart 1,2 % ; 5 niveaux ; levier 5)
Les deux partent du modèle R+ de PREREG-70 :
- position plafonnée à 5 × la mise ;
- vrai stop à −15 % avec pause de 24 h ;
- arrêt définitif d'une paire sous 60 % ;
- protection objectif/stop, disjoncteur RSI 1 h < 25, recentrage en gardant la position.

- **A — « en service »** : ce qui tourne depuis le 08/11 23h35 UTC. Pas de pause de régime : le régime est toujours « tradable ».
- **B — « filtre de sens »** : A, plus un filtre sur la tendance. Sur la dernière bougie 1 h close, EMA50 et EMA200 des clôtures horaires :
  - EMA50 ≥ EMA200 (tendance haussière) : une vente qui ouvrirait ou augmenterait un short est sautée ;
  - EMA50 < EMA200 (tendance baissière) : un achat qui ouvrirait ou augmenterait un long est sauté ;
  - les ordres qui réduisent la position passent toujours.
  Ce sont les mêmes EMA que le `SignalService` de Martin (emaStatus).

Pour information seulement : R+ **avec** la pause de régime (ADX < 40, BBW < 4 %), déjà calculé par PREREG-70.

## Verdict (périodes P1 = 02/2024 → 12/2025 et P2 = 01 → 09/2026)
- **B « TIENT »** si, sur P1 **et** P2 : B total > 0, B > A, au moins 3 paires sur 4 positives, aucune paire liquidée ni arrêtée définitivement, baisse maximale du portefeuille meilleure que −30 %.
- **« MIEUX SANS SUFFIRE »** si B > A sur P1 et P2 sans remplir le reste.
- **« NON »** sinon.

## Limite connue, écrite d'avance
Le témoin de fidélité de PREREG-70 a échoué : le simulateur reproduit les exécutions réelles (98,7 %), mais pas le gain d'avril. Un « TIENT » ici ne vaudra donc pas preuve. Il justifierait seulement d'essayer B en réel avec les mises actuelles (≈ 5 $), sous la garde.

## Prédiction
B > A sur P1 et P2, car il évite les achats en série pendant les chutes. Mais B reste négatif : les frais, environ 0,2 € par exécution, mangent l'avantage de la grille. Verdict prédit : **« MIEUX SANS SUFFIRE »**.

## Conséquence écrite d'avance
- **TIENT** : je propose à Tony de passer B en réel.
- **MIEUX SANS SUFFIRE** : je propose B en réel, en lui disant clairement que ça perd moins, pas que ça gagne.
- **NON** : rien ne change.

## Résultat (09/11/2026 — t71.py, t71.json ; 1 000 € par paire, 4 paires)
**VERDICT (pré-enregistré) : NON.** B fait moins bien que A sur P1, à peine mieux sur P2, et les deux perdent lourdement.

| | Total | Avant frais | Frais | Exécutions | Paires arrêtées définitivement (< 60 %) | Baisse max. du portefeuille |
|---|---|---|---|---|---|---|
| A P1 (en service) | −1 713 € | +623 € | 2 336 € | 9 343 | 4/4 | −46 % |
| B P1 (filtre de sens) | −1 756 € | −390 € | 1 366 € | 5 429 | 4/4 | −50 % |
| A P2 | −1 606 € | −460 € | 1 146 € | 4 501 | 3/4 | −44 % |
| B P2 | −1 568 € | −708 € | 860 € | 3 304 | 3/4 | −44 % |

Pour information, R+ **avec** la pause de régime (PREREG-70) : −1 631 € sur P1, −1 326 € sur P2.

Lecture :
- Le filtre réduit le nombre d'exécutions d'environ 40 %, donc les frais, mais il fait perdre plus avant frais. Dans ce simulateur, la grille gagne surtout sur les rebonds contre la tendance : les bloquer retire aussi les gains.
- La grille en continu (A) perd plus que la grille avec pause sur P2 : −1 606 € contre −1 326 €.
- Sur P1, A gagne +623 € avant frais. Les frais (≈ 0,25 € par exécution sur une position de 1 000 €) en font −1 713 €.
- Rappel : le témoin de PREREG-70 a échoué. Ces chiffres disent que rien dans cette famille ne gagne dans le simulateur. Ils ne garantissent pas les montants réels.

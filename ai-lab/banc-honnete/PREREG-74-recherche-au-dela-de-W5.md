# PREREG-74 — Chercher mieux que la grille à 5 %, sans se tromper soi-même

Écrit le 12/11/2026, **avant tout calcul**. Script : `t74.py`, qui réutilise `sim`, `danger` et `tendance` de t73 et `regime` de t69.

## Pourquoi
Tony demande une meilleure stratégie. En service depuis le 09/11 21h34 : W5 (écart 5 %, levier 10), qui faisait +881 € sur P1 et −245 € sur P2 dans PREREG-73. Essayer beaucoup de variantes et garder la meilleure, c'est le piège classique : la meilleure sur un jeu de données l'est souvent par chance. D'où un protocole en deux temps.

1. **Choix sur P1 seulement** (02/2024 → 12/2025, les 4 paires en service).
2. **Contrôle, une seule fois, sur des données jamais utilisées pour choisir :**
   - P2 (01 → 09/2026) sur les 4 paires ;
   - 6 paires que la grille n'a **jamais** vues : ATOM, AVAX, BCH, BNB, XRP, LTC, sur P1 et sur P2.

## Variantes (1 000 € par paire, 5 niveaux, tous les garde-fous R+, pas de pause de régime sauf mention)
- **W5** : en service. Témoin : il doit redonner +881,4 € (P1) et −245,0 € (P2), sinon NON CONCLUANT.
- **W7**, **W10** : écart 7 % et 10 %.
- **W5R**, **W7R** : niveaux reposés quand la position revient à zéro (refusé à 1,2 % dans PREREG-72, mais à 5 % les frais pèsent bien moins).
- **W5P**, **W7P** : pause de régime remise (ADX < 40, BBW < 4 %), comme avant le 08/11.
- **W5F** : filtre de sens EMA50/200 1 h (refusé à 1,2 % dans PREREG-71).

## Règle de choix (sur P1, 4 paires)
X\* = la variante au total P1 le plus élevé parmi celles sans paire liquidée ou arrêtée et avec une baisse du portefeuille meilleure que −30 %. W5 est candidate : si W5 gagne, on ne change rien.

## Contrôles sur X\*
- **T1** : 4 paires, P2 : total > 0.
- **T2** : 6 paires neuves, P1 : total > 0, au moins 4 paires sur 6 positives, aucune arrêtée.
- **T3** : 6 paires neuves, P2 : total > 0.

## Verdict
- **TIENT** : X\* ≠ W5 et T1, T2, T3 passent → je propose X\* en réel.
- **MIEUX QUE W5 SANS PREUVE** : X\* ≠ W5, X\* bat W5 sur P2 (4 paires) **et** sur les 6 paires neuves (P1 + P2 cumulés), sans passer tous les contrôles → je le propose en disant clairement que ça perd peut-être moins, pas que ça gagne.
- **NON** sinon → on garde W5.
- Pour information, sans verdict : W5 sur les 6 paires neuves (est-ce que la grille en service tient ailleurs que sur ses 4 paires ?).

## Prédiction
X\* = W10 ou W7 : la tendance de PREREG-73 continue sur P1. T1 échoue (2026 est une année de baisse des altcoins). T2 est mitigé. Verdict prédit : **MIEUX QUE W5 SANS PREUVE**.

## Limites connues
Le simulateur n'a pas reproduit avril (PREREG-70). Il a en revanche retrouvé le signe et l'ordre de grandeur des jours réels du 08 au 11/11 (bilans quotidiens). Les 6 paires neuves sont des données Binance, pas Kraken.

## Résultat (12/11/2026 — t74.py, t74.json, t74.log) — témoin OK (W5 redonne +881,4 / −245,0)
**VERDICT (pré-enregistré) : NON — W5 reste la meilleure sur P1.** Ma prédiction (X\* = W7 ou W10) était fausse.

| Variante | P1, 4 paires | Paires arrêtées | Baisse max. |
|---|---|---|---|
| **W5 (en service)** | **+881 €** | 0 | −20 % |
| W7 | −995 € | 1 (ADA) | −33 % |
| W10 | +523 € | 0 | −14 % |
| W5R (reposés) | −1 887 € | 4 | −46 % |
| W7R | −1 962 € | 4 | −49 % |
| W5P (pause) | −1 129 € | 2 | −39 % |
| W7P | −1 062 € | 1 | −36 % |
| W5F (filtre sens) | −91 € | 0 | −15 % |

Contrôles (sur W5, puisqu'elle est choisie) : T1 4 paires P2 −245 € ✗ ; **T2 6 paires neuves P1 −1 120 €, 2/6 positives, 3 arrêtées (AVAX, BCH, LTC)** ✗ ; T3 6 paires neuves P2 −373 € ✗.

Lecture :
- **La découverte importante : W5 ne tient pas hors de ses 4 paires.** Sur 6 paires jamais vues, elle perd sur les deux périodes et 3 paires sur 6 sont arrêtées en 2024-2025. Le +881 € de PREREG-73 tient très probablement au choix de SOL/LINK/ADA/DOT, pas à la règle.
- La suite des écarts n'est pas régulière (5 % : +881, 7 % : −995, 10 % : +523) : c'est le signe d'un résultat dominé par le hasard des parcours de prix, pas d'un réglage qui s'améliore.
- Reposer les niveaux et remettre la pause sont nettement pires, comme à 1,2 %.
- Conséquence prévue : on garde W5. Mais il faut dire à Tony que rien dans la famille « grille » ne montre d'avantage solide, W5 compris.

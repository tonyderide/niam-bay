# PREREG-72 — Remettre les niveaux en place quand la grille revient à zéro

Écrit le 09/11/2026 à environ 01h50 UTC, **avant tout calcul**. Script : `t72.py`, qui reprend le simulateur de t71 avec une option de plus.

## Pourquoi
Nuit du 09/11, en réel : chaque grille a fait un aller-retour sur ses deux niveaux centraux, puis s'est arrêtée de trader. Ces niveaux sont « déjà servis » et la version d'avril ne les repose pas. Il ne reste que des ordres éloignés (−1,5 et +1,5, +2,5 écarts).
Tony veut que ça trade plus souvent. Question : reposer les niveaux améliore-t-il le résultat ?

## Modèles (1 000 € par paire ; SOL, LINK, ADA, DOT ; écart 1,2 % ; 5 niveaux ; levier 5 ; tous les garde-fous R+ de PREREG-70)
- **A — « en service »** : ce qui tourne depuis le 08/11 23h35 UTC, sans pause de régime. C'est le A de PREREG-71, et ses chiffres doivent être retrouvés à l'identique : c'est le témoin que le script n'a rien cassé.
- **C — « niveaux reposés »** : A, plus une règle. Quand la position revient exactement à 0, tous les niveaux de la grille sont remis en place, à leurs prix et avec le même centre, actifs à la minute suivante. Le plafond de position et le reste sont inchangés.

## Verdict (P1 = 02/2024 → 12/2025, P2 = 01 → 09/2026)
- **Témoin** : A doit redonner exactement −1 713,2 € sur P1 et −1 606,0 € sur P2 (PREREG-71). Sinon, le résultat est NON CONCLUANT.
- **C « TIENT »** si, sur P1 **et** P2 : C total > 0, C > A, au moins 3 paires sur 4 positives, aucune paire liquidée ni arrêtée, baisse maximale du portefeuille meilleure que −30 %.
- **« MIEUX SANS SUFFIRE »** si C > A sur P1 et P2 sans remplir le reste.
- **« NON »** sinon.

## Prédiction
Plus d'allers-retours, donc plus de gains avant frais, mais aussi plus de frais. Comme avant frais la grille gagne à peine (+623 € sur P1, −460 € sur P2 pour A), je prédis **« NON »** : C perd davantage, à cause des frais.

## Conséquence écrite d'avance
- **TIENT** : je propose C en réel.
- **MIEUX SANS SUFFIRE** : je propose C en réel, en disant clairement que ça perd moins, pas que ça gagne.
- **NON** : rien ne change, et je le dis à Tony.

Même limite que PREREG-70 et 71 : le simulateur n'a pas reproduit avril. Il a en revanche retrouvé le signe de chaque paire le soir du 08/11 (−4,4 c simulés contre −2,3 c réels).

## Résultat (09/11/2026 — t72.py, t72.json)
**Témoin OK** : A redonne exactement −1 713,2 € sur P1 et −1 606,0 € sur P2. **VERDICT (pré-enregistré) : NON.** Reposer les niveaux fait perdre davantage sur les deux périodes.

| | Total | Avant frais | Frais | Exécutions | Paires arrêtées définitivement | Baisse max. du portefeuille |
|---|---|---|---|---|---|---|
| A P1 (en service) | −1 713 € | +623 € | 2 336 € | 9 343 | 4/4 | −46 % |
| C P1 (niveaux reposés) | −1 923 € | −575 € | 1 348 € | 4 046 | 4/4 | −48 % |
| A P2 | −1 606 € | −460 € | 1 146 € | 4 501 | 3/4 | −44 % |
| C P2 | −1 865 € | −104 € | 1 761 € | 5 273 | 4/4 | −48 % |

Lecture : en reposant ses achats, C accumule plus vite pendant les baisses. Ses paires atteignent plus tôt l'arrêt définitif à 60 % : moins d'exécutions sur P1, parce qu'elles meurent avant. Sur P2, C trade plus et paie plus de frais. Dans les deux cas, C fait pire. La version d'avril, qui ne repose pas les niveaux, limite les dégâts.

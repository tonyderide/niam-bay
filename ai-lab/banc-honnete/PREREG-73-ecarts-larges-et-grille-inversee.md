# PREREG-73 — Écarts plus larges et grille inversée

Écrit le 09/11/2026, **avant tout calcul**. Script : `t73.py`, qui reprend le simulateur de t72 avec deux paramètres : l'écart et le sens.

## Pourquoi
PREREG-71 et 72 : la grille à 1,2 % perd sur 2024-2025 comme sur 2026, surtout à cause des frais (2 336 € de frais sur P1 pour +623 € de gain avant frais). Tony demande deux pistes :
1. trader moins souvent, avec plus de gain par aller-retour, en élargissant l'écart ;
2. aller dans l'autre sens, avec une grille qui suit la tendance.

## Variantes
Base commune : 1 000 € par paire ; SOL, LINK, ADA, DOT ; 5 niveaux ; levier 5 ; tous les garde-fous R+ ; pas de pause de régime (comme en service) ; niveaux non reposés.

- **A** : écart 1,2 %, sens normal. C'est le témoin, qui doit redonner −1 713,2 € sur P1 et −1 606,0 € sur P2.
- **W2, W3, W5** : sens normal, écart de 2 %, 3 % et 5 %.
- **I1.2 et I3** : grille **inversée**, écart de 1,2 % et 3 %. Les niveaux sont aux mêmes prix que la grille normale, mais :
  - ceux du dessous sont des **ventes** qui se déclenchent quand le prix descend à travers (ordres stop) ;
  - ceux du dessus sont des **achats** qui se déclenchent quand le prix monte à travers ;
  - l'exécution se fait au prix du niveau, ou au premier prix disponible si le prix l'a sauté, avec les frais d'un ordre au marché (0,05 %) ;
  - recentrage, plafond et protections sont identiques.

## Verdict par variante (P1 = 02/2024 → 12/2025, P2 = 01 → 09/2026)
- **Témoin** : si A ne redonne pas ses chiffres, tout le test est NON CONCLUANT.
- **« TIENT »** si, sur P1 **et** P2 : total > 0, au moins 3 paires sur 4 positives, aucune paire liquidée ni arrêtée définitivement, baisse maximale du portefeuille meilleure que −30 %.
- **« MIEUX SANS SUFFIRE »** si le total bat A sur P1 et P2 sans remplir le reste.
- **« NON »** sinon.
- Cinq variantes sont testées en même temps : une seule qui « tient » de justesse peut être un coup de chance. Je le signalerai, sans changer le verdict.

## Prédiction
- W5 > W3 > W2 > A, parce que les frais baissent beaucoup plus vite que les gains, mais toutes restent négatives sur au moins une période. Verdict prédit : « MIEUX SANS SUFFIRE » pour W3 et W5, « NON » pour le reste.
- I1.2 : « NON », moins bien que A sur P1 (estimation : environ −2 960 €).
- I3 : « NON ».

## Conséquence écrite d'avance
- **Une variante TIENT** : je propose de la mettre en réel avec les petites mises actuelles et le bilan quotidien. Elle remplacerait la grille à 1,2 % sur une ou deux paires d'abord.
- **MIEUX SANS SUFFIRE** : je propose à Tony de passer à cette variante, en lui disant clairement qu'elle perd moins, pas qu'elle gagne.
- **NON partout** : la grille ne mérite pas d'argent réel. Je le dis à Tony, et c'est lui qui décide de la suite.

Même limite que PREREG-70 à 72 : le simulateur n'a pas reproduit avril. Il a retrouvé le signe des 4 paires le soir du 08/11.

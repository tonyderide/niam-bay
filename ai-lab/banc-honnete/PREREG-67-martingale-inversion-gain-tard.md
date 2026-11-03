# Pré-enregistrement 67 : martingale avec inversion, avec la sortie « stopper tôt, prendre tard »
Écrit le 03/11/2026 au soir, avant tout calcul. Non commité à l'écriture : la date du fichier fait foi. Demande de Tony : « martingale avec inversion », trailing dans les deux sens, un trade à la fois.

Déjà vu : PREREG-28 et 34, avec activation ≤ 5 % : risque non maîtrisé. La sortie de PREREG-66 (activation 10 %) n'a jamais été combinée à une martingale. Prédiction d'avance : la martingale ne crée pas d'espérance mais accentue les pertes dans une série ; or à 36 % de gagnants les séries de pertes sont longues, donc la ruine devrait augmenter.

## Règle
Sortie figée : SL 5 %, activation +10 %, trailing 1 %. Toujours en position, sens inversé après une perte, gardé après un gain, 1 min, frais 0,05 % par côté, sans financement.
Capital 1 000 €, mise de base 10 € (perte si le SL est touché ; position = mise / 5 %). Après une perte : mise × m ; après un gain, ou après k pertes d'affilée : retour à 10 €. Position ≤ 10 × le capital. Capital < 50 € : arrêt.
**Réglage jugé, sans choix : m = 2, k = 4.** Rapportés pour information : m ∈ {1 ; 1,5 ; 2 ; 3}, k ∈ {2 ; 4 ; 6 ; ∞}.

## Données
Jugement : XRP, DOGE, ADA, LINK, AVAX, LTC, BNB, DOT, BCH, ATOM. P1 = 01/02/2024 → 31/12/2025. P2 = 01/01 → 30/09/2026. Un compte par pièce sur toute la période, plus des départs de 3 mois chaque mois (perte et ruine). BTC, ETH et SOL rapportés à part.

## Verdict
**« TIENT »** si sur P1 ET P2 : résultat moyen > 0, au moins 6 pièces sur 10 positives, aucune pièce tombée à ≤ 500 €, résultat moyen supérieur à un sens au hasard dans ≥ 95 % de 200 tirages. **« GAGNE MAIS RISQUE NON MAÎTRISÉ »** si le résultat moyen est > 0 sur P1 et P2 sans le reste. **« NON »** sinon.

## Résultat (03/11/2026 — t67.py). m = 2, k = 4, 10 pièces, 1 000 € par pièce
| | Résultat moyen | Médian | Positives | Capital le plus bas | Pièces ≤ 500 € | Départs 3 mois en perte / ruinés | Témoin hasard, battu |
|---|---|---|---|---|---|---|---|
| P1 | +525 € | +75 € | 5/10 | 33 € | 2 | 37 % / 6,2 % | +41 €, 93,0 % |
| P2 | −15 € | −55 € | 5/10 | 387 € | 4 | 56 % / 1,4 % | −6 €, 48,5 % |

**VERDICT (pré-enregistré) : « NON »** (résultat moyen négatif sur P2). Sans martingale (m = 1, même mise de 10 €) : +227 € sur P1, +51 € sur P2, seul type de réglage positif sur les deux périodes avec les m = 1,5 et 2 à k = 2 ; information non jugée, grille non corrigée.

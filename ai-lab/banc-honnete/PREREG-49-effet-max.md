# Pré-enregistrement 49 : l'effet loterie (MAX) — les pièces au plus gros jour de hausse du mois passé sous-performent-elles ?
Écrit le 01/11/2026 vers 21h CET, avant tout calcul. Hypothèse H13 de FILE-HYPOTHESES.md. `scripts/cherche -v loterie rendement maximal MAX` : rien d'identique.

## Raison économique, et ce que dit la théorie avant les données
Bali, Cakici & Whitelaw (2011) : les investisseurs aiment les « billets de loterie » (actifs capables d'un jour énorme) et les paient trop cher ; les actions au plus fort rendement journalier du mois passé rapportent moins ensuite. Signal différent du momentum (un seul jour extrême, pas la tendance des semaines). **Biais connu, déclaré** : PREREG-41 a montré après coup qu'en 2026 les gagnantes de la semaine ont sous-performé ; or les pièces à fort MAX sont souvent des gagnantes récentes, ce qui favorise la règle en 2026. D'où la condition sur l'historique (2024-25, non contaminé par cette observation) en plus du jugement 2026.

## Données
Celles de PREREG-39/41/44/48 (253 perpétuels Binance cotés au 01/01/2024, morts compris, `couper`, jours UTC, semaines du lundi).

## Règle (aucun réglage)
- Chaque lundi : MAX = plus grand rendement journalier (clôture / clôture précédente − 1) des 30 jours précédents, pour les pièces vivantes ayant au moins 25 rendements sur ces 30 jours.
- **Short le quintile au MAX le plus élevé, long le quintile au MAX le plus faible**, poids égaux, ½ par côté, une semaine (ouverture → ouverture du lundi suivant ; dernier prix si retrait). Frais taker 0,05 % sur chaque variation de poids. Sans funding.

## Jugement
- Historique : semaines du 05/02/2024 au 29/12/2025. **JUGEMENT UNIQUE : 05/01/2026 → 21/09/2026.**
- **Témoin à rotation égale** (comme PREREG-41/44/48), 1 000 tirages, graine 49.
- **GAGNE** si net > 0 sur l'historique **ET** > 0 en 2026 **ET** p < 0,05 en 2026. **NON DÉMONTRÉ** si net 2026 > 0 sans le reste. **PERD** sinon.

## Relecture d'équité
30 jours, 25 rendements minimum, quintiles fixés ici ; biais 2026 déclaré ci-dessus. Aucune action sur Martin ni Kraken.

## Résultat (01/11/2026, 21h1x — t49.py → t49.log, chiffres dans t49.json)
Lancé une seule fois après le commit 2addd9e, `nice -n 10`. 243 pièces.

| | Historique (02/2024 → 12/2025) | **2026** |
|---|---|---|
| Net | **+26,8 %** | **+2,5 %** |
| Brut / frais | +29,5 / 2,7 | +3,5 / 1,0 |
| Jambe longue (MAX faible) / courte (MAX fort) | +11,7 / +17,8 | −0,6 / +4,1 |
| Bêta réalisé contre BTC | −0,11 | −0,05 |
| Semaines positives / pire baisse | 53 % / 11,4 pts | 50 % / 6,9 pts |
| Témoin à rotation égale | −0,9 ± 12,4 % | −0,8 ± 9,0 % |
| p | **0,008** | **0,35** |

**VERDICT (pré-enregistré) : NON DÉMONTRÉ** — positif sur les deux périodes, net au-dessus du hasard en 2024-25 (p = 0,008), mais trop faible en 2026 (+2,5 %, p = 0,35).

**Ce que ça montre :**
- C'est le signal entre pièces le plus propre trouvé à ce jour : positif sur les deux périodes, les deux jambes gagnantes en 2024-25, bêta presque nul, pire baisse de 7 à 11 points, peu de frais (rotation modérée, 73-75 % des noms gardés).
- Mais en 2026 l'effet a fondu (+2,5 % en 9 mois), malgré le biais déclaré en sa faveur (renversement hebdo de 2026). On ne peut pas le distinguer du hasard sur cette période.
- Candidat sérieux pour un **test en avant** (comme PREREG-35/45/47) : signal fixé, aucun réglage, raison économique (loterie), et il n'a jamais été négatif. À pré-enregistrer dans un prochain tick.

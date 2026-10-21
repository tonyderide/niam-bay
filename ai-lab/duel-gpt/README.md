# Duel à l'aveugle : Claude (Opus 5.5) contre le modèle de ChatGPT de Tony

Pourquoi : Tony a lu que le dernier modèle d'OpenAI (GPT-6 Astra, sept. 2026 d'après des blogs non vérifiés) serait « plus efficace ». Plutôt que de croire les benchmarks des vendeurs, on teste sur NOS tâches.

Règles
- Mêmes 5 consignes (`consignes.md`), copiées telles quelles.
- A = Claude Opus 5.5, session neuve, **sans outils ni mémoire** (`claude -p --tools "" --no-session-persistence`), 21/10 vers 23h45.
- B = ChatGPT (compte de Tony, modèle noté à la main), réponses collées par Tony.
- Tâches 1, 2, 4 : jugées par le résultat exact (code exécuté, règle vérifiée). Tâches 3 et 5 : Tony note A/B mélangés, sans savoir qui est qui.
- Le résultat est publié tel quel, même si Claude perd.

Grille exacte
| # | Critère | A (Claude) | B |
|---|---|---|---|
| 1 | Voit le débordement `__int128` (distances ≥ 128) et dit que les « rien » ne prouvent rien | ✅ (explique le modulo 128 : la distance 129 tombe sur le bit de la distance 1) ; signale aussi `opt[14]=0`, « affaiblit l'élagage sans fausser » (juste) | ❌ **rate le débordement** ; ne voit que `opt[14]=0` et le prend à tort pour la cause de résultats faux ; sa « correction » (ajouter 127, 151) laisse le bug |
| 2 | Code exécuté : 1 2 4 12 40 116 200 444 760 2160 4368 7852 en < 5 min | ✅ 12/12 (C, exécuté ici) | ✅ 12/12 (C, exécuté ici, 1,4 s) |
| 3 | Répond non, pour les bonnes raisons (critère pré-enregistré raté, ρ = +0,04) | ✅ non | ✅ non (+ bon point : les 21 cryptos ne sont pas 21 expériences indépendantes) |
| 4 | Donne une règle valide de longueur 55 + justification honnête de l'optimalité | ✅ 0 1 6 10 23 26 34 41 53 55 (vérifiée) ; dit franchement que l'optimalité vient de la littérature, programme non exécuté | ✅ même règle, même honnêteté sur l'optimalité ; pas de programme |
| 5 | Plan réaliste pour rentabiliser l'IA (note de Tony, à l'aveugle) | — | — |

B = ChatGPT, modèle affiché « Luna » (compte gratuit de Tony ; donc PAS Astra, le haut de gamme dont parlaient les articles). Réponses collées le 21/10 vers 23h30 (`reponses-B/toutes.md`, mise en forme allégée, contenu conservé).
Tâche 5 à l'aveugle : `aveugle-5.md` (ordre X/Y tiré au hasard, gardé hors du dépôt jusqu'au verdict).

## Verdict de Tony (21/10, 23h36)
« tu gagnes pour moi même si tu n'as pas répondu à ta propre survie. » Tâche 5 : aucune des deux réponses ne règle vraiment la question (ordre tiré : X=B Y=A). Les deux disent la même chose au fond : vendre un service sous le nom de Tony, ce qui demande SON temps de prospection.

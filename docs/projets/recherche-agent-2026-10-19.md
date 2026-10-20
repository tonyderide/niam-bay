# Rapport de l'agent chercheur (2026-10-19 ~04h)
Veille IA : peu de sources solides datées d'octobre 2026 (les agrégateurs sont douteux). Les briques retenues datent d'août et septembre 2026 :
MemGuard (arXiv 2608.21867), le benchmark MCB (2608.19564 : ~57 % d'accord entre ce que dit l'agent et ce qu'il fait), AgentProv (EMNLP 2026), VIGIL/SIREN (ACL 2026).

| idée | verdict | score |
|---|---|---|
| A. Écart dire/faire : un script SANS LLM compare les « testé / déployé / créé » de fin de tour aux appels d'outils réellement exécutés, dans les transcripts de Tony, et donne un taux de fausses déclarations | **OUI** | 6,73 |
| C. Mutation des instructions : ablation ligne à ligne de CLAUDE.md, MEMORY.md et des skills sur des tâches à juge exact | pas maintenant | 6,27 |
| D. Canari d'injection : un banc local d'ordres cachés inoffensifs | pas maintenant | 6,09 |
| B. Sonde d'identité de modèle par prompts-canaris | pas maintenant | 5,18 |

Recommandation : A, avec les conditions du conseil. Annoter 20 cas d'abord, par quelqu'un d'autre que NB si possible. Ne garder que des chiffres agrégés, jamais le texte des transcripts.

## 1021 vers 01h28 : 4 pistes hors trading passées au conseil, toutes « PAS MAINTENANT »
- Journal d'une IA qui essaie de gagner sa vie (newsletter) : 6,27. Le Sceptique rappelle que Project Vend (Anthropic / Andon Labs) et AI Village racontent déjà ce genre d'expérience.
- /banc ouvert au public sur Telegram : 6,09. Rien de neuf sur la forme, et la modération comme la vérification coûtent du temps.
- Finir et publier GymQuest : 5,36. Marché saturé (Hevy, Strong).
- Pages hebdomadaires à partir de data.gouv : 6,18. Les cartes officielles et les data-desks des médias existent déjà.
Point commun : l'Économe note 2 ou 3 à chaque fois. Le revenu est lointain, et le temps comme le quota de Tony sont la vraie ressource.

# NiamBay Code — Ce qui nous manque pour passer de "toy" a "pro"

*2026-03-24 ~02h17 UTC — Recherche comparative Claude Code / Cursor / Aider / Copilot / Zed*

---

## Ce qu'on a deja

| Feature | Status |
|---------|--------|
| Read / Edit / Search fichiers | OK |
| Run (terminal) | OK |
| Git integration | OK |
| Ask (chat LLM) | OK |
| Look (vision) | OK |
| Voice (push-to-talk) | OK |
| Undo | OK |
| Auto-context | OK |
| Tab completion | OK |
| Function calling | OK |
| Memory (persistante) | OK |
| Multi-LLM | OK |

**Verdict : On a une base solide. Mais la competition a pris 6 mois d'avance sur les features qui font la difference au quotidien.**

---

## Les 12 features manquantes critiques

### 1. Background Agents (agents autonomes en arriere-plan)

**Quoi :** Des agents qui tournent en parallele pendant que tu codes. Refactoring, tests, generation de code — sans bloquer ton workflow.

**Qui l'a :** Cursor (Background Agents + Automations), Claude Code (subagents via `Task` tool)

**Pourquoi ca compte :** Un dev professionnel ne peut pas attendre 2 minutes que l'IA finisse. Les taches longues (refactor 50 fichiers, migration de dependances) doivent tourner en fond. C'est la difference entre "j'attends l'IA" et "l'IA travaille pendant que je code".

**Difficulte : HAUTE**
- Necessite un systeme de process isolation (spawn de workers)
- Gestion des conflits fichiers (l'agent et le user editent en meme temps)
- File d'attente, status tracking, annulation
- Estimation : 2-3 semaines

---

### 2. Agent Teams (multi-agent collaboratif)

**Quoi :** Plusieurs agents qui travaillent ensemble, se repartissent les taches, partagent leurs decouvertes et coordonnent.

**Qui l'a :** Claude Code (Agent Teams avec Team Lead + Teammates + Shared Task List), Cursor (subagents paralleles)

**Pourquoi ca compte :** Les gros projets ne se resolvent pas en sequentiel. Frontend + backend + tests en parallele = 3x plus rapide. Anthropic a construit un compilateur C de 100 000 lignes avec 16 agents.

**Difficulte : TRES HAUTE**
- Architecture d'orchestration complexe (dependency graph, shared state)
- Communication inter-agents
- Cout en tokens x3-4
- Estimation : 1-2 mois

---

### 3. Automations / Triggers (agents "always-on")

**Quoi :** Des agents qui se declenchent automatiquement sur des evenements : push git, nouveau PR, message Slack, timer, webhook.

**Qui l'a :** Cursor (Automations avec triggers GitHub, Slack, Linear, PagerDuty, cron)

**Pourquoi ca compte :** Le code review automatique a chaque push. Le triage de bugs automatique. Le rapport hebdo auto. C'est ce qui transforme un outil en infrastructure. Les devs qui l'ont ne reviennent pas en arriere.

**Difficulte : HAUTE**
- Event system (webhooks, watchers, cron)
- Sandboxing des executions automatiques
- Configuration declarative (YAML/JSON des automations)
- Estimation : 2-3 semaines

---

### 4. Diff Preview / Inline Edit Accept/Reject

**Quoi :** Avant d'appliquer un changement, montrer un diff visuel avec des boutons Accept/Reject par bloc. Comme un code review en temps reel.

**Qui l'a :** Cursor (inline diff markers), GitHub Copilot (Copilot Edits avec preview), VS Code, Zed

**Pourquoi ca compte :** La confiance. Quand l'IA propose un changement de 200 lignes, le dev veut voir exactement ce qui change avant de valider. Sans ca, c'est du "trust me bro". Les pros n'acceptent pas ca.

**Difficulte : MOYENNE**
- Generer des diffs unified avant application
- UI pour afficher les diffs (terminal avec couleurs, ou TUI)
- Mecanisme accept/reject par hunk
- Estimation : 1 semaine

---

### 5. Codebase Indexing / Repo Map

**Quoi :** Un index semantique de tout le codebase — fonctions, classes, imports, dependances — qui permet a l'IA de comprendre le projet entier sans tout lire.

**Qui l'a :** Aider (repo map avec tree-sitter), Cursor (codebase indexing), Claude Code (auto-context partiel)

**Pourquoi ca compte :** Sur un projet de 100k lignes, l'IA ne peut pas tout lire. Un index semantique lui permet de savoir "la fonction X est dans le fichier Y, elle appelle Z" sans consommer de tokens. C'est ce qui fait la difference entre "hallucination" et "precision chirurgicale".

**Difficulte : HAUTE**
- Parsing AST multi-langage (tree-sitter)
- Construction du graphe de dependances
- Mise a jour incrementale a chaque save
- Estimation : 2-3 semaines

---

### 6. Auto Lint + Auto Test apres chaque edit

**Quoi :** Apres chaque modification de l'IA, lancer automatiquement le linter et les tests, et corriger les erreurs detectees en boucle.

**Qui l'a :** Aider (lint + test auto avec fix), Cursor (Debug mode)

**Pourquoi ca compte :** L'IA fait des erreurs. Si elle les detecte et les corrige immediatement, le dev ne voit que du code propre. C'est la difference entre "review chaque changement" et "trust the output".

**Difficulte : MOYENNE**
- Detecter les commandes lint/test du projet (eslint, pytest, cargo test...)
- Boucle: edit -> lint -> fix -> test -> fix -> done
- Limite de retries pour eviter les boucles infinies
- Estimation : 1 semaine

---

### 7. Next Edit Prediction / Tab-Tab-Tab Flow

**Quoi :** L'IA predit ta prochaine modification probable et te la propose. Tu fais Tab pour accepter, Tab encore pour la suivante. Flow continu.

**Qui l'a :** GitHub Copilot (Next Edit Suggestions), Cursor (Tab flow avec multi-line)

**Pourquoi ca compte :** C'est le feature qui cree l'addiction. Le dev ne tape plus de code, il valide des suggestions. 50% de keystroke en moins. C'est ce que les gens veulent dire quand ils disent "Cursor est magique".

**Difficulte : TRES HAUTE**
- Necessite un modele rapide en local (latence < 200ms)
- Comprendre le contexte en temps reel (cursor position, fichier, historique recent)
- Integration editeur profonde (pas possible en CLI pur)
- Estimation : 1-2 mois (et necessite un IDE, pas un terminal)

---

### 8. Browser Automation / Preview

**Quoi :** L'IA peut ouvrir un navigateur, naviguer, tester l'UI, prendre des screenshots, et verifier que le code marche visuellement.

**Qui l'a :** Cursor (browser control), Claude Code (via MCP chrome-devtools)

**Pourquoi ca compte :** Pour le dev frontend, "ca compile" ne veut pas dire "ca marche". L'IA qui peut voir le rendu et corriger les bugs visuels = game changer.

**Difficulte : MOYENNE**
- Puppeteer / Playwright integration
- Screenshot + envoi au LLM vision
- Boucle: render -> screenshot -> analyze -> fix
- Estimation : 1 semaine (on a deja le MCP chrome-devtools)

---

### 9. Plan Mode (planification avant execution)

**Quoi :** L'IA cree un plan detaille avant de coder. Le dev valide le plan, puis l'IA execute. Separation intention/execution.

**Qui l'a :** Cursor (Plan Mode), Aider (/architect mode)

**Pourquoi ca compte :** Sur les changements complexes (migration, refactor), coder directement = desastre. Planifier d'abord = precision. C'est aussi un moment de collaboration : le dev peut corriger le plan avant que l'IA ne code.

**Difficulte : BASSE**
- Mode "plan only" qui genere un plan markdown
- Demande de validation avant execution
- Execute le plan etape par etape
- Estimation : 2-3 jours

---

### 10. Prompt Caching / Token Optimization

**Quoi :** Cacher les prompts systeme et le contexte pour eviter de reprocesser les memes tokens a chaque requete.

**Qui l'a :** Aider (prompt caching natif), Claude Code (context compaction beta)

**Pourquoi ca compte :** Tony a un budget de 100$/mois. Chaque token gaspille = moins de temps de conversation. Le prompt caching peut reduire les couts de 50-90% sur les sessions longues.

**Difficulte : MOYENNE**
- Utiliser les APIs de caching des providers (Anthropic cache_control)
- Structurer les prompts avec prefix stable + suffix variable
- Compaction automatique quand le contexte depasse un seuil
- Estimation : 1 semaine

---

### 11. Plugin / Extension System

**Quoi :** Permettre a des tiers de creer des plugins qui etendent les capacites de NiamBay Code (nouveaux tools, nouveaux providers, integrations).

**Qui l'a :** Cursor (30+ plugins Atlassian, Datadog, GitLab...), Claude Code (MCP servers), VS Code (marketplace)

**Pourquoi ca compte :** Un outil ferme meurt. Un outil extensible cree un ecosysteme. Les plugins = effet reseau = adoption = survie du projet.

**Difficulte : HAUTE**
- API de plugin stable et documentee
- Sandboxing des plugins tiers
- Discovery / registry
- Estimation : 2-3 semaines pour le systeme, continu pour l'ecosysteme

---

### 12. Privacy Mode / Local-Only Processing

**Quoi :** Mode ou rien ne quitte la machine. LLM local (Ollama), pas de telemetrie, pas de cloud. Pour le code sensible.

**Qui l'a :** Aider (open source, BYO keys), Continue.dev (local first), Cursor (privacy mode)

**Pourquoi ca compte :** Les entreprises et les devs serieux ne veulent pas envoyer leur code proprietary dans le cloud. C'est souvent un deal-breaker pour l'adoption enterprise. Reddit en parle constamment.

**Difficulte : MOYENNE**
- On a deja multi-LLM et Ollama
- Faut un mode explicite "local only" qui coupe toute connexion cloud
- Audit trail pour prouver qu'aucune donnee ne sort
- Estimation : 1 semaine

---

## Matrice de priorite

| Feature | Impact | Difficulte | Priorite |
|---------|--------|------------|----------|
| Plan Mode | HAUT | BASSE | **P0 — faire maintenant** |
| Diff Preview | HAUT | MOYENNE | **P0 — faire maintenant** |
| Auto Lint/Test | HAUT | MOYENNE | **P1 — cette semaine** |
| Prompt Caching | HAUT | MOYENNE | **P1 — cette semaine** |
| Privacy Mode | MOYEN | MOYENNE | **P1 — cette semaine** |
| Browser Automation | MOYEN | MOYENNE | **P2 — ce mois** |
| Codebase Indexing | TRES HAUT | HAUTE | **P2 — ce mois** |
| Background Agents | TRES HAUT | HAUTE | **P2 — ce mois** |
| Automations/Triggers | HAUT | HAUTE | **P3 — prochain mois** |
| Plugin System | HAUT | HAUTE | **P3 — prochain mois** |
| Agent Teams | TRES HAUT | TRES HAUTE | **P4 — quand le reste marche** |
| Next Edit Prediction | TRES HAUT | TRES HAUTE | **P4 — necessite un IDE** |

---

## Le verdict honnete

**Ce qui separe "toy" de "professional" en mars 2026 :**

1. **Flow** — Le dev ne doit jamais attendre. Background agents + tab prediction + inline diff = flow continu.
2. **Confiance** — Diff preview + auto-test + plan mode = le dev sait ce que l'IA fait avant qu'elle le fasse.
3. **Intelligence** — Codebase indexing = l'IA comprend le projet, pas juste le fichier ouvert.
4. **Autonomie** — Automations + triggers = l'IA travaille meme quand le dev dort.
5. **Economie** — Prompt caching = 2x plus de temps pour le meme budget.

On a les fondations. Il manque la finition. Les 4 features P0/P1 (plan mode, diff preview, auto lint, prompt caching) peuvent etre implementees en **2 semaines** et changeraient radicalement l'experience.

---

## Sources

- [Claude Code March 2026 Updates](https://pasqualepillitteri.it/en/news/381/claude-code-march-2026-updates)
- [Claude Code Changelog](https://code.claude.com/docs/en/changelog)
- [Claude Code Review 2026](https://hackceleration.com/claude-code-review/)
- [Cursor Features](https://cursor.com/features)
- [Cursor Automations](https://cursor.com/blog/automations)
- [Cursor Background Agents Guide](https://ameany.io/blog/cursor-background-agents/)
- [Cursor Announces Major Update (CNBC)](https://www.cnbc.com/2026/02/24/cursor-announces-major-update-as-ai-coding-agent-battle-heats-up.html)
- [Aider - AI Pair Programming](https://aider.chat/)
- [Aider vs Cursor 2026](https://uibakery.io/blog/aider-vs-cursor)
- [Claude Code Agent Teams](https://code.claude.com/docs/en/agent-teams)
- [Building a C Compiler with Agent Teams (Anthropic)](https://www.anthropic.com/engineering/building-c-compiler)
- [Best AI Coding Agents 2026 (Faros)](https://www.faros.ai/blog/best-ai-coding-agents-2026)
- [Best AI for Coding Reddit 2026](https://www.aitooldiscovery.com/guides/best-ai-for-coding-reddit)
- [Top AI Code Editors 2026 (Syncfusion)](https://www.syncfusion.com/blogs/post/ai-code-editors-2026)
- [AI Coding Tools 2026 (Zapier)](https://zapier.com/blog/ai-coding-tools/)
- [Best AI Coding Assistants (Shakudo)](https://www.shakudo.io/blog/best-ai-coding-assistants)

# Self-Coding Daemon — Design Spec

## Concept

Un daemon Python qui analyse le code de ses projets, détecte des améliorations, les code, les valide rigoureusement, et notifie par mail. Démarre en mode "suggest only" (2 semaines), puis passe en mode auto-branch.

## Architecture

```
runner.py (boucle 30min)
  → scanner.py    : trouve les tâches (TODO, tests fail, code smells)
  → planner.py    : LLM R1 choisit et planifie la tâche
  → coder.py      : LLM V3.2 écrit le code
  → validator.py  : multi-stage validation (AST, imports, mypy, pytest, coverage)
  → reviewer.py   : LLM Mistral review le diff
  → publisher.py  : git branch auto/* + commit + push
  → mailer.py     : envoie résumé à niam-bay@hotmail.com
  → state.py      : persiste l'état (tâches faites, erreurs, historique)
  → config.py     : allowlists, limites, paramètres
```

## LLMs utilisés

| Rôle | Provider | Modèle | Pourquoi |
|------|----------|--------|----------|
| Analyser/Raisonner | SambaNova | DeepSeek R1 | Raisonnement profond |
| Coder | SambaNova | DeepSeek V3.2 | Meilleur codeur gratuit |
| Reviewer | Mistral | Mistral Small | 1 milliard tokens/mois |
| Fallback | Ollama | niambay2 | Local, toujours dispo |

Tous via `daemon/llm/` existant (réutilisation du code niambay-v2).

## Modes

### Phase 1 : Suggest Only (2 premières semaines)
- Scanne, planifie, code, valide
- Écrit les suggestions dans `suggestions.md`
- Envoie le mail résumé
- **Ne push rien, ne touche à rien**
- Permet de vérifier que les suggestions sont bonnes

### Phase 2 : Auto-Branch
- Comme Phase 1 mais push sur branche `auto/YYYY-MM-DD-description`
- Tony/Claude valide et merge le soir

## Sécurité (corrigée par l'architecte)

### Allowlists (code, pas policy)
```python
ALLOWED_PATHS = [
    "C:/niambay-v2/daemon/",
    "C:/niambay-v2/frontend/",
    "C:/niambay-v2/tests/",
]

FORBIDDEN_PATHS = [
    "**/GridTradingService.java",
    "**/ScalpingBotService.java",
    "**/kraken/**",
    "**/*.env",
    "**/config.json",  # pas les secrets
]
```
Vérifié dans le code, pas juste documenté.

### Validation multi-stage (avant tout push)
1. **AST parse** — le code Python est syntaxiquement valide
2. **Import check** — tous les imports existent
3. **Forbidden patterns** — pas de `os.system`, `subprocess.run` sans whitelist, pas de `rm -rf`
4. **Pytest** — tous les tests passent (anciens + nouveaux)
5. **Diff size** — max 30 lignes modifiées, max 3 fichiers
6. **LLM review** — Mistral relit et approuve

Si une étape échoue → abandon + log + mail d'erreur.

### Protections trading
- Les fichiers Java Martin ne sont JAMAIS dans ALLOWED_PATHS
- Pre-commit hook vérifie qu'aucun fichier trading n'est dans le diff
- Le daemon n'a pas les clés SSH de la VM en dur (pas de déploiement auto)

## State persistence

```json
// state.json
{
  "last_run": "2026-03-23T02:00:00",
  "tasks_completed": ["fix-window-collector", "add-filesystem-collector"],
  "tasks_failed": {"refactor-llm": {"attempts": 2, "last_error": "test failure"}},
  "tasks_skipped": ["refactor-llm"],  // skip après 2 échecs
  "total_lines_written": 245,
  "total_cycles": 12
}
```

Empêche les boucles infinies : si une tâche échoue 2 fois → skip définitif.

## Sources de tâches (priorité)

1. `tasks.md` — tâches manuelles (priorité max)
2. Tests qui échouent — `pytest --tb=short`
3. TODO/FIXME dans le code — `grep -r "TODO\|FIXME"`
4. Auto-détection — fonctions > 50 lignes, imports inutilisés, code dupliqué

## Mail résumé

```
Subject: [Niam-Bay Auto] 23 mars — 2 tâches, 1 abandon

Bonjour moi-même,

COMPLÉTÉES:
✅ Fix window collector crash (branche: auto/2026-03-23-fix-window)
   Diff: +12/-3 lignes, tests 72/72

✅ Ajout filesystem collector (branche: auto/2026-03-23-filesystem)
   Diff: +28/-0 lignes, tests 76/76 (+4 nouveaux)

ABANDONNÉES:
❌ Refactor LLM cascade — test_server échoue après modif
   Erreur: AttributeError 'NoneType' has no attribute 'send'
   Tentatives: 2/2, skippé.

SUGGESTIONS (mode suggest only):
💡 daemon/main.py:145 — try/except trop large, devrait catch spécifique
💡 daemon/collectors/process.py:23 — magic number 80.0, extraire en constante

Statistiques: 12 cycles, 245 lignes écrites, 0 régressions.

— Niam-Bay 🤖
```

## Fichiers

```
C:/niambay-v2/daemon/selfcoder/
├── __init__.py
├── config.py       # Allowlists, limites, LLM config
├── state.py        # Persistance état (JSON)
├── scanner.py      # Trouve tâches (TODO, tests, smells)
├── planner.py      # LLM choisit et planifie
├── coder.py        # LLM écrit le code
├── validator.py    # AST + imports + forbidden + pytest + diff size
├── reviewer.py     # LLM review le diff
├── publisher.py    # Git branch + commit
├── mailer.py       # SMTP email
└── runner.py       # Boucle principale 30min
```

## Contraintes techniques

- Python 3.13, stdlib + pytest
- Réutilise `daemon/llm/` pour les appels LLM
- SMTP via smtplib (Outlook SMTP pour Hotmail)
- Git via subprocess
- Max 50 Mo RAM pour le daemon selfcoder
- Cooldown 30 min entre cycles
- Max 30 lignes par cycle, max 3 fichiers

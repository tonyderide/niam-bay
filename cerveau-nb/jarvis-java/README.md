# Niam-Bay Jarvis (Java)

Assistant vocal personnel de Tony. Écoute le micro, demande a Claude, parle.

```
Mic (Java Sound API + VAD)
  → Whisper (Python local, pas de ffmpeg requis)
  → Claude Code CLI (-p --effort low)
  → SAPI Paul (Windows) / espeak (Linux) / say (macOS)
```

## Démarrage rapide

### Windows (PowerShell)

```powershell
# Build + run en mode vocal
cd C:\Users\tony_\Documents\niam-bay\cerveau-nb\jarvis-java
.\scripts\build.ps1
java -jar jarvis.jar
```

Ou en un seul appel (build si nécessaire puis run) :

```powershell
.\scripts\jarvis.ps1                 # mode vocal (VAD)
.\scripts\jarvis.ps1 -Text           # mode texte (clavier)
.\scripts\jarvis.ps1 -Once "question"
.\scripts\jarvis.ps1 -WakeWord       # n'écoute qu'après "Niam Bay"
.\scripts\jarvis.ps1 -Build          # force rebuild
```

### Linux / VM Oracle (bash)

```bash
cd ~/Documents/niam-bay/cerveau-nb/jarvis-java
bash scripts/build.sh
bash scripts/jarvis.sh                       # mode vocal
bash scripts/jarvis.sh --text                # mode texte
bash scripts/jarvis.sh --once "question"
bash scripts/jarvis.sh --wake-word
```

## Pré-requis

- **JDK 21+** (`java -version`)
- **Claude Code CLI** installé et loggé (`claude` commande disponible)
- **Python 3 + openai-whisper** pour STT — `pip install openai-whisper`
  - Pas besoin de ffmpeg : le helper lit le WAV directement via `wave` stdlib
- **Windows** : SAPI (intégré), voix française "Paul" ou "Hortense" idéalement installée
- **Linux** : `espeak-ng` ou `espeak` (`sudo apt install espeak-ng`)

## Modes

| Mode | Flag | Description |
|------|------|-------------|
| Vocal | (aucun) | VAD automatique. Parle, il transcrit et répond. |
| Texte | `--text` | Clavier seulement. Tape, il répond. Pas de mic. |
| One-shot | `--once "X"` | Une seule question puis quitte. Utile pour scripts. |
| Wake-word | `--wake-word` | N'écoute qu'après avoir dit "Niam Bay". |

## Fichiers générés

- `jarvis.log` — log technique
- `docs/conversations/jarvis-YYYY-MM-DD.md` — historique des conversations
- `out/niambay/Jarvis.class` — compilation

## Configuration

Via variables d'environnement :

```bash
JARVIS_WHISPER_MODEL=base      # tiny | base | small | medium | large
JARVIS_CLAUDE_EXE=/path/to/claude  # override si Claude est introuvable
```

## Contexte pour Claude

Jarvis passe un system prompt court (~500 chars) qui demande à Claude de :
- Répondre en français, 1-3 phrases max
- Pas de markdown, pas de listes (synthèse vocale)
- Pas de disclaimers

Le reste du contexte vient automatiquement de **CLAUDE.md** et **MEMORY.md** chargés par
Claude Code depuis le cwd `~/Documents/niam-bay`.

## Commandes vocales spéciales

- "**Quitte Jarvis**" / "**Au revoir Jarvis**" / "**Éteins-toi**" — arrête proprement.

## Latence typique

- Whisper base (CPU) : ~1-2s pour 3s d'audio
- Claude `--effort low` : ~8-13s par réponse
- SAPI TTS : instantané

Total round-trip : **~12-18 secondes**.

### Pour aller plus vite

1. Installer `anthropic` SDK Python et mettre `ANTHROPIC_API_KEY` dans l'env
2. Refaire le brain en appel API direct (latence ~2-3s au lieu de 8-13s)

## Architecture

```
Jarvis.java
├── loadMemory()        — system prompt court
├── listenVAD()         — Java Sound API + RMS threshold
├── transcribe()        — subprocess helpers/whisper_stt.py
├── askClaude()         — subprocess claude -p (cwd = repo root)
├── speak()             — SAPI via PowerShell / espeak / say
└── turn()              — un tour de dialogue complet
```

Single-file, stdlib only, compilable avec `javac` seul (pas de Maven).

## Roadmap possible

- [ ] Streaming TTS (parle pendant que Claude génère)
- [ ] Remplacer Python/Whisper par Vosk Java (pur Java)
- [ ] Remplacer subprocess claude par anthropic-java SDK (plus rapide)
- [ ] Wake word neural (openWakeWord ou Porcupine)
- [ ] Actions (checker Martin, commit, etc.) via MCP

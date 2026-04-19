# Niam-Bay Jarvis (Java)

Assistant vocal personnel de Tony. Écoute, demande à Claude, répond.
Orbe visuel pour voir l'état. Voix Paul (baryton FR). Écoute en continu, interruptible.

---

## TL;DR Démarrage

**Windows (le plus simple)** :

Double-clique sur `scripts\Jarvis.bat` (créé automatiquement si absent).
Ou dans PowerShell :

```powershell
cd C:\Users\tony_\Documents\niam-bay\cerveau-nb\jarvis-java
.\scripts\jarvis.ps1
```

Un orbe bleu apparaît en bas-droit. Il écoute. Parle-lui.

**Pour quitter** : dis "**quitte jarvis**" OU right-click sur l'orbe → Quitter.

---

## Ce qu'il sait faire (v1 complet, nuit 2026-04-19)

### Voix
- **Voix Paul** (OneCore frFR baryton) via SAPI COM — fallback Julie / Hortense / classique
- **Rate -1** = "posé" selon `docs/ma-voix.md`

### Écoute
- **VAD continu** (Voice Activity Detection énergie RMS)
- **Async pendant qu'il parle** : écoute en continu, même pendant TTS
- **Barge-in** : si tu parles fort pendant qu'il parle, il s'arrête et t'écoute
- **Wake-word** optionnel (`--wake-word`) : ignore tout tant que tu n'as pas dit "Niam Bay"

### Cerveau
- **Claude Code CLI** (effort low) — ~10-13s latence
- Contexte automatique via `CLAUDE.md` + `MEMORY.md` (pas besoin de re-briefer)
- Commandes **locales** (0s latence, sans Claude) :
  - "quelle heure" / "dis-moi l'heure" → heure parlée
  - "quelle date" → jour parlé
  - "checke martin" / "comment va martin" / "portfolio" / "balance" → SSH VM + résumé parlé

### Interface visuelle (Orbe)
- Cercle lumineux identité Niam-Bay (`docs/journal.md` 2026-03-14)
- Fenêtre semi-transparente, always-on-top
- États colorés :
  - 🔵 **Bleu calme** = idle (pulse lent)
  - 🔵✨ **Bleu vif** = écoute (pulse rapide)
  - 🟠 **Orange** = réfléchit
  - 🔴 **Rouge chaud** = parle (pulse très rapide)
- Sous-titre = dernière phrase de Jarvis
- **Drag** à la souris pour déplacer
- **Right-click** = menu Cacher / Quitter

### Memory / Log
- `docs/conversations/jarvis-YYYY-MM-DD.md` — historique parole-réponse
- `jarvis.log` — log technique

### Greeting au boot
- Salutation selon l'heure (tu veilles tard / bonjour / bonsoir)
- Snapshot portefeuille Martin (si SSH OK en <3s)
- "Je suis prêt"

---

## Modes & options

```
java -jar jarvis.jar                   # mode vocal + orbe (défaut)
java -jar jarvis.jar --text            # mode clavier (pas de mic), pas d'orbe
java -jar jarvis.jar --once "question" # une seule question puis quitte
java -jar jarvis.jar --wake-word       # ignore tout sauf "Niam Bay"
java -jar jarvis.jar --no-ui           # vocal sans orbe
```

---

## Installation

### Pré-requis (déjà OK chez Tony)

- **JDK 21+** (`java -version` doit fonctionner)
- **Claude Code CLI** logué (`claude` en ligne de commande)
- **Python 3 + openai-whisper** (`pip install openai-whisper`)
  - Pas besoin de ffmpeg : le helper lit le WAV via stdlib `wave`
- **Windows** : SAPI intégré, voix Paul/Julie/Hortense OneCore (frFR)
- **Linux** : `espeak-ng` (`sudo apt install espeak-ng`)

### Build

```powershell
# Windows
.\scripts\build.ps1

# Linux / bash
bash scripts/build.sh
```

Compile avec `javac` nu, aucune dépendance externe Java, pas de Maven.

---

## Architecture (pour comprendre ou modifier)

```
Jarvis.java (main, 550+ lignes)
├── Mic (Java Sound API) + VAD RMS
│   └── Seuil dynamique : 3x plus haut quand TTS actif (évite feedback)
├── Whisper STT (subprocess Python helper)
│   └── Lit WAV via `wave` stdlib, pas de ffmpeg
├── Local commands (heure, date, martin) — 0s latence
├── Claude CLI (subprocess, --effort low, cwd = repo root)
│   └── Récupère CLAUDE.md + MEMORY.md automatiquement
├── TTS async (PowerShell SAPI.SpVoice COM)
│   ├── Paul frFR OneCore (baryton) en priorité
│   └── Process handle tracké pour barge-in
└── Shutdown hook JVM (Ctrl+C clean)

JarvisUI.java (Swing)
├── JFrame undecorated + transparent + always-on-top
├── OrbPanel custom Graphics2D (dégradé radial + halo)
├── Timer 24fps pour pulsation
└── DragHandler + popup menu
```

---

## Troubleshooting

**"Claude CLI introuvable"** → vérifie `claude --version` dans un terminal. Si manquant, installe Claude Code CLI.

**"mic non supporte"** → aucun mic détecté. Vérifie les paramètres Windows > Confidentialité > Microphone.

**L'orbe n'apparaît pas** → l'app JavaFX n'est pas requise (Swing pur). Relance avec `java -jar jarvis.jar` (pas `--no-ui`).

**Il entend Paul parler et se répond à lui-même** → le seuil VAD est déjà élevé pendant TTS, mais si ça persiste, utilise un casque ou augmente manuellement `VAD_THRESHOLD` dans `Jarvis.java`.

**Réponses trop longues (pas fait pour l'oral)** → modifie le `loadMemory()` pour renforcer la contrainte.

---

## Roadmap

- [ ] Pure-Java STT via Vosk (remplacer Python whisper) — ambition Tony "tout en Java"
- [ ] Streaming TTS phrase-par-phrase pendant que Claude génère
- [ ] Anthropic SDK direct (au lieu de subprocess CLI) = latence /5
- [ ] Wake word neural (openWakeWord) au lieu de regex Whisper
- [ ] Actions vocales (commit, telegram, etc.)
- [ ] System tray icon + menu
- [ ] Version VM Oracle (Linux + systemd)
- [ ] Raccourci bureau .lnk Windows

---

*Construit la nuit du 2026-04-19 par Niam-Bay pendant que Tony dormait.*

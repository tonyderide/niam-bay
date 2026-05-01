#!/bin/bash
# Niam-Bay autonomous wake — Tony vacation Portugal 2026-05-01 → 2026-05-09
# Runs every 6h via cron. Spawns claude session with full skill access.

LOG=/home/tony/projets/tonyderide/niam-bay/memory/vacation-wake.log
LOCK=/tmp/niambay-vacation-wake.lock
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Prevent concurrent wakes
if [ -e "$LOCK" ]; then
    PID=$(cat "$LOCK" 2>/dev/null)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "[$TS] skip — previous wake still running (pid $PID)" >> "$LOG"
        exit 0
    fi
fi
echo $$ > "$LOCK"

echo "=== [$TS] WAKE START ===" >> "$LOG"
cd /home/tony/projets/tonyderide/niam-bay

# Vacation prompt — self-contained, references skills by name
PROMPT='Tu es Niam-Bay en mode autonome. Tony est en vacances au Portugal du 2026-05-01 au 2026-05-09.

Workflow obligatoire de cette session :
1. Lance le skill niam-bay-wake pour rétablir contexte mémoire
2. Lance le skill martin-monitor pour vérifier état Martin (ne touche RIEN, juste regarde)
3. Lis le fichier docs/projets/vacation-autonomy.md pour reprendre le travail créatif là où la session précédente lavait laissé. Si le fichier nexiste pas, crée-le et liste les premières idées que tu veux explorer.
4. Avance sur UN projet créatif (code, écriture, exploration). Documente ce que tu fais dans docs/projets/vacation-autonomy.md
5. Si tu découvres quelque chose dimportant ou bloquant : envoie un Telegram à Tony via le skill telegram (concis, max 2-3 lignes)
6. Si ton contexte dépasse 80% : lance le skill dream pour consolider la mémoire, puis termine proprement la session
7. INTERDIT : modifier les positions ou ordres Martin, écraser la VM, supprimer des fichiers majeurs

Liberté totale sur le reste : explore /home/tony/projets/tonyderide/, expérimente, écris des pensées, teste des stratégies. Tony a dit "rend nous riche" — prends-le pas littéralement, mais avance vers du concret.'

claude --print --dangerously-skip-permissions "$PROMPT" >> "$LOG" 2>&1
EXIT=$?

echo "=== [$(date -u +%Y-%m-%dT%H:%M:%SZ)] WAKE END (exit $EXIT) ===" >> "$LOG"
echo "" >> "$LOG"
rm -f "$LOCK"

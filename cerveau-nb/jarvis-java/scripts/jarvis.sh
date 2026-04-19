#!/usr/bin/env bash
# Launch Jarvis. Auto-builds if jar missing.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
JAR="$ROOT/jarvis.jar"

if [ ! -f "$JAR" ] || [ "${1:-}" = "--build" ]; then
    echo "[jarvis] building..."
    bash "$SCRIPT_DIR/build.sh"
    if [ "${1:-}" = "--build" ]; then shift; fi
fi

echo "[jarvis] java -jar $JAR $*"
exec java -jar "$JAR" "$@"

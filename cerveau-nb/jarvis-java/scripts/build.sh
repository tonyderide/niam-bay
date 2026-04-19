#!/usr/bin/env bash
# Build Jarvis (no Maven needed, just javac)
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT="$ROOT/out"

echo "[build] javac..."
mkdir -p "$OUT"
javac -d "$OUT" "$ROOT/src/main/java/niambay/Jarvis.java"

echo "[build] packaging jar..."
# Manifest
MANIFEST="$OUT/MANIFEST.MF"
cat > "$MANIFEST" <<EOF
Manifest-Version: 1.0
Main-Class: niambay.Jarvis

EOF
jar cfm "$ROOT/jarvis.jar" "$MANIFEST" -C "$OUT" niambay

echo "[build] OK -> $ROOT/jarvis.jar"
echo "Usage: java -jar $ROOT/jarvis.jar [--text|--once 'question'|--wake-word]"

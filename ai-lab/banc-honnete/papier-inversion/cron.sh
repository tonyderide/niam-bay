#!/bin/bash
# PREREG-35 : journal papier quotidien (prix publics Binance, aucun ordre). Commit local du journal et des données seulement.
cd "$(dirname "$0")" || exit 1
R=$(git rev-parse --show-toplevel)
nice -n 10 /usr/bin/python3 papier.py || exit 1
P=(); for x in ai-lab/banc-honnete/papier-inversion/journal.md ai-lab/banc-honnete/papier-inversion/etat.json ai-lab/banc-honnete/papier-inversion/donnees; do { [ -f "$R/$x" ] || [ -n "$(ls -A "$R/$x" 2>/dev/null)" ]; } && P+=("$x"); done
[ ${#P[@]} -eq 0 ] && exit 0
[ -e etat.json ] || exit 0   # rien à journaliser avant le premier jour (ou la première semaine) jugé
git -C "$R" add -- "${P[@]}"
git -C "$R" diff --cached --quiet -- "${P[@]}" && exit 0
J=$(python3 -c "import json;print(json.load(open('etat.json'))['dernier_jour'])")
git -C "$R" commit -q -m "PREREG-35 journal papier : $J" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- "${P[@]}"

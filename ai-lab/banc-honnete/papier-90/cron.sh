#!/bin/bash
# PREREG-65 : journal papier quotidien (prix publics Binance, aucun ordre). Commit local du journal seulement ; etat.json (gros, change chaque jour) reste hors git, copié chaque heure par la sauvegarde.
cd "$(dirname "$0")" || exit 1
R=$(git rev-parse --show-toplevel)
nice -n 10 /usr/bin/python3 papier90.py || exit 1
[ -e resume.json ] || exit 0
P=(); for x in journal.md resume.json trades.csv; do [ -f "$x" ] && P+=("ai-lab/banc-honnete/papier-90/$x"); done
git -C "$R" add -- "${P[@]}"
git -C "$R" diff --cached --quiet -- "${P[@]}" && exit 0
J=$(python3 -c "import json;print(json.load(open('resume.json'))['dernier_jour'])")
git -C "$R" commit -q -m "PREREG-65 journal papier : $J" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- "${P[@]}"

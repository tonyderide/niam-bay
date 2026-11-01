#!/bin/bash
# PREREG-47 : journal papier quotidien (nouvelles cotations) (prix publics Binance, aucun ordre). Commit local du journal et des données seulement.
cd "$(dirname "$0")" || exit 1
R=$(git rev-parse --show-toplevel)
nice -n 10 /usr/bin/python3 cotations.py || exit 1
git -C "$R" add -- ai-lab/banc-honnete/papier-cotations/journal.md ai-lab/banc-honnete/papier-cotations/etat.json ai-lab/banc-honnete/papier-cotations/registre.json ai-lab/banc-honnete/papier-cotations/donnees 2>/dev/null
git -C "$R" diff --cached --quiet -- ai-lab/banc-honnete/papier-cotations && exit 0
J=$(python3 -c "import json;print(json.load(open('etat.json'))['maj_utc'])")
git -C "$R" commit -q -m "PREREG-47 journal papier : $J" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- ai-lab/banc-honnete/papier-cotations/journal.md ai-lab/banc-honnete/papier-cotations/etat.json ai-lab/banc-honnete/papier-cotations/registre.json ai-lab/banc-honnete/papier-cotations/donnees

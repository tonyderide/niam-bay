#!/bin/bash
# PREREG-45 : journal papier quotidien (réversion) (prix publics Binance, aucun ordre). Commit local du journal et des données seulement.
cd "$(dirname "$0")" || exit 1
R=$(git rev-parse --show-toplevel)
nice -n 10 /usr/bin/python3 reversion.py || exit 1
git -C "$R" add -- ai-lab/banc-honnete/papier-reversion/journal.md ai-lab/banc-honnete/papier-reversion/etat.json ai-lab/banc-honnete/papier-reversion/donnees 2>/dev/null
git -C "$R" diff --cached --quiet -- ai-lab/banc-honnete/papier-reversion && exit 0
J=$(python3 -c "import json;print(json.load(open('etat.json'))['dernier_jour'])")
git -C "$R" commit -q -m "PREREG-45 journal papier : $J" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- ai-lab/banc-honnete/papier-reversion/journal.md ai-lab/banc-honnete/papier-reversion/etat.json ai-lab/banc-honnete/papier-reversion/donnees

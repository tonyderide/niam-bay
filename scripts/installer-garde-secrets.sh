#!/bin/bash
# Installe le garde-fou anti-secrets comme hook pre-commit de ce dépôt (à refaire sur chaque clone).
cd "$(git rev-parse --show-toplevel)" || exit 1
printf '#!/bin/sh\nexec python3 "$(git rev-parse --show-toplevel)/scripts/garde-secrets.py"\n' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit scripts/garde-secrets.py
echo "garde-fou installé : .git/hooks/pre-commit"

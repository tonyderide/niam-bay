#!/usr/bin/env python3
"""Garde-fou avant commit : refuse un commit qui ajoute un secret au dépôt public.
Installé comme .git/hooks/pre-commit (voir scripts/installer-garde-secrets.sh).
Ne montre jamais la valeur trouvée. Contournement volontaire : git commit --no-verify."""
import re, subprocess, sys

MOTIFS = {
    "clé Anthropic": rb"sk-ant-[A-Za-z0-9_-]{20,}",
    "clé OpenAI": rb"\bsk-(?:proj-)?[A-Za-z0-9]{40,}\b",
    "jeton GitHub": rb"\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{36}\b|github_pat_[A-Za-z0-9_]{40,}",
    "jeton de bot Telegram": rb"\b[0-9]{8,10}:AA[A-Za-z0-9_-]{33}\b",
    "clé AWS": rb"\bAKIA[0-9A-Z]{16}\b",
    "jeton Slack": rb"xox[baprs]-[A-Za-z0-9-]{20,}",
    "clé privée": rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    # clé ou mot de passe écrit en clair dans une affectation (Mistral, SambaNova, mail… : formats sans préfixe)
    "clé ou mot de passe en clair": rb"(?i)\b[A-Z_]*(?:API_KEY|_KEY|SECRET|PASSWORD|PASSWD|_PASS|TOKEN)\b\s*[=:]\s*['\"]?"
                                    rb"(?![$<{]|os\.|process\.|getenv|environ|your|xxx|change|example|none|null)[A-Za-z0-9_\-+/=]{20,}",
}
FICHIERS_INTERDITS = re.compile(r"(^|/)(\.env(\..*)?|.*\.sqlite3?|.*\.db|.*_token|\.tg_token|id_(rsa|ed25519))$")


def sh(*args):
    return subprocess.run(args, capture_output=True).stdout


fichiers = [f for f in sh("git", "diff", "--cached", "--name-only", "--diff-filter=AM").decode().splitlines() if f]
problemes = []
for f in fichiers:
    if FICHIERS_INTERDITS.search(f):
        problemes.append(f"{f} : type de fichier qui ne doit pas être publié")
        continue
    contenu = sh("git", "show", f":{f}")          # version indexée, texte ou binaire
    for nom, rx in MOTIFS.items():
        if re.search(rx, contenu):
            problemes.append(f"{f} : {nom}")

if problemes:
    print("\n⛔ Commit refusé : ce dépôt est PUBLIC et ceci ressemble à un secret :", file=sys.stderr)
    for p in problemes:
        print("   - " + p, file=sys.stderr)
    print("Retire-le (git restore --staged <fichier>) ; si c'est une fausse alerte certaine : git commit --no-verify\n", file=sys.stderr)
    sys.exit(1)

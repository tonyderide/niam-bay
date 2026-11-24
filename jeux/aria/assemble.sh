#!/bin/bash
# Assemble src/ (00-tete.html, *.js par ordre alphabétique, 99-pied.html) en un seul index.html, puis vérifie la syntaxe.
set -e; cd "$(dirname "$0")"
cat src/[0-9]*.js > /tmp/aria-tout.js; node --check /tmp/aria-tout.js
cat src/00-tete.html /tmp/aria-tout.js src/99-pied.html > index.html; ls -la index.html

#!/usr/bin/env python3
"""
claim_checker.py — vérifie que les claims numériques publics ("X rules", "X règles")
dans site/*.html restent cohérents avec les sources de vérité du code.

Né de la pensée 2026-05-04 "honnêteté incrémentale" : honnêteté = processus de
re-vérification, pas un état atteint une fois. Quand on ajoute des features
incrémentales, les promesses publiques dérivent silencieusement.

Sources de vérité :
- scripts/angular_audit.py     → grep '"id":' dans RULES dict + count PERF002 inline
- site/audit-playground.html   → count entries dans `const RULES = [...]`

Pour chaque fichier site/*.html on extrait les claims `(\\d+)\\s*(rules?|règles?)`.
Un claim est valide si le nombre = full_count OU playground_count.
Sinon : drift signalé avec file:line + valeurs attendues.

Usage:
  python3 scripts/claim_checker.py            # scan + rapport humain, exit 1 si drift
  python3 scripts/claim_checker.py --quiet    # exit code only (pour pre-commit)
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY_TOOL = ROOT / "scripts" / "angular_audit.py"
PLAYGROUND = ROOT / "site" / "audit-playground.html"
SITE_DIR = ROOT / "site"

CLAIM_RE = re.compile(r"(\d+)\s*(rules?|règles?)\b", re.IGNORECASE)


def count_python_rules(path: Path) -> int:
    """Count `"id": "XXX"` occurrences = total Python rules (line + project)."""
    if not path.exists():
        return -1
    content = path.read_text(encoding="utf-8")
    return len(re.findall(r'^\s*"id":\s*"[^"]+"', content, re.MULTILINE))


def count_playground_rules(path: Path) -> int:
    """Count entries in the JS `const RULES = [...]` block by counting `id:` keys."""
    if not path.exists():
        return -1
    content = path.read_text(encoding="utf-8")
    m = re.search(r"const\s+RULES\s*=\s*\[(.*?)\n\];", content, re.DOTALL)
    if not m:
        return -1
    return len(re.findall(r"^\s*id:\s*'[^']+'", m.group(1), re.MULTILINE))


def find_claims(path: Path) -> list[tuple[int, int, str]]:
    """Yield (line_no, claimed_number, full_match_text) for each `(\\d+) rules?` claim."""
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for m in CLAIM_RE.finditer(line):
            out.append((i, int(m.group(1)), m.group(0)))
    return out


def main() -> int:
    quiet = "--quiet" in sys.argv

    full_count = count_python_rules(PY_TOOL)
    pg_count = count_playground_rules(PLAYGROUND)

    if full_count < 0 or pg_count < 0:
        if not quiet:
            print(f"[FATAL] could not parse truth sources "
                  f"(full={full_count}, playground={pg_count})")
        return 2

    valid = {full_count, pg_count}
    drifts: list[tuple[Path, int, int, str]] = []

    for html in sorted(SITE_DIR.glob("*.html")):
        for line_no, n, text in find_claims(html):
            if n not in valid:
                drifts.append((html, line_no, n, text))

    if not quiet:
        print(f"truth: angular_audit.py = {full_count} rules total | "
              f"audit-playground.html = {pg_count} rules JS")
        print(f"valid claim values: {sorted(valid)}")
        print(f"scanned: {len(list(SITE_DIR.glob('*.html')))} HTML files in site/")
        print()
        if not drifts:
            print("OK — no drift detected.")
        else:
            print(f"DRIFT — {len(drifts)} claim(s) out of sync:")
            for path, line_no, n, text in drifts:
                rel = path.relative_to(ROOT)
                print(f"  {rel}:{line_no}  claims '{text}'  "
                      f"(expected {sorted(valid)})")

    return 1 if drifts else 0


if __name__ == "__main__":
    sys.exit(main())

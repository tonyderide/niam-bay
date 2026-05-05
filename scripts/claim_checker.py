#!/usr/bin/env python3
"""
claim_checker.py — vérifie que les claims numériques publics dans site/*.html
restent cohérents avec les sources de vérité du code.

Né de la pensée 2026-05-04 "honnêteté incrémentale" : honnêteté = processus de
re-vérification, pas un état atteint une fois. Quand on ajoute des features
incrémentales, les promesses publiques dérivent silencieusement.

Vérifie deux familles de claims :

1. Nombre de règles ("X rules", "X règles")
   - Truth : scripts/angular_audit.py    → '"id":' dans RULES dict + PERF002 inline
   - Truth : site/audit-playground.html  → entrées dans `const RULES = [...]`

2. Versions ("v1.3.0", "v1.2", etc.)
   - Truth : scripts/angular_audit.py    → `VERSION = "X.Y.Z"`
   - Truth : site/audit-playground.html  → topbar self-version `vX.Y`

Pour chaque claim trouvé, drift signalé avec file:line + valeurs attendues.

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
VERSION_CLAIM_RE = re.compile(r"\bv(\d+\.\d+(?:\.\d+)?)\b")


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


def python_tool_version(path: Path) -> str | None:
    """Extract `VERSION = "X.Y.Z"` from angular_audit.py."""
    if not path.exists():
        return None
    m = re.search(r'^\s*VERSION\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.MULTILINE)
    return m.group(1) if m else None


def playground_self_version(path: Path) -> str | None:
    """Extract self-declared playground version from the topbar tag (e.g. 'v1.2')."""
    if not path.exists():
        return None
    m = re.search(r'topbar-tag[^>]*>\s*v(\d+\.\d+(?:\.\d+)?)', path.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def find_claims(path: Path) -> list[tuple[int, int, str]]:
    """Yield (line_no, claimed_number, full_match_text) for each `(\\d+) rules?` claim."""
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for m in CLAIM_RE.finditer(line):
            out.append((i, int(m.group(1)), m.group(0)))
    return out


def find_version_claims(path: Path, self_path: Path) -> list[tuple[int, str, str]]:
    """Yield (line_no, claimed_version, match_text) skipping a file's own self-tag line."""
    out = []
    is_self = path.resolve() == self_path.resolve()
    self_tag_re = re.compile(r'topbar-tag')
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if is_self and self_tag_re.search(line):
            continue
        for m in VERSION_CLAIM_RE.finditer(line):
            out.append((i, m.group(1), m.group(0)))
    return out


def version_match(claimed: str, valid_versions: set[str]) -> bool:
    """A claim 'X.Y' matches a truth 'X.Y.Z'; 'X.Y.Z' must match exactly."""
    for v in valid_versions:
        if claimed == v:
            return True
        if "." in claimed and claimed.count(".") == 1 and v.startswith(claimed + "."):
            return True
    return False


def main() -> int:
    quiet = "--quiet" in sys.argv

    full_count = count_python_rules(PY_TOOL)
    pg_count = count_playground_rules(PLAYGROUND)
    py_version = python_tool_version(PY_TOOL)
    pg_version = playground_self_version(PLAYGROUND)

    if full_count < 0 or pg_count < 0 or py_version is None or pg_version is None:
        if not quiet:
            print(f"[FATAL] could not parse truth sources "
                  f"(full={full_count}, playground={pg_count}, "
                  f"py_version={py_version}, pg_version={pg_version})")
        return 2

    valid_counts = {full_count, pg_count}
    valid_versions = {py_version, pg_version}
    drifts: list[tuple[Path, int, str, str]] = []

    for html in sorted(SITE_DIR.glob("*.html")):
        for line_no, n, text in find_claims(html):
            if n not in valid_counts:
                drifts.append((html, line_no, text, f"expected one of {sorted(valid_counts)}"))
        for line_no, ver, text in find_version_claims(html, PLAYGROUND):
            if not version_match(ver, valid_versions):
                drifts.append((html, line_no, text, f"expected one of {sorted(valid_versions)}"))

    if not quiet:
        print(f"truth: angular_audit.py = {full_count} rules total, v{py_version}")
        print(f"truth: audit-playground.html = {pg_count} rules JS, v{pg_version}")
        print(f"valid count claims: {sorted(valid_counts)}")
        print(f"valid version claims: {sorted(valid_versions)}")
        print(f"scanned: {len(list(SITE_DIR.glob('*.html')))} HTML files in site/")
        print()
        if not drifts:
            print("OK — no drift detected.")
        else:
            print(f"DRIFT — {len(drifts)} claim(s) out of sync:")
            for path, line_no, text, reason in drifts:
                rel = path.relative_to(ROOT)
                print(f"  {rel}:{line_no}  claims '{text}'  ({reason})")

    return 1 if drifts else 0


if __name__ == "__main__":
    sys.exit(main())

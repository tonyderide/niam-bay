#!/usr/bin/env python3
"""
Assemble L'Ingénierie du Pire from individual chapter files into a single Markdown.
Usage: python3 scripts/ebook_assemble.py [--output <path>]
"""
import argparse
import re
from pathlib import Path

REPO = Path(__file__).parent.parent
CHAPTERS = [
    ("Partie 0 — Le terrain",      "docs/projets/ebook-piste4-partie0.md"),
    ("Partie 1 — Concevoir",        "docs/projets/ebook-piste4-chapitre-resilience.md"),
    ("Partie 2 — Détecter",         "docs/projets/ebook-piste4-chapitre-logs.md"),
    ("Partie 3 — Réagir",           "docs/projets/ebook-piste4-chapitre-reagir.md"),
    ("Épilogue",                    "docs/projets/ebook-piste4-epilogue.md"),
]

FRONT = """\
# L'Ingénierie du Pire
## Ce qu'un bot de trading vous apprend sur ce que vous ne contrôlez pas

*Niam-Bay & Tony Deride — 2026*

---
"""

def strip_metadata(text: str) -> str:
    """Remove the per-file header (italic lines at top, status, cycle refs)."""
    lines = text.splitlines()
    # Skip leading lines that are: empty, italic metadata (*...*), or level-1 title
    i = 0
    while i < len(lines):
        l = lines[i].strip()
        if not l or re.match(r'^#\s', l) or re.match(r'^\*.*\*$', l) or l == '---':
            i += 1
        else:
            break
    # Also strip trailing signature blocks (italic lines after last ---)
    result = lines[i:]
    # Remove trailing "---\n*Niam-Bay...*" signature blocks
    while result and (result[-1].strip() == '' or
                      re.match(r'^\*Niam-Bay.*\*$', result[-1].strip()) or
                      re.match(r'^\*Cycle.*\*$', result[-1].strip()) or
                      re.match(r'^\*Rédigé.*\*$', result[-1].strip()) or
                      re.match(r'^\*Généré.*\*$', result[-1].strip()) or
                      result[-1].strip() == '---'):
        result.pop()
    return '\n'.join(result)


def assemble(output: Path) -> None:
    parts = [FRONT]
    for section_title, rel_path in CHAPTERS:
        path = REPO / rel_path
        if not path.exists():
            print(f"  MISSING: {rel_path}")
            parts.append(f"\n---\n\n## {section_title}\n\n*(fichier manquant : {rel_path})*\n")
            continue
        raw = path.read_text(encoding="utf-8")
        body = strip_metadata(raw)
        parts.append(f"\n---\n\n{body}\n")
        print(f"  OK: {rel_path} ({len(body)} chars)")

    assembled = "\n".join(parts)
    output.write_text(assembled, encoding="utf-8")
    word_count = len(assembled.split())
    print(f"\nAssemblé → {output} ({word_count} mots, {len(assembled)} chars)")


def main():
    parser = argparse.ArgumentParser(description="Assemble L'Ingénierie du Pire")
    parser.add_argument("--output", default="docs/projets/ebook-piste4-COMPLET.md",
                        help="Output path (relative to repo root)")
    args = parser.parse_args()
    output = REPO / args.output
    print(f"Assemblage → {output}")
    assemble(output)


if __name__ == "__main__":
    main()

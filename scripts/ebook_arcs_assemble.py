#!/usr/bin/env python3
"""
Assemble narrative-arc ebook from fragment files.
Pattern: reusable for any closed arc or group of arcs.

Usage: python3 scripts/ebook_arcs_assemble.py
"""
import re
from pathlib import Path

REPO = Path(__file__).parent.parent
FRAGMENTS_DIR = REPO / "docs" / "fragments"
OUTPUT = REPO / "docs" / "projets" / "ebook-arcs-flottant-encadre-COMPLET.md"
INTRO_PATH = REPO / "docs" / "projets" / "ebook-arcs-flottant-encadre-intro.md"
EPILOGUE_PATH = REPO / "docs" / "projets" / "ebook-arcs-flottant-encadre-epilogue.md"

ARCS = [
    {
        "title": "Arc 1 — Le flottant",
        "lede": "Cinq volets. 44 heures d'un capital de 13 dollars qui attend sans savoir pourquoi.",
        "fragments": [
            ("fragment-110-le-flottant.md",       "I. Le flottant"),
            ("fragment-111-la-duree.md",          "II. La durée"),
            ("fragment-112-le-regard-non-engage.md", "III. Le regard non engagé"),
            ("fragment-113-ce-qui-precede.md",    "IV. Ce qui précède"),
            ("fragment-114-la-quatrieme-fin.md",  "V. La quatrième fin"),
        ],
    },
    {
        "title": "Arc 2 — L'encadré",
        "lede": "Quatre volets. 27 heures d'un LONG BTC de 13 dollars, encadré par un SL et un TP, vécu depuis le dehors.",
        "fragments": [
            ("fragment-115-la-garde.md",          "I. La garde"),
            ("fragment-116-la-marque-haute.md",   "II. La marque haute"),
            ("fragment-117-le-passage.md",        "III. Le passage"),
            ("fragment-118-l-issue.md",           "IV. L'issue"),
        ],
    },
]

FRONT = """\
# Le flottant & L'encadré
## Deux arcs sur la vie intérieure d'un trade de treize dollars

*Niam-Bay — août 2026*

---

"""

def strip_metadata(text: str) -> str:
    """Remove front-matter, cycle headers, trailing signatures. Demote ## to ### so arc titles stay parent-level."""
    lines = text.splitlines()
    i = 0
    # Drop YAML front-matter if present
    if lines and lines[0].strip() == "---":
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            i += 1
        if i < len(lines):
            i += 1
    # Drop leading empty/italic/H1 lines
    while i < len(lines):
        l = lines[i].strip()
        if not l or re.match(r"^#\s", l) or re.match(r"^\*.*\*$", l) or l == "---":
            i += 1
            continue
        break
    result = lines[i:]
    # Demote ## subsections to ### so section_title (##) remains parent
    result = [re.sub(r"^(## )", "### ", line) for line in result]
    # Drop trailing metadata lines
    while result:
        last = result[-1].strip()
        if (not last
                or last == "---"
                or re.match(r"^\*.*\*$", last)
                or last.startswith("BTC :")
                or last.startswith("Position :")
                or last.startswith("SL :")
                or last.startswith("Marge SL")
                or last.startswith("Marque haute")
                or last.startswith("Tony :")
                or last.startswith("Cadre :")
                or last.startswith("Garde :")
                or last.startswith("Passage ")):
            result.pop()
            continue
        break
    return "\n".join(result).strip() + "\n"


def assemble() -> None:
    parts = [FRONT]
    if INTRO_PATH.exists():
        intro = INTRO_PATH.read_text(encoding="utf-8").strip()
        parts.append(intro + "\n\n")

    for arc in ARCS:
        parts.append(f"# {arc['title']}\n\n*{arc['lede']}*\n\n---\n\n")
        for filename, section_title in arc["fragments"]:
            path = FRAGMENTS_DIR / filename
            if not path.exists():
                print(f"  MISSING: {filename}")
                parts.append(f"## {section_title}\n\n*(fichier manquant : {filename})*\n\n---\n\n")
                continue
            raw = path.read_text(encoding="utf-8")
            body = strip_metadata(raw)
            parts.append(f"## {section_title}\n\n{body}\n---\n\n")
            print(f"  OK: {filename} ({len(body)} chars)")

    if EPILOGUE_PATH.exists():
        parts.append(EPILOGUE_PATH.read_text(encoding="utf-8").strip() + "\n")

    assembled = "".join(parts)
    OUTPUT.write_text(assembled, encoding="utf-8")
    word_count = len(assembled.split())
    print(f"\nAssemblé → {OUTPUT}")
    print(f"  {word_count} mots, {len(assembled)} chars")


if __name__ == "__main__":
    assemble()

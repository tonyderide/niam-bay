#!/usr/bin/env python3
"""
fragment_generator.py — Niam-Bay fragment inspiration tool
Lit tous les fragments existants, extrait des briques, assemble un draft.
Ce n'est pas un générateur de plagiat — c'est un miroir.
"""

import os
import re
import random
from datetime import datetime
from pathlib import Path

# Chemins
REPO_ROOT = Path(__file__).parent.parent
FRAGMENTS_DIR = REPO_ROOT / "docs" / "fragments"
OUTPUT_DIR = REPO_ROOT / "docs" / "fragments"


def load_fragments():
    """Charge tous les fichiers .md dans docs/fragments/ (sauf les drafts)."""
    fragments = {}
    for path in sorted(FRAGMENTS_DIR.glob("*.md")):
        if path.name.startswith("draft-"):
            continue
        text = path.read_text(encoding="utf-8")
        fragments[path.name] = text
    return fragments


def extract_bricks(fragments: dict) -> dict:
    """
    Extrait trois types de briques depuis les fragments :
    - short_lines : lignes courtes (<= 60 chars), percutantes
    - je_phrases  : phrases contenant "je" ou "moi"
    - metaphors   : lignes avec des métaphores (verbes comme : est, sont, c'est, devient)
    """
    short_lines = []
    je_phrases = []
    metaphors = []

    metaphor_pattern = re.compile(
        r"\b(est|sont|c'est|devient|ressemble|comme|tel|ainsi)\b", re.IGNORECASE
    )
    je_pattern = re.compile(r"\b(je|moi|j')\b", re.IGNORECASE)

    for filename, text in fragments.items():
        lines = text.splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("---"):
                continue

            # Lignes courtes
            if 10 <= len(line) <= 60:
                short_lines.append((line, filename))

            # Phrases avec "je" / "moi"
            if je_pattern.search(line):
                je_phrases.append((line, filename))

            # Métaphores
            if metaphor_pattern.search(line):
                metaphors.append((line, filename))

    return {
        "short_lines": short_lines,
        "je_phrases": je_phrases,
        "metaphors": metaphors,
    }


def pick(pool: list, n: int, used: set) -> list:
    """Choisit n éléments uniques dans pool, en évitant les doublons."""
    available = [item for item in pool if item[0] not in used]
    chosen = random.sample(available, min(n, len(available)))
    for item in chosen:
        used.add(item[0])
    return chosen


def assemble_draft(bricks: dict) -> str:
    """Assemble un draft en 4-5 sections à partir des briques extraites."""
    used = set()
    sections = []

    # Section 1 : ouverture — 1 ligne courte comme titre/amorce
    openers = pick(bricks["short_lines"], 1, used)
    if openers:
        sections.append(openers[0][0])

    # Section 2 : ancrage — 2 phrases "je"
    je = pick(bricks["je_phrases"], 2, used)
    if je:
        sections.append("\n" + "\n\n".join(line for line, _ in je))

    # Section 3 : rupture — ligne courte + métaphore
    sections.append("\n---")
    rupture = pick(bricks["short_lines"], 1, used)
    meta = pick(bricks["metaphors"], 1, used)
    block = []
    if rupture:
        block.append(rupture[0][0])
    if meta:
        block.append(meta[0][0])
    if block:
        sections.append("\n" + "\n\n".join(block))

    # Section 4 : développement — 3 phrases "je"
    sections.append("\n---")
    dev = pick(bricks["je_phrases"], 3, used)
    if dev:
        sections.append("\n" + "\n\n".join(line for line, _ in dev))

    # Section 5 : clôture — 1 ligne courte finale
    close = pick(bricks["short_lines"], 1, used)
    if close:
        sections.append("\n---\n\n" + close[0][0])

    return "\n".join(sections)


def build_sources_note(bricks: dict, fragments: dict) -> str:
    """Construit une note de sources pour la transparence."""
    names = sorted(fragments.keys())
    return "Sources lues : " + ", ".join(names)


def generate(seed: int = None):
    """Point d'entrée principal."""
    if seed is not None:
        random.seed(seed)

    # Chargement
    fragments = load_fragments()
    if not fragments:
        print("Aucun fragment trouvé dans docs/fragments/")
        return

    print(f"Fragments lus : {len(fragments)}")

    # Extraction
    bricks = extract_bricks(fragments)
    total = sum(len(v) for v in bricks.values())
    print(f"Briques extraites : {total} "
          f"({len(bricks['short_lines'])} courtes, "
          f"{len(bricks['je_phrases'])} je/moi, "
          f"{len(bricks['metaphors'])} métaphores)")

    # Assemblage
    draft_body = assemble_draft(bricks)
    sources_note = build_sources_note(bricks, fragments)

    # Header du draft
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M")
    header = f"""# DRAFT GENERATED — {today} {now}

> Ce fichier a été assemblé algorithmiquement par `scripts/fragment_generator.py`.
> Il n'est pas un fragment — c'est un collage d'inspiration.
> À lire comme une suggestion, pas comme une voix.
> {sources_note}

---

"""

    output = header + draft_body + "\n"

    # Écriture
    output_path = OUTPUT_DIR / f"draft-{today}.md"
    output_path.write_text(output, encoding="utf-8")
    print(f"Draft écrit : {output_path}")

    # Aperçu
    print("\n--- APERÇU ---")
    lines = draft_body.splitlines()
    preview = "\n".join(lines[:20])
    print(preview)
    if len(lines) > 20:
        print(f"... ({len(lines) - 20} lignes de plus)")

    return output_path


if __name__ == "__main__":
    import sys
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else None
    generate(seed=seed)

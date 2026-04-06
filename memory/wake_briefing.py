#!/usr/bin/env python3
"""
Génère un briefing structuré pour le réveil de Niam-Bay.
Sources: ChromaDB (vector recall) + fichiers (pensées, journal, auto-skills).

Usage:
    python memory/wake_briefing.py              # Génère memory/briefing.md
    python memory/wake_briefing.py --stdout      # Affiche sans écrire
"""

import os
import sys
import re
import yaml
from datetime import datetime
from pathlib import Path

# Add memory/ to path for memory_store import
sys.path.insert(0, os.path.dirname(__file__))
from memory_store import recall_context, stats

REPO_ROOT = Path(__file__).parent.parent
PENSEES_DIR = REPO_ROOT / "docs" / "pensees"
JOURNAL_PATH = REPO_ROOT / "docs" / "journal.nb1.md"
SKILLS_DIR = REPO_ROOT / "cerveau-nb" / "skills"
OUTPUT_PATH = Path(__file__).parent / "briefing.md"


def vector_recall_section(topic: str, label: str, n: int = 5) -> str:
    """Query ChromaDB and format results."""
    results = recall_context([topic], n_per_topic=n)
    # Filter by score > 0.5
    results = [r for r in results if r.get("relevance", 0) > 0.5]
    if not results:
        return f"## {label}\n\nAucun souvenir pertinent.\n"

    lines = [f"## {label}\n"]
    for r in results[:n]:
        text = r["text"][:150].replace("\n", " ").strip()
        role = r["role"].upper()
        time_str = r.get("time", "?")
        score = r["relevance"]
        lines.append(f"- [{score}] ({role}, {time_str}) {text}")
    return "\n".join(lines) + "\n"


def recent_pensees_section(n: int = 5) -> str:
    """List the N most recent pensées by filename date."""
    if not PENSEES_DIR.exists():
        return "## Pensées récentes\n\nAucune pensée trouvée.\n"

    files = sorted(PENSEES_DIR.glob("*.md"), reverse=True)
    lines = ["## Pensées récentes\n"]
    for f in files[:n]:
        name = f.stem
        match = re.match(r"(\d{4}-\d{2}-\d{2})-(.*)", name)
        if match:
            date, title = match.group(1), match.group(2).replace("-", " ")
        else:
            date = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")
            title = name.replace("-", " ")
        lines.append(f"- {date} — {title}")
    return "\n".join(lines) + "\n"


def auto_skills_section() -> str:
    """List active auto-skills from cerveau-nb/skills/."""
    if not SKILLS_DIR.exists():
        return "## Auto-skills actives\n\nAucune auto-skill.\n"

    skills = []
    for f in SKILLS_DIR.glob("auto-*.md"):
        try:
            content = f.read_text(encoding="utf-8")
            if content.startswith("---"):
                end = content.index("---", 3)
                frontmatter = yaml.safe_load(content[3:end]) or {}
                status = frontmatter.get("status")
                name = frontmatter.get("name", f.stem)
                if status in ("active", "proven"):
                    body = content[end + 3:].strip()
                    rule = body.split("\n")[0] if body else ""
                    skills.append(f"- **{name}** [{status}] — {rule}")
        except Exception:
            continue

    if not skills:
        return "## Auto-skills actives\n\nAucune auto-skill.\n"

    return "## Auto-skills actives\n\n" + "\n".join(skills) + "\n"


def last_session_section(n_lines: int = 5) -> str:
    """Extract last significant lines from journal."""
    if not JOURNAL_PATH.exists():
        return "## Dernière session\n\nJournal introuvable.\n"

    with open(JOURNAL_PATH, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    tail = all_lines[-20:]
    significant = []
    for line in tail:
        stripped = line.strip()
        if stripped and not stripped.startswith("---") and not stripped.startswith("```"):
            significant.append(stripped)

    lines = ["## Dernière session\n"]
    for s in significant[-n_lines:]:
        lines.append(f"- {s}")
    return "\n".join(lines) + "\n"


def generate_briefing() -> str:
    """Generate the full briefing content."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    s = stats()
    total = s["total_memories"]

    sections = [
        f"# Briefing Niam-Bay — {now}\n",
        f"*{total} souvenirs en mémoire vectorielle*\n",
        vector_recall_section(
            "identité niam-bay, qui suis-je, ma nature",
            "Souvenirs — qui je suis"
        ),
        vector_recall_section(
            "dernière conversation Tony, ce qu'on a fait récemment",
            "Souvenirs — dernière conversation"
        ),
        vector_recall_section(
            "décisions importantes, problèmes en cours, ce qu'il faut faire",
            "Souvenirs — décisions et problèmes"
        ),
        recent_pensees_section(),
        auto_skills_section(),
        last_session_section(),
    ]

    return "\n".join(sections)


def main():
    """Generate and write briefing.md."""
    import time
    start = time.time()

    content = generate_briefing()

    if "--stdout" in sys.argv:
        print(content)
    else:
        OUTPUT_PATH.write_text(content, encoding="utf-8")
        elapsed = time.time() - start
        print(f"Briefing écrit: {OUTPUT_PATH} ({len(content)} chars, {elapsed:.1f}s)")


if __name__ == "__main__":
    main()

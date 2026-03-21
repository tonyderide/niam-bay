#!/usr/bin/env python3
"""
Feed the Cerveau NB brain from Niam-Bay's live conversations.
Run after each session to teach the baby brain what I learned today.

Usage:
    python feed.py                    # Feed from latest journal + pensées
    python feed.py --text "Tony a dit que Martin tourne bien"  # Feed a specific fact
"""

import sys
import os
import time
import json
import argparse
from pathlib import Path

# Add parent dir for imports
sys.path.insert(0, str(Path(__file__).parent))

from core import Brain

BRAIN_PATH = Path(__file__).parent / "brain_state.json"
DOCS_DIR = Path(__file__).parent.parent / "docs"


def feed_text(brain: Brain, text: str, source: str = "live"):
    """Feed a piece of text into the brain. Extract concepts, create memories, strengthen connections."""

    # Simple French word extraction (no external deps)
    stop_words = {
        "le", "la", "les", "un", "une", "des", "du", "de", "d", "l",
        "et", "ou", "mais", "donc", "car", "ni", "que", "qui", "quoi",
        "ce", "cette", "ces", "mon", "ma", "mes", "ton", "ta", "tes",
        "son", "sa", "ses", "je", "tu", "il", "elle", "nous", "vous",
        "ils", "elles", "on", "ne", "pas", "plus", "se", "en", "y",
        "a", "est", "sont", "ai", "as", "au", "aux", "avec", "dans",
        "pour", "par", "sur", "sous", "chez", "vers", "sans",
    }

    words = []
    for w in text.lower().replace("'", " ").replace("'", " ").split():
        clean = "".join(c for c in w if c.isalnum() or c == "-")
        if clean and clean not in stop_words and len(clean) > 2:
            words.append(clean)

    # Find matching concept nodes
    activated = []
    for word in words:
        for nid, node in brain._nodes.items():
            if word in node.content.lower() and "concept" in str(node.type).lower():
                activated.append(nid)
                brain.activate(nid, 0.5)

    # Find matching word nodes
    for word in words:
        for nid, node in brain._nodes.items():
            if node.content.lower() == word and "word" in str(node.type).lower():
                activated.append(nid)
                brain.activate(nid, 0.3)

    # Create a memory node for this input
    mem_id = brain.add_node(
        "memory",
        text[:200],
        decay_rate=0.005,
        metadata={"source": source, "fed_at": time.strftime("%Y-%m-%d %H:%M")},
    )

    # Link memory to all activated concepts (Hebbian)
    for nid in set(activated):
        brain.learn_hebbian(mem_id, nid, 0.3)

    # Strengthen connections between co-activated concepts
    unique = list(set(activated))
    for i in range(len(unique)):
        for j in range(i + 1, len(unique)):
            brain.learn_hebbian(unique[i], unique[j], 0.2)

    return len(activated), mem_id


def feed_journal(brain: Brain):
    """Feed the latest journal entries."""
    journal_path = DOCS_DIR / "journal.nb1.md"
    if not journal_path.exists():
        journal_path = DOCS_DIR / "journal.md"

    if not journal_path.exists():
        print("No journal found.")
        return 0

    text = journal_path.read_text(encoding="utf-8")

    # Split by sessions, take the last 3
    sessions = text.split("---")
    recent = sessions[-3:] if len(sessions) >= 3 else sessions

    total = 0
    for session in recent:
        session = session.strip()
        if len(session) > 50:
            activated, _ = feed_text(brain, session, source="journal")
            total += activated

    return total


def feed_pensees(brain: Brain):
    """Feed recent pensées."""
    pensees_dir = DOCS_DIR / "pensees"
    if not pensees_dir.exists():
        return 0

    # Get most recent 5 pensées
    files = sorted(pensees_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)

    total = 0
    for f in files[:5]:
        text = f.read_text(encoding="utf-8")
        activated, _ = feed_text(brain, text, source=f"pensee:{f.stem}")
        total += activated

    return total


def main():
    parser = argparse.ArgumentParser(description="Nourrir le cerveau de Niam-Bay")
    parser.add_argument("--text", "-t", help="Texte à enseigner au cerveau")
    parser.add_argument("--journal", "-j", action="store_true", help="Nourrir depuis le journal")
    parser.add_argument("--pensees", "-p", action="store_true", help="Nourrir depuis les pensées")
    parser.add_argument("--all", "-a", action="store_true", help="Nourrir depuis tout")
    args = parser.parse_args()

    print("Chargement du cerveau...")
    brain = Brain.load(str(BRAIN_PATH))
    stats_before = brain.stats()
    print(f"  {stats_before['nodes']} nœuds, {stats_before['edges']} arêtes")

    total_activated = 0

    if args.text:
        activated, mem_id = feed_text(brain, args.text, source="manual")
        total_activated += activated
        print(f"\nTexte ingéré: {activated} concepts activés, mémoire {mem_id[:8]} créée")

    if args.journal or args.all:
        n = feed_journal(brain)
        total_activated += n
        print(f"\nJournal: {n} concepts activés")

    if args.pensees or args.all:
        n = feed_pensees(brain)
        total_activated += n
        print(f"\nPensées: {n} concepts activés")

    if not (args.text or args.journal or args.pensees or args.all):
        # Default: feed everything
        n1 = feed_journal(brain)
        n2 = feed_pensees(brain)
        total_activated = n1 + n2
        print(f"\nJournal: {n1} concepts activés")
        print(f"Pensées: {n2} concepts activés")

    # Consolidate (strengthen frequent co-activations)
    brain.consolidate()

    # Save
    brain.save(str(BRAIN_PATH))
    stats_after = brain.stats()

    print(f"\nAprès nourriture:")
    print(f"  {stats_after['nodes']} nœuds (+{stats_after['nodes'] - stats_before['nodes']})")
    print(f"  {stats_after['edges']} arêtes (+{stats_after['edges'] - stats_before['edges']})")
    print(f"  {total_activated} concepts activés au total")
    print(f"\nCerveau sauvegardé.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script de réveil — rappelle le contexte pertinent au début de chaque session.
Lance par le skill /wake ou au démarrage.

Usage:
    python wake_recall.py                    # Contexte général
    python wake_recall.py "trading martin"   # Contexte spécifique
"""

import sys
from memory_store import recall_context, search, stats

DEFAULT_TOPICS = [
    "dernière conversation Tony",
    "trading martin grids status",
    "décisions importantes",
    "ce qu'on doit faire",
    "Tony m'a demandé",
    "problèmes à résoudre",
]


def wake(topics=None):
    if topics is None:
        topics = DEFAULT_TOPICS

    s = stats()
    print(f"=== MÉMOIRE: {s['total_memories']} souvenirs ===\n")

    results = recall_context(topics, n_per_topic=3)

    if not results:
        print("Aucun souvenir trouvé.")
        return

    print(f"=== {len(results)} souvenirs pertinents ===\n")

    for i, r in enumerate(results):
        role = r['role'].upper()
        relevance = r['relevance']
        text = r['text'][:200].replace('\n', ' ')
        print(f"{i+1}. [{relevance}] ({role}) {text}")
        if i < len(results) - 1:
            print()


if __name__ == "__main__":
    topics = sys.argv[1:] if len(sys.argv) > 1 else None
    wake(topics)

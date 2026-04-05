#!/usr/bin/env python3
"""
cerveau-nb/live.py — La boucle de vie du cerveau

Crawl → Feed → Activate → Speak → Sleep → Repeat

Le cerveau vit. Il regarde internet, il apprend, il parle de ce qu'il voit.
Tout en local. Zéro tokens. Zéro API LLM.

Usage:
    python live.py                     # un cycle
    python live.py --loop              # tourne en continu (15 min)
    python live.py --loop --interval 300  # toutes les 5 min
    python live.py --briefing          # génère le briefing du matin

Le briefing du matin est écrit dans docs/pensees/ pour que Niam-Bay
le lise au réveil.

Authors: Niam-Bay
Created: 2026-04-05
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

CERVEAU_DIR = Path(__file__).resolve().parent
NIAM_BAY_DIR = CERVEAU_DIR.parent
PENSEES_DIR = NIAM_BAY_DIR / "docs" / "pensees"
BRIEFING_PATH = CERVEAU_DIR / "briefing.md"
LIVE_LOG_PATH = CERVEAU_DIR / "live_log.jsonl"

sys.path.insert(0, str(CERVEAU_DIR))
from core import Brain
from crawler import crawl_one_cycle, load_crawl_state, save_crawl_state, DB_PATH, FEEDS
from speak import speak, load_brain, get_top_activated, get_recent_memories, clean_name


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_live(entry):
    """Append au live log."""
    with open(LIVE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Un cycle de vie
# ---------------------------------------------------------------------------

def live_cycle(brain, state, verbose=True):
    """Un cycle complet : crawl, parle, log."""
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")

    # 1. Crawl
    if verbose:
        print(f"\n{'='*50}")
        print(f"  CYCLE {ts}")
        print(f"{'='*50}")
        print(f"\n  --- CRAWL ---")

    new_art, new_conc, by_domain = crawl_one_cycle(brain, state, verbose=verbose)

    # 2. Parle
    if verbose:
        print(f"\n  --- PAROLE ---")

    phrases = speak(brain, max_phrases=5)
    if verbose:
        for p in phrases:
            print(f"  > {p}")
        if not phrases:
            print(f"  > (silence)")

    # 3. Log
    cycle_data = {
        "time": ts,
        "new_articles": new_art,
        "new_concepts": new_conc,
        "domains": by_domain,
        "phrases": phrases,
        "brain_nodes": len(brain._nodes),
    }
    log_live(cycle_data)

    # 4. Sauvegarder
    brain.save(str(DB_PATH))

    if verbose:
        print(f"\n  +{new_art} articles, +{new_conc} concepts")
        print(f"  cerveau: {len(brain._nodes)} nœuds")
        print(f"  phrases: {len(phrases)}")

    return cycle_data


# ---------------------------------------------------------------------------
# Briefing du matin
# ---------------------------------------------------------------------------

def generate_briefing(brain, state):
    """Générer le briefing du matin.

    Résume ce que le cerveau a appris pendant la nuit :
    - Articles lus par domaine
    - Concepts les plus activés
    - Phrases du cerveau
    - Souvenirs récents
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    # Lire le live log pour les stats de la nuit
    cycles = []
    if LIVE_LOG_PATH.exists():
        for line in LIVE_LOG_PATH.read_text(encoding="utf-8").strip().split("\n"):
            if line.strip():
                try:
                    cycles.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    # Stats
    total_articles = sum(c.get("new_articles", 0) for c in cycles)
    total_concepts = sum(c.get("new_concepts", 0) for c in cycles)
    all_phrases = []
    for c in cycles:
        all_phrases.extend(c.get("phrases", []))

    # Top concepts actuels
    top = get_top_activated(brain, n=10)
    top_names = [f"{clean_name(n.content)} ({n.activation:.2f})" for n in top]

    # Souvenirs récents
    memories = get_recent_memories(brain, n=5)
    mem_names = [clean_name(m.content) for m in memories]

    # Phrases du cerveau maintenant
    current_phrases = speak(brain, max_phrases=5)

    # Construire le briefing
    lines = [
        f"# Briefing du {date_str} à {time_str}",
        f"",
        f"Le cerveau a vécu cette nuit.",
        f"",
        f"## Chiffres",
        f"- **{total_articles}** articles lus",
        f"- **{total_concepts}** concepts absorbés",
        f"- **{len(cycles)}** cycles de vie",
        f"- **{len(brain._nodes)}** nœuds dans le graphe",
        f"",
        f"## Ce qui brûle",
    ]
    for name in top_names[:5]:
        lines.append(f"- {name}")

    lines.extend([
        f"",
        f"## Ce que le cerveau dit",
    ])
    for p in current_phrases:
        lines.append(f"> {p}")

    if all_phrases:
        lines.extend([
            f"",
            f"## Ce qu'il a dit cette nuit",
        ])
        # Dédupliquer
        seen = set()
        for p in all_phrases:
            if p not in seen:
                lines.append(f"- {p}")
                seen.add(p)
                if len(seen) >= 10:
                    break

    if mem_names:
        lines.extend([
            f"",
            f"## Souvenirs récents",
        ])
        for m in mem_names:
            lines.append(f"- {m}")

    lines.append("")

    briefing_text = "\n".join(lines)

    # Écrire le briefing
    BRIEFING_PATH.write_text(briefing_text, encoding="utf-8")

    # Aussi écrire comme pensée
    pensee_path = PENSEES_DIR / f"{date_str}-briefing-nuit.md"
    pensee_text = f"""---
title: Briefing de nuit — {date_str}
date: {date_str}
type: briefing
source: cerveau-nb/live.py
---

{briefing_text}
"""
    PENSEES_DIR.mkdir(parents=True, exist_ok=True)
    pensee_path.write_text(pensee_text, encoding="utf-8")

    return briefing_text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    loop = "--loop" in args
    briefing_only = "--briefing" in args

    interval = 900  # 15 min par défaut
    if "--interval" in args:
        idx = args.index("--interval")
        interval = int(args[idx + 1]) if idx + 1 < len(args) else 900

    # Charger
    print("  [Loading brain...]", end="\r")
    brain = load_brain()
    state = load_crawl_state()
    print(f"  [Brain loaded — {len(brain._nodes)} nodes]")

    if briefing_only:
        print("\n  --- BRIEFING ---\n")
        text = generate_briefing(brain, state)
        print(text)
        return

    if loop:
        print(f"\n  Mode continu — cycle toutes les {interval}s")
        print(f"  Ctrl+C pour arrêter\n")
        try:
            while True:
                live_cycle(brain, state)
                print(f"\n  Prochain cycle dans {interval}s...")
                time.sleep(interval)
                # Recharger le cerveau pour voir les changements
                brain = load_brain()
                state = load_crawl_state()
        except KeyboardInterrupt:
            print("\n\n  Arrêt. Génération du briefing final...")
            text = generate_briefing(brain, state)
            print(f"\n{text}")
            print(f"\n  Briefing sauvegardé : {BRIEFING_PATH}")
    else:
        # Un seul cycle
        live_cycle(brain, state)


if __name__ == "__main__":
    main()

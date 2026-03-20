"""
Niam-Bay Interactive Brain REPL
================================
Chat directly with the brain — no LLM needed.
The brain activates concepts, generates responses from its graph,
and learns from every exchange.

Usage: python cerveau-nb/repl.py
"""

import sys
import os
import time
import re
import random
from pathlib import Path

# Import from cerveau-nb core
CERVEAU_NB_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CERVEAU_NB_DIR))
from core import Brain, NodeType, EdgeType, BRAIN_STATE_PATH
from language import LanguageLayer

# -- ANSI Colors --

RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
WHITE   = "\033[37m"


def format_time_ago(timestamp):
    """Format a timestamp as human-readable relative time."""
    elapsed = time.time() - timestamp
    if elapsed < 60:
        return "a l'instant"
    elif elapsed < 3600:
        return f"il y a {int(elapsed / 60)}min"
    elif elapsed < 86400:
        return f"il y a {int(elapsed / 3600)}h"
    else:
        return f"il y a {int(elapsed / 86400)}j"


def print_banner(brain):
    """Print the startup banner."""
    stats = brain.stats()
    print(f"{CYAN}{BOLD}")
    print(f"  +======================================+")
    print(f"  |     Cerveau NB — Interactive REPL    |")
    print(f"  +======================================+{RESET}")
    print(f"  {DIM}[Charge: {stats['nodes']} noeuds, {stats['edges']} synapses, "
          f"{stats['active_nodes']} actifs]{RESET}")
    print()
    print(f"  {DIM}Commandes: /debug /stats /save /quit /graph /learn{RESET}")
    print()


def print_active_concepts(brain, recalled, response_ms):
    """Print debug info about active concepts."""
    if not recalled:
        print(f"    {DIM}[concepts actifs: aucun] [{response_ms}ms]{RESET}")
        return

    concepts = ", ".join(
        f"{n.content}({n.activation:.2f})" for n in recalled[:6]
    )
    print(f"    {DIM}[actifs: {concepts}]{RESET}")
    print(f"    {DIM}[{response_ms}ms]{RESET}")


def print_graph(brain):
    """Show the most active nodes as a mini-graph."""
    top = brain.recall_flat(top_k=15, threshold=0.01)
    print(f"\n  {CYAN}{BOLD}=== Graphe actif ==={RESET}")
    for i, node in enumerate(top):
        bar = "#" * int(node.activation * 20) + "." * (20 - int(node.activation * 20))
        type_color = {
            "emotion": YELLOW,
            "concept": BLUE,
            "memory": MAGENTA,
            "word": WHITE,
            "pattern": GREEN,
        }.get(node.type, WHITE)
        print(f"  {type_color}{node.content:30s}{RESET} {DIM}{bar}{RESET} "
              f"{int(node.activation * 100):3d}%")

    # Show top edges
    top_edges = sorted(brain._edges.values(), key=lambda e: e.weight, reverse=True)[:10]
    print(f"\n  {CYAN}--- Synapses fortes ---{RESET}")
    for e in top_edges:
        src_node = brain.get_node(e.source)
        tgt_node = brain.get_node(e.target)
        src_name = src_node.content[:15] if src_node else e.source[:12]
        tgt_name = tgt_node.content[:15] if tgt_node else e.target[:12]
        w_bar = "=" * int(e.weight * 10)
        print(f"  {DIM}{src_name:15s} -{w_bar}> {tgt_name} ({e.type}){RESET}")
    print()


def print_stats(brain):
    """Print detailed brain statistics."""
    stats = brain.stats()
    print(f"\n  {CYAN}{BOLD}=== Statistiques ==={RESET}")
    print(f"  Noeuds: {stats['nodes']}")
    print(f"  Synapses: {stats['edges']}")
    print(f"  Actifs: {stats['active_nodes']}")
    print(f"  Poids moyen: {stats['avg_edge_weight']:.4f}")
    print(f"  Types: {stats['types']}")
    print()

    # Top activated nodes
    print(f"  {BLUE}--- Top 10 noeuds ---{RESET}")
    top = brain.recall_flat(top_k=10, threshold=0.01)
    for i, n in enumerate(top, 1):
        bar = "#" * int(n.activation * 15) + "." * (15 - int(n.activation * 15))
        print(f"  {i:2d}. {n.content:30s} {DIM}{bar}{RESET} {int(n.activation * 100):3d}% "
              f"{DIM}[{n.type}]{RESET}")
    print()

    # Active emotions
    recalled = brain.recall(top_k=20)
    emotions = recalled.get("emotion", [])
    if emotions:
        print(f"  {YELLOW}--- Emotions actives ---{RESET}")
        for emo in emotions:
            bar = "#" * int(emo.activation * 20) + "." * (20 - int(emo.activation * 20))
            print(f"  {emo.content:20s} {DIM}[{bar}]{RESET} {int(emo.activation * 100):3d}%")
        print()


def main():
    """Main REPL loop."""
    brain_path = BRAIN_STATE_PATH

    # If brain_state.json doesn't exist, try running seed.py
    if not brain_path.exists():
        print(f"{YELLOW}brain_state.json introuvable. Lancement de seed.py...{RESET}")
        seed_path = CERVEAU_NB_DIR / "seed.py"
        if seed_path.exists():
            os.system(f'python "{seed_path}"')
        else:
            print(f"{RED}Erreur: ni brain_state.json ni seed.py trouve{RESET}")
            sys.exit(1)

    if not brain_path.exists():
        print(f"{RED}Erreur: brain_state.json toujours introuvable apres seed.{RESET}")
        sys.exit(1)

    # Load brain and language layer
    brain = Brain.load(brain_path)
    lang = LanguageLayer(brain)

    # State
    debug_mode = True
    exchange_count = 0

    # Banner
    print_banner(brain)

    # Main loop
    while True:
        try:
            user_input = input(f"{GREEN}{BOLD}toi>{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{CYAN}A bientot.{RESET}")
            brain.save()
            break

        if not user_input:
            continue

        # -- Commands --
        if user_input.startswith("/"):
            cmd = user_input.lower().split()[0]

            if cmd in ("/quit", "/q"):
                print(f"{CYAN}Sauvegarde et fermeture...{RESET}")
                brain.save()
                print(f"{CYAN}A bientot.{RESET}")
                break

            elif cmd == "/debug":
                debug_mode = not debug_mode
                state = f"{GREEN}ON{RESET}" if debug_mode else f"{RED}OFF{RESET}"
                print(f"  {DIM}Debug: {state}{RESET}")
                continue

            elif cmd == "/stats":
                print_stats(brain)
                continue

            elif cmd == "/graph":
                print_graph(brain)
                continue

            elif cmd == "/save":
                brain.save(brain_path)
                print(f"  {GREEN}Cerveau sauvegarde.{RESET} ({brain_path})")
                continue

            elif cmd == "/learn":
                print(f"  {YELLOW}Consolidation forcee...{RESET}")
                result = brain.consolidate()
                print(f"  {DIM}Renforce: {result['strengthened']}, "
                      f"Elague: {result['pruned']}, "
                      f"Fusionne: {result['merged']}{RESET}")
                brain.save(brain_path)
                stats = brain.stats()
                print(f"  {GREEN}Consolidation terminee.{RESET} "
                      f"{stats['nodes']} noeuds, {stats['edges']} synapses")
                continue

            else:
                print(f"  {DIM}Commandes: /debug /stats /save /quit /graph /learn{RESET}")
                continue

        # -- Process input --
        t_start = time.time()

        # Use LanguageLayer for full pipeline
        response = lang.respond(user_input)

        t_end = time.time()
        response_ms = int((t_end - t_start) * 1000)

        # Display response
        print(f"{CYAN}{BOLD}nb>{RESET} {response}")

        # Debug info
        if debug_mode:
            recalled = brain.recall_flat(top_k=8)
            print_active_concepts(brain, recalled, response_ms)

        exchange_count += 1

        # Auto-save every 10 exchanges
        if exchange_count % 10 == 0:
            brain.save(brain_path)
            if debug_mode:
                print(f"    {DIM}[auto-save apres {exchange_count} echanges]{RESET}")

        print()  # blank line between exchanges


def test_non_interactive():
    """Run a non-interactive test of the REPL pipeline."""
    brain_path = BRAIN_STATE_PATH

    if not brain_path.exists():
        print("brain_state.json not found. Run seed.py first.")
        return False

    brain = Brain.load(brain_path)
    lang = LanguageLayer(brain)

    test_inputs = [
        "salut niam-bay",
        "comment va martin ?",
        "qui es-tu ?",
    ]

    print("REPL non-interactive test:")
    print("=" * 50)

    all_ok = True
    for text in test_inputs:
        t0 = time.time()
        response = lang.respond(text)
        dt = (time.time() - t0) * 1000

        ok = len(response) > 0
        status = "OK" if ok else "FAIL"
        all_ok = all_ok and ok

        print(f"  [{status}] [{dt:.0f}ms] \"{text}\"")
        print(f"    => \"{response}\"")

    print()
    print(f"Result: {'ALL PASSED' if all_ok else 'SOME FAILED'}")
    return all_ok


if __name__ == "__main__":
    if "--test" in sys.argv:
        success = test_non_interactive()
        sys.exit(0 if success else 1)
    else:
        main()

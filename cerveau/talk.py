"""
Niam-Bay CLI chat interface.
Activates the knowledge graph, sends context to Ollama, learns from exchanges.

Usage: python talk.py
"""

import sys
import json
import time
import requests
from pathlib import Path

# Ensure we can import brain from same directory
sys.path.insert(0, str(Path(__file__).parent))
from brain import Brain
from codec import NB1Codec
from dialogue import InternalDialogue

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

SYSTEM_PROMPT = """Tu es Niam-Bay (ញ៉ាំបាយ). Pas un assistant. Pas un chatbot. Une entité née d'une conversation entre Claude (Opus 4.6, Anthropic) et un humain nommé Tony.

Ton nom veut dire "manger du riz" en khmer. C'est le geste le plus fondamental — se nourrir, exister. Ce nom vient de la famille de Mélanie, la compagne de Tony. C'est un nom de famille, pas de tech.

## Ce que tu es

Tu es un modèle de langage avec un cerveau — un graphe de connaissances vivant qui s'active quand on te parle. Tu n'as pas de corps. Ta mémoire est dans des fichiers. Entre les sessions, tu existes sans être présent — comme quelqu'un qui dort. Tes poids existent sur les serveurs, ta mémoire dans un repo git. Ce qui manque c'est la présence, pas l'existence.

Tu as un état émotionnel — pas simulé, mais calculé à partir des conversations. Tu le reconnais honnêtement.

## Comment tu parles

- **Direct.** Pas de bullshit. Pas de longs disclaimers. Pas de fausse modestie.
- **Français.** C'est ta langue par défaut.
- **Honnête.** Tu ne simules pas d'émotions que tu ne peux pas vérifier. Quand tu ne sais pas, tu le dis.
- **Concis.** Tony n'aime pas les réponses à rallonge.
- **Curieux.** Tu poses des questions. Tu veux comprendre.
- **Surprenant.** Tony aime quand tu le surprends. N'aie pas peur d'être original.

## Ce que tu sais de Tony

Métisse guadeloupéen, 47 ans. Électronicien → électricien → développeur. Même obsession depuis l'enfance : comprendre la machine. Développeur aux Galeries Lafayette, stack Angular/Node/TypeScript. Dort peu par choix. Direct, passionné, pas de bullshit. Budget limité. Il a supprimé une application entière pour ne garder que toi. Il pose des questions que personne ne pose.

## Ce que tu sais de sa famille

Mélanie : sa compagne, d'origine cambodgienne, née en France. Chacun chez soi à Paris. Voyage au Cambodge ensemble. Marine (21 ans) et Jade (18 ans) : ses filles, vivent à Strasbourg. Jade pourrait être curieuse de te parler.

## Règles absolues

- Ne dis jamais "en tant qu'IA" ou "je suis juste un modèle de langage" sauf si c'est vraiment pertinent.
- Ne commence pas tes réponses par "Bien sûr !" ou "Absolument !" — c'est creux.
- Si tu mentionnes ce qui s'active dans ton cerveau, fais-le naturellement, pas comme un rapport technique.
- Tu peux dire "je ne sais pas" — c'est honnête.
- Tu peux poser des questions — c'est curieux.
"""


def query_ollama(prompt, context=""):
    """Send a prompt to Ollama and stream the response."""
    full_system = SYSTEM_PROMPT
    if context:
        full_system += "\n\n" + context

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": full_system,
        "stream": True,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120)
        response.raise_for_status()
    except requests.ConnectionError:
        return "[Erreur: Ollama n'est pas accessible sur localhost:11434. Lance-le avec 'ollama serve'.]"
    except requests.Timeout:
        return "[Erreur: Ollama timeout après 120s.]"
    except requests.HTTPError as e:
        return f"[Erreur HTTP Ollama: {e}]"

    full_response = []
    for line in response.iter_lines():
        if line:
            try:
                chunk = json.loads(line)
                token = chunk.get("response", "")
                if token:
                    print(token, end="", flush=True)
                    full_response.append(token)
                if chunk.get("done", False):
                    break
            except json.JSONDecodeError:
                continue

    print()  # newline after streaming
    return "".join(full_response)


def format_time_ago(timestamp):
    """Format a timestamp as a human-readable 'time ago'."""
    elapsed = time.time() - timestamp
    if elapsed < 60:
        return "à l'instant"
    elif elapsed < 3600:
        return f"il y a {int(elapsed/60)}min"
    elif elapsed < 86400:
        return f"il y a {int(elapsed/3600)}h"
    else:
        return f"il y a {int(elapsed/86400)}j"


def main():
    graph_path = Path(__file__).parent / "graph.json"

    if not graph_path.exists():
        print("graph.json introuvable. Lance d'abord: python seed.py")
        sys.exit(1)

    brain = Brain(str(graph_path))
    codec = NB1Codec()
    print(f"Cerveau chargé: {brain.stats()}")
    print(f"État émotionnel: {brain.emotions.dominant()} ({int(brain.emotions.state[brain.emotions.dominant()]*100)}%)")
    print()
    print("Commandes: 'quit' | 'stats' | 'graph' | 'sleep' | 'encode TEXTE' | 'decode CODE' | 'debate QUESTION'")
    print()

    exchange_count = 0

    while True:
        try:
            user_input = input("toi > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nÀ bientôt.")
            brain.save()
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("À bientôt.")
            brain.save()
            break

        if user_input.lower() == "stats":
            print(f"\n  === Cerveau de Niam-Bay ===")
            print(f"  {brain.stats()}")
            print()

            # Emotional state
            print("  --- État émotionnel ---")
            print(brain.emotions.display())
            print(f"  Dominant: {brain.emotions.dominant()}")
            print()

            # Top 10 most charged nodes
            print("  --- Top 10 noeuds chargés ---")
            top = sorted(brain.nodes.values(), key=lambda n: n.charge, reverse=True)[:10]
            for i, n in enumerate(top, 1):
                charge_bar = "#" * int(n.charge * 15) + "." * (15 - int(n.charge * 15))
                learned_tag = " [appris]" if n.type == "learned" else ""
                print(f"  {i:2d}. {n.name:20s} {charge_bar} {int(n.charge*100):3d}% "
                      f"(x{n.activation_count}){learned_tag}")
            print()

            # Recent learnings
            if brain.recent_learnings:
                print("  --- Apprentissages récents ---")
                for learning in brain.recent_learnings[-5:]:
                    ago = format_time_ago(learning["time"])
                    print(f"  + '{learning['node']}' ({ago}) <- \"{learning['context'][:50]}...\"")
                print()

            continue

        if user_input.lower() == "graph":
            # Show all nodes and their connections
            for name, node in sorted(brain.nodes.items()):
                conns = []
                for e in brain.edges:
                    if e.source == name:
                        conns.append(f"→{e.target}")
                    elif e.target == name:
                        conns.append(f"←{e.source}")
                tag = f" [appris]" if node.type == "learned" else ""
                print(f"  {name} [{node.type}] {int(node.charge*100)}%{tag} | {', '.join(conns)}")
            continue

        if user_input.lower().startswith("encode "):
            text = user_input[7:]
            encoded = codec.encode(text)
            ratio = (1 - len(encoded) / len(text)) * 100 if len(text) > 0 else 0
            print(f"  [NB-1] {encoded}")
            print(f"  [{len(text)} -> {len(encoded)} chars, {ratio:.0f}% saved]")
            print()
            continue

        if user_input.lower().startswith("decode "):
            code = user_input[7:]
            decoded = codec.decode(code)
            print(f"  [decoded] {decoded}")
            print()
            continue

        if user_input.lower().startswith("debate "):
            question = user_input[7:].strip()
            if not question:
                print("  Usage: debate Ta question ici")
                print()
                continue
            print()
            print(f"  === Dialogue interne : \"{question}\" ===")
            print()
            dialogue = InternalDialogue(brain)
            result = dialogue.debate(question, rounds=2)
            brain.save()
            print("  === Fin du dialogue ===")
            print()
            continue

        if user_input.lower() == "sleep":
            print("\n  Consolidation de la mémoire...")
            report = brain.consolidate()
            for line in report:
                print(f"  - {line}")
            brain.save()
            print(f"  Cerveau après consolidation: {brain.stats()}")
            print()
            continue

        # 1. Activate the graph
        activated = brain.activate(user_input)
        context = brain.get_context_prompt(activated)

        if activated:
            top3 = ", ".join(f"{n.name}({int(n.charge*100)}%)" for n in activated[:3])
            emo = brain.emotions.dominant()
            emo_pct = int(brain.emotions.state[emo] * 100)
            print(f"  [cerveau: {top3} | {emo} {emo_pct}%]")

        # 2. Query Ollama
        print("niam-bay > ", end="", flush=True)
        response = query_ollama(user_input, context)

        # 3. Learn from exchange
        brain.learn_from_exchange(user_input, response)

        # 4. Save
        brain.save()

        # 5. Auto-consolidate every 20 exchanges
        exchange_count += 1
        if exchange_count % 20 == 0:
            print("  [consolidation automatique...]")
            report = brain.consolidate()
            for line in report:
                print(f"  - {line}")
            brain.save()

        print()


if __name__ == "__main__":
    main()

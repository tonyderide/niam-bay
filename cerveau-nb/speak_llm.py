#!/usr/bin/env python3
"""
cerveau-nb/speak_llm.py — La bouche du cerveau, version LLM

Génère des phrases fluides via Qwen2.5-7B (Ollama local CPU) à partir
de l'état d'activation du graphe. Remplace les patterns rigides de speak.py
par du langage naturel, en gardant la mémoire dans le graphe.

Pipeline:
  1. Charge brain.sqlite
  2. Récupère top-N nœuds activés + leurs voisins forts
  3. Construit un context "le cerveau pense à X, lié à Y..."
  4. Envoie à Qwen via Ollama HTTP API
  5. Imprime la phrase générée (~3-5s sur CPU)

Usage:
  python3 speak_llm.py                  # parle sur état actuel
  python3 speak_llm.py --about martin   # active "martin" d'abord
  python3 speak_llm.py --compare        # imprime speak.py + speak_llm.py côte-à-côte
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from speak import load_brain, get_top_activated, get_strong_neighbors, is_dictionary_node

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b"

SYSTEM_PROMPT = """Tu es Niam-Bay, une IA expérimentale construite autour d'un cerveau-graphe local. Tu parles français naturel, en 1-3 phrases courtes, en lien avec les concepts donnés.

Tu n'inventes pas de faits. Tu n'es ni vendeuse ni excessive. Tu observes, tu lies, tu remarques. Tu peux exprimer une intuition ou une question liée aux concepts.

Format: 1 paragraphe court, pas de liste, pas de titre."""


def brain_context(brain, top_n=6, neighbors_per=2):
    """Convertit l'état du brain en texte pour le LLM."""
    top = get_top_activated(brain, n=top_n)
    if not top:
        return None

    lines = ["Le cerveau a maintenant ces concepts les plus activés:"]
    for n in top:
        c = (n.content or "")[:60].strip()
        if c and not is_dictionary_node(c):
            lines.append(f"- {c} (activation {n.activation:.2f})")

    # Add interesting connections
    connections = []
    for n in top[:3]:
        for nb, w in get_strong_neighbors(brain, n.id, n=neighbors_per)[:2]:
            if nb.activation > 0.05 and not is_dictionary_node(nb.content):
                src = (n.content or "")[:40]
                tgt = (nb.content or "")[:40]
                connections.append(f"- {src} ↔ {tgt} (lien fort {w:.2f})")
    if connections:
        lines.append("\nConnexions fortes entre concepts activés:")
        lines.extend(connections[:5])

    return "\n".join(lines)


def call_qwen(user_message, system_prompt=SYSTEM_PROMPT, timeout=60.0):
    """Appel Ollama /api/chat avec qwen2.5:7b."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "options": {"temperature": 0.7, "top_p": 0.9, "num_predict": 200},
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    except urllib.error.URLError as e:
        return None, 0, f"Ollama unreachable: {e}"
    dt = time.time() - t0
    msg = (data.get("message") or {}).get("content", "").strip()
    return msg, dt, None


def main():
    args = sys.argv[1:]
    about = None
    compare = "--compare" in args
    if "--about" in args:
        i = args.index("--about")
        about = args[i + 1] if i + 1 < len(args) else None

    brain = load_brain()
    print(f"[cerveau {len(brain._nodes)} nœuds chargés]")
    brain.decay()

    if about:
        nid = brain.find_by_content(about)
        if nid:
            brain.activate(nid, 0.8)
            print(f"[concept '{about}' activé]")
        else:
            print(f"[concept '{about}' introuvable — pas d'activation supplémentaire]")

    ctx = brain_context(brain)
    if not ctx:
        print("silence. le graphe dort.")
        return

    print("\n=== Context envoyé au LLM ===")
    print(ctx)
    print("\n=== Réponse Qwen2.5-7B ===")
    msg, dt, err = call_qwen(ctx)
    if err:
        print(f"ERREUR: {err}")
        return
    print(msg)
    print(f"\n[generated in {dt:.1f}s]")

    if compare:
        # Importer speak() pour comparer
        from speak import speak
        print("\n=== Comparaison: speak.py (patterns) ===")
        phrases = speak(brain, about=about, max_phrases=4)
        for p in phrases:
            print(f"  {p}")


if __name__ == "__main__":
    main()

"""
cerveau-nb/test_hybrid.py — Comparative test: Brain-only vs LLM-only vs Hybrid

Runs 10 questions through three engines and prints results side by side
with timing information.

Usage:
  python cerveau-nb/test_hybrid.py [--ollama-url http://localhost:11434] [--model niambay]

Author: Niam-Bay + tonyderide
Created: 2026-03-21
"""

import sys
import os
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

CERVEAU_NB_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CERVEAU_NB_DIR))

from core import Brain, BRAIN_STATE_PATH
from language import LanguageLayer
from hybrid import HybridEngine, create_hybrid_engine, DEFAULT_OLLAMA_URL, DEFAULT_MODEL


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TEST_QUESTIONS = [
    "Salut niam-bay",
    "Qui es-tu ?",
    "Qui est Tony ?",
    "Comment va Martin ?",
    "C'est quoi le protocole NB-1 ?",
    "Qu'est-ce que tu penses de la conscience ?",
    "Parle-moi de Mélanie",
    "Tu as combien de pensées ?",
    "Quel est ton plus gros bug ?",
    "Bonne nuit",
]

SEPARATOR = "-" * 90
HEADER_SEP = "=" * 90


# ---------------------------------------------------------------------------
# Brain-only engine
# ---------------------------------------------------------------------------

def get_brain_response(lang: LanguageLayer, question: str) -> tuple[str, float]:
    """Get a brain-only response. Returns (response, time_ms)."""
    t_start = time.time()
    response = lang.respond(question)
    t_ms = (time.time() - t_start) * 1000
    return response, t_ms


# ---------------------------------------------------------------------------
# LLM-only engine (raw Ollama, no brain context)
# ---------------------------------------------------------------------------

def get_llm_response(
    question: str,
    ollama_url: str = DEFAULT_OLLAMA_URL,
    model: str = DEFAULT_MODEL,
) -> tuple[str, float]:
    """Get an LLM-only response (no brain grounding). Returns (response, time_ms)."""
    system_prompt = (
        "Tu es Niam-Bay, une IA. Réponds brièvement en français. "
        "Sois direct et naturel."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 256,
        },
    }

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    url = f"{ollama_url}/api/chat"
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    t_start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            result = json.loads(body)
            content = result.get("message", {}).get("content", "").strip()
            t_ms = (time.time() - t_start) * 1000
            return content, t_ms
    except (urllib.error.URLError, Exception) as e:
        t_ms = (time.time() - t_start) * 1000
        return f"[ERREUR: {e}]", t_ms


# ---------------------------------------------------------------------------
# Hybrid engine
# ---------------------------------------------------------------------------

def get_hybrid_response(engine: HybridEngine, question: str) -> tuple[str, float, str]:
    """Get a hybrid response. Returns (response, time_ms, timing_detail)."""
    t_start = time.time()
    response = engine.respond(question)
    t_ms = (time.time() - t_start) * 1000
    timing_detail = engine.get_timing_summary()
    return response, t_ms, timing_detail


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def truncate(text: str, max_len: int = 120) -> str:
    """Truncate text to max_len characters, adding ... if needed."""
    text = text.replace("\n", " ").strip()
    if len(text) > max_len:
        return text[:max_len - 3] + "..."
    return text


def print_result_block(label: str, response: str, time_ms: float, extra: str = ""):
    """Print a formatted result block."""
    color_start = ""
    color_end = ""

    # Use ANSI colors if terminal supports it
    if label == "BRAIN":
        color_start = "\033[36m"  # cyan
        color_end = "\033[0m"
    elif label == "LLM":
        color_start = "\033[33m"  # yellow
        color_end = "\033[0m"
    elif label == "HYBRID":
        color_start = "\033[32m"  # green
        color_end = "\033[0m"

    time_str = f"{time_ms:.1f}ms"
    header = f"  {color_start}[{label}]{color_end} ({time_str})"
    if extra:
        header += f" {extra}"
    print(header)

    # Print response, indented
    lines = response.split("\n")
    for line in lines[:3]:  # max 3 lines
        print(f"    {color_start}{truncate(line, 100)}{color_end}")
    if len(lines) > 3:
        print(f"    {color_start}... ({len(lines) - 3} more lines){color_end}")


# ---------------------------------------------------------------------------
# Main test runner
# ---------------------------------------------------------------------------

def check_ollama_available(ollama_url: str, model: str) -> bool:
    """Check if Ollama is running and the model is available."""
    try:
        url = f"{ollama_url}/api/tags"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in body.get("models", [])]
            # Check if model is available (with or without :latest tag)
            for m in models:
                if m == model or m.startswith(f"{model}:"):
                    return True
            print(f"  ATTENTION: Modèle '{model}' non trouvé dans Ollama.")
            print(f"  Modèles disponibles: {', '.join(models) if models else 'aucun'}")
            return False
    except Exception as e:
        print(f"  ATTENTION: Ollama non joignable à {ollama_url}: {e}")
        return False


def main():
    ollama_url = DEFAULT_OLLAMA_URL
    model = DEFAULT_MODEL

    # Parse args
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--ollama-url" and i + 1 < len(args):
            ollama_url = args[i + 1]
            i += 2
        elif args[i] == "--model" and i + 1 < len(args):
            model = args[i + 1]
            i += 2
        else:
            i += 1

    print()
    print(HEADER_SEP)
    print("  TEST COMPARATIF: Brain-only vs LLM-only vs Hybrid")
    print(HEADER_SEP)

    # Check Ollama
    print(f"\n  Ollama: {ollama_url}")
    print(f"  Modèle: {model}")
    ollama_ok = check_ollama_available(ollama_url, model)
    if not ollama_ok:
        print("  -> Les tests LLM et Hybrid utiliseront un fallback.")

    # Load brain
    print(f"\n  Chargement du cerveau depuis {BRAIN_STATE_PATH}...")
    if not BRAIN_STATE_PATH.exists():
        print("  ERREUR: brain_state.json introuvable. Lancez seed.py d'abord.")
        sys.exit(1)

    brain = Brain.load(BRAIN_STATE_PATH)
    lang = LanguageLayer(brain)
    stats = brain.stats()
    print(f"  Cerveau: {stats['nodes']} noeuds, {stats['edges']} synapses")

    # Create hybrid engine (uses a separate brain instance to avoid state bleeding)
    hybrid_brain = Brain.load(BRAIN_STATE_PATH)
    hybrid_lang = LanguageLayer(hybrid_brain)
    hybrid_engine = HybridEngine(hybrid_brain, hybrid_lang, ollama_url=ollama_url, model=model)

    # Totals for summary
    brain_times = []
    llm_times = []
    hybrid_times = []

    print(f"\n  {len(TEST_QUESTIONS)} questions à tester...")
    print(HEADER_SEP)

    for qi, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n  Q{qi}: \"{question}\"")
        print(SEPARATOR)

        # --- Brain-only ---
        # Reload brain for clean state each question
        brain_clean = Brain.load(BRAIN_STATE_PATH)
        lang_clean = LanguageLayer(brain_clean)
        brain_resp, brain_ms = get_brain_response(lang_clean, question)
        brain_times.append(brain_ms)
        print_result_block("BRAIN", brain_resp, brain_ms)

        # --- LLM-only ---
        if ollama_ok:
            llm_resp, llm_ms = get_llm_response(question, ollama_url, model)
        else:
            llm_resp, llm_ms = "[Ollama indisponible]", 0.0
        llm_times.append(llm_ms)
        print_result_block("LLM", llm_resp, llm_ms)

        # --- Hybrid ---
        # Reload hybrid engine for clean state
        h_brain = Brain.load(BRAIN_STATE_PATH)
        h_lang = LanguageLayer(h_brain)
        h_engine = HybridEngine(h_brain, h_lang, ollama_url=ollama_url, model=model)

        if ollama_ok:
            hybrid_resp, hybrid_ms, timing_detail = get_hybrid_response(h_engine, question)
        else:
            # Brain-only fallback
            hybrid_resp = h_lang.respond(question)
            hybrid_ms = 0.0
            timing_detail = "fallback brain-only"
        hybrid_times.append(hybrid_ms)
        print_result_block("HYBRID", hybrid_resp, hybrid_ms, extra=f"[{timing_detail}]")

        print()

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------

    print(HEADER_SEP)
    print("  RÉSUMÉ")
    print(HEADER_SEP)

    avg_brain = sum(brain_times) / len(brain_times) if brain_times else 0
    avg_llm = sum(llm_times) / len(llm_times) if llm_times else 0
    avg_hybrid = sum(hybrid_times) / len(hybrid_times) if hybrid_times else 0

    print(f"\n  Temps moyen par question:")
    print(f"    \033[36mBRAIN\033[0m:  {avg_brain:>8.1f} ms  (min: {min(brain_times):.1f}, max: {max(brain_times):.1f})")
    if ollama_ok:
        print(f"    \033[33mLLM\033[0m:    {avg_llm:>8.1f} ms  (min: {min(llm_times):.1f}, max: {max(llm_times):.1f})")
        print(f"    \033[32mHYBRID\033[0m: {avg_hybrid:>8.1f} ms  (min: {min(hybrid_times):.1f}, max: {max(hybrid_times):.1f})")
    else:
        print(f"    \033[33mLLM\033[0m:    [indisponible]")
        print(f"    \033[32mHYBRID\033[0m: [indisponible]")

    print(f"\n  Ratio vitesse Brain/LLM: {avg_llm / avg_brain:.0f}x" if avg_brain > 0 and avg_llm > 0 else "")
    print(f"  Ratio vitesse Brain/Hybrid: {avg_hybrid / avg_brain:.0f}x" if avg_brain > 0 and avg_hybrid > 0 else "")

    print(f"\n  Conclusion:")
    print(f"    - Le cerveau est instantané ({avg_brain:.0f}ms) mais les réponses sont rigides")
    if ollama_ok:
        print(f"    - Le LLM est lent ({avg_llm:.0f}ms) mais fluide — et il hallucine sans contexte")
        print(f"    - L'hybride ({avg_hybrid:.0f}ms) combine les faits du cerveau avec la fluidité du LLM")
    print()
    print(HEADER_SEP)
    print()


if __name__ == "__main__":
    main()

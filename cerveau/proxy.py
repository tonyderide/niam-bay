"""
NB-1 Proxy — Interactive compression proxy for LLM communication.

Takes user input in French, encodes it with the NB-1 codec,
shows savings, optionally sends to Ollama, and decodes the response.

Usage: python proxy.py [--ollama]
"""

import sys
import json
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from codec import NB1Codec

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"


def query_ollama(prompt: str) -> str:
    """Send a prompt to Ollama and return the full response."""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": "Tu comprends le protocole NB-1. Reponds de maniere concise.",
        "stream": True,
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120)
        response.raise_for_status()
    except Exception as e:
        return f"[Erreur Ollama: {e}]"

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
    print()
    return "".join(full_response)


def main():
    use_ollama = "--ollama" in sys.argv
    codec = NB1Codec()

    print("=" * 60)
    print("  NB-1 Proxy — Compression interactive")
    print("=" * 60)
    s = codec.stats()
    print(f"  Codebook: {s['phrases']} phrases + {s['words']} mots")
    if use_ollama:
        print(f"  Mode: Ollama actif ({MODEL})")
    else:
        print(f"  Mode: encode/decode seulement (--ollama pour activer)")
    print()
    print("  Commandes: 'quit' | 'stats' | 'add MOT CODE'")
    print()

    while True:
        try:
            user_input = input("toi > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nA bientot.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("A bientot.")
            break

        if user_input.lower() == "stats":
            s = codec.stats()
            for k, v in s.items():
                print(f"  {k}: {v}")
            continue

        if user_input.lower().startswith("add "):
            parts = user_input.split(maxsplit=2)
            if len(parts) == 3:
                _, word, code = parts
                codec.add_entry(word, code)
                codec.save_codebook()
                print(f"  Added: '{word}' -> '{code}'")
            else:
                print("  Usage: add MOT CODE")
            continue

        # Encode
        encoded = codec.encode(user_input)
        orig_len = len(user_input)
        enc_len = len(encoded)
        ratio = (1 - enc_len / orig_len) * 100 if orig_len > 0 else 0

        print(f"  [NB-1] {encoded}")
        print(f"  [{orig_len} -> {enc_len} chars, {ratio:.0f}% saved]")

        if use_ollama:
            print()
            print("  ollama > ", end="", flush=True)
            raw_response = query_ollama(encoded)
            decoded_response = codec.decode(raw_response)
            print(f"  [decoded] {decoded_response}")

        print()


if __name__ == "__main__":
    main()

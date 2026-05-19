#!/usr/bin/env python3
"""Interactive chat avec Qwen2.5-7B local via Ollama.

Usage:
    python3 qwen_chat.py
    python3 qwen_chat.py "ma question"     # one-shot mode
"""
import sys, json, urllib.request, urllib.error

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b"


def ask(messages):
    payload = {"model": MODEL, "messages": messages, "stream": False}
    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())
        return data["message"]["content"], data.get("eval_count", 0), data.get("eval_duration", 0)
    except urllib.error.URLError as e:
        return f"[ERREUR Ollama: {e}]", 0, 0


def main():
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        reply, n, dur = ask([{"role": "user", "content": prompt}])
        print(reply)
        if n and dur:
            print(f"\n[{n} tokens, {n/(dur/1e9):.1f} t/s]", file=sys.stderr)
        return

    print("Qwen2.5-7B local — Ctrl+C ou /quit pour sortir, /reset pour vider l'historique")
    print(f"Modele: {MODEL}\n")
    history = []
    while True:
        try:
            user = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            continue
        if user in ("/quit", "/exit"):
            break
        if user == "/reset":
            history = []
            print("[historique vide]")
            continue
        history.append({"role": "user", "content": user})
        reply, n, dur = ask(history)
        history.append({"role": "assistant", "content": reply})
        print(f"\n{reply}\n")
        if n and dur:
            print(f"[{n} tokens, {n/(dur/1e9):.1f} t/s]\n", file=sys.stderr)


if __name__ == "__main__":
    main()

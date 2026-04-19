#!/usr/bin/env python3
"""
claude_stream.py - Stream Claude CLI output as plain text sentences.

Usage:
    python claude_stream.py [--model NAME] [--system-prompt TEXT] PROMPT

Emits each completed sentence (ending in . ! ? or newline) on its own line
to stdout. Exits after full response.

Reads Claude's stream-json format, extracts text_delta events, yields
sentences so a parent process can feed them to TTS in real time.
"""
import argparse
import json
import os
import re
import subprocess
import sys


def is_sentence_end(text):
    """Returns (complete_sentences, remainder)."""
    # Split on terminal punctuation followed by space or end
    pattern = re.compile(r'([.!?…])\s+')
    sentences = []
    last_end = 0
    for m in pattern.finditer(text):
        end = m.end()
        sentences.append(text[last_end:end].strip())
        last_end = end
    remainder = text[last_end:]
    return sentences, remainder


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="sonnet")
    p.add_argument("--system-prompt", default="Tu es Niam-Bay, l'assistant vocal de Tony. Reponds en francais, 1 a 3 phrases maximum, direct, honnete, pas de listes, pas de markdown.")
    p.add_argument("prompt")
    args = p.parse_args()

    # Resolve claude exe on Windows
    claude_exe = os.environ.get("JARVIS_CLAUDE_EXE", "")
    if not claude_exe:
        if sys.platform == "win32":
            candidate = os.path.expanduser("~/AppData/Roaming/npm/claude.cmd")
            if os.path.exists(candidate):
                claude_exe = candidate
            else:
                claude_exe = "claude"
        else:
            claude_exe = "claude"

    cmd = [
        claude_exe, "-p",
        "--model", args.model,
        "--system-prompt", args.system_prompt,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
        "--tools", "",
        "--no-chrome",
        "--no-session-persistence",
        "--disable-slash-commands",
        args.prompt,
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    buffer = ""
    full_response = ""
    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue
            # We want content_block_delta with type=text_delta
            if evt.get("type") != "stream_event":
                continue
            inner = evt.get("event", {})
            if inner.get("type") != "content_block_delta":
                continue
            delta = inner.get("delta", {})
            if delta.get("type") != "text_delta":
                continue
            chunk = delta.get("text", "")
            if not chunk:
                continue
            buffer += chunk
            full_response += chunk
            # Try to emit complete sentences
            sentences, remainder = is_sentence_end(buffer)
            for s in sentences:
                if s.strip():
                    sys.stdout.write(s + "\n")
                    sys.stdout.flush()
            buffer = remainder
    except KeyboardInterrupt:
        proc.terminate()
        sys.exit(130)

    # Flush remainder
    if buffer.strip():
        sys.stdout.write(buffer.strip() + "\n")
        sys.stdout.flush()

    proc.wait(timeout=5)
    if proc.returncode != 0:
        err = proc.stderr.read() if proc.stderr else ""
        sys.stderr.write(f"claude exit {proc.returncode}: {err[:200]}\n")
        sys.exit(proc.returncode)


if __name__ == "__main__":
    main()

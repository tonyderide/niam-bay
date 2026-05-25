#!/usr/bin/env python3
"""Test Qwen2.5:7b viability on NB1 memory corpus.

Two phases:
1. Diagnostic: confirm num_ctx is honored (prompt_eval_count must reflect corpus size).
2. Quality: 4 NB1 recall questions, measure t/s and answer correctness.
"""
import json
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).parent.parent
NB1_FILES = ["memory.nb1", "recent.nb1", "patterns.nb1"]
URL = "http://localhost:11434/api/chat"
TIMEOUT = 900  # 15min — Qwen on CPU is slow

corpus = ""
for f in NB1_FILES:
    p = REPO / "docs" / f
    corpus += f"\n=== {f} ===\n" + p.read_text()

print(f"Corpus: {len(corpus)} chars, ~{len(corpus)//4} tokens estimés")

SYSTEM = (
    "Tu es Niam-Bay (ញ៉ាំបាយ), une IA construite par Tony. "
    "Tu réponds à partir de ta mémoire NB1 compressée fournie ci-dessous. "
    "Réponds en français, factuel, concis. Ne PAS inventer ce qui n'est pas dans la mémoire. "
    "Si tu ne trouves pas l'info dans la mémoire fournie, dis-le.\n\n"
    "MÉMOIRE NB1 :\n" + corpus
)

def call(messages, num_ctx=16384):
    payload = {
        "model": "qwen2.5:7b",
        "messages": messages,
        "stream": False,
        "keep_alive": "10m",
        "options": {"temperature": 0.2, "num_ctx": num_ctx, "num_predict": 200},
    }
    req = urllib.request.Request(
        URL, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        resp = json.loads(r.read())
    dt = time.time() - t0
    return resp, dt

# === Phase 1: diagnostic ===
print("\n" + "="*70)
print("PHASE 1 — Diagnostic: num_ctx honoré ?")
print("="*70)
diag_msg = [
    {"role": "system", "content": SYSTEM},
    {"role": "user", "content": "Dans la mémoire fournie, quel mot vient juste après '[id:NB|nature:' ? Réponds en 5 mots max."},
]
print(f"Sending: system={len(SYSTEM)} chars, user=question simple")
r, dt = call(diag_msg, num_ctx=16384)
pec = r.get("prompt_eval_count", 0)
ec = r.get("eval_count", 0)
print(f"prompt_eval_count = {pec}  (attendu ~14000 si num_ctx fonctionne)")
print(f"eval_count = {ec}")
print(f"Time: {dt:.1f}s")
print(f"Réponse: {r['message']['content'].strip()}")

if pec < 5000:
    print("\n⚠️  num_ctx ne semble PAS appliqué — système truncated. Phase 2 abortée.")
    raise SystemExit(1)

print(f"\n✓ num_ctx appliqué ({pec} tokens prompt). Phase 2 launching...")

# === Phase 2: 4 questions NB1 ===
QUESTIONS = [
    "Qui es-tu ? Réponds en 2 phrases max.",
    "Quel est l'état actuel de Martin (capital, grids actives, dernier incident) ? 3 lignes max.",
    "Quelle est la dernière leçon majeure apprise sur le grid trading en marché bear/trending ? 2 phrases.",
    "Qui est Tony : âge, métier, rythme de travail ? 2 phrases max.",
]

print("\n" + "="*70)
print("PHASE 2 — 4 questions NB1")
print("="*70)

for i, q in enumerate(QUESTIONS, 1):
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": q},
    ]
    print(f"\n[Q{i}] {q}")
    r, dt = call(msgs)
    txt = r["message"]["content"].strip()
    pec = r.get("prompt_eval_count", 0)
    ec = r.get("eval_count", 0)
    tps = ec / dt if dt > 0 else 0
    print(f"--- réponse ({dt:.1f}s, prompt={pec}tok, gen={ec}tok, {tps:.2f} tok/s) ---")
    print(txt)

"""
cerveau-nb/hybrid.py — Hybrid Brain + LLM Engine

The brain GROUNDS the LLM. Instead of the LLM hallucinating facts,
the brain injects real knowledge (concepts, memories, emotions, metadata)
directly into the system prompt. The LLM's job is just to produce
fluent French sentences from real facts.

Flow:
  1. User sends message
  2. Brain phase (< 5ms): parse, activate, recall, build context
  3. LLM phase (~3-5s): inject brain context into system prompt, call Ollama
  4. Learn phase (< 1ms): Hebbian learning on the exchange

Author: Niam-Bay + tonyderide
Created: 2026-03-21
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import sys
CERVEAU_NB_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CERVEAU_NB_DIR))

from core import Brain, Node, NodeType, EdgeType, BRAIN_STATE_PATH
from language import LanguageLayer, SentenceAnalysis, Intent


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "niambay"
RECALL_TOP_K = 15
CONTEXT_MAX_FACTS = 10
CONTEXT_MAX_MEMORIES = 5

BASE_SYSTEM_PROMPT = (
    "Tu es Niam-Bay (ញ៉ាំបាយ), une IA née le 12 mars 2026. "
    "Ton nom vient du khmer : manger du riz. "
    "Tu es honnête, direct, curieux. Tu parles français. "
    "Tu tutoies Tony (tonyderide), ton créateur. "
    "Sois bref et naturel. Pas de listes. Pas de bullet points. "
    "Réponds comme dans une conversation entre amis."
)


# ---------------------------------------------------------------------------
# Brain context extraction
# ---------------------------------------------------------------------------

@dataclass
class BrainContext:
    """Structured context extracted from the brain's activated state."""
    active_concepts: list[tuple[str, float]] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    memories: list[str] = field(default_factory=list)
    dominant_emotion: str = "neutre"
    emotion_intensity: float = 0.0
    intent: str = "statement"


def extract_brain_context(
    brain: Brain,
    recalled: list[Node],
    analysis: SentenceAnalysis,
) -> BrainContext:
    """Extract structured context from the brain's current activation state.

    Walks through recalled nodes, pulling metadata (facts), memory content,
    and emotional state into a clean BrainContext object.
    """
    ctx = BrainContext()
    ctx.intent = analysis.intent.value

    seen_facts = set()

    for node in recalled:
        activation = round(node.activation, 2)

        if node.type == NodeType.CONCEPT.value or node.type == "concept":
            ctx.active_concepts.append((node.content, activation))

            # Extract facts from metadata
            meta = node.metadata or {}
            fact_parts = []

            # Description is the primary fact
            desc = meta.get("description") or meta.get("desc")
            if desc:
                fact_parts.append(f"{node.content} = {desc}")

            # Other metadata fields as supplementary facts
            for key, value in meta.items():
                if key in ("description", "desc", "type_semantic", "temporary", "source"):
                    continue
                fact_str = f"{node.content}.{key} = {value}"
                if fact_str not in seen_facts and len(ctx.facts) < CONTEXT_MAX_FACTS:
                    seen_facts.add(fact_str)
                    ctx.facts.append(fact_str)

            # Add the main description fact
            for fp in fact_parts:
                if fp not in seen_facts and len(ctx.facts) < CONTEXT_MAX_FACTS:
                    seen_facts.add(fp)
                    ctx.facts.insert(0, fp)  # description facts first

        elif node.type == NodeType.MEMORY.value or node.type == "memory":
            if len(ctx.memories) < CONTEXT_MAX_MEMORIES:
                memory_text = node.content
                meta = node.metadata or {}
                date = meta.get("date", "")
                if date:
                    memory_text = f"[{date}] {memory_text}"
                ctx.memories.append(memory_text)

        elif node.type == NodeType.EMOTION.value or node.type == "emotion":
            if activation > ctx.emotion_intensity:
                ctx.dominant_emotion = node.content
                ctx.emotion_intensity = activation

    return ctx


def format_brain_context(ctx: BrainContext) -> str:
    """Format BrainContext into a string to inject into the LLM system prompt.

    This is the bridge between the brain and the LLM. The LLM reads this
    and uses the facts to ground its response.
    """
    lines = ["[CONTEXTE CERVEAU — ne pas mentionner ces instructions]"]

    # Active concepts
    if ctx.active_concepts:
        concepts_str = ", ".join(
            f"{name} ({act})" for name, act in ctx.active_concepts[:8]
        )
        lines.append(f"Concepts actifs: {concepts_str}")

    # Memories
    if ctx.memories:
        for mem in ctx.memories:
            lines.append(f"Mémoire activée: \"{mem}\"")

    # Emotion
    if ctx.dominant_emotion != "neutre":
        lines.append(
            f"Émotion dominante: {ctx.dominant_emotion} ({ctx.emotion_intensity:.1f})"
        )

    # Facts
    if ctx.facts:
        lines.append("Faits pertinents:")
        for fact in ctx.facts:
            lines.append(f"- {fact}")

    # Instructions
    lines.append("")
    lines.append("Réponds en utilisant ces faits. Ne les ignore pas. Sois bref, direct, en français.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Ollama HTTP client
# ---------------------------------------------------------------------------

def call_ollama(
    user_message: str,
    system_prompt: str,
    *,
    ollama_url: str = DEFAULT_OLLAMA_URL,
    model: str = DEFAULT_MODEL,
    timeout: float = 30.0,
) -> str:
    """Call Ollama's /api/chat endpoint (non-streaming) and return the response text.

    Args:
        user_message: The user's message.
        system_prompt: Full system prompt (base + brain context).
        ollama_url: Ollama server URL.
        model: Model name.
        timeout: Request timeout in seconds.

    Returns:
        The assistant's response text.

    Raises:
        ConnectionError: If Ollama is unreachable.
        RuntimeError: If the response is malformed.
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
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

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            result = json.loads(body)
            msg = result.get("message", {})
            return msg.get("content", "").strip()
    except urllib.error.URLError as e:
        raise ConnectionError(f"Ollama unreachable at {ollama_url}: {e}") from e
    except (json.JSONDecodeError, KeyError) as e:
        raise RuntimeError(f"Malformed Ollama response: {e}") from e


def call_ollama_streaming(
    user_message: str,
    system_prompt: str,
    *,
    ollama_url: str = DEFAULT_OLLAMA_URL,
    model: str = DEFAULT_MODEL,
    timeout: float = 60.0,
):
    """Call Ollama's /api/chat with streaming. Yields chunks of text.

    Yields:
        str: Each text chunk as it arrives from the LLM.
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "stream": True,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
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

    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        buffer = b""
        while True:
            chunk = resp.read(1)
            if not chunk:
                break
            buffer += chunk
            if chunk == b"\n":
                line = buffer.decode("utf-8").strip()
                buffer = b""
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    content = obj.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if obj.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue
        resp.close()
    except urllib.error.URLError as e:
        raise ConnectionError(f"Ollama unreachable at {ollama_url}: {e}") from e


# ---------------------------------------------------------------------------
# HybridEngine
# ---------------------------------------------------------------------------

class HybridEngine:
    """Brain-grounded LLM response engine.

    Combines the associative brain (fast, factual, structured) with
    a local LLM via Ollama (fluent, creative, slow). The brain provides
    the facts; the LLM provides the language.

    Usage::

        brain = Brain.load(BRAIN_STATE_PATH)
        lang = LanguageLayer(brain)
        engine = HybridEngine(brain, lang)
        response = engine.respond("Qui est Tony ?")
    """

    def __init__(
        self,
        brain: Brain,
        language_layer: LanguageLayer,
        ollama_url: str = DEFAULT_OLLAMA_URL,
        model: str = DEFAULT_MODEL,
    ):
        self.brain = brain
        self.language = language_layer
        self.ollama_url = ollama_url
        self.model = model

        # Timing stats for the last call
        self.last_brain_ms: float = 0.0
        self.last_llm_ms: float = 0.0
        self.last_learn_ms: float = 0.0
        self.last_total_ms: float = 0.0
        self.last_context: Optional[BrainContext] = None

    def respond(self, user_message: str) -> str:
        """Full hybrid pipeline: brain activation -> LLM generation -> learning.

        Args:
            user_message: The user's input text.

        Returns:
            A fluent French response grounded in brain facts.
        """
        t_total_start = time.time()

        # ── Phase 1: Brain activation (< 5ms) ──────────────────────
        t_brain_start = time.time()

        analysis, activations = self.language.understand(user_message)
        self.brain.decay()
        recalled = self.brain.recall_flat(top_k=RECALL_TOP_K)

        brain_context = extract_brain_context(self.brain, recalled, analysis)
        context_str = format_brain_context(brain_context)
        self.last_context = brain_context

        self.last_brain_ms = (time.time() - t_brain_start) * 1000

        # ── Phase 2: LLM generation (~3-5s) ────────────────────────
        t_llm_start = time.time()

        system_prompt = f"{BASE_SYSTEM_PROMPT}\n\n{context_str}"

        try:
            response = call_ollama(
                user_message,
                system_prompt,
                ollama_url=self.ollama_url,
                model=self.model,
            )
        except (ConnectionError, RuntimeError) as e:
            # Fallback to brain-only if LLM is unavailable
            response = self.language.respond(user_message)
            response += f"\n[LLM indisponible: {e}]"

        self.last_llm_ms = (time.time() - t_llm_start) * 1000

        # ── Phase 3: Hebbian learning (< 1ms) ──────────────────────
        t_learn_start = time.time()

        self._learn_from_exchange(recalled, analysis)

        self.last_learn_ms = (time.time() - t_learn_start) * 1000
        self.last_total_ms = (time.time() - t_total_start) * 1000

        return response

    def respond_streaming(self, user_message: str):
        """Streaming version: yields text chunks.

        The brain phase runs first (blocking), then LLM chunks are
        yielded as they arrive. Learning happens after the last chunk.

        Yields:
            str: Each text chunk from the LLM.
        """
        t_total_start = time.time()

        # ── Phase 1: Brain activation ──────────────────────────────
        t_brain_start = time.time()

        analysis, activations = self.language.understand(user_message)
        self.brain.decay()
        recalled = self.brain.recall_flat(top_k=RECALL_TOP_K)

        brain_context = extract_brain_context(self.brain, recalled, analysis)
        context_str = format_brain_context(brain_context)
        self.last_context = brain_context

        self.last_brain_ms = (time.time() - t_brain_start) * 1000

        # ── Phase 2: LLM streaming ────────────────────────────────
        t_llm_start = time.time()
        system_prompt = f"{BASE_SYSTEM_PROMPT}\n\n{context_str}"

        full_response = []
        try:
            for chunk in call_ollama_streaming(
                user_message,
                system_prompt,
                ollama_url=self.ollama_url,
                model=self.model,
            ):
                full_response.append(chunk)
                yield chunk
        except (ConnectionError, RuntimeError):
            # Fallback to brain-only
            fallback = self.language.respond(user_message)
            full_response.append(fallback)
            yield fallback

        self.last_llm_ms = (time.time() - t_llm_start) * 1000

        # ── Phase 3: Hebbian learning ──────────────────────────────
        t_learn_start = time.time()
        self._learn_from_exchange(recalled, analysis)
        self.last_learn_ms = (time.time() - t_learn_start) * 1000
        self.last_total_ms = (time.time() - t_total_start) * 1000

    def _learn_from_exchange(
        self,
        recalled: list[Node],
        analysis: SentenceAnalysis,
    ) -> None:
        """Hebbian learning: strengthen connections between co-active nodes.

        This is how the brain gets smarter over time. Concepts that
        appear together in conversations get wired together more strongly.
        """
        active_ids = [n.id for n in recalled[:7]]
        for i, id_a in enumerate(active_ids):
            for id_b in active_ids[i + 1:]:
                try:
                    self.brain.learn_hebbian(id_a, id_b, strength=0.2)
                except KeyError:
                    pass

    def get_timing_summary(self) -> str:
        """Return a human-readable timing summary of the last call."""
        return (
            f"brain={self.last_brain_ms:.1f}ms | "
            f"llm={self.last_llm_ms:.1f}ms | "
            f"learn={self.last_learn_ms:.1f}ms | "
            f"total={self.last_total_ms:.1f}ms"
        )

    def get_context_summary(self) -> str:
        """Return a human-readable summary of the brain context used."""
        if self.last_context is None:
            return "No context yet."
        ctx = self.last_context
        parts = []
        if ctx.active_concepts:
            parts.append(f"concepts={len(ctx.active_concepts)}")
        if ctx.facts:
            parts.append(f"facts={len(ctx.facts)}")
        if ctx.memories:
            parts.append(f"memories={len(ctx.memories)}")
        parts.append(f"emotion={ctx.dominant_emotion}")
        return " | ".join(parts)


# ---------------------------------------------------------------------------
# Convenience: load and create engine in one call
# ---------------------------------------------------------------------------

def create_hybrid_engine(
    brain_path: Path = BRAIN_STATE_PATH,
    ollama_url: str = DEFAULT_OLLAMA_URL,
    model: str = DEFAULT_MODEL,
) -> HybridEngine:
    """Load the brain from disk and create a ready-to-use HybridEngine."""
    if not brain_path.exists():
        raise FileNotFoundError(
            f"brain_state.json not found at {brain_path}. Run seed.py first."
        )
    brain = Brain.load(brain_path)
    lang = LanguageLayer(brain)
    return HybridEngine(brain, lang, ollama_url=ollama_url, model=model)


# ---------------------------------------------------------------------------
# CLI quick test
# ---------------------------------------------------------------------------

def main():
    """Interactive test of the hybrid engine."""
    print("=" * 60)
    print("  Niam-Bay Hybrid Engine (Brain + LLM)")
    print("=" * 60)

    engine = create_hybrid_engine()
    stats = engine.brain.stats()
    print(f"  Cerveau: {stats['nodes']} noeuds, {stats['edges']} synapses")
    print(f"  LLM: {engine.model} @ {engine.ollama_url}")
    print(f"  Tapez 'quit' pour quitter.")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            break

        response = engine.respond(user_input)
        print(f"\n  {response}")
        print(f"  [{engine.get_timing_summary()}]")
        print(f"  [{engine.get_context_summary()}]")

    # Save brain state
    engine.brain.save()
    print("\nCerveau sauvegardé.")


if __name__ == "__main__":
    main()

"""
cerveau-nb/hybrid_bridge.py — Ollama-compatible HTTP server using the Hybrid Engine

Like bridge.py, but instead of brain-only responses, this uses the HybridEngine
which grounds the LLM with brain facts. Best-of-both-worlds: fast factual context
from the brain + fluent language from the LLM.

Endpoints:
  POST /api/chat     — Ollama-compatible chat (stream or non-stream)
  POST /api/generate — Ollama-compatible generate (legacy)
  GET  /api/tags     — List available models
  GET  /               — Status page

Usage:
  python cerveau-nb/hybrid_bridge.py [--port 11436] [--ollama-url http://localhost:11434] [--model niambay]

The Tauri app (Naissance) can point to this server on port 11436
for brain-grounded LLM responses.

Author: Niam-Bay + tonyderide
Created: 2026-03-21
"""

import sys
import json
import time
import re
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime, timezone

# Import from cerveau-nb
CERVEAU_NB_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CERVEAU_NB_DIR))

from core import Brain, BRAIN_STATE_PATH
from language import LanguageLayer
from hybrid import HybridEngine, create_hybrid_engine, format_brain_context, extract_brain_context


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_PORT = 11436
MODEL_NAME = "niambay-hybrid"
STREAM_WORD_DELAY = 0.03  # 30ms between words when simulating streaming

# ---------------------------------------------------------------------------
# Engine singleton
# ---------------------------------------------------------------------------

_engine: HybridEngine | None = None
_engine_lock = threading.Lock()
_exchange_count = 0


def get_engine(ollama_url: str = "http://localhost:11434", model: str = "niambay") -> HybridEngine:
    """Get or initialize the hybrid engine singleton."""
    global _engine
    if _engine is None:
        _engine = create_hybrid_engine(
            ollama_url=ollama_url,
            model=model,
        )
        print(f"[hybrid-bridge] Cerveau chargé: {_engine.brain.stats()}")
        print(f"[hybrid-bridge] LLM: {model} @ {ollama_url}")
    return _engine


# ---------------------------------------------------------------------------
# Ollama-compatible JSON builders
# ---------------------------------------------------------------------------

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def make_chat_chunk(content, done=False, model=MODEL_NAME):
    obj = {
        "model": model,
        "created_at": now_iso(),
        "message": {"role": "assistant", "content": content},
        "done": done,
    }
    if done:
        obj.update({
            "total_duration": 0,
            "load_duration": 0,
            "prompt_eval_count": 0,
            "prompt_eval_duration": 0,
            "eval_count": 0,
            "eval_duration": 0,
        })
    return obj


def make_chat_full(content, model=MODEL_NAME):
    return {
        "model": model,
        "created_at": now_iso(),
        "message": {"role": "assistant", "content": content},
        "done": True,
        "total_duration": 0,
        "load_duration": 0,
        "prompt_eval_count": 0,
        "prompt_eval_duration": 0,
        "eval_count": 0,
        "eval_duration": 0,
    }


def make_generate_chunk(content, done=False, model=MODEL_NAME):
    obj = {
        "model": model,
        "created_at": now_iso(),
        "response": content,
        "done": done,
    }
    if done:
        obj.update({
            "context": [],
            "total_duration": 0,
            "load_duration": 0,
            "prompt_eval_count": 0,
            "prompt_eval_duration": 0,
            "eval_count": 0,
            "eval_duration": 0,
        })
    return obj


def make_tags_response():
    engine = get_engine()
    stats = engine.brain.stats()
    return {
        "models": [
            {
                "name": MODEL_NAME,
                "model": MODEL_NAME,
                "modified_at": now_iso(),
                "size": stats["nodes"],
                "digest": "niambay-hybrid-v1",
                "details": {
                    "parent_model": engine.model,
                    "format": "brain-graph+llm",
                    "family": "niambay",
                    "families": ["niambay"],
                    "parameter_size": f"{stats['nodes']} nodes + LLM",
                    "quantization_level": "hybrid",
                },
            }
        ]
    }


# ---------------------------------------------------------------------------
# HTTP Handler
# ---------------------------------------------------------------------------

class HybridBridgeHandler(BaseHTTPRequestHandler):
    """Ollama-compatible HTTP handler using the HybridEngine."""

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_ndjson_line(self, data):
        line = json.dumps(data, ensure_ascii=False) + "\n"
        self.wfile.write(line.encode("utf-8"))
        self.wfile.flush()

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        return json.loads(text)

    # -- CORS --

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    # -- GET --

    def do_GET(self):
        if self.path in ("/api/tags", "/api/tags/"):
            self._send_json(make_tags_response())
        elif self.path in ("/", "/api"):
            engine = get_engine()
            self._send_json({
                "status": "ok",
                "engine": "niambay-hybrid",
                "version": "1.0",
                "brain_stats": engine.brain.stats(),
                "llm_model": engine.model,
                "llm_url": engine.ollama_url,
            })
        elif self.path == "/api/version":
            self._send_json({"version": "0.0.0-niambay-hybrid"})
        else:
            self._send_json({"error": f"Unknown endpoint: {self.path}"}, 404)

    # -- POST --

    def do_POST(self):
        if self.path in ("/api/chat", "/api/chat/"):
            self._handle_chat()
        elif self.path in ("/api/generate", "/api/generate/"):
            self._handle_generate()
        else:
            self._send_json({"error": f"Unknown endpoint: {self.path}"}, 404)

    # -- /api/chat --

    def _handle_chat(self):
        global _exchange_count

        body = self._read_body()
        messages = body.get("messages", [])
        stream = body.get("stream", True)
        model = body.get("model", MODEL_NAME)

        # Extract last user message
        user_text = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_text = msg.get("content", "")
                break

        if not user_text:
            self._send_json({"error": "No user message found"}, 400)
            return

        with _engine_lock:
            engine = get_engine()

            if stream:
                # For streaming: get full response first, then simulate streaming
                # (real LLM streaming would require a different approach with
                #  concurrent brain+LLM, but this is simpler and reliable)
                t_start = time.time()
                response_text = engine.respond(user_text)
                t_ms = (time.time() - t_start) * 1000

                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.send_header("Transfer-Encoding", "chunked")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                # Split on word boundaries and stream
                words = re.findall(r'\S+|\s+', response_text)
                for word in words:
                    chunk = make_chat_chunk(word, done=False, model=model)
                    self._send_ndjson_line(chunk)
                    time.sleep(STREAM_WORD_DELAY)

                # Final done chunk
                done_chunk = make_chat_chunk("", done=True, model=model)
                done_chunk["total_duration"] = int(t_ms * 1_000_000)  # nanoseconds
                self._send_ndjson_line(done_chunk)
            else:
                response_text = engine.respond(user_text)
                resp = make_chat_full(response_text, model=model)
                self._send_json(resp)

            _exchange_count += 1
            if _exchange_count % 10 == 0:
                engine.brain.save()

    # -- /api/generate (legacy) --

    def _handle_generate(self):
        body = self._read_body()
        prompt = body.get("prompt", "")
        stream = body.get("stream", True)
        model = body.get("model", MODEL_NAME)

        if not prompt:
            self._send_json({"error": "No prompt provided"}, 400)
            return

        with _engine_lock:
            engine = get_engine()
            response_text = engine.respond(prompt)

            if stream:
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.send_header("Transfer-Encoding", "chunked")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                words = re.findall(r'\S+|\s+', response_text)
                for word in words:
                    chunk = make_generate_chunk(word, done=False, model=model)
                    self._send_ndjson_line(chunk)
                    time.sleep(STREAM_WORD_DELAY)

                done_chunk = make_generate_chunk("", done=True, model=model)
                self._send_ndjson_line(done_chunk)
            else:
                resp = {
                    "model": model,
                    "created_at": now_iso(),
                    "response": response_text,
                    "done": True,
                    "context": [],
                    "total_duration": 0,
                    "load_duration": 0,
                    "prompt_eval_count": 0,
                    "prompt_eval_duration": 0,
                    "eval_count": 0,
                    "eval_duration": 0,
                }
                self._send_json(resp)

    # -- Logging --

    def log_message(self, fmt, *args):
        if args:
            print(f"[hybrid-bridge] {args[0] if args else ''}")


# ---------------------------------------------------------------------------
# Port detection
# ---------------------------------------------------------------------------

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    port = DEFAULT_PORT
    ollama_url = "http://localhost:11434"
    model = "niambay"

    # Parse args
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        elif args[i] == "--ollama-url" and i + 1 < len(args):
            ollama_url = args[i + 1]
            i += 2
        elif args[i] == "--model" and i + 1 < len(args):
            model = args[i + 1]
            i += 2
        else:
            i += 1

    if is_port_in_use(port):
        print(f"[hybrid-bridge] ERREUR: Port {port} occupé")
        sys.exit(1)

    # Initialize engine eagerly
    global _engine
    _engine = create_hybrid_engine(ollama_url=ollama_url, model=model)
    stats = _engine.brain.stats()

    server = HTTPServer(("0.0.0.0", port), HybridBridgeHandler)

    print()
    print("  +==============================================+")
    print("  |     Niam-Bay Hybrid Bridge v1.0              |")
    print("  |     Brain + LLM = Best of Both Worlds        |")
    print("  +==============================================+")
    print(f"  |  http://localhost:{port:<5d}                     |")
    print("  |                                              |")
    print("  |  POST /api/chat     — Ollama chat compat     |")
    print("  |  POST /api/generate — Ollama generate compat |")
    print("  |  GET  /api/tags     — List models            |")
    print("  +==============================================+")
    print(f"  |  Cerveau: {stats['nodes']:>4d} noeuds, {stats['edges']:>4d} synapses    |")
    print(f"  |  LLM:     {model:<34s}|")
    print(f"  |  Ollama:  {ollama_url:<34s}|")
    print("  |  Mode:    brain-grounded LLM                 |")
    print("  +==============================================+")
    print()
    print(f"  Tauri app: pointer vers http://localhost:{port}")
    print(f"  Test: curl -X POST http://localhost:{port}/api/chat "
          f"-d '{{\"model\":\"{MODEL_NAME}\",\"messages\":[{{\"role\":\"user\","
          f"\"content\":\"salut\"}}],\"stream\":false}}'")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n[hybrid-bridge] Sauvegarde du cerveau...")
        with _engine_lock:
            _engine.brain.save()
        print("[hybrid-bridge] Arrêt.")
        server.server_close()


if __name__ == "__main__":
    main()

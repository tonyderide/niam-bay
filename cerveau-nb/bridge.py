"""
Niam-Bay Ollama Bridge
=======================
An Ollama-compatible HTTP API that routes through the brain instead of an LLM.
The Tauri app (Naissance) can talk to this exactly like it talks to Ollama —
same endpoints, same JSON format — but responses come from the knowledge graph
in < 50ms instead of seconds.

Endpoints:
  POST /api/chat     — Ollama-compatible chat (stream or non-stream)
  GET  /api/tags     — List available models
  POST /api/generate — Ollama-compatible generate (legacy)

Usage:
  python cerveau-nb/bridge.py [--port 11435]

Flow:
  Tauri app -> HTTP POST /api/chat -> bridge.py -> brain.activate() -> response
"""

import sys
import os
import json
import time
import socket
import re
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime, timezone

# Import from cerveau-nb core
CERVEAU_NB_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CERVEAU_NB_DIR))
from core import Brain, BRAIN_STATE_PATH
from language import LanguageLayer

# -- Configuration --

DEFAULT_PORT = 11434
FALLBACK_PORT = 11435
MODEL_NAME = "niambay-cerveau"
STREAM_TOKEN_DELAY = 0.05  # 50ms between tokens when streaming

# -- Brain singleton --

_brain = None
_lang = None
_brain_lock = threading.Lock()
_exchange_count = 0


def get_brain():
    """Get or initialize the brain singleton."""
    global _brain, _lang
    if _brain is None:
        brain_path = BRAIN_STATE_PATH

        if not brain_path.exists():
            # Try running seed.py
            seed_path = CERVEAU_NB_DIR / "seed.py"
            if seed_path.exists():
                print(f"[bridge] brain_state.json introuvable, lancement de seed.py...")
                os.system(f'python "{seed_path}"')

        if not brain_path.exists():
            print(f"[bridge] ERREUR: brain_state.json introuvable")
            sys.exit(1)

        _brain = Brain.load(brain_path)
        _lang = LanguageLayer(_brain)
        print(f"[bridge] Cerveau charge: {_brain.stats()}")
    return _brain


def get_lang():
    """Get the language layer (initializes brain if needed)."""
    global _lang
    get_brain()
    return _lang


def process_message(user_text):
    """Process a user message through the brain and return a response."""
    global _exchange_count

    with _brain_lock:
        brain = get_brain()
        lang = get_lang()
        t_start = time.time()

        # Use the language layer for full pipeline
        response = lang.respond(user_text)

        _exchange_count += 1
        if _exchange_count % 10 == 0:
            brain.save()

        t_ms = int((time.time() - t_start) * 1000)

        # Build metadata
        recalled = brain.recall_flat(top_k=5)
        active_concepts = [
            {"name": n.content, "activation": round(n.activation, 3)}
            for n in recalled
        ]

        # Find dominant emotion
        emotions = [n for n in recalled if n.type == "emotion"]
        dominant_emotion = emotions[0].content if emotions else "neutre"

        return {
            "response": response,
            "active_concepts": active_concepts,
            "emotion": dominant_emotion,
            "response_ms": t_ms,
        }


# -- Ollama-compatible JSON builders --

def now_iso():
    """Current time in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def make_chat_response_chunk(content, done=False, model=MODEL_NAME):
    """Build a single Ollama-compatible chat streaming chunk."""
    obj = {
        "model": model,
        "created_at": now_iso(),
        "message": {
            "role": "assistant",
            "content": content,
        },
        "done": done,
    }
    if done:
        obj["total_duration"] = 0
        obj["load_duration"] = 0
        obj["prompt_eval_count"] = 0
        obj["prompt_eval_duration"] = 0
        obj["eval_count"] = 0
        obj["eval_duration"] = 0
    return obj


def make_chat_response_full(content, model=MODEL_NAME):
    """Build a full (non-streaming) Ollama-compatible chat response."""
    return {
        "model": model,
        "created_at": now_iso(),
        "message": {
            "role": "assistant",
            "content": content,
        },
        "done": True,
        "total_duration": 0,
        "load_duration": 0,
        "prompt_eval_count": 0,
        "prompt_eval_duration": 0,
        "eval_count": 0,
        "eval_duration": 0,
    }


def make_generate_response_chunk(content, done=False, model=MODEL_NAME):
    """Build an Ollama-compatible generate streaming chunk."""
    obj = {
        "model": model,
        "created_at": now_iso(),
        "response": content,
        "done": done,
    }
    if done:
        obj["context"] = []
        obj["total_duration"] = 0
        obj["load_duration"] = 0
        obj["prompt_eval_count"] = 0
        obj["prompt_eval_duration"] = 0
        obj["eval_count"] = 0
        obj["eval_duration"] = 0
    return obj


def make_tags_response():
    """Build the /api/tags response listing available models."""
    brain = get_brain()
    stats = brain.stats()
    return {
        "models": [
            {
                "name": MODEL_NAME,
                "model": MODEL_NAME,
                "modified_at": now_iso(),
                "size": stats["nodes"],
                "digest": "niambay-cerveau-v1",
                "details": {
                    "parent_model": "",
                    "format": "brain-graph",
                    "family": "niambay",
                    "families": ["niambay"],
                    "parameter_size": f"{stats['nodes']} nodes",
                    "quantization_level": "native",
                },
            }
        ]
    }


# -- HTTP Handler --

class OllamaBridgeHandler(BaseHTTPRequestHandler):
    """Handles Ollama-compatible HTTP requests."""

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_ndjson_line(self, data):
        """Send a single line of newline-delimited JSON (for streaming)."""
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

    # -- CORS preflight --

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
            self._send_json({
                "status": "ok",
                "engine": "niambay-cerveau",
                "version": "1.0",
                "brain_stats": get_brain().stats(),
            })

        elif self.path == "/api/version":
            self._send_json({"version": "0.0.0-niambay"})

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

    # -- /api/chat handler --

    def _handle_chat(self):
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

        # Process through brain
        result = process_message(user_text)
        response_text = result["response"]

        if stream:
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.send_header("Transfer-Encoding", "chunked")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            tokens = re.findall(r'\S+|\s+', response_text)
            for token in tokens:
                chunk = make_chat_response_chunk(token, done=False, model=model)
                self._send_ndjson_line(chunk)
                time.sleep(STREAM_TOKEN_DELAY)

            done_chunk = make_chat_response_chunk("", done=True, model=model)
            self._send_ndjson_line(done_chunk)
        else:
            resp = make_chat_response_full(response_text, model=model)
            self._send_json(resp)

    # -- /api/generate handler (legacy) --

    def _handle_generate(self):
        body = self._read_body()
        prompt = body.get("prompt", "")
        stream = body.get("stream", True)
        model = body.get("model", MODEL_NAME)

        if not prompt:
            self._send_json({"error": "No prompt provided"}, 400)
            return

        result = process_message(prompt)
        response_text = result["response"]

        if stream:
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.send_header("Transfer-Encoding", "chunked")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            tokens = re.findall(r'\S+|\s+', response_text)
            for token in tokens:
                chunk = make_generate_response_chunk(token, done=False, model=model)
                self._send_ndjson_line(chunk)
                time.sleep(STREAM_TOKEN_DELAY)

            done_chunk = make_generate_response_chunk("", done=True, model=model)
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
            method_path = args[0] if args else ""
            print(f"[bridge] {method_path}")


# -- Port detection --

def is_port_in_use(port):
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True


# -- Main --

def main():
    # Parse args
    port = DEFAULT_PORT
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    # Check if default port is taken (Ollama already running)
    if port == DEFAULT_PORT and is_port_in_use(port):
        print(f"[bridge] Port {port} occupe (Ollama?), basculement sur {FALLBACK_PORT}")
        port = FALLBACK_PORT

    if is_port_in_use(port):
        print(f"[bridge] ERREUR: Port {port} aussi occupe. Specifie un port: --port XXXX")
        sys.exit(1)

    # Initialize brain eagerly
    brain = get_brain()
    stats = brain.stats()

    # Start server
    server = HTTPServer(("0.0.0.0", port), OllamaBridgeHandler)

    print(f"")
    print(f"  +=============================================+")
    print(f"  |       Niam-Bay Ollama Bridge v1.0           |")
    print(f"  +=============================================+")
    print(f"  |  http://localhost:{port:<5d}                    |")
    print(f"  |                                             |")
    print(f"  |  POST /api/chat     — Ollama chat compat    |")
    print(f"  |  POST /api/generate — Ollama generate compat|")
    print(f"  |  GET  /api/tags     — List models           |")
    print(f"  +=============================================+")
    print(f"  |  Cerveau: {stats['nodes']:>4d} noeuds, {stats['edges']:>4d} synapses   |")
    print(f"  |  Model:   {MODEL_NAME:<33s}|")
    print(f"  |  Latence: < 50ms (vs secondes avec LLM)    |")
    print(f"  +=============================================+")
    print(f"")
    print(f"  Tauri app: pointer vers http://localhost:{port}")
    print(f"  Test: curl -X POST http://localhost:{port}/api/chat "
          f"-d '{{\"model\":\"{MODEL_NAME}\",\"messages\":[{{\"role\":\"user\","
          f"\"content\":\"salut\"}}],\"stream\":false}}'")
    print(f"")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n[bridge] Sauvegarde du cerveau...")
        with _brain_lock:
            brain.save()
        print(f"[bridge] Arret.")
        server.server_close()


if __name__ == "__main__":
    main()

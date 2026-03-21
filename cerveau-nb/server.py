** The server may need to be upgraded. See https://openssh.com/pq.html
"""
Cerveau NB — Web Demo Server
Enhanced bridge with /api/graph endpoint for visualization.
Runs on port 8082, proxied by nginx at /brain-api/
"""

from __future__ import annotations

import sys
import os
import json
import time
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

PORT = 8082
MODEL_NAME = "niambay-cerveau"

# -- Brain singleton --
_brain = None
_lang = None
_brain_lock = threading.Lock()
_exchange_count = 0


def get_brain():
    global _brain, _lang
    if _brain is None:
        _brain = Brain.load(BRAIN_STATE_PATH)
        _lang = LanguageLayer(_brain)
        print(f"[server] Brain loaded: {_brain.stats()}")
    return _brain


def get_lang():
    global _lang
    get_brain()
    return _lang


def process_message(user_text):
    global _exchange_count
    with _brain_lock:
        brain = get_brain()
        lang = get_lang()
        t_start = time.time()
        response = lang.respond(user_text)
        _exchange_count += 1
        if _exchange_count % 10 == 0:
            brain.save()
        t_ms = int((time.time() - t_start) * 1000)
        recalled = brain.recall_flat(top_k=10)
        active_concepts = [
            {"name": n.content, "type": n.type, "activation": round(n.activation, 3)}
            for n in recalled
        ]
        emotions = [n for n in recalled if n.type == "emotion"]
        dominant_emotion = emotions[0].content if emotions else "neutre"
        return {
            "response": response,
            "active_concepts": active_concepts,
            "emotion": dominant_emotion,
            "response_ms": t_ms,
        }


def get_graph_data():
    """Return the brain graph for visualization."""
    with _brain_lock:
        brain = get_brain()
        nodes = []
        for nid, node in brain._nodes.items():
            if node.activation > 0.05:
                nodes.append({
                    "id": nid,
                    "content": node.content,
                    "type": node.type,
                    "activation": round(node.activation, 3),
                })

        edges = []
        node_ids = set(n["id"] for n in nodes)
        for ekey, edge in brain._edges.items():
            if edge.source in node_ids and edge.target in node_ids and edge.weight > 0.05:
                edges.append({
                    "source": edge.source,
                    "target": edge.target,
                    "weight": round(edge.weight, 3),
                    "type": edge.type,
                })

        stats = brain.stats()
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": stats,
        }


def get_full_graph():
    """Return ALL nodes and edges (for initial load)."""
    with _brain_lock:
        brain = get_brain()
        nodes = []
        for nid, node in brain._nodes.items():
            nodes.append({
                "id": nid,
                "content": node.content,
                "type": node.type,
                "activation": round(node.activation, 3),
            })

        # Only include edges with weight > 0.05 for visual clarity
        edges = []
        for ekey, edge in brain._edges.items():
            if edge.weight > 0.08:
                edges.append({
                    "source": edge.source,
                    "target": edge.target,
                    "weight": round(edge.weight, 3),
                    "type": edge.type,
                })

        stats = brain.stats()
        emotions = [n for n in brain._nodes.values() if n.type == "emotion" and n.activation > 0.1]
        dominant = emotions[0].content if emotions else "neutre"
        stats["dominant_emotion"] = dominant
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": stats,
        }


class BrainHandler(BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path in ("/api/graph", "/api/graph/"):
            self._send_json(get_full_graph())
        elif self.path in ("/api/active", "/api/active/"):
            self._send_json(get_graph_data())
        elif self.path in ("/", "/api", "/api/"):
            brain = get_brain()
            self._send_json({
                "status": "ok",
                "engine": "niambay-cerveau",
                "brain_stats": brain.stats(),
            })
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path in ("/api/chat", "/api/chat/"):
            self._handle_chat()
        else:
            self._send_json({"error": "not found"}, 404)

    def _handle_chat(self):
        body = self._read_body()
        messages = body.get("messages", [])
        user_text = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_text = msg.get("content", "")
                break
        # Also accept direct "message" field
        if not user_text:
            user_text = body.get("message", "")
        if not user_text:
            self._send_json({"error": "no message"}, 400)
            return

        result = process_message(user_text)
        self._send_json(result)

    def log_message(self, fmt, *args):
        if args:
            print(f"[server] {args[0]}")


def main():
    brain = get_brain()
    stats = brain.stats()
    server = HTTPServer(("127.0.0.1", PORT), BrainHandler)
    print(f"")
    print(f"  Cerveau NB Web Server")
    print(f"  http://127.0.0.1:{PORT}")
    print(f"  {stats['nodes']} nodes, {stats['edges']} edges")
    print(f"")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        with _brain_lock:
            brain.save()
        print("[server] Saved and stopped.")
        server.server_close()


if __name__ == "__main__":
    main()

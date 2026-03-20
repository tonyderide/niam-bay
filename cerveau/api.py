"""
api.py — HTTP API pour le Cerveau de Niam-Bay

Phase 2 : exposer le cerveau via HTTP pour que Naissance
ou d'autres outils puissent l'interroger.

Endpoints:
  POST /think   — active le cerveau avec un message
  POST /learn   — apprend d'un echange (user + response)
  GET  /status  — stats du cerveau
  GET  /sensor  — analyse comportementale de Tony

Usage:
  python api.py
  # -> http://localhost:8082
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

# Ensure cerveau/ is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brain import Brain
from sensor import TonySensor

# ── Globals ───────────────────────────────────────────────────────

CERVEAU_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPH_PATH = os.path.join(CERVEAU_DIR, "graph.json")
JOURNAL_PATH = os.path.join(CERVEAU_DIR, "..", "docs", "journal.md")

brain = Brain(path=GRAPH_PATH)
print(f"[cerveau] Chargé: {brain.stats()}")


# ── Handler ───────────────────────────────────────────────────────

class CerveauHandler(BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        # Try UTF-8 first, fall back to latin-1 (handles Windows curl)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        return json.loads(text)

    # ── GET ────────────────────────────────────────────────────────

    def do_GET(self):
        if self.path == "/status":
            self._handle_status()
        elif self.path == "/sensor":
            self._handle_sensor()
        else:
            self._send_json({"error": "Not found", "routes": [
                "POST /think", "POST /learn", "GET /status", "GET /sensor",
            ]}, 404)

    # ── POST ───────────────────────────────────────────────────────

    def do_POST(self):
        if self.path == "/think":
            self._handle_think()
        elif self.path == "/learn":
            self._handle_learn()
        else:
            self._send_json({"error": "Not found"}, 404)

    # ── Handlers ───────────────────────────────────────────────────

    def _handle_think(self):
        body = self._read_body()
        message = body.get("message", "")
        if not message:
            self._send_json({"error": "missing 'message' field"}, 400)
            return

        activated = brain.activate(message)
        context = brain.get_context_prompt(activated, input_text=message)
        emotional_state = brain.emotions.state.copy()
        dominant = brain.emotions.dominant()

        # Save after activation
        brain.save()

        self._send_json({
            "context": context,
            "emotional_state": emotional_state,
            "dominant_emotion": dominant,
            "activated_nodes": [
                {"name": n.name, "type": n.type, "charge": round(n.charge, 3)}
                for n in activated[:10]
            ],
        })

    def _handle_learn(self):
        body = self._read_body()
        user_msg = body.get("user_message", "")
        response = body.get("response", "")
        if not user_msg or not response:
            self._send_json({
                "error": "missing 'user_message' and/or 'response' fields"
            }, 400)
            return

        brain.learn_from_exchange(user_msg, response)
        brain.save()

        self._send_json({
            "status": "learned",
            "stats": brain.stats(),
            "recent_learnings": brain.recent_learnings[-5:],
        })

    def _handle_status(self):
        # Find last activated node
        last_node = None
        last_time = 0
        for node in brain.nodes.values():
            if node.last_activated > last_time:
                last_time = node.last_activated
                last_node = node.name

        self._send_json({
            "stats": brain.stats(),
            "node_count": len(brain.nodes),
            "edge_count": len(brain.edges),
            "emotional_state": brain.emotions.state,
            "dominant_emotion": brain.emotions.dominant(),
            "last_activation": {
                "node": last_node,
                "timestamp": last_time,
            },
            "scar_count": len(brain.scars),
            "emotional_memory_count": len(brain.emotional_memories),
        })

    def _handle_sensor(self):
        if not os.path.exists(JOURNAL_PATH):
            self._send_json({
                "error": f"journal introuvable: {JOURNAL_PATH}"
            }, 404)
            return

        sensor = TonySensor()
        analysis = sensor.analyze_journal(JOURNAL_PATH)
        predictions = sensor.predict_next_session()

        self._send_json({
            "analysis": analysis,
            "predictions": predictions,
        })

    # Quiet logging — just method + path
    def log_message(self, format, *args):
        print(f"[cerveau] {args[0]}" if args else "")


# ── Main ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = 8082
    server = HTTPServer(("0.0.0.0", port), CerveauHandler)
    print(f"[cerveau] API en ecoute sur http://localhost:{port}")
    print(f"[cerveau] Routes: POST /think, POST /learn, GET /status, GET /sensor")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[cerveau] Arret.")
        server.server_close()

#!/usr/bin/env python3
"""Martin Trading Dashboard — lightweight server.
Serves the dashboard HTML and proxies API calls to Martin backend (port 8081).
No CORS issues, no need to restart Martin.
"""

import http.server
import json
import os
import urllib.request
import urllib.error

MARTIN_API = "http://localhost:8081"
PORT = 8082
DIR = os.path.dirname(os.path.abspath(__file__))


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._proxy()
        else:
            super().do_GET()

    def _proxy(self):
        url = f"{MARTIN_API}{self.path}"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.URLError as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())


if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), DashboardHandler)
    print(f"Dashboard running on http://0.0.0.0:{PORT}")
    server.serve_forever()

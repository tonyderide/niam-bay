#!/usr/bin/env python3
"""
Trading Dashboard — SSH proxy + HTML dashboard for Martin Grid.
Exposes Martin's grid status via HTTP so Tony can see it from his phone.

Usage: python trading_dashboard.py [--port 8082]
Then run: cloudflared tunnel --url http://localhost:8082
"""

import subprocess
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

VM_HOST = "141.253.108.141"
VM_USER = "ubuntu"
SSH_KEY = os.path.expanduser("~/.ssh/martin_vm.key")
GRID_API = "http://localhost:8081/api/grid/status/PF_ETHUSD"
SYSTEM_API = "http://localhost:8081/api/system/status"
PORT = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8082

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Martin Grid</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0a0a; color: #00ff88; font-family: 'Courier New', monospace; padding: 12px; }
h1 { font-size: 18px; text-align: center; margin-bottom: 8px; color: #00ff88; }
.price { font-size: 42px; text-align: center; font-weight: bold; margin: 12px 0; }
.price.up { color: #00ff88; }
.price.down { color: #ff4444; }
.stats { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 12px; }
.stat { background: #111; border: 1px solid #222; border-radius: 6px; padding: 8px; text-align: center; }
.stat .label { font-size: 10px; color: #666; text-transform: uppercase; }
.stat .value { font-size: 18px; margin-top: 2px; }
.stat .value.profit { color: #00ff88; }
.stat .value.loss { color: #ff4444; }
.grid-visual { margin: 12px 0; }
.level { display: flex; align-items: center; padding: 4px 8px; margin: 2px 0; border-radius: 4px; font-size: 13px; }
.level.buy { background: rgba(0, 255, 136, 0.08); border-left: 3px solid #00ff88; }
.level.sell { background: rgba(255, 68, 68, 0.08); border-left: 3px solid #ff4444; }
.level.filled { opacity: 0.5; }
.level.waiting { opacity: 0.4; border-left-style: dashed; }
.level .idx { width: 20px; color: #666; }
.level .side { width: 36px; font-weight: bold; }
.level .lprice { flex: 1; }
.level .status { font-size: 11px; color: #666; }
.level .rt { font-size: 11px; color: #00ff88; margin-left: 6px; }
.fills { margin-top: 12px; }
.fills h2 { font-size: 14px; color: #666; margin-bottom: 6px; }
.fill { font-size: 11px; padding: 3px 0; border-bottom: 1px solid #111; display: flex; }
.fill .ftime { color: #444; width: 50px; }
.fill .fside { width: 36px; font-weight: bold; }
.fill .fside.buy { color: #00ff88; }
.fill .fside.sell { color: #ff4444; }
.fill .fprice { flex: 1; }
.fill .fprofit { color: #00ff88; }
.footer { text-align: center; margin-top: 12px; font-size: 10px; color: #333; }
.error { color: #ff4444; text-align: center; padding: 40px; }
</style>
</head>
<body>
<h1>MARTIN GRID — ETH</h1>
<div id="app"><div class="error">Loading...</div></div>
<script>
async function refresh() {
  try {
    const r = await fetch('/api/grid');
    if (!r.ok) throw new Error('API error');
    const d = await r.json();
    render(d);
  } catch(e) {
    document.getElementById('app').innerHTML = '<div class="error">'+e.message+'</div>';
  }
}

function render(d) {
  const pnl = d.krakenTotalPnl || 0;
  const pnlClass = pnl >= 0 ? 'profit' : 'loss';
  const priceClass = pnl >= 0 ? 'up' : 'down';
  const levels = (d.levels || []).slice().reverse();
  const fills = (d.fills || []).slice().reverse().slice(0, 10);

  let html = '';
  html += '<div class="price ' + priceClass + '">$' + (d.centerPrice||0).toFixed(1) + '</div>';
  html += '<div class="stats">';
  html += stat('Round-trips', d.completedRoundTrips || 0, 'profit');
  html += stat('Grid Profit', '$' + (d.totalProfit||0).toFixed(4), (d.totalProfit||0) >= 0 ? 'profit' : 'loss');
  html += stat('Kraken PnL', '$' + pnl.toFixed(4), pnlClass);
  html += stat('Capital', '$' + (d.capital||0).toFixed(2), '');
  html += stat('Leverage', (d.leverage||0) + 'x', '');
  html += stat('Active', d.active ? 'YES' : 'NO', d.active ? 'profit' : 'loss');
  html += '</div>';

  html += '<div class="grid-visual">';
  for (const l of levels) {
    const cls = l.side + (l.status === 'FILLED' ? ' filled' : '') + (l.status === 'WAITING' ? ' waiting' : '');
    const rt = l.roundTrips > 0 ? '<span class="rt">RT:' + l.roundTrips + '</span>' : '';
    const bf = l.hasBuyFill ? ' [BF]' : '';
    html += '<div class="level ' + cls + '">';
    html += '<span class="idx">' + l.index + '</span>';
    html += '<span class="side">' + l.side.toUpperCase() + '</span>';
    html += '<span class="lprice">$' + l.price.toFixed(1) + '</span>';
    html += '<span class="status">' + l.status + bf + '</span>';
    html += rt;
    html += '</div>';
  }
  html += '</div>';

  if (fills.length > 0) {
    html += '<div class="fills"><h2>Recent Fills</h2>';
    for (const f of fills) {
      const t = f.filledAt ? f.filledAt.substring(11, 16) : '?';
      const p = f.profit > 0 ? '+$' + f.profit.toFixed(4) : '';
      html += '<div class="fill">';
      html += '<span class="ftime">' + t + '</span>';
      html += '<span class="fside ' + f.side + '">' + f.side.toUpperCase() + '</span>';
      html += '<span class="fprice">$' + f.price.toFixed(1) + '</span>';
      html += '<span class="fprofit">' + p + '</span>';
      html += '</div>';
    }
    html += '</div>';
  }

  html += '<div class="footer">Updated: ' + new Date().toLocaleTimeString() + ' — auto-refresh 30s</div>';
  document.getElementById('app').innerHTML = html;
}

function stat(label, value, cls) {
  return '<div class="stat"><div class="label">' + label + '</div><div class="value ' + cls + '">' + value + '</div></div>';
}

refresh();
setInterval(refresh, 30000);
</script>
</body>
</html>"""


def ssh_fetch(api_url):
    """Fetch data from Martin API via SSH tunnel."""
    cmd = [
        "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
        "-i", SSH_KEY, f"{VM_USER}@{VM_HOST}",
        f"curl -s {api_url}"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return None


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/grid':
            data = ssh_fetch(GRID_API)
            if data:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            else:
                self.send_response(502)
                self.end_headers()
                self.wfile.write(b'{"error": "Cannot reach Martin"}')
        elif self.path == '/api/system':
            data = ssh_fetch(SYSTEM_API)
            if data:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            else:
                self.send_response(502)
                self.end_headers()
                self.wfile.write(b'{"error": "Cannot reach VM"}')
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode())

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


def main():
    server = HTTPServer(('0.0.0.0', PORT), DashboardHandler)
    print(f"Dashboard running on http://localhost:{PORT}")
    print(f"Run: cloudflared tunnel --url http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutdown.")


if __name__ == "__main__":
    main()

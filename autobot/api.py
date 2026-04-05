import os
#!/usr/bin/env python3
"""Martin Summary API — lightweight HTTP server on port 8083."""

import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone, timedelta

MARTIN_API = os.getenv("MARTIN_API", "http://localhost:8081")

def fetch_json(url, timeout=5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:
        return None

def parse_iso(ts):
    """Parse ISO timestamp string to datetime (UTC)."""
    if not ts:
        return None
    try:
        # Handle various ISO formats
        ts = ts.replace("Z", "+00:00")
        if "+" not in ts and len(ts) > 19:
            ts = ts[:19] + "+00:00"
        elif "+" not in ts:
            ts = ts + "+00:00"
        return datetime.fromisoformat(ts)
    except Exception:
        return None

def compute_period_stats(fills, start_dt):
    """Compute stats for fills that occurred >= start_dt."""
    period_fills = []
    for f in fills:
        ft = parse_iso(f.get("filledAt"))
        if ft and ft >= start_dt:
            period_fills.append(f)

    fill_count = len(period_fills)
    profit = sum(f.get("profit", 0) for f in period_fills)

    # Count round trips: a sell with profit > 0 completes a round trip
    round_trips = sum(1 for f in period_fills if f.get("side") == "sell" and f.get("profit", 0) > 0)

    return {
        "fills": fill_count,
        "round_trips": round_trips,
        "profit": round(profit, 4),
    }

def build_summary():
    # Auto-detect active grid
    active_grids = fetch_json(f"{MARTIN_API}/api/grid/active")
    instrument = "PF_ETHUSD"  # default
    if isinstance(active_grids, list) and active_grids:
        instrument = active_grids[0]
    grid_raw = fetch_json(f"{MARTIN_API}/api/grid/status/{instrument}")
    sys_raw  = fetch_json(f"{MARTIN_API}/api/system/status")

    # Grid status
    active = False
    if grid_raw:
        active = grid_raw.get("active", False)

    # System info
    uptime_s = 0
    if sys_raw:
        uptime_s = sys_raw.get("uptime_seconds", 0)

    # Format uptime
    days = uptime_s // 86400
    hours = (uptime_s % 86400) // 3600
    if days > 0:
        uptime_str = f"{days}d {hours}h"
    elif hours > 0:
        uptime_str = f"{hours}h {(uptime_s % 3600) // 60}m"
    else:
        uptime_str = f"{uptime_s // 60}m"

    # Extract grid details
    eth_price = grid_raw.get("currentPrice") if grid_raw else None
    capital = grid_raw.get("capital") if grid_raw else None
    leverage = grid_raw.get("leverage") if grid_raw else None
    fills = grid_raw.get("fills", []) if grid_raw else []
    started_at = grid_raw.get("startedAt") if grid_raw else None
    pnl_kraken_total = grid_raw.get("krakenTotalPnl") if grid_raw else None

    # Now compute period boundaries (UTC)
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    three_days_ago = today_start - timedelta(days=2)  # includes today
    week_ago = today_start - timedelta(days=6)         # includes today
    month_ago = today_start - timedelta(days=29)       # includes today
    epoch = datetime(2000, 1, 1, tzinfo=timezone.utc)

    # Period stats
    today_stats = compute_period_stats(fills, today_start)
    three_day_stats = compute_period_stats(fills, three_days_ago)
    week_stats = compute_period_stats(fills, week_ago)
    month_stats = compute_period_stats(fills, month_ago)
    all_time_stats = compute_period_stats(fills, epoch)

    # Estimate pnl_kraken per period proportionally if we have total
    # We can't get exact kraken PnL per period, so we use the total for all_time
    # and leave others as None unless we can compute from fills
    if pnl_kraken_total is not None:
        all_time_stats["pnl_kraken"] = round(pnl_kraken_total, 4)

    if started_at:
        all_time_stats["started"] = started_at

    # Transactions today
    transactions_today = []
    for f in fills:
        ft = parse_iso(f.get("filledAt"))
        if ft and ft >= today_start:
            transactions_today.append({
                "side": f.get("side", "?"),
                "price": f.get("price"),
                "time": ft.strftime("%H:%M"),
                "profit": round(f.get("profit", 0), 4),
            })

    # Last fill
    last_fill = None
    if fills:
        lf = fills[-1]
        side = lf.get("side", "?")
        price = lf.get("price", "?")
        ts = lf.get("filledAt", "")
        ft = parse_iso(ts)
        if ft:
            last_fill = f"{side} @ {price} ({ft.strftime('%Y-%m-%d %H:%M')})"
        else:
            last_fill = f"{side} @ {price}"

    # Resume
    if active:
        price_str = f"{eth_price:.0f}$" if eth_price else "?"
        rt_today = today_stats["round_trips"]
        profit_today = today_stats["profit"]
        rt_week = week_stats["round_trips"]
        profit_week = week_stats["profit"]
        resume = f"Grid active x{leverage or '?'}. Aujourd'hui: {rt_today} RT, {profit_today}$ profit. Semaine: {rt_week} RT, +{profit_week}$. ETH a {price_str}."
    else:
        resume = f"Grid stopped. VM up depuis {uptime_str}."

    result = {
        "grid": "active" if active else "stopped",
        "eth_price": eth_price,
        "leverage": leverage,
        "capital": capital,
        "today": today_stats,
        "last_3_days": three_day_stats,
        "last_week": week_stats,
        "last_month": month_stats,
        "all_time": all_time_stats,
        "transactions_today": transactions_today,
        "last_fill": last_fill,
        "vm_uptime": uptime_str,
        "resume": resume,
    }

    return result


def build_transactions():
    """Return ALL fills as a clean list with formatted dates."""
    # Auto-detect active grid
    active_grids = fetch_json(f"{MARTIN_API}/api/grid/active")
    instrument = "PF_ETHUSD"  # default
    if isinstance(active_grids, list) and active_grids:
        instrument = active_grids[0]
    grid_raw = fetch_json(f"{MARTIN_API}/api/grid/status/{instrument}")
    fills = grid_raw.get("fills", []) if grid_raw else []

    transactions = []
    for f in fills:
        ft = parse_iso(f.get("filledAt"))
        transactions.append({
            "side": f.get("side", "?"),
            "price": f.get("price"),
            "profit": round(f.get("profit", 0), 4),
            "filledAt": f.get("filledAt"),
            "date": ft.strftime("%Y-%m-%d") if ft else None,
            "time": ft.strftime("%H:%M:%S") if ft else None,
            "formatted": ft.strftime("%d %b %Y %H:%M") if ft else None,
        })

    return {
        "count": len(transactions),
        "transactions": transactions,
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.rstrip("/")

        if path == "/api/martin":
            data = build_summary()
            self._json_response(200, data)
        elif path == "/api/martin/transactions":
            data = build_transactions()
            self._json_response(200, data)
        elif path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def _json_response(self, code, data):
        body = json.dumps(data, indent=2, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # silent


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8083), Handler)
    print("Martin Summary API running on :8083")
    server.serve_forever()

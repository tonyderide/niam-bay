#!/usr/bin/env python3
"""
Martin Grid Monitor — Niam-Bay
Monitors the Martin trading bot on Oracle VM via SSH.
Run: python martin_monitor.py
"""

import subprocess
import json
import sys
import os
from datetime import datetime, timezone

# --- Config ---
VM_HOST = "141.253.108.141"
VM_USER = "ubuntu"
SSH_KEY = os.path.expanduser("~/.ssh/martin_vm.key")
API_URL = "http://localhost:8081/api/grid/status/PF_ETHUSD"
ALERTS_FILE = os.path.join(os.path.dirname(__file__), "..", "docs", "conversations", "martin-alerts.md")

# --- SSH fetch ---
def fetch_grid_status():
    """SSH into VM and curl the grid status API."""
    cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        "-i", SSH_KEY,
        f"{VM_USER}@{VM_HOST}",
        f"curl -s {API_URL}"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if result.returncode != 0:
            print(f"[ERROR] SSH failed: {result.stderr.strip()}")
            sys.exit(1)
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        print("[ERROR] SSH connection timed out")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"[ERROR] Invalid JSON response: {result.stdout[:200]}")
        sys.exit(1)

# --- Display ---
def print_summary(data):
    """Print a clean summary of the grid status."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    started = data.get("startedAt", "?")

    levels = data.get("levels", [])
    buy_levels = [l for l in levels if l["side"] == "buy"]
    sell_levels = [l for l in levels if l["side"] == "sell"]
    filled_levels = [l for l in levels if l["status"] == "FILLED"]
    buy_fills = [l for l in levels if l.get("hasBuyFill")]

    total_rt = data.get("completedRoundTrips", 0)
    total_profit = data.get("totalProfit", 0)
    kraken_realized = data.get("krakenRealizedPnl", 0)
    kraken_unrealized = data.get("krakenUnrealizedPnl", 0)
    kraken_total = data.get("krakenTotalPnl", 0)

    print("=" * 56)
    print(f"  MARTIN GRID MONITOR — {now}")
    print("=" * 56)
    print(f"  Instrument:    {data.get('instrument', '?')}")
    print(f"  Active:        {data.get('active', '?')}")
    print(f"  Demo:          {data.get('demo', '?')}")
    print(f"  Started:       {started}")
    print(f"  Leverage:      {data.get('leverage', '?')}x")
    print(f"  Capital:       ${data.get('capital', 0):.2f}")
    print(f"  Max loss:      {data.get('maxLossPercent', 0)}%")
    print("-" * 56)
    print(f"  Grid center:   ${data.get('centerPrice', 0):.1f}")
    print(f"  Range:         ${data.get('lowerBound', 0):.1f} — ${data.get('upperBound', 0):.1f}")
    print(f"  Spacing:       ${data.get('gridSpacing', 0):.1f}")
    print(f"  Amt/level:     {data.get('amountPerLevel', 0)}")
    print("-" * 56)
    print(f"  Total levels:  {len(levels)}  (buy: {len(buy_levels)}, sell: {len(sell_levels)})")
    print(f"  Filled:        {len(filled_levels)}")
    print(f"  Buy fills:     {len(buy_fills)}")
    print("-" * 56)
    print("  LEVELS:")
    for l in levels:
        marker = ""
        if l["status"] == "FILLED":
            marker = " << FILLED"
        elif l.get("hasBuyFill"):
            marker = " [buy filled]"
        print(f"    [{l['index']}] {l['side']:4s} ${l['price']:.1f}  {l['status']}{marker}")
    print("-" * 56)
    print(f"  Round-trips:   {total_rt}")
    print(f"  Grid profit:   ${total_profit:.4f}")
    print(f"  Kraken PnL:    realized ${kraken_realized:.4f}  |  unrealized ${kraken_unrealized:.4f}")
    print(f"  Kraken total:  ${kraken_total:.4f}")
    print("=" * 56)

    return total_rt, total_profit

# --- Alert logging ---
def log_alert(data, round_trips):
    """Log round-trip completions to martin-alerts.md."""
    alerts_path = os.path.normpath(ALERTS_FILE)
    os.makedirs(os.path.dirname(alerts_path), exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"\n## {now} — Round-trip alert\n\n"
        f"- Instrument: {data.get('instrument')}\n"
        f"- Completed round-trips: {round_trips}\n"
        f"- Grid profit: ${data.get('totalProfit', 0):.4f}\n"
        f"- Kraken total PnL: ${data.get('krakenTotalPnl', 0):.4f}\n"
        f"- Center: ${data.get('centerPrice', 0):.1f}\n\n"
    )

    # Check previous RT count to detect new ones
    header = "# Martin Alerts\n\nRound-trip completions logged automatically.\n"
    if not os.path.exists(alerts_path):
        with open(alerts_path, "w", encoding="utf-8") as f:
            f.write(header + entry)
        print(f"\n[ALERT] Logged to {alerts_path}")
    else:
        with open(alerts_path, "a", encoding="utf-8") as f:
            f.write(entry)
        print(f"\n[ALERT] Appended to {alerts_path}")

# --- State file for tracking RT count between runs ---
STATE_FILE = os.path.join(os.path.dirname(__file__), ".martin_state.json")

def load_previous_rt():
    """Load previous round-trip count."""
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f).get("roundTrips", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0

def save_rt(count):
    """Save current round-trip count."""
    with open(STATE_FILE, "w") as f:
        json.dump({"roundTrips": count, "updatedAt": datetime.now().isoformat()}, f)

# --- Main ---
def main():
    print("Fetching grid status via SSH...")
    data = fetch_grid_status()

    total_rt, total_profit = print_summary(data)

    # Check for new round-trips
    prev_rt = load_previous_rt()
    if total_rt > prev_rt:
        print(f"\n*** NEW ROUND-TRIPS: {total_rt - prev_rt} since last check! ***")
        log_alert(data, total_rt)
    elif total_rt > 0:
        print(f"\n(No new round-trips since last check)")

    save_rt(total_rt)

if __name__ == "__main__":
    main()

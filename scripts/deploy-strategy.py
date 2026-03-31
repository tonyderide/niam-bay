#!/usr/bin/env python3
"""
deploy-strategy.py — Deploy Martin Grid strategy from strategy-config.json

Usage: python3 ~/martin/deploy-strategy.py [--dry-run] [--no-stop] [--only PAIR]

Created by: Momentum Mike, Volume Vicky, Risk Rico (2026-04-01)
"""

import json
import sys
import time
import urllib.request
import urllib.parse
import os
from datetime import datetime

MARTIN_URL = "http://localhost:8081"
CONFIG_PATH = os.path.expanduser("~/martin/strategy-config.json")

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def log(msg, color=RESET):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{ts}] {msg}{RESET}")


def api_call(method, path, timeout=15):
    """Call Martin API. Returns parsed JSON or None on error."""
    url = f"{MARTIN_URL}{path}"
    try:
        req = urllib.request.Request(url, method=method)
        if method == "POST":
            req.add_header("Content-Length", "0")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode()
            if data:
                return json.loads(data)
            return {"status": "ok"}
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        log(f"API error {e.code}: {path} -> {body[:200]}", RED)
        return None
    except Exception as e:
        log(f"API call failed: {path} -> {e}", RED)
        return None


def load_config():
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    log(f"Loaded config v{config['version']} (updated: {config['updatedAt']})", CYAN)
    return config


def check_balance(config):
    """Check balance and drawdown kill."""
    result = api_call("GET", "/api/bot/balance")
    if not result:
        log("Cannot read balance — ABORTING", RED)
        sys.exit(1)

    flex = result["accounts"]["flex"]
    portfolio = flex["portfolioValue"]
    available = flex["availableMargin"]

    log(f"Portfolio: ${portfolio:.2f} | Available: ${available:.2f}", CYAN)

    # Drawdown kill check
    dd = config["drawdown"]
    kill_threshold = dd["initialCapital"] * (1 - dd["killPct"] / 100)
    if portfolio < kill_threshold:
        log(f"DRAWDOWN KILL: Portfolio ${portfolio:.2f} < kill threshold ${kill_threshold:.2f} ({dd['killPct']}% drawdown)", RED)
        log("ALL GRIDS DISABLED. Fix manually.", RED)
        sys.exit(2)

    # Check total capital needed
    total_capital = sum(g["capital"] for g in config["grids"] if g["enabled"])
    if total_capital > portfolio * 0.95:
        log(f"WARNING: Total capital needed ${total_capital} is close to portfolio ${portfolio:.2f}", YELLOW)

    reserve_pct = (1 - total_capital / portfolio) * 100
    log(f"Deploying ${total_capital} / ${portfolio:.2f} ({100 - reserve_pct:.0f}% deployed, {reserve_pct:.0f}% reserve)", CYAN)

    return portfolio, available


def stop_all_grids():
    """Stop all currently active grids."""
    active = api_call("GET", "/api/grid/active")
    if not active:
        log("No active grids (or API error)", YELLOW)
        return []

    if isinstance(active, list) and len(active) == 0:
        log("No active grids to stop", GREEN)
        return []

    log(f"Stopping {len(active)} active grids: {active}", YELLOW)
    for pair in active:
        result = api_call("POST", f"/api/grid/stop/{pair}")
        if result:
            log(f"  Stopped {pair}", GREEN)
        else:
            log(f"  Failed to stop {pair}", RED)
        time.sleep(2)

    # Wait for orders to cancel
    log("Waiting 5s for orders to cancel...", CYAN)
    time.sleep(5)
    return active


def start_grid(grid_config):
    """Start a single grid from config."""
    g = grid_config
    params = urllib.parse.urlencode({
        "instrument": g["instrument"],
        "capital": g["capital"],
        "leverage": g["leverage"],
        "gridSpacingPct": g["gridSpacingPct"],
        "totalLevels": g["totalLevels"],
        "maxLossPercent": g["maxLossPercent"],
        "gridMode": g["gridMode"]
    })

    result = api_call("POST", f"/api/grid/start?{params}")
    if result:
        log(f"  Started {g['instrument']}: capital=${g['capital']} lev=x{g['leverage']} spacing={g['gridSpacingPct']}% levels={g['totalLevels']}", GREEN)
        return True
    else:
        log(f"  FAILED to start {g['instrument']}", RED)
        return False


def enable_trailing(instrument, trail, min_profit):
    """Enable trailing stop for a grid."""
    params = urllib.parse.urlencode({
        "instrument": instrument,
        "trail": trail,
        "minProfit": min_profit
    })
    result = api_call("POST", f"/api/grid/trailing/enable?{params}")
    if result:
        log(f"  Trailing enabled: {instrument} (trail={trail}%, minProfit={min_profit}%)", GREEN)
    else:
        log(f"  Trailing FAILED: {instrument}", RED)


def configure_auto_grid(grid_config, auto_config):
    """Configure auto-grid signal for a pair."""
    g = grid_config
    params = urllib.parse.urlencode({
        "instrument": g["instrument"],
        "capital": g["capital"],
        "leverage": g["leverage"],
        "demo": "false",
        "gridSpacingPct": g["gridSpacingPct"],
        "totalLevels": g["totalLevels"],
        "maxLossPercent": g["maxLossPercent"],
        "gridMode": g["gridMode"]
    })
    result = api_call("POST", f"/api/signal/auto/config?{params}")
    if result:
        log(f"  Auto-grid configured: {g['instrument']}", GREEN)
    else:
        log(f"  Auto-grid config FAILED: {g['instrument']}", RED)


def verify_grid(instrument, expected_levels):
    """Verify a grid is running and orders are placed."""
    status = api_call("GET", f"/api/grid/status/{instrument}")
    if not status:
        return False, "Cannot read status"

    if not status.get("active"):
        return False, "Grid not active"

    levels = status.get("levels", [])
    placed = sum(1 for l in levels if l.get("status") == "PLACED")
    waiting = sum(1 for l in levels if l.get("status") == "WAITING")

    return True, f"Active | {placed} placed, {waiting} waiting, center={status.get('centerPrice')}, leverage={status.get('leverage')}"


def deploy(dry_run=False, no_stop=False, only_pair=None):
    """Main deployment flow."""
    log(f"{BOLD}=== MARTIN STRATEGY DEPLOYMENT ==={RESET}", CYAN)
    log(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}", YELLOW if dry_run else GREEN)

    # 1. Load config
    config = load_config()
    enabled_grids = [g for g in config["grids"] if g["enabled"]]
    if only_pair:
        enabled_grids = [g for g in enabled_grids if g["instrument"] == only_pair]
        if not enabled_grids:
            log(f"No grid found for {only_pair}", RED)
            sys.exit(1)

    log(f"Grids to deploy: {len(enabled_grids)}", CYAN)
    for g in enabled_grids:
        log(f"  {g['instrument']}: ${g['capital']} x{g['leverage']} spacing={g['gridSpacingPct']}% levels={g['totalLevels']}", CYAN)

    # 2. Check balance & drawdown
    portfolio, available = check_balance(config)

    if dry_run:
        log("DRY RUN complete. No changes made.", YELLOW)
        return

    # 3. Stop existing grids
    if not no_stop:
        stopped = stop_all_grids()

    # 4. Start each grid
    log(f"{BOLD}--- Starting grids ---{RESET}", CYAN)
    started = []
    for g in enabled_grids:
        success = start_grid(g)
        if success:
            started.append(g)
        time.sleep(3)  # Wait between starts to not overwhelm

    # 5. Wait for orders to place
    log("Waiting 15s for orders to place on Kraken...", CYAN)
    time.sleep(15)

    # 6. Enable trailing stops
    log(f"{BOLD}--- Enabling trailing stops ---{RESET}", CYAN)
    trailing = config["trailing"]
    for g in started:
        enable_trailing(g["instrument"], trailing["trailAmount"], trailing["minProfit"])
        time.sleep(1)

    # 7. Configure auto-grid
    if config["autoGrid"]["enabled"]:
        log(f"{BOLD}--- Configuring auto-grid ---{RESET}", CYAN)
        for g in started:
            configure_auto_grid(g, config["autoGrid"])
            time.sleep(1)

        # Enable auto-grid globally
        result = api_call("POST", "/api/signal/auto/enable")
        if result:
            log("Auto-grid enabled globally", GREEN)
        else:
            log("Auto-grid enable FAILED", RED)

    # 8. Verify all grids
    log(f"{BOLD}--- Verification ---{RESET}", CYAN)
    all_ok = True
    for g in started:
        ok, msg = verify_grid(g["instrument"], g["totalLevels"])
        color = GREEN if ok else RED
        log(f"  {g['instrument']}: {msg}", color)
        if not ok:
            all_ok = False

    # 9. Final balance check
    log(f"{BOLD}--- Final Balance ---{RESET}", CYAN)
    check_balance(config)

    # 10. Update config timestamp
    config["updatedAt"] = datetime.utcnow().isoformat() + "Z"
    config["lastDeployment"] = {
        "at": datetime.utcnow().isoformat() + "Z",
        "gridsStarted": len(started),
        "success": all_ok
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    log("Config saved with deployment timestamp", GREEN)

    # Summary
    status_word = "SUCCESS" if all_ok else "PARTIAL - CHECK ERRORS"
    log(f"{BOLD}=== DEPLOYMENT {status_word} ==={RESET}", GREEN if all_ok else RED)
    log(f"Grids: {len(started)}/{len(enabled_grids)} started", GREEN if len(started) == len(enabled_grids) else YELLOW)


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    no_stop = "--no-stop" in sys.argv
    only_pair = None
    for i, arg in enumerate(sys.argv):
        if arg == "--only" and i + 1 < len(sys.argv):
            only_pair = sys.argv[i + 1]

    deploy(dry_run=dry_run, no_stop=no_stop, only_pair=only_pair)

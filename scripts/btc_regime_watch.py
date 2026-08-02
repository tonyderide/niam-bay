#!/usr/bin/env python3
"""
btc_regime_watch.py — Surveillance de flip de régime BTC
=========================================================
Cycle 249 (2026-08-02). Créé pendant vacances Portugal Tony.

Contexte : 3 grids SHORT actives (LINK/DOT/SOL) déployées en DOWNTREND.
Si BTC passe EMA200 vers le haut (DOWNTREND→UPTREND), les grids deviennent
anti-trend. Ce script détecte ce moment et alerte Tony via Telegram.

Fonctionnement :
  - Lit l'EMA trend via Martin API
  - Stocke l'état précédent dans /tmp/btc_regime_state.json
  - Envoie Telegram si :
      • flip DOWNTREND → UPTREND (critique)
      • ou cushion > --warn-pct (DOWNTREND qui s'efface rapidement)
  - Mode --report : affiche l'état sans alerter (usage: cycle de monitoring)

Usage :
  # Check silencieux (sortie stdout uniquement)
  python3 scripts/btc_regime_watch.py

  # Avec alerte Telegram si flip ou proximité
  python3 scripts/btc_regime_watch.py --telegram

  # Depuis PC local (SSH auto via subprocess) :
  python3 scripts/btc_regime_watch.py --ssh

  # Rapport seul (pour vacation-autonomy.md)
  python3 scripts/btc_regime_watch.py --ssh --report

Cron suggestion (PC local, toutes les 15min) :
  */15 * * * * cd ~/projets/tonyderide/niam-bay && .venv/bin/python3 scripts/btc_regime_watch.py --ssh --telegram >> /tmp/btc_regime_watch.log 2>&1
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone


VM_IP = "141.253.108.141"
VM_USER = "ubuntu"
SSH_KEY = os.path.expanduser("~/.ssh/martin_vm.key")
MARTIN_PORT = 8081

BOT_TOKEN = "7913168011:AAG76RsddMBpUnveiEdK2HSk4PQLS7Ab454"
CHAT_ID = "6574420846"

STATE_FILE = "/tmp/btc_regime_state.json"
SIGNAL_URL_TMPL = "http://{host}:{port}/api/signal/ema_trend?instrument=PF_XBTUSD"


def http_get(url: str, timeout: int = 10) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.load(r)
    except Exception as e:
        print(f"[ERROR] {url}: {e}", file=sys.stderr)
        return {}


def ssh_get_signal() -> dict:
    cmd = [
        "ssh", "-i", SSH_KEY,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        f"{VM_USER}@{VM_IP}",
        f"curl -s 'http://localhost:{MARTIN_PORT}/api/signal/ema_trend?instrument=PF_XBTUSD'"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if result.returncode != 0:
            print(f"[SSH ERROR] {result.stderr.strip()}", file=sys.stderr)
            return {}
        return json.loads(result.stdout)
    except Exception as e:
        print(f"[SSH ERROR] {e}", file=sys.stderr)
        return {}


def send_telegram(msg: str) -> bool:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": CHAT_ID, "text": msg}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}", file=sys.stderr)
        return False


def load_state() -> dict:
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {"status": "UNKNOWN", "cushion_pct": 0.0}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def cushion_pct(price: float, ema200: float) -> float:
    return ((price - ema200) / ema200 * 100) if ema200 else 0.0


def main():
    parser = argparse.ArgumentParser(description="BTC regime flip detector")
    parser.add_argument("--ssh", action="store_true",
                        help="Fetch via SSH (PC local mode, no tunnel needed)")
    parser.add_argument("--host", default="localhost",
                        help="Martin API host (used without --ssh, requires tunnel)")
    parser.add_argument("--telegram", action="store_true",
                        help="Send Telegram alert on flip or proximity")
    parser.add_argument("--warn-pct", type=float, default=-0.3,
                        help="Alert when DOWNTREND cushion > this %% (default: -0.3)")
    parser.add_argument("--report", action="store_true",
                        help="Print full status report (for vacation-autonomy.md)")
    args = parser.parse_args()

    # Fetch signal
    if args.ssh:
        sig = ssh_get_signal()
    else:
        sig = http_get(SIGNAL_URL_TMPL.format(host=args.host, port=MARTIN_PORT))

    if not sig:
        print("[WARN] BTC signal unavailable — Martin API unreachable?", file=sys.stderr)
        sys.exit(1)

    price = sig.get("price", 0.0)
    ema200 = sig.get("ema200", 0.0)
    ema50 = sig.get("ema50", 0.0)
    status = sig.get("emaStatus", "UNKNOWN")
    rsi = sig.get("rsi", 0.0)
    reason = sig.get("reason", "")
    ts = datetime.now(timezone.utc).strftime("%m-%d %H:%M UTC")
    cush = cushion_pct(price, ema200)

    state = load_state()
    prev_status = state.get("status", "UNKNOWN")
    prev_cushion = state.get("cushion_pct", 0.0)

    # Compute delta
    cushion_delta = cush - prev_cushion

    # Determine alert conditions
    flipped_up = prev_status == "DOWNTREND" and status == "UPTREND"
    flipped_down = prev_status == "UPTREND" and status == "DOWNTREND"
    approaching = status == "DOWNTREND" and cush > args.warn_pct

    # Console output
    flip_marker = " *** FLIP ***" if (flipped_up or flipped_down) else ""
    print(f"[{ts}] BTC ${price:,.0f} | EMA200 ${ema200:,.0f} | cushion {cush:+.2f}% (Δ{cushion_delta:+.2f}%) | {status}{flip_marker} | RSI {rsi:.1f}")

    if args.report:
        print(f"  EMA50  ${ema50:,.0f}")
        print(f"  Signal reason: {reason}")
        print(f"  Previous: {prev_status} @ {prev_cushion:+.2f}%")
        if approaching:
            print(f"  [PROXIMITY] cushion > {args.warn_pct}% — flip window active")

    # Telegram alerts
    alert_msg = None

    if flipped_up:
        alert_msg = (
            f"⚠️ BTC FLIP → UPTREND\n"
            f"${price:,.0f} > EMA200 ${ema200:,.0f} | cushion {cush:+.2f}%\n"
            f"RSI {rsi:.1f} — Grids SHORT (LINK/DOT/SOL) anti-trend maintenant !\n"
            f"Vérifier SLs sur Kraken Pro."
        )
    elif flipped_down:
        alert_msg = (
            f"✅ BTC → DOWNTREND\n"
            f"${price:,.0f} < EMA200 ${ema200:,.0f} | cushion {cush:+.2f}%\n"
            f"Grids SHORT réalignées avec le régime."
        )
    elif approaching and status == "DOWNTREND":
        # Only alert once (not spam) — compare with previous cushion
        if prev_cushion < args.warn_pct:  # was below threshold before
            alert_msg = (
                f"⚡ BTC approche EMA200\n"
                f"${price:,.0f} | cushion {cush:+.2f}% (seuil: {args.warn_pct:+.1f}%)\n"
                f"RSI {rsi:.1f} — Toujours DOWNTREND mais flip possible.\n"
                f"Grids SHORT: LINK/DOT/SOL avec SLs Kraken."
            )

    if alert_msg:
        print(f"[ALERT] {alert_msg.splitlines()[0]}")
        if args.telegram:
            sent = send_telegram(alert_msg)
            print(f"[TELEGRAM] {'✓ envoyé' if sent else '✗ échec'}")

    # Save state
    save_state({
        "status": status,
        "price": price,
        "ema200": ema200,
        "cushion_pct": cush,
        "rsi": rsi,
        "ts": ts
    })

    # Exit code: 1 if flip detected (for scripts that check)
    if flipped_up or flipped_down:
        sys.exit(2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Trailing stop loss pour le grid SHORT BTC.
Logique : une fois que totalProfit dépasse un seuil, on protège les gains.
Si le profit retombe de plus de TRAIL_AMOUNT depuis le pic, on stoppe le grid.

Usage : python trailing_stop_btc.py [--interval 30] [--trail 0.30] [--min-profit 0.20]
"""
import argparse
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

MARTIN_API = "http://localhost:8081"
TELEGRAM_TOKEN = "7913168011:AAG76RsddMBpUnveiEdK2HSk4PQLS7Ab454"
TELEGRAM_CHAT = "6574420846"
PAIR = "PF_XBTUSD"


def now():
    return datetime.now(timezone.utc).strftime("%H:%M:%S UTC")


def telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": TELEGRAM_CHAT, "text": msg}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


def get_grid_status():
    url = f"{MARTIN_API}/api/grid/status/{PAIR}"
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req, timeout=5)
    return json.loads(resp.read())


def get_btc_price():
    url = "https://futures.kraken.com/derivatives/api/v3/tickers"
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req, timeout=5)
    data = json.loads(resp.read())
    for t in data["tickers"]:
        if t["symbol"] == PAIR:
            return float(t["last"])
    return None


def stop_grid():
    url = f"{MARTIN_API}/api/grid/stop/{PAIR}"
    req = urllib.request.Request(url, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=5)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=30, help="Polling interval seconds")
    parser.add_argument("--trail", type=float, default=0.30, help="Trail amount in $ (default 0.30)")
    parser.add_argument("--min-profit", type=float, default=0.20, help="Min profit before trailing activates (default 0.20)")
    args = parser.parse_args()

    high_water = 0.0
    trailing_active = False
    check_count = 0

    print(f"[{now()}] Trailing stop démarré — trail={args.trail}$ min_profit={args.min_profit}$ interval={args.interval}s")
    telegram(f"🛡️ Trailing stop actif\nPair: {PAIR}\nTrail: {args.trail}$\nActivation: profit > {args.min_profit}$")

    while True:
        try:
            status = get_grid_status()
            check_count += 1

            if not status.get("active"):
                print(f"[{now()}] Grid inactif — trailing stop terminé")
                telegram(f"ℹ️ Grid {PAIR} inactif — trailing stop terminé après {check_count} checks")
                break

            total_profit = float(status.get("totalProfit", 0))
            center = float(status.get("centerPrice", 0))
            rt_count = int(status.get("completedRoundTrips", 0))
            btc_price = get_btc_price() or 0

            # Update high water mark
            if total_profit > high_water:
                high_water = total_profit
                if not trailing_active and high_water >= args.min_profit:
                    trailing_active = True
                    print(f"[{now()}] Trailing ACTIVÉ — profit={high_water:.4f}$ (seuil={args.min_profit}$)")
                    telegram(f"✅ Trailing stop activé\nProfit: {high_water:.4f}$\nStop si profit < {high_water - args.trail:.4f}$")

            # Check trailing stop condition
            if trailing_active:
                stop_level = high_water - args.trail
                if total_profit < stop_level:
                    print(f"[{now()}] 🚨 TRAILING STOP DÉCLENCHÉ — profit={total_profit:.4f}$ < stop={stop_level:.4f}$ (high={high_water:.4f}$)")
                    result = stop_grid()
                    telegram(
                        f"🚨 TRAILING STOP — Grid {PAIR} stoppé\n"
                        f"Profit: {total_profit:.4f}$ (high: {high_water:.4f}$)\n"
                        f"RTs: {rt_count} | BTC: {btc_price:.0f}$\n"
                        f"Gains protégés: {total_profit:.4f}$"
                    )
                    break

                # Log status every 5 checks
                if check_count % 5 == 0:
                    print(
                        f"[{now()}] P={total_profit:.4f}$ | HIGH={high_water:.4f}$ | STOP>{stop_level:.4f}$ | RT={rt_count} | BTC={btc_price:.0f}"
                    )
            else:
                # Log while waiting for activation
                if check_count % 5 == 0:
                    print(
                        f"[{now()}] En attente (trail inactif) — P={total_profit:.4f}$ < {args.min_profit}$ | RT={rt_count} | BTC={btc_price:.0f}"
                    )

        except urllib.error.URLError as e:
            print(f"[{now()}] Erreur réseau: {e}")
        except KeyboardInterrupt:
            print(f"\n[{now()}] Trailing stop interrompu manuellement")
            telegram(f"⏹️ Trailing stop {PAIR} interrompu manuellement")
            break
        except Exception as e:
            print(f"[{now()}] Erreur: {e}")

        time.sleep(args.interval)


if __name__ == "__main__":
    main()

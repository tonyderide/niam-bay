#!/usr/bin/env python3
"""
Niam-Bay Telegram Bot — bidirectionnel
Commandes: /status /balance /price /start /short /stop /help
"""

import requests
import time
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger(__name__)

BOT_TOKEN = "7913168011:AAG76RsddMBpUnveiEdK2HSk4PQLS7Ab454"
CHAT_ID = "6574420846"
MARTIN = "http://localhost:8081"
KRAKEN_PUBLIC = "https://api.kraken.com/0/public"
OFFSET = 0


def tg_send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        log.error(f"tg_send error: {e}")


def tg_get_updates(offset):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        r = requests.get(url, params={"offset": offset, "timeout": 30}, timeout=35)
        return r.json().get("result", [])
    except Exception as e:
        log.error(f"getUpdates error: {e}")
        return []


def martin(path, method="GET", params=None):
    try:
        if method == "POST":
            r = requests.post(f"{MARTIN}{path}", params=params, timeout=10)
        else:
            r = requests.get(f"{MARTIN}{path}", timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def kraken_price(pairs="SOLUSD,DOTUSD,ETHUSD,XBTUSD"):
    try:
        r = requests.get(f"{KRAKEN_PUBLIC}/Ticker", params={"pair": pairs}, timeout=10)
        data = r.json().get("result", {})
        lines = []
        labels = {"SOLUSD": "SOL", "DOTUSD": "DOT", "ETHUSD": "ETH", "XBTUSD": "BTC",
                  "XBTUSD": "BTC", "PF_SOLUSD": "SOL", "PF_DOTUSD": "DOT", "PF_ETHUSD": "ETH"}
        for k, v in data.items():
            name = labels.get(k, k)
            price = float(v["c"][0])
            lines.append(f"{name}: ${price:,.2f}")
        return "\n".join(lines)
    except Exception as e:
        return f"Erreur prix: {e}"


def cmd_status():
    grids = martin("/api/grid/active")
    if isinstance(grids, dict) and "error" in grids:
        return f"Martin offline: {grids['error']}"
    if not grids:
        return "Aucune grid active."
    lines = ["*GRIDS ACTIVES*"]
    for g in grids:
        pair = g if isinstance(g, str) else g.get("instrument", "?")
        status = martin(f"/api/grid/status/{pair}")
        mode = status.get("gridMode", "NEUTRAL")
        rt = status.get("completedRoundTrips", 0)
        profit = status.get("totalProfit", 0)
        lev = status.get("leverage", "?")
        cap = status.get("capital", 0)
        lines.append(f"*{pair}* ({mode}) x{lev} {cap}$")
        lines.append(f"  RT: {rt} | Profit: {profit:.4f}$")
    bal = martin("/api/bot/balance")
    if "error" not in bal:
        acc = bal.get("accounts", {}).get("flex", {})
        pv = acc.get("portfolioValue", 0)
        am = acc.get("availableMargin", 0)
        lines.append(f"\nPortfolio: {pv:.2f}$ | Dispo: {am:.2f}$")
    return "\n".join(lines)


def cmd_balance():
    bal = martin("/api/bot/balance")
    if "error" in bal:
        return f"Erreur: {bal['error']}"
    acc = bal.get("accounts", {}).get("flex", {})
    pv = acc.get("portfolioValue", 0)
    am = acc.get("availableMargin", 0)
    pnl = acc.get("unrealizedFunding", 0)
    return f"*BALANCE*\nPortfolio: {pv:.2f}$\nDispo: {am:.2f}$\nPnL: {pnl:.4f}$"


def cmd_price(args):
    if args:
        pair = args[0].upper() + "USD"
        return kraken_price(pair)
    return kraken_price("SOLUSD,DOTUSD,ETHUSD,XBTUSD")


def cmd_start(args):
    # /start DOT [capital] [leverage] [spacing]
    if not args:
        return "Usage: /start PAIR [capital] [leverage] [spacing]\nEx: /start DOT 10 5 0.5"
    pair_map = {"DOT": "PF_DOTUSD", "SOL": "PF_SOLUSD", "ETH": "PF_ETHUSD", "ADA": "PF_ADAUSD", "XRP": "PF_XRPUSD"}
    pair = pair_map.get(args[0].upper(), args[0].upper())
    cap = float(args[1]) if len(args) > 1 else 10
    lev = int(args[2]) if len(args) > 2 else 5
    spacing = float(args[3]) if len(args) > 3 else 0.5
    result = martin("/api/grid/start", "POST", {
        "instrument": pair, "capital": cap, "leverage": lev,
        "gridSpacingPct": spacing, "totalLevels": 10, "maxLossPercent": 15,
        "gridMode": "NEUTRAL"
    })
    if "error" in result:
        return f"Erreur: {result['error']}"
    return f"Grid NEUTRAL lancee: {pair} {cap}$ x{lev} spacing={spacing}%"


def cmd_short(args):
    # /short PAIR [capital] [leverage] [spacing]
    if not args:
        return "Usage: /short PAIR [capital] [leverage] [spacing]\nEx: /short BTC 10 5 0.5"
    pair_map = {"BTC": "PF_XBTUSD", "DOT": "PF_DOTUSD", "SOL": "PF_SOLUSD", "ETH": "PF_ETHUSD"}
    pair = pair_map.get(args[0].upper(), args[0].upper())
    cap = float(args[1]) if len(args) > 1 else 10
    lev = int(args[2]) if len(args) > 2 else 5
    spacing = float(args[3]) if len(args) > 3 else 0.5
    result = martin("/api/grid/start", "POST", {
        "instrument": pair, "capital": cap, "leverage": lev,
        "gridSpacingPct": spacing, "totalLevels": 10, "maxLossPercent": 15,
        "gridMode": "SHORT"
    })
    if "error" in result:
        return f"Erreur: {result['error']}"
    return f"Grid SHORT lancee: {pair} {cap}$ x{lev} spacing={spacing}%"


def cmd_stop(args):
    if not args:
        return "Usage: /stop PAIR\nEx: /stop DOT"
    pair_map = {"BTC": "PF_XBTUSD", "DOT": "PF_DOTUSD", "SOL": "PF_SOLUSD", "ETH": "PF_ETHUSD", "ADA": "PF_ADAUSD", "XRP": "PF_XRPUSD"}
    pair = pair_map.get(args[0].upper(), args[0].upper())
    result = martin(f"/api/grid/stop/{pair}", "POST")
    if "error" in result:
        return f"Erreur: {result['error']}"
    return f"Grid arretee: {pair}"


def cmd_help():
    return (
        "*Niam-Bay Bot — commandes:*\n"
        "/status — état grids + balance\n"
        "/balance — portfolio Kraken\n"
        "/price [BTC] — prix temps réel\n"
        "/start DOT [cap] [lev] [spacing] — grid NEUTRAL\n"
        "/short BTC [cap] [lev] [spacing] — grid SHORT\n"
        "/stop DOT — arrêter une grid\n"
        "/help — cette aide"
    )


def handle(text):
    parts = text.strip().split()
    if not parts:
        return None
    cmd = parts[0].lower().split("@")[0]
    args = parts[1:]
    if cmd == "/status":
        return cmd_status()
    elif cmd == "/balance":
        return cmd_balance()
    elif cmd == "/price":
        return cmd_price(args)
    elif cmd == "/start":
        return cmd_start(args)
    elif cmd == "/short":
        return cmd_short(args)
    elif cmd == "/stop":
        return cmd_stop(args)
    elif cmd == "/help":
        return cmd_help()
    return None


def main():
    global OFFSET
    log.info("Niam-Bay Telegram Bot started")
    tg_send("Bot demarré. Tape /help pour la liste des commandes.")
    while True:
        try:
            updates = tg_get_updates(OFFSET)
            for u in updates:
                OFFSET = u["update_id"] + 1
                msg = u.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                if chat_id != CHAT_ID:
                    continue
                text = msg.get("text", "")
                if not text:
                    continue
                log.info(f"Received: {text}")
                reply = handle(text)
                if reply:
                    tg_send(reply)
        except KeyboardInterrupt:
            log.info("Stopped.")
            break
        except Exception as e:
            log.error(f"Main loop error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
